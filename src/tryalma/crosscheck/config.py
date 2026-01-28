"""Configuration types for cross-check service.

Task 1.2: Configuration dataclasses for cross-check operations.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

from dataclasses import dataclass, field

from tryalma.crosscheck.exceptions import ConfigurationError


@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring.

    Defines confidence values for different cross-validation scenarios.
    Per Requirements 3.1-3.5 and 7.3.
    """

    # Confidence when both sources agree (Requirement 3.2)
    agreement_confidence: float = 1.0

    # Base confidence when sources disagree (Requirement 3.3)
    disagreement_base_confidence: float = 0.4

    # Confidence for single-source extraction from MRZ (Requirement 3.4)
    single_source_mrz_confidence: float = 0.7

    # Confidence for single-source extraction from VLM (Requirement 3.4)
    single_source_vlm_confidence: float = 0.6

    # Weight multiplier for critical fields in document confidence (Requirement 3.5)
    critical_field_weight: float = 2.0

    # Weight multiplier for standard fields in document confidence
    standard_field_weight: float = 1.0


@dataclass
class CrossCheckConfig:
    """Configuration for CrossCheckService.

    Provides configurable parameters for cross-check extraction behavior.
    Per Requirements 7.1-7.5.
    """

    # Hugging Face configuration (Requirement 7.1)
    hf_token: str | None = None  # Falls back to HF_TOKEN env var if None
    vlm_model: str = "Qwen/Qwen2-VL-7B-Instruct"

    # Timeout configuration (Requirement 7.2)
    mrz_timeout_seconds: float = 30.0
    vlm_timeout_seconds: float = 60.0

    # Confidence thresholds (Requirement 7.3)
    confidence_config: ConfidenceConfig = field(default_factory=ConfidenceConfig)

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if self.mrz_timeout_seconds <= 0:
            raise ConfigurationError("mrz_timeout_seconds must be positive")
        if self.vlm_timeout_seconds <= 0:
            raise ConfigurationError("vlm_timeout_seconds must be positive")
