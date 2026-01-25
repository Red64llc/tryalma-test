"""G28-specific exception classes.

Task 2: Exception hierarchy for G28 form extraction failures.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

from tryalma.exceptions import ProcessingError, ValidationError


class G28ExtractionError(ProcessingError):
    """Base exception for G-28 extraction failures.

    Exit code 3 (processing error) per project conventions.
    """

    message: str = "G-28 form extraction failed"


class NotG28FormError(G28ExtractionError):
    """Document is not recognized as a G-28 form.

    Raised when document type mismatch is detected.
    Exit code 3 (processing error).
    """

    message: str = "Document is not recognized as a USCIS Form G-28"


class DocumentLoadError(G28ExtractionError):
    """Failed to load or convert document.

    Raised for file loading or conversion failures.
    Exit code 3 (processing error).
    """

    message: str = "Failed to load document"


class ExtractionAPIError(G28ExtractionError):
    """External extraction API failure.

    Raised when external API (e.g., Claude Vision) is unavailable or fails.
    Exit code 3 (processing error).
    """

    message: str = "Extraction service unavailable"


class UnsupportedFormatError(ValidationError):
    """File format not supported.

    Exit code 2 (validation error) per project conventions.
    """

    message: str = "Unsupported file format. Supported: PDF, PNG, JPG, JPEG, TIFF"


class LowQualityWarning(G28ExtractionError):
    """Document quality too poor for reliable extraction.

    Raised when image quality is insufficient for accurate extraction.
    Exit code 3 (processing error).
    """

    message: str = "Document quality is too poor for reliable extraction"
