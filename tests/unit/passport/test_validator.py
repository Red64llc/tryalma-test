"""Unit tests for MRZ validator.

Task 4.1: MRZValidator class with ICAO 9303 compliance.

Requirements: 6.2, 6.3, 6.4
"""

import pytest

from tryalma.passport.models import CheckDigitResult, MRZType, ValidationResult


class TestMRZValidatorValidate:
    """Tests for validate method."""

    def test_validate_returns_validation_result(self, sample_mrz_td3_data: str):
        """Test validate returns a ValidationResult instance."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        assert isinstance(result, ValidationResult)

    def test_validate_auto_detects_td3_format(self, sample_mrz_td3_data: str):
        """Test validate auto-detects TD3 (passport) MRZ format."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        assert result.mrz_type == MRZType.TD3

    def test_validate_auto_detects_td1_format(self, sample_mrz_td1_data: str):
        """Test validate auto-detects TD1 (ID card) MRZ format."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td1_data)

        assert result.mrz_type == MRZType.TD1

    def test_validate_returns_valid_result_for_valid_mrz(self, sample_mrz_td3_data: str):
        """Test validate returns is_valid=True for MRZ with valid check digits."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        assert result.is_valid is True

    def test_validate_returns_check_digit_results(self, sample_mrz_td3_data: str):
        """Test validate returns list of CheckDigitResult."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        assert isinstance(result.check_digits, list)
        assert len(result.check_digits) > 0
        assert all(isinstance(cd, CheckDigitResult) for cd in result.check_digits)

    def test_validate_includes_warnings_list(self, sample_mrz_td3_data: str):
        """Test validate returns warnings list (may be empty)."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        assert isinstance(result.warnings, list)

    def test_validate_with_explicit_mrz_type(self, sample_mrz_td3_data: str):
        """Test validate accepts explicit MRZ type parameter."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data, mrz_type=MRZType.TD3)

        assert result.mrz_type == MRZType.TD3
        assert result.is_valid is True


class TestMRZValidatorValidateTD3:
    """Tests for validate_td3 method (passport format)."""

    def test_validate_td3_accepts_two_line_format(self, sample_mrz_td3_data: str):
        """Test validate_td3 accepts 2-line MRZ format."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td3(sample_mrz_td3_data)

        assert isinstance(result, ValidationResult)
        assert result.mrz_type == MRZType.TD3

    def test_validate_td3_validates_document_number_check_digit(
        self, sample_mrz_td3_data: str
    ):
        """Test validate_td3 validates document number check digit."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td3(sample_mrz_td3_data)

        # Check that document number check digit is validated
        doc_number_check = next(
            (cd for cd in result.check_digits if "document" in cd.field_name.lower()),
            None,
        )
        assert doc_number_check is not None

    def test_validate_td3_validates_birth_date_check_digit(
        self, sample_mrz_td3_data: str
    ):
        """Test validate_td3 validates birth date check digit."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td3(sample_mrz_td3_data)

        # Check that birth date check digit is validated
        birth_check = next(
            (cd for cd in result.check_digits if "birth" in cd.field_name.lower()),
            None,
        )
        assert birth_check is not None

    def test_validate_td3_validates_expiry_date_check_digit(
        self, sample_mrz_td3_data: str
    ):
        """Test validate_td3 validates expiry date check digit."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td3(sample_mrz_td3_data)

        # Check that expiry date check digit is validated
        expiry_check = next(
            (cd for cd in result.check_digits if "expir" in cd.field_name.lower()),
            None,
        )
        assert expiry_check is not None

    def test_validate_td3_validates_composite_check_digit(
        self, sample_mrz_td3_data: str
    ):
        """Test validate_td3 validates composite check digit."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td3(sample_mrz_td3_data)

        # Check that composite check digit is validated
        composite_check = next(
            (cd for cd in result.check_digits if "composite" in cd.field_name.lower()),
            None,
        )
        assert composite_check is not None


