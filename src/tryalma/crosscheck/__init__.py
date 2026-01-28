"""Cross-check module for dual-source passport extraction with validation.

This module provides cross-validation between MRZ and VLM extraction sources
with confidence scoring and discrepancy reporting.
"""

from tryalma.crosscheck.config import ConfidenceConfig, CrossCheckConfig
from tryalma.crosscheck.exceptions import (
    ConfigurationError,
    CrossCheckError,
    VLMExtractionError,
    VLMTimeoutError,
)
from tryalma.crosscheck.models import (
    CrossCheckResult,
    DiscrepancySeverity,
    ExtractionStatus,
    FieldDiscrepancy,
    FieldValidationResult,
    ProcessingMetadata,
    VisualZoneData,
)

__all__ = [
    # Models
    "ExtractionStatus",
    "DiscrepancySeverity",
    "VisualZoneData",
    "FieldDiscrepancy",
    "FieldValidationResult",
    "ProcessingMetadata",
    "CrossCheckResult",
    # Config
    "ConfidenceConfig",
    "CrossCheckConfig",
    # Exceptions
    "CrossCheckError",
    "VLMExtractionError",
    "VLMTimeoutError",
    "ConfigurationError",
]
