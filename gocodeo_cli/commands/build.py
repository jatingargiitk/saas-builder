"""
Commands for step-by-step building of SaaS applications.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from gocodeo_cli.agents.build_agent import BuildAgent
from gocodeo_cli.services.project_state import ProjectState, ProjectStage, load_project_state
from gocodeo_cli.utils import config
from gocodeo_cli.services.llm_service import llm

# Create Typer app
app = typer.Typer(
    help="Build your application step by step",
    no_args_is_help=True
)

console = Console()

# Available model options
MODELS = {
    "1": "claude-3-7-sonnet-20250219",
    "2": "gpt-4.1",
    "3": "gemini-2.5-pro-preview-03-25"
}

# Template stacks mapping
TEMPLATE_STACKS = {
    "1": ("quickart", "E-commerce Template"),
    "2": ("growith", "SaaS Marketing Template"),
    "3": ("crm", "CRM  Template"),
    "4": ("growith", "Default Template")
}

# Set Claude 3.7 Sonnet as default model
DEFAULT_MODEL = MODELS["1"]

@app.command()
def init(
    name: str = typer.Option(None, "--name", "-n", prompt="What's your project name?"),
    description: str = typer.Option(None, "--description", "-d", prompt="Describe your application"),
    directory: Optional[str] = typer.Option(None, "--directory", "-dir", help="Project directory (defaults to project name)"),
    tech_stack: Optional[str] = typer.Option(None, "--tech-stack", "-t", help="Tech stack to use (1=Next.js UI Only, 2=Next.js+Supabase)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to use")
):
    """
    Initialize and build a new SaaS project with all necessary components.
    
    This command creates a full SaaS application with:
    - Project scaffold based on selected template
    - Authentication system
    - Data persistence
    """
    # Show template stack options
    template_name = "growith"  # Default template
    console.print("\n[bold]Available Template Stacks:[/bold]\n")
    for key, (_, desc) in TEMPLATE_STACKS.items():
        console.print(f"{key}. {desc}")
        if key != "4":  # Add newline except for last item
            console.print()
    
    stack_choice = typer.prompt("\nSelect your template stack (enter number)", default="4")
    template_name = TEMPLATE_STACKS.get(stack_choice, TEMPLATE_STACKS["4"])[0]
    
    # Show tech stack options if not provided
    if not tech_stack:
        console.print("\n[bold]Available Tech Stacks:[/bold]\n")
        console.print("1. Next.js (UI Only)")
        console.print("   Modern frontend-focused application")
        console.print("   Features: Beautiful UI, TypeScript, Tailwind CSS\n")
        console.print("2. Next.js + Supabase")
        console.print("   Full-stack app with serverless backend")
        console.print("   Features: Authentication, Real-time, PostgreSQL, TypeScript\n")
        
        tech_stack = typer.prompt("Select your tech stack (enter number)", default="1")
    
    # Collect Supabase credentials for stack 1
    supabase_url = None
    supabase_anon_key = None
    supabase_token = None
    
    if tech_stack == "2":
        console.print("\n[bold]For Supabase integration, please provide your credentials:[/bold]")
        supabase_url = typer.prompt("Supabase Project URL",hide_input=True)
        supabase_anon_key = typer.prompt("Supabase Anon Key",hide_input=True)
        supabase_token = typer.prompt("Supabase Access Token",hide_input=True)
    
    # Show model options if not provided
    if not model:
        console.print("\nAvailable AI Models:\n")
        console.print("1. Claude 3.7 Sonnet (Anthropic)")
        console.print("   High quality code with excellent documentation\n")
        
        console.print("2. GPT-4.1 (OpenAI)")
        console.print("   Fast and reliable code generation\n")
        
        console.print("3. Gemini 2.5 Pro (Google)")
        console.print("   Advanced reasoning and error-free code\n")
        
        model_choice = typer.prompt("Select AI model to use (enter number) [1/2/3]", default="1")
        model = MODELS.get(model_choice, DEFAULT_MODEL)
    
    # Validate API key for the selected model
    _validate_api_key_for_model(model)
    
    # Normalize project name for directory
    if not directory:
        directory = name.lower().replace(" ", "-")
    
    # Create project directory
    project_dir = Path(directory)
    if project_dir.exists() and any(project_dir.iterdir()):
        console.print(f"[yellow]Directory {directory} already exists and is not empty.[/yellow]")
        overwrite = typer.confirm("Do you want to continue anyway?", default=False)
        if not overwrite:
            raise typer.Abort()
    
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create build agent
    agent = BuildAgent(project_dir)
    
    # Run the build flow
    console.print(f"\n[bold]Building project: {name}[/bold]\n")
    
    try:
        # Use asyncio to run the build flow
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        result = asyncio.run(agent.run_build_flow(
            name, 
            description, 
            tech_stack, 
            model, 
            supabase_url=supabase_url, 
            supabase_anon_key=supabase_anon_key,
            supabase_token=supabase_token,
            template_name=template_name
        ))
        
        if not result:
            console.print("\n[red]Build failed![/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)



# def get_tech_stack_name(choice: str) -> str:
#     """Get the display name for a tech stack choice."""
#     stacks = {
#         "1": "Next.js + Supabase",
#         "2": "Next.js + Firebase",
#         "3": "Next.js + MongoDB"
#     }
#     return stacks.get(choice, "Unknown")

def _validate_api_key_for_model(model: str) -> None:
    """Validate API key for the selected model, prompt if missing."""
    try:
        # Load environment variables from workspace
        config.load_workspace_env()
        
        # This will prompt for the API key if it's missing
        if model.startswith("gpt"):
            llm._ensure_openai_client()
        elif model.startswith("claude"):
            llm._ensure_anthropic_client()
        elif model.startswith("gemini"):
            llm._ensure_gemini_available()
    except Exception as e:
        console.print(f"[red]Error validating API key: {str(e)}[/red]")
        raise typer.Exit(1) 