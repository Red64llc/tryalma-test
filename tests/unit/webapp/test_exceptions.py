"""Tests for WebApp exception hierarchy.

TDD: RED phase - These tests define expected behavior for webapp exceptions.
"""

import pytest


class TestWebAppError:
    """Tests for base WebAppError class."""

    def test_webapp_error_has_default_status_code(self):
        """WebAppError should have 500 as default status code."""
        from tryalma.webapp.exceptions import WebAppError

        error = WebAppError()

        assert error.status_code == 500

    def test_webapp_error_has_default_error_code(self):
        """WebAppError should have INTERNAL_ERROR as default error code."""
        from tryalma.webapp.exceptions import WebAppError

        error = WebAppError()

        assert error.error_code == "INTERNAL_ERROR"

    def test_webapp_error_has_default_message(self):
        """WebAppError should have a default message."""
        from tryalma.webapp.exceptions import WebAppError

        error = WebAppError()

        assert error.message == "An unexpected error occurred"

    def test_webapp_error_accepts_custom_message(self):
        """WebAppError should accept custom message."""
        from tryalma.webapp.exceptions import WebAppError

        error = WebAppError("Custom error message")

        assert error.message == "Custom error message"

    def test_webapp_error_inherits_from_exception(self):
        """WebAppError should be an Exception."""
        from tryalma.webapp.exceptions import WebAppError

        error = WebAppError()

        assert isinstance(error, Exception)


