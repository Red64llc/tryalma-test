"""Tests for PassportExtractionService.

Task 5.1: Single image extraction workflow
Task 5.2: Batch directory processing

Requirements: 1.1, 1.2, 1.4, 5.1, 5.2
"""

from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tryalma.passport.exceptions import (
    ImageReadError,
    MRZNotFoundError,
    PassportExtractionError,
    UnsupportedFormatError,
)
from tryalma.passport.models import (
    CheckDigitResult,
    ExtractionResult,
    MRZType,
    PassportData,
    RawMRZData,
    ValidationResult,
)


class TestPassportExtractionServiceInit:
    """Test PassportExtractionService initialization."""

    def test_service_accepts_extractor_and_validator(self):
        """Service can be instantiated with extractor and validator dependencies."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        assert service is not None
        assert service._extractor is mock_extractor
        assert service._validator is mock_validator

    def test_service_stores_dependencies_for_later_use(self):
        """Service stores dependencies as instance attributes."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        assert hasattr(service, "_extractor")
        assert hasattr(service, "_validator")


class TestPassportExtractionServiceExtractSingle:
    """Test extract_single method for single image processing."""

    def test_extract_single_returns_extraction_result(self, tmp_path):
        """extract_single returns an ExtractionResult object."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        # Set up successful extraction
        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="P<UTOERIKSSON<<ANNA<MARIA\nL898902C3...",
            surname="ERIKSSON",
            given_names="ANNA MARIA",
            nationality="UTO",
            birth_date="740812",
            sex="F",
            expiry_date="120415",
            document_number="L898902C3",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert isinstance(result, ExtractionResult)

    def test_extract_single_success_sets_correct_fields(self, tmp_path):
        """On successful extraction, result contains passport data."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="P<UTOERIKSSON<<ANNA<MARIA\nL898902C3...",
            surname="ERIKSSON",
            given_names="ANNA MARIA",
            nationality="UTO",
            birth_date="740812",
            sex="F",
            expiry_date="120415",
            document_number="L898902C3",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert result.source_file == image_path

    def test_extract_single_parses_dates_correctly(self, tmp_path):
        """Dates are parsed from YYMMDD format to Python date objects."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test mrz",
            surname="SMITH",
            given_names="JOHN",
            nationality="USA",
            birth_date="850315",  # March 15, 1985
            sex="M",
            expiry_date="300314",  # March 14, 2030
            document_number="123456789",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.date_of_birth == date(1985, 3, 15)
        assert result.data.expiry_date == date(2030, 3, 14)

    def test_extract_single_handles_century_crossover_dates(self, tmp_path):
        """Birth dates handle century crossover (e.g., 74 -> 1974)."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test mrz",
            surname="DOE",
            given_names="JANE",
            nationality="GBR",
            birth_date="740812",  # August 12, 1974
            sex="F",
            expiry_date="120415",  # April 15, 2012
            document_number="ABC123456",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        # 74 should be 1974, not 2074
        assert result.data.date_of_birth == date(1974, 8, 12)

    def test_extract_single_includes_validation_status(self, tmp_path):
        """Extraction result includes MRZ validation status."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="P<UTOERIKSSON<<ANNA<MARIA\nL898902C3...",
            surname="ERIKSSON",
            given_names="ANNA MARIA",
            nationality="UTO",
            birth_date="740812",
            sex="F",
            expiry_date="120415",
            document_number="L898902C3",
        )
        mock_extractor.extract.return_value = raw_mrz

        check_digit_error = CheckDigitResult(
            field_name="document_number_check_digit",
            is_valid=False,
            expected="5",
            actual="3",
        )
        validation_result = ValidationResult(
            is_valid=False,
            mrz_type=MRZType.TD3,
            check_digits=[check_digit_error],
            warnings=["Document number check digit invalid"],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is True  # Extraction succeeded even if validation failed
        assert result.data.mrz_valid is False
        assert len(result.data.check_digit_errors) > 0

    def test_extract_single_handles_mrz_not_found_error(self, tmp_path):
        """When no MRZ is found, returns failure result with error message."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        mock_extractor.extract.side_effect = MRZNotFoundError("No MRZ found")

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "No MRZ" in result.error or "MRZ" in result.error

    def test_extract_single_handles_unsupported_format_error(self, tmp_path):
        """When format is unsupported, returns failure result."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        mock_extractor.extract.side_effect = UnsupportedFormatError(
            "Unsupported format: .pdf"
        )

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.pdf"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is False
        assert result.error is not None
        assert "Unsupported" in result.error or "format" in result.error.lower()

    def test_extract_single_handles_image_read_error(self, tmp_path):
        """When image cannot be read, returns failure result."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        mock_extractor.extract.side_effect = ImageReadError("Could not read image")

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "corrupted.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is False
        assert result.error is not None

    def test_extract_single_provides_user_friendly_error_messages(self, tmp_path):
        """Error messages are user-friendly without stack traces."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        mock_extractor.extract.side_effect = MRZNotFoundError(
            "No Machine Readable Zone (MRZ) detected in image"
        )

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        # Error should not contain Python traceback indicators
        assert "Traceback" not in str(result.error)
        assert "File " not in str(result.error)


class TestPassportExtractionServiceExtractBatch:
    """Test extract_batch method for directory processing."""

    def test_extract_batch_returns_list_of_extraction_results(self, tmp_path):
        """extract_batch returns a list of ExtractionResult objects."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()
        mock_extractor.is_supported_format.return_value = True

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        # Create test images
        for i in range(3):
            (tmp_path / f"passport_{i}.jpg").touch()

        results = service.extract_batch(tmp_path)

        assert isinstance(results, list)
        assert all(isinstance(r, ExtractionResult) for r in results)

    def test_extract_batch_processes_all_supported_images(self, tmp_path):
        """Batch processing includes all supported image formats."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        def is_supported(path):
            return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

        mock_extractor.is_supported_format.side_effect = is_supported

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        # Create test images with different formats
        (tmp_path / "test1.jpg").touch()
        (tmp_path / "test2.png").touch()
        (tmp_path / "test3.tiff").touch()
        (tmp_path / "readme.txt").touch()  # Should be skipped

        results = service.extract_batch(tmp_path)

        assert len(results) == 3  # Only image files processed

    def test_extract_batch_continues_on_individual_file_errors(self, tmp_path):
        """Batch processing continues when individual files fail."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()
        mock_extractor.is_supported_format.return_value = True

        # First file fails, second succeeds
        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="M",
            expiry_date="300101",
            document_number="123",
        )

        call_count = [0]

        def extract_side_effect(path):
            call_count[0] += 1
            if call_count[0] == 1:
                raise MRZNotFoundError("No MRZ in first image")
            return raw_mrz

        mock_extractor.extract.side_effect = extract_side_effect

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        # Create test images
        (tmp_path / "fail.jpg").touch()
        (tmp_path / "success.jpg").touch()

        results = service.extract_batch(tmp_path)

        # Both files should have results
        assert len(results) == 2
        # One should be failure, one success
        failures = [r for r in results if not r.success]
        successes = [r for r in results if r.success]
        assert len(failures) == 1
        assert len(successes) == 1

    def test_extract_batch_supports_progress_callback(self, tmp_path):
        """Batch processing calls progress callback with current/total."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()
        mock_extractor.is_supported_format.return_value = True

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        # Create test images
        for i in range(3):
            (tmp_path / f"passport_{i}.jpg").touch()

        progress_calls = []

        def progress_callback(current: int, total: int):
            progress_calls.append((current, total))

        service.extract_batch(tmp_path, on_progress=progress_callback)

        # Progress should have been called for each file
        assert len(progress_calls) == 3
        # Check progress values
        assert progress_calls[0] == (1, 3)
        assert progress_calls[1] == (2, 3)
        assert progress_calls[2] == (3, 3)

    def test_extract_batch_returns_empty_list_for_empty_directory(self, tmp_path):
        """Empty directory returns empty results list."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        results = service.extract_batch(tmp_path)

        assert results == []


