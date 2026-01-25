"""Unit tests for G28-specific exceptions.

Task 2: Exception hierarchy for G28 form extraction failures.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest


class TestG28ExtractionError:
    """Tests for G28ExtractionError base exception."""

    def test_g28_extraction_error_default_message(self):
        """Test G28ExtractionError has default message."""
        from tryalma.g28.exceptions import G28ExtractionError

        error = G28ExtractionError()

        assert str(error) == "G-28 form extraction failed"
        assert error.message == "G-28 form extraction failed"

    def test_g28_extraction_error_custom_message(self):
        """Test G28ExtractionError with custom message."""
        from tryalma.g28.exceptions import G28ExtractionError

        error = G28ExtractionError("Custom error message")

        assert str(error) == "Custom error message"
        assert error.message == "Custom error message"

    def test_g28_extraction_error_inherits_from_processing_error(self):
        """Test G28ExtractionError extends ProcessingError."""
        from tryalma.exceptions import ProcessingError
        from tryalma.g28.exceptions import G28ExtractionError

        error = G28ExtractionError()

        assert isinstance(error, ProcessingError)

    def test_g28_extraction_error_exit_code_is_3(self):
        """Test G28ExtractionError has exit_code 3 (processing error)."""
        from tryalma.g28.exceptions import G28ExtractionError

        error = G28ExtractionError()

        assert error.exit_code == 3


class TestNotG28FormError:
    """Tests for NotG28FormError exception."""

    def test_not_g28_form_error_default_message(self):
        """Test NotG28FormError has meaningful default message about form type mismatch."""
        from tryalma.g28.exceptions import NotG28FormError

        error = NotG28FormError()

        message = str(error)
        assert "G-28" in message
        assert "not recognized" in message.lower() or "not" in message.lower()

    def test_not_g28_form_error_custom_message(self):
        """Test NotG28FormError with custom message."""
        from tryalma.g28.exceptions import NotG28FormError

        error = NotG28FormError("Detected form I-130 instead of G-28")

        assert str(error) == "Detected form I-130 instead of G-28"

    def test_not_g28_form_error_inherits_from_g28_extraction_error(self):
        """Test NotG28FormError extends G28ExtractionError."""
        from tryalma.g28.exceptions import G28ExtractionError, NotG28FormError

        error = NotG28FormError()

        assert isinstance(error, G28ExtractionError)

    def test_not_g28_form_error_exit_code_is_3(self):
        """Test NotG28FormError has exit_code 3 (processing error)."""
        from tryalma.g28.exceptions import NotG28FormError

        error = NotG28FormError()

        assert error.exit_code == 3


class TestDocumentLoadError:
    """Tests for DocumentLoadError exception."""

    def test_document_load_error_default_message(self):
        """Test DocumentLoadError has meaningful default message."""
        from tryalma.g28.exceptions import DocumentLoadError

        error = DocumentLoadError()

        message = str(error)
        assert "load" in message.lower() or "document" in message.lower()

    def test_document_load_error_custom_message(self):
        """Test DocumentLoadError with custom message."""
        from tryalma.g28.exceptions import DocumentLoadError

        error = DocumentLoadError("Failed to convert PDF: corrupted file")

        assert str(error) == "Failed to convert PDF: corrupted file"

    def test_document_load_error_inherits_from_g28_extraction_error(self):
        """Test DocumentLoadError extends G28ExtractionError."""
        from tryalma.g28.exceptions import DocumentLoadError, G28ExtractionError

        error = DocumentLoadError()

        assert isinstance(error, G28ExtractionError)

    def test_document_load_error_exit_code_is_3(self):
        """Test DocumentLoadError has exit_code 3 (processing error)."""
        from tryalma.g28.exceptions import DocumentLoadError

        error = DocumentLoadError()

        assert error.exit_code == 3


class TestExtractionAPIError:
    """Tests for ExtractionAPIError exception."""

    def test_extraction_api_error_default_message(self):
        """Test ExtractionAPIError has meaningful default message."""
        from tryalma.g28.exceptions import ExtractionAPIError

        error = ExtractionAPIError()

        message = str(error)
        assert "extraction" in message.lower() or "service" in message.lower() or "api" in message.lower()

    def test_extraction_api_error_custom_message(self):
        """Test ExtractionAPIError with custom message."""
        from tryalma.g28.exceptions import ExtractionAPIError

        error = ExtractionAPIError("Claude API rate limit exceeded")

        assert str(error) == "Claude API rate limit exceeded"

    def test_extraction_api_error_inherits_from_g28_extraction_error(self):
        """Test ExtractionAPIError extends G28ExtractionError."""
        from tryalma.g28.exceptions import ExtractionAPIError, G28ExtractionError

        error = ExtractionAPIError()

        assert isinstance(error, G28ExtractionError)

    def test_extraction_api_error_exit_code_is_3(self):
        """Test ExtractionAPIError has exit_code 3 (processing error)."""
        from tryalma.g28.exceptions import ExtractionAPIError

        error = ExtractionAPIError()

        assert error.exit_code == 3


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError exception (G28-specific)."""

    def test_unsupported_format_error_default_message(self):
        """Test UnsupportedFormatError has meaningful default message with supported formats."""
        from tryalma.g28.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        message = str(error)
        assert "format" in message.lower()
        # Should mention supported formats
        assert "pdf" in message.lower() or "PNG" in message or "supported" in message.lower()

    def test_unsupported_format_error_custom_message(self):
        """Test UnsupportedFormatError with custom message."""
        from tryalma.g28.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError("File format .doc is not supported")

        assert str(error) == "File format .doc is not supported"

    def test_unsupported_format_error_inherits_from_validation_error(self):
        """Test UnsupportedFormatError extends ValidationError."""
        from tryalma.exceptions import ValidationError
        from tryalma.g28.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert isinstance(error, ValidationError)

    def test_unsupported_format_error_exit_code_is_2(self):
        """Test UnsupportedFormatError has exit_code 2 (validation error)."""
        from tryalma.g28.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert error.exit_code == 2


