"""Tests for FieldMappingConfig - field mapping configuration for form population.

These tests verify:
- Task 3.1: Field mapping data structures (Requirements: 3.1, 3.3, 9.4)
- Task 3.2: Target form field mappings (Requirements: 3.1, 3.3, 9.1, 9.2, 9.3, 9.4)
- Task 3.3: Mapping validation and field retrieval (Requirements: 3.2, 3.4, 3.5)
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
        """FieldType enum should include TEXT type.

        Requirements: 3.3
        """
        assert FieldType.TEXT.value == "text"

    def test_field_type_dropdown_exists(self):
        """FieldType enum should include DROPDOWN type.

        Requirements: 3.3
        """
        assert FieldType.DROPDOWN.value == "dropdown"

    def test_field_type_checkbox_exists(self):
        """FieldType enum should include CHECKBOX type.

        Requirements: 3.3
        """
        assert FieldType.CHECKBOX.value == "checkbox"

    def test_field_type_radio_exists(self):
        """FieldType enum should include RADIO type.

        Requirements: 3.3
        """
        assert FieldType.RADIO.value == "radio"

    def test_field_type_date_exists(self):
        """FieldType enum should include DATE type.

        Requirements: 3.3
        """
        assert FieldType.DATE.value == "date"

    def test_field_type_signature_exists(self):
        """FieldType enum should include SIGNATURE type for exclusion.

        Requirements: 9.4
        """
        assert FieldType.SIGNATURE.value == "signature"


class TestFieldMapping:
    """Tests for FieldMapping dataclass (Task 3.1)."""

    def test_field_mapping_creation_with_required_fields(self):
        """FieldMapping should require field_id, selector, and field_type.

        Requirements: 3.1
        """
        mapping = FieldMapping(
            field_id="attorney_family_name",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.field_id == "attorney_family_name"
        assert mapping.selector == "input[name='familyName']"
        assert mapping.field_type == FieldType.TEXT

    def test_field_mapping_required_flag_defaults_to_false(self):
        """FieldMapping should have required flag defaulting to False.

        Requirements: 3.1
        """
        mapping = FieldMapping(
            field_id="attorney_middle_name",
            selector="input[name='middleName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.required is False

    def test_field_mapping_required_flag_can_be_true(self):
        """FieldMapping should support required=True for mandatory fields.

        Requirements: 3.1
        """
        mapping = FieldMapping(
            field_id="attorney_family_name",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
            required=True,
        )

        assert mapping.required is True

    def test_field_mapping_is_signature_flag_defaults_to_false(self):
        """FieldMapping should have is_signature flag defaulting to False.

        Requirements: 9.4
        """
        mapping = FieldMapping(
            field_id="attorney_family_name",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.is_signature is False

    def test_field_mapping_is_signature_flag_for_signature_fields(self):
        """FieldMapping should support is_signature=True for signature fields.

        Requirements: 9.4
        """
        mapping = FieldMapping(
            field_id="client_signature",
            selector="input[name='clientSignature']",
            field_type=FieldType.SIGNATURE,
            is_signature=True,
        )

        assert mapping.is_signature is True

    def test_field_mapping_format_pattern_defaults_to_none(self):
        """FieldMapping should have format_pattern defaulting to None.

        Requirements: 3.1
        """
        mapping = FieldMapping(
            field_id="attorney_family_name",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        assert mapping.format_pattern is None

    def test_field_mapping_format_pattern_for_phone(self):
        """FieldMapping should support format_pattern for phone numbers.

        Requirements: 3.1
        """
        mapping = FieldMapping(
            field_id="attorney_daytime_phone",
            selector="input[name='daytimePhone']",
            field_type=FieldType.TEXT,
            format_pattern="###-###-####",
        )

        assert mapping.format_pattern == "###-###-####"

    def test_field_mapping_is_frozen(self):
        """FieldMapping should be immutable (frozen dataclass).

        Requirements: 3.1
        """
        mapping = FieldMapping(
            field_id="attorney_family_name",
            selector="input[name='familyName']",
            field_type=FieldType.TEXT,
        )

        with pytest.raises(AttributeError):
            mapping.field_id = "different_id"


class TestFormFieldMappings:
    """Tests for FORM_FIELD_MAPPINGS constant (Task 3.2)."""

    def test_form_field_mappings_is_list(self):
        """FORM_FIELD_MAPPINGS should be a list of FieldMapping objects.

        Requirements: 3.1
        """
        assert isinstance(FORM_FIELD_MAPPINGS, list)
        assert all(isinstance(m, FieldMapping) for m in FORM_FIELD_MAPPINGS)

    # Part 1: Attorney/Representative Information
    def test_attorney_family_name_mapping_exists(self):
        """Should map attorney family name field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_family_name")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True
        assert "familyName" in mapping.selector or "family" in mapping.selector.lower()

    def test_attorney_given_name_mapping_exists(self):
        """Should map attorney given name field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_given_name")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_attorney_street_address_mapping_exists(self):
        """Should map attorney street address field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_street_address")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_attorney_city_mapping_exists(self):
        """Should map attorney city field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_city")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_attorney_state_mapping_is_dropdown(self):
        """Should map attorney state as dropdown field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_state")

        assert mapping is not None
        assert mapping.field_type == FieldType.DROPDOWN
        assert mapping.required is True

    def test_attorney_zip_mapping_exists(self):
        """Should map attorney zip code field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_zip")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_attorney_daytime_phone_has_format_pattern(self):
        """Should map attorney phone with format pattern.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_daytime_phone")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True
        assert mapping.format_pattern == "###-###-####"

    def test_attorney_email_mapping_exists(self):
        """Should map attorney email field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("attorney_email")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT

    # Part 2: Eligibility Information
    def test_eligibility_is_attorney_is_checkbox(self):
        """Should map eligibility attorney checkbox.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("eligibility_is_attorney")

        assert mapping is not None
        assert mapping.field_type == FieldType.CHECKBOX

    def test_eligibility_bar_number_mapping_exists(self):
        """Should map eligibility bar number field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("eligibility_bar_number")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT

    def test_eligibility_accreditation_date_is_date(self):
        """Should map eligibility accreditation date as date field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("eligibility_accreditation_date")

        assert mapping is not None
        assert mapping.field_type == FieldType.DATE

    # Part 3: Beneficiary/Passport Information
    def test_beneficiary_last_name_mapping_exists(self):
        """Should map beneficiary last name field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_last_name")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_beneficiary_first_names_mapping_exists(self):
        """Should map beneficiary first names field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_first_names")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_beneficiary_passport_number_mapping_exists(self):
        """Should map beneficiary passport number field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_passport_number")

        assert mapping is not None
        assert mapping.field_type == FieldType.TEXT
        assert mapping.required is True

    def test_beneficiary_date_of_birth_is_date(self):
        """Should map beneficiary date of birth as date field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_date_of_birth")

        assert mapping is not None
        assert mapping.field_type == FieldType.DATE
        assert mapping.required is True

    def test_beneficiary_sex_is_radio(self):
        """Should map beneficiary sex as radio field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_sex")

        assert mapping is not None
        assert mapping.field_type == FieldType.RADIO
        assert mapping.required is True

    def test_beneficiary_nationality_mapping_exists(self):
        """Should map beneficiary nationality field.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_nationality")

        assert mapping is not None
        assert mapping.required is True

    def test_beneficiary_date_of_issue_is_date(self):
        """Should map beneficiary passport issue date.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_date_of_issue")

        assert mapping is not None
        assert mapping.field_type == FieldType.DATE
        assert mapping.required is True

    def test_beneficiary_date_of_expiration_is_date(self):
        """Should map beneficiary passport expiration date.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("beneficiary_date_of_expiration")

        assert mapping is not None
        assert mapping.field_type == FieldType.DATE
        assert mapping.required is True

    # Part 4: Consent Checkboxes
    def test_consent_notices_to_attorney_is_checkbox(self):
        """Should map consent notices checkbox.

        Requirements: 3.1, 3.3
        """
        mapping = _find_mapping_by_field_id("consent_notices_to_attorney")

        assert mapping is not None
        assert mapping.field_type == FieldType.CHECKBOX

    # Signature Fields (Excluded)
    def test_client_signature_is_signature_type(self):
        """Should mark client signature as signature type.

        Requirements: 9.1, 9.4
        """
        mapping = _find_mapping_by_field_id("client_signature")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True

    def test_client_signature_date_is_signature_type(self):
        """Should mark client signature date as signature type.

        Requirements: 9.2, 9.4
        """
        mapping = _find_mapping_by_field_id("client_signature_date")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True

    def test_attorney_signature_is_signature_type(self):
        """Should mark attorney signature as signature type.

        Requirements: 9.1, 9.4
        """
        mapping = _find_mapping_by_field_id("attorney_signature")

        assert mapping is not None
        assert mapping.field_type == FieldType.SIGNATURE
        assert mapping.is_signature is True

    def test_attorney_signature_date_is_signature_type(self):
        """Should mark attorney signature date as signature type.

        Requirements: 9.2, 9.4
        """
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
        """FieldMappingConfig should load default FORM_FIELD_MAPPINGS.

        Requirements: 3.1
        """
        assert len(config.mappings) > 0
        assert len(config.mappings) == len(FORM_FIELD_MAPPINGS)

    def test_get_populatable_mappings_excludes_signatures(self, config):
        """get_populatable_mappings should exclude signature fields.

        Requirements: 9.1, 9.2, 9.3, 9.4
        """
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
        """get_signature_mappings should return only signature fields.

        Requirements: 9.4
        """
        signatures = config.get_signature_mappings()

        for mapping in signatures:
            assert mapping.is_signature is True

        # Should have at least 4 signature fields
        assert len(signatures) >= 4

    def test_get_required_fields_returns_required_non_signature_ids(self, config):
        """get_required_fields should return required field IDs excluding signatures.

        Requirements: 3.2
        """
        required = config.get_required_fields()

        assert isinstance(required, list)
        assert all(isinstance(f, str) for f in required)

        # Required fields should include key attorney/beneficiary fields
        assert "attorney_family_name" in required
        assert "beneficiary_last_name" in required
        assert "beneficiary_passport_number" in required

        # Signatures should NOT be in required (even if marked required)
        assert "client_signature" not in required
        assert "attorney_signature" not in required


