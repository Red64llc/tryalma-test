"""Unit tests for G28 form data models.

Tests all data models using TDD methodology.
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

from datetime import date
from typing import Literal

import pytest
from pydantic import ValidationError


class TestExtractedField:
    """Test ExtractedField generic wrapper with confidence scoring.

    Task 1.1: Base extracted field model with confidence scoring.
    Requirements: 8.6
    """

    def test_extracted_field_holds_string_value_with_confidence(self):
        """ExtractedField can hold a string value with confidence score."""
        from tryalma.g28.models import ExtractedField

        field = ExtractedField[str](value="John", confidence=0.95)

        assert field.value == "John"
        assert field.confidence == 0.95
        assert field.is_uncertain is False

    def test_extracted_field_holds_bool_value_with_confidence(self):
        """ExtractedField can hold a boolean value."""
        from tryalma.g28.models import ExtractedField

        field = ExtractedField[bool](value=True, confidence=0.85)

        assert field.value is True
        assert field.confidence == 0.85

    def test_extracted_field_holds_date_value(self):
        """ExtractedField can hold a date value."""
        from tryalma.g28.models import ExtractedField

        test_date = date(2024, 1, 15)
        field = ExtractedField[date](value=test_date, confidence=0.90)

        assert field.value == test_date
        assert field.confidence == 0.90

    def test_extracted_field_allows_none_value(self):
        """ExtractedField can have None value for empty/N/A fields."""
        from tryalma.g28.models import ExtractedField

        field = ExtractedField[str](value=None, confidence=0.0)

        assert field.value is None
        assert field.confidence == 0.0

    def test_extracted_field_marks_uncertain_when_below_threshold(self):
        """ExtractedField can be marked as uncertain."""
        from tryalma.g28.models import ExtractedField

        field = ExtractedField[str](value="Smith", confidence=0.5, is_uncertain=True)

        assert field.is_uncertain is True

    def test_extracted_field_confidence_must_be_between_0_and_1(self):
        """Confidence score must be in range [0.0, 1.0]."""
        from tryalma.g28.models import ExtractedField

        with pytest.raises(ValidationError):
            ExtractedField[str](value="Test", confidence=1.5)

        with pytest.raises(ValidationError):
            ExtractedField[str](value="Test", confidence=-0.1)

    def test_extracted_field_is_immutable(self):
        """ExtractedField should be immutable (frozen)."""
        from tryalma.g28.models import ExtractedField

        field = ExtractedField[str](value="Test", confidence=0.9)

        with pytest.raises(ValidationError):
            field.value = "Changed"

    def test_extracted_field_is_json_serializable(self):
        """ExtractedField can be serialized to JSON-compatible dict."""
        from tryalma.g28.models import ExtractedField

        field = ExtractedField[str](value="Smith", confidence=0.95, is_uncertain=False)
        data = field.model_dump()

        assert data == {"value": "Smith", "confidence": 0.95, "is_uncertain": False}


class TestAddress:
    """Test Address model for mailing addresses.

    Task 1.2: Address and contact information models.
    Requirements: 2.3, 5.6
    """

    def test_address_with_us_fields(self):
        """Address supports US address fields."""
        from tryalma.g28.models import Address

        address = Address(
            street_number_and_name="123 Main Street",
            apt_ste_flr="Suite 100",
            city_or_town="New York",
            state="NY",
            zip_code="10001",
            country="USA",
        )

        assert address.street_number_and_name == "123 Main Street"
        assert address.apt_ste_flr == "Suite 100"
        assert address.city_or_town == "New York"
        assert address.state == "NY"
        assert address.zip_code == "10001"
        assert address.country == "USA"

    def test_address_with_international_fields(self):
        """Address supports international fields (province, postal code)."""
        from tryalma.g28.models import Address

        address = Address(
            street_number_and_name="456 Queen Street",
            city_or_town="Toronto",
            province="Ontario",
            postal_code="M5V 2A8",
            country="Canada",
        )

        assert address.province == "Ontario"
        assert address.postal_code == "M5V 2A8"
        assert address.state is None

    def test_address_all_fields_optional(self):
        """All address fields are optional for partial form data."""
        from tryalma.g28.models import Address

        address = Address()

        assert address.street_number_and_name is None
        assert address.apt_ste_flr is None
        assert address.city_or_town is None
        assert address.state is None
        assert address.zip_code is None
        assert address.province is None
        assert address.postal_code is None
        assert address.country is None

    def test_address_is_json_serializable(self):
        """Address can be serialized to JSON."""
        from tryalma.g28.models import Address

        address = Address(city_or_town="Boston", state="MA")
        data = address.model_dump(exclude_none=True)

        assert data == {"city_or_town": "Boston", "state": "MA"}


class TestAttorneyInfo:
    """Test Part 1 Attorney Information model.

    Task 1.3: Part 1 attorney information model.
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """

    def test_attorney_info_with_name_fields(self):
        """AttorneyInfo captures attorney name fields."""
        from tryalma.g28.models import AttorneyInfo, ExtractedField

        attorney = AttorneyInfo(
            family_name=ExtractedField[str](value="Smith", confidence=0.95),
            given_name=ExtractedField[str](value="John", confidence=0.95),
            middle_name=ExtractedField[str](value="Q", confidence=0.90),
        )

        assert attorney.family_name.value == "Smith"
        assert attorney.given_name.value == "John"
        assert attorney.middle_name.value == "Q"

    def test_attorney_info_with_uscis_account_number(self):
        """AttorneyInfo includes USCIS Online Account Number."""
        from tryalma.g28.models import AttorneyInfo, ExtractedField

        attorney = AttorneyInfo(
            uscis_online_account_number=ExtractedField[str](
                value="A123456789", confidence=0.88
            ),
        )

        assert attorney.uscis_online_account_number.value == "A123456789"

    def test_attorney_info_with_contact_fields(self):
        """AttorneyInfo includes contact information."""
        from tryalma.g28.models import AttorneyInfo, ExtractedField

        attorney = AttorneyInfo(
            daytime_telephone=ExtractedField[str](value="555-123-4567", confidence=0.92),
            mobile_telephone=ExtractedField[str](value="555-987-6543", confidence=0.90),
            email_address=ExtractedField[str](value="john@lawfirm.com", confidence=0.95),
            fax_number=ExtractedField[str](value="555-123-4568", confidence=0.85),
        )

        assert attorney.daytime_telephone.value == "555-123-4567"
        assert attorney.mobile_telephone.value == "555-987-6543"
        assert attorney.email_address.value == "john@lawfirm.com"
        assert attorney.fax_number.value == "555-123-4568"

    def test_attorney_info_with_embedded_address(self):
        """AttorneyInfo embeds Address model."""
        from tryalma.g28.models import Address, AttorneyInfo

        address = Address(
            street_number_and_name="100 Law Office Blvd",
            city_or_town="New York",
            state="NY",
            zip_code="10001",
        )
        attorney = AttorneyInfo(address=address)

        assert attorney.address.city_or_town == "New York"

    def test_attorney_info_all_fields_optional(self):
        """All AttorneyInfo fields are optional (empty form)."""
        from tryalma.g28.models import AttorneyInfo

        attorney = AttorneyInfo()

        assert attorney.family_name is None
        assert attorney.uscis_online_account_number is None
        assert attorney.address is None


class TestEligibilityInfo:
    """Test Part 2 Eligibility Information model.

    Task 1.4: Part 2 eligibility information model.
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
    """

    def test_eligibility_info_attorney_checkbox(self):
        """EligibilityInfo captures attorney eligibility checkbox."""
        from tryalma.g28.models import EligibilityInfo, ExtractedField

        eligibility = EligibilityInfo(
            is_attorney=ExtractedField[bool](value=True, confidence=0.98),
        )

        assert eligibility.is_attorney.value is True

    def test_eligibility_info_bar_information(self):
        """EligibilityInfo captures licensing authority and bar number."""
        from tryalma.g28.models import EligibilityInfo, ExtractedField

        eligibility = EligibilityInfo(
            licensing_authority=ExtractedField[str](
                value="State Bar of California", confidence=0.92
            ),
            bar_number=ExtractedField[str](value="123456", confidence=0.95),
        )

        assert eligibility.licensing_authority.value == "State Bar of California"
        assert eligibility.bar_number.value == "123456"

    def test_eligibility_info_disciplinary_status(self):
        """EligibilityInfo captures disciplinary order status."""
        from tryalma.g28.models import EligibilityInfo, ExtractedField

        eligibility = EligibilityInfo(
            is_subject_to_disciplinary_order=ExtractedField[bool](
                value=False, confidence=0.90
            ),
        )

        assert eligibility.is_subject_to_disciplinary_order.value is False

    def test_eligibility_info_law_firm_name(self):
        """EligibilityInfo captures law firm or organization name."""
        from tryalma.g28.models import EligibilityInfo, ExtractedField

        eligibility = EligibilityInfo(
            law_firm_name=ExtractedField[str](
                value="Smith & Associates LLP", confidence=0.94
            ),
        )

        assert eligibility.law_firm_name.value == "Smith & Associates LLP"

    def test_eligibility_info_accredited_representative(self):
        """EligibilityInfo captures accredited representative details."""
        from tryalma.g28.models import EligibilityInfo, ExtractedField

        eligibility = EligibilityInfo(
            is_accredited_representative=ExtractedField[bool](
                value=True, confidence=0.88
            ),
            recognized_organization_name=ExtractedField[str](
                value="Legal Aid Society", confidence=0.90
            ),
            accreditation_date=ExtractedField[date](
                value=date(2023, 6, 15), confidence=0.85
            ),
        )

        assert eligibility.is_accredited_representative.value is True
        assert eligibility.recognized_organization_name.value == "Legal Aid Society"
        assert eligibility.accreditation_date.value == date(2023, 6, 15)

    def test_eligibility_info_association_and_law_student(self):
        """EligibilityInfo captures association and law student checkboxes."""
        from tryalma.g28.models import EligibilityInfo, ExtractedField

        eligibility = EligibilityInfo(
            is_associated=ExtractedField[bool](value=True, confidence=0.92),
            associated_attorney_name=ExtractedField[str](
                value="Jane Doe", confidence=0.88
            ),
            is_law_student_or_graduate=ExtractedField[bool](
                value=False, confidence=0.95
            ),
            law_student_name=ExtractedField[str](value=None, confidence=0.0),
        )

        assert eligibility.is_associated.value is True
        assert eligibility.associated_attorney_name.value == "Jane Doe"
        assert eligibility.is_law_student_or_graduate.value is False


class TestNoticeOfAppearance:
    """Test Part 3 Notice of Appearance model.

    Task 1.5: Part 3 notice of appearance model.
    Requirements: 4.1, 4.2, 4.3, 4.4
    """

    def test_notice_agency_checkboxes(self):
        """NoticeOfAppearance captures agency checkboxes as booleans."""
        from tryalma.g28.models import ExtractedField, NoticeOfAppearance

        notice = NoticeOfAppearance(
            agency_uscis=ExtractedField[bool](value=True, confidence=0.98),
            agency_ice=ExtractedField[bool](value=False, confidence=0.95),
            agency_cbp=ExtractedField[bool](value=False, confidence=0.95),
        )

        assert notice.agency_uscis.value is True
        assert notice.agency_ice.value is False
        assert notice.agency_cbp.value is False

    def test_notice_form_numbers_and_matters(self):
        """NoticeOfAppearance captures form numbers and matter descriptions."""
        from tryalma.g28.models import ExtractedField, NoticeOfAppearance

        notice = NoticeOfAppearance(
            agency_uscis=ExtractedField[bool](value=True, confidence=0.98),
            uscis_form_numbers=ExtractedField[str](value="I-130, I-485", confidence=0.90),
            agency_ice=ExtractedField[bool](value=True, confidence=0.95),
            ice_matter=ExtractedField[str](
                value="Removal proceedings", confidence=0.85
            ),
        )

        assert notice.uscis_form_numbers.value == "I-130, I-485"
        assert notice.ice_matter.value == "Removal proceedings"

    def test_notice_receipt_number(self):
        """NoticeOfAppearance captures receipt number."""
        from tryalma.g28.models import ExtractedField, NoticeOfAppearance

        notice = NoticeOfAppearance(
            receipt_number=ExtractedField[str](value="MSC2190123456", confidence=0.92),
        )

        assert notice.receipt_number.value == "MSC2190123456"

    def test_notice_representation_type_literal(self):
        """NoticeOfAppearance captures representation type as literal enum."""
        from tryalma.g28.models import ExtractedField, NoticeOfAppearance

        # Test valid literal values
        for rep_type in [
            "Applicant",
            "Petitioner",
            "Requestor",
            "Beneficiary/Derivative",
            "Respondent",
        ]:
            notice = NoticeOfAppearance(
                representation_type=ExtractedField[
                    Literal[
                        "Applicant",
                        "Petitioner",
                        "Requestor",
                        "Beneficiary/Derivative",
                        "Respondent",
                    ]
                ](value=rep_type, confidence=0.95),
            )
            assert notice.representation_type.value == rep_type


class TestClientInfo:
    """Test Part 3 Client Information model.

    Task 1.6: Part 3 client information model.
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """

    def test_client_info_name_fields(self):
        """ClientInfo captures client name fields."""
        from tryalma.g28.models import ClientInfo, ExtractedField

        client = ClientInfo(
            family_name=ExtractedField[str](value="Doe", confidence=0.95),
            given_name=ExtractedField[str](value="Jane", confidence=0.95),
            middle_name=ExtractedField[str](value="M", confidence=0.88),
        )

        assert client.family_name.value == "Doe"
        assert client.given_name.value == "Jane"
        assert client.middle_name.value == "M"

    def test_client_info_entity_information(self):
        """ClientInfo captures entity information for organizations."""
        from tryalma.g28.models import ClientInfo, ExtractedField

        client = ClientInfo(
            entity_name=ExtractedField[str](value="Acme Corporation", confidence=0.92),
            entity_signatory_title=ExtractedField[str](value="CEO", confidence=0.88),
        )

        assert client.entity_name.value == "Acme Corporation"
        assert client.entity_signatory_title.value == "CEO"

    def test_client_info_uscis_and_alien_numbers(self):
        """ClientInfo captures USCIS account and A-number."""
        from tryalma.g28.models import ClientInfo, ExtractedField

        client = ClientInfo(
            uscis_online_account_number=ExtractedField[str](
                value="B987654321", confidence=0.90
            ),
            alien_registration_number=ExtractedField[str](
                value="A012345678", confidence=0.95
            ),
        )

        assert client.uscis_online_account_number.value == "B987654321"
        assert client.alien_registration_number.value == "A012345678"

    def test_client_info_contact_information(self):
        """ClientInfo captures client contact details."""
        from tryalma.g28.models import ClientInfo, ExtractedField

        client = ClientInfo(
            daytime_telephone=ExtractedField[str](value="555-111-2222", confidence=0.92),
            mobile_telephone=ExtractedField[str](value="555-333-4444", confidence=0.90),
            email_address=ExtractedField[str](value="jane@email.com", confidence=0.94),
        )

        assert client.daytime_telephone.value == "555-111-2222"
        assert client.mobile_telephone.value == "555-333-4444"
        assert client.email_address.value == "jane@email.com"

    def test_client_info_mailing_address(self):
        """ClientInfo embeds mailing address."""
        from tryalma.g28.models import Address, ClientInfo

        address = Address(
            street_number_and_name="789 Elm Street",
            city_or_town="Chicago",
            state="IL",
            zip_code="60601",
        )
        client = ClientInfo(mailing_address=address)

        assert client.mailing_address.city_or_town == "Chicago"
        assert client.mailing_address.state == "IL"


class TestConsentAndSignatures:
    """Test Parts 4-5 Consent and Signatures model.

    Task 1.7: Parts 4-5 consent and signatures model.
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """

    def test_consent_notice_delivery_preferences(self):
        """ConsentAndSignatures captures notice delivery checkboxes."""
        from tryalma.g28.models import ConsentAndSignatures, ExtractedField

        consent = ConsentAndSignatures(
            send_notices_to_attorney=ExtractedField[bool](value=True, confidence=0.98),
            send_secure_documents_to_attorney=ExtractedField[bool](
                value=False, confidence=0.95
            ),
            send_i94_to_client=ExtractedField[bool](value=True, confidence=0.92),
        )

        assert consent.send_notices_to_attorney.value is True
        assert consent.send_secure_documents_to_attorney.value is False
        assert consent.send_i94_to_client.value is True

    def test_consent_client_signature_presence(self):
        """ConsentAndSignatures detects client signature presence."""
        from tryalma.g28.models import ConsentAndSignatures, ExtractedField

        consent = ConsentAndSignatures(
            client_signature_present=ExtractedField[bool](value=True, confidence=0.85),
        )

        assert consent.client_signature_present.value is True

    def test_consent_signature_dates_iso_format(self):
        """ConsentAndSignatures captures signature dates in ISO 8601 format."""
        from tryalma.g28.models import ConsentAndSignatures, ExtractedField

        consent = ConsentAndSignatures(
            client_signature_date=ExtractedField[date](
                value=date(2024, 1, 15), confidence=0.88
            ),
            attorney_signature_date=ExtractedField[date](
                value=date(2024, 1, 15), confidence=0.90
            ),
        )

        assert consent.client_signature_date.value == date(2024, 1, 15)
        assert consent.attorney_signature_date.value == date(2024, 1, 15)

    def test_consent_attorney_signature_presence(self):
        """ConsentAndSignatures detects attorney signature presence."""
        from tryalma.g28.models import ConsentAndSignatures, ExtractedField

        consent = ConsentAndSignatures(
            attorney_signature_present=ExtractedField[bool](value=True, confidence=0.90),
        )

        assert consent.attorney_signature_present.value is True

    def test_consent_law_student_signature_date(self):
        """ConsentAndSignatures captures law student signature date."""
        from tryalma.g28.models import ConsentAndSignatures, ExtractedField

        consent = ConsentAndSignatures(
            law_student_signature_date=ExtractedField[date](
                value=date(2024, 1, 16), confidence=0.80
            ),
        )

        assert consent.law_student_signature_date.value == date(2024, 1, 16)


class TestAdditionalInfo:
    """Test Part 6 Additional Information model.

    Task 1.8: Part 6 additional information model.
    Requirements: 7.1, 7.2, 7.3
    """

    def test_additional_info_entry_structure(self):
        """AdditionalInfoEntry has page, part, item number, and content."""
        from tryalma.g28.models import AdditionalInfoEntry

        entry = AdditionalInfoEntry(
            page_number=3,
            part_number=1,
            item_number="5.b",
            content="Additional attorney information here",
        )

        assert entry.page_number == 3
        assert entry.part_number == 1
        assert entry.item_number == "5.b"
        assert entry.content == "Additional attorney information here"

    def test_additional_info_name_fields(self):
        """AdditionalInfo captures name fields for Part 6 identification."""
        from tryalma.g28.models import AdditionalInfo, ExtractedField

        additional = AdditionalInfo(
            family_name=ExtractedField[str](value="Smith", confidence=0.92),
            given_name=ExtractedField[str](value="John", confidence=0.92),
            middle_name=ExtractedField[str](value="Q", confidence=0.88),
        )

        assert additional.family_name.value == "Smith"
        assert additional.given_name.value == "John"

    def test_additional_info_entries_list(self):
        """AdditionalInfo supports list of entries."""
        from tryalma.g28.models import AdditionalInfo, AdditionalInfoEntry

        entries = [
            AdditionalInfoEntry(
                page_number=3, part_number=2, item_number="1.c", content="Entry 1"
            ),
            AdditionalInfoEntry(
                page_number=3, part_number=2, item_number="1.d", content="Entry 2"
            ),
        ]
        additional = AdditionalInfo(entries=entries)

        assert len(additional.entries) == 2
        assert additional.entries[0].content == "Entry 1"
        assert additional.entries[1].content == "Entry 2"

    def test_additional_info_empty_entries_by_default(self):
        """AdditionalInfo returns empty collection when Part 6 is absent."""
        from tryalma.g28.models import AdditionalInfo

        additional = AdditionalInfo()

        assert additional.entries == []


class TestG28FormData:
    """Test aggregate G28FormData model.

    Task 1.9: Aggregate G28FormData model.
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
    """

    def test_g28_form_data_metadata_fields(self):
        """G28FormData includes metadata fields."""
        from tryalma.g28.models import G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )

        assert form_data.source_file == "test.pdf"
        assert form_data.form_detected is True
        assert form_data.extraction_timestamp == "2024-01-15T10:30:00Z"
        assert form_data.overall_confidence == 0.92

    def test_g28_form_data_combines_all_parts(self):
        """G28FormData combines all form section models."""
        from tryalma.g28.models import (
            AdditionalInfo,
            AttorneyInfo,
            ClientInfo,
            ConsentAndSignatures,
            EligibilityInfo,
            ExtractedField,
            G28FormData,
            NoticeOfAppearance,
        )

        form_data = G28FormData(
            source_file="form.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95)
            ),
            part2_eligibility=EligibilityInfo(
                is_attorney=ExtractedField[bool](value=True, confidence=0.98)
            ),
            part3_notice_of_appearance=NoticeOfAppearance(
                agency_uscis=ExtractedField[bool](value=True, confidence=0.98)
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField[str](value="Doe", confidence=0.95)
            ),
            part4_5_consent_signatures=ConsentAndSignatures(
                client_signature_present=ExtractedField[bool](
                    value=True, confidence=0.85
                )
            ),
            part6_additional_info=AdditionalInfo(),
        )

        assert form_data.part1_attorney_info.family_name.value == "Smith"
        assert form_data.part2_eligibility.is_attorney.value is True
        assert form_data.part3_notice_of_appearance.agency_uscis.value is True
        assert form_data.part3_client_info.family_name.value == "Doe"
        assert form_data.part4_5_consent_signatures.client_signature_present.value is True
        assert form_data.part6_additional_info.entries == []

    def test_g28_form_data_validation_result_lists(self):
        """G28FormData includes validation result lists."""
        from tryalma.g28.models import G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.80,
            missing_sections=["part6_additional_info"],
            uncertain_fields=["part1_attorney_info.fax_number"],
            validation_warnings=["Email format may be invalid"],
        )

        assert "part6_additional_info" in form_data.missing_sections
        assert "part1_attorney_info.fax_number" in form_data.uncertain_fields
        assert "Email format may be invalid" in form_data.validation_warnings

    def test_g28_form_data_validation_lists_default_empty(self):
        """Validation result lists default to empty."""
        from tryalma.g28.models import G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )

        assert form_data.missing_sections == []
        assert form_data.uncertain_fields == []
        assert form_data.validation_warnings == []

    def test_g28_form_data_to_dict_with_confidence(self):
        """G28FormData.to_dict includes confidence when requested."""
        from tryalma.g28.models import AttorneyInfo, ExtractedField, G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95)
            ),
        )

        result = form_data.to_dict(include_confidence=True)

        assert "overall_confidence" in result
        assert result["overall_confidence"] == 0.90

    def test_g28_form_data_to_dict_organized_by_section(self):
        """G28FormData.to_dict organizes output by form section."""
        from tryalma.g28.models import AttorneyInfo, ExtractedField, G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.90,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField[str](value="Smith", confidence=0.95)
            ),
        )

        result = form_data.to_dict(include_confidence=True)

        assert "part1_attorney_info" in result
        assert "source_file" in result

    def test_g28_form_data_overall_confidence_constrained(self):
        """G28FormData overall_confidence must be in [0.0, 1.0]."""
        from tryalma.g28.models import G28FormData

        with pytest.raises(ValidationError):
            G28FormData(
                source_file="test.pdf",
                extraction_timestamp="2024-01-15T10:30:00Z",
                overall_confidence=1.5,
            )


class TestG28ExtractionResult:
    """Test G28ExtractionResult wrapper model.

    Task 1.10: Extraction result wrapper model.
    Requirements: 9.2, 10.1, 10.2, 10.3, 10.4
    """

    def test_extraction_result_success_with_data(self):
        """G28ExtractionResult wraps successful extraction."""
        from tryalma.g28.models import G28ExtractionResult, G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        result = G28ExtractionResult(
            success=True,
            data=form_data,
            source_file="test.pdf",
        )

        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert result.source_file == "test.pdf"

    def test_extraction_result_failure_with_error(self):
        """G28ExtractionResult wraps failed extraction with error."""
        from tryalma.g28.models import G28ExtractionResult

        result = G28ExtractionResult(
            success=False,
            data=None,
            error="Document is not recognized as a G-28 form",
            error_code="NOT_G28_FORM",
            source_file="unknown.pdf",
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "Document is not recognized as a G-28 form"
        assert result.error_code == "NOT_G28_FORM"

    def test_extraction_result_warnings_list(self):
        """G28ExtractionResult includes warnings for non-fatal issues."""
        from tryalma.g28.models import G28ExtractionResult, G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.70,
        )
        result = G28ExtractionResult(
            success=True,
            data=form_data,
            warnings=["Low confidence on some fields", "Possible poor image quality"],
            source_file="test.pdf",
        )

        assert len(result.warnings) == 2
        assert "Low confidence" in result.warnings[0]

    def test_extraction_result_warnings_default_empty(self):
        """G28ExtractionResult warnings default to empty list."""
        from tryalma.g28.models import G28ExtractionResult

        result = G28ExtractionResult(
            success=False,
            error="Test error",
            source_file="test.pdf",
        )

        assert result.warnings == []

    def test_extraction_result_to_output_json(self):
        """G28ExtractionResult.to_output serializes to JSON."""
        from tryalma.g28.models import G28ExtractionResult, G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        result = G28ExtractionResult(
            success=True,
            data=form_data,
            source_file="test.pdf",
        )

        output = result.to_output(format="json")

        assert isinstance(output, str)
        assert '"success": true' in output or '"success":true' in output

    def test_extraction_result_to_output_yaml(self):
        """G28ExtractionResult.to_output serializes to YAML."""
        from tryalma.g28.models import G28ExtractionResult, G28FormData

        form_data = G28FormData(
            source_file="test.pdf",
            extraction_timestamp="2024-01-15T10:30:00Z",
            overall_confidence=0.92,
        )
        result = G28ExtractionResult(
            success=True,
            data=form_data,
            source_file="test.pdf",
        )

        output = result.to_output(format="yaml")

        assert isinstance(output, str)
        assert "success:" in output or "success :" in output
