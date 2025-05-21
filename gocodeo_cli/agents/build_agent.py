import os
import asyncio
import platform
from pathlib import Path
from typing import Dict, List, Optional
import signal
import sys
import atexit

from rich.console import Console
from rich.panel import Panel

from .base import BaseAgent, AgentState
from ..tools.build_tools import InitializeTool, AddAuthTool, AddDataTool
from ..tools.env_tools import EnvFileCreatorTool
from ..tools.sql_tools import SqlMigrationTool
from ..tools.npm_tools import NpmInstallTool, NpmDevServerTool
from ..services.project_state import ProjectState, ProjectStage

class BuildAgent(BaseAgent):
    """
    Agent responsible for orchestrating the project build process.
    Handles the entire flow from initialization to completion.
    """
    
    def __init__(self, project_dir: Path, project_state: Optional[ProjectState] = None):
        """
        Initialize the build agent.
        
        Args:
            project_dir: Directory where the project will be built
            project_state: Existing project state or None to create new
        """
        super().__init__(name="build_agent", project_dir=project_dir)
        
        # Initialize project state
        self.project_state = project_state or ProjectState(project_dir)
        
        # Register tools
        self.add_tool(InitializeTool())
        self.add_tool(AddAuthTool())
        self.add_tool(AddDataTool())
        
        # Register new tools
        self.add_tool(EnvFileCreatorTool())
        self.add_tool(SqlMigrationTool())
        self.add_tool(NpmInstallTool())
        self.add_tool(NpmDevServerTool())
        
        # Flag to track if cleanup has already been performed
        self._cleanup_done = False
        
        # Register signal handlers for clean termination
        self._register_signal_handlers()
        
        # Register exit handler to ensure cleanup on terminal close
        atexit.register(self._atexit_cleanup)
        
    def _register_signal_handlers(self):
        """Register signal handlers to properly terminate processes on exit."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C and other termination signals."""
        self.cleanup()
        sys.exit(0)
        
    def _atexit_cleanup(self):
        """Cleanup handler specifically for atexit to avoid duplicate messages."""
        if not self._cleanup_done:
            self.cleanup()
        
    def cleanup(self):
        """Clean up resources and terminate running processes."""
        # Avoid duplicate cleanup
        if self._cleanup_done:
            return
            
        # Check if we have a dev server running and terminate it
        if "npm_run_dev" in self.tools and isinstance(self.tools["npm_run_dev"], NpmDevServerTool):
            self.tools["npm_run_dev"].cleanup()
            
        # Mark cleanup as done
        self._cleanup_done = True
    
    async def run_build_flow(self, name: str, description: str, tech_stack: str = "1", model: str = "claude-3-sonnet", 
                           supabase_url: str = None, supabase_anon_key: str = None, supabase_token: str = None,
                           template_name: str = "growith") -> bool:
        """
        Run the complete build flow from initialization to completion.
        
        Args:
            name: Project name
            description: Project description
            tech_stack: Selected tech stack (1=Next.js UI Only, 2=Next.js+Supabase)
            model: LLM model to use
            supabase_url: Supabase project URL
            supabase_anon_key: Supabase anonymous key
            supabase_token: Supabase access token
            template_name: Name of the template stack to use (default: growith)
            
        Returns:
            True if build was successful, False otherwise
        """
        try:
            # Store Supabase credentials in memory context if provided
            if supabase_url:
                self.memory.context["supabase_url"] = supabase_url
            if supabase_anon_key:
                self.memory.context["supabase_anon_key"] = supabase_anon_key
            if supabase_token:
                self.memory.context["supabase_token"] = supabase_token
            
            # Store template name in memory context
            self.memory.context["template_name"] = template_name
            
            # Run initialization
            init_result = await self.tools["initialize"].execute(
                agent=self,
                name=name,
                description=description,
                tech_stack=tech_stack,
                model=model,
                template_name=template_name,
                prompt_template="init_ui.txt" if tech_stack == "1" else "init.txt"
            )
            self.console.print(init_result)
            
            if "❌" in init_result:
                return False
                
            # Update project state
            self.project_state.initialize(name, description, tech_stack, model)
            self.project_state.add_files(self.memory.files)
            
            # For Next.js + Supabase (tech_stack=2), run the full flow
            if tech_stack == "2":
                # Add authentication
           
                auth_result = await self.tools["add_auth"].execute(
                    agent=self, 
                    model=model
                )
                self.console.print(auth_result)
                
                if "❌" in auth_result:
                    return False
                    
                # Update project state
                self.project_state.update_stage(ProjectStage.AUTH_ADDED)
                self.project_state.add_files(self.memory.files)
                
         
                data_result = await self.tools["add_data"].execute(
                    agent=self,
                    model=model
                )
                self.console.print(data_result)
                
                if "❌" in data_result:
                    return False
                    
                # Update project state
                self.project_state.update_stage(ProjectStage.DATA_ADDED)
                self.project_state.add_files(self.memory.files)
                
                # Create environment file
                env_result = await self.tools["create_env"].execute(
                    agent=self,
                    tech_stack=tech_stack
                )
                self.console.print(env_result)
                
                if "❌" in env_result:
                    return False
                
                # Run SQL migrations for Supabase
                sql_result = await self.tools["run_migrations"].execute(agent=self)
                self.console.print(sql_result)
                
                if "❌" in sql_result:
                    return False
            
            # Install npm dependencies
            npm_result = await self.tools["npm_install"].execute(agent=self)
            self.console.print(npm_result)
            
            if "❌" in npm_result:
                return False
            
            # Start development server
            dev_result = await self.tools["npm_run_dev"].execute(agent=self)
            self.console.print(dev_result)
            
            # Build complete
            self.state = AgentState.FINISHED
            self.console.print("\n✅ Build complete!")
            
            # Display summary
            self._print_build_summary()
            
            # Display prompt about continuing the server or terminating it
            self.console.print("\n[bold cyan]The development server is running in the background.[/bold cyan]")
            self.console.print("[bold cyan]Press Ctrl+C to terminate the server and exit.[/bold cyan]")
            self.console.print("[bold yellow]Important: Closing this terminal window will also terminate the server.[/bold yellow]")
            
            # Wait for user to decide to terminate
            try:
                while True:
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, asyncio.CancelledError):
                self.cleanup()
            
            return True
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.console.print(f"\n[red]Error:[/red] {str(e)}")
            import traceback
            traceback.print_exc()
            self.cleanup()  # Clean up resources on error
            return False
    
    def _print_build_summary(self):
        """Print a summary of the build process."""
        num_files = len(self.memory.files)
        
        summary = f"""
        Project: {self.memory.context.get('project_name', 'Unknown')}
        Description: {self.memory.context.get('project_description', 'Unknown')}
        Tech Stack: {self._get_tech_stack_name(self.memory.context.get('tech_stack', '1'))}
        Files Generated: {num_files}
        Status: {self.state.value}
        """
        
        self.console.print(Panel(summary, title="Build Summary", expand=False))
    
    def _get_tech_stack_name(self, tech_stack: str) -> str:
        """Get the full name of a tech stack from its code."""
        tech_stacks = {
            "1": "Next.js (UI Only)",
            "2": "Next.js + Supabase",
            "3": "Next.js with MongoDB"
        }
        return tech_stacks.get(tech_stack, "Unknown Tech Stack") 