class TestFieldMappingConfigValidation:
    """Tests for FieldMappingConfig validation methods (Task 3.3)."""

    @pytest.fixture
    def config(self):
        """Create FieldMappingConfig instance."""
        return FieldMappingConfig()

    def test_validate_data_returns_empty_list_when_all_required_present(self, config):
        """validate_data should return empty list when all required fields present.

        Requirements: 3.2
        """
        required_fields = config.get_required_fields()
        extracted_data = {field_id: "some_value" for field_id in required_fields}

        missing = config.validate_data(extracted_data)

        assert missing == []

    def test_validate_data_returns_missing_field_ids(self, config):
        """validate_data should return list of missing required field IDs.

        Requirements: 3.2
        """
        # Provide empty data
        extracted_data: dict[str, str | bool | None] = {}

        missing = config.validate_data(extracted_data)

        assert len(missing) > 0
        # Should include required fields like attorney_family_name
        assert "attorney_family_name" in missing

    def test_validate_data_considers_none_values_as_missing(self, config):
        """validate_data should treat None values as missing.

        Requirements: 3.2
        """
        extracted_data: dict[str, str | bool | None] = {
            "attorney_family_name": None,
            "attorney_given_name": "John",
        }

        missing = config.validate_data(extracted_data)

        assert "attorney_family_name" in missing
        assert "attorney_given_name" not in missing

    def test_validate_data_accepts_boolean_values(self, config):
        """validate_data should accept boolean values for checkbox fields.

        Requirements: 3.2
        """
        required_fields = config.get_required_fields()
        extracted_data: dict[str, str | bool | None] = {
            field_id: "value" for field_id in required_fields
        }
        # Add a checkbox field
        extracted_data["eligibility_is_attorney"] = True

        missing = config.validate_data(extracted_data)

        assert missing == []

    def test_validate_data_logs_warning_for_missing_required(
        self, config, caplog
    ):
        """validate_data should log warnings for missing required fields.

        Requirements: 3.5
        """
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
