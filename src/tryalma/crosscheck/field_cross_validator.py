"""Field cross-validator for comparing MRZ and VLM extraction sources.

Task 3.1: FieldCrossValidator class implementing cross-validation logic.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import TYPE_CHECKING

from tryalma.crosscheck.models import (
    DiscrepancySeverity,
    FieldDiscrepancy,
    FieldValidationResult,
    VisualZoneData,
)

if TYPE_CHECKING:
    from tryalma.passport.models import RawMRZData


class FieldCrossValidator:
    """Cross-validates passport fields between MRZ and VLM extraction sources.

    Compares extracted fields between sources, applies normalization before
    comparison, and records discrepancies when values differ.

    Attributes:
        MRZ_PREFERRED_FIELDS: Fields where MRZ is more reliable (machine-readable data).
        VLM_PREFERRED_FIELDS: Fields where VLM is more reliable (human-readable names).
    """

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

    # Severity mapping per design.md
    SEVERITY_MAP: dict[str, DiscrepancySeverity] = {
        "passport_number": DiscrepancySeverity.CRITICAL,
        "date_of_birth": DiscrepancySeverity.CRITICAL,
        "surname": DiscrepancySeverity.WARNING,
        "given_names": DiscrepancySeverity.WARNING,
        "expiry_date": DiscrepancySeverity.WARNING,
        "nationality": DiscrepancySeverity.WARNING,
        "sex": DiscrepancySeverity.INFORMATIONAL,
        "place_of_birth": DiscrepancySeverity.INFORMATIONAL,
    }

    # Field name mapping from MRZ to standard field names
    MRZ_FIELD_MAP: dict[str, str] = {
        "document_number": "passport_number",
        "birth_date": "date_of_birth",
        "nationality": "nationality",
        "surname": "surname",
        "given_names": "given_names",
        "expiry_date": "expiry_date",
        "sex": "sex",
    }

    # Field name mapping from VLM to standard field names
    VLM_FIELD_MAP: dict[str, str] = {
        "passport_number": "passport_number",
        "date_of_birth": "date_of_birth",
        "nationality": "nationality",
        "surname": "surname",
        "given_names": "given_names",
        "expiry_date": "expiry_date",
        "sex": "sex",
        "place_of_birth": "place_of_birth",
    }

    # All standard field names for iteration
    STANDARD_FIELDS: list[str] = [
        "surname",
        "given_names",
        "date_of_birth",
        "nationality",
        "passport_number",
        "expiry_date",
        "sex",
        "place_of_birth",
    ]

    def normalize_field(self, field_name: str, value: str | None) -> str | None:
        """Normalize field value for comparison.

        Applies case folding, whitespace normalization, and diacritics handling
        per Requirement 2.2.

        Args:
            field_name: Name of the field (for potential field-specific rules).
            value: The value to normalize.

        Returns:
            Normalized value, or None if input is None or empty.
        """
        if value is None:
            return None

        value = value.strip()
        if not value:
            return None

        # Case folding
        value = value.lower()

        # Collapse multiple whitespace to single space
        value = re.sub(r"\s+", " ", value)

        # Handle diacritics - decompose and remove combining characters
        # NFKD decomposes characters, then we filter out combining marks
        normalized = unicodedata.normalize("NFKD", value)
        # Remove combining diacritical marks (category 'M')
        value = "".join(c for c in normalized if not unicodedata.combining(c))

        return value

    def normalize_date(self, date_str: str | None) -> str | None:
        """Normalize date to ISO format YYYY-MM-DD.

        Handles multiple input formats per Requirement 2.3:
        - ISO: YYYY-MM-DD
        - MRZ: YYMMDD
        - European: DD/MM/YYYY
        - US: MM-DD-YYYY

        Args:
            date_str: Date string to normalize.

        Returns:
            ISO format date string, or None if input is None, empty, or invalid.
        """
        if date_str is None:
            return None

        date_str = date_str.strip()
        if not date_str:
            return None

        # Try ISO format first (YYYY-MM-DD)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                return None

        # Try MRZ format (YYMMDD)
        if re.match(r"^\d{6}$", date_str):
            try:
                # Interpret YY as 19xx if >= 50, else 20xx
                yy = int(date_str[:2])
                mm = date_str[2:4]
                dd = date_str[4:6]

                if yy >= 50:
                    year = 1900 + yy
                else:
                    year = 2000 + yy

                # Validate it's a real date
                parsed = datetime.strptime(f"{year}-{mm}-{dd}", "%Y-%m-%d")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                return None

        # Try European format (DD/MM/YYYY)
        if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
            try:
                parsed = datetime.strptime(date_str, "%d/%m/%Y")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                return None

        # Try US format (MM-DD-YYYY)
        if re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
            try:
                parsed = datetime.strptime(date_str, "%m-%d-%Y")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                return None

        # Unknown format
        return None

    def _get_mrz_value(self, mrz_data: RawMRZData, field_name: str) -> str | None:
        """Get value from MRZ data for a standard field name."""
        # Reverse lookup: find MRZ attribute name for standard field
        mrz_attr_map = {
            "passport_number": "document_number",
            "date_of_birth": "birth_date",
            "nationality": "nationality",
            "surname": "surname",
            "given_names": "given_names",
            "expiry_date": "expiry_date",
            "sex": "sex",
            "place_of_birth": None,  # MRZ doesn't have this
        }

        attr_name = mrz_attr_map.get(field_name)
        if attr_name is None:
            return None

        return getattr(mrz_data, attr_name, None)

    def _get_vlm_value(self, vlm_data: VisualZoneData, field_name: str) -> str | None:
        """Get value from VLM data for a standard field name."""
        return getattr(vlm_data, field_name, None)

    def _normalize_for_comparison(
        self, field_name: str, value: str | None
    ) -> str | None:
        """Normalize a value for comparison based on field type."""
        if value is None:
            return None

        # Date fields use date normalization
        if field_name in {"date_of_birth", "expiry_date"}:
            return self.normalize_date(value)

        # Other fields use text normalization
        return self.normalize_field(field_name, value)

    def _select_final_value(
        self,
        field_name: str,
        mrz_value: str | None,
        vlm_value: str | None,
    ) -> str | None:
        """Select the final value based on source preference rules.

        Args:
            field_name: Standard field name.
            mrz_value: Raw value from MRZ.
            vlm_value: Raw value from VLM.

        Returns:
            The preferred source's value.
        """
        # If only one source has a value, use it
        if mrz_value is None and vlm_value is None:
            return None
        if mrz_value is not None and vlm_value is None:
            return mrz_value
        if mrz_value is None and vlm_value is not None:
            return vlm_value

        # Both have values - apply preference rules
        if field_name in self.MRZ_PREFERRED_FIELDS:
            return mrz_value
        if field_name in self.VLM_PREFERRED_FIELDS:
            return vlm_value

        # Default to MRZ for fields not explicitly categorized
        return mrz_value

    def cross_validate(
        self,
        mrz_data: RawMRZData | None,
        visual_data: VisualZoneData | None,
    ) -> list[FieldValidationResult]:
        """Compare all fields between MRZ and VLM sources.

        Cross-validates each passport field, applying normalization before
        comparison. Records discrepancies for fields where sources disagree.

        Args:
            mrz_data: Extracted MRZ data, or None if extraction failed.
            visual_data: Extracted visual zone data, or None if extraction failed.

        Returns:
            List of FieldValidationResult for each passport field that has data.
        """
        # Handle both sources being None
        if mrz_data is None and visual_data is None:
            return []

        results: list[FieldValidationResult] = []

        for field_name in self.STANDARD_FIELDS:
            # Get raw values from each source
            mrz_value = (
                self._get_mrz_value(mrz_data, field_name) if mrz_data else None
            )
            vlm_value = (
                self._get_vlm_value(visual_data, field_name) if visual_data else None
            )

            # Skip if neither source has a value
            if mrz_value is None and vlm_value is None:
                continue

            # Normalize for comparison
            mrz_normalized = self._normalize_for_comparison(field_name, mrz_value)
            vlm_normalized = self._normalize_for_comparison(field_name, vlm_value)

            # Select final value
            final_value = self._select_final_value(field_name, mrz_value, vlm_value)

            # Determine if validated (agreement or single source)
            if mrz_value is None or vlm_value is None:
                # Single source - validated by default
                validated = True
                discrepancy = None
            elif mrz_normalized == vlm_normalized:
                # Both sources agree
                validated = True
                discrepancy = None
            else:
                # Sources disagree - record discrepancy
                validated = False
                severity = self.SEVERITY_MAP.get(
                    field_name, DiscrepancySeverity.INFORMATIONAL
                )

                # Determine reason based on source preference
                if field_name in self.MRZ_PREFERRED_FIELDS:
                    reason = f"MRZ preferred for {field_name}; values differ"
                elif field_name in self.VLM_PREFERRED_FIELDS:
                    reason = f"VLM preferred for {field_name}; values differ"
                else:
                    reason = f"Values differ for {field_name}"

                discrepancy = FieldDiscrepancy(
                    field_name=field_name,
                    mrz_value=mrz_value,
                    vlm_value=vlm_value,
                    recommended_value=final_value,
                    severity=severity,
                    reason=reason,
                )

            results.append(
                FieldValidationResult(
                    field_name=field_name,
                    validated=validated,
                    mrz_value=mrz_value,
                    vlm_value=vlm_value,
                    final_value=final_value,
                    discrepancy=discrepancy,
                )
            )

        return results
