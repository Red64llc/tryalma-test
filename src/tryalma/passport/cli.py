"""Passport extraction CLI command.

Task 7.1, 7.2, 7.3: CLI command implementation.

Requirements: 1.1-1.4, 3.1-3.4, 4.1-4.4, 5.1-5.4, 7.1-7.3
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from tryalma.exceptions import CLIError
from tryalma.passport.exceptions import TesseractNotFoundError
from tryalma.passport.extractor import MRZExtractor
from tryalma.passport.formatter import OutputFormat, OutputFormatter
from tryalma.passport.service import PassportExtractionService
from tryalma.passport.validator import MRZValidator

# Create the passport sub-app
app = typer.Typer(
    name="passport",
    help="Extract passport data from images using MRZ (Machine Readable Zone) OCR.",
)

# Rich console for output
console = Console()
error_console = Console(stderr=True)


def _check_tesseract() -> None:
    """Check if Tesseract is installed and raise helpful error if not.

    Requirement 5.3: Show installation instructions if missing.
    """
    if not MRZExtractor.check_tesseract_installed():
        raise TesseractNotFoundError()


def _validate_path(path: Path) -> None:
    """Validate that the path exists.

    Requirement 1.3: Invalid path error with exit code 2.
    """
    if not path.exists():
        error_console.print(f"[red]Error:[/red] Path does not exist: {path}")
        raise typer.Exit(code=2)


@app.command()
def extract(
    path: Path = typer.Argument(
        ...,
        help="Path to passport image file or directory containing images",
        exists=False,  # We handle validation ourselves for better error messages
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.TABLE,
        "--format",
        "-f",
        help="Output format: table, json, or csv",
        case_sensitive=False,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write results to file instead of stdout",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show additional details including confidence scores",
    ),
) -> None:
    """Extract passport data from image file(s).

    Process a single passport image or a directory of images to extract
    structured data from the Machine Readable Zone (MRZ).

    Supports JPEG, PNG, and TIFF image formats.

    Examples:
        # Extract from single image
        tryalma passport extract passport.jpg

        # Extract from directory with JSON output
        tryalma passport extract ./passports --format json

        # Save results to file
        tryalma passport extract passport.jpg --output results.json --format json

        # Verbose mode with confidence scores
        tryalma passport extract passport.jpg --verbose
    """
    # Validate path exists (Requirement 1.3)
    _validate_path(path)

    # Check Tesseract is available (Requirement 5.3)
    try:
        _check_tesseract()
    except TesseractNotFoundError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code)

    # Create service instances
    extractor = MRZExtractor()
    validator = MRZValidator()
    service = PassportExtractionService(extractor, validator)
    formatter = OutputFormatter()

    # Determine if single file or directory
    if path.is_file():
        results = _process_single_file(service, path)
    else:
        results = _process_directory(service, path)

    # Check for empty results (Requirement 1.4)
    if not results:
        console.print("[yellow]No supported image files found to process.[/yellow]")
        raise typer.Exit(code=0)

    # Format output
    output_text = formatter.format(results, format, verbose=verbose)

    # Write to file or stdout (Requirement 4.4)
    if output:
        output.write_text(output_text)
        console.print(f"[green]Results written to {output}[/green]")
    else:
        # Use typer.echo for JSON/CSV to avoid Rich formatting/control characters
        if format in (OutputFormat.JSON, OutputFormat.CSV):
            typer.echo(output_text)
        else:
            console.print(output_text)

    # Display summary for batch processing (Requirement 3.2)
    if len(results) > 1:
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        console.print(f"\n[bold]Summary:[/bold] {successful} successful, {failed} failed")

    # Determine exit code (Requirement 5.4)
    exit_code = _determine_exit_code(results)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def _process_single_file(
    service: PassportExtractionService, file_path: Path
) -> list:
    """Process a single image file.

    Requirement 1.1: Single image file processing.

    Args:
        service: PassportExtractionService instance.
        file_path: Path to the image file.

    Returns:
        List containing single ExtractionResult.
    """
    result = service.extract_single(file_path)
    return [result]


def _process_directory(
    service: PassportExtractionService, directory: Path
) -> list:
    """Process all images in a directory.

    Requirements 1.2, 3.2: Batch processing with progress display.

    Args:
        service: PassportExtractionService instance.
        directory: Path to directory containing images.

    Returns:
        List of ExtractionResult objects.
    """
    # Define progress callback
    def on_progress(current: int, total: int) -> None:
        pass  # Progress is handled by Rich Progress below

    # Use Rich progress bar for batch processing (Requirement 7.3)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing images...", total=None)

        # Process with progress callback
        results = service.extract_batch(directory, on_progress=on_progress)

        progress.update(task, completed=True)

    return results


def _determine_exit_code(results: list) -> int:
    """Determine the appropriate exit code based on results.

    Requirement 5.4: Exit codes (0, 1, 2, 3)

    Args:
        results: List of ExtractionResult objects.

    Returns:
        Exit code: 0 for all success, 3 for any processing failure.
    """
    if not results:
        return 0

    # Check if all results succeeded
    all_success = all(r.success for r in results)

    if all_success:
        return 0

    # For single file failure, return processing error
    if len(results) == 1 and not results[0].success:
        return 3  # Processing error

    # For batch with partial failures, still succeed
    # (individual failures are reported in output)
    any_success = any(r.success for r in results)
    if any_success:
        return 0

    # All failed
    return 3
