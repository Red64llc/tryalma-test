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
    # ==========================================================================
    # Part 1: Attorney/Representative Information
    # ==========================================================================
    FieldMapping(
        "attorney_surname",
        "input[name='family-name']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_given_names",
        "input[name='given-name']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_middle_name",
        "input[name='middle-name']",
        FieldType.TEXT,
    ),
    # Attorney Address
    FieldMapping(
        "attorney_street_address",
        "input[name='street-address']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_apartment",
        "input[name='apartment']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_city",
        "input[name='city']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_state",
        "select[name='state']",
        FieldType.DROPDOWN,
    ),
    FieldMapping(
        "attorney_zip_code",
        "input[name='zip-code']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_country",
        "input[name='country']",
        FieldType.TEXT,
    ),
    # Attorney Contact
    FieldMapping(
        "attorney_phone",
        "input[name='daytime-phone']",
        FieldType.TEXT,
        format_pattern="###-###-####",
    ),
    FieldMapping(
        "attorney_mobile_phone",
        "input[name='mobile-phone']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_email",
        "input[name='email']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_fax",
        "input[name='fax-number']",
        FieldType.TEXT,
    ),
    # ==========================================================================
    # Part 2: Eligibility Information
    # ==========================================================================
    FieldMapping(
        "is_attorney_eligible",
        "input[name='attorney-eligible']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "licensing_authority",
        "input[name='licensing-authority']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "bar_number",
        "input[name='bar-number']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "is_subject_to_order",
        "input[name='subject-to-order']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "law_firm_name",
        "input[name='law-firm-name']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "is_accredited_rep",
        "input[name='accredited-rep']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "recognized_org_name",
        "input[name='organization-name']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "accreditation_date",
        "input[name='accreditation-date']",
        FieldType.DATE,
    ),
    FieldMapping(
        "is_associated_attorney",
        "input[name='associated-attorney']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "associated_attorney_name",
        "input[name='associated-attorney-name']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "is_law_student",
        "input[name='law-student']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "law_student_name",
        "input[name='law-student-name']",
        FieldType.TEXT,
    ),
    # ==========================================================================
    # Part 3: Beneficiary/Applicant Information (from passport and G-28)
    # ==========================================================================
    FieldMapping(
        "applicant_surname",
        "input[name='passport-surname']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "applicant_given_names",
        "input[name='passport-given-names']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "applicant_middle_name",
        "input[name='passport-middle-name']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "passport_number",
        "input[name='passport-number']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "nationality",
        "input[name='passport-nationality']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "applicant_dob",
        "input[name='passport-dob']",
        FieldType.DATE,
    ),
    FieldMapping(
        "applicant_sex",
        "select[name='passport-sex']",
        FieldType.DROPDOWN,
    ),
    FieldMapping(
        "passport_expiry",
        "input[name='passport-expiry-date']",
        FieldType.DATE,
    ),
    FieldMapping(
        "a_number",
        "input[name='alien-number']",
        FieldType.TEXT,
    ),
    # Client contact and address (from G-28)
    FieldMapping(
        "client_phone",
        "input[name='client-phone']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_mobile_phone",
        "input[name='client-mobile-phone']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_email",
        "input[name='client-email']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_street_address",
        "input[name='client-street-address']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_apartment",
        "input[name='client-apartment']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_city",
        "input[name='client-city']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_state",
        "select[name='client-state']",
        FieldType.DROPDOWN,
    ),
    FieldMapping(
        "client_zip_code",
        "input[name='client-zip-code']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_province",
        "input[name='client-province']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_postal_code",
        "input[name='client-postal-code']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "client_country",
        "input[name='client-country']",
        FieldType.TEXT,
    ),
    # ==========================================================================
    # Part 4: Consent Options
    # ==========================================================================
    FieldMapping(
        "send_notices_to_attorney",
        "input[name='notices-to-attorney']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "send_documents_to_attorney",
        "input[name='documents-to-attorney']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "send_i94_to_client",
        "input[name='i94-to-client']",
        FieldType.CHECKBOX,
    ),
    # ==========================================================================
    # EXCLUDED: Signature fields (Requirements 9.1-9.4)
    # These are marked with is_signature=True and excluded from population
    # ==========================================================================
    FieldMapping(
        "client_signature",
        "input[name='client-signature']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
    FieldMapping(
        "client_signature_date",
        "input[name='client-signature-date']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
    FieldMapping(
        "attorney_signature",
        "input[name='attorney-signature']",
        FieldType.SIGNATURE,
        is_signature=True,
    ),
    FieldMapping(
        "attorney_signature_date",
        "input[name='attorney-signature-date']",
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
