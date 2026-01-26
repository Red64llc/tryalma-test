"""Tests for FormPopulationService.

TDD tests for Tasks 6.1 and 6.2:
- 6.1: Service orchestration (Requirements: 8.1, 11.1, 11.2, 11.4)
- 6.2: Population workflow with delays and error collection (Requirements: 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 11.3)
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, call
import time

import pytest

from tryalma.form_populator.service import (
    FormPopulationService,
    PopulationConfig,
)
from tryalma.form_populator.models import FieldStatus, FieldResult
from tryalma.form_populator.reporter import PopulationReport
from tryalma.form_populator.field_mapping_config import (
    FieldMapping,
    FieldMappingConfig,
    FieldType,
)
from tryalma.form_populator.exceptions import (
    FormPopulationError,
    NavigationError,
    FormNotFoundError,
)


class TestPopulationConfig:
    """Test the PopulationConfig dataclass."""

    def test_default_config(self):
        """PopulationConfig has sensible defaults."""
        config = PopulationConfig()

        assert config.headless is True
        assert config.timeout_ms == 30000
        assert config.inter_field_delay_ms == 50
        assert config.retry_count == 3
        assert config.debug_mode is False

    def test_custom_config(self):
        """PopulationConfig accepts custom values."""
        config = PopulationConfig(
            headless=False,
            timeout_ms=60000,
            inter_field_delay_ms=100,
            retry_count=5,
            debug_mode=True,
        )

        assert config.headless is False
        assert config.timeout_ms == 60000
        assert config.inter_field_delay_ms == 100
        assert config.retry_count == 5
        assert config.debug_mode is True


class TestFormPopulationServiceCreation:
    """Test FormPopulationService initialization."""

    def test_service_creation(self):
        """FormPopulationService can be created."""
        service = FormPopulationService()
        assert service is not None

    def test_service_with_custom_config(self):
        """FormPopulationService accepts custom configuration."""
        config = PopulationConfig(headless=False, timeout_ms=60000)
        service = FormPopulationService(config=config)

        assert service._config.headless is False
        assert service._config.timeout_ms == 60000

    def test_service_with_custom_mapping_config(self):
        """FormPopulationService accepts custom field mapping configuration."""
        custom_mappings = [
            FieldMapping("field1", "input#field1", FieldType.TEXT),
        ]
        mapping_config = FieldMappingConfig(mappings=custom_mappings)
        service = FormPopulationService(mapping_config=mapping_config)

        assert len(service._mapping_config.mappings) == 1


class TestServiceValidation:
    """Test extracted data validation (Requirement 11.2)."""

    def test_validate_extracted_data_returns_empty_for_valid_data(self):
        """validate_extracted_data returns empty list when all required fields present."""
        service = FormPopulationService()
        # Provide all required fields from the default mapping config
        # Keys match webapp's FieldMapper output
        extracted_data = {
            "attorney_surname": "Smith",
            "attorney_given_names": "Barbara",
            "applicant_surname": "Doe",
            "applicant_given_names": "Jane",
        }

        missing = service.validate_extracted_data(extracted_data)

        assert missing == []

    def test_validate_extracted_data_returns_missing_fields(self):
        """validate_extracted_data returns list of missing required fields."""
        service = FormPopulationService()
        extracted_data = {
            "attorney_surname": "Smith",
            # Missing other required fields
        }

        missing = service.validate_extracted_data(extracted_data)

        assert "attorney_given_names" in missing
        assert "applicant_surname" in missing
        assert "applicant_given_names" in missing

    def test_validate_extracted_data_treats_none_as_missing(self):
        """validate_extracted_data treats None values as missing."""
        service = FormPopulationService()
        extracted_data = {
            "attorney_surname": None,
            "attorney_given_names": "John",
        }

        missing = service.validate_extracted_data(extracted_data)

        assert "attorney_surname" in missing


class TestServicePopulateMethod:
    """Test the main populate method (Requirements 8.1, 11.1, 11.4)."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_returns_population_report(self, mock_browser_class):
        """populate returns a PopulationReport."""
        # Setup mock
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_context = MagicMock()
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        service = FormPopulationService()
        extracted_data = {"attorney_surname": "Smith"}
        form_url = "https://example.com/form"

        report = service.populate(form_url, extracted_data)

        assert isinstance(report, PopulationReport)
        assert report.form_url == form_url

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_launches_browser(self, mock_browser_class):
        """populate launches browser with configured settings."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        config = PopulationConfig(headless=False, timeout_ms=60000)
        service = FormPopulationService(config=config)
        extracted_data = {"attorney_surname": "Smith"}

        service.populate("https://example.com/form", extracted_data)

        mock_browser_class.assert_called_once_with(headless=False, timeout_ms=60000)
        mock_browser.launch.assert_called_once()

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_navigates_to_form_url(self, mock_browser_class):
        """populate navigates to the form URL."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        service = FormPopulationService()
        form_url = "https://mendrika-alma.github.io/form-submission/"

        service.populate(form_url, {"attorney_surname": "Smith"})

        mock_browser.navigate.assert_called_once_with(form_url)

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_waits_for_form_ready(self, mock_browser_class):
        """populate waits for form to be ready before populating."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        service = FormPopulationService()

        service.populate("https://example.com/form", {"attorney_surname": "Smith"})

        mock_browser.wait_for_form_ready.assert_called_once()

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_closes_browser_after_completion(self, mock_browser_class):
        """populate closes browser after completion."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_exit = MagicMock(return_value=False)
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = mock_exit

        service = FormPopulationService()

        service.populate("https://example.com/form", {"attorney_surname": "Smith"})

        # Context manager __exit__ should be called
        mock_exit.assert_called_once()


