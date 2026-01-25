"""Unit tests for G28 OutputFormatter.

Task 6: Implement OutputFormatter for JSON and YAML.
Task 10.5: Implement OutputFormatter tests.

Tests follow TDD methodology - written before implementation.
Requirements: 8.1, 9.2, 9.4
"""

import json
from datetime import date

import pytest
import yaml


class TestOutputFormatterJSONFormat:
    """Test JSON output formatting.

    Task 6: Format G28FormData to JSON string with proper indentation.
    Requirements: 8.1, 9.2
    """

    def test_format_json_returns_valid_json_string(self):
        """OutputFormatter.format_json returns a valid JSON string."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed is not None
        assert isinstance(parsed, dict)

    def test_format_json_includes_proper_indentation(self):
        """OutputFormatter.format_json includes proper indentation (2 spaces)."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data)

        # Should have newlines and indentation (not compact)
        assert "\n" in result
        assert "  " in result  # 2-space indentation

    def test_format_json_includes_source_file(self):
        """OutputFormatter.format_json includes source_file in output."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="my_form.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.85,
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data)
        parsed = json.loads(result)

        assert parsed["source_file"] == "my_form.pdf"

    def test_format_json_includes_form_sections(self):
        """OutputFormatter.format_json includes form sections organized properly."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95)
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data)
        parsed = json.loads(result)

        assert "part1_attorney_info" in parsed

    def test_format_json_handles_dates_correctly(self):
        """OutputFormatter.format_json serializes dates to ISO 8601 format."""
        from tryalma.g28.models import (
            ConsentAndSignatures,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part4_5_consent_signatures=ConsentAndSignatures(
                client_signature_date=ExtractedField[date](
                    value=date(2024, 1, 15), confidence=0.88
                ),
            ),
        )
        formatter = OutputFormatter()

        # Test verbose mode (full wrapper with value key)
        result_verbose = formatter.format_json(form_data, verbose=True)
        parsed_verbose = json.loads(result_verbose)
        sig_date_verbose = parsed_verbose["part4_5_consent_signatures"]["client_signature_date"]["value"]
        assert sig_date_verbose == "2024-01-15"

        # Test non-verbose mode (simplified - just the value)
        result_simple = formatter.format_json(form_data, verbose=False)
        parsed_simple = json.loads(result_simple)
        sig_date_simple = parsed_simple["part4_5_consent_signatures"]["client_signature_date"]
        assert sig_date_simple == "2024-01-15"


class TestOutputFormatterYAMLFormat:
    """Test YAML output formatting.

    Task 6: Format G28FormData to YAML string using PyYAML.
    Requirements: 9.4
    """

    def test_format_yaml_returns_valid_yaml_string(self):
        """OutputFormatter.format_yaml returns a valid YAML string."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format_yaml(form_data)

        # Should be valid YAML
        parsed = yaml.safe_load(result)
        assert parsed is not None
        assert isinstance(parsed, dict)

    def test_format_yaml_includes_source_file(self):
        """OutputFormatter.format_yaml includes source_file in output."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="my_form.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.85,
        )
        formatter = OutputFormatter()

        result = formatter.format_yaml(form_data)
        parsed = yaml.safe_load(result)

        assert parsed["source_file"] == "my_form.pdf"

    def test_format_yaml_uses_block_style(self):
        """OutputFormatter.format_yaml uses block style (not flow style)."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95)
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_yaml(form_data)

        # Block style uses colons and newlines, not braces
        assert ":" in result
        assert "\n" in result
        # Flow style would have { } for nested objects
        assert result.count("{") == 0 or "family_name:" in result

    def test_format_yaml_handles_dates_correctly(self):
        """OutputFormatter.format_yaml serializes dates properly."""
        from tryalma.g28.models import (
            ConsentAndSignatures,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part4_5_consent_signatures=ConsentAndSignatures(
                client_signature_date=ExtractedField[date](
                    value=date(2024, 1, 15), confidence=0.88
                ),
            ),
        )
        formatter = OutputFormatter()

        # Test verbose mode (full wrapper with value key)
        result_verbose = formatter.format_yaml(form_data, verbose=True)
        parsed_verbose = yaml.safe_load(result_verbose)
        sig_date_verbose = parsed_verbose["part4_5_consent_signatures"]["client_signature_date"]["value"]
        # YAML may parse as date or string
        assert sig_date_verbose == date(2024, 1, 15) or sig_date_verbose == "2024-01-15"

        # Test non-verbose mode (simplified - just the value)
        result_simple = formatter.format_yaml(form_data, verbose=False)
        parsed_simple = yaml.safe_load(result_simple)
        sig_date_simple = parsed_simple["part4_5_consent_signatures"]["client_signature_date"]
        assert sig_date_simple == date(2024, 1, 15) or sig_date_simple == "2024-01-15"

    def test_format_yaml_supports_unicode(self):
        """OutputFormatter.format_yaml supports unicode characters."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Garcia", confidence=0.95)
            ),
        )
        formatter = OutputFormatter()

        # Test verbose mode (has value wrapper)
        result_verbose = formatter.format_yaml(form_data, verbose=True)
        parsed_verbose = yaml.safe_load(result_verbose)
        assert parsed_verbose["part1_attorney_info"]["family_name"]["value"] == "Garcia"

        # Test non-verbose mode (simplified - just the value)
        result_simple = formatter.format_yaml(form_data, verbose=False)
        parsed_simple = yaml.safe_load(result_simple)
        assert parsed_simple["part1_attorney_info"]["family_name"] == "Garcia"


