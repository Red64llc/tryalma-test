"""Confidence scorer for cross-check validation results.

Task 3.2: ConfidenceScorer class implementing confidence calculations.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

from __future__ import annotations

from tryalma.crosscheck.config import ConfidenceConfig
from tryalma.crosscheck.models import FieldValidationResult


class ConfidenceScorer:
    """Calculates confidence scores for cross-check results.

    Implements confidence scoring based on field agreement, disagreement,
    and single-source scenarios. Applies weighted averaging for document-level
    confidence with critical fields weighted higher.

    Attributes:
        CRITICAL_FIELDS: Set of fields considered critical for document confidence.
    """

    # Critical fields get higher weight per design.md
    CRITICAL_FIELDS: set[str] = {
        "passport_number",
        "date_of_birth",
        "surname",
        "given_names",
    }

    def __init__(self, config: ConfidenceConfig | None = None) -> None:
        """Initialize the confidence scorer.

        Args:
            config: Optional confidence configuration. Uses defaults if None.
        """
        self.config = config or ConfidenceConfig()

    def calculate_field_confidence(
        self,
        validation_result: FieldValidationResult,
        sources_available: list[str],
    ) -> float:
        """Calculate confidence for a single field.

        Confidence is determined by:
        - 1.0 (agreement_confidence) when both sources agree (Requirement 3.2)
        - Reduced (disagreement_base_confidence) when sources disagree (Requirement 3.3)
        - Moderate (0.6-0.7) for single source extraction (Requirement 3.4)

        Args:
            validation_result: Result from cross-validation.
            sources_available: List of sources that provided data (e.g., ["mrz", "qwen2-vl"]).

        Returns:
            Confidence score between 0.0 and 1.0 (clamped).
        """
        has_mrz = "mrz" in sources_available
        has_vlm = "qwen2-vl" in sources_available
        both_sources = has_mrz and has_vlm

        # Determine confidence based on scenario
        if both_sources:
            if validation_result.validated:
                # Both sources agree (Requirement 3.2)
                confidence = self.config.agreement_confidence
            else:
                # Sources disagree (Requirement 3.3)
                confidence = self.config.disagreement_base_confidence
        else:
            # Single source extraction (Requirement 3.4)
            if has_mrz:
                confidence = self.config.single_source_mrz_confidence
            elif has_vlm:
                confidence = self.config.single_source_vlm_confidence
            else:
                # No sources (shouldn't happen, but handle gracefully)
                confidence = 0.0

        # Clamp to valid range
        return self._clamp(confidence)

    def calculate_document_confidence(
        self,
        field_confidences: dict[str, float],
    ) -> float | None:
        """Calculate weighted average document confidence.

        Critical fields (passport_number, date_of_birth, surname, given_names)
        receive higher weight than standard fields per Requirement 3.5.

        Args:
            field_confidences: Map of field name to confidence score.

        Returns:
            Overall document confidence between 0.0 and 1.0, or None if no fields.
        """
        if not field_confidences:
            return None

        total_weight = 0.0
        weighted_sum = 0.0

        for field_name, confidence in field_confidences.items():
            # Apply weight based on field criticality
            if field_name in self.CRITICAL_FIELDS:
                weight = self.config.critical_field_weight
            else:
                weight = self.config.standard_field_weight

            # Clamp field confidence before adding
            clamped_confidence = self._clamp(confidence)

            weighted_sum += clamped_confidence * weight
            total_weight += weight

        if total_weight == 0:
            return None

        document_confidence = weighted_sum / total_weight

        # Clamp final result
        return self._clamp(document_confidence)

    def _clamp(self, value: float) -> float:
        """Clamp a value to the range [0.0, 1.0].

        Args:
            value: Value to clamp.

        Returns:
            Value clamped to [0.0, 1.0].
        """
        return max(0.0, min(1.0, value))
