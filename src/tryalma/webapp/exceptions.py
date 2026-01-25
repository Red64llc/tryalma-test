"""WebApp exception hierarchy for HTTP error responses.

Web-specific exceptions that map to HTTP status codes and provide
user-friendly error messages for the document upload UI.
"""

from tryalma.exceptions import ProcessingError, ValidationError


class WebAppError(Exception):
    """Base exception for web application errors.

    Provides HTTP status code and error code for API responses.

    Attributes:
        status_code: HTTP status code to return
        error_code: Machine-readable error code for clients
        message: Human-readable error message
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        """Initialize WebAppError with optional custom message.

        Args:
            message: Custom error message (uses class default if not provided)
        """
        self.message = message or self.__class__.message
        super().__init__(self.message)


class FileValidationError(WebAppError, ValidationError):
    """File validation failed.

    HTTP 400 Bad Request - indicates client error in file submission.
    """

    status_code: int = 400
    error_code: str = "VALIDATION_ERROR"
    message: str = "File validation failed"


class UnsupportedFormatError(FileValidationError):
    """File format not supported.

    HTTP 415 Unsupported Media Type - file type is not in allowed list.
    """

    status_code: int = 415
    error_code: str = "UNSUPPORTED_FORMAT"
    message: str = "Unsupported file format. Supported: PDF, JPEG, PNG"


class FileTooLargeError(FileValidationError):
    """File exceeds size limit.

    HTTP 413 Content Too Large - file size exceeds maximum allowed (10MB).
    """

    status_code: int = 413
    error_code: str = "FILE_TOO_LARGE"
    message: str = "File size exceeds maximum allowed (10MB)"


class DocumentTypeRequiredError(FileValidationError):
    """Document type not specified.

    HTTP 400 Bad Request - user must select document type before uploading.
    """

    status_code: int = 400
    error_code: str = "DOCUMENT_TYPE_REQUIRED"
    message: str = "Please select a document type before uploading"


class ExtractionFailedError(WebAppError, ProcessingError):
    """Extraction service failed.

    HTTP 422 Unprocessable Entity - document was valid but extraction failed.
    """

    status_code: int = 422
    error_code: str = "EXTRACTION_FAILED"
    message: str = "Failed to extract data from document"