class TestLowQualityWarning:
    """Tests for LowQualityWarning exception."""

    def test_low_quality_warning_default_message(self):
        """Test LowQualityWarning has meaningful default message."""
        from tryalma.g28.exceptions import LowQualityWarning

        error = LowQualityWarning()

        message = str(error)
        assert "quality" in message.lower()

    def test_low_quality_warning_custom_message(self):
        """Test LowQualityWarning with custom message."""
        from tryalma.g28.exceptions import LowQualityWarning

        error = LowQualityWarning("Image resolution too low: 72 DPI")

        assert str(error) == "Image resolution too low: 72 DPI"

    def test_low_quality_warning_inherits_from_g28_extraction_error(self):
        """Test LowQualityWarning extends G28ExtractionError."""
        from tryalma.g28.exceptions import G28ExtractionError, LowQualityWarning

        error = LowQualityWarning()

        assert isinstance(error, G28ExtractionError)

    def test_low_quality_warning_exit_code_is_3(self):
        """Test LowQualityWarning has exit_code 3 (processing error)."""
        from tryalma.g28.exceptions import LowQualityWarning

        error = LowQualityWarning()

        assert error.exit_code == 3


class TestG28ExceptionHierarchy:
    """Tests for G28 exception hierarchy relationships."""

    def test_all_g28_exceptions_extend_cli_error(self):
        """Test all G28 exceptions eventually extend CLIError."""
        from tryalma.exceptions import CLIError
        from tryalma.g28.exceptions import (
            DocumentLoadError,
            ExtractionAPIError,
            G28ExtractionError,
            LowQualityWarning,
            NotG28FormError,
            UnsupportedFormatError,
        )

        exceptions = [
            G28ExtractionError(),
            NotG28FormError(),
            DocumentLoadError(),
            ExtractionAPIError(),
            UnsupportedFormatError(),
            LowQualityWarning(),
        ]

        for exc in exceptions:
            assert isinstance(exc, CLIError), f"{type(exc).__name__} should extend CLIError"

    def test_exceptions_are_catchable_by_base_type(self):
        """Test exceptions can be caught by their base types."""
        from tryalma.g28.exceptions import (
            DocumentLoadError,
            ExtractionAPIError,
            G28ExtractionError,
            LowQualityWarning,
            NotG28FormError,
        )

        # NotG28FormError should be catchable as G28ExtractionError
        with pytest.raises(G28ExtractionError):
            raise NotG28FormError()

        # DocumentLoadError should be catchable as G28ExtractionError
        with pytest.raises(G28ExtractionError):
            raise DocumentLoadError()

        # ExtractionAPIError should be catchable as G28ExtractionError
        with pytest.raises(G28ExtractionError):
            raise ExtractionAPIError()

        # LowQualityWarning should be catchable as G28ExtractionError
        with pytest.raises(G28ExtractionError):
            raise LowQualityWarning()

    def test_unsupported_format_error_not_catchable_as_g28_extraction_error(self):
        """Test UnsupportedFormatError is NOT catchable as G28ExtractionError.

        This is because UnsupportedFormatError extends ValidationError (exit code 2),
        not G28ExtractionError (exit code 3).
        """
        from tryalma.g28.exceptions import G28ExtractionError, UnsupportedFormatError

        error = UnsupportedFormatError()

        assert not isinstance(error, G28ExtractionError)

    def test_all_exceptions_have_exit_code_attribute(self):
        """Test all G28 exceptions have exit_code attribute."""
        from tryalma.g28.exceptions import (
            DocumentLoadError,
            ExtractionAPIError,
            G28ExtractionError,
            LowQualityWarning,
            NotG28FormError,
            UnsupportedFormatError,
        )

        exceptions = [
            G28ExtractionError(),
            NotG28FormError(),
            DocumentLoadError(),
            ExtractionAPIError(),
            UnsupportedFormatError(),
            LowQualityWarning(),
        ]

        for exc in exceptions:
            assert hasattr(exc, "exit_code"), f"{type(exc).__name__} should have exit_code"
            assert isinstance(exc.exit_code, int), f"{type(exc).__name__}.exit_code should be int"

    def test_processing_errors_have_exit_code_3(self):
        """Test all processing-related errors have exit code 3."""
        from tryalma.g28.exceptions import (
            DocumentLoadError,
            ExtractionAPIError,
            G28ExtractionError,
            LowQualityWarning,
            NotG28FormError,
        )

        processing_exceptions = [
            G28ExtractionError(),
            NotG28FormError(),
            DocumentLoadError(),
            ExtractionAPIError(),
            LowQualityWarning(),
        ]

        for exc in processing_exceptions:
            assert exc.exit_code == 3, f"{type(exc).__name__} should have exit_code 3"

    def test_validation_errors_have_exit_code_2(self):
        """Test all validation-related errors have exit code 2."""
        from tryalma.g28.exceptions import UnsupportedFormatError

        validation_exceptions = [
            UnsupportedFormatError(),
        ]

        for exc in validation_exceptions:
            assert exc.exit_code == 2, f"{type(exc).__name__} should have exit_code 2"