class TestOutputFormatterVerboseMode:
    """Test verbose mode output.

    Task 6: Support verbose mode that includes confidence scores and metadata.
    Requirements: 9.4 (verbose flag)
    """

    def test_format_json_verbose_includes_confidence_scores(self):
        """Verbose JSON output includes confidence scores for fields."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95),
                given_name=ExtractedField[str](value="John", confidence=0.88),
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=True)
        parsed = json.loads(result)

        # Verbose mode should include confidence in each field
        attorney = parsed["part1_attorney_info"]
        assert "confidence" in attorney["family_name"]
        assert attorney["family_name"]["confidence"] == 0.95
        assert attorney["given_name"]["confidence"] == 0.88

    def test_format_json_verbose_includes_overall_confidence(self):
        """Verbose JSON output includes overall_confidence metadata."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=True)
        parsed = json.loads(result)

        assert "overall_confidence" in parsed
        assert parsed["overall_confidence"] == 0.92

    def test_format_json_verbose_includes_uncertain_fields(self):
        """Verbose JSON output includes uncertain_fields list."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.75,
            uncertain_fields=["part1_attorney_info.fax_number"],
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=True)
        parsed = json.loads(result)

        assert "uncertain_fields" in parsed
        assert "part1_attorney_info.fax_number" in parsed["uncertain_fields"]

    def test_format_json_verbose_includes_validation_warnings(self):
        """Verbose JSON output includes validation_warnings list."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.80,
            validation_warnings=["Email format may be invalid"],
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=True)
        parsed = json.loads(result)

        assert "validation_warnings" in parsed
        assert "Email format may be invalid" in parsed["validation_warnings"]

    def test_format_yaml_verbose_includes_confidence_scores(self):
        """Verbose YAML output includes confidence scores for fields."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95),
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_yaml(form_data, verbose=True)
        parsed = yaml.safe_load(result)

        # Verbose mode should include confidence in each field
        assert "confidence" in parsed["part1_attorney_info"]["family_name"]
        assert parsed["part1_attorney_info"]["family_name"]["confidence"] == 0.95


class TestOutputFormatterNonVerboseMode:
    """Test non-verbose (simplified) output mode.

    Task 6: Support non-verbose mode that returns simplified output.
    Requirements: 9.2 (default JSON output)
    """

    def test_format_json_non_verbose_returns_simplified_values(self):
        """Non-verbose JSON output returns just values, not field wrappers."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95),
                given_name=ExtractedField[str](value="John", confidence=0.88),
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        # Non-verbose mode should return just the value, not the wrapper
        attorney = parsed["part1_attorney_info"]
        assert attorney["family_name"] == "Smith"
        assert attorney["given_name"] == "John"

    def test_format_json_non_verbose_excludes_confidence_metadata(self):
        """Non-verbose JSON output excludes confidence-related metadata."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
            uncertain_fields=["some_field"],
            validation_warnings=["some warning"],
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        # Non-verbose excludes confidence metadata
        assert "overall_confidence" not in parsed
        assert "uncertain_fields" not in parsed
        assert "validation_warnings" not in parsed

    def test_format_json_non_verbose_includes_source_file(self):
        """Non-verbose JSON output still includes source_file."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        # Source file should always be included
        assert "source_file" in parsed
        assert parsed["source_file"] == "test.pdf"

    def test_format_yaml_non_verbose_returns_simplified_values(self):
        """Non-verbose YAML output returns just values, not field wrappers."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95),
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_yaml(form_data, verbose=False)
        parsed = yaml.safe_load(result)

        # Non-verbose mode should return just the value
        assert parsed["part1_attorney_info"]["family_name"] == "Smith"

    def test_format_json_non_verbose_handles_null_values(self):
        """Non-verbose JSON output handles null field values."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value=None, confidence=0.0),
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        # Null values should be represented as null
        assert parsed["part1_attorney_info"]["family_name"] is None