class TestPassportExtractionServiceGetSupportedExtensions:
    """Test get_supported_extensions method."""

    def test_get_supported_extensions_returns_set(self):
        """get_supported_extensions returns a set of file extensions."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_extractor.SUPPORTED_EXTENSIONS = {".jpg", ".png"}
        mock_validator = Mock()

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        extensions = service.get_supported_extensions()

        assert isinstance(extensions, set)

    def test_get_supported_extensions_delegates_to_extractor(self):
        """Supported extensions come from the extractor."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_extractor.SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
        mock_validator = Mock()

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        extensions = service.get_supported_extensions()

        assert extensions == {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


class TestPassportExtractionServiceDateParsing:
    """Test date parsing utilities."""

    def test_date_parsing_handles_future_expiry_dates(self, tmp_path):
        """Expiry dates in the future are parsed correctly."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="M",
            expiry_date="350615",  # June 15, 2035
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.expiry_date == date(2035, 6, 15)

    def test_date_parsing_handles_invalid_dates_gracefully(self, tmp_path):
        """Invalid date formats result in None instead of crashing."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="INVALID",  # Not a valid date
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        # Should still succeed, just with None date
        assert result.success is True
        assert result.data.date_of_birth is None

    def test_date_parsing_handles_none_dates(self, tmp_path):
        """None date values are handled correctly."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date=None,
            sex="M",
            expiry_date=None,
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is True
        assert result.data.date_of_birth is None
        assert result.data.expiry_date is None

    def test_date_parsing_handles_short_dates(self, tmp_path):
        """Short date strings (< 6 chars) result in None."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="12345",  # Too short (5 chars)
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is True
        assert result.data.date_of_birth is None

    def test_date_parsing_handles_impossible_dates(self, tmp_path):
        """Impossible dates (e.g., Feb 31) result in None."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="850231",  # February 31 doesn't exist
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is True
        assert result.data.date_of_birth is None


class TestPassportExtractionServiceSexNormalization:
    """Test sex field normalization."""

    def test_sex_normalization_returns_m_for_male(self, tmp_path):
        """Sex 'M' is returned as-is."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="M",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.sex == "M"

    def test_sex_normalization_returns_f_for_female(self, tmp_path):
        """Sex 'F' is returned as-is."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="F",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.sex == "F"

    def test_sex_normalization_returns_none_for_unspecified(self, tmp_path):
        """Sex '<' (unspecified in MRZ) becomes None."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="<",
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.sex is None

    def test_sex_normalization_handles_lowercase(self, tmp_path):
        """Lowercase sex values are normalized to uppercase."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex="m",  # lowercase
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.sex == "M"

    def test_sex_normalization_returns_none_for_none_input(self, tmp_path):
        """None sex input remains None."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        raw_mrz = RawMRZData(
            mrz_type="TD3",
            raw_text="test",
            surname="TEST",
            given_names="USER",
            nationality="USA",
            birth_date="900101",
            sex=None,
            expiry_date="300101",
            document_number="123",
        )
        mock_extractor.extract.return_value = raw_mrz

        validation_result = ValidationResult(
            is_valid=True,
            mrz_type=MRZType.TD3,
            check_digits=[],
            warnings=[],
        )
        mock_validator.validate.return_value = validation_result

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.data.sex is None


class TestPassportExtractionServiceUnexpectedErrors:
    """Test handling of unexpected errors."""

    def test_extract_single_handles_unexpected_exception(self, tmp_path):
        """Unexpected exceptions are caught and return failure result."""
        from tryalma.passport.service import PassportExtractionService

        mock_extractor = Mock()
        mock_validator = Mock()

        # Simulate an unexpected error
        mock_extractor.extract.side_effect = RuntimeError("Unexpected internal error")

        service = PassportExtractionService(
            extractor=mock_extractor,
            validator=mock_validator,
        )

        image_path = tmp_path / "test.jpg"
        image_path.touch()

        result = service.extract_single(image_path)

        assert result.success is False
        assert result.error is not None
        assert "Extraction failed" in result.error
