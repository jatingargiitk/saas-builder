"""
GoCodeo CLI - Generate full-stack SaaS applications with AI.
"""
import typer
from rich import print
from rich.console import Console
from rich.panel import Panel

from gocodeo_cli.commands import  build

# Initialize Typer app
app = typer.Typer(
    name="gocodeo",
    help="AI-powered CLI for generating full-stack SaaS applications",
    add_completion=False,
)

# Create console for rich output
console = Console()

def version_callback(value: bool):
    """Print version information."""
    if value:
        print(Panel.fit(
            "[bold blue]GoCodeo CLI[/bold blue] [yellow]v0.1.0[/yellow]",
            title="Version",
            border_style="blue",
        ))
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version information.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    GoCodeo CLI - Generate full-stack SaaS applications with AI.
    """
    pass


app.add_typer(build.app, name="build")  # Add agentic build commands

if __name__ == "__main__":
    app() 