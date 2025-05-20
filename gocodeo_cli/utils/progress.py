import threading
import time
import sys
from rich.console import Console

class ProgressSpinner:
    
    SHOW_CURSOR = "\033[?25h"

    def __init__(self, message: str, console: Console = None):
        """
        Initialize the progress spinner.
        
        Args:
            message: The message to display before the dots
            console: Rich console instance to use for output
        """
        self.message = message
        self.is_running = False
        self.thread = None
        self.console = console or Console()
        self._lock = threading.Lock()
        self.max_length = 0 
  
    
    def _animate(self):
        """Animation loop that displays the message with animated dots."""
        dots = 0
        while self.is_running:
            with self._lock:
                full_message = f"{self.message}{'.' * dots}"
                padding = ' ' * (self.max_length - len(full_message))
                sys.stdout.write('\r' + full_message + padding)
                sys.stdout.flush()
            dots = (dots + 1) % 4
            time.sleep(0.5)
    
    def start(self):
        """Start the progress animation in a separate thread."""
        self.is_running = True
        self.thread = threading.Thread(target=self._animate)
        self.max_length = len(self.message) + 3
        self.thread.daemon = True
        HIDE_CURSOR = "\033[?25l"
        sys.stdout.write(HIDE_CURSOR)
        self.thread.start()
    
    def stop(self, preserve_message=False):
        """
        Stop the progress animation.
        
        Args:
            preserve_message: If True, keeps the task message and clears only dots
        """
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=0.1)  # Short timeout to ensure thread stops
        
        # Triple-safety clearing mechanism to ensure no dots remain
        for _ in range(3):  # Try multiple clearing attempts
            # Clear the line completely with extra padding
            sys.stdout.write('\r' + ' ' * (self.max_length + 5) + '\r')
            sys.stdout.flush()
            time.sleep(0.01)  # Small delay to ensure terminal processes the clear
        
        # Show cursor again
        sys.stdout.write(self.SHOW_CURSOR)
        sys.stdout.flush()
        
        # Fallback direct clear using terminal escape sequence
        sys.stdout.write('\033[2K\r')  # Clear entire line regardless of content
        sys.stdout.flush()
        
        if preserve_message:
            sys.stdout.write(f"{self.message}\n")
            sys.stdout.flush()
    
    def success(self, success_message: str):
        """
        Stop the spinner and print a success message.
        
        Args:
            success_message: Message to display after spinner finishes
        """
        self.stop(preserve_message=True)
        self.console.print(f"[green]✓ {success_message}[/green]")
