import os
import subprocess
import time
import socket
from typing import Dict, Any, Optional
import platform
import signal
from rich.console import Console
from ..agents.base import BaseTool, BaseAgent
from ..utils.progress import ProgressSpinner

class NpmInstallTool(BaseTool):
    """Tool for installing npm dependencies."""
    
    def __init__(self):
        super().__init__(
            name="npm_install",
            description="Install npm dependencies in the project directory"
        )
        self.console = Console()
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Install npm dependencies in the project directory.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments
            
        Returns:
            Result message
        """
        try:
            # Change to project directory
            os.chdir(agent.project_dir)
            
            # Get the tech stack from agent's memory context
            tech_stack = agent.memory.context.get("tech_stack", None)
            # If tech_stack is 1 (UI only), use task number 2, otherwise use 5
            task_number = 2 if tech_stack == "1" else 5
            self.console.print("\n")

            # Create and start progress spinner
            spinner = ProgressSpinner(f"📦 Task{task_number}: Running Terminal Agent", self.console)
            spinner.start()
            
            # Run npm install
            agent.memory.add_message("system", "Installing npm dependencies...")
            
            # Execute npm install
            npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

            # Execute npm install
            process = subprocess.run(
                [npm_cmd, "install"],
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # Stop the spinner before checking result
            spinner.stop(preserve_message=True)
            
            # Check result
            if process.returncode == 0:
                agent.memory.add_message("system", "Dependencies installed successfully")
                return f"✓ Task{task_number} completed: Dependencies installed successfully"
            else:
                agent.memory.add_message("system", f"Failed to install dependencies: {process.stderr}")
                return f"❌ Failed to install dependencies: {process.stderr}"
                
        except Exception as e:
            # Make sure to stop spinner on error
            if 'spinner' in locals():
                spinner.stop(preserve_message=True)
            agent.memory.add_message("system", f"Failed to install dependencies: {str(e)}")
            return f"❌ Failed to install dependencies: {str(e)}"

class NpmDevServerTool(BaseTool):
    """Tool for starting the npm development server."""
    
    def __init__(self):
        super().__init__(
            name="npm_run_dev",
            description="Start the npm development server"
        )
        self.process = None
        self.console = Console()
        # Flag to track if cleanup has already been performed
        self._cleanup_done = False
        # Register signal handlers for proper cleanup
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """Register signal handlers to properly terminate the process."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals by cleaning up the dev server process."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up the development server process."""
        # Avoid duplicate cleanup
        if self._cleanup_done:
            return
            
        if self.process is not None and self.process.poll() is None:
            try:
                # Store PID for debug logging but don't display it
                pid = self.process.pid
                
                if platform.system() == "Windows":
                    # On Windows, use taskkill to kill the process tree
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                                  capture_output=True, text=True)
                else:
                    # On Unix-like systems, send SIGTERM to process group
                    pgid = os.getpgid(pid)
                    os.killpg(pgid, signal.SIGTERM)
                    self.process.terminate()
                
                # Wait for process to terminate
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    if platform.system() == "Windows":
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                                      capture_output=True, text=True)
                    else:
                        self.process.kill()
                
                self.console.print("✓ Development server terminated successfully")
            except Exception as e:
                self.console.print(f"❌ Error terminating development server: {str(e)}")
            finally:
                self.process = None
                
        # Mark cleanup as done
        self._cleanup_done = True
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available by attempting to bind to it."""
        try:
            # Create a TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            # Try to bind to the port
            sock.bind(('127.0.0.1', port))
            # If successful, the port is available
            sock.close()
            return True
        except (socket.error, OSError):
            # If binding fails, the port is in use
            return False
    
    def _find_available_port(self, start_port: int = 3000, end_port: int = 3005) -> int:
        """Find the first available port in the given range."""
        for port in range(start_port, end_port + 1):
            if self._is_port_available(port):
                return port
        # If no ports are available, return the default port and let it fail
        return start_port
    
    async def execute(self, agent: BaseAgent, **kwargs) -> str:
        """
        Start the npm development server.
        
        Args:
            agent: The agent executing this tool
            kwargs: Additional arguments
            
        Returns:
            Result message
        """
        try:
            # Print current directory for debugging
            current_dir = os.getcwd()
            
            # Get the tech stack from agent's memory context
            tech_stack = agent.memory.context.get("tech_stack", None)
            # If tech_stack is 1 (UI only), use task number 3, otherwise use 6
            task_number = 3 if tech_stack == "1" else 6
            self.console.print("\n")

            # Create and start progress spinner
            self.console.print(f"📦 Task{task_number}: Running Browser Agent")
            
            
            # Start the development server
            agent.memory.add_message("system", "Starting development server...")
            
            # Find an available port
            port = self._find_available_port()
            
            # Determine the correct command to run
            npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
            
            # Start server as background process
            kwargs = {}
            if platform.system() == "Windows":
                kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs['preexec_fn'] = os.setsid
            
            # Pass the port to Next.js using the -- -p flag
            self.process = subprocess.Popen(
                [npm_cmd, "run", "dev", "--", "-p", str(port)],
                cwd=current_dir,
                text=True,
                **kwargs
            )
            
            # Give it a few seconds to start
            time.sleep(4)

            
            # Check if server is still running
            if self.process.poll() is None:
                # Server is running
                agent.memory.add_message("system", f"Development server started successfully on port {port}")
                
                # Try to open browser with the correct port
                url = f"http://localhost:{port}"
                browser_success = self._open_in_browser(url)
                
                # Add info message about how to terminate
                self.console.print("\n[bold cyan]ℹ️ Press Ctrl+C to terminate the development server[/bold cyan]")
                
                if browser_success:
                    return f"✓ Task {task_number} completed: Development server started successfully and opened in browser at {url}"
                else:
                    return f"✓ Task {task_number} completed: Development server started successfully at {url}"
            else:
                # Server failed to start
                stdout, stderr = self.process.communicate()
                error_message = stderr or stdout or "Unknown error"
                agent.memory.add_message("system", f"Failed to start development server: {error_message}")
                return f"❌ Failed to start development server: {error_message}"
                
        except Exception as e:
            # Make sure to stop spinner on error

            agent.memory.add_message("system", f"Failed to start development server: {str(e)}")
            return f"❌ Failed to start development server: {str(e)}"
    
    def _open_in_browser(self, url: str) -> bool:
        """Open the URL in the default browser."""
        try:
            import webbrowser
            if webbrowser.open(url):
                return True
                
            # If that fails, try system-specific commands
            if platform.system() == "Windows":
                print(f"Opening URL in Windows: {url}")
                os.system(f"start {url}")
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open {url}")
            else:  # Linux
                os.system(f"xdg-open {url}")
                
            return True
        except Exception:
            return False 