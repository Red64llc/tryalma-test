"""Unit tests for DiscrepancyReporter.

Task 3.3: Test discrepancy reporting and severity classification.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest

from tryalma.crosscheck.discrepancy_reporter import DiscrepancyReporter
from tryalma.crosscheck.models import (
    DiscrepancySeverity,
    FieldDiscrepancy,
    FieldValidationResult,
)


class TestSeverityMapping:
    """Test severity classification for each passport field (Requirement 5.5)."""

    def test_passport_number_is_critical(self):
        """Passport number discrepancies should be critical."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["passport_number"] == DiscrepancySeverity.CRITICAL

    def test_date_of_birth_is_critical(self):
        """Date of birth discrepancies should be critical."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["date_of_birth"] == DiscrepancySeverity.CRITICAL

    def test_surname_is_warning(self):
        """Surname discrepancies should be warning level."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["surname"] == DiscrepancySeverity.WARNING

    def test_given_names_is_warning(self):
        """Given names discrepancies should be warning level."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["given_names"] == DiscrepancySeverity.WARNING

    def test_expiry_date_is_warning(self):
        """Expiry date discrepancies should be warning level."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["expiry_date"] == DiscrepancySeverity.WARNING

    def test_nationality_is_warning(self):
        """Nationality discrepancies should be warning level."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["nationality"] == DiscrepancySeverity.WARNING

    def test_sex_is_informational(self):
        """Sex discrepancies should be informational."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["sex"] == DiscrepancySeverity.INFORMATIONAL

    def test_place_of_birth_is_informational(self):
        """Place of birth discrepancies should be informational."""
        reporter = DiscrepancyReporter()
        assert reporter.SEVERITY_MAP["place_of_birth"] == DiscrepancySeverity.INFORMATIONAL


