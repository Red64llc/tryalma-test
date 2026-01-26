"""Tests for PopulationReporter and PopulationReport.

TDD tests for Tasks 5.1 and 5.2:
- 5.1: Population result tracking (Requirements: 12.2, 12.3, 12.4, 12.5)
- 5.2: Report generation (Requirements: 12.1, 12.6)
"""

import json
from datetime import datetime

import pytest
from freezegun import freeze_time

from tryalma.form_populator.models import FieldStatus, FieldResult
from tryalma.form_populator.reporter import (
    PopulationReport,
    PopulationReporter,
)


class TestFieldResult:
    """Test the FieldResult dataclass for result tracking."""

    def test_field_result_populated_status(self):
        """FieldResult can track populated field with value and selector."""
        result = FieldResult(
            field_id="attorney_family_name",
            status=FieldStatus.POPULATED,
            value="Smith",
            selector="input[name='familyName']",
        )

        assert result.field_id == "attorney_family_name"
        assert result.status == FieldStatus.POPULATED
        assert result.value == "Smith"
        assert result.selector == "input[name='familyName']"
        assert result.error_message is None

    def test_field_result_skipped_status(self):
        """FieldResult can track skipped field with reason."""
        result = FieldResult(
            field_id="attorney_online_account",
            status=FieldStatus.SKIPPED,
            error_message="No data available",
            selector="input[name='onlineAccountNumber']",
        )

        assert result.field_id == "attorney_online_account"
        assert result.status == FieldStatus.SKIPPED
        assert result.error_message == "No data available"

    def test_field_result_error_status(self):
        """FieldResult can track errored field with error description."""
        result = FieldResult(
            field_id="attorney_state",
            status=FieldStatus.ERROR,
            value="XY",
            error_message="No matching option found for value: XY",
            selector="select[name='state']",
        )

        assert result.field_id == "attorney_state"
        assert result.status == FieldStatus.ERROR
        assert result.error_message == "No matching option found for value: XY"
        assert result.value == "XY"

    def test_field_result_manual_required_status(self):
        """FieldResult can track fields requiring manual attention."""
        result = FieldResult(
            field_id="client_signature",
            status=FieldStatus.MANUAL_REQUIRED,
            error_message="Signature requires manual completion",
            selector="input[name='clientSignature']",
        )

        assert result.field_id == "client_signature"
        assert result.status == FieldStatus.MANUAL_REQUIRED
        assert result.error_message == "Signature requires manual completion"


class TestPopulationReport:
    """Test the PopulationReport dataclass (Requirement 12.1)."""

    def test_population_report_creation(self):
        """PopulationReport contains all required fields."""
        populated = [
            FieldResult("field1", FieldStatus.POPULATED, "value1", selector="sel1"),
        ]
        skipped = [
            FieldResult("field2", FieldStatus.SKIPPED, error_message="No data"),
        ]
        errors = [
            FieldResult("field3", FieldStatus.ERROR, error_message="Failed"),
        ]
        manual = [
            FieldResult("sig", FieldStatus.MANUAL_REQUIRED, error_message="Manual"),
        ]

        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=5234,
            populated_fields=populated,
            skipped_fields=skipped,
            error_fields=errors,
            manual_attention_fields=manual,
        )

        assert report.success is True
        assert report.form_url == "https://example.com/form"
        assert report.timestamp == "2026-01-25T10:30:00Z"
        assert report.duration_ms == 5234
        assert len(report.populated_fields) == 1
        assert len(report.skipped_fields) == 1
        assert len(report.error_fields) == 1
        assert len(report.manual_attention_fields) == 1

    def test_population_report_to_dict(self):
        """PopulationReport.to_dict() returns proper dictionary structure."""
        populated = [
            FieldResult("field1", FieldStatus.POPULATED, "value1", selector="sel1"),
        ]
        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=5234,
            populated_fields=populated,
            skipped_fields=[],
            error_fields=[],
            manual_attention_fields=[],
        )

        result = report.to_dict()

        assert result["success"] is True
        assert result["form_url"] == "https://example.com/form"
        assert result["timestamp"] == "2026-01-25T10:30:00Z"
        assert result["duration_ms"] == 5234
        assert "summary" in result
        assert result["summary"]["populated"] == 1
        assert result["summary"]["skipped"] == 0
        assert result["summary"]["errors"] == 0
        assert result["summary"]["manual_required"] == 0

    def test_population_report_to_json(self):
        """PopulationReport.to_json() serializes to valid JSON string."""
        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=5234,
            populated_fields=[],
            skipped_fields=[],
            error_fields=[],
            manual_attention_fields=[],
        )

        json_str = report.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert parsed["form_url"] == "https://example.com/form"

    def test_population_report_summary_counts(self):
        """PopulationReport summary includes correct counts."""
        populated = [
            FieldResult("f1", FieldStatus.POPULATED, "v1"),
            FieldResult("f2", FieldStatus.POPULATED, "v2"),
            FieldResult("f3", FieldStatus.POPULATED, "v3"),
        ]
        skipped = [
            FieldResult("s1", FieldStatus.SKIPPED, error_message="Missing"),
            FieldResult("s2", FieldStatus.SKIPPED, error_message="Missing"),
        ]
        errors = [
            FieldResult("e1", FieldStatus.ERROR, error_message="Failed"),
        ]
        manual = [
            FieldResult("m1", FieldStatus.MANUAL_REQUIRED, error_message="Manual"),
            FieldResult("m2", FieldStatus.MANUAL_REQUIRED, error_message="Manual"),
            FieldResult("m3", FieldStatus.MANUAL_REQUIRED, error_message="Manual"),
            FieldResult("m4", FieldStatus.MANUAL_REQUIRED, error_message="Manual"),
        ]

        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=1000,
            populated_fields=populated,
            skipped_fields=skipped,
            error_fields=errors,
            manual_attention_fields=manual,
        )

        result = report.to_dict()
        summary = result["summary"]

        assert summary["total_fields"] == 10  # 3 + 2 + 1 + 4
        assert summary["populated"] == 3
        assert summary["skipped"] == 2
        assert summary["errors"] == 1
        assert summary["manual_required"] == 4


