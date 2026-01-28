"""Unit tests for cross-check data models.

Task 1.1: Test data models for cross-check functionality.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest


class TestExtractionStatus:
    """Tests for ExtractionStatus enumeration."""

    def test_extraction_status_has_success_state(self):
        """ExtractionStatus should have SUCCESS state."""
        from tryalma.crosscheck.models import ExtractionStatus

        assert ExtractionStatus.SUCCESS.value == "success"

    def test_extraction_status_has_partial_state(self):
        """ExtractionStatus should have PARTIAL state."""
        from tryalma.crosscheck.models import ExtractionStatus

        assert ExtractionStatus.PARTIAL.value == "partial"

    def test_extraction_status_has_error_state(self):
        """ExtractionStatus should have ERROR state."""
        from tryalma.crosscheck.models import ExtractionStatus

        assert ExtractionStatus.ERROR.value == "error"

    def test_extraction_status_is_string_enum(self):
        """ExtractionStatus values should be usable as strings."""
        from tryalma.crosscheck.models import ExtractionStatus

        assert str(ExtractionStatus.SUCCESS) == "ExtractionStatus.SUCCESS"
        assert ExtractionStatus.SUCCESS == "success"


class TestDiscrepancySeverity:
    """Tests for DiscrepancySeverity enumeration."""

    def test_severity_has_critical_level(self):
        """DiscrepancySeverity should have CRITICAL level."""
        from tryalma.crosscheck.models import DiscrepancySeverity

        assert DiscrepancySeverity.CRITICAL.value == "critical"

    def test_severity_has_warning_level(self):
        """DiscrepancySeverity should have WARNING level."""
        from tryalma.crosscheck.models import DiscrepancySeverity

        assert DiscrepancySeverity.WARNING.value == "warning"

    def test_severity_has_informational_level(self):
        """DiscrepancySeverity should have INFORMATIONAL level."""
        from tryalma.crosscheck.models import DiscrepancySeverity

        assert DiscrepancySeverity.INFORMATIONAL.value == "informational"


class TestVisualZoneData:
    """Tests for VisualZoneData structure."""

    def test_visual_zone_data_holds_passport_fields(self):
        """VisualZoneData should hold all extracted passport fields."""
        from tryalma.crosscheck.models import VisualZoneData

        data = VisualZoneData(
            surname="SMITH",
            given_names="JOHN WILLIAM",
            date_of_birth="1985-03-15",
            nationality="USA",
            passport_number="123456789",
            expiry_date="2030-03-14",
            sex="M",
            place_of_birth="NEW YORK",
        )

        assert data.surname == "SMITH"
        assert data.given_names == "JOHN WILLIAM"
        assert data.date_of_birth == "1985-03-15"
        assert data.nationality == "USA"
        assert data.passport_number == "123456789"
        assert data.expiry_date == "2030-03-14"
        assert data.sex == "M"
        assert data.place_of_birth == "NEW YORK"

    def test_visual_zone_data_fields_default_to_none(self):
        """VisualZoneData fields should default to None."""
        from tryalma.crosscheck.models import VisualZoneData

        data = VisualZoneData()

        assert data.surname is None
        assert data.given_names is None
        assert data.date_of_birth is None
        assert data.nationality is None
        assert data.passport_number is None
        assert data.expiry_date is None
        assert data.sex is None
        assert data.place_of_birth is None

    def test_visual_zone_data_stores_raw_response(self):
        """VisualZoneData should store raw VLM response."""
        from tryalma.crosscheck.models import VisualZoneData

        raw = '{"surname": "SMITH"}'
        data = VisualZoneData(raw_response=raw)

        assert data.raw_response == raw


class TestFieldDiscrepancy:
    """Tests for FieldDiscrepancy model."""

    def test_field_discrepancy_stores_field_name(self):
        """FieldDiscrepancy should store field name."""
        from tryalma.crosscheck.models import DiscrepancySeverity, FieldDiscrepancy

        discrepancy = FieldDiscrepancy(
            field_name="passport_number",
            mrz_value="123456789",
            vlm_value="123456780",
            recommended_value="123456789",
            severity=DiscrepancySeverity.CRITICAL,
            reason="Last digit differs",
        )

        assert discrepancy.field_name == "passport_number"

    def test_field_discrepancy_stores_both_source_values(self):
        """FieldDiscrepancy should store values from both sources."""
        from tryalma.crosscheck.models import DiscrepancySeverity, FieldDiscrepancy

        discrepancy = FieldDiscrepancy(
            field_name="surname",
            mrz_value="SMITH",
            vlm_value="SMYTH",
            recommended_value="SMITH",
            severity=DiscrepancySeverity.WARNING,
            reason="Spelling differs",
        )

        assert discrepancy.mrz_value == "SMITH"
        assert discrepancy.vlm_value == "SMYTH"

    def test_field_discrepancy_stores_recommended_value(self):
        """FieldDiscrepancy should store recommended value."""
        from tryalma.crosscheck.models import DiscrepancySeverity, FieldDiscrepancy

        discrepancy = FieldDiscrepancy(
            field_name="date_of_birth",
            mrz_value="1985-03-15",
            vlm_value="1985-03-16",
            recommended_value="1985-03-15",
            severity=DiscrepancySeverity.CRITICAL,
            reason="MRZ preferred for dates",
        )

        assert discrepancy.recommended_value == "1985-03-15"

    def test_field_discrepancy_stores_severity_level(self):
        """FieldDiscrepancy should store severity level."""
        from tryalma.crosscheck.models import DiscrepancySeverity, FieldDiscrepancy

        discrepancy = FieldDiscrepancy(
            field_name="sex",
            mrz_value="M",
            vlm_value="F",
            recommended_value="M",
            severity=DiscrepancySeverity.INFORMATIONAL,
            reason="Sex field differs",
        )

        assert discrepancy.severity == DiscrepancySeverity.INFORMATIONAL

    def test_field_discrepancy_stores_reason(self):
        """FieldDiscrepancy should store reason for discrepancy."""
        from tryalma.crosscheck.models import DiscrepancySeverity, FieldDiscrepancy

        discrepancy = FieldDiscrepancy(
            field_name="passport_number",
            mrz_value="123456789",
            vlm_value="123456780",
            recommended_value="123456789",
            severity=DiscrepancySeverity.CRITICAL,
            reason="Check digit validation passed for MRZ",
        )

        assert discrepancy.reason == "Check digit validation passed for MRZ"


class TestFieldValidationResult:
    """Tests for FieldValidationResult model."""

    def test_field_validation_result_tracks_field_name(self):
        """FieldValidationResult should track field name."""
        from tryalma.crosscheck.models import FieldValidationResult

        result = FieldValidationResult(
            field_name="surname",
            validated=True,
            mrz_value="SMITH",
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        assert result.field_name == "surname"

    def test_field_validation_result_tracks_validated_status(self):
        """FieldValidationResult should track whether field was validated."""
        from tryalma.crosscheck.models import FieldValidationResult

        result = FieldValidationResult(
            field_name="surname",
            validated=True,
            mrz_value="SMITH",
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        assert result.validated is True

    def test_field_validation_result_tracks_both_source_values(self):
        """FieldValidationResult should track values from both sources."""
        from tryalma.crosscheck.models import FieldValidationResult

        result = FieldValidationResult(
            field_name="surname",
            validated=False,
            mrz_value="SMITH",
            vlm_value="SMYTH",
            final_value="SMITH",
            discrepancy=None,
        )

        assert result.mrz_value == "SMITH"
        assert result.vlm_value == "SMYTH"

    def test_field_validation_result_tracks_final_value(self):
        """FieldValidationResult should track the determined final value."""
        from tryalma.crosscheck.models import FieldValidationResult

        result = FieldValidationResult(
            field_name="surname",
            validated=True,
            mrz_value="SMITH",
            vlm_value="SMITH",
            final_value="SMITH",
            discrepancy=None,
        )

        assert result.final_value == "SMITH"

    def test_field_validation_result_can_hold_discrepancy(self):
        """FieldValidationResult should optionally hold discrepancy details."""
        from tryalma.crosscheck.models import (
            DiscrepancySeverity,
            FieldDiscrepancy,
            FieldValidationResult,
        )

        discrepancy = FieldDiscrepancy(
            field_name="surname",
            mrz_value="SMITH",
            vlm_value="SMYTH",
            recommended_value="SMITH",
            severity=DiscrepancySeverity.WARNING,
            reason="Spelling differs",
        )

        result = FieldValidationResult(
            field_name="surname",
            validated=False,
            mrz_value="SMITH",
            vlm_value="SMYTH",
            final_value="SMITH",
            discrepancy=discrepancy,
        )

        assert result.discrepancy is not None
        assert result.discrepancy.severity == DiscrepancySeverity.WARNING


class TestProcessingMetadata:
    """Tests for ProcessingMetadata structure."""

    def test_processing_metadata_tracks_extraction_duration(self):
        """ProcessingMetadata should track total extraction duration in ms."""
        from tryalma.crosscheck.models import ProcessingMetadata

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        assert metadata.extraction_duration_ms == 3200

    def test_processing_metadata_tracks_mrz_duration(self):
        """ProcessingMetadata should track MRZ extraction duration."""
        from tryalma.crosscheck.models import ProcessingMetadata

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        assert metadata.mrz_duration_ms == 1200

    def test_processing_metadata_tracks_vlm_duration(self):
        """ProcessingMetadata should track VLM extraction duration."""
        from tryalma.crosscheck.models import ProcessingMetadata

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        assert metadata.vlm_duration_ms == 2000

    def test_processing_metadata_tracks_vlm_model(self):
        """ProcessingMetadata should track which VLM model was used."""
        from tryalma.crosscheck.models import ProcessingMetadata

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        assert metadata.vlm_model == "Qwen/Qwen2-VL-7B-Instruct"

    def test_processing_metadata_has_timestamp(self):
        """ProcessingMetadata should include timestamp."""
        from tryalma.crosscheck.models import ProcessingMetadata

        before = datetime.now(UTC)
        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=None,
            vlm_duration_ms=None,
            vlm_model=None,
        )
        after = datetime.now(UTC)

        assert metadata.timestamp >= before
        assert metadata.timestamp <= after

    def test_processing_metadata_durations_can_be_none(self):
        """ProcessingMetadata duration fields can be None when source failed."""
        from tryalma.crosscheck.models import ProcessingMetadata

        metadata = ProcessingMetadata(
            extraction_duration_ms=1500,
            mrz_duration_ms=None,
            vlm_duration_ms=1500,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        assert metadata.mrz_duration_ms is None
        assert metadata.vlm_duration_ms == 1500


class TestCrossCheckResult:
    """Tests for CrossCheckResult container."""

    def test_crosscheck_result_contains_status(self):
        """CrossCheckResult should contain extraction status."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
        )

        assert result.status == ExtractionStatus.SUCCESS

    def test_crosscheck_result_contains_passport_data(self):
        """CrossCheckResult should contain passport data."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus
        from tryalma.passport.models import PassportData

        passport = PassportData(source_file=Path("/test/image.jpg"))

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=passport,
        )

        assert result.passport_data is not None
        assert result.passport_data.source_file == Path("/test/image.jpg")

    def test_crosscheck_result_contains_field_confidences(self):
        """CrossCheckResult should contain confidence scores per field."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            field_confidences={"surname": 1.0, "passport_number": 0.6},
        )

        assert result.field_confidences["surname"] == 1.0
        assert result.field_confidences["passport_number"] == 0.6

    def test_crosscheck_result_contains_document_confidence(self):
        """CrossCheckResult should contain overall document confidence."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            document_confidence=0.91,
        )

        assert result.document_confidence == 0.91

    def test_crosscheck_result_contains_discrepancies(self):
        """CrossCheckResult should contain list of discrepancies."""
        from tryalma.crosscheck.models import (
            CrossCheckResult,
            DiscrepancySeverity,
            ExtractionStatus,
            FieldDiscrepancy,
        )

        discrepancy = FieldDiscrepancy(
            field_name="passport_number",
            mrz_value="123456789",
            vlm_value="123456780",
            recommended_value="123456789",
            severity=DiscrepancySeverity.CRITICAL,
            reason="Check digit mismatch",
        )

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            discrepancies=[discrepancy],
        )

        assert len(result.discrepancies) == 1
        assert result.discrepancies[0].field_name == "passport_number"

    def test_crosscheck_result_contains_sources_used(self):
        """CrossCheckResult should track which sources were used."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            sources_used=["mrz", "qwen2-vl"],
        )

        assert "mrz" in result.sources_used
        assert "qwen2-vl" in result.sources_used

    def test_crosscheck_result_tracks_source_success(self):
        """CrossCheckResult should track per-source success status."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.PARTIAL,
            passport_data=None,
            mrz_extraction_success=True,
            vlm_extraction_success=False,
        )

        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is False

    def test_crosscheck_result_contains_metadata(self):
        """CrossCheckResult should contain processing metadata."""
        from tryalma.crosscheck.models import (
            CrossCheckResult,
            ExtractionStatus,
            ProcessingMetadata,
        )

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            metadata=metadata,
        )

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms == 3200

    def test_crosscheck_result_contains_error_field(self):
        """CrossCheckResult should contain general error message."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.ERROR,
            passport_data=None,
            error="Both extraction sources failed",
        )

        assert result.error == "Both extraction sources failed"

    def test_crosscheck_result_contains_source_specific_errors(self):
        """CrossCheckResult should contain per-source error messages."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.PARTIAL,
            passport_data=None,
            mrz_error="No MRZ detected",
            vlm_error=None,
        )

        assert result.mrz_error == "No MRZ detected"
        assert result.vlm_error is None

    def test_crosscheck_result_defaults_empty_collections(self):
        """CrossCheckResult should default to empty collections."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
        )

        assert result.field_confidences == {}
        assert result.discrepancies == []
        assert result.sources_used == []

    def test_crosscheck_result_to_dict_serializes_to_json(self):
        """CrossCheckResult.to_dict() should produce JSON-serializable dict."""
        from tryalma.crosscheck.models import (
            CrossCheckResult,
            DiscrepancySeverity,
            ExtractionStatus,
            FieldDiscrepancy,
            ProcessingMetadata,
        )
        from tryalma.passport.models import PassportData

        discrepancy = FieldDiscrepancy(
            field_name="passport_number",
            mrz_value="123456789",
            vlm_value="123456780",
            recommended_value="123456789",
            severity=DiscrepancySeverity.CRITICAL,
            reason="Check digit mismatch",
        )

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        passport = PassportData(source_file=Path("/test/image.jpg"), surname="SMITH")

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=passport,
            field_confidences={"surname": 1.0},
            document_confidence=0.91,
            discrepancies=[discrepancy],
            sources_used=["mrz", "qwen2-vl"],
            metadata=metadata,
        )

        output = result.to_dict()

        assert output["status"] == "success"
        assert output["passport_data"]["surname"] == "SMITH"
        assert output["field_confidences"]["surname"] == 1.0
        assert output["document_confidence"] == 0.91
        assert len(output["discrepancies"]) == 1
        assert output["discrepancies"][0]["severity"] == "critical"
        assert output["sources_used"] == ["mrz", "qwen2-vl"]
        assert output["metadata"]["extraction_duration_ms"] == 3200

    def test_crosscheck_result_to_dict_excludes_metadata_when_requested(self):
        """CrossCheckResult.to_dict() should optionally exclude metadata."""
        from tryalma.crosscheck.models import (
            CrossCheckResult,
            ExtractionStatus,
            ProcessingMetadata,
        )

        metadata = ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
        )

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            metadata=metadata,
        )

        output = result.to_dict(include_metadata=False)

        assert "metadata" not in output

    def test_crosscheck_result_has_discrepancies_helper(self):
        """CrossCheckResult.has_discrepancies() should return True when discrepancies exist."""
        from tryalma.crosscheck.models import (
            CrossCheckResult,
            DiscrepancySeverity,
            ExtractionStatus,
            FieldDiscrepancy,
        )

        discrepancy = FieldDiscrepancy(
            field_name="surname",
            mrz_value="SMITH",
            vlm_value="SMYTH",
            recommended_value="SMITH",
            severity=DiscrepancySeverity.WARNING,
            reason="Spelling differs",
        )

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            discrepancies=[discrepancy],
        )

        assert result.has_discrepancies() is True

    def test_crosscheck_result_has_discrepancies_returns_false_when_empty(self):
        """CrossCheckResult.has_discrepancies() should return False when no discrepancies."""
        from tryalma.crosscheck.models import CrossCheckResult, ExtractionStatus

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            discrepancies=[],
        )

        assert result.has_discrepancies() is False

    def test_crosscheck_result_get_critical_discrepancies(self):
        """CrossCheckResult.get_critical_discrepancies() should filter critical only."""
        from tryalma.crosscheck.models import (
            CrossCheckResult,
            DiscrepancySeverity,
            ExtractionStatus,
            FieldDiscrepancy,
        )

        critical = FieldDiscrepancy(
            field_name="passport_number",
            mrz_value="123",
            vlm_value="456",
            recommended_value="123",
            severity=DiscrepancySeverity.CRITICAL,
            reason="Critical mismatch",
        )

        warning = FieldDiscrepancy(
            field_name="surname",
            mrz_value="SMITH",
            vlm_value="SMYTH",
            recommended_value="SMITH",
            severity=DiscrepancySeverity.WARNING,
            reason="Warning mismatch",
        )

        result = CrossCheckResult(
            status=ExtractionStatus.SUCCESS,
            passport_data=None,
            discrepancies=[critical, warning],
        )

        critical_only = result.get_critical_discrepancies()

        assert len(critical_only) == 1
        assert critical_only[0].field_name == "passport_number"
