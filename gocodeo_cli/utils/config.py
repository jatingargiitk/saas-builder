"""
Configuration utilities for the GoCodeo CLI.
"""
import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from dotenv import load_dotenv

# Create a console for output
console = Console()

def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment variables."""
    return os.getenv("OPENAI_API_KEY")

def get_anthropic_api_key() -> Optional[str]:
    """Get Anthropic API key from environment variables."""
    return os.getenv("ANTHROPIC_API_KEY")

def get_google_api_key() -> Optional[str]:
    """Get Google API key from environment variables."""
    return os.getenv("GOOGLE_API_KEY")

def set_openai_api_key(key: str) -> None:
    """Set OpenAI API key in environment variables."""
    os.environ["OPENAI_API_KEY"] = key

def set_anthropic_api_key(key: str) -> None:
    """Set Anthropic API key in environment variables."""
    os.environ["ANTHROPIC_API_KEY"] = key

def set_google_api_key(key: str) -> None:
    """Set Google API key in environment variables."""
    os.environ["GOOGLE_API_KEY"] = key

def load_workspace_env() -> None:
    """Load environment variables from .env file in current working directory."""
    env_path = Path.cwd() / ".env" 
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

def prompt_for_api_key(model_type: str) -> str:
    """Prompt user for API key based on model type."""
    # First check if we can load from workspace env file
    load_workspace_env()
    
    # Determine the key type and check if it exists
    if model_type.startswith("claude"):
        key_name = "Anthropic"
        key_env = "ANTHROPIC_API_KEY"
        key = get_anthropic_api_key()
    elif model_type.startswith("gpt"):
        key_name = "OpenAI"
        key_env = "OPENAI_API_KEY"
        key = get_openai_api_key()
    elif model_type.startswith("gemini"):
        key_name = "Google"
        key_env = "GOOGLE_API_KEY"
        key = get_google_api_key()
    else:
        key_name = "Unknown"
        key_env = "UNKNOWN_API_KEY"
        key = None
    
    # If key found in env, return it
    if key:
        return key
    
    # If not found, prompt the user
    console.print(f"\n[yellow]No {key_name} API key found in environment variables.[/yellow]")
    console.print(f"You can set it permanently by adding {key_env} to your .env file.")
    api_key = typer.prompt(f"Please enter your {key_name} API key",hide_input=True)
    
    return api_key

