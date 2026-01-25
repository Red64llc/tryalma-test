"""Unit tests for MRZ extractor.

Task 3.1, 3.2: Test MRZExtractor class that wraps PassportEye for MRZ extraction.

Requirements: 1.5, 2.1-2.8, 5.3, 6.1
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestMRZExtractorSupportedExtensions:
    """Tests for SUPPORTED_EXTENSIONS constant."""

    def test_supported_extensions_includes_jpg(self):
        """Test that .jpg is a supported extension."""
        from tryalma.passport.extractor import MRZExtractor

        assert ".jpg" in MRZExtractor.SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_jpeg(self):
        """Test that .jpeg is a supported extension."""
        from tryalma.passport.extractor import MRZExtractor

        assert ".jpeg" in MRZExtractor.SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_png(self):
        """Test that .png is a supported extension."""
        from tryalma.passport.extractor import MRZExtractor

        assert ".png" in MRZExtractor.SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_tiff(self):
        """Test that .tiff is a supported extension."""
        from tryalma.passport.extractor import MRZExtractor

        assert ".tiff" in MRZExtractor.SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_tif(self):
        """Test that .tif is a supported extension."""
        from tryalma.passport.extractor import MRZExtractor

        assert ".tif" in MRZExtractor.SUPPORTED_EXTENSIONS


class TestMRZExtractorIsSupportedFormat:
    """Tests for is_supported_format method."""

    def test_is_supported_format_returns_true_for_jpg(self, tmp_path: Path):
        """Test is_supported_format returns True for .jpg files."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        jpg_path = tmp_path / "passport.jpg"
        jpg_path.touch()

        assert extractor.is_supported_format(jpg_path) is True

    def test_is_supported_format_returns_true_for_jpeg(self, tmp_path: Path):
        """Test is_supported_format returns True for .jpeg files."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        jpeg_path = tmp_path / "passport.jpeg"
        jpeg_path.touch()

        assert extractor.is_supported_format(jpeg_path) is True

    def test_is_supported_format_returns_true_for_png(self, tmp_path: Path):
        """Test is_supported_format returns True for .png files."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        png_path = tmp_path / "passport.png"
        png_path.touch()

        assert extractor.is_supported_format(png_path) is True

    def test_is_supported_format_returns_true_for_tiff(self, tmp_path: Path):
        """Test is_supported_format returns True for .tiff files."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        tiff_path = tmp_path / "passport.tiff"
        tiff_path.touch()

        assert extractor.is_supported_format(tiff_path) is True

    def test_is_supported_format_returns_true_for_tif(self, tmp_path: Path):
        """Test is_supported_format returns True for .tif files."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        tif_path = tmp_path / "passport.tif"
        tif_path.touch()

        assert extractor.is_supported_format(tif_path) is True

    def test_is_supported_format_returns_false_for_pdf(self, tmp_path: Path):
        """Test is_supported_format returns False for unsupported formats."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        pdf_path = tmp_path / "passport.pdf"
        pdf_path.touch()

        assert extractor.is_supported_format(pdf_path) is False

    def test_is_supported_format_returns_false_for_txt(self, tmp_path: Path):
        """Test is_supported_format returns False for .txt files."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        txt_path = tmp_path / "passport.txt"
        txt_path.touch()

        assert extractor.is_supported_format(txt_path) is False

    def test_is_supported_format_case_insensitive(self, tmp_path: Path):
        """Test is_supported_format is case insensitive."""
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        jpg_upper_path = tmp_path / "passport.JPG"
        jpg_upper_path.touch()

        assert extractor.is_supported_format(jpg_upper_path) is True


class TestMRZExtractorCheckTesseractInstalled:
    """Tests for check_tesseract_installed static method."""

    @patch("tryalma.passport.extractor.check_tesseract_installed")
    def test_check_tesseract_installed_returns_true_when_available(
        self, mock_check: MagicMock
    ):
        """Test returns True when Tesseract is found in PATH."""
        from tryalma.passport.extractor import MRZExtractor

        mock_check.return_value = True

        result = MRZExtractor.check_tesseract_installed()

        assert result is True

    @patch("tryalma.passport.extractor.check_tesseract_installed")
    def test_check_tesseract_installed_returns_false_when_unavailable(
        self, mock_check: MagicMock
    ):
        """Test returns False when Tesseract is not found in PATH."""
        from tryalma.passport.extractor import MRZExtractor

        mock_check.return_value = False

        result = MRZExtractor.check_tesseract_installed()

        assert result is False