class TestPopulationReporter:
    """Test the PopulationReporter class for tracking and generating reports."""

    def test_reporter_creation(self):
        """PopulationReporter can be created."""
        reporter = PopulationReporter()
        assert reporter is not None

    def test_record_populated(self):
        """record_populated tracks field with value and selector."""
        reporter = PopulationReporter()

        reporter.record_populated(
            field_id="attorney_family_name",
            value="Smith",
            selector="input[name='familyName']",
        )

        # Verify internally tracked
        assert len(reporter._populated_fields) == 1
        result = reporter._populated_fields[0]
        assert result.field_id == "attorney_family_name"
        assert result.status == FieldStatus.POPULATED
        assert result.value == "Smith"

    def test_record_skipped(self):
        """record_skipped tracks field with reason for skipping."""
        reporter = PopulationReporter()

        reporter.record_skipped(
            field_id="attorney_online_account",
            reason="No data available",
            selector="input[name='onlineAccountNumber']",
        )

        assert len(reporter._skipped_fields) == 1
        result = reporter._skipped_fields[0]
        assert result.field_id == "attorney_online_account"
        assert result.status == FieldStatus.SKIPPED
        assert result.error_message == "No data available"

    def test_record_error(self):
        """record_error tracks field with error description."""
        reporter = PopulationReporter()

        reporter.record_error(
            field_id="attorney_state",
            error="Element not found",
            selector="select[name='state']",
        )

        assert len(reporter._error_fields) == 1
        result = reporter._error_fields[0]
        assert result.field_id == "attorney_state"
        assert result.status == FieldStatus.ERROR
        assert result.error_message == "Element not found"

    def test_record_manual_required(self):
        """record_manual_required tracks fields requiring manual attention."""
        reporter = PopulationReporter()

        reporter.record_manual_required(
            field_id="client_signature",
            reason="Signature requires manual completion",
        )

        assert len(reporter._manual_attention_fields) == 1
        result = reporter._manual_attention_fields[0]
        assert result.field_id == "client_signature"
        assert result.status == FieldStatus.MANUAL_REQUIRED

    @freeze_time("2026-01-25T10:30:00Z")
    def test_generate_report_includes_timestamp(self):
        """generate_report includes correct timestamp."""
        reporter = PopulationReporter()
        start_time = datetime(2026, 1, 25, 10, 29, 55)  # 5 seconds earlier

        report = reporter.generate_report(
            form_url="https://example.com/form",
            start_time=start_time,
        )

        assert report.timestamp == "2026-01-25T10:30:00Z"
        assert report.duration_ms == 5000  # 5 seconds

    def test_generate_report_includes_form_url(self):
        """generate_report includes target form URL."""
        reporter = PopulationReporter()
        start_time = datetime.now()

        report = reporter.generate_report(
            form_url="https://mendrika-alma.github.io/form-submission/",
            start_time=start_time,
        )

        assert report.form_url == "https://mendrika-alma.github.io/form-submission/"

    def test_generate_report_success_when_no_errors(self):
        """generate_report sets success=True when no errors."""
        reporter = PopulationReporter()
        reporter.record_populated("field1", "value1", "sel1")
        start_time = datetime.now()

        report = reporter.generate_report(
            form_url="https://example.com/form",
            start_time=start_time,
        )

        assert report.success is True

    def test_generate_report_success_false_when_errors_exist(self):
        """generate_report sets success=False when errors exist."""
        reporter = PopulationReporter()
        reporter.record_populated("field1", "value1", "sel1")
        reporter.record_error("field2", "Failed", "sel2")
        start_time = datetime.now()

        report = reporter.generate_report(
            form_url="https://example.com/form",
            start_time=start_time,
        )

        assert report.success is False

    def test_generate_report_collects_all_fields(self):
        """generate_report collects all tracked fields."""
        reporter = PopulationReporter()
        reporter.record_populated("p1", "v1", "s1")
        reporter.record_populated("p2", "v2", "s2")
        reporter.record_skipped("sk1", "No data", "s3")
        reporter.record_error("e1", "Failed", "s4")
        reporter.record_manual_required("m1", "Signature")
        start_time = datetime.now()

        report = reporter.generate_report(
            form_url="https://example.com/form",
            start_time=start_time,
        )

        assert len(report.populated_fields) == 2
        assert len(report.skipped_fields) == 1
        assert len(report.error_fields) == 1
        assert len(report.manual_attention_fields) == 1

    def test_generate_report_calculates_duration(self):
        """generate_report calculates operation duration in milliseconds."""
        reporter = PopulationReporter()
        # Use fixed time for predictable duration
        start_time = datetime(2026, 1, 25, 10, 0, 0, 0)
        end_time = datetime(2026, 1, 25, 10, 0, 5, 234000)  # 5.234 seconds later

        with freeze_time(end_time):
            report = reporter.generate_report(
                form_url="https://example.com/form",
                start_time=start_time,
            )

        assert report.duration_ms == 5234

    def test_reporter_reset(self):
        """Reporter can be reset to clear tracked fields."""
        reporter = PopulationReporter()
        reporter.record_populated("field1", "value1", "sel1")
        reporter.record_error("field2", "Failed", "sel2")

        reporter.reset()

        assert len(reporter._populated_fields) == 0
        assert len(reporter._error_fields) == 0
        assert len(reporter._skipped_fields) == 0
        assert len(reporter._manual_attention_fields) == 0


