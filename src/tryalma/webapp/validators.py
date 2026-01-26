"""File validators for the document upload UI.

Validates uploaded files for type, size, and content integrity.
Used by the upload blueprint to ensure only supported files are processed.

Task 2.1: File validation with magic byte checking to prevent extension spoofing.
"""

from dataclasses import dataclass
from pathlib import Path

from werkzeug.datastructures import FileStorage


@dataclass
class ValidationResult:
    """Result of file validation.

    Attributes:
        is_valid: True if file passed all validation checks
        error_message: User-friendly error message if validation failed, None otherwise
    """

    is_valid: bool
    error_message: str | None


class FileValidator:
    """Validates uploaded files for the upload UI.

    Performs extension validation, size checking, and content-type verification
    using magic bytes to prevent extension spoofing attacks.

    Attributes:
        ALLOWED_EXTENSIONS: Frozenset of allowed file extensions (lowercase, with dot)
        MAX_FILE_SIZE: Maximum allowed file size in bytes (10MB)
    """

    ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".jpg", ".jpeg", ".png"})
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Magic byte signatures for supported file types
    _MAGIC_BYTES: dict[str, list[bytes]] = {
        ".pdf": [b"%PDF"],
        ".jpg": [b"\xFF\xD8\xFF"],
        ".jpeg": [b"\xFF\xD8\xFF"],
        ".png": [b"\x89PNG\r\n\x1a\n"],
    }

    def validate(self, file_storage: FileStorage) -> ValidationResult:
        """Validate an uploaded file.

        Performs the following checks in order:
        1. Filename is present and non-empty
        2. File is not empty
        3. Extension is in allowed list
        4. File size is within limit
        5. Content matches extension (magic byte check)

        Args:
            file_storage: Flask FileStorage object from request.files

        Returns:
            ValidationResult with is_valid and error_message
        """
        # Check filename exists
        if not file_storage.filename:
            return ValidationResult(
                is_valid=False,
                error_message="No filename provided",
            )

        # Check file is not empty
        file_storage.stream.seek(0, 2)  # Seek to end
        file_size = file_storage.stream.tell()
        file_storage.stream.seek(0)  # Reset to beginning

        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                error_message="File is empty. Please select a valid file.",
            )

        # Check extension
        extension = self.get_file_extension(file_storage.filename)
        if extension not in self.ALLOWED_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                error_message="Unsupported file format. Supported: PDF, JPEG, PNG",
            )

        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            return ValidationResult(
                is_valid=False,
                error_message="File size exceeds maximum allowed (10MB)",
            )

        # Check magic bytes (content-type validation)
        if not self._validate_magic_bytes(file_storage, extension):
            return ValidationResult(
                is_valid=False,
                error_message="File content does not match its extension. Please ensure the file type is correct.",
            )

        return ValidationResult(is_valid=True, error_message=None)

    def get_file_extension(self, filename: str) -> str:
        """Extract and normalize file extension.

        Args:
            filename: The filename to extract extension from

        Returns:
            Lowercase extension with leading dot, or empty string if no extension
        """
        path = Path(filename)
        return path.suffix.lower()

    def _validate_magic_bytes(self, file_storage: FileStorage, extension: str) -> bool:
        """Validate file content matches expected magic bytes for extension.

        Args:
            file_storage: The file to validate
            extension: Expected file extension (lowercase, with dot)

        Returns:
            True if content matches expected magic bytes, False otherwise
        """
        magic_signatures = self._MAGIC_BYTES.get(extension)
        if not magic_signatures:
            # No magic bytes defined for this extension
            return True

        # Read the beginning of the file for magic byte check
        file_storage.stream.seek(0)
        header = file_storage.stream.read(16)
        file_storage.stream.seek(0)  # Reset for later use

        # Check if any of the magic signatures match
        return any(header.startswith(sig) for sig in magic_signatures)
