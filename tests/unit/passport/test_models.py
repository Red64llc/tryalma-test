"""Unit tests for passport domain models.

Task 2.1, 2.2: Test PassportData, ExtractionResult, RawMRZData, ValidationResult,
CheckDigitResult dataclasses and MRZType enum.

Requirements: 2.1-2.9, 3.3, 6.1, 6.2, 6.4
"""

from datetime import date
from pathlib import Path

import pytest


class TestPassportData:
    """Tests for PassportData dataclass."""

    def test_passport_data_creation_with_all_fields(self):
        """Test creating PassportData with all fields populated."""
        from tryalma.passport.models import PassportData

        data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            given_names="JOHN WILLIAM",
            date_of_birth=date(1985, 3, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 3, 14),
            sex="M",
            place_of_birth="NEW YORK",
            mrz_type="TD3",
            mrz_valid=True,
            check_digit_errors=[],
            confidence=0.95,
            raw_mrz="P<USASMITH<<JOHN<WILLIAM<<<<<<<<<<<<<<<<<<<",
        )

        assert data.surname == "SMITH"
        assert data.given_names == "JOHN WILLIAM"
        assert data.date_of_birth == date(1985, 3, 15)
        assert data.nationality == "USA"
        assert data.passport_number == "123456789"
        assert data.expiry_date == date(2030, 3, 14)
        assert data.sex == "M"
        assert data.place_of_birth == "NEW YORK"
        assert data.mrz_type == "TD3"
        assert data.mrz_valid is True
        assert data.check_digit_errors == []
        assert data.confidence == 0.95
        assert data.source_file == Path("/test/passport.jpg")

    def test_passport_data_creation_with_minimal_fields(self):
        """Test creating PassportData with only required field (source_file)."""
        from tryalma.passport.models import PassportData

        data = PassportData(source_file=Path("/test/passport.jpg"))

        assert data.source_file == Path("/test/passport.jpg")
        assert data.surname is None
        assert data.given_names is None
        assert data.date_of_birth is None
        assert data.nationality is None
        assert data.passport_number is None
        assert data.expiry_date is None
        assert data.sex is None
        assert data.place_of_birth is None
        assert data.mrz_type is None
        assert data.mrz_valid is False
        assert data.check_digit_errors == []
        assert data.confidence is None
        assert data.raw_mrz is None

    def test_passport_data_to_dict_basic(self):
        """Test to_dict method returns dictionary representation."""
        from tryalma.passport.models import PassportData

        data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=date(1985, 3, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 3, 14),
            sex="M",
        )

        result = data.to_dict()

        assert result["surname"] == "SMITH"
        assert result["given_names"] == "JOHN"
        assert result["date_of_birth"] == "1985-03-15"
        assert result["nationality"] == "USA"
        assert result["passport_number"] == "123456789"
        assert result["expiry_date"] == "2030-03-14"
        assert result["sex"] == "M"
        assert result["source_file"] == "/test/passport.jpg"

    def test_passport_data_to_dict_verbose_includes_metadata(self):
        """Test to_dict with verbose=True includes confidence and raw_mrz."""
        from tryalma.passport.models import PassportData

        data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            confidence=0.95,
            raw_mrz="P<USASMITH<<<<<",
            mrz_valid=True,
        )

        result = data.to_dict(verbose=True)

        assert result["confidence"] == 0.95
        assert result["raw_mrz"] == "P<USASMITH<<<<<"
        assert result["mrz_valid"] is True

    def test_passport_data_to_dict_non_verbose_excludes_metadata(self):
        """Test to_dict with verbose=False excludes confidence and raw_mrz."""
        from tryalma.passport.models import PassportData

        data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            confidence=0.95,
            raw_mrz="P<USASMITH<<<<<",
        )

        result = data.to_dict(verbose=False)

        assert "confidence" not in result
        assert "raw_mrz" not in result

    def test_passport_data_get_unavailable_fields(self):
        """Test get_unavailable_fields returns list of None fields."""
        from tryalma.passport.models import PassportData

        data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            given_names=None,
            date_of_birth=date(1985, 3, 15),
            nationality=None,
            passport_number="123456789",
            expiry_date=None,
            sex="M",
            place_of_birth=None,
        )

        unavailable = data.get_unavailable_fields()

        assert "given_names" in unavailable
        assert "nationality" in unavailable
        assert "expiry_date" in unavailable
        assert "place_of_birth" in unavailable
        assert "surname" not in unavailable
        assert "date_of_birth" not in unavailable
        assert "passport_number" not in unavailable
        assert "sex" not in unavailable

    def test_passport_data_get_unavailable_fields_all_present(self):
        """Test get_unavailable_fields returns empty list when all fields present."""
        from tryalma.passport.models import PassportData

        data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=date(1985, 3, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 3, 14),
            sex="M",
            place_of_birth="NEW YORK",
        )

        unavailable = data.get_unavailable_fields()

        assert unavailable == []


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_extraction_result_success(self):
        """Test creating a successful extraction result."""
        from tryalma.passport.models import ExtractionResult, PassportData

        passport_data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
        )

        result = ExtractionResult(
            success=True,
            data=passport_data,
            error=None,
            source_file=Path("/test/passport.jpg"),
        )

        assert result.success is True
        assert result.data == passport_data
        assert result.error is None
        assert result.source_file == Path("/test/passport.jpg")

    def test_extraction_result_failure(self):
        """Test creating a failed extraction result."""
        from tryalma.passport.models import ExtractionResult

        result = ExtractionResult(
            success=False,
            data=None,
            error="No MRZ detected in image",
            source_file=Path("/test/passport.jpg"),
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "No MRZ detected in image"
        assert result.source_file == Path("/test/passport.jpg")


class TestRawMRZData:
    """Tests for RawMRZData dataclass."""

    def test_raw_mrz_data_creation(self):
        """Test creating RawMRZData with all fields."""
        from tryalma.passport.models import RawMRZData

        data = RawMRZData(
            mrz_type="TD3",
            raw_text="P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<L898902C36UTO7408122F1204159ZE184226B<<<<<10",
            surname="ERIKSSON",
            given_names="ANNA MARIA",
            country="UTO",
            nationality="UTO",
            birth_date="740812",
            sex="F",
            expiry_date="120415",
            document_number="L898902C3",
            optional_data="ZE184226B",
            confidence=0.95,
        )

        assert data.mrz_type == "TD3"
        assert data.surname == "ERIKSSON"
        assert data.given_names == "ANNA MARIA"
        assert data.country == "UTO"
        assert data.nationality == "UTO"
        assert data.birth_date == "740812"
        assert data.sex == "F"
        assert data.expiry_date == "120415"
        assert data.document_number == "L898902C3"
        assert data.optional_data == "ZE184226B"
        assert data.confidence == 0.95

    def test_raw_mrz_data_optional_fields_default_to_none(self):
        """Test RawMRZData with minimal required fields."""
        from tryalma.passport.models import RawMRZData

        data = RawMRZData(
            mrz_type="TD3",
            raw_text="P<UTO...",
        )

        assert data.mrz_type == "TD3"
        assert data.raw_text == "P<UTO..."
        assert data.surname is None
        assert data.given_names is None
        assert data.country is None
        assert data.nationality is None
        assert data.birth_date is None
        assert data.sex is None
        assert data.expiry_date is None
        assert data.document_number is None
        assert data.optional_data is None
        assert data.confidence is None


class TestMRZType:
    """Tests for MRZType enum."""

    def test_mrz_type_td1(self):
        """Test MRZType.TD1 value."""
        from tryalma.passport.models import MRZType

        assert MRZType.TD1.value == "TD1"

    def test_mrz_type_td2(self):
        """Test MRZType.TD2 value."""
        from tryalma.passport.models import MRZType

        assert MRZType.TD2.value == "TD2"

    def test_mrz_type_td3(self):
        """Test MRZType.TD3 value."""
        from tryalma.passport.models import MRZType

        assert MRZType.TD3.value == "TD3"

    def test_mrz_type_mrva(self):
        """Test MRZType.MRVA value."""
        from tryalma.passport.models import MRZType

        assert MRZType.MRVA.value == "MRVA"

    def test_mrz_type_mrvb(self):
        """Test MRZType.MRVB value."""
        from tryalma.passport.models import MRZType

        assert MRZType.MRVB.value == "MRVB"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test creating a valid ValidationResult."""
        from tryalma.passport.models import CheckDigitResult, MRZType, ValidationResult

        check_digits = [
            CheckDigitResult(
                field_name="document_number",
                is_valid=True,
                expected="6",
                actual="6",
            ),
            CheckDigitResult(
                field_name="birth_date",
                is_valid=True,
                expected="2",
                actual="2",
            ),
        ]

        result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=check_digits,
            warnings=[],
        )

        assert result.is_valid is True
        assert result.mrz_type == MRZType.TD3
        assert len(result.check_digits) == 2
        assert result.warnings == []

    def test_validation_result_invalid_with_errors(self):
        """Test creating an invalid ValidationResult with check digit errors."""
        from tryalma.passport.models import CheckDigitResult, MRZType, ValidationResult

        check_digits = [
            CheckDigitResult(
                field_name="document_number",
                is_valid=False,
                expected="6",
                actual="5",
            ),
        ]

        result = ValidationResult(
            is_valid=False,
            mrz_type=MRZType.TD3,
            check_digits=check_digits,
            warnings=["Document number check digit mismatch"],
        )

        assert result.is_valid is False
        assert result.check_digits[0].is_valid is False
        assert result.check_digits[0].expected == "6"
        assert result.check_digits[0].actual == "5"
        assert len(result.warnings) == 1


class TestCheckDigitResult:
    """Tests for CheckDigitResult dataclass."""

    def test_check_digit_result_valid(self):
        """Test creating a valid CheckDigitResult."""
        from tryalma.passport.models import CheckDigitResult

        result = CheckDigitResult(
            field_name="document_number",
            is_valid=True,
            expected="6",
            actual="6",
        )

        assert result.field_name == "document_number"
        assert result.is_valid is True
        assert result.expected == "6"
        assert result.actual == "6"

    def test_check_digit_result_invalid(self):
        """Test creating an invalid CheckDigitResult."""
        from tryalma.passport.models import CheckDigitResult

        result = CheckDigitResult(
            field_name="expiry_date",
            is_valid=False,
            expected="9",
            actual="8",
        )

        assert result.field_name == "expiry_date"
        assert result.is_valid is False
        assert result.expected == "9"
        assert result.actual == "8"

    def test_check_digit_result_with_none_values(self):
        """Test CheckDigitResult when expected/actual are None."""
        from tryalma.passport.models import CheckDigitResult

        result = CheckDigitResult(
            field_name="optional",
            is_valid=True,
            expected=None,
            actual=None,
        )

        assert result.expected is None
        assert result.actual is None