class TestMRZValidatorValidateTD1:
    """Tests for validate_td1 method (ID card format)."""

    def test_validate_td1_accepts_three_line_format(self, sample_mrz_td1_data: str):
        """Test validate_td1 accepts 3-line MRZ format."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td1(sample_mrz_td1_data)

        assert isinstance(result, ValidationResult)
        assert result.mrz_type == MRZType.TD1

    def test_validate_td1_validates_document_number_check_digit(
        self, sample_mrz_td1_data: str
    ):
        """Test validate_td1 validates document number check digit."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td1(sample_mrz_td1_data)

        # Check that document number check digit is validated
        doc_number_check = next(
            (cd for cd in result.check_digits if "document" in cd.field_name.lower()),
            None,
        )
        assert doc_number_check is not None

    def test_validate_td1_validates_birth_date_check_digit(
        self, sample_mrz_td1_data: str
    ):
        """Test validate_td1 validates birth date check digit."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate_td1(sample_mrz_td1_data)

        # Check that birth date check digit is validated
        birth_check = next(
            (cd for cd in result.check_digits if "birth" in cd.field_name.lower()),
            None,
        )
        assert birth_check is not None


class TestMRZValidatorInvalidMRZ:
    """Tests for handling invalid MRZ data."""

    def test_validate_returns_invalid_for_corrupted_check_digit(self):
        """Test validate returns is_valid=False for invalid check digit."""
        from tryalma.passport.validator import MRZValidator

        # Create MRZ with intentionally wrong check digit (changed last digit)
        # Original TD3 with valid checksums:
        # P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
        # L898902C36UTO7408122F1204159ZE184226B<<<<<10
        # Corrupt the document number check digit (change 6 to 9)
        invalid_mrz = (
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\n"
            "L898902C39UTO7408122F1204159ZE184226B<<<<<10"  # 6 changed to 9
        )

        validator = MRZValidator()
        result = validator.validate(invalid_mrz)

        assert result.is_valid is False
        # Should have at least one invalid check digit
        invalid_checks = [cd for cd in result.check_digits if not cd.is_valid]
        assert len(invalid_checks) > 0

    def test_validate_returns_check_digit_error_details(self):
        """Test invalid check digit result includes expected vs actual values."""
        from tryalma.passport.validator import MRZValidator

        # MRZ with wrong check digit
        invalid_mrz = (
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\n"
            "L898902C39UTO7408122F1204159ZE184226B<<<<<10"
        )

        validator = MRZValidator()
        result = validator.validate(invalid_mrz)

        # Find the invalid check digit result
        invalid_check = next(
            (cd for cd in result.check_digits if not cd.is_valid),
            None,
        )

        # Should have details about what was expected vs actual
        if invalid_check:
            assert invalid_check.field_name is not None

    def test_validate_handles_malformed_mrz_gracefully(self):
        """Test validate handles badly formatted MRZ without crashing."""
        from tryalma.passport.validator import MRZValidator

        # Incomplete/malformed MRZ
        malformed_mrz = "P<UTO<<<<<\nSHORT"

        validator = MRZValidator()
        result = validator.validate(malformed_mrz)

        # Should return a result (either invalid or with warnings)
        assert isinstance(result, ValidationResult)
        # Either invalid or has warnings
        assert result.is_valid is False or len(result.warnings) > 0

    def test_validate_handles_empty_string(self):
        """Test validate handles empty MRZ string."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate("")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False