class TestMRZExtractorGetTesseractInstallInstructions:
    """Tests for get_tesseract_install_instructions static method."""

    def test_get_tesseract_install_instructions_returns_string(self):
        """Test returns installation instructions as string."""
        from tryalma.passport.extractor import MRZExtractor

        instructions = MRZExtractor.get_tesseract_install_instructions()

        assert isinstance(instructions, str)
        assert len(instructions) > 0
        assert "Tesseract" in instructions


class TestMRZExtractorExtract:
    """Tests for extract method."""

    def test_extract_raises_unsupported_format_error_for_invalid_extension(
        self, tmp_path: Path
    ):
        """Test extract raises UnsupportedFormatError for non-image files."""
        from tryalma.passport.exceptions import UnsupportedFormatError
        from tryalma.passport.extractor import MRZExtractor

        extractor = MRZExtractor()
        pdf_path = tmp_path / "passport.pdf"
        pdf_path.write_text("fake pdf content")

        with pytest.raises(UnsupportedFormatError):
            extractor.extract(pdf_path)

    @patch("tryalma.passport.extractor.read_mrz")
    def test_extract_raises_mrz_not_found_error_when_no_mrz_detected(
        self, mock_read_mrz: MagicMock, temp_passport_image: Path
    ):
        """Test extract raises MRZNotFoundError when PassportEye returns None."""
        from tryalma.passport.exceptions import MRZNotFoundError
        from tryalma.passport.extractor import MRZExtractor

        mock_read_mrz.return_value = None

        extractor = MRZExtractor()

        with pytest.raises(MRZNotFoundError):
            extractor.extract(temp_passport_image)

    @patch("tryalma.passport.extractor.read_mrz")
    def test_extract_returns_raw_mrz_data_on_success(
        self, mock_read_mrz: MagicMock, temp_passport_image: Path, mock_passporteye_result
    ):
        """Test extract returns RawMRZData when PassportEye succeeds."""
        from tryalma.passport.extractor import MRZExtractor
        from tryalma.passport.models import RawMRZData

        mock_read_mrz.return_value = mock_passporteye_result

        extractor = MRZExtractor()
        result = extractor.extract(temp_passport_image)

        assert isinstance(result, RawMRZData)
        assert result.mrz_type == "TD3"
        assert result.surname == "ERIKSSON"
        assert result.given_names == "ANNA MARIA"
        assert result.country == "UTO"
        assert result.nationality == "UTO"
        assert result.birth_date == "740812"
        assert result.sex == "F"
        assert result.expiry_date == "120415"
        assert result.document_number == "L898902C3"

    @patch("tryalma.passport.extractor.read_mrz")
    def test_extract_captures_raw_mrz_text(
        self, mock_read_mrz: MagicMock, temp_passport_image: Path
    ):
        """Test extract captures the raw MRZ text lines."""
        from tryalma.passport.extractor import MRZExtractor

        # Create mock with aux attribute containing raw MRZ
        mock_result = MagicMock()
        mock_result.mrz_type = "TD3"
        mock_result.valid = True
        mock_result.valid_score = 1.0
        mock_result.country = "UTO"
        mock_result.nationality = "UTO"
        mock_result.surname = "SMITH"
        mock_result.names = "JOHN"
        mock_result.number = "123456789"
        mock_result.date_of_birth = "850315"
        mock_result.sex = "M"
        mock_result.expiration_date = "300314"
        mock_result.personal_number = ""
        mock_result.optional1 = ""
        mock_result.optional2 = ""

        # PassportEye stores raw MRZ in aux attribute
        aux_mock = MagicMock()
        aux_mock.text = "P<UTOSMITH<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<\n1234567896UTO8503152M3003146<<<<<<<<<<<<<<00"
        mock_result.aux = aux_mock

        mock_read_mrz.return_value = mock_result

        extractor = MRZExtractor()
        result = extractor.extract(temp_passport_image)

        assert result.raw_text is not None
        assert "P<UTO" in result.raw_text

    @patch("tryalma.passport.extractor.read_mrz")
    def test_extract_handles_image_read_error(
        self, mock_read_mrz: MagicMock, tmp_path: Path
    ):
        """Test extract raises ImageReadError for corrupted images."""
        from tryalma.passport.exceptions import ImageReadError
        from tryalma.passport.extractor import MRZExtractor

        # Create a corrupted image file
        corrupted_path = tmp_path / "corrupted.jpg"
        corrupted_path.write_bytes(b"not a valid image")

        # Simulate PassportEye raising an exception for corrupt image
        mock_read_mrz.side_effect = Exception("Cannot read image")

        extractor = MRZExtractor()

        with pytest.raises(ImageReadError):
            extractor.extract(corrupted_path)

    @patch("tryalma.passport.extractor.read_mrz")
    def test_extract_handles_confidence_score(
        self, mock_read_mrz: MagicMock, temp_passport_image: Path
    ):
        """Test extract captures confidence score when available."""
        from tryalma.passport.extractor import MRZExtractor

        mock_result = MagicMock()
        mock_result.mrz_type = "TD3"
        mock_result.valid = True
        mock_result.valid_score = 0.85  # PassportEye's confidence indicator
        mock_result.country = "UTO"
        mock_result.nationality = "UTO"
        mock_result.surname = "SMITH"
        mock_result.names = "JOHN"
        mock_result.number = "123456789"
        mock_result.date_of_birth = "850315"
        mock_result.sex = "M"
        mock_result.expiration_date = "300314"
        mock_result.personal_number = ""
        mock_result.optional1 = ""
        mock_result.optional2 = ""
        mock_result.aux = MagicMock(text="P<UTO...")

        mock_read_mrz.return_value = mock_result

        extractor = MRZExtractor()
        result = extractor.extract(temp_passport_image)

        assert result.confidence == 0.85

    @patch("tryalma.passport.extractor.read_mrz")
    def test_extract_handles_missing_optional_fields(
        self, mock_read_mrz: MagicMock, temp_passport_image: Path
    ):
        """Test extract handles when some MRZ fields are empty."""
        from tryalma.passport.extractor import MRZExtractor

        mock_result = MagicMock()
        mock_result.mrz_type = "TD3"
        mock_result.valid = True
        mock_result.valid_score = 1.0
        mock_result.country = "UTO"
        mock_result.nationality = "UTO"
        mock_result.surname = "SMITH"
        mock_result.names = ""  # Empty names
        mock_result.number = "123456789"
        mock_result.date_of_birth = "850315"
        mock_result.sex = "M"
        mock_result.expiration_date = "300314"
        mock_result.personal_number = ""
        mock_result.optional1 = ""
        mock_result.optional2 = ""
        mock_result.aux = MagicMock(text="P<UTO...")

        mock_read_mrz.return_value = mock_result

        extractor = MRZExtractor()
        result = extractor.extract(temp_passport_image)

        # Empty strings should be converted to None
        assert result.given_names is None


class TestMRZExtractorTesseractErrorHandling:
    """Tests for Tesseract-related error handling."""

    @patch("tryalma.passport.extractor.read_mrz")
    @patch("tryalma.passport.extractor.check_tesseract_installed")
    def test_extract_raises_tesseract_not_found_when_missing(
        self,
        mock_check_tesseract: MagicMock,
        mock_read_mrz: MagicMock,
        temp_passport_image: Path,
    ):
        """Test extract raises TesseractNotFoundError when Tesseract is missing."""
        from tryalma.passport.exceptions import TesseractNotFoundError
        from tryalma.passport.extractor import MRZExtractor

        # Simulate Tesseract not found error from PassportEye
        mock_read_mrz.side_effect = Exception("tesseract is not installed")
        mock_check_tesseract.return_value = False

        extractor = MRZExtractor()

        with pytest.raises(TesseractNotFoundError):
            extractor.extract(temp_passport_image)
