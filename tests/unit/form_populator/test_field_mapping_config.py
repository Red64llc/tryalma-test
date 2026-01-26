"""Tests for FieldMappingConfig - field mapping configuration for form population.

These tests verify:
- Task 3.1: Field mapping data structures (Requirements: 3.1, 3.3, 9.4)
- Task 3.2: Target form field mappings (Requirements: 3.1, 3.3, 9.1, 9.2, 9.3, 9.4)
- Task 3.3: Mapping validation and field retrieval (Requirements: 3.2, 3.4, 3.5)

NOTE: Field mappings are aligned with webapp's FieldMapper output keys:
- attorney_surname, attorney_given_names, attorney_email, attorney_phone
- applicant_surname, applicant_given_names, applicant_dob, applicant_sex
- passport_number, nationality, passport_expiry, a_number
"""

import logging

import pytest

from tryalma.form_populator.field_mapping_config import (
    FieldType,
    FieldMapping,
    FieldMappingConfig,
    FORM_FIELD_MAPPINGS,
)


class TestFieldType:
    """Tests for FieldType enumeration (Task 3.1)."""

    def test_field_type_text_exists(self):
        """FieldType enum should include TEXT type."""
        assert FieldType.TEXT.value == "text"

    def test_field_type_dropdown_exists(self):
        """FieldType enum should include DROPDOWN type."""
        assert FieldType.DROPDOWN.value == "dropdown"

    def test_field_type_checkbox_exists(self):
        """FieldType enum should include CHECKBOX type."""
        assert FieldType.CHECKBOX.value == "checkbox"

    def test_field_type_radio_exists(self):
        """FieldType enum should include RADIO type."""
        assert FieldType.RADIO.value == "radio"

    def test_field_type_date_exists(self):
        """FieldType enum should include DATE type."""
        assert FieldType.DATE.value == "date"

    def test_field_type_signature_exists(self):
        """FieldType enum should include SIGNATURE type for exclusion."""
        assert FieldType.SIGNATURE.value == "signature"


