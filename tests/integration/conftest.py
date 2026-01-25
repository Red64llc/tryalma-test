"""Pytest fixtures for G-28 form parser integration tests.

Task 9.1: Create test fixtures with sample G-28 documents.
Requirements: 1.1, 1.2, 1.5
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from PIL import Image

from tryalma.g28.document_loader import DocumentLoader
from tryalma.g28.exceptions import ExtractionAPIError, NotG28FormError
from tryalma.g28.field_extractor import FieldExtractor
from tryalma.g28.models import (
    AdditionalInfo,
    Address,
    AttorneyInfo,
    ClientInfo,
    ConsentAndSignatures,
    EligibilityInfo,
    ExtractedField,
    G28ExtractionResult,
    G28FormData,
    NoticeOfAppearance,
)
from tryalma.g28.output_formatter import OutputFormatter
from tryalma.g28.parser_service import G28ParserService


# Path to the example G-28 PDF in the docs folder
EXAMPLE_G28_PDF = Path(__file__).parent.parent.parent / "docs" / "Example_G-28.pdf"


@pytest.fixture
def example_g28_pdf_path() -> Path:
    """Return path to the example G-28 PDF document.
    
    Task 9.1: Use example form from docs/Example_G-28.pdf as primary fixture.
    """
    assert EXAMPLE_G28_PDF.exists(), f"Example G-28 PDF not found at {EXAMPLE_G28_PDF}"
    return EXAMPLE_G28_PDF


@pytest.fixture
def example_g28_pdf_bytes(example_g28_pdf_path: Path) -> bytes:
    """Return bytes of the example G-28 PDF document."""
    return example_g28_pdf_path.read_bytes()


@pytest.fixture
def synthetic_g28_image(tmp_path: Path) -> Path:
    """Create a synthetic test image for G-28 form testing.
    
    Task 9.1: Create synthetic test images with known field values.
    """
    # Create a simple synthetic image (white background)
    img = Image.new("RGB", (800, 1000), color="white")
    image_path = tmp_path / "synthetic_g28.png"
    img.save(image_path)
    return image_path


@pytest.fixture
def synthetic_g28_image_bytes(synthetic_g28_image: Path) -> tuple[bytes, str]:
    """Return bytes and filename for synthetic G-28 image."""
    return synthetic_g28_image.read_bytes(), synthetic_g28_image.name


@pytest.fixture
def non_g28_image(tmp_path: Path) -> Path:
    """Create a non-G28 document image (edge case: wrong form type).
    
    Task 9.1: Create edge case documents (wrong form type).
    """
    # Create a simple image that's not a G-28 form
    img = Image.new("RGB", (400, 400), color="gray")
    image_path = tmp_path / "non_g28_document.png"
    img.save(image_path)
    return image_path


@pytest.fixture
def unsupported_file(tmp_path: Path) -> Path:
    """Create a file with unsupported format.
    
    Task 9.1: Create edge case documents (unsupported format).
    """
    unsupported_path = tmp_path / "document.xyz"
    unsupported_path.write_text("This is not a supported format")
    return unsupported_path


@pytest.fixture
def corrupted_pdf(tmp_path: Path) -> Path:
    """Create a corrupted PDF file.
    
    Task 9.1: Create edge case documents (poor quality/corrupted).
    """
    # Create a file with .pdf extension but invalid content
    corrupted_path = tmp_path / "corrupted.pdf"
    corrupted_path.write_bytes(b"This is not a valid PDF content")
    return corrupted_path


@pytest.fixture
def missing_file_path(tmp_path: Path) -> Path:
    """Return path to a non-existent file."""
    return tmp_path / "non_existent_file.pdf"


@pytest.fixture
def expected_attorney_info() -> dict[str, Any]:
    """Expected attorney information from Example_G-28.pdf.
    
    Based on actual values visible in the example document.
    """
    return {
        "family_name": "Smith",
        "given_name": "Barbara",
        "middle_name": None,
        "street_number_and_name": "545 Bryant Street",
        "city_or_town": "Palo Alto",
        "state": "CA",
        "zip_code": "94301",
        "country": "United States of America",
        "email_address": "immigration@tryalma.ai",
        "fax_number": "1650123456",
        "law_firm_name": "Alma Legal Services PC",
        "bar_number": "12083456",
        "licensing_authority": "State Bar of California",
    }


@pytest.fixture
def expected_client_info() -> dict[str, Any]:
    """Expected client information from Example_G-28.pdf.
    
    Based on actual values visible in the example document.
    """
    return {
        "family_name": "Jonas",
        "given_name": "Joe",
        "middle_name": None,  # N/A on form
        "daytime_telephone": "+61 45453434",
        "email_address": "b.smith_00@test.ai",
        "street_number_and_name": "16 Anytown Street",
        "city_or_town": "Perth",
        "state": "WA",
        "province": "WA",
        "postal_code": "6000",
        "country": "Australia",
    }


@pytest.fixture
def mock_extraction_response() -> G28FormData:
    """Create a mock G28FormData response for testing without API calls.
    
    Represents expected extraction from Example_G-28.pdf.
    """
    return G28FormData(
        source_file="Example_G-28.pdf",
        form_detected=True,
        extraction_timestamp=datetime.now().isoformat(),
        overall_confidence=0.95,
        part1_attorney_info=AttorneyInfo(
            uscis_online_account_number=None,
            family_name=ExtractedField(value="Smith", confidence=0.95),
            given_name=ExtractedField(value="Barbara", confidence=0.95),
            middle_name=None,
            address=Address(
                street_number_and_name="545 Bryant Street",
                apt_ste_flr=None,
                city_or_town="Palo Alto",
                state="CA",
                zip_code="94301",
                province=None,
                postal_code=None,
                country="United States of America",
            ),
            daytime_telephone=None,
            mobile_telephone=None,
            email_address=ExtractedField(value="immigration@tryalma.ai", confidence=0.90),
            fax_number=ExtractedField(value="1650123456", confidence=0.85),
        ),
        part2_eligibility=EligibilityInfo(
            is_attorney=ExtractedField(value=True, confidence=0.95),
            licensing_authority=ExtractedField(value="State Bar of California", confidence=0.90),
            bar_number=ExtractedField(value="12083456", confidence=0.95),
            is_subject_to_disciplinary_order=ExtractedField(value=False, confidence=0.90),
            law_firm_name=ExtractedField(value="Alma Legal Services PC", confidence=0.95),
            is_accredited_representative=ExtractedField(value=False, confidence=0.90),
            recognized_organization_name=None,
            accreditation_date=None,
            is_associated=ExtractedField(value=False, confidence=0.85),
            associated_attorney_name=None,
            is_law_student_or_graduate=ExtractedField(value=False, confidence=0.90),
            law_student_name=None,
        ),
        part3_notice_of_appearance=NoticeOfAppearance(
            agency_uscis=ExtractedField(value=True, confidence=0.95),
            uscis_form_numbers=None,
            agency_ice=ExtractedField(value=False, confidence=0.90),
            ice_matter=None,
            agency_cbp=ExtractedField(value=True, confidence=0.90),
            cbp_matter=ExtractedField(value="I-129 E-3 Application", confidence=0.85),
            receipt_number=None,
            representation_type=ExtractedField(value="Applicant", confidence=0.95),
        ),
        part3_client_info=ClientInfo(
            family_name=ExtractedField(value="Jonas", confidence=0.95),
            given_name=ExtractedField(value="Joe", confidence=0.95),
            middle_name=None,
            entity_name=None,
            entity_signatory_title=None,
            uscis_online_account_number=None,
            alien_registration_number=None,
            daytime_telephone=ExtractedField(value="+61 45453434", confidence=0.90),
            mobile_telephone=None,
            email_address=ExtractedField(value="b.smith_00@test.ai", confidence=0.90),
            mailing_address=Address(
                street_number_and_name="16 Anytown Street",
                apt_ste_flr=None,
                city_or_town="Perth",
                state="WA",
                zip_code=None,
                province="WA",
                postal_code="6000",
                country="Australia",
            ),
        ),
        part4_5_consent_signatures=ConsentAndSignatures(
            send_notices_to_attorney=ExtractedField(value=True, confidence=0.90),
            send_secure_documents_to_attorney=ExtractedField(value=False, confidence=0.85),
            send_i94_to_client=ExtractedField(value=False, confidence=0.85),
            client_signature_present=ExtractedField(value=False, confidence=0.70),
            client_signature_date=None,
            attorney_signature_present=ExtractedField(value=False, confidence=0.70),
            attorney_signature_date=None,
            law_student_signature_date=None,
        ),
        part6_additional_info=AdditionalInfo(
            family_name=ExtractedField(value="Smith", confidence=0.95),
            given_name=ExtractedField(value="Barbara", confidence=0.95),
            middle_name=None,
            entries=[],
        ),
        missing_sections=[],
        uncertain_fields=[],
        validation_warnings=[],
    )


@pytest.fixture
def mock_non_g28_response() -> G28FormData:
    """Create a mock G28FormData response for a non-G28 document."""
    return G28FormData(
        source_file="non_g28.pdf",
        form_detected=False,  # Key: This indicates not a G-28 form
        extraction_timestamp=datetime.now().isoformat(),
        overall_confidence=0.2,
        missing_sections=["part1_attorney_info", "part2_eligibility", "part3"],
        uncertain_fields=[],
        validation_warnings=["Document does not appear to be a G-28 form"],
    )


@pytest.fixture
def mock_vision_extractor(mock_extraction_response: G28FormData):
    """Create a mock VisionExtractor that returns predefined responses.
    
    Used to test parser service without making real API calls.
    """
    mock = MagicMock()
    mock.extract_structured.return_value = mock_extraction_response
    return mock


@pytest.fixture
def mock_vision_extractor_non_g28(mock_non_g28_response: G28FormData):
    """Create a mock VisionExtractor that returns non-G28 response."""
    mock = MagicMock()
    mock.extract_structured.return_value = mock_non_g28_response
    return mock


@pytest.fixture
def mock_vision_extractor_api_error():
    """Create a mock VisionExtractor that raises API errors."""
    mock = MagicMock()
    mock.extract_structured.side_effect = ExtractionAPIError("API connection failed")
    return mock


@pytest.fixture
def document_loader() -> DocumentLoader:
    """Create a real DocumentLoader instance."""
    return DocumentLoader()


@pytest.fixture
def output_formatter() -> OutputFormatter:
    """Create a real OutputFormatter instance."""
    return OutputFormatter()


@pytest.fixture
def parser_service_with_mock(
    document_loader: DocumentLoader,
    mock_vision_extractor,
    output_formatter: OutputFormatter,
) -> G28ParserService:
    """Create a G28ParserService with mocked VisionExtractor.
    
    This allows testing the parser service end-to-end without making
    real API calls to Claude.
    """
    field_extractor = FieldExtractor(
        primary_extractor=mock_vision_extractor,
        confidence_threshold=0.7,
    )
    
    return G28ParserService(
        document_loader=document_loader,
        field_extractor=field_extractor,
        output_formatter=output_formatter,
        confidence_threshold=0.7,
    )


@pytest.fixture
def parser_service_non_g28(
    document_loader: DocumentLoader,
    mock_vision_extractor_non_g28,
    output_formatter: OutputFormatter,
) -> G28ParserService:
    """Create a G28ParserService that returns non-G28 detection."""
    field_extractor = FieldExtractor(
        primary_extractor=mock_vision_extractor_non_g28,
        confidence_threshold=0.7,
    )
    
    return G28ParserService(
        document_loader=document_loader,
        field_extractor=field_extractor,
        output_formatter=output_formatter,
        confidence_threshold=0.7,
    )


@pytest.fixture
def parser_service_api_error(
    document_loader: DocumentLoader,
    mock_vision_extractor_api_error,
    output_formatter: OutputFormatter,
) -> G28ParserService:
    """Create a G28ParserService that simulates API failures."""
    field_extractor = FieldExtractor(
        primary_extractor=mock_vision_extractor_api_error,
        confidence_threshold=0.7,
    )
    
    return G28ParserService(
        document_loader=document_loader,
        field_extractor=field_extractor,
        output_formatter=output_formatter,
        confidence_threshold=0.7,
    )
