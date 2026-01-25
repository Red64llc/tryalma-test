"""Output formatting for passport extraction results.

Task 6.1: Table output formatter using Rich
Task 6.2: JSON and CSV output formatters

Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3
"""

import csv
import io
import json
from enum import Enum

from rich.console import Console
from rich.table import Table

from tryalma.passport.models import ExtractionResult


class OutputFormat(str, Enum):
    """Output format options for passport extraction results.

    Requirement 4.1: Table as default
    Requirement 4.2: JSON support
    Requirement 4.3: CSV support
    """

    TABLE = "table"
    JSON = "json"
    CSV = "csv"


class OutputFormatter:
    """Formats passport extraction results for display.

    Supports table (Rich), JSON, and CSV output formats with optional
    verbose mode for additional details like confidence scores.

    Requirements:
    - 3.1: Clear labels for single image display
    - 3.2: Clear separation for batch results
    - 3.3: Source file in output
    - 3.4: Verbose mode with confidence scores
    - 4.1: Table format default
    - 4.2: JSON output format
    - 4.3: CSV output format
    """

    # Standard CSV/JSON field order
    STANDARD_FIELDS = [
        "source_file",
        "surname",
        "given_names",
        "date_of_birth",
        "nationality",
        "passport_number",
        "expiry_date",
        "sex",
        "place_of_birth",
        "mrz_type",
        "mrz_valid",
    ]

    def format(
        self,
        results: list[ExtractionResult],
        format: OutputFormat,
        verbose: bool = False,
    ) -> str:
        """Format extraction results in the specified format.

        Args:
            results: List of extraction results to format.
            format: Output format (table, json, csv).
            verbose: Include confidence scores and additional details.

        Returns:
            Formatted string ready for display or file output.
        """
        if format == OutputFormat.TABLE:
            return self.format_table(results, verbose=verbose)
        elif format == OutputFormat.JSON:
            return self.format_json(results, verbose=verbose)
        elif format == OutputFormat.CSV:
            return self.format_csv(results, verbose=verbose)
        else:
            # Should not reach here with enum, but handle gracefully
            return self.format_table(results, verbose=verbose)

    def format_table(
        self,
        results: list[ExtractionResult],
        verbose: bool = False,
    ) -> str:
        """Format results as a human-readable table using Rich.

        Requirements:
        - 3.1: Display all extracted fields with clear labels
        - 3.2: Clear separation between records in batch
        - 3.3: Source file name alongside each result
        - 3.4: Confidence scores in verbose mode

        Args:
            results: List of extraction results to format.
            verbose: Include confidence scores and additional details.

        Returns:
            Formatted table string.
        """
        if not results:
            return "No results to display."

        # Use Rich console to capture output as string
        console = Console(force_terminal=False, no_color=True, width=120)
        output = io.StringIO()
        console = Console(file=output, force_terminal=False, no_color=True, width=120)

        for i, result in enumerate(results):
            if i > 0:
                # Add separator between records (Requirement 3.2)
                console.print("\n" + "-" * 60 + "\n")

            self._render_single_result_table(console, result, verbose)

        return output.getvalue()

    def _render_single_result_table(
        self,
        console: Console,
        result: ExtractionResult,
        verbose: bool,
    ) -> None:
        """Render a single extraction result as a table.

        Args:
            console: Rich console for output.
            result: Extraction result to render.
            verbose: Include verbose details.
        """
        # Create table for this result
        table = Table(
            title=f"Passport Data: {result.source_file.name}",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", width=40)

        if result.success and result.data:
            data = result.data

            # Personal information (Requirements 2.1-2.8)
            table.add_row("Surname", data.surname or "N/A")
            table.add_row("Given Names", data.given_names or "N/A")
            table.add_row(
                "Date of Birth",
                data.date_of_birth.isoformat() if data.date_of_birth else "N/A",
            )
            table.add_row("Nationality", data.nationality or "N/A")
            table.add_row("Passport Number", data.passport_number or "N/A")
            table.add_row(
                "Expiry Date",
                data.expiry_date.isoformat() if data.expiry_date else "N/A",
            )
            table.add_row("Sex", data.sex or "N/A")
            table.add_row("Place of Birth", data.place_of_birth or "N/A")

            # MRZ validation info (Requirements 6.2-6.3)
            table.add_row("MRZ Type", data.mrz_type or "N/A")
            table.add_row("MRZ Valid", "Yes" if data.mrz_valid else "No")

            if data.check_digit_errors:
                table.add_row(
                    "Check Digit Errors", ", ".join(data.check_digit_errors)
                )

            # Verbose mode: confidence and raw MRZ (Requirement 3.4)
            if verbose:
                confidence_str = (
                    f"{data.confidence:.2f}" if data.confidence is not None else "N/A"
                )
                table.add_row("Confidence", confidence_str)
                if data.raw_mrz:
                    table.add_row("Raw MRZ", data.raw_mrz[:50] + "...")

        else:
            # Failed extraction
            table.add_row("Status", "Error")
            table.add_row("Error", result.error or "Unknown error")

        console.print(table)

    def format_json(
        self,
        results: list[ExtractionResult],
        verbose: bool = False,
    ) -> str:
        """Format results as JSON.

        JSON structure per design.md:
        {
            "results": [...],
            "summary": {"total": N, "successful": N, "failed": N}
        }

        Requirements:
        - 4.2: Valid JSON output
        - 2.9: Include unavailable_fields

        Args:
            results: List of extraction results to format.
            verbose: Include confidence scores and raw MRZ.

        Returns:
            Valid JSON string.
        """
        output_results = []
        successful_count = 0
        failed_count = 0

        for result in results:
            if result.success and result.data:
                successful_count += 1
                item = self._result_to_json_dict(result, verbose)
            else:
                failed_count += 1
                item = {
                    "source_file": str(result.source_file),
                    "success": False,
                    "error": result.error,
                }

            output_results.append(item)

        output = {
            "results": output_results,
            "summary": {
                "total": len(results),
                "successful": successful_count,
                "failed": failed_count,
            },
        }

        return json.dumps(output, indent=2)

    def _result_to_json_dict(
        self,
        result: ExtractionResult,
        verbose: bool,
    ) -> dict:
        """Convert a successful extraction result to JSON-serializable dict.

        Args:
            result: Successful extraction result.
            verbose: Include verbose details.

        Returns:
            Dictionary ready for JSON serialization.
        """
        data = result.data
        assert data is not None  # Caller ensures success=True

        item = {
            "source_file": str(data.source_file),
            "success": True,
            "surname": data.surname,
            "given_names": data.given_names,
            "date_of_birth": (
                data.date_of_birth.isoformat() if data.date_of_birth else None
            ),
            "nationality": data.nationality,
            "passport_number": data.passport_number,
            "expiry_date": data.expiry_date.isoformat() if data.expiry_date else None,
            "sex": data.sex,
            "place_of_birth": data.place_of_birth,
            "mrz_type": data.mrz_type,
            "mrz_valid": data.mrz_valid,
            "check_digit_errors": data.check_digit_errors,
            "unavailable_fields": data.get_unavailable_fields(),
        }

        if verbose:
            item["confidence"] = data.confidence
            item["raw_mrz"] = data.raw_mrz

        return item

    def format_csv(
        self,
        results: list[ExtractionResult],
        verbose: bool = False,
    ) -> str:
        """Format results as CSV with headers.

        Headers per design.md:
        source_file,surname,given_names,date_of_birth,nationality,
        passport_number,expiry_date,sex,place_of_birth,mrz_type,mrz_valid

        Requirement 4.3: Valid CSV output.

        Args:
            results: List of extraction results to format.
            verbose: Include confidence column.

        Returns:
            Valid CSV string with headers.
        """
        output = io.StringIO()

        # Build header list
        fieldnames = list(self.STANDARD_FIELDS)
        if verbose:
            fieldnames.append("confidence")
        # Always include error column for failed results
        fieldnames.append("error")

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for result in results:
            row = self._result_to_csv_row(result, verbose)
            writer.writerow(row)

        return output.getvalue()

    def _result_to_csv_row(
        self,
        result: ExtractionResult,
        verbose: bool,
    ) -> dict:
        """Convert an extraction result to CSV row dict.

        Args:
            result: Extraction result (success or failure).
            verbose: Include confidence.

        Returns:
            Dictionary for CSV row.
        """
        if result.success and result.data:
            data = result.data
            row = {
                "source_file": str(data.source_file),
                "surname": data.surname or "",
                "given_names": data.given_names or "",
                "date_of_birth": (
                    data.date_of_birth.isoformat() if data.date_of_birth else ""
                ),
                "nationality": data.nationality or "",
                "passport_number": data.passport_number or "",
                "expiry_date": data.expiry_date.isoformat() if data.expiry_date else "",
                "sex": data.sex or "",
                "place_of_birth": data.place_of_birth or "",
                "mrz_type": data.mrz_type or "",
                "mrz_valid": str(data.mrz_valid),
                "error": "",
            }
            if verbose:
                row["confidence"] = (
                    str(data.confidence) if data.confidence is not None else ""
                )
        else:
            # Failed extraction
            row = {
                "source_file": str(result.source_file),
                "surname": "",
                "given_names": "",
                "date_of_birth": "",
                "nationality": "",
                "passport_number": "",
                "expiry_date": "",
                "sex": "",
                "place_of_birth": "",
                "mrz_type": "",
                "mrz_valid": "",
                "error": result.error or "Unknown error",
            }
            if verbose:
                row["confidence"] = ""

        return row
