"""Field mapping configuration for form population.

This module defines the data structures and configuration for mapping
extracted document data to form field CSS selectors on the target form.

Task 3.1: Field mapping data structures (Requirements: 3.1, 3.3, 9.4)
Task 3.2: Target form field mappings (Requirements: 3.1, 3.3, 9.1-9.4)
Task 3.3: Mapping validation and field retrieval (Requirements: 3.2, 3.4, 3.5)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FieldType(Enum):
    """Enumeration of supported form field types.

    Requirements: 3.3 - Support mapping to text inputs, dropdowns,
                        checkboxes, radio buttons, and date fields.
    """

    TEXT = "text"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    SIGNATURE = "signature"  # Excluded from population (Requirement 9.4)


@dataclass(frozen=True)
class FieldMapping:
    """Single field mapping configuration.

    Maps an extracted data key to a form field CSS selector with
    type information, required status, and format pattern.

    Attributes:
        field_id: Unique identifier for the extracted data field.
        selector: CSS selector for the target form field.
        field_type: Type of the form field (text, dropdown, etc.).
        required: Whether this field is required (default False).
        is_signature: Whether this is a signature field to exclude (default False).
        format_pattern: Optional format pattern (e.g., "###-###-####" for phone).

    Requirements: 3.1
    """

    field_id: str
    selector: str
    field_type: FieldType
    required: bool = False
    is_signature: bool = False
    format_pattern: str | None = None


# Target form field mappings for https://mendrika-alma.github.io/form-submission/
# This maps extracted data keys to form field CSS selectors.
#
# Requirements:
# - 3.1: Associate extracted data keys with form field selectors
# - 3.3: Support all field types
# - 9.1-9.4: Mark and exclude signature fields

FORM_FIELD_MAPPINGS: list[FieldMapping] = [
    # Part 1: Attorney/Representative Information
    # Keys match webapp's FieldMapper output (attorney_surname, attorney_given_names, etc.)
    FieldMapping(
        "attorney_surname",  # From webapp extraction: attorney_surname
        "input[name='familyName']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_given_names",  # From webapp extraction: attorney_given_names
        "input[name='givenName']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_phone",  # From webapp extraction: attorney_phone
        "input[name='daytimePhone']",
        FieldType.TEXT,
        format_pattern="###-###-####",
    ),
    FieldMapping(
        "attorney_email",  # From webapp extraction: attorney_email
        "input[name='email']",
        FieldType.TEXT,
    ),
    # Note: Part 2 eligibility fields are not extracted from documents
    # and are not included in the mapping. They require manual entry.
    # Part 3: Beneficiary/Applicant Information (from passport and G-28)
    # Keys match webapp's FieldMapper output
    FieldMapping(
        "applicant_surname",  # From webapp: applicant_surname
        "input[name='lastName']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "applicant_given_names",  # From webapp: applicant_given_names
        "input[name='firstNames']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "passport_number",  # From webapp: passport_number
        "input[name='passportNumber']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "nationality",  # From webapp: nationality
        "input[name='nationality']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "applicant_dob",  # From webapp: applicant_dob
        "input[name='dateOfBirth']",
        FieldType.DATE,
    ),
    FieldMapping(
        "applicant_sex",  # From webapp: applicant_sex
        "input[name='sex']",
        FieldType.RADIO,
    ),
    FieldMapping(
        "passport_expiry",  # From webapp: passport_expiry
        "input[name='dateOfExpiration']",
        FieldType.DATE,
    ),
    FieldMapping(
        "a_number",  # From webapp: a_number (alien registration number)
        "input[name='alienNumber']",
        FieldType.TEXT,
    ),
    # Note: Part 4 consent checkboxes require user confirmation
    # and are not auto-populated from extraction.
    # EXCLUDED: Signature fields (Requirements 9.1-9.4)
    # These are marked with is_signature=True and excluded from population
    FieldMapping(
        "client_signature",
        "input[name='clientSignature']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
    FieldMapping(
        "client_signature_date",
        "input[name='clientSignatureDate']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
    FieldMapping(
        "attorney_signature",
        "input[name='attorneySignature']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
    FieldMapping(
        "attorney_signature_date",
        "input[name='attorneySignatureDate']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
]


@dataclass
class FieldMappingConfig:
    """Configuration manager for field mappings.

    Provides methods to retrieve populatable and signature mappings,
    validate extracted data, and get required field IDs.

    Requirements:
    - 3.1: Field mapping configuration
    - 3.2: Validate source fields present in extracted data
    - 3.4: Skip optional fields when data unavailable
    - 3.5: Log warnings for missing required fields
    - 9.1-9.4: Exclude signature fields from population
    """

    mappings: list[FieldMapping] = field(
        default_factory=lambda: list(FORM_FIELD_MAPPINGS)
    )

    def get_populatable_mappings(self) -> list[FieldMapping]:
        """Return non-signature field mappings.

        Requirements: 9.1-9.4 - Exclude signature fields from population.

        Returns:
            List of FieldMapping objects that can be populated.
        """
        return [m for m in self.mappings if not m.is_signature]

    def get_signature_mappings(self) -> list[FieldMapping]:
        """Return signature field mappings for reporting.

        Requirements: 9.4 - Identify signature fields for manual attention.

        Returns:
            List of FieldMapping objects that are signature fields.
        """
        return [m for m in self.mappings if m.is_signature]

    def get_required_fields(self) -> list[str]:
        """Return list of required field IDs excluding signatures.

        Requirements: 3.2 - Validate required source fields.

        Returns:
            List of field_id strings for required non-signature fields.
        """
        return [
            m.field_id
            for m in self.mappings
            if m.required and not m.is_signature
        ]

    def validate_data(
        self,
        extracted_data: dict[str, str | bool | None],
    ) -> list[str]:
        """Validate extracted data against required fields.

        Checks that all required fields are present and not None.
        Logs warnings for missing required field data but does not
        raise exceptions (Requirements 3.5 - continue with available fields).

        Requirements:
        - 3.2: Validate required source fields present
        - 3.5: Log warnings for missing required field data

        Args:
            extracted_data: Dictionary of field_id -> value from extraction.

        Returns:
            List of missing required field IDs (empty if all present).
        """
        missing: list[str] = []
        required_fields = self.get_required_fields()

        for field_id in required_fields:
            if field_id not in extracted_data or extracted_data[field_id] is None:
                missing.append(field_id)

        if missing:
            logger.warning(
                "Missing required field data: %s. Continuing with available fields.",
                ", ".join(missing),
            )

        return missing
