"""
SaaS-Builder CLI - Generate full-stack SaaS applications with AI.
"""
import typer
from rich import print
from rich.console import Console
from rich.panel import Panel

from gocodeo_cli.commands import build

# Initialize Typer app
app = typer.Typer(
    name="saas-builder",
    help="AI-powered CLI for generating full-stack SaaS applications",
    add_completion=False,
)

# Create console for rich output
console = Console()

def version_callback(value: bool):
    """Print version information."""
    if value:
        print(Panel.fit(
            "[bold blue]SaaS-Builder[/bold blue] [yellow]v0.1.0[/yellow]",
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
    SaaS-Builder CLI - Generate full-stack SaaS applications with AI.
    """
    pass

app.command()(build.init)

if __name__ == "__main__":
    app() 