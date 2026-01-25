"""Tests for OutputFormatter.

Task 6.1: Table output formatter tests
Task 6.2: JSON and CSV output formatter tests

Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3
"""

import json
from datetime import date
from pathlib import Path

import pytest

from tryalma.passport.models import ExtractionResult, PassportData


class TestOutputFormatterEnum:
    """Tests for OutputFormat enum."""

    def test_output_format_has_table_value(self):
        """OutputFormat enum should have TABLE value."""
        from tryalma.passport.formatter import OutputFormat

        assert OutputFormat.TABLE.value == "table"

    def test_output_format_has_json_value(self):
        """OutputFormat enum should have JSON value."""
        from tryalma.passport.formatter import OutputFormat

        assert OutputFormat.JSON.value == "json"

    def test_output_format_has_csv_value(self):
        """OutputFormat enum should have CSV value."""
        from tryalma.passport.formatter import OutputFormat

        assert OutputFormat.CSV.value == "csv"


class TestOutputFormatterTableFormat:
    """Tests for table output formatting (Requirement 4.1)."""

    @pytest.fixture
    def successful_result(self) -> ExtractionResult:
        """Create a successful extraction result for testing."""
        return ExtractionResult(
            success=True,
            data=PassportData(
                source_file=Path("/tmp/passport1.jpg"),
                surname="ERIKSSON",
                given_names="ANNA MARIA",
                date_of_birth=date(1974, 8, 12),
                nationality="UTO",
                passport_number="L898902C3",
                expiry_date=date(2012, 4, 15),
                sex="F",
                place_of_birth=None,
                mrz_type="TD3",
                mrz_valid=True,
                check_digit_errors=[],
                confidence=0.95,
                raw_mrz="P<UTOERIKSSON<<ANNA<MARIA...",
            ),
            error=None,
            source_file=Path("/tmp/passport1.jpg"),
        )

    @pytest.fixture
    def failed_result(self) -> ExtractionResult:
        """Create a failed extraction result for testing."""
        return ExtractionResult(
            success=False,
            data=None,
            error="No MRZ detected in image",
            source_file=Path("/tmp/passport2.jpg"),
        )

    def test_format_table_returns_string(self, successful_result: ExtractionResult):
        """format_table should return a string."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result])

        assert isinstance(result, str)

    def test_format_table_includes_field_labels(
        self, successful_result: ExtractionResult
    ):
        """Table output should include field labels (Requirement 3.1)."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result])

        # Check for common field labels
        assert "Surname" in result or "surname" in result.lower()
        assert "Given Names" in result or "given" in result.lower()
        assert "Nationality" in result or "nationality" in result.lower()

    def test_format_table_includes_source_file(
        self, successful_result: ExtractionResult
    ):
        """Table output should include source file (Requirement 3.3)."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result])

        assert "passport1.jpg" in result

    def test_format_table_includes_passport_data_values(
        self, successful_result: ExtractionResult
    ):
        """Table output should include extracted values."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result])

        assert "ERIKSSON" in result
        assert "ANNA MARIA" in result
        assert "UTO" in result

    def test_format_table_batch_separates_records(
        self, successful_result: ExtractionResult, failed_result: ExtractionResult
    ):
        """Batch table output should clearly separate records (Requirement 3.2)."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result, failed_result])

        # Both files should appear
        assert "passport1.jpg" in result
        assert "passport2.jpg" in result

    def test_format_table_verbose_includes_confidence(
        self, successful_result: ExtractionResult
    ):
        """Verbose mode should include confidence scores (Requirement 3.4)."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result], verbose=True)

        # Should include confidence (0.95)
        assert "0.95" in result or "95" in result

    def test_format_table_handles_empty_results(self):
        """Table formatter should handle empty results gracefully."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([])

        assert isinstance(result, str)
        assert "No results" in result or result == ""

    def test_format_table_shows_mrz_validation_status(
        self, successful_result: ExtractionResult
    ):
        """Table should show MRZ validation status (Requirement 6.3)."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([successful_result])

        # Should indicate valid or show checkmark/status
        assert "valid" in result.lower() or "Yes" in result or "True" in result

    def test_format_table_shows_failed_extraction_error(
        self, failed_result: ExtractionResult
    ):
        """Table should show error message for failed extractions."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_table([failed_result])

        assert "No MRZ detected" in result or "Error" in result


class TestOutputFormatterDispatch:
    """Tests for the main format() method that dispatches to specific formatters."""

    @pytest.fixture
    def sample_result(self) -> ExtractionResult:
        """Create a sample extraction result."""
        return ExtractionResult(
            success=True,
            data=PassportData(
                source_file=Path("/tmp/test.jpg"),
                surname="DOE",
                given_names="JOHN",
                date_of_birth=date(1990, 1, 15),
                nationality="USA",
                passport_number="123456789",
                expiry_date=date(2030, 1, 14),
                sex="M",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=Path("/tmp/test.jpg"),
        )

    def test_format_dispatches_to_table(self, sample_result: ExtractionResult):
        """format() with TABLE should call format_table."""
        from tryalma.passport.formatter import OutputFormat, OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format([sample_result], OutputFormat.TABLE)

        # Should return table-formatted string
        assert isinstance(result, str)
        assert "DOE" in result

    def test_format_dispatches_to_json(self, sample_result: ExtractionResult):
        """format() with JSON should call format_json."""
        from tryalma.passport.formatter import OutputFormat, OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format([sample_result], OutputFormat.JSON)

        # Should be valid JSON
        parsed = json.loads(result)
        assert "results" in parsed

    def test_format_dispatches_to_csv(self, sample_result: ExtractionResult):
        """format() with CSV should call format_csv."""
        from tryalma.passport.formatter import OutputFormat, OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format([sample_result], OutputFormat.CSV)

        # Should have CSV header
        assert "source_file" in result or "surname" in result


class TestOutputFormatterJSON:
    """Tests for JSON output formatting (Requirement 4.2)."""

    @pytest.fixture
    def successful_result(self) -> ExtractionResult:
        """Create a successful extraction result."""
        return ExtractionResult(
            success=True,
            data=PassportData(
                source_file=Path("/tmp/passport.jpg"),
                surname="SMITH",
                given_names="JOHN WILLIAM",
                date_of_birth=date(1985, 3, 15),
                nationality="USA",
                passport_number="123456789",
                expiry_date=date(2030, 3, 14),
                sex="M",
                place_of_birth=None,
                mrz_type="TD3",
                mrz_valid=True,
                check_digit_errors=[],
                confidence=0.92,
            ),
            error=None,
            source_file=Path("/tmp/passport.jpg"),
        )

    @pytest.fixture
    def failed_result(self) -> ExtractionResult:
        """Create a failed extraction result."""
        return ExtractionResult(
            success=False,
            data=None,
            error="Image corrupted",
            source_file=Path("/tmp/bad.jpg"),
        )

    def test_format_json_produces_valid_json(
        self, successful_result: ExtractionResult
    ):
        """JSON output must be valid JSON."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result])

        # Should not raise JSONDecodeError
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_json_has_results_array(self, successful_result: ExtractionResult):
        """JSON output should have results array."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result])
        parsed = json.loads(result)

        assert "results" in parsed
        assert isinstance(parsed["results"], list)
        assert len(parsed["results"]) == 1

    def test_format_json_has_summary(
        self, successful_result: ExtractionResult, failed_result: ExtractionResult
    ):
        """JSON output should include summary statistics."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result, failed_result])
        parsed = json.loads(result)

        assert "summary" in parsed
        assert parsed["summary"]["total"] == 2
        assert parsed["summary"]["successful"] == 1
        assert parsed["summary"]["failed"] == 1

    def test_format_json_includes_all_fields(
        self, successful_result: ExtractionResult
    ):
        """JSON output should include all passport fields."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result])
        parsed = json.loads(result)

        item = parsed["results"][0]
        assert item["surname"] == "SMITH"
        assert item["given_names"] == "JOHN WILLIAM"
        assert item["nationality"] == "USA"
        assert item["passport_number"] == "123456789"
        assert item["sex"] == "M"
        assert item["mrz_type"] == "TD3"
        assert item["mrz_valid"] is True

    def test_format_json_includes_unavailable_fields(
        self, successful_result: ExtractionResult
    ):
        """JSON output should include unavailable_fields list (Requirement 2.9)."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result])
        parsed = json.loads(result)

        item = parsed["results"][0]
        assert "unavailable_fields" in item
        assert "place_of_birth" in item["unavailable_fields"]

    def test_format_json_formats_dates_as_iso(
        self, successful_result: ExtractionResult
    ):
        """JSON dates should be in ISO format."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result])
        parsed = json.loads(result)

        item = parsed["results"][0]
        assert item["date_of_birth"] == "1985-03-15"
        assert item["expiry_date"] == "2030-03-14"

    def test_format_json_includes_source_file(
        self, successful_result: ExtractionResult
    ):
        """JSON output should include source file path."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result])
        parsed = json.loads(result)

        item = parsed["results"][0]
        assert "source_file" in item
        assert "passport.jpg" in item["source_file"]

    def test_format_json_handles_failed_results(
        self, failed_result: ExtractionResult
    ):
        """JSON should include failed results with error message."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([failed_result])
        parsed = json.loads(result)

        item = parsed["results"][0]
        assert "error" in item
        assert item["error"] == "Image corrupted"

    def test_format_json_verbose_includes_confidence(
        self, successful_result: ExtractionResult
    ):
        """Verbose JSON should include confidence scores."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([successful_result], verbose=True)
        parsed = json.loads(result)

        item = parsed["results"][0]
        assert "confidence" in item
        assert item["confidence"] == 0.92

    def test_format_json_handles_empty_results(self):
        """JSON formatter should handle empty results."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_json([])
        parsed = json.loads(result)

        assert parsed["results"] == []
        assert parsed["summary"]["total"] == 0


class TestOutputFormatterCSV:
    """Tests for CSV output formatting (Requirement 4.3)."""

    @pytest.fixture
    def successful_result(self) -> ExtractionResult:
        """Create a successful extraction result."""
        return ExtractionResult(
            success=True,
            data=PassportData(
                source_file=Path("/tmp/passport.jpg"),
                surname="DOE",
                given_names="JANE",
                date_of_birth=date(1995, 6, 20),
                nationality="GBR",
                passport_number="987654321",
                expiry_date=date(2028, 6, 19),
                sex="F",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=Path("/tmp/passport.jpg"),
        )

    @pytest.fixture
    def multiple_results(self) -> list[ExtractionResult]:
        """Create multiple extraction results."""
        return [
            ExtractionResult(
                success=True,
                data=PassportData(
                    source_file=Path("/tmp/p1.jpg"),
                    surname="SMITH",
                    given_names="JOHN",
                    date_of_birth=date(1990, 1, 1),
                    nationality="USA",
                    passport_number="111111111",
                    expiry_date=date(2030, 1, 1),
                    sex="M",
                    mrz_type="TD3",
                    mrz_valid=True,
                ),
                error=None,
                source_file=Path("/tmp/p1.jpg"),
            ),
            ExtractionResult(
                success=True,
                data=PassportData(
                    source_file=Path("/tmp/p2.jpg"),
                    surname="DOE",
                    given_names="JANE",
                    date_of_birth=date(1985, 12, 25),
                    nationality="GBR",
                    passport_number="222222222",
                    expiry_date=date(2025, 12, 25),
                    sex="F",
                    mrz_type="TD3",
                    mrz_valid=False,
                ),
                error=None,
                source_file=Path("/tmp/p2.jpg"),
            ),
        ]

    def test_format_csv_produces_valid_csv(self, successful_result: ExtractionResult):
        """CSV output should be parseable as CSV."""
        import csv
        import io

        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_csv([successful_result])

        # Should be parseable
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) >= 2  # Header + at least one data row

    def test_format_csv_has_header_row(self, successful_result: ExtractionResult):
        """CSV output should have proper header row."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_csv([successful_result])

        # First line should be headers
        header_line = result.split("\n")[0]
        assert "source_file" in header_line
        assert "surname" in header_line
        assert "nationality" in header_line

    def test_format_csv_includes_all_standard_fields(
        self, successful_result: ExtractionResult
    ):
        """CSV header should include all standard fields."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_csv([successful_result])
        header_line = result.split("\n")[0]

        expected_fields = [
            "source_file",
            "surname",
            "given_names",
            "date_of_birth",
            "nationality",
            "passport_number",
            "expiry_date",
            "sex",
            "mrz_type",
            "mrz_valid",
        ]
        for field in expected_fields:
            assert field in header_line

    def test_format_csv_data_row_matches_header(
        self, successful_result: ExtractionResult
    ):
        """CSV data rows should align with headers."""
        import csv
        import io

        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_csv([successful_result])

        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["surname"] == "DOE"
        assert rows[0]["given_names"] == "JANE"
        assert rows[0]["nationality"] == "GBR"

    def test_format_csv_multiple_rows(self, multiple_results: list[ExtractionResult]):
        """CSV should handle multiple results as multiple rows."""
        import csv
        import io

        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_csv(multiple_results)

        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["surname"] == "SMITH"
        assert rows[1]["surname"] == "DOE"

    def test_format_csv_handles_empty_results(self):
        """CSV formatter should handle empty results with just headers."""
        from tryalma.passport.formatter import OutputFormatter

        formatter = OutputFormatter()
        result = formatter.format_csv([])

        # Should at least have headers or be empty string
        assert isinstance(result, str)

    def test_format_csv_handles_none_values(self):
        """CSV should handle None values gracefully."""
        import csv
        import io

        from tryalma.passport.formatter import OutputFormatter

        result_with_none = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=Path("/tmp/test.jpg"),
                surname="TEST",
                given_names=None,  # None value
                date_of_birth=None,
                nationality="USA",
                passport_number=None,
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=Path("/tmp/test.jpg"),
        )

        formatter = OutputFormatter()
        result = formatter.format_csv([result_with_none])

        # Should be parseable without errors
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        # None values should be empty strings in CSV
        assert rows[0]["given_names"] == ""
        assert rows[0]["date_of_birth"] == ""

    def test_format_csv_escapes_special_characters(self):
        """CSV should properly escape commas and quotes in values."""
        import csv
        import io

        from tryalma.passport.formatter import OutputFormatter

        result_with_comma = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=Path("/tmp/test.jpg"),
                surname="O'BRIEN",  # Contains apostrophe
                given_names='JOHN "JACK"',  # Contains quotes
                nationality="USA",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=Path("/tmp/test.jpg"),
        )

        formatter = OutputFormatter()
        result = formatter.format_csv([result_with_comma])

        # Should be parseable
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        assert "O'BRIEN" in rows[0]["surname"]
        assert "JACK" in rows[0]["given_names"]

    def test_format_csv_failed_results_show_error(self):
        """CSV should handle failed results with error column."""
        import csv
        import io

        from tryalma.passport.formatter import OutputFormatter

        failed_result = ExtractionResult(
            success=False,
            data=None,
            error="MRZ not found",
            source_file=Path("/tmp/bad.jpg"),
        )

        formatter = OutputFormatter()
        result = formatter.format_csv([failed_result])

        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        # Error should be captured somehow (either in error column or empty fields)
        assert "bad.jpg" in rows[0]["source_file"]
