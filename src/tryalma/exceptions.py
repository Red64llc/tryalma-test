"""Custom exception hierarchy for TryAlma."""


class TryAlmaError(Exception):
    """Base exception for all TryAlma errors."""

    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


class CLIError(TryAlmaError):
    """Base exception for CLI errors."""

    exit_code: int = 1


class ValidationError(CLIError):
    """Validation error with exit code 2."""

    exit_code: int = 2
    message: str = "Validation failed"


class ProcessingError(CLIError):
    """Processing error with exit code 3."""

    exit_code: int = 3
    message: str = "Processing failed"


class APIError(TryAlmaError):
    """Base exception for API errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"


class NotFoundError(APIError):
    """Resource not found error."""

    status_code: int = 404
    code: str = "NOT_FOUND"
    message: str = "Resource not found"