class TestValueRecommendation:
    """Test value recommendation based on source reliability (Requirement 5.3)."""

    def test_recommend_mrz_for_passport_number(self):
        """MRZ should be recommended for passport number."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="passport_number",
            mrz_value="MRZ123456",
            vlm_value="VLM123456",
        )

        assert recommended == "MRZ123456"

    def test_recommend_mrz_for_date_of_birth(self):
        """MRZ should be recommended for date of birth."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="date_of_birth",
            mrz_value="1985-03-15",
            vlm_value="1985-03-16",
        )

        assert recommended == "1985-03-15"

    def test_recommend_mrz_for_expiry_date(self):
        """MRZ should be recommended for expiry date."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="expiry_date",
            mrz_value="2030-03-14",
            vlm_value="2030-03-15",
        )

        assert recommended == "2030-03-14"

    def test_recommend_mrz_for_nationality(self):
        """MRZ should be recommended for nationality."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="nationality",
            mrz_value="USA",
            vlm_value="US",
        )

        assert recommended == "USA"

    def test_recommend_vlm_for_surname(self):
        """VLM should be recommended for surname (handles special chars)."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="surname",
            mrz_value="MULLER",
            vlm_value="MUELLER",
        )

        assert recommended == "MUELLER"

    def test_recommend_vlm_for_given_names(self):
        """VLM should be recommended for given names."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="given_names",
            mrz_value="JOSE",
            vlm_value="JOSE MARIA",
        )

        assert recommended == "JOSE MARIA"

    def test_recommend_vlm_for_place_of_birth(self):
        """VLM should be recommended for place of birth."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="place_of_birth",
            mrz_value=None,  # MRZ doesn't have this
            vlm_value="NEW YORK",
        )

        assert recommended == "NEW YORK"

    def test_recommend_falls_back_when_preferred_is_none(self):
        """Should fall back to other source when preferred source is None."""
        reporter = DiscrepancyReporter()

        # surname prefers VLM, but VLM is None
        recommended = reporter.recommend_value(
            field_name="surname",
            mrz_value="SMITH",
            vlm_value=None,
        )

        assert recommended == "SMITH"

    def test_recommend_none_when_both_none(self):
        """Should return None when both sources are None."""
        reporter = DiscrepancyReporter()

        recommended = reporter.recommend_value(
            field_name="surname",
            mrz_value=None,
            vlm_value=None,
        )

        assert recommended is None

    def test_recommend_default_to_mrz_for_unknown_field(self):
        """Should default to MRZ for fields not explicitly categorized."""
        reporter = DiscrepancyReporter()

        # sex is not in either preference list in reporter
        recommended = reporter.recommend_value(
            field_name="sex",
            mrz_value="M",
            vlm_value="F",
        )

        # Default should be MRZ
        assert recommended == "M"


class TestGenerateReport:
    """Test discrepancy report generation (Requirement 5.1)."""

    def test_generate_report_includes_discrepant_fields(self):
        """Report should include all fields where sources disagree."""
        reporter = DiscrepancyReporter()

        validation_results = [
            FieldValidationResult(
                field_name="surname",
                validated=True,  # No discrepancy
                mrz_value="SMITH",
                vlm_value="SMITH",
                final_value="SMITH",
                discrepancy=None,
            ),
            FieldValidationResult(
                field_name="passport_number",
                validated=False,  # Has discrepancy
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
            ),
        ]

        report = reporter.generate_report(validation_results)

        # Only passport_number should be in report
        assert len(report) == 1
        assert report[0].field_name == "passport_number"

    def test_generate_report_empty_when_no_discrepancies(self):
        """Report should be empty when all sources agree (Requirement 5.4)."""
        reporter = DiscrepancyReporter()

        validation_results = [
            FieldValidationResult(
                field_name="surname",
                validated=True,
                mrz_value="SMITH",
                vlm_value="SMITH",
                final_value="SMITH",
                discrepancy=None,
            ),
            FieldValidationResult(
                field_name="passport_number",
                validated=True,
                mrz_value="123456789",
                vlm_value="123456789",
                final_value="123456789",
                discrepancy=None,
            ),
        ]

        report = reporter.generate_report(validation_results)

        assert len(report) == 0

    def test_generate_report_includes_mrz_and_vlm_values(self):
        """Report should include both source values (Requirement 5.2)."""
        reporter = DiscrepancyReporter()

        validation_results = [
            FieldValidationResult(
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
            ),
        ]

        report = reporter.generate_report(validation_results)

        assert report[0].mrz_value == "SMITH"
        assert report[0].vlm_value == "SMYTH"

    def test_generate_report_includes_recommended_value(self):
        """Report should include recommended value (Requirement 5.2)."""
        reporter = DiscrepancyReporter()

        validation_results = [
            FieldValidationResult(
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
                    reason="MRZ preferred",
                ),
            ),
        ]

        report = reporter.generate_report(validation_results)

        assert report[0].recommended_value == "123456789"

    def test_generate_report_assigns_correct_severity(self):
        """Report should have correct severity for each field."""
        reporter = DiscrepancyReporter()

        validation_results = [
            FieldValidationResult(
                field_name="passport_number",
                validated=False,
                mrz_value="123",
                vlm_value="456",
                final_value="123",
                discrepancy=FieldDiscrepancy(
                    field_name="passport_number",
                    mrz_value="123",
                    vlm_value="456",
                    recommended_value="123",
                    severity=DiscrepancySeverity.CRITICAL,
                    reason="Values differ",
                ),
            ),
            FieldValidationResult(
                field_name="sex",
                validated=False,
                mrz_value="M",
                vlm_value="F",
                final_value="M",
                discrepancy=FieldDiscrepancy(
                    field_name="sex",
                    mrz_value="M",
                    vlm_value="F",
                    recommended_value="M",
                    severity=DiscrepancySeverity.INFORMATIONAL,
                    reason="Values differ",
                ),
            ),
        ]

        report = reporter.generate_report(validation_results)

        passport_disc = next(d for d in report if d.field_name == "passport_number")
        sex_disc = next(d for d in report if d.field_name == "sex")

        assert passport_disc.severity == DiscrepancySeverity.CRITICAL
        assert sex_disc.severity == DiscrepancySeverity.INFORMATIONAL


class TestGenerateReportFromRawData:
    """Test creating discrepancy report from raw field data."""

    def test_create_discrepancy_directly(self):
        """Should be able to create a discrepancy directly from field values."""
        reporter = DiscrepancyReporter()

        discrepancy = reporter.create_discrepancy(
            field_name="passport_number",
            mrz_value="123456789",
            vlm_value="123456780",
        )

        assert discrepancy.field_name == "passport_number"
        assert discrepancy.mrz_value == "123456789"
        assert discrepancy.vlm_value == "123456780"
        assert discrepancy.recommended_value == "123456789"  # MRZ preferred
        assert discrepancy.severity == DiscrepancySeverity.CRITICAL

    def test_create_discrepancy_includes_reason(self):
        """Discrepancy should include reason for recommendation."""
        reporter = DiscrepancyReporter()

        discrepancy = reporter.create_discrepancy(
            field_name="surname",
            mrz_value="MULLER",
            vlm_value="MUELLER",
        )

        assert "vlm" in discrepancy.reason.lower() or "VLM" in discrepancy.reason

    def test_create_discrepancy_with_missing_mrz(self):
        """Should handle missing MRZ value."""
        reporter = DiscrepancyReporter()

        discrepancy = reporter.create_discrepancy(
            field_name="place_of_birth",
            mrz_value=None,
            vlm_value="NEW YORK",
        )

        assert discrepancy.mrz_value is None
        assert discrepancy.vlm_value == "NEW YORK"
        assert discrepancy.recommended_value == "NEW YORK"

    def test_create_discrepancy_with_missing_vlm(self):
        """Should handle missing VLM value."""
        reporter = DiscrepancyReporter()

        discrepancy = reporter.create_discrepancy(
            field_name="passport_number",
            mrz_value="123456789",
            vlm_value=None,
        )

        assert discrepancy.mrz_value == "123456789"
        assert discrepancy.vlm_value is None
        assert discrepancy.recommended_value == "123456789"


class TestMultipleDiscrepancies:
    """Test handling multiple discrepancies in a single report."""

    def test_report_preserves_order(self):
        """Report should maintain field order from validation results."""
        reporter = DiscrepancyReporter()

        validation_results = [
            FieldValidationResult(
                field_name="surname",
                validated=False,
                mrz_value="A",
                vlm_value="B",
                final_value="B",
                discrepancy=FieldDiscrepancy(
                    field_name="surname",
                    mrz_value="A",
                    vlm_value="B",
                    recommended_value="B",
                    severity=DiscrepancySeverity.WARNING,
                    reason="Differ",
                ),
            ),
            FieldValidationResult(
                field_name="passport_number",
                validated=False,
                mrz_value="1",
                vlm_value="2",
                final_value="1",
                discrepancy=FieldDiscrepancy(
                    field_name="passport_number",
                    mrz_value="1",
                    vlm_value="2",
                    recommended_value="1",
                    severity=DiscrepancySeverity.CRITICAL,
                    reason="Differ",
                ),
            ),
        ]

        report = reporter.generate_report(validation_results)

        assert len(report) == 2
        assert report[0].field_name == "surname"
        assert report[1].field_name == "passport_number"

    def test_report_with_empty_validation_results(self):
        """Report should handle empty validation results."""
        reporter = DiscrepancyReporter()

        report = reporter.generate_report([])

        assert len(report) == 0
