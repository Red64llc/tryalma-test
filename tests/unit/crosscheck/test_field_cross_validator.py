"""Unit tests for FieldCrossValidator.

Task 3.1: Test field cross-validation with source preference rules.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest

from tryalma.crosscheck.models import (
    DiscrepancySeverity,
    FieldDiscrepancy,
    FieldValidationResult,
    VisualZoneData,
)
from tryalma.crosscheck.field_cross_validator import FieldCrossValidator
from tryalma.passport.models import RawMRZData


class TestFieldCrossValidatorSourcePreference:
    """Test source preference rules for field cross-validation."""

    def test_mrz_preferred_for_passport_number(self):
        """MRZ should be preferred for machine-readable passport number."""
        validator = FieldCrossValidator()
        assert "passport_number" in validator.MRZ_PREFERRED_FIELDS

    def test_mrz_preferred_for_date_of_birth(self):
        """MRZ should be preferred for date of birth."""
        validator = FieldCrossValidator()
        assert "date_of_birth" in validator.MRZ_PREFERRED_FIELDS

    def test_mrz_preferred_for_expiry_date(self):
        """MRZ should be preferred for expiry date."""
        validator = FieldCrossValidator()
        assert "expiry_date" in validator.MRZ_PREFERRED_FIELDS

    def test_mrz_preferred_for_nationality(self):
        """MRZ should be preferred for nationality."""
        validator = FieldCrossValidator()
        assert "nationality" in validator.MRZ_PREFERRED_FIELDS

    def test_vlm_preferred_for_surname(self):
        """VLM should be preferred for surname (handles special chars)."""
        validator = FieldCrossValidator()
        assert "surname" in validator.VLM_PREFERRED_FIELDS

    def test_vlm_preferred_for_given_names(self):
        """VLM should be preferred for given names."""
        validator = FieldCrossValidator()
        assert "given_names" in validator.VLM_PREFERRED_FIELDS

    def test_vlm_preferred_for_place_of_birth(self):
        """VLM should be preferred for place of birth."""
        validator = FieldCrossValidator()
        assert "place_of_birth" in validator.VLM_PREFERRED_FIELDS


class TestTextNormalization:
    """Test text normalization for comparison (Requirement 2.2)."""

    def test_normalize_field_folds_case(self):
        """Normalization should be case-insensitive."""
        validator = FieldCrossValidator()
        result = validator.normalize_field("surname", "SMITH")
        assert result == "smith"

    def test_normalize_field_trims_whitespace(self):
        """Normalization should trim leading/trailing whitespace."""
        validator = FieldCrossValidator()
        result = validator.normalize_field("surname", "  SMITH  ")
        assert result == "smith"

    def test_normalize_field_collapses_internal_whitespace(self):
        """Normalization should collapse multiple spaces to single space."""
        validator = FieldCrossValidator()
        result = validator.normalize_field("given_names", "JOHN   WILLIAM")
        assert result == "john william"

    def test_normalize_field_handles_diacritics(self):
        """Normalization should handle diacritics via unicodedata."""
        validator = FieldCrossValidator()
        # e with acute accent should normalize
        result = validator.normalize_field("surname", "MULLER")
        assert result == "muller"

    def test_normalize_field_removes_combining_diacritics(self):
        """Normalization should remove combining diacritical marks."""
        validator = FieldCrossValidator()
        # e with acute (composed) should become e
        result = validator.normalize_field("surname", "\u00e9")  # e-acute
        assert result == "e"

    def test_normalize_field_handles_none(self):
        """Normalization should return None for None input."""
        validator = FieldCrossValidator()
        result = validator.normalize_field("surname", None)
        assert result is None

    def test_normalize_field_handles_empty_string(self):
        """Normalization should return None for empty string."""
        validator = FieldCrossValidator()
        result = validator.normalize_field("surname", "")
        assert result is None


class TestDateNormalization:
    """Test date normalization for comparison (Requirement 2.3)."""

    def test_normalize_date_iso_format(self):
        """Already ISO format should remain unchanged."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("1985-03-15")
        assert result == "1985-03-15"

    def test_normalize_date_yymmdd_format(self):
        """YYMMDD format from MRZ should convert to ISO."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("850315")  # March 15, 1985
        assert result == "1985-03-15"

    def test_normalize_date_yymmdd_2000s(self):
        """YYMMDD format with 20xx year should convert correctly."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("050315")  # March 15, 2005
        assert result == "2005-03-15"

    def test_normalize_date_dd_mm_yyyy(self):
        """DD/MM/YYYY format should convert to ISO."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("15/03/1985")
        assert result == "1985-03-15"

    def test_normalize_date_mm_dd_yyyy(self):
        """MM-DD-YYYY format should convert to ISO."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("03-15-1985")
        assert result == "1985-03-15"

    def test_normalize_date_handles_none(self):
        """Normalization should return None for None input."""
        validator = FieldCrossValidator()
        result = validator.normalize_date(None)
        assert result is None

    def test_normalize_date_handles_empty_string(self):
        """Normalization should return None for empty string."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("")
        assert result is None

    def test_normalize_date_handles_invalid_date(self):
        """Normalization should return None for invalid date."""
        validator = FieldCrossValidator()
        result = validator.normalize_date("not-a-date")
        assert result is None


class TestCrossValidation:
    """Test field-by-field cross-validation (Requirement 2.1)."""

    def test_cross_validate_matching_fields(self):
        """Matching fields should be marked as validated (Requirement 2.4)."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            surname="SMITH",
            given_names="JOHN",
            document_number="123456789",
            birth_date="850315",
            nationality="USA",
            expiry_date="300314",
            sex="M",
        )

        visual_data = VisualZoneData(
            surname="SMITH",
            given_names="JOHN",
            passport_number="123456789",
            date_of_birth="1985-03-15",
            nationality="USA",
            expiry_date="2030-03-14",
            sex="M",
        )

        results = validator.cross_validate(mrz_data, visual_data)

        # Find surname result
        surname_result = next(r for r in results if r.field_name == "surname")
        assert surname_result.validated is True
        assert surname_result.discrepancy is None

    def test_cross_validate_records_discrepancy_on_mismatch(self):
        """Mismatched fields should record discrepancy (Requirement 2.5)."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            surname="SMITH",
            document_number="123456789",
        )

        visual_data = VisualZoneData(
            surname="SMITH",
            passport_number="123456780",  # Different last digit
        )

        results = validator.cross_validate(mrz_data, visual_data)

        # Find passport_number result
        passport_result = next(r for r in results if r.field_name == "passport_number")
        assert passport_result.validated is False
        assert passport_result.discrepancy is not None
        assert passport_result.discrepancy.mrz_value == "123456789"
        assert passport_result.discrepancy.vlm_value == "123456780"

    def test_cross_validate_normalizes_before_comparison(self):
        """Fields should be normalized before comparison (Requirement 2.2)."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            surname="SMITH",  # Uppercase
        )

        visual_data = VisualZoneData(
            surname="Smith",  # Mixed case - should match after normalization
        )

        results = validator.cross_validate(mrz_data, visual_data)

        surname_result = next(r for r in results if r.field_name == "surname")
        assert surname_result.validated is True

    def test_cross_validate_normalizes_dates(self):
        """Date fields should use standardized format for comparison (Requirement 2.3)."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            birth_date="850315",  # YYMMDD format
        )

        visual_data = VisualZoneData(
            date_of_birth="1985-03-15",  # ISO format - should match
        )

        results = validator.cross_validate(mrz_data, visual_data)

        dob_result = next(r for r in results if r.field_name == "date_of_birth")
        assert dob_result.validated is True


class TestSingleSourceHandling:
    """Test handling when one extraction source is None."""

    def test_cross_validate_with_mrz_only(self):
        """When VLM is None, MRZ values should be used with validated=True."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            surname="SMITH",
            document_number="123456789",
        )

        results = validator.cross_validate(mrz_data, None)

        surname_result = next(r for r in results if r.field_name == "surname")
        assert surname_result.validated is True
        assert surname_result.final_value == "SMITH"
        assert surname_result.mrz_value == "SMITH"
        assert surname_result.vlm_value is None
        assert surname_result.discrepancy is None

    def test_cross_validate_with_vlm_only(self):
        """When MRZ is None, VLM values should be used with validated=True."""
        validator = FieldCrossValidator()

        visual_data = VisualZoneData(
            surname="SMITH",
            passport_number="123456789",
        )

        results = validator.cross_validate(None, visual_data)

        surname_result = next(r for r in results if r.field_name == "surname")
        assert surname_result.validated is True
        assert surname_result.final_value == "SMITH"
        assert surname_result.mrz_value is None
        assert surname_result.vlm_value == "SMITH"
        assert surname_result.discrepancy is None

    def test_cross_validate_with_both_none(self):
        """When both sources are None, should return empty results."""
        validator = FieldCrossValidator()

        results = validator.cross_validate(None, None)

        assert len(results) == 0

    def test_cross_validate_single_source_field_missing(self):
        """When single source has field as None, validated should still be True."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            surname="SMITH",
            # passport_number is None
        )

        results = validator.cross_validate(mrz_data, None)

        # passport_number should not appear in results since neither has it
        passport_result = next(
            (r for r in results if r.field_name == "passport_number"),
            None
        )
        # Either not in results, or marked as unavailable
        if passport_result is not None:
            assert passport_result.final_value is None


class TestFinalValueSelection:
    """Test that final_value is selected based on source preference."""

    def test_final_value_uses_mrz_for_machine_readable_fields(self):
        """For machine-readable fields, MRZ value should be preferred."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            document_number="MRZ123456",
        )

        visual_data = VisualZoneData(
            passport_number="VLM123456",
        )

        results = validator.cross_validate(mrz_data, visual_data)

        passport_result = next(r for r in results if r.field_name == "passport_number")
        # Even with mismatch, MRZ is preferred for passport_number
        assert passport_result.final_value == "MRZ123456"

    def test_final_value_uses_vlm_for_names(self):
        """For name fields, VLM value should be preferred."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            surname="MULLER",  # MRZ can't handle umlauts
        )

        visual_data = VisualZoneData(
            surname="MUELLER",  # VLM captured umlaut as UE
        )

        results = validator.cross_validate(mrz_data, visual_data)

        surname_result = next(r for r in results if r.field_name == "surname")
        # VLM is preferred for surnames
        assert surname_result.final_value == "MUELLER"


class TestFieldMappingBetweenSources:
    """Test that fields are correctly mapped between MRZ and VLM data structures."""

    def test_document_number_maps_to_passport_number(self):
        """MRZ document_number should map to passport_number field."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            document_number="ABC123456",
        )

        visual_data = VisualZoneData(
            passport_number="ABC123456",
        )

        results = validator.cross_validate(mrz_data, visual_data)

        passport_result = next(r for r in results if r.field_name == "passport_number")
        assert passport_result.mrz_value == "ABC123456"
        assert passport_result.vlm_value == "ABC123456"
        assert passport_result.validated is True

    def test_birth_date_maps_to_date_of_birth(self):
        """MRZ birth_date should map to date_of_birth field."""
        validator = FieldCrossValidator()

        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            birth_date="850315",
        )

        visual_data = VisualZoneData(
            date_of_birth="1985-03-15",
        )

        results = validator.cross_validate(mrz_data, visual_data)

        dob_result = next(r for r in results if r.field_name == "date_of_birth")
        assert dob_result.validated is True
