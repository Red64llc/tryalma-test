"""Discrepancy reporter for cross-check validation results.

Task 3.3: DiscrepancyReporter class implementing discrepancy reporting.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from __future__ import annotations

from tryalma.crosscheck.models import (
    DiscrepancySeverity,
    FieldDiscrepancy,
    FieldValidationResult,
)


class DiscrepancyReporter:
    """Generates discrepancy reports from cross-validation results.

    Implements severity classification based on field type and provides
    value recommendations based on source reliability rules.

    Attributes:
        SEVERITY_MAP: Mapping of field names to severity levels.
        MRZ_PREFERRED_FIELDS: Fields where MRZ is more reliable.
        VLM_PREFERRED_FIELDS: Fields where VLM is more reliable.
    """

    # Severity mapping per design.md and Requirement 5.5
    SEVERITY_MAP: dict[str, DiscrepancySeverity] = {
        # Critical: Identity fields
        "passport_number": DiscrepancySeverity.CRITICAL,
        "date_of_birth": DiscrepancySeverity.CRITICAL,
        # Warning: Important fields
        "surname": DiscrepancySeverity.WARNING,
        "given_names": DiscrepancySeverity.WARNING,
        "expiry_date": DiscrepancySeverity.WARNING,
        "nationality": DiscrepancySeverity.WARNING,
        # Informational: Optional fields
        "sex": DiscrepancySeverity.INFORMATIONAL,
        "place_of_birth": DiscrepancySeverity.INFORMATIONAL,
    }

    # Source preference rules per Requirement 5.3
    MRZ_PREFERRED_FIELDS: set[str] = {
        "passport_number",
        "date_of_birth",
        "expiry_date",
        "nationality",
    }

    VLM_PREFERRED_FIELDS: set[str] = {
        "surname",
        "given_names",
        "place_of_birth",
    }

    def recommend_value(
        self,
        field_name: str,
        mrz_value: str | None,
        vlm_value: str | None,
    ) -> str | None:
        """Recommend value based on source reliability rules.

        Rules per Requirement 5.3:
        - MRZ preferred for machine-readable data (numbers, dates)
        - VLM preferred for names with special characters

        Args:
            field_name: Name of the field.
            mrz_value: Value from MRZ extraction.
            vlm_value: Value from Qwen2-VL extraction.

        Returns:
            Recommended value, or None if neither source has data.
        """
        # Handle cases where one source is missing
        if mrz_value is None and vlm_value is None:
            return None

        if mrz_value is not None and vlm_value is None:
            return mrz_value

        if mrz_value is None and vlm_value is not None:
            return vlm_value

        # Both have values - apply preference rules
        if field_name in self.VLM_PREFERRED_FIELDS:
            return vlm_value
        if field_name in self.MRZ_PREFERRED_FIELDS:
            return mrz_value

        # Default to MRZ for fields not explicitly categorized
        return mrz_value

    def _get_severity(self, field_name: str) -> DiscrepancySeverity:
        """Get severity level for a field.

        Args:
            field_name: Name of the field.

        Returns:
            Severity level, defaulting to INFORMATIONAL for unknown fields.
        """
        return self.SEVERITY_MAP.get(field_name, DiscrepancySeverity.INFORMATIONAL)

    def _get_reason(
        self,
        field_name: str,
        mrz_value: str | None,
        vlm_value: str | None,
    ) -> str:
        """Generate reason string for recommendation.

        Args:
            field_name: Name of the field.
            mrz_value: Value from MRZ extraction.
            vlm_value: Value from VLM extraction.

        Returns:
            Human-readable reason for the recommendation.
        """
        if mrz_value is None:
            return f"Only VLM has value for {field_name}"
        if vlm_value is None:
            return f"Only MRZ has value for {field_name}"

        if field_name in self.VLM_PREFERRED_FIELDS:
            return f"VLM preferred for {field_name}; handles special characters better"
        if field_name in self.MRZ_PREFERRED_FIELDS:
            return f"MRZ preferred for {field_name}; machine-readable data more reliable"

        return f"MRZ used as default for {field_name}; values differ"

    def create_discrepancy(
        self,
        field_name: str,
        mrz_value: str | None,
        vlm_value: str | None,
    ) -> FieldDiscrepancy:
        """Create a discrepancy record from field values.

        Args:
            field_name: Name of the field.
            mrz_value: Value from MRZ extraction.
            vlm_value: Value from VLM extraction.

        Returns:
            FieldDiscrepancy with all details populated.
        """
        return FieldDiscrepancy(
            field_name=field_name,
            mrz_value=mrz_value,
            vlm_value=vlm_value,
            recommended_value=self.recommend_value(field_name, mrz_value, vlm_value),
            severity=self._get_severity(field_name),
            reason=self._get_reason(field_name, mrz_value, vlm_value),
        )

    def generate_report(
        self,
        validation_results: list[FieldValidationResult],
    ) -> list[FieldDiscrepancy]:
        """Generate list of discrepancies from validation results.

        Includes only fields where sources disagree (validated=False).
        Returns empty list when all sources agree (Requirement 5.4).

        Args:
            validation_results: Results from FieldCrossValidator.

        Returns:
            List of FieldDiscrepancy for fields where sources disagree.
        """
        discrepancies: list[FieldDiscrepancy] = []

        for result in validation_results:
            # Only include fields with discrepancies
            if result.discrepancy is not None:
                discrepancies.append(result.discrepancy)

        return discrepancies
