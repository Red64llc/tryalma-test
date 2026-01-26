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
    FieldMapping(
        "attorney_online_account",
        "input[name='onlineAccountNumber']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_family_name",
        "input[name='familyName']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_given_name",
        "input[name='givenName']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_middle_name",
        "input[name='middleName']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_street_address",
        "input[name='streetAddress']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_apt_ste_flr",
        "input[name='aptSteFlr']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "attorney_city",
        "input[name='city']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_state",
        "select[name='state']",
        FieldType.DROPDOWN,
        required=True,
    ),
    FieldMapping(
        "attorney_zip",
        "input[name='zipCode']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "attorney_country",
        "input[name='country']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_daytime_phone",
        "input[name='daytimePhone']",
        FieldType.TEXT,
        required=True,
        format_pattern="###-###-####",
    ),
    FieldMapping(
        "attorney_mobile_phone",
        "input[name='mobilePhone']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "attorney_email",
        "input[name='email']",
        FieldType.TEXT,
    ),
    # Part 2: Eligibility Information
    FieldMapping(
        "eligibility_is_attorney",
        "input[name='isAttorney']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "eligibility_licensing_authority",
        "input[name='licensingAuthority']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "eligibility_bar_number",
        "input[name='barNumber']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "eligibility_restriction_status",
        "input[name='restrictionStatus']",
        FieldType.RADIO,
    ),
    FieldMapping(
        "eligibility_law_firm",
        "input[name='lawFirmName']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "eligibility_is_accredited",
        "input[name='isAccreditedRep']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "eligibility_org_name",
        "input[name='organizationName']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "eligibility_accreditation_date",
        "input[name='accreditationDate']",
        FieldType.DATE,
    ),
    FieldMapping(
        "eligibility_is_associated",
        "input[name='isAssociated']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "eligibility_is_law_student",
        "input[name='isLawStudent']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "eligibility_student_name",
        "input[name='studentName']",
        FieldType.TEXT,
    ),
    # Part 3: Beneficiary/Passport Information
    FieldMapping(
        "beneficiary_last_name",
        "input[name='lastName']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "beneficiary_first_names",
        "input[name='firstNames']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "beneficiary_middle_names",
        "input[name='middleNames']",
        FieldType.TEXT,
    ),
    FieldMapping(
        "beneficiary_passport_number",
        "input[name='passportNumber']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "beneficiary_country_of_issue",
        "input[name='countryOfIssue']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "beneficiary_nationality",
        "input[name='nationality']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "beneficiary_date_of_birth",
        "input[name='dateOfBirth']",
        FieldType.DATE,
        required=True,
    ),
    FieldMapping(
        "beneficiary_place_of_birth",
        "input[name='placeOfBirth']",
        FieldType.TEXT,
        required=True,
    ),
    FieldMapping(
        "beneficiary_sex",
        "input[name='sex']",
        FieldType.RADIO,
        required=True,
    ),
    FieldMapping(
        "beneficiary_date_of_issue",
        "input[name='dateOfIssue']",
        FieldType.DATE,
        required=True,
    ),
    FieldMapping(
        "beneficiary_date_of_expiration",
        "input[name='dateOfExpiration']",
        FieldType.DATE,
        required=True,
    ),
    # Part 4: Client Consent (excluding signatures)
    FieldMapping(
        "consent_notices_to_attorney",
        "input[name='noticesToAttorney']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "consent_documents_to_attorney",
        "input[name='documentsToAttorney']",
        FieldType.CHECKBOX,
    ),
    FieldMapping(
        "consent_documents_to_client",
        "input[name='documentsToClient']",
        FieldType.CHECKBOX,
    ),
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
