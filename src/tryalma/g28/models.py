"""Domain models for G-28 form data extraction.

Task 1: Core Data Models for G-28 Form Parser.
Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.4, 5.1-5.6, 6.1-6.6, 7.1-7.3, 8.1-8.6, 9.2, 10.1-10.4
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Generic, Literal, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ExtractedField(BaseModel, Generic[T]):
    """Generic field wrapper with confidence score.

    Task 1.1: Base extracted field model with confidence scoring.
    Requirements: 8.6

    Attributes:
        value: The extracted field value (can be None for empty/N/A fields)
        confidence: Confidence score in range [0.0, 1.0]
        is_uncertain: True if confidence falls below threshold
    """

    model_config = ConfigDict(frozen=True)

    value: T | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    is_uncertain: bool = False


class Address(BaseModel):
    """Mailing address structure supporting US and international formats.

    Task 1.2: Address and contact information models.
    Requirements: 2.3, 5.6

    Attributes:
        street_number_and_name: Street address
        apt_ste_flr: Apartment/Suite/Floor designation
        city_or_town: City or town name
        state: US state (2-letter code)
        zip_code: US ZIP code
        province: International province
        postal_code: International postal code
        country: Country name
    """

    street_number_and_name: str | None = None
    apt_ste_flr: str | None = None
    city_or_town: str | None = None
    state: str | None = None
    zip_code: str | None = None
    province: str | None = None
    postal_code: str | None = None
    country: str | None = None


class AttorneyInfo(BaseModel):
    """Part 1: Attorney or Accredited Representative Information.

    Task 1.3: Part 1 attorney information model.
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5

    Captures attorney name, USCIS account number, address, and contact details.
    All fields are optional as forms may have partial data.
    """

    uscis_online_account_number: ExtractedField[str] | None = None
    family_name: ExtractedField[str] | None = None
    given_name: ExtractedField[str] | None = None
    middle_name: ExtractedField[str] | None = None
    address: Address | None = None
    daytime_telephone: ExtractedField[str] | None = None
    mobile_telephone: ExtractedField[str] | None = None
    email_address: ExtractedField[str] | None = None
    fax_number: ExtractedField[str] | None = None


class EligibilityInfo(BaseModel):
    """Part 2: Eligibility Information.

    Task 1.4: Part 2 eligibility information model.
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7

    Captures attorney eligibility, licensing, accreditation, and association details.
    """

    is_attorney: ExtractedField[bool] | None = None
    licensing_authority: ExtractedField[str] | None = None
    bar_number: ExtractedField[str] | None = None
    is_subject_to_disciplinary_order: ExtractedField[bool] | None = None
    law_firm_name: ExtractedField[str] | None = None
    is_accredited_representative: ExtractedField[bool] | None = None
    recognized_organization_name: ExtractedField[str] | None = None
    accreditation_date: ExtractedField[date] | None = None
    is_associated: ExtractedField[bool] | None = None
    associated_attorney_name: ExtractedField[str] | None = None
    is_law_student_or_graduate: ExtractedField[bool] | None = None
    law_student_name: ExtractedField[str] | None = None


class NoticeOfAppearance(BaseModel):
    """Part 3: Notice of Appearance details.

    Task 1.5: Part 3 notice of appearance model.
    Requirements: 4.1, 4.2, 4.3, 4.4

    Captures agency selections, form numbers, receipt number, and representation type.
    """

    agency_uscis: ExtractedField[bool] | None = None
    uscis_form_numbers: ExtractedField[str] | None = None
    agency_ice: ExtractedField[bool] | None = None
    ice_matter: ExtractedField[str] | None = None
    agency_cbp: ExtractedField[bool] | None = None
    cbp_matter: ExtractedField[str] | None = None
    receipt_number: ExtractedField[str] | None = None
    representation_type: ExtractedField[
        Literal[
            "Applicant",
            "Petitioner",
            "Requestor",
            "Beneficiary/Derivative",
            "Respondent",
        ]
    ] | None = None


class ClientInfo(BaseModel):
    """Part 3: Client Information.

    Task 1.6: Part 3 client information model.
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

    Captures client name, entity info, identification numbers, contact, and address.
    """

    family_name: ExtractedField[str] | None = None
    given_name: ExtractedField[str] | None = None
    middle_name: ExtractedField[str] | None = None
    entity_name: ExtractedField[str] | None = None
    entity_signatory_title: ExtractedField[str] | None = None
    uscis_online_account_number: ExtractedField[str] | None = None
    alien_registration_number: ExtractedField[str] | None = None
    daytime_telephone: ExtractedField[str] | None = None
    mobile_telephone: ExtractedField[str] | None = None
    email_address: ExtractedField[str] | None = None
    mailing_address: Address | None = None


class ConsentAndSignatures(BaseModel):
    """Parts 4-5: Consent options and signature information.

    Task 1.7: Parts 4-5 consent and signatures model.
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6

    Captures notice delivery preferences and signature presence/dates.
    """

    send_notices_to_attorney: ExtractedField[bool] | None = None
    send_secure_documents_to_attorney: ExtractedField[bool] | None = None
    send_i94_to_client: ExtractedField[bool] | None = None
    client_signature_present: ExtractedField[bool] | None = None
    client_signature_date: ExtractedField[date] | None = None
    attorney_signature_present: ExtractedField[bool] | None = None
    attorney_signature_date: ExtractedField[date] | None = None
    law_student_signature_date: ExtractedField[date] | None = None


class AdditionalInfoEntry(BaseModel):
    """Single additional information entry from Part 6.

    Task 1.8: Part 6 additional information model.
    Requirements: 7.1, 7.2, 7.3

    Attributes:
        page_number: Page number reference
        part_number: Part number reference
        item_number: Item number reference (e.g., "5.b")
        content: Additional information content
    """

    page_number: int | None = None
    part_number: int | None = None
    item_number: str | None = None
    content: str | None = None


class AdditionalInfo(BaseModel):
    """Part 6: Additional Information.

    Task 1.8: Part 6 additional information model.
    Requirements: 7.1, 7.2, 7.3

    Captures name fields for identification and list of additional entries.
    Returns empty collection when Part 6 is absent.
    """

    family_name: ExtractedField[str] | None = None
    given_name: ExtractedField[str] | None = None
    middle_name: ExtractedField[str] | None = None
    entries: list[AdditionalInfoEntry] = Field(default_factory=list)


class G28FormData(BaseModel):
    """Complete G-28 form data structure.

    Task 1.9: Aggregate G28FormData model.
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5

    Combines all part models into a single aggregate root with metadata
    and validation results.
    """

    # Metadata
    source_file: str
    form_detected: bool = True
    extraction_timestamp: str
    overall_confidence: float = Field(ge=0.0, le=1.0)

    # Form sections
    part1_attorney_info: AttorneyInfo | None = None
    part2_eligibility: EligibilityInfo | None = None
    part3_notice_of_appearance: NoticeOfAppearance | None = None
    part3_client_info: ClientInfo | None = None
    part4_5_consent_signatures: ConsentAndSignatures | None = None
    part6_additional_info: AdditionalInfo | None = None

    # Validation results
    missing_sections: list[str] = Field(default_factory=list)
    uncertain_fields: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)

    def to_dict(self, include_confidence: bool = True) -> dict[str, Any]:
        """Serialize to dictionary for JSON output.

        Args:
            include_confidence: If True, include confidence scores and metadata.

        Returns:
            Dictionary representation organized by form section.
        """
        return self.model_dump()


class G28ExtractionResult(BaseModel):
    """Result wrapper for G-28 extraction operation.

    Task 1.10: Extraction result wrapper model.
    Requirements: 9.2, 10.1, 10.2, 10.3, 10.4

    Wraps extraction outcome with success/failure status, data, errors, and warnings.
    """

    success: bool
    data: G28FormData | None = None
    error: str | None = None
    error_code: str | None = None
    warnings: list[str] = Field(default_factory=list)
    source_file: str

    def to_output(self, format: Literal["json", "yaml"] = "json") -> str:
        """Serialize result to specified format.

        Args:
            format: Output format - "json" or "yaml"

        Returns:
            Serialized string in requested format
        """
        data = self.model_dump()
        if format == "yaml":
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        return json.dumps(data, indent=2, default=str)