class TestServiceFieldPopulation:
    """Test field population workflow (Requirements 8.1, 8.2)."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_fills_text_field(self, mock_browser_class):
        """populate fills text fields from extracted data."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None  # No maxlength

        # Use minimal mapping - field_id must match extracted_data key
        mapping = FieldMappingConfig(mappings=[
            FieldMapping("attorney_surname", "input[name='familyName']", FieldType.TEXT),
        ])
        service = FormPopulationService(mapping_config=mapping)

        service.populate("https://example.com/form", {"attorney_surname": "Smith"})

        mock_browser.fill.assert_called_with("input[name='familyName']", "Smith")

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_reports_populated_fields(self, mock_browser_class):
        """populate reports successfully populated fields."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("attorney_surname", "input[name='familyName']", FieldType.TEXT),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate("https://example.com/form", {"attorney_surname": "Smith"})

        assert len(report.populated_fields) == 1
        assert report.populated_fields[0].field_id == "attorney_surname"
        assert report.populated_fields[0].value == "Smith"


class TestSignatureFieldExclusion:
    """Test signature field exclusion (Requirements 9.1, 9.2, 9.3)."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_never_populates_signature_fields(self, mock_browser_class):
        """populate never populates signature fields."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("attorney_surname", "input[name='familyName']", FieldType.TEXT),
            FieldMapping("client_signature", "input[name='clientSignature']", FieldType.SIGNATURE, is_signature=True),
            FieldMapping("client_signature_date", "input[name='clientSignatureDate']", FieldType.SIGNATURE, is_signature=True),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {
                "attorney_surname": "Smith",
                "client_signature": "John Doe",
                "client_signature_date": "2026-01-25",
            },
        )

        # Should only populate 1 field (the text field)
        assert len(report.populated_fields) == 1
        assert report.populated_fields[0].field_id == "attorney_surname"

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_reports_signature_fields_as_manual_required(self, mock_browser_class):
        """populate reports signature fields as requiring manual attention."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("client_signature", "input[name='clientSignature']", FieldType.SIGNATURE, is_signature=True),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate("https://example.com/form", {})

        assert len(report.manual_attention_fields) == 1
        assert report.manual_attention_fields[0].field_id == "client_signature"


class TestNoFormSubmission:
    """Test that form is never submitted (Requirement 8.5)."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_never_clicks_submit_button(self, mock_browser_class):
        """populate never interacts with submit buttons."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        service = FormPopulationService()

        service.populate("https://example.com/form", {"attorney_surname": "Smith"})

        # Should never call click on submit button
        # Check that no button-related methods were called
        for call_item in mock_browser.method_calls:
            method_name = call_item[0]
            assert "submit" not in method_name.lower()
            # Also check no click calls at all
            assert method_name != "click"


