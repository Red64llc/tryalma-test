"""Tests for FileValidator.

TDD: RED phase - These tests define expected behavior for the file validator
used to validate uploaded documents in the webapp.

Task 2.1: Implement file validator for uploaded documents
- Validate file extensions against allowed list (PDF, JPEG, PNG)
- Check file content-type using magic bytes to prevent extension spoofing
- Enforce maximum file size limit
- Return validation results with user-friendly error messages
- Requirements: 1.2, 1.3, 1.6
"""

from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_has_is_valid_field(self):
        """ValidationResult should have is_valid boolean field."""
        from tryalma.webapp.validators import ValidationResult

        result = ValidationResult(is_valid=True, error_message=None)

        assert result.is_valid is True

    def test_validation_result_has_error_message_field(self):
        """ValidationResult should have error_message optional field."""
        from tryalma.webapp.validators import ValidationResult

        result = ValidationResult(is_valid=False, error_message="Test error")

        assert result.error_message == "Test error"

    def test_validation_result_error_message_is_none_when_valid(self):
        """ValidationResult error_message should be None when valid."""
        from tryalma.webapp.validators import ValidationResult

        result = ValidationResult(is_valid=True, error_message=None)

        assert result.error_message is None


class TestFileValidatorConstants:
    """Tests for FileValidator constants."""

    def test_allowed_extensions_includes_pdf(self):
        """ALLOWED_EXTENSIONS should include .pdf."""
        from tryalma.webapp.validators import FileValidator

        assert ".pdf" in FileValidator.ALLOWED_EXTENSIONS

    def test_allowed_extensions_includes_jpg(self):
        """ALLOWED_EXTENSIONS should include .jpg."""
        from tryalma.webapp.validators import FileValidator

        assert ".jpg" in FileValidator.ALLOWED_EXTENSIONS

    def test_allowed_extensions_includes_jpeg(self):
        """ALLOWED_EXTENSIONS should include .jpeg."""
        from tryalma.webapp.validators import FileValidator

        assert ".jpeg" in FileValidator.ALLOWED_EXTENSIONS

    def test_allowed_extensions_includes_png(self):
        """ALLOWED_EXTENSIONS should include .png."""
        from tryalma.webapp.validators import FileValidator

        assert ".png" in FileValidator.ALLOWED_EXTENSIONS

    def test_allowed_extensions_is_frozenset(self):
        """ALLOWED_EXTENSIONS should be immutable (frozenset)."""
        from tryalma.webapp.validators import FileValidator

        assert isinstance(FileValidator.ALLOWED_EXTENSIONS, frozenset)

    def test_max_file_size_is_10mb(self):
        """MAX_FILE_SIZE should be 10MB in bytes."""
        from tryalma.webapp.validators import FileValidator

        expected_size = 10 * 1024 * 1024  # 10MB
        assert FileValidator.MAX_FILE_SIZE == expected_size


class TestFileValidatorExtensionValidation:
    """Tests for file extension validation."""

    def test_validate_accepts_pdf_extension(self):
        """Validator should accept .pdf files."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_pdf_file("document.pdf")

        result = validator.validate(file)

        assert result.is_valid is True
        assert result.error_message is None

    def test_validate_accepts_jpg_extension(self):
        """Validator should accept .jpg files."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_jpeg_file("image.jpg")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_jpeg_extension(self):
        """Validator should accept .jpeg files."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_jpeg_file("image.jpeg")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_png_extension(self):
        """Validator should accept .png files."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_png_file("image.png")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_uppercase_extension(self):
        """Validator should accept uppercase extensions (case-insensitive)."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_pdf_file("document.PDF")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_mixed_case_extension(self):
        """Validator should accept mixed case extensions."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_jpeg_file("image.JpEg")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_rejects_unsupported_extension(self):
        """Validator should reject unsupported file extensions."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("document.doc", b"test content")

        result = validator.validate(file)

        assert result.is_valid is False
        assert result.error_message is not None

    def test_validate_rejects_exe_extension(self):
        """Validator should reject executable files."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("malware.exe", b"MZ")  # PE header

        result = validator.validate(file)

        assert result.is_valid is False

    def test_validate_rejects_no_extension(self):
        """Validator should reject files without extension."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("noextension", b"test content")

        result = validator.validate(file)

        assert result.is_valid is False

    def test_unsupported_format_error_message_lists_supported_formats(self):
        """Error message for unsupported format should list supported formats."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("document.doc", b"test content")

        result = validator.validate(file)

        assert "PDF" in result.error_message
        assert "JPEG" in result.error_message
        assert "PNG" in result.error_message


class TestFileValidatorSizeValidation:
    """Tests for file size validation."""

    def test_validate_accepts_file_under_limit(self):
        """Validator should accept files under the size limit."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        # Create a 1MB PDF file
        content = _create_pdf_header() + b"x" * (1024 * 1024)
        file = _create_mock_file("document.pdf", content)

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_file_at_exact_limit(self):
        """Validator should accept files at exactly the size limit."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        # Create exactly 10MB PDF file
        pdf_header = _create_pdf_header()
        content = pdf_header + b"x" * (10 * 1024 * 1024 - len(pdf_header))
        file = _create_mock_file("document.pdf", content)

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_rejects_file_over_limit(self):
        """Validator should reject files over the size limit."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        # Create 11MB PDF file (over 10MB limit)
        pdf_header = _create_pdf_header()
        content = pdf_header + b"x" * (11 * 1024 * 1024)
        file = _create_mock_file("document.pdf", content)

        result = validator.validate(file)

        assert result.is_valid is False
        assert result.error_message is not None

    def test_file_too_large_error_message_mentions_limit(self):
        """Error message for large files should mention the size limit."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        pdf_header = _create_pdf_header()
        content = pdf_header + b"x" * (11 * 1024 * 1024)
        file = _create_mock_file("document.pdf", content)

        result = validator.validate(file)

        assert "10MB" in result.error_message or "10 MB" in result.error_message


