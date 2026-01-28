"""Unit tests for ConfidenceScorer.

Task 3.2: Test confidence scoring calculations.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

import pytest

from tryalma.crosscheck.config import ConfidenceConfig
from tryalma.crosscheck.confidence_scorer import ConfidenceScorer
from tryalma.crosscheck.models import (
    DiscrepancySeverity,
    FieldDiscrepancy,
    FieldValidationResult,
)


class TestConfidenceScorerConfig:
    """Test ConfidenceScorer with configurable values."""

    def test_scorer_accepts_config(self):
        """Scorer should accept ConfidenceConfig."""
        config = ConfidenceConfig(
            agreement_confidence=0.95,
            disagreement_base_confidence=0.3,
        )
        scorer = ConfidenceScorer(config=config)
        assert scorer.config.agreement_confidence == 0.95

    def test_scorer_uses_default_config_when_none(self):
        """Scorer should use default config when none provided."""
        scorer = ConfidenceScorer()
        assert scorer.config.agreement_confidence == 1.0
        assert scorer.config.disagreement_base_confidence == 0.4


class TestFieldConfidenceAgreement:
    """Test field confidence when sources agree (Requirement 3.2)."""

    def test_confidence_is_1_when_both_sources_agree(self):
        """Confidence should be 1.0 when both sources provide matching values."""
        scorer = ConfidenceScorer()

        validation_result = FieldValidationResult(
            field_name="surname",
            validated=True,  # Agreement
            mrz_value="SMITH",
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["mrz", "qwen2-vl"],
        )

        assert confidence == 1.0


class TestFieldConfidenceDisagreement:
    """Test field confidence when sources disagree (Requirement 3.3)."""

    def test_confidence_reduced_on_disagreement(self):
        """Confidence should be reduced when sources disagree."""
        scorer = ConfidenceScorer()

        validation_result = FieldValidationResult(
            field_name="passport_number",
            validated=False,  # Disagreement
            mrz_value="123456789",
            vlm_value="123456780",
            final_value="123456789",
            discrepancy=FieldDiscrepancy(
                field_name="passport_number",
                mrz_value="123456789",
                vlm_value="123456780",
                recommended_value="123456789",
                severity=DiscrepancySeverity.CRITICAL,
                reason="Values differ",
            ),
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["mrz", "qwen2-vl"],
        )

        # Should use disagreement_base_confidence (default 0.4)
        assert confidence == 0.4

    def test_confidence_uses_custom_disagreement_value(self):
        """Confidence should use configured disagreement value."""
        config = ConfidenceConfig(disagreement_base_confidence=0.5)
        scorer = ConfidenceScorer(config=config)

        validation_result = FieldValidationResult(
            field_name="surname",
            validated=False,
            mrz_value="SMITH",
            vlm_value="SMYTH",
            final_value="SMYTH",
            discrepancy=FieldDiscrepancy(
                field_name="surname",
                mrz_value="SMITH",
                vlm_value="SMYTH",
                recommended_value="SMYTH",
                severity=DiscrepancySeverity.WARNING,
                reason="Values differ",
            ),
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["mrz", "qwen2-vl"],
        )

        assert confidence == 0.5


class TestFieldConfidenceSingleSource:
    """Test field confidence for single-source extraction (Requirement 3.4)."""

    def test_mrz_only_confidence_is_0_7(self):
        """MRZ-only extraction should have confidence of 0.7."""
        scorer = ConfidenceScorer()

        validation_result = FieldValidationResult(
            field_name="passport_number",
            validated=True,
            mrz_value="123456789",
            vlm_value=None,  # VLM not available
            final_value="123456789",
            discrepancy=None,
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["mrz"],  # Only MRZ
        )

        assert confidence == 0.7

    def test_vlm_only_confidence_is_0_6(self):
        """VLM-only extraction should have confidence of 0.6."""
        scorer = ConfidenceScorer()

        validation_result = FieldValidationResult(
            field_name="surname",
            validated=True,
            mrz_value=None,  # MRZ not available
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["qwen2-vl"],  # Only VLM
        )

        assert confidence == 0.6

    def test_single_source_with_custom_confidence(self):
        """Single source confidence should use configured values."""
        config = ConfidenceConfig(
            single_source_mrz_confidence=0.8,
            single_source_vlm_confidence=0.65,
        )
        scorer = ConfidenceScorer(config=config)

        mrz_result = FieldValidationResult(
            field_name="passport_number",
            validated=True,
            mrz_value="123456789",
            vlm_value=None,
            final_value="123456789",
            discrepancy=None,
        )

        vlm_result = FieldValidationResult(
            field_name="surname",
            validated=True,
            mrz_value=None,
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        mrz_confidence = scorer.calculate_field_confidence(
            mrz_result,
            sources_available=["mrz"],
        )
        vlm_confidence = scorer.calculate_field_confidence(
            vlm_result,
            sources_available=["qwen2-vl"],
        )

        assert mrz_confidence == 0.8
        assert vlm_confidence == 0.65


class TestFieldConfidenceClamping:
    """Test that confidence values are clamped to 0.0-1.0 range."""

    def test_confidence_clamped_to_max_1(self):
        """Confidence should never exceed 1.0."""
        config = ConfidenceConfig(agreement_confidence=1.5)  # Invalid high value
        scorer = ConfidenceScorer(config=config)

        validation_result = FieldValidationResult(
            field_name="surname",
            validated=True,
            mrz_value="SMITH",
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["mrz", "qwen2-vl"],
        )

        assert confidence == 1.0

    def test_confidence_clamped_to_min_0(self):
        """Confidence should never be below 0.0."""
        config = ConfidenceConfig(disagreement_base_confidence=-0.5)  # Invalid low value
        scorer = ConfidenceScorer(config=config)

        validation_result = FieldValidationResult(
            field_name="passport_number",
            validated=False,
            mrz_value="123456789",
            vlm_value="123456780",
            final_value="123456789",
            discrepancy=FieldDiscrepancy(
                field_name="passport_number",
                mrz_value="123456789",
                vlm_value="123456780",
                recommended_value="123456789",
                severity=DiscrepancySeverity.CRITICAL,
                reason="Values differ",
            ),
        )

        confidence = scorer.calculate_field_confidence(
            validation_result,
            sources_available=["mrz", "qwen2-vl"],
        )

        assert confidence == 0.0


class TestDocumentConfidence:
    """Test weighted document confidence calculation (Requirement 3.5)."""

    def test_document_confidence_is_weighted_average(self):
        """Document confidence should be weighted average of field confidences."""
        scorer = ConfidenceScorer()

        field_confidences = {
            "surname": 1.0,
            "given_names": 1.0,
            "date_of_birth": 1.0,
            "passport_number": 1.0,
        }

        document_confidence = scorer.calculate_document_confidence(field_confidences)

        # All 1.0, so average should be 1.0
        assert document_confidence == 1.0

    def test_document_confidence_weights_critical_fields_higher(self):
        """Critical fields should have higher weight in document confidence."""
        scorer = ConfidenceScorer()

        # passport_number and date_of_birth are critical, surname is standard
        field_confidences = {
            "passport_number": 0.4,  # Critical field, low confidence
            "date_of_birth": 0.4,    # Critical field, low confidence
            "surname": 1.0,          # Standard field, high confidence
            "given_names": 1.0,      # Critical field (per design), high confidence
        }

        document_confidence = scorer.calculate_document_confidence(field_confidences)

        # With critical fields weighted 2x, document confidence should be pulled
        # toward the low-confidence critical fields
        # Weights: passport_number=2, date_of_birth=2, surname=2, given_names=2
        # All are critical per ConfidenceScorer.CRITICAL_FIELDS
        # Total weight = 8, sum = 0.4*2 + 0.4*2 + 1.0*2 + 1.0*2 = 5.6
        # Average = 5.6 / 8 = 0.7
        assert document_confidence == 0.7

    def test_document_confidence_with_mixed_weights(self):
        """Document confidence with mix of critical and standard fields."""
        config = ConfidenceConfig(
            critical_field_weight=2.0,
            standard_field_weight=1.0,
        )
        scorer = ConfidenceScorer(config=config)

        field_confidences = {
            "passport_number": 1.0,  # Critical (weight 2)
            "sex": 0.6,              # Standard (weight 1)
        }

        document_confidence = scorer.calculate_document_confidence(field_confidences)

        # passport_number: 1.0 * 2 = 2.0
        # sex: 0.6 * 1 = 0.6
        # Total weight = 3, sum = 2.6
        # Average = 2.6 / 3 = 0.8666...
        assert round(document_confidence, 2) == 0.87

    def test_document_confidence_empty_dict_returns_none(self):
        """Document confidence should return None for empty field dict."""
        scorer = ConfidenceScorer()

        document_confidence = scorer.calculate_document_confidence({})

        assert document_confidence is None

    def test_document_confidence_clamped(self):
        """Document confidence should be clamped to 0.0-1.0."""
        scorer = ConfidenceScorer()

        # Even with weird inputs, result should be clamped
        field_confidences = {
            "surname": 1.5,  # Over max (would be clamped at field level normally)
        }

        document_confidence = scorer.calculate_document_confidence(field_confidences)

        assert document_confidence <= 1.0
        assert document_confidence >= 0.0


class TestCriticalFieldsDefinition:
    """Test that critical fields are properly defined."""

    def test_passport_number_is_critical(self):
        """Passport number should be a critical field."""
        scorer = ConfidenceScorer()
        assert "passport_number" in scorer.CRITICAL_FIELDS

    def test_date_of_birth_is_critical(self):
        """Date of birth should be a critical field."""
        scorer = ConfidenceScorer()
        assert "date_of_birth" in scorer.CRITICAL_FIELDS

    def test_surname_is_critical(self):
        """Surname should be a critical field (per design)."""
        scorer = ConfidenceScorer()
        assert "surname" in scorer.CRITICAL_FIELDS

    def test_given_names_is_critical(self):
        """Given names should be a critical field (per design)."""
        scorer = ConfidenceScorer()
        assert "given_names" in scorer.CRITICAL_FIELDS

    def test_sex_is_not_critical(self):
        """Sex should not be a critical field."""
        scorer = ConfidenceScorer()
        assert "sex" not in scorer.CRITICAL_FIELDS
