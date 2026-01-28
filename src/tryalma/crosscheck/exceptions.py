"""Cross-check exception hierarchy.

Task 1.2: Exception types for cross-check operations.

Requirements: 7.4, 7.5
"""

from tryalma.exceptions import ProcessingError, ValidationError


class CrossCheckError(ProcessingError):
    """Base exception for cross-check operations.

    Exit code 3 (processing error) per project conventions.
    """

    message: str = "Cross-check extraction failed"


class VLMExtractionError(CrossCheckError):
    """VLM extraction failed.

    Raised when Qwen2-VL extraction encounters an error.
    Exit code 3 (processing error).
    """

    message: str = "Qwen2-VL extraction failed"


class VLMTimeoutError(CrossCheckError):
    """VLM extraction timed out.

    Raised when Qwen2-VL extraction exceeds the configured timeout.
    Exit code 3 (processing error).
    """

    message: str = "Qwen2-VL extraction timed out"


class ConfigurationError(ValidationError):
    """Cross-check configuration invalid or missing.

    Exit code 2 (validation error) per project conventions.

    Raised for:
    - Missing HF_TOKEN
    - Invalid timeout values
    - Invalid confidence thresholds
    """

    message: str = "Cross-check configuration error"