class TestDelaysBetweenFields:
    """Test configurable delays between field interactions (Requirement 8.3)."""

    @patch("tryalma.form_populator.service.BrowserController")
    @patch("tryalma.form_populator.service.time.sleep")
    def test_populate_adds_delay_between_fields(self, mock_sleep, mock_browser_class):
        """populate adds configurable delay between field interactions."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("field1", "input#field1", FieldType.TEXT),
            FieldMapping("field2", "input#field2", FieldType.TEXT),
            FieldMapping("field3", "input#field3", FieldType.TEXT),
        ])
        config = PopulationConfig(inter_field_delay_ms=100)
        service = FormPopulationService(config=config, mapping_config=mapping)

        service.populate(
            "https://example.com/form",
            {"field1": "value1", "field2": "value2", "field3": "value3"},
        )

        # Should sleep between fields (3 fields = 2 sleeps between them)
        assert mock_sleep.call_count >= 2
        mock_sleep.assert_called_with(0.1)  # 100ms = 0.1s


class TestErrorCollection:
    """Test error collection during population (Requirements 8.4, 11.3)."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_continues_after_field_error(self, mock_browser_class):
        """populate continues populating after individual field error."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None
        # First fill succeeds, second fails, third succeeds
        mock_browser.fill.side_effect = [None, Exception("Element not found"), None]

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("field1", "input#field1", FieldType.TEXT),
            FieldMapping("field2", "input#field2", FieldType.TEXT),
            FieldMapping("field3", "input#field3", FieldType.TEXT),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {"field1": "value1", "field2": "value2", "field3": "value3"},
        )

        # Should have 2 populated and 1 error
        assert len(report.populated_fields) == 2
        assert len(report.error_fields) == 1
        assert report.error_fields[0].field_id == "field2"

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_reports_missing_data_fields(self, mock_browser_class):
        """populate reports fields with missing data as skipped."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("field1", "input#field1", FieldType.TEXT),
            FieldMapping("field2", "input#field2", FieldType.TEXT),
        ])
        service = FormPopulationService(mapping_config=mapping)

        # Only provide data for field1
        report = service.populate(
            "https://example.com/form",
            {"field1": "value1"},
        )

        assert len(report.populated_fields) == 1
        assert len(report.skipped_fields) == 1
        assert report.skipped_fields[0].field_id == "field2"

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_handles_incomplete_data(self, mock_browser_class):
        """populate populates available fields when data is incomplete."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("field1", "input#field1", FieldType.TEXT, required=True),
            FieldMapping("field2", "input#field2", FieldType.TEXT),
            FieldMapping("field3", "input#field3", FieldType.TEXT, required=True),
        ])
        service = FormPopulationService(mapping_config=mapping)

        # Only provide data for field2 (missing both required fields)
        report = service.populate(
            "https://example.com/form",
            {"field2": "value2"},
        )

        # Should populate field2 even though required fields are missing
        assert len(report.populated_fields) == 1
        assert report.populated_fields[0].field_id == "field2"


class TestReportGeneration:
    """Test that populate returns comprehensive report."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_report_includes_form_url(self, mock_browser_class):
        """populate report includes the form URL."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        service = FormPopulationService()
        form_url = "https://mendrika-alma.github.io/form-submission/"

        report = service.populate(form_url, {"attorney_surname": "Smith"})

        assert report.form_url == form_url

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_report_has_to_dict_method(self, mock_browser_class):
        """populate report has to_dict method for serialization."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("field1", "input#field1", FieldType.TEXT),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {"field1": "value1"},
        )

        result = report.to_dict()
        assert "success" in result
        assert "form_url" in result
        assert "populated_fields" in result


class TestFieldTypeHandling:
    """Test that different field types are handled correctly."""

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_handles_checkbox_field(self, mock_browser_class):
        """populate handles checkbox fields correctly."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("is_attorney", "input[name='isAttorney']", FieldType.CHECKBOX),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {"is_attorney": True},
        )

        mock_browser.check.assert_called_once_with("input[name='isAttorney']")
        assert len(report.populated_fields) == 1

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_handles_dropdown_field(self, mock_browser_class):
        """populate handles dropdown/select fields correctly."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("state", "select[name='state']", FieldType.DROPDOWN),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {"state": "California"},
        )

        mock_browser.select_option.assert_called()
        assert len(report.populated_fields) == 1

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_handles_radio_field(self, mock_browser_class):
        """populate handles radio button fields correctly."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("sex", "input[name='sex']", FieldType.RADIO),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {"sex": "M"},
        )

        # Radio buttons use check method with value selector
        mock_browser.check.assert_called()
        assert len(report.populated_fields) == 1

    @patch("tryalma.form_populator.service.BrowserController")
    def test_populate_handles_date_field(self, mock_browser_class):
        """populate handles date fields correctly."""
        mock_browser = MagicMock()
        mock_browser_class.return_value = mock_browser
        mock_browser.launch.return_value.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.launch.return_value.__exit__ = MagicMock(return_value=False)
        mock_browser.get_attribute.return_value = None

        mapping = FieldMappingConfig(mappings=[
            FieldMapping("date_of_birth", "input[name='dateOfBirth']", FieldType.DATE),
        ])
        service = FormPopulationService(mapping_config=mapping)

        report = service.populate(
            "https://example.com/form",
            {"date_of_birth": "1990-01-15"},
        )

        # Date fields use fill method with formatted date
        mock_browser.fill.assert_called()
        assert len(report.populated_fields) == 1
