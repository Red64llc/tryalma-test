"""TryAlma - CLI and API application."""

__version__ = "0.1.0"

# Cross-check exports (Task 5.1)
from tryalma.crosscheck import (
    # Service
    CrossCheckService,
    # Config
    CrossCheckConfig,
    ConfidenceConfig,
    # Provider
    Qwen2VLProvider,
    # Models
    CrossCheckResult,
    ExtractionStatus,
    DiscrepancySeverity,
    VisualZoneData,
    FieldDiscrepancy,
    FieldValidationResult,
    ProcessingMetadata,
    # Core logic
    FieldCrossValidator,
    ConfidenceScorer,
    DiscrepancyReporter,
    # Exceptions
    CrossCheckError,
    VLMExtractionError,
    VLMTimeoutError,
    ConfigurationError,
)

__all__ = [
    "__version__",
    # Cross-check service
    "CrossCheckService",
    # Cross-check config
    "CrossCheckConfig",
    "ConfidenceConfig",
    # Cross-check provider
    "Qwen2VLProvider",
    # Cross-check models
    "CrossCheckResult",
    "ExtractionStatus",
    "DiscrepancySeverity",
    "VisualZoneData",
    "FieldDiscrepancy",
    "FieldValidationResult",
    "ProcessingMetadata",
    # Cross-check core logic
    "FieldCrossValidator",
    "ConfidenceScorer",
    "DiscrepancyReporter",
    # Cross-check exceptions
    "CrossCheckError",
    "VLMExtractionError",
    "VLMTimeoutError",
    "ConfigurationError",
]
