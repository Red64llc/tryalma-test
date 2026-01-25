"""CLI command for G-28 form parsing.

Task 8: CLI Command implementation.

Requirements:
- 8.1: Define parse-g28 command with Typer (9.1, 9.3, 9.4, 9.6)
- 8.2: Implement command execution logic (9.1, 9.2, 9.3, 9.4, 9.6)
- 8.3: Implement CLI error handling (9.5, 10.1, 10.2, 10.3, 10.4)
- 8.4: Register command with main CLI application (9.1)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from tryalma.g28.exceptions import (
    G28ExtractionError,
    UnsupportedFormatError,
)
from tryalma.g28.parser_service import G28ParserService


def parse_g28(
    file_path: Path = typer.Argument(
        ...,
        help="Path to G-28 form (PDF or image file: PNG, JPG, JPEG, TIFF)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (writes to stdout if not specified)",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or yaml",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Include confidence scores and processing metadata",
    ),
) -> None:
    """Parse a G-28 form and extract structured data.

    Supports PDF and image formats (PNG, JPG, JPEG, TIFF).
    Outputs JSON by default; use --format yaml for YAML output.

    Examples:

        tryalma parse-g28 form.pdf

        tryalma parse-g28 form.pdf --output result.json

        tryalma parse-g28 form.pdf --format yaml --verbose
    """
    try:
        # Task 8.2: Initialize G28ParserService with default dependencies
        if verbose:
            typer.echo("Initializing G28 parser...", err=True)

        service = G28ParserService.create_default()

        if verbose:
            typer.echo(f"Processing file: {file_path}", err=True)

        # Task 8.2: Invoke parse() with provided arguments
        result = service.parse(
            file_path=file_path,
            output_format=format,  # type: ignore[arg-type]
            verbose=verbose,
        )

        # Handle failed extraction result
        if not result.success:
            typer.echo(f"Error: {result.error}", err=True)
            # Determine appropriate exit code based on error type
            if result.error_code == "UNSUPPORTED_FORMAT":
                raise typer.Exit(code=2)
            else:
                raise typer.Exit(code=3)

        # Task 8.2: Format and output the result
        output_content = result.to_output(format=format)  # type: ignore[arg-type]

        if output:
            # Task 8.2: Write to specified file when --output provided
            if verbose:
                typer.echo(f"Writing output to: {output}", err=True)
            output.write_text(output_content)
            if verbose:
                typer.echo("Done.", err=True)
        else:
            # Task 8.2: Output to stdout by default
            typer.echo(output_content)

    except typer.Exit:
        # Re-raise typer.Exit exceptions (from failed result handling)
        raise

    except UnsupportedFormatError as e:
        # Task 8.3: Exit with code 2 for validation errors
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=2)

    except G28ExtractionError as e:
        # Task 8.3: Exit with code 3 for processing errors
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=3)

    except ValueError as e:
        # Handle configuration errors (e.g., missing API key)
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    except Exception as e:
        # Task 8.3: Never expose stack traces to users
        typer.echo(f"Error: An unexpected error occurred during processing.", err=True)
        raise typer.Exit(code=1)