class TestFileValidatorMagicByteValidation:
    """Tests for magic byte content-type validation."""

    def test_validate_accepts_valid_pdf_magic_bytes(self):
        """Validator should accept PDF files with correct magic bytes."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_pdf_file("document.pdf")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_valid_jpeg_magic_bytes(self):
        """Validator should accept JPEG files with correct magic bytes."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_jpeg_file("image.jpg")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_accepts_valid_png_magic_bytes(self):
        """Validator should accept PNG files with correct magic bytes."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_png_file("image.png")

        result = validator.validate(file)

        assert result.is_valid is True

    def test_validate_rejects_pdf_extension_with_wrong_content(self):
        """Validator should reject .pdf files that are not actually PDFs (spoofing)."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        # File claims to be PDF but has text content
        file = _create_mock_file("fake.pdf", b"This is not a PDF")

        result = validator.validate(file)

        assert result.is_valid is False
        assert result.error_message is not None

    def test_validate_rejects_jpeg_extension_with_wrong_content(self):
        """Validator should reject .jpg files that are not actually JPEGs (spoofing)."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        # File claims to be JPEG but has wrong content
        file = _create_mock_file("fake.jpg", b"This is not a JPEG")

        result = validator.validate(file)

        assert result.is_valid is False

    def test_validate_rejects_png_extension_with_wrong_content(self):
        """Validator should reject .png files that are not actually PNGs (spoofing)."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        # File claims to be PNG but has PDF content
        file = _create_mock_file("fake.png", _create_pdf_header() + b"content")

        result = validator.validate(file)

        assert result.is_valid is False

    def test_spoofed_file_error_message_is_user_friendly(self):
        """Error message for spoofed files should be user-friendly."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("fake.pdf", b"This is not a PDF")

        result = validator.validate(file)

        # Should mention content type mismatch
        assert "content" in result.error_message.lower() or "type" in result.error_message.lower()


class TestFileValidatorGetFileExtension:
    """Tests for get_file_extension helper method."""

    def test_get_file_extension_extracts_pdf(self):
        """get_file_extension should extract .pdf from filename."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()

        result = validator.get_file_extension("document.pdf")

        assert result == ".pdf"

    def test_get_file_extension_extracts_lowercase(self):
        """get_file_extension should return lowercase extension."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()

        result = validator.get_file_extension("document.PDF")

        assert result == ".pdf"

    def test_get_file_extension_handles_multiple_dots(self):
        """get_file_extension should handle filenames with multiple dots."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()

        result = validator.get_file_extension("my.document.v2.pdf")

        assert result == ".pdf"

    def test_get_file_extension_returns_empty_for_no_extension(self):
        """get_file_extension should return empty string for no extension."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()

        result = validator.get_file_extension("noextension")

        assert result == ""

    def test_get_file_extension_handles_hidden_files(self):
        """get_file_extension should handle hidden files (starting with dot)."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()

        result = validator.get_file_extension(".hidden.pdf")

        assert result == ".pdf"


class TestFileValidatorEmptyFile:
    """Tests for empty file handling."""

    def test_validate_rejects_empty_file(self):
        """Validator should reject empty files."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("empty.pdf", b"")

        result = validator.validate(file)

        assert result.is_valid is False
        assert result.error_message is not None

    def test_empty_file_error_message_is_descriptive(self):
        """Error message for empty files should be descriptive."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = _create_mock_file("empty.pdf", b"")

        result = validator.validate(file)

        assert "empty" in result.error_message.lower()


class TestFileValidatorNoFilename:
    """Tests for handling files without filenames."""

    def test_validate_rejects_file_without_filename(self):
        """Validator should reject files without a filename."""
        from tryalma.webapp.validators import FileValidator

        validator = FileValidator()
        file = FileStorage(stream=BytesIO(b"test"), filename="")

        result = validator.validate(file)

        assert result.is_valid is False


# Helper functions to create mock files with proper magic bytes


def _create_mock_file(filename: str, content: bytes) -> FileStorage:
    """Create a mock FileStorage with given filename and content."""
    stream = BytesIO(content)
    return FileStorage(stream=stream, filename=filename)


def _create_pdf_header() -> bytes:
    """Create valid PDF magic bytes header."""
    return b"%PDF-1.4"


def _create_mock_pdf_file(filename: str) -> FileStorage:
    """Create a mock PDF FileStorage with valid magic bytes."""
    content = _create_pdf_header() + b"\nPDF content here"
    return _create_mock_file(filename, content)


def _create_jpeg_header() -> bytes:
    """Create valid JPEG magic bytes header (SOI marker)."""
    return b"\xFF\xD8\xFF\xE0"


def _create_mock_jpeg_file(filename: str) -> FileStorage:
    """Create a mock JPEG FileStorage with valid magic bytes."""
    content = _create_jpeg_header() + b"JFIF" + b"\x00" * 100
    return _create_mock_file(filename, content)


def _create_png_header() -> bytes:
    """Create valid PNG magic bytes header."""
    return b"\x89PNG\r\n\x1a\n"


def _create_mock_png_file(filename: str) -> FileStorage:
    """Create a mock PNG FileStorage with valid magic bytes."""
    content = _create_png_header() + b"\x00" * 100
    return _create_mock_file(filename, content)
