"""Field mapper for extracted document data.

Maps extraction results from PassportExtractionService and G28ParserService
to a unified form field schema for the document upload UI.

Task 3.1: Passport field mapping
Task 3.2: G-28 field mapping
Task 3.3: Field merge logic

Requirements: 5.1, 5.2, 5.3, 5.4
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from tryalma.passport.models import PassportData

if TYPE_CHECKING:
    from tryalma.g28.models import G28FormData


@dataclass
class MappedField:
    """Field with value and metadata for form display.

    Attributes:
        field_id: Unique identifier for the form field
        value: The extracted value as a string (or None if not available)
        confidence: Extraction confidence score (0.0-1.0) or None
        source: Origin of the data ("passport" or "g28")
        auto_populated: True if automatically filled from extraction
    """

    field_id: str
    value: str | None
    confidence: float | None
    source: str
    auto_populated: bool


class FieldMapper:
    """Maps extraction results to form fields.

    Converts PassportData and G28FormData into a unified dictionary
    of MappedField objects keyed by form field ID.
    """

    # Passport field mappings: source field -> form field ID
    PASSPORT_FIELD_MAP: dict[str, str] = {
        "surname": "applicant_surname",
        "given_names": "applicant_given_names",
        "date_of_birth": "applicant_dob",
        "passport_number": "passport_number",
        "nationality": "nationality",
        "expiry_date": "passport_expiry",
        "sex": "applicant_sex",
    }

    # G-28 field mappings: (section, source field) -> form field ID
    # Attorney information (Part 1)
    G28_ATTORNEY_FIELD_MAP: dict[str, str] = {
        "family_name": "attorney_surname",
        "given_name": "attorney_given_names",
        "middle_name": "attorney_middle_name",
        "email_address": "attorney_email",
        "daytime_telephone": "attorney_phone",
        "mobile_telephone": "attorney_mobile_phone",
        "fax_number": "attorney_fax",
    }

    # Attorney address (Part 1) - nested in address object
    G28_ATTORNEY_ADDRESS_MAP: dict[str, str] = {
        "street_number_and_name": "attorney_street_address",
        "apt_ste_flr": "attorney_apartment",
        "city_or_town": "attorney_city",
        "state": "attorney_state",
        "zip_code": "attorney_zip_code",
        "country": "attorney_country",
    }

    # Eligibility information (Part 2)
    G28_ELIGIBILITY_FIELD_MAP: dict[str, str] = {
        "is_attorney": "is_attorney_eligible",
        "licensing_authority": "licensing_authority",
        "bar_number": "bar_number",
        "is_subject_to_disciplinary_order": "is_subject_to_order",
        "law_firm_name": "law_firm_name",
        "is_accredited_representative": "is_accredited_rep",
        "recognized_organization_name": "recognized_org_name",
        "accreditation_date": "accreditation_date",
        "is_associated": "is_associated_attorney",
        "associated_attorney_name": "associated_attorney_name",
        "is_law_student_or_graduate": "is_law_student",
        "law_student_name": "law_student_name",
    }

    # Notice of appearance (Part 3)
    G28_NOTICE_FIELD_MAP: dict[str, str] = {
        "agency_uscis": "agency_uscis",
        "uscis_form_numbers": "uscis_form_numbers",
        "agency_ice": "agency_ice",
        "ice_matter": "ice_matter",
        "agency_cbp": "agency_cbp",
        "cbp_matter": "cbp_matter",
        "receipt_number": "receipt_number",
        "representation_type": "representation_type",
    }

    # Client information (Part 3)
    G28_CLIENT_FIELD_MAP: dict[str, str] = {
        "family_name": "applicant_surname",
        "given_name": "applicant_given_names",
        "middle_name": "applicant_middle_name",
        "alien_registration_number": "a_number",
        "daytime_telephone": "client_phone",
        "mobile_telephone": "client_mobile_phone",
        "email_address": "client_email",
    }

    # Client address (Part 3) - nested in mailing_address object
    G28_CLIENT_ADDRESS_MAP: dict[str, str] = {
        "street_number_and_name": "client_street_address",
        "apt_ste_flr": "client_apartment",
        "city_or_town": "client_city",
        "state": "client_state",
        "zip_code": "client_zip_code",
        "province": "client_province",
        "postal_code": "client_postal_code",
        "country": "client_country",
    }

    # Consent options (Part 4)
    G28_CONSENT_FIELD_MAP: dict[str, str] = {
        "send_notices_to_attorney": "send_notices_to_attorney",
        "send_secure_documents_to_attorney": "send_documents_to_attorney",
        "send_i94_to_client": "send_i94_to_client",
    }

    def map_passport_data(self, data: PassportData) -> dict[str, MappedField]:
        """Map PassportData to form fields.

        Args:
            data: Extracted passport data from PassportExtractionService

        Returns:
            Dictionary of field_id -> MappedField
        """
        result: dict[str, MappedField] = {}
        confidence = data.confidence

        for source_field, target_field in self.PASSPORT_FIELD_MAP.items():
            raw_value = getattr(data, source_field)

            # Convert date objects to ISO format strings
            if isinstance(raw_value, date):
                value = raw_value.isoformat()
            else:
                value = raw_value

            result[target_field] = MappedField(
                field_id=target_field,
                value=value,
                confidence=confidence,
                source="passport",
                auto_populated=True,
            )

        return result

    def map_g28_data(self, data: "G28FormData") -> dict[str, MappedField]:
        """Map G28FormData to form fields.

        Args:
            data: Extracted G-28 data from G28ParserService

        Returns:
            Dictionary of field_id -> MappedField
        """
        result: dict[str, MappedField] = {}

        # Map attorney information (Part 1)
        attorney_info = data.part1_attorney_info
        for source_field, target_field in self.G28_ATTORNEY_FIELD_MAP.items():
            value, confidence = self._extract_g28_field_value(attorney_info, source_field)
            result[target_field] = MappedField(
                field_id=target_field,
                value=value,
                confidence=confidence,
                source="g28",
                auto_populated=True,
            )

        # Map attorney address (Part 1)
        if attorney_info and attorney_info.address:
            for source_field, target_field in self.G28_ATTORNEY_ADDRESS_MAP.items():
                value = getattr(attorney_info.address, source_field, None)
                result[target_field] = MappedField(
                    field_id=target_field,
                    value=value,
                    confidence=1.0 if value else None,
                    source="g28",
                    auto_populated=True,
                )

        # Map eligibility information (Part 2)
        eligibility_info = data.part2_eligibility
        for source_field, target_field in self.G28_ELIGIBILITY_FIELD_MAP.items():
            value, confidence = self._extract_g28_field_value(eligibility_info, source_field)
            # Convert boolean to string for checkboxes, dates to ISO format
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, date):
                value = value.isoformat()
            result[target_field] = MappedField(
                field_id=target_field,
                value=value,
                confidence=confidence,
                source="g28",
                auto_populated=True,
            )

        # Map notice of appearance (Part 3)
        notice_info = data.part3_notice_of_appearance
        for source_field, target_field in self.G28_NOTICE_FIELD_MAP.items():
            value, confidence = self._extract_g28_field_value(notice_info, source_field)
            if isinstance(value, bool):
                value = str(value).lower()
            result[target_field] = MappedField(
                field_id=target_field,
                value=value,
                confidence=confidence,
                source="g28",
                auto_populated=True,
            )

        # Map client information (Part 3)
        client_info = data.part3_client_info
        for source_field, target_field in self.G28_CLIENT_FIELD_MAP.items():
            value, confidence = self._extract_g28_field_value(client_info, source_field)
            result[target_field] = MappedField(
                field_id=target_field,
                value=value,
                confidence=confidence,
                source="g28",
                auto_populated=True,
            )

        # Map client address (Part 3)
        if client_info and client_info.mailing_address:
            for source_field, target_field in self.G28_CLIENT_ADDRESS_MAP.items():
                value = getattr(client_info.mailing_address, source_field, None)
                result[target_field] = MappedField(
                    field_id=target_field,
                    value=value,
                    confidence=1.0 if value else None,
                    source="g28",
                    auto_populated=True,
                )

        # Map consent options (Part 4)
        consent_info = data.part4_5_consent_signatures
        for source_field, target_field in self.G28_CONSENT_FIELD_MAP.items():
            value, confidence = self._extract_g28_field_value(consent_info, source_field)
            if isinstance(value, bool):
                value = str(value).lower()
            result[target_field] = MappedField(
                field_id=target_field,
                value=value,
                confidence=confidence,
                source="g28",
                auto_populated=True,
            )

        return result

    def _extract_g28_field_value(
        self, section: object | None, field_name: str
    ) -> tuple[str | None, float | None]:
        """Extract value and confidence from a G-28 ExtractedField.

        Args:
            section: AttorneyInfo or ClientInfo section (or None)
            field_name: Name of the field to extract

        Returns:
            Tuple of (value, confidence), both may be None
        """
        if section is None:
            return None, None

        extracted_field = getattr(section, field_name, None)
        if extracted_field is None:
            return None, None

        # ExtractedField has value and confidence attributes
        return extracted_field.value, extracted_field.confidence

    def merge_fields(
        self,
        existing: dict[str, MappedField],
        new: dict[str, MappedField],
    ) -> dict[str, MappedField]:
        """Merge new fields into existing without overwriting populated values.

        Implements Requirement 5.4: when multiple documents are processed,
        merge extracted data into the form without overwriting previously
        populated fields.

        Args:
            existing: Current form fields (from previous extractions)
            new: New extracted fields to merge

        Returns:
            Merged field dictionary (new dictionary, inputs not modified)
        """
        # Start with a copy of existing fields
        result = dict(existing)

        # Add or update fields from new extraction
        for field_id, new_field in new.items():
            if field_id not in result:
                # New field - add it
                result[field_id] = new_field
            else:
                # Field exists - only update if existing value is None
                existing_field = result[field_id]
                if existing_field.value is None and new_field.value is not None:
                    result[field_id] = new_field
                # Otherwise keep existing value (first-in wins)

        return result
