"""Passport-specific exception classes.

Task 2.3: Exception hierarchy for passport extraction failures.

Requirements: 5.1, 5.2, 5.3, 5.4
"""

from tryalma.exceptions import ProcessingError, ValidationError


class PassportExtractionError(ProcessingError):
    """Base exception for passport extraction failures.

    Exit code 3 (processing error) per project conventions.
    """

    message: str = "Passport extraction failed"


class MRZNotFoundError(PassportExtractionError):
    """No MRZ detected in the image.

    Raised when PassportEye cannot find a Machine Readable Zone.
    Exit code 3 (processing error).
    """

    message: str = "No Machine Readable Zone (MRZ) detected in image"


class UnsupportedFormatError(ValidationError):
    """Image format not supported.

    Exit code 2 (validation error) per project conventions.
    """

    message: str = "Unsupported image format"


class TesseractNotFoundError(PassportExtractionError):
    """Tesseract OCR not installed.

    Exit code 1 (configuration error) - overrides parent's exit code.
    Provides platform-specific installation instructions.
    """

    exit_code: int = 1
    message: str = "Tesseract OCR is not installed"

    def __init__(self) -> None:
        """Initialize with installation instructions."""
        from tryalma.passport.utils import get_tesseract_install_instructions

        instructions = get_tesseract_install_instructions()
        full_message = f"{self.message}.\n\n{instructions}"
        super().__init__(full_message)


class ImageReadError(PassportExtractionError):
    """Image file could not be read.

    Raised for corrupted or unreadable image files.
    Exit code 3 (processing error).
    """

    message: str = "Could not read image file"
