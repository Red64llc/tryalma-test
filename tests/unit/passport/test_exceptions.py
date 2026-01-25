"""Unit tests for passport-specific exceptions.

Task 2.3: Test passport-specific exception classes.

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import pytest


class TestPassportExtractionError:
    """Tests for PassportExtractionError base exception."""

    def test_passport_extraction_error_default_message(self):
        """Test PassportExtractionError has default message."""
        from tryalma.passport.exceptions import PassportExtractionError

        error = PassportExtractionError()

        assert str(error) == "Passport extraction failed"
        assert error.message == "Passport extraction failed"

    def test_passport_extraction_error_custom_message(self):
        """Test PassportExtractionError with custom message."""
        from tryalma.passport.exceptions import PassportExtractionError

        error = PassportExtractionError("Custom error message")

        assert str(error) == "Custom error message"
        assert error.message == "Custom error message"

    def test_passport_extraction_error_inherits_from_processing_error(self):
        """Test PassportExtractionError extends ProcessingError."""
        from tryalma.exceptions import ProcessingError
        from tryalma.passport.exceptions import PassportExtractionError

        error = PassportExtractionError()

        assert isinstance(error, ProcessingError)

    def test_passport_extraction_error_exit_code_is_3(self):
        """Test PassportExtractionError has exit_code 3 (processing error)."""
        from tryalma.passport.exceptions import PassportExtractionError

        error = PassportExtractionError()

        assert error.exit_code == 3


class TestMRZNotFoundError:
    """Tests for MRZNotFoundError exception."""

    def test_mrz_not_found_error_default_message(self):
        """Test MRZNotFoundError has meaningful default message."""
        from tryalma.passport.exceptions import MRZNotFoundError

        error = MRZNotFoundError()

        assert "Machine Readable Zone" in str(error) or "MRZ" in str(error)
        assert "detected" in str(error).lower()

    def test_mrz_not_found_error_custom_message(self):
        """Test MRZNotFoundError with custom message."""
        from tryalma.passport.exceptions import MRZNotFoundError

        error = MRZNotFoundError("No MRZ in passport.jpg")

        assert str(error) == "No MRZ in passport.jpg"

    def test_mrz_not_found_error_inherits_from_passport_extraction_error(self):
        """Test MRZNotFoundError extends PassportExtractionError."""
        from tryalma.passport.exceptions import (
            MRZNotFoundError,
            PassportExtractionError,
        )

        error = MRZNotFoundError()

        assert isinstance(error, PassportExtractionError)

    def test_mrz_not_found_error_exit_code_is_3(self):
        """Test MRZNotFoundError has exit_code 3 (processing error)."""
        from tryalma.passport.exceptions import MRZNotFoundError

        error = MRZNotFoundError()

        assert error.exit_code == 3


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError exception."""

    def test_unsupported_format_error_default_message(self):
        """Test UnsupportedFormatError has meaningful default message."""
        from tryalma.passport.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert "format" in str(error).lower()

    def test_unsupported_format_error_custom_message(self):
        """Test UnsupportedFormatError with custom message."""
        from tryalma.passport.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError("Unsupported format: .bmp")

        assert str(error) == "Unsupported format: .bmp"

    def test_unsupported_format_error_inherits_from_validation_error(self):
        """Test UnsupportedFormatError extends ValidationError."""
        from tryalma.exceptions import ValidationError
        from tryalma.passport.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert isinstance(error, ValidationError)

    def test_unsupported_format_error_exit_code_is_2(self):
        """Test UnsupportedFormatError has exit_code 2 (validation error)."""
        from tryalma.passport.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert error.exit_code == 2


class TestTesseractNotFoundError:
    """Tests for TesseractNotFoundError exception."""

    def test_tesseract_not_found_error_contains_instructions(self):
        """Test TesseractNotFoundError message includes install instructions."""
        from tryalma.passport.exceptions import TesseractNotFoundError

        error = TesseractNotFoundError()

        message = str(error)
        assert "Tesseract" in message
        # Should include some installation guidance
        assert "install" in message.lower()

    def test_tesseract_not_found_error_inherits_from_passport_extraction_error(self):
        """Test TesseractNotFoundError extends PassportExtractionError."""
        from tryalma.passport.exceptions import (
            PassportExtractionError,
            TesseractNotFoundError,
        )

        error = TesseractNotFoundError()

        assert isinstance(error, PassportExtractionError)

    def test_tesseract_not_found_error_exit_code_is_1(self):
        """Test TesseractNotFoundError has exit_code 1 (configuration error)."""
        from tryalma.passport.exceptions import TesseractNotFoundError

        error = TesseractNotFoundError()

        assert error.exit_code == 1


class TestImageReadError:
    """Tests for ImageReadError exception."""

    def test_image_read_error_default_message(self):
        """Test ImageReadError has meaningful default message."""
        from tryalma.passport.exceptions import ImageReadError

        error = ImageReadError()

        assert "image" in str(error).lower() or "read" in str(error).lower()

    def test_image_read_error_custom_message(self):
        """Test ImageReadError with custom message."""
        from tryalma.passport.exceptions import ImageReadError

        error = ImageReadError("Could not read corrupted.jpg: file is corrupted")

        assert str(error) == "Could not read corrupted.jpg: file is corrupted"

    def test_image_read_error_inherits_from_passport_extraction_error(self):
        """Test ImageReadError extends PassportExtractionError."""
        from tryalma.passport.exceptions import (
            ImageReadError,
            PassportExtractionError,
        )

        error = ImageReadError()

        assert isinstance(error, PassportExtractionError)

    def test_image_read_error_exit_code_is_3(self):
        """Test ImageReadError has exit_code 3 (processing error)."""
        from tryalma.passport.exceptions import ImageReadError

        error = ImageReadError()

        assert error.exit_code == 3


class TestExceptionHierarchy:
    """Tests for exception hierarchy relationships."""

    def test_all_passport_exceptions_extend_cli_error(self):
        """Test all passport exceptions eventually extend CLIError."""
        from tryalma.exceptions import CLIError
        from tryalma.passport.exceptions import (
            ImageReadError,
            MRZNotFoundError,
            PassportExtractionError,
            TesseractNotFoundError,
            UnsupportedFormatError,
        )

        exceptions = [
            PassportExtractionError(),
            MRZNotFoundError(),
            UnsupportedFormatError(),
            TesseractNotFoundError(),
            ImageReadError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, CLIError), f"{type(exc).__name__} should extend CLIError"

    def test_exceptions_are_catchable_by_base_type(self):
        """Test exceptions can be caught by their base types."""
        from tryalma.passport.exceptions import (
            ImageReadError,
            MRZNotFoundError,
            PassportExtractionError,
        )

        # MRZNotFoundError should be catchable as PassportExtractionError
        with pytest.raises(PassportExtractionError):
            raise MRZNotFoundError()

        # ImageReadError should be catchable as PassportExtractionError
        with pytest.raises(PassportExtractionError):
            raise ImageReadError()