class TestFieldMapping:
    """Tests for FieldMapping dataclass (Task 3.1)."""

    def test_field_mapping_creation_with_required_fields(self):
        """FieldMapping should require field_id, selector, and field_type."""
        mapping = FieldMapping(
            field_id="attorney_surname",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.field_id == "attorney_surname"
        assert mapping.selector == "input[name='familyName']"
        assert mapping.field_type == FieldType.TEXT

    def test_field_mapping_required_flag_defaults_to_false(self):
        """FieldMapping should have required flag defaulting to False."""
        mapping = FieldMapping(
            field_id="attorney_phone",
            selector="input[name='daytimePhone']",
            field_type=FieldType.TEXT,
        )

        assert mapping.required is False

    def test_field_mapping_required_flag_can_be_true(self):
        """FieldMapping should support required=True for mandatory fields."""
        mapping = FieldMapping(
            field_id="attorney_surname",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
            required=True,
        )

        assert mapping.required is True

    def test_field_mapping_is_signature_flag_defaults_to_false(self):
        """FieldMapping should have is_signature flag defaulting to False."""
        mapping = FieldMapping(
            field_id="attorney_surname",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.is_signature is False

    def test_field_mapping_is_signature_flag_for_signature_fields(self):
        """FieldMapping should support is_signature=True for signature fields."""
        mapping = FieldMapping(
            field_id="client_signature",
            selector="input[name='clientSignature']",
            field_type=FieldType.SIGNATURE,
            is_signature=True,
        )

        assert mapping.is_signature is True

    def test_field_mapping_format_pattern_defaults_to_none(self):
        """FieldMapping should have format_pattern defaulting to None."""
        mapping = FieldMapping(
            field_id="attorney_surname",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.format_pattern is None

    def test_field_mapping_format_pattern_for_phone(self):
        """FieldMapping should support format_pattern for phone numbers."""
        mapping = FieldMapping(
            field_id="attorney_phone",
            selector="input[name='daytimePhone']",
            field_type=FieldType.TEXT,
            format_pattern="###-###-####",
        )

        assert mapping.format_pattern == "###-###-####"

    def test_field_mapping_is_frozen(self):
        """FieldMapping should be immutable (frozen dataclass)."""
        mapping = FieldMapping(
            field_id="attorney_surname",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        with pytest.raises(AttributeError):
            mapping.field_id = "different_id"


class TestFormFieldMappings:
    """Tests for FORM_FIELD_MAPPINGS constant (Task 3.2).

    Field mappings are aligned with webapp's FieldMapper output.
    """

    def test_form_field_mappings_is_list(self):
        """FORM_FIELD_MAPPINGS should be a list of FieldMapping objects."""
        assert isinstance(FORM_FIELD_MAPPINGS, list)
        assert all(isinstance(m, FieldMapping) for m in FORM_FIELD_MAPPINGS)

    # Attorney Information (from G-28)
    def test_attorney_surname_mapping_exists(self):
        """Should map attorney surname field (from webapp: attorney_surname)."""
        mapping = _find_mapping_by_field_id("attorney_surname")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_attorney_given_names_mapping_exists(self):
        """Should map attorney given names field (from webapp: attorney_given_names)."""
        mapping = _find_mapping_by_field_id("attorney_given_names")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_attorney_email_mapping_exists(self):
        """Should map attorney email field (from webapp: attorney_email)."""
        mapping = _find_mapping_by_field_id("attorney_email")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT

    def test_attorney_phone_has_format_pattern(self):
        """Should map attorney phone with format pattern."""
        mapping = _find_mapping_by_field_id("attorney_phone")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.format_pattern == "###-###-####"

    # Applicant/Beneficiary Information (from passport and G-28)
    def test_applicant_surname_mapping_exists(self):
        """Should map applicant surname field (from webapp: applicant_surname)."""
        mapping = _find_mapping_by_field_id("applicant_surname")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_applicant_given_names_mapping_exists(self):
        """Should map applicant given names field (from webapp: applicant_given_names)."""
        mapping = _find_mapping_by_field_id("applicant_given_names")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_passport_number_mapping_exists(self):
        """Should map passport number field (from webapp: passport_number)."""
        mapping = _find_mapping_by_field_id("passport_number")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT

    def test_nationality_mapping_exists(self):
        """Should map nationality field (from webapp: nationality)."""
        mapping = _find_mapping_by_field_id("nationality")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT

    def test_applicant_dob_is_date(self):
        """Should map applicant date of birth as date field."""
        mapping = _find_mapping_by_field_id("applicant_dob")

        assert mapping is not None
        assert mapping.field_type == FieldType.DATE

    def test_applicant_sex_is_radio(self):
        """Should map applicant sex as radio field."""
        mapping = _find_mapping_by_field_id("applicant_sex")

        assert mapping is not None
        assert mapping.field_type == FieldType.RADIO

    def test_passport_expiry_is_date(self):
        """Should map passport expiry as date field."""
        mapping = _find_mapping_by_field_id("passport_expiry")

        assert mapping is not None
        assert mapping.field_type == FieldType.DATE

    def test_a_number_mapping_exists(self):
        """Should map A-Number field (from webapp: a_number)."""
        mapping = _find_mapping_by_field_id("a_number")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT

    # Signature Fields (Excluded)
    def test_client_signature_is_signature_type(self):
        """Should mark client signature as signature type."""
        mapping = _find_mapping_by_field_id("client_signature")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True

    def test_client_signature_date_is_signature_type(self):
        """Should mark client signature date as signature type."""
        mapping = _find_mapping_by_field_id("client_signature_date")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True

    def test_attorney_signature_is_signature_type(self):
        """Should mark attorney signature as signature type."""
        mapping = _find_mapping_by_field_id("attorney_signature")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True

    def test_attorney_signature_date_is_signature_type(self):
        """Should mark attorney signature date as signature type."""
        mapping = _find_mapping_by_field_id("attorney_signature_date")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True


class TestFieldMappingConfig:
    """Tests for FieldMappingConfig class (Task 3.3)."""

    @pytest.fixture
    def config(self):
        """Create FieldMappingConfig instance."""
        return FieldMappingConfig()

    def test_config_has_default_mappings(self, config):
        """FieldMappingConfig should load default FORM_FIELD_MAPPINGS."""
        assert len(config.mappings) > 0
        assert len(config.mappings) == len(FORM_FIELD_MAPPINGS)

    def test_get_populatable_mappings_excludes_signatures(self, config):
        """get_populatable_mappings should exclude signature fields."""
        populatable = config.get_populatable_mappings()

        # Verify no signature fields
        for mapping in populatable:
            assert mapping.is_signature is False
            assert mapping.field_type != FieldType.SIGNATURE

        # Verify signature fields are truly excluded
        signature_ids = {"client_signature", "client_signature_date",
                        "attorney_signature", "attorney_signature_date"}
        populatable_ids = {m.field_id for m in populatable}
        assert signature_ids.isdisjoint(populatable_ids)

    def test_get_signature_mappings_returns_only_signatures(self, config):
        """get_signature_mappings should return only signature fields."""
        signatures = config.get_signature_mappings()

        for mapping in signatures:
            assert mapping.is_signature is True

        # Should have 4 signature fields
        assert len(signatures) == 4

    def test_get_required_fields_returns_required_non_signature_ids(self, config):
        """get_required_fields should return required field IDs excluding signatures."""
        required = config.get_required_fields()

        assert isinstance(required, list)
        assert all(isinstance(f, str) for f in required)

        # Required fields should include attorney/applicant fields
        assert "attorney_surname" in required
        assert "attorney_given_names" in required
        assert "applicant_surname" in required
        assert "applicant_given_names" in required

        # Signatures should NOT be in required
        assert "client_signature" not in required
        assert "attorney_signature" not in required


class TestFieldMappingConfigValidation:
    """Tests for FieldMappingConfig validation methods (Task 3.3)."""

    @pytest.fixture
    def config(self):
        """Create FieldMappingConfig instance."""
        return FieldMappingConfig()

    def test_validate_data_returns_empty_list_when_all_required_present(self, config):
        """validate_data should return empty list when all required fields present."""
        required_fields = config.get_required_fields()
        extracted_data = {field_id: "some_value" for field_id in required_fields}

        missing = config.validate_data(extracted_data)

        assert missing == []

    def test_validate_data_returns_missing_field_ids(self, config):
        """validate_data should return list of missing required field IDs."""
        # Provide empty data
        extracted_data: dict[str, str | bool | None] = {}

        missing = config.validate_data(extracted_data)

        assert len(missing) > 0
        # Should include required fields like attorney_surname
        assert "attorney_surname" in missing

    def test_validate_data_considers_none_values_as_missing(self, config):
        """validate_data should treat None values as missing."""
        extracted_data: dict[str, str | bool | None] = {
            "attorney_surname": None,
            "attorney_given_names": "John",
        }

        missing = config.validate_data(extracted_data)

        assert "attorney_surname" in missing
        assert "attorney_given_names" not in missing

    def test_validate_data_accepts_boolean_values(self, config):
        """validate_data should accept boolean values for checkbox fields."""
        required_fields = config.get_required_fields()
        extracted_data: dict[str, str | bool | None] = {
            field_id: "value" for field_id in required_fields
        }

        missing = config.validate_data(extracted_data)

        assert missing == []

    def test_validate_data_logs_warning_for_missing_required(
        self, config, caplog
    ):
        """validate_data should log warnings for missing required fields."""
        extracted_data: dict[str, str | bool | None] = {}

        with caplog.at_level(logging.WARNING):
            config.validate_data(extracted_data)

        # Check that warning was logged
        assert any("missing" in record.message.lower() or "required" in record.message.lower()
                   for record in caplog.records)


# Helper function to find mapping by field_id
def _find_mapping_by_field_id(field_id: str) -> FieldMapping | None:
    """Find a FieldMapping by its field_id."""
    for mapping in FORM_FIELD_MAPPINGS:
        if mapping.field_id == field_id:
            return mapping
    return None
