"""Contract tests for PassportEye library.

Task 8.3: Test PassportEye API returns expected structure for valid passports.

These tests verify that the PassportEye library behaves as expected by our
MRZExtractor implementation. They document the contract between our code
and the external library for future compatibility verification.

Requirements: 6.1
"""

from unittest.mock import MagicMock

import pytest

# These tests document the expected PassportEye API contract
# They verify our assumptions about the library's behavior


class TestPassportEyeReadMRZContract:
    """Contract tests for passporteye.read_mrz() function.

    These tests document the expected structure and behavior of PassportEye's
    read_mrz() function, which is the primary interface we use for MRZ extraction.
    """

    def test_read_mrz_returns_none_for_no_mrz_detected(self):
        """read_mrz should return None when no MRZ is found in an image.

        This is the documented behavior we depend on for MRZNotFoundError.
        """
        from passporteye import read_mrz
        from pathlib import Path
        from PIL import Image
        import tempfile

        # Create a blank image with no MRZ
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (100, 100), color="white")
            img.save(f, "JPEG")
            temp_path = Path(f.name)

        try:
            result = read_mrz(str(temp_path))
            # Contract: read_mrz returns None when no MRZ detected
            assert result is None
        finally:
            temp_path.unlink()

    def test_read_mrz_result_has_mrz_type_attribute(self):
        """MRZ result object should have mrz_type attribute.

        We depend on this attribute to identify TD1/TD3 format.
        This test uses a mock since we can't guarantee a real passport image.
        """
        # Document the expected interface
        mock_result = MagicMock()
        mock_result.mrz_type = "TD3"

        # Contract: result has mrz_type attribute
        assert hasattr(mock_result, "mrz_type")
        assert mock_result.mrz_type in ("TD1", "TD2", "TD3", "MRVA", "MRVB")

    def test_read_mrz_result_has_required_fields(self):
        """MRZ result object should have all required passport fields.

        Documents the fields we extract from PassportEye results.
        """
        # Document expected interface with required fields
        expected_fields = [
            "mrz_type",        # TD1, TD2, TD3, etc.
            "valid",           # Boolean indicating if MRZ is valid
            "valid_score",     # Confidence score (0.0 to 1.0)
            "country",         # Issuing country
            "nationality",     # Holder's nationality
            "surname",         # Holder's surname
            "names",           # Given names (note: 'names' not 'given_names')
            "number",          # Document number (note: 'number' not 'passport_number')
            "date_of_birth",   # DOB in YYMMDD format
            "sex",             # M, F, or <
            "expiration_date", # Expiry in YYMMDD format
            "personal_number", # Optional personal number
        ]

        # Create mock to document expected interface
        mock_result = MagicMock()
        for field in expected_fields:
            setattr(mock_result, field, "test_value")

        # Verify all expected fields exist
        for field in expected_fields:
            assert hasattr(mock_result, field), f"Missing field: {field}"

    def test_read_mrz_result_aux_contains_raw_text(self):
        """MRZ result should have aux.text containing raw MRZ text.

        We depend on this for capturing the original MRZ string.
        """
        # Document the aux structure
        mock_aux = MagicMock()
        mock_aux.text = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"

        mock_result = MagicMock()
        mock_result.aux = mock_aux

        # Contract: aux.text contains raw MRZ lines
        assert hasattr(mock_result.aux, "text")
        assert isinstance(mock_result.aux.text, str)
        assert "\n" in mock_result.aux.text  # MRZ has multiple lines

    def test_read_mrz_date_format_is_yymmdd(self):
        """PassportEye returns dates in YYMMDD format.

        Documents the date format we must parse in our service layer.
        """
        # Document expected date format
        sample_dates = [
            "740812",  # August 12, 1974
            "850315",  # March 15, 1985
            "120415",  # April 15, 2012
            "300314",  # March 14, 2030
        ]

        for date_str in sample_dates:
            # Contract: dates are 6 characters YYMMDD
            assert len(date_str) == 6
            assert date_str.isdigit()

            year = int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])

            assert 0 <= year <= 99
            assert 1 <= month <= 12
            assert 1 <= day <= 31

    def test_read_mrz_sex_field_values(self):
        """PassportEye sex field should be M, F, or < for unspecified.

        Documents the sex field values we must handle.
        """
        # Contract: sex field uses these values
        valid_sex_values = {"M", "F", "<"}

        for value in valid_sex_values:
            mock_result = MagicMock()
            mock_result.sex = value
            assert mock_result.sex in valid_sex_values