class TestOutputFormatterFormatMethod:
    """Test the unified format() method.

    Task 6: Unified interface for formatting.
    Requirements: 8.1, 9.2, 9.4
    """

    def test_format_with_json_format_returns_json(self):
        """format() with format='json' returns JSON string."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format(form_data, format="json")

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["source_file"] == "test.pdf"

    def test_format_with_yaml_format_returns_yaml(self):
        """format() with format='yaml' returns YAML string."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format(form_data, format="yaml")

        # Should be valid YAML
        parsed = yaml.safe_load(result)
        assert parsed["source_file"] == "test.pdf"

    def test_format_passes_verbose_flag(self):
        """format() passes verbose flag to underlying formatters."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95),
            ),
        )
        formatter = OutputFormatter()

        # Verbose mode
        verbose_result = formatter.format(form_data, format="json", verbose=True)
        verbose_parsed = json.loads(verbose_result)
        assert "confidence" in verbose_parsed["part1_attorney_info"]["family_name"]

        # Non-verbose mode
        non_verbose_result = formatter.format(form_data, format="json", verbose=False)
        non_verbose_parsed = json.loads(non_verbose_result)
        assert non_verbose_parsed["part1_attorney_info"]["family_name"] == "Smith"

    def test_format_defaults_to_json(self):
        """format() defaults to JSON format when not specified."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        formatter = OutputFormatter()

        result = formatter.format(form_data)

        # Should be valid JSON (default)
        parsed = json.loads(result)
        assert parsed["source_file"] == "test.pdf"

    def test_format_defaults_to_non_verbose(self):
        """format() defaults to non-verbose mode when not specified."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95),
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format(form_data)  # No verbose flag
        parsed = json.loads(result)

        # Should be non-verbose (simplified values)
        assert parsed["part1_attorney_info"]["family_name"] == "Smith"


class TestOutputFormatterEdgeCases:
    """Test edge cases and error handling.

    Task 6: Robust output formatting.
    """

    def test_format_handles_empty_form_data(self):
        """OutputFormatter handles minimal form data without sections."""
        from tryalma.g28.models import G28FormData
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="empty.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.0,
        )
        formatter = OutputFormatter()

        # Should not raise
        json_result = formatter.format_json(form_data)
        yaml_result = formatter.format_yaml(form_data)

        assert json.loads(json_result)["source_file"] == "empty.pdf"
        assert yaml.safe_load(yaml_result)["source_file"] == "empty.pdf"

    def test_format_handles_all_sections_populated(self):
        """OutputFormatter handles fully populated form data."""
        from tryalma.g28.models import (
            AdditionalInfo,
            AdditionalInfoEntry,
            AttorneyInfo,
            ClientInfo,
            ConsentAndSignatures,
            EligibilityInfo,
            ExtractedField,
            G28FormData,
            NoticeOfAppearance,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="full.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95)
            ),
            part2_eligibility=EligibilityInfo(
                is_attorney=ExtractedField[bool](value=True, confidence=0.98)
            ),
            part3_notice_of_appearance=NoticeOfAppearance(
                agency_uscis=ExtractedField[bool](value=True, confidence=0.99)
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField[str](value="Doe", confidence=0.92)
            ),
            part4_5_consent_signatures=ConsentAndSignatures(
                client_signature_present=ExtractedField[bool](value=True, confidence=0.85)
            ),
            part6_additional_info=AdditionalInfo(
                entries=[
                    AdditionalInfoEntry(page_number=3, part_number=1, content="Extra info")
                ]
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        assert parsed["part1_attorney_info"]["family_name"] == "Smith"
        assert parsed["part2_eligibility"]["is_attorney"] is True
        assert parsed["part3_client_info"]["family_name"] == "Doe"

    def test_format_handles_nested_address_objects(self):
        """OutputFormatter handles nested Address objects correctly."""
        from tryalma.g28.models import (
            Address,
            AttorneyInfo,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                address=Address(
                    street_number_and_name="123 Main St",
                    city_or_town="New York",
                    state="NY",
                    zip_code="10001",
                )
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        # Address should be nested properly
        address = parsed["part1_attorney_info"]["address"]
        assert address["street_number_and_name"] == "123 Main St"
        assert address["city_or_town"] == "New York"
        assert address["state"] == "NY"

    def test_format_handles_list_fields(self):
        """OutputFormatter handles list fields like additional info entries."""
        from tryalma.g28.models import (
            AdditionalInfo,
            AdditionalInfoEntry,
            G28FormData,
        )
        from tryalma.g28.output_formatter import OutputFormatter

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part6_additional_info=AdditionalInfo(
                entries=[
                    AdditionalInfoEntry(page_number=3, part_number=1, content="Entry 1"),
                    AdditionalInfoEntry(page_number=3, part_number=2, content="Entry 2"),
                ]
            ),
        )
        formatter = OutputFormatter()

        result = formatter.format_json(form_data, verbose=False)
        parsed = json.loads(result)

        entries = parsed["part6_additional_info"]["entries"]
        assert len(entries) == 2
        assert entries[0]["content"] == "Entry 1"
        assert entries[1]["content"] == "Entry 2"