class TestPopulationReportSerialization:
    """Test PopulationReport JSON serialization (Requirement 12.6)."""

    def test_to_json_includes_all_field_details(self):
        """to_json includes field details in populated_fields."""
        populated = [
            FieldResult(
                "attorney_family_name",
                FieldStatus.POPULATED,
                "Smith",
                selector="input[name='familyName']",
            ),
        ]
        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=1000,
            populated_fields=populated,
            skipped_fields=[],
            error_fields=[],
            manual_attention_fields=[],
        )

        json_str = report.to_json()
        parsed = json.loads(json_str)

        assert len(parsed["populated_fields"]) == 1
        field = parsed["populated_fields"][0]
        assert field["field_id"] == "attorney_family_name"
        assert field["value"] == "Smith"
        assert field["selector"] == "input[name='familyName']"

    def test_to_json_includes_skipped_field_reasons(self):
        """to_json includes reason for skipped fields."""
        skipped = [
            FieldResult(
                "attorney_online_account",
                FieldStatus.SKIPPED,
                error_message="No data available",
            ),
        ]
        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=1000,
            populated_fields=[],
            skipped_fields=skipped,
            error_fields=[],
            manual_attention_fields=[],
        )

        json_str = report.to_json()
        parsed = json.loads(json_str)

        assert len(parsed["skipped_fields"]) == 1
        field = parsed["skipped_fields"][0]
        assert field["field_id"] == "attorney_online_account"
        assert field["reason"] == "No data available"

    def test_to_json_includes_error_descriptions(self):
        """to_json includes error descriptions for error fields."""
        errors = [
            FieldResult(
                "attorney_state",
                FieldStatus.ERROR,
                "XY",
                error_message="No matching option found",
                selector="select[name='state']",
            ),
        ]
        report = PopulationReport(
            success=False,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=1000,
            populated_fields=[],
            skipped_fields=[],
            error_fields=errors,
            manual_attention_fields=[],
        )

        json_str = report.to_json()
        parsed = json.loads(json_str)

        assert len(parsed["error_fields"]) == 1
        field = parsed["error_fields"][0]
        assert field["field_id"] == "attorney_state"
        assert field["error"] == "No matching option found"

    def test_to_json_includes_manual_attention_reasons(self):
        """to_json includes reasons for manual attention fields."""
        manual = [
            FieldResult(
                "client_signature",
                FieldStatus.MANUAL_REQUIRED,
                error_message="Signature requires manual completion",
            ),
        ]
        report = PopulationReport(
            success=True,
            form_url="https://example.com/form",
            timestamp="2026-01-25T10:30:00Z",
            duration_ms=1000,
            populated_fields=[],
            skipped_fields=[],
            error_fields=[],
            manual_attention_fields=manual,
        )

        json_str = report.to_json()
        parsed = json.loads(json_str)

        assert len(parsed["manual_attention_fields"]) == 1
        field = parsed["manual_attention_fields"][0]
        assert field["field_id"] == "client_signature"
        assert field["reason"] == "Signature requires manual completion"
