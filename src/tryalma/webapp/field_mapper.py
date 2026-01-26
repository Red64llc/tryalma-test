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
        "email_address": "attorney_email",
        "daytime_telephone": "attorney_phone",
    }

    # Client information (Part 3)
    G28_CLIENT_FIELD_MAP: dict[str, str] = {
        "family_name": "applicant_surname",
        "given_name": "applicant_given_names",
        "alien_registration_number": "a_number",
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
