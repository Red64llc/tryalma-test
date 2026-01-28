"""Cross-check CLI command.

Task 5.2: CLI crosscheck subcommand implementation.

Requirements: 6.1, 7.1, 7.2
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tryalma.crosscheck.config import CrossCheckConfig
from tryalma.crosscheck.exceptions import ConfigurationError
from tryalma.crosscheck.models import (
    CrossCheckResult,
    DiscrepancySeverity,
    ExtractionStatus,
)
from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider
from tryalma.crosscheck.service import CrossCheckService
from tryalma.passport.extractor import MRZExtractor
from tryalma.passport.validator import MRZValidator

# Rich console for output
console = Console()
error_console = Console(stderr=True)


def crosscheck(
    image_path: Path = typer.Argument(
        ...,
        help="Path to passport image file",
        exists=False,  # We handle validation ourselves for better error messages
    ),
    hf_token: str | None = typer.Option(
        None,
        "--hf-token",
        envvar="HF_TOKEN",
        help="Hugging Face API token (defaults to HF_TOKEN env var)",
    ),
    mrz_timeout: float = typer.Option(
        30.0,
        "--mrz-timeout",
        help="MRZ extraction timeout in seconds",
    ),
    vlm_timeout: float = typer.Option(
        60.0,
        "--vlm-timeout",
        help="VLM extraction timeout in seconds",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output including all metadata",
    ),
) -> None:
    """Cross-check passport data using dual-source extraction.

    Extracts passport data from both MRZ (Machine Readable Zone) and VLM
    (Vision Language Model - Qwen2-VL) sources, cross-validates results,
    and reports discrepancies.

    Requires a Hugging Face API token for VLM extraction. Set the HF_TOKEN
    environment variable or use --hf-token option.

    Examples:
        # Basic usage
        tryalma crosscheck passport.jpg

        # With explicit token and custom timeouts
        tryalma crosscheck passport.jpg --hf-token your_token --vlm-timeout 90

        # Verbose output with all metadata
        tryalma crosscheck passport.jpg --verbose
    """
    # Validate image path exists (exit code 2 for validation error)
    if not image_path.exists():
        error_console.print(f"[red]Error:[/red] Image file not found: {image_path}")
        raise typer.Exit(code=2)

    # Validate HF token is provided
    if not hf_token:
        error_console.print(
            "[red]Error:[/red] HF_TOKEN required. Set HF_TOKEN environment variable "
            "or use --hf-token option."
        )
        raise typer.Exit(code=2)

    try:
        # Create configuration
        config = CrossCheckConfig(
            hf_token=hf_token,
            mrz_timeout_seconds=mrz_timeout,
            vlm_timeout_seconds=vlm_timeout,
        )
        config.validate()

        # Create service components
        mrz_extractor = MRZExtractor()
        mrz_validator = MRZValidator()
        vlm_provider = Qwen2VLProvider(hf_token=hf_token)

        # Create service and run extraction
        service = CrossCheckService(
            mrz_extractor=mrz_extractor,
            mrz_validator=mrz_validator,
            vlm_provider=vlm_provider,
            config=config,
        )

        result = service.extract_and_crosscheck(image_path)

        # Display results
        _display_result(result, verbose)

        # Determine exit code
        exit_code = _determine_exit_code(result)
        if exit_code != 0:
            raise typer.Exit(code=exit_code)

    except ConfigurationError as e:
        error_console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(code=2)


def _display_result(result: CrossCheckResult, verbose: bool) -> None:
    """Display cross-check result to console.

    Args:
        result: The cross-check result to display.
        verbose: If True, show additional metadata.
    """
    # Status header
    status_color = {
        ExtractionStatus.SUCCESS: "green",
        ExtractionStatus.PARTIAL: "yellow",
        ExtractionStatus.ERROR: "red",
    }.get(result.status, "white")

    console.print(f"\n[bold]Status:[/bold] [{status_color}]{result.status.value}[/]")

    # Sources used
    if result.sources_used:
        console.print(f"[bold]Sources:[/bold] {', '.join(result.sources_used)}")

    # Error handling
    if result.status == ExtractionStatus.ERROR:
        console.print(f"\n[red]Error:[/red] {result.error}")
        if result.mrz_error:
            console.print(f"  MRZ: {result.mrz_error}")
        if result.vlm_error:
            console.print(f"  VLM: {result.vlm_error}")
        return

    # Document confidence
    if result.document_confidence is not None:
        confidence_pct = result.document_confidence * 100
        console.print(
            f"[bold]Document Confidence:[/bold] {confidence_pct:.1f}%"
        )

    # Extracted fields
    if result.passport_data:
        console.print("\n[bold]Extracted Fields:[/bold]")
        _display_passport_data(result)

    # Discrepancies
    if result.discrepancies:
        console.print(f"\n[bold]Discrepancies ({len(result.discrepancies)}):[/bold]")
        _display_discrepancies(result)
    else:
        console.print("\n[green]No discrepancies found - sources agree.[/green]")

    # Verbose metadata
    if verbose and result.metadata:
        console.print("\n[bold]Metadata:[/bold]")
        _display_metadata(result)


def _display_passport_data(result: CrossCheckResult) -> None:
    """Display extracted passport data as a table."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value")
    table.add_column("Confidence")

    data = result.passport_data
    if not data:
        return

    fields = [
        ("Surname", data.surname),
        ("Given Names", data.given_names),
        ("Passport Number", data.passport_number),
        ("Nationality", data.nationality),
        ("Date of Birth", str(data.date_of_birth) if data.date_of_birth else None),
        ("Expiry Date", str(data.expiry_date) if data.expiry_date else None),
        ("Sex", data.sex),
        ("Place of Birth", data.place_of_birth),
    ]

    for field_name, value in fields:
        # Get confidence for this field
        field_key = field_name.lower().replace(" ", "_")
        confidence = result.field_confidences.get(field_key)
        conf_str = f"{confidence * 100:.0f}%" if confidence is not None else "-"

        table.add_row(
            field_name,
            str(value) if value else "[dim]-[/dim]",
            conf_str,
        )

    console.print(table)


