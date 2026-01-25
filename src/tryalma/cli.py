"""TryAlma CLI application."""

import typer

from tryalma.core import get_greeting
from tryalma.passport.cli import app as passport_app

app = typer.Typer(
    name="tryalma",
    help="TryAlma CLI - A sample CLI and API application.",
    add_completion=False,
)

# Register passport sub-command
app.add_typer(passport_app, name="passport")


@app.command()
def hello(
    name: str = typer.Option(
        "World",
        "--name",
        "-n",
        help="Name to greet.",
    ),
) -> None:
    """Print a greeting message."""
    message = get_greeting(name)
    typer.echo(message)


@app.command()
def version() -> None:
    """Show the application version."""
    from tryalma import __version__

    typer.echo(f"tryalma version {__version__}")


if __name__ == "__main__":
    app()