class TestFileValidationError:
    """Tests for FileValidationError class."""

    def test_file_validation_error_has_status_400(self):
        """FileValidationError should have 400 status code."""
        from tryalma.webapp.exceptions import FileValidationError

        error = FileValidationError()

        assert error.status_code == 400

    def test_file_validation_error_has_validation_error_code(self):
        """FileValidationError should have VALIDATION_ERROR code."""
        from tryalma.webapp.exceptions import FileValidationError

        error = FileValidationError()

        assert error.error_code == "VALIDATION_ERROR"

    def test_file_validation_error_inherits_from_webapp_error(self):
        """FileValidationError should inherit from WebAppError."""
        from tryalma.webapp.exceptions import FileValidationError, WebAppError

        error = FileValidationError()

        assert isinstance(error, WebAppError)

    def test_file_validation_error_inherits_from_validation_error(self):
        """FileValidationError should inherit from tryalma ValidationError."""
        from tryalma.exceptions import ValidationError
        from tryalma.webapp.exceptions import FileValidationError

        error = FileValidationError()

        assert isinstance(error, ValidationError)


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError class."""

    def test_unsupported_format_error_has_status_415(self):
        """UnsupportedFormatError should have 415 status code."""
        from tryalma.webapp.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert error.status_code == 415

    def test_unsupported_format_error_has_correct_error_code(self):
        """UnsupportedFormatError should have UNSUPPORTED_FORMAT code."""
        from tryalma.webapp.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert error.error_code == "UNSUPPORTED_FORMAT"

    def test_unsupported_format_error_has_descriptive_message(self):
        """UnsupportedFormatError should have helpful default message."""
        from tryalma.webapp.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        assert "PDF" in error.message
        assert "JPEG" in error.message
        assert "PNG" in error.message

    def test_unsupported_format_error_inherits_from_file_validation_error(self):
        """UnsupportedFormatError should inherit from FileValidationError."""
        from tryalma.webapp.exceptions import FileValidationError, UnsupportedFormatError

        error = UnsupportedFormatError()

        assert isinstance(error, FileValidationError)


class TestFileTooLargeError:
    """Tests for FileTooLargeError class."""

    def test_file_too_large_error_has_status_413(self):
        """FileTooLargeError should have 413 status code."""
        from tryalma.webapp.exceptions import FileTooLargeError

        error = FileTooLargeError()

        assert error.status_code == 413

    def test_file_too_large_error_has_correct_error_code(self):
        """FileTooLargeError should have FILE_TOO_LARGE code."""
        from tryalma.webapp.exceptions import FileTooLargeError

        error = FileTooLargeError()

        assert error.error_code == "FILE_TOO_LARGE"

    def test_file_too_large_error_has_descriptive_message(self):
        """FileTooLargeError should mention 10MB limit."""
        from tryalma.webapp.exceptions import FileTooLargeError

        error = FileTooLargeError()

        assert "10MB" in error.message

    def test_file_too_large_error_inherits_from_file_validation_error(self):
        """FileTooLargeError should inherit from FileValidationError."""
        from tryalma.webapp.exceptions import FileTooLargeError, FileValidationError

        error = FileTooLargeError()

        assert isinstance(error, FileValidationError)


class TestDocumentTypeRequiredError:
    """Tests for DocumentTypeRequiredError class."""

    def test_document_type_required_error_has_status_400(self):
        """DocumentTypeRequiredError should have 400 status code."""
        from tryalma.webapp.exceptions import DocumentTypeRequiredError

        error = DocumentTypeRequiredError()

        assert error.status_code == 400

    def test_document_type_required_error_has_correct_error_code(self):
        """DocumentTypeRequiredError should have DOCUMENT_TYPE_REQUIRED code."""
        from tryalma.webapp.exceptions import DocumentTypeRequiredError

        error = DocumentTypeRequiredError()

        assert error.error_code == "DOCUMENT_TYPE_REQUIRED"

    def test_document_type_required_error_has_descriptive_message(self):
        """DocumentTypeRequiredError should instruct user to select type."""
        from tryalma.webapp.exceptions import DocumentTypeRequiredError

        error = DocumentTypeRequiredError()

        assert "document type" in error.message.lower()

    def test_document_type_required_error_inherits_from_file_validation_error(self):
        """DocumentTypeRequiredError should inherit from FileValidationError."""
        from tryalma.webapp.exceptions import DocumentTypeRequiredError, FileValidationError

        error = DocumentTypeRequiredError()

        assert isinstance(error, FileValidationError)


class TestExtractionFailedError:
    """Tests for ExtractionFailedError class."""

    def test_extraction_failed_error_has_status_422(self):
        """ExtractionFailedError should have 422 status code."""
        from tryalma.webapp.exceptions import ExtractionFailedError

        error = ExtractionFailedError()

        assert error.status_code == 422

    def test_extraction_failed_error_has_correct_error_code(self):
        """ExtractionFailedError should have EXTRACTION_FAILED code."""
        from tryalma.webapp.exceptions import ExtractionFailedError

        error = ExtractionFailedError()

        assert error.error_code == "EXTRACTION_FAILED"

    def test_extraction_failed_error_has_descriptive_message(self):
        """ExtractionFailedError should describe extraction failure."""
        from tryalma.webapp.exceptions import ExtractionFailedError

        error = ExtractionFailedError()

        assert "extract" in error.message.lower()

    def test_extraction_failed_error_inherits_from_webapp_error(self):
        """ExtractionFailedError should inherit from WebAppError."""
        from tryalma.webapp.exceptions import ExtractionFailedError, WebAppError

        error = ExtractionFailedError()

        assert isinstance(error, WebAppError)

    def test_extraction_failed_error_inherits_from_processing_error(self):
        """ExtractionFailedError should inherit from tryalma ProcessingError."""
        from tryalma.exceptions import ProcessingError
        from tryalma.webapp.exceptions import ExtractionFailedError

        error = ExtractionFailedError()

        assert isinstance(error, ProcessingError)


class TestExceptionUsability:
    """Tests for exception usability in error handling."""

    def test_exceptions_can_be_raised_and_caught(self):
        """All exceptions should be raisable and catchable."""
        from tryalma.webapp.exceptions import (
            DocumentTypeRequiredError,
            ExtractionFailedError,
            FileTooLargeError,
            UnsupportedFormatError,
            WebAppError,
        )

        # Test that each can be raised and caught
        for exc_class in [
            WebAppError,
            UnsupportedFormatError,
            FileTooLargeError,
            DocumentTypeRequiredError,
            ExtractionFailedError,
        ]:
            with pytest.raises(exc_class):
                raise exc_class()

    def test_exceptions_have_str_representation(self):
        """Exceptions should have meaningful string representation."""
        from tryalma.webapp.exceptions import UnsupportedFormatError

        error = UnsupportedFormatError()

        # str() should include the message
        assert str(error) == error.message