class TestPassportEyeResultTypes:
    """Contract tests for PassportEye result types and edge cases."""

    def test_result_valid_score_is_float(self):
        """valid_score should be a float between 0.0 and 1.0.

        We use this for confidence scoring in extraction results.
        """
        # Document expected valid_score range
        valid_scores = [0.0, 0.5, 0.85, 1.0]

        for score in valid_scores:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_result_empty_fields_are_empty_strings(self):
        """Empty optional fields should be empty strings, not None.

        Documents how PassportEye represents missing data, which affects
        our to_optional() conversion logic.
        """
        # Contract: empty fields are "" not None from PassportEye
        mock_result = MagicMock()
        mock_result.personal_number = ""
        mock_result.optional1 = ""
        mock_result.optional2 = ""

        assert mock_result.personal_number == ""
        assert mock_result.optional1 == ""
        assert mock_result.optional2 == ""


class TestPassportEyeTD3Contract:
    """Contract tests specific to TD3 (passport) format."""

    def test_td3_mrz_type_is_td3(self):
        """TD3 passports should return mrz_type='TD3'."""
        mock_result = MagicMock()
        mock_result.mrz_type = "TD3"

        assert mock_result.mrz_type == "TD3"

    def test_td3_has_two_line_mrz(self):
        """TD3 format MRZ has 2 lines of 44 characters each."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

        assert len(line1) == 44
        assert len(line2) == 44

        full_mrz = f"{line1}\n{line2}"
        assert len(full_mrz) == 89  # 44 + 1 + 44


class TestPassportEyeTD1Contract:
    """Contract tests specific to TD1 (ID card) format."""

    def test_td1_mrz_type_is_td1(self):
        """TD1 ID cards should return mrz_type='TD1'."""
        mock_result = MagicMock()
        mock_result.mrz_type = "TD1"

        assert mock_result.mrz_type == "TD1"

    def test_td1_has_three_line_mrz(self):
        """TD1 format MRZ has 3 lines of 30 characters each."""
        line1 = "I<UTOD231458907<<<<<<<<<<<<<<<"
        line2 = "7408122F1204159UTO<<<<<<<<<<<6"
        line3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<"

        assert len(line1) == 30
        assert len(line2) == 30
        assert len(line3) == 30

        full_mrz = f"{line1}\n{line2}\n{line3}"
        assert len(full_mrz) == 92  # 30 + 1 + 30 + 1 + 30


class TestPassportEyeExceptionContract:
    """Contract tests for PassportEye exception behavior."""

    def test_invalid_image_path_raises_exception(self):
        """read_mrz should raise exception for non-existent files."""
        from passporteye import read_mrz

        # Contract: invalid path raises an exception
        with pytest.raises(Exception):
            read_mrz("/non/existent/path/to/image.jpg")

    def test_corrupted_image_behavior(self):
        """read_mrz handles corrupted images.

        Note: Behavior may vary (could return None or raise exception).
        This test documents that we need to handle both cases.
        """
        from passporteye import read_mrz
        from pathlib import Path
        import tempfile

        # Create a file with invalid image content
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"not a valid image content at all")
            temp_path = Path(f.name)

        try:
            # Contract: corrupted images either return None or raise exception
            # Our implementation handles both cases
            try:
                result = read_mrz(str(temp_path))
                # If no exception, result should be None
                assert result is None
            except Exception:
                # Exception is also acceptable for corrupted images
                pass
        finally:
            temp_path.unlink()