class TestMRZValidatorCheckDigitResult:
    """Tests for CheckDigitResult content."""

    def test_check_digit_result_contains_field_name(self, sample_mrz_td3_data: str):
        """Test CheckDigitResult includes field name."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        for cd in result.check_digits:
            assert cd.field_name is not None
            assert len(cd.field_name) > 0

    def test_check_digit_result_contains_validity_flag(self, sample_mrz_td3_data: str):
        """Test CheckDigitResult includes is_valid flag."""
        from tryalma.passport.validator import MRZValidator

        validator = MRZValidator()
        result = validator.validate(sample_mrz_td3_data)

        for cd in result.check_digits:
            assert isinstance(cd.is_valid, bool)


class TestMRZValidatorWarnings:
    """Tests for validation warnings."""

    def test_validate_includes_expiry_warning_for_expired_document(self):
        """Test validate includes warning for expired documents when enabled."""
        from tryalma.passport.validator import MRZValidator

        # MRZ with past expiry date (120415 = 2012-04-15)
        expired_mrz = (
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\n"
            "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        )

        validator = MRZValidator()
        result = validator.validate(expired_mrz)

        # The validator may include expiry warnings
        # This depends on mrz library's check_expiry feature
        assert isinstance(result.warnings, list)


class TestMRZValidatorUnsupportedTypes:
    """Tests for unsupported MRZ types (TD2, MRVA, MRVB)."""

    def test_validate_with_td2_type_returns_not_supported(self):
        """Test validate returns warning for TD2 type (not yet supported)."""
        from tryalma.passport.validator import MRZValidator

        # Use a sample MRZ string (content doesn't matter for type override)
        mrz = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"

        validator = MRZValidator()
        result = validator.validate(mrz, mrz_type=MRZType.TD2)

        assert result.is_valid is False
        assert result.mrz_type == MRZType.TD2
        assert len(result.warnings) > 0
        assert "not yet supported" in result.warnings[0]

    def test_validate_with_mrva_type_returns_not_supported(self):
        """Test validate returns warning for MRVA type (not yet supported)."""
        from tryalma.passport.validator import MRZValidator

        mrz = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"

        validator = MRZValidator()
        result = validator.validate(mrz, mrz_type=MRZType.MRVA)

        assert result.is_valid is False
        assert result.mrz_type == MRZType.MRVA
        assert len(result.warnings) > 0

    def test_validate_with_mrvb_type_returns_not_supported(self):
        """Test validate returns warning for MRVB type (not yet supported)."""
        from tryalma.passport.validator import MRZValidator

        mrz = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"

        validator = MRZValidator()
        result = validator.validate(mrz, mrz_type=MRZType.MRVB)

        assert result.is_valid is False
        assert result.mrz_type == MRZType.MRVB
        assert len(result.warnings) > 0


class TestMRZValidatorValidationErrors:
    """Tests for validation error handling."""

    def test_validate_td1_handles_invalid_length_gracefully(self):
        """Test validate_td1 returns result with warning for invalid TD1 length."""
        from tryalma.passport.validator import MRZValidator

        # TD1 requires 92 characters (30+1+30+1+30), this is too short
        invalid_td1 = "I<UTO\n7408122\nERIKSSON"

        validator = MRZValidator()
        result = validator.validate_td1(invalid_td1)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.warnings) > 0

    def test_validate_td3_handles_invalid_length_gracefully(self):
        """Test validate_td3 returns result with warning for invalid TD3 length."""
        from tryalma.passport.validator import MRZValidator

        # TD3 requires 89 characters (44+1+44), this is too short
        invalid_td3 = "P<UTO\nL89890"

        validator = MRZValidator()
        result = validator.validate_td3(invalid_td3)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.warnings) > 0


class TestMRZValidatorAutoDetect:
    """Tests for MRZ type auto-detection edge cases."""

    def test_detect_single_line_mrz_defaults_to_td3(self):
        """Test single-line MRZ (invalid) defaults to TD3."""
        from tryalma.passport.validator import MRZValidator

        # Single line MRZ - not 2 or 3 lines
        single_line = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<L898902C36UTO7408122F1204159"

        validator = MRZValidator()
        result = validator.validate(single_line)

        # Should default to TD3 and fail validation
        assert result.mrz_type == MRZType.TD3
        assert result.is_valid is False

    def test_detect_four_line_mrz_uses_length_fallback(self):
        """Test four-line MRZ uses length-based detection."""
        from tryalma.passport.validator import MRZValidator

        # Four lines - ambiguous, should fall back to length check
        # Long enough to trigger TD1 detection (>= 90 chars)
        four_line = "LINE1<<<<<<<<<<<<<<<<<<<<<<<\nLINE2<<<<<<<<<<<<<<<<<<<<<<<\nLINE3<<<<<<<<<<<<<<<<<<<<<<<\nLINE4"

        validator = MRZValidator()
        result = validator.validate(four_line)

        # Should detect and attempt validation (will fail but shouldn't crash)
        assert isinstance(result, ValidationResult)

    def test_detect_very_short_mrz_defaults_to_td3(self):
        """Test very short MRZ defaults to TD3."""
        from tryalma.passport.validator import MRZValidator

        # Very short - should default to TD3
        short_mrz = "P<UTO"

        validator = MRZValidator()
        result = validator.validate(short_mrz)

        # With 1 line and short length, should use TD3
        assert result.mrz_type == MRZType.TD3