def _display_discrepancies(result: CrossCheckResult) -> None:
    """Display discrepancy information."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Severity")
    table.add_column("MRZ Value")
    table.add_column("VLM Value")
    table.add_column("Recommended")

    for disc in result.discrepancies:
        severity_color = {
            DiscrepancySeverity.CRITICAL: "red",
            DiscrepancySeverity.WARNING: "yellow",
            DiscrepancySeverity.INFORMATIONAL: "blue",
        }.get(disc.severity, "white")

        table.add_row(
            disc.field_name,
            f"[{severity_color}]{disc.severity.value}[/]",
            disc.mrz_value or "[dim]-[/dim]",
            disc.vlm_value or "[dim]-[/dim]",
            disc.recommended_value or "[dim]-[/dim]",
        )

    console.print(table)


def _display_metadata(result: CrossCheckResult) -> None:
    """Display processing metadata."""
    if not result.metadata:
        return

    meta = result.metadata

    table = Table(show_header=True, header_style="bold")
    table.add_column("Property")
    table.add_column("Value")

    table.add_row("Total Duration", f"{meta.extraction_duration_ms}ms")

    if meta.mrz_duration_ms is not None:
        table.add_row("MRZ Duration", f"{meta.mrz_duration_ms}ms")

    if meta.vlm_duration_ms is not None:
        table.add_row("VLM Duration", f"{meta.vlm_duration_ms}ms")

    if meta.vlm_model:
        table.add_row("VLM Model", meta.vlm_model)

    table.add_row("Timestamp", meta.timestamp.isoformat())

    console.print(table)


def _determine_exit_code(result: CrossCheckResult) -> int:
    """Determine exit code based on result status.

    Exit codes follow CLI conventions:
    - 0: Success or partial success
    - 3: Processing error (both sources failed)

    Args:
        result: The cross-check result.

    Returns:
        Exit code (0, or 3).
    """
    if result.status == ExtractionStatus.ERROR:
        return 3  # Processing error

    # SUCCESS or PARTIAL both return 0
    return 0
