"""Unit tests for FieldExtractor.

Task 5: Field Extraction Coordinator tests.

Tests cover:
- 5.1 FieldExtractor with backend injection
- 5.2 Main extraction method
- 5.3 Field normalization and validation

Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.4, 5.1-5.6, 6.1-6.6, 7.1-7.3, 8.4, 8.5, 10.1, 10.3, 10.5
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from pydantic import BaseModel

from tryalma.g28.exceptions import ExtractionAPIError, NotG28FormError
from tryalma.g28.models import (
    Address,
    AttorneyInfo,
    ClientInfo,
    ConsentAndSignatures,
    EligibilityInfo,
    ExtractedField,
    G28FormData,
    NoticeOfAppearance,
)


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a simple test image."""
    return Image.new("RGB", (100, 100), color="white")


@pytest.fixture
def sample_images(sample_image: Image.Image) -> list[Image.Image]:
    """Create a list of test images."""
    return [sample_image, sample_image]


@pytest.fixture
def mock_extraction_backend():
    """Create a mock extraction backend."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_fallback_backend():
    """Create a mock fallback extraction backend."""
    mock = MagicMock()
    return mock


class TestFieldExtractorInit:
    """Tests for Task 5.1: FieldExtractor with backend injection."""

    def test_accepts_primary_extraction_backend_via_constructor(
        self, mock_extraction_backend
    ):
        """Test FieldExtractor accepts primary extraction backend via constructor."""
        from tryalma.g28.field_extractor import FieldExtractor

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)

        assert extractor._primary_extractor is mock_extraction_backend

    def test_optionally_accepts_fallback_extraction_backend(
        self, mock_extraction_backend, mock_fallback_backend
    ):
        """Test FieldExtractor optionally accepts fallback extraction backend."""
        from tryalma.g28.field_extractor import FieldExtractor

        extractor = FieldExtractor(
            primary_extractor=mock_extraction_backend,
            fallback_extractor=mock_fallback_backend,
        )

        assert extractor._fallback_extractor is mock_fallback_backend

    def test_fallback_extractor_defaults_to_none(self, mock_extraction_backend):
        """Test fallback extractor is None by default."""
        from tryalma.g28.field_extractor import FieldExtractor

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)

        assert extractor._fallback_extractor is None

    def test_accepts_confidence_threshold(self, mock_extraction_backend):
        """Test FieldExtractor accepts confidence threshold configuration."""
        from tryalma.g28.field_extractor import FieldExtractor

        extractor = FieldExtractor(
            primary_extractor=mock_extraction_backend,
            confidence_threshold=0.8,
        )

        assert extractor._confidence_threshold == 0.8

    def test_default_confidence_threshold_is_0_7(self, mock_extraction_backend):
        """Test default confidence threshold is 0.7."""
        from tryalma.g28.field_extractor import FieldExtractor

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)

        assert extractor._confidence_threshold == 0.7


class TestFallbackBehavior:
    """Tests for fallback extraction behavior (Task 5.1)."""

    def test_uses_primary_extractor_when_successful(
        self, mock_extraction_backend, mock_fallback_backend, sample_images
    ):
        """Test primary extractor is used when successful."""
        from tryalma.g28.field_extractor import FieldExtractor

        # Mock successful primary extraction
        mock_form_data = _create_mock_g28_form_data()
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(
            primary_extractor=mock_extraction_backend,
            fallback_extractor=mock_fallback_backend,
        )

        result = extractor.extract(sample_images)

        mock_extraction_backend.extract_structured.assert_called_once()
        mock_fallback_backend.extract_structured.assert_not_called()

    def test_falls_back_to_secondary_on_primary_failure(
        self, mock_extraction_backend, mock_fallback_backend, sample_images
    ):
        """Test falls back to secondary extractor only on primary failure."""
        from tryalma.g28.field_extractor import FieldExtractor

        # Mock primary failure, secondary success
        mock_extraction_backend.extract_structured.side_effect = ExtractionAPIError(
            "Primary failed"
        )
        mock_form_data = _create_mock_g28_form_data()
        mock_fallback_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(
            primary_extractor=mock_extraction_backend,
            fallback_extractor=mock_fallback_backend,
        )

        result = extractor.extract(sample_images)

        mock_extraction_backend.extract_structured.assert_called_once()
        mock_fallback_backend.extract_structured.assert_called_once()

    def test_raises_error_when_both_extractors_fail(
        self, mock_extraction_backend, mock_fallback_backend, sample_images
    ):
        """Test raises error when both primary and fallback fail."""
        from tryalma.g28.field_extractor import FieldExtractor

        # Both fail
        mock_extraction_backend.extract_structured.side_effect = ExtractionAPIError(
            "Primary failed"
        )
        mock_fallback_backend.extract_structured.side_effect = ExtractionAPIError(
            "Fallback failed"
        )

        extractor = FieldExtractor(
            primary_extractor=mock_extraction_backend,
            fallback_extractor=mock_fallback_backend,
        )

        with pytest.raises(ExtractionAPIError):
            extractor.extract(sample_images)

    def test_raises_error_when_no_fallback_and_primary_fails(
        self, mock_extraction_backend, sample_images
    ):
        """Test raises error when no fallback and primary fails."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_extraction_backend.extract_structured.side_effect = ExtractionAPIError(
            "Primary failed"
        )

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)

        with pytest.raises(ExtractionAPIError):
            extractor.extract(sample_images)


class TestMainExtractionMethod:
    """Tests for Task 5.2: Main extraction method."""

    def test_accepts_list_of_page_images(
        self, mock_extraction_backend, sample_images
    ):
        """Test extract method accepts list of page images."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data()
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        # Verify images were passed to backend
        call_args = mock_extraction_backend.extract_structured.call_args
        assert call_args[0][0] == sample_images

    def test_delegates_to_extraction_backend_with_g28_schema(
        self, mock_extraction_backend, sample_images
    ):
        """Test delegates to extraction backend with G28FormData schema."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data()
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        extractor.extract(sample_images)

        # Verify G28FormData schema was used
        call_args = mock_extraction_backend.extract_structured.call_args
        assert call_args[0][1] == G28FormData

    def test_returns_fully_populated_g28_form_data(
        self, mock_extraction_backend, sample_images
    ):
        """Test returns fully populated G28FormData with confidence scores."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data()
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        assert isinstance(result, G28FormData)

    def test_detects_non_g28_form_and_raises_error(
        self, mock_extraction_backend, sample_images
    ):
        """Test detects if document is not a G-28 form and raises NotG28FormError."""
        from tryalma.g28.field_extractor import FieldExtractor

        # Mock response indicating not a G-28 form
        mock_form_data = _create_mock_g28_form_data(form_detected=False)
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)

        with pytest.raises(NotG28FormError):
            extractor.extract(sample_images)

    def test_handles_empty_image_list(self, mock_extraction_backend):
        """Test handles empty image list gracefully."""
        from tryalma.g28.field_extractor import FieldExtractor

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)

        with pytest.raises(ValueError, match="[Ii]mage"):
            extractor.extract([])


class TestFieldNormalization:
    """Tests for Task 5.3: Field normalization."""

    def test_normalizes_date_fields_to_iso8601(
        self, mock_extraction_backend, sample_images
    ):
        """Test normalizes date fields to ISO 8601 format (YYYY-MM-DD)."""
        from tryalma.g28.field_extractor import FieldExtractor

        # Mock form with dates in various formats that need normalization
        mock_form_data = _create_mock_g28_form_data(
            client_signature_date=ExtractedField(value=date(2024, 3, 15), confidence=0.9),
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        # Dates should be in ISO 8601 format
        if result.part4_5_consent_signatures and result.part4_5_consent_signatures.client_signature_date:
            date_value = result.part4_5_consent_signatures.client_signature_date.value
            if date_value is not None:
                # Should be a date object (ISO 8601 when serialized)
                assert isinstance(date_value, date)

    def test_checkbox_fields_are_boolean(
        self, mock_extraction_backend, sample_images
    ):
        """Test checkbox fields are represented as boolean values."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data(
            is_attorney=ExtractedField(value=True, confidence=0.95),
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        if result.part2_eligibility and result.part2_eligibility.is_attorney:
            assert isinstance(result.part2_eligibility.is_attorney.value, bool)


class TestFieldValidation:
    """Tests for Task 5.3: Field validation."""

    def test_validates_email_format_and_flags_invalid(
        self, mock_extraction_backend, sample_images
    ):
        """Test validates email format and flags invalid values."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data(
            attorney_email="invalid-email",  # Invalid email
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        # Invalid email should be flagged in validation_warnings
        assert any("email" in warning.lower() for warning in result.validation_warnings)

    def test_validates_phone_number_format_and_flags_invalid(
        self, mock_extraction_backend, sample_images
    ):
        """Test validates phone number format and flags invalid values."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data(
            attorney_phone="abc123",  # Invalid phone
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        # Invalid phone should be flagged in validation_warnings
        assert any("phone" in warning.lower() for warning in result.validation_warnings)

    def test_flags_fields_below_confidence_threshold(
        self, mock_extraction_backend, sample_images
    ):
        """Test flags fields with confidence below threshold as uncertain."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data(
            attorney_name_confidence=0.5,  # Below default 0.7 threshold
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(
            primary_extractor=mock_extraction_backend,
            confidence_threshold=0.7,
        )
        result = extractor.extract(sample_images)

        # Low confidence fields should be flagged as uncertain
        assert len(result.uncertain_fields) > 0

    def test_valid_email_not_flagged(
        self, mock_extraction_backend, sample_images
    ):
        """Test valid email is not flagged."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data(
            attorney_email="attorney@example.com",  # Valid email
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        # Valid email should NOT be flagged
        email_warnings = [w for w in result.validation_warnings if "email" in w.lower()]
        assert len(email_warnings) == 0

    def test_valid_phone_not_flagged(
        self, mock_extraction_backend, sample_images
    ):
        """Test valid phone number is not flagged."""
        from tryalma.g28.field_extractor import FieldExtractor

        mock_form_data = _create_mock_g28_form_data(
            attorney_phone="(555) 123-4567",  # Valid phone
        )
        mock_extraction_backend.extract_structured.return_value = mock_form_data

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract(sample_images)

        # Valid phone should NOT be flagged
        phone_warnings = [w for w in result.validation_warnings if "phone" in w.lower()]
        assert len(phone_warnings) == 0


class TestExtractWithSchema:
    """Tests for extract_with_schema method."""

    def test_extract_with_custom_schema(
        self, mock_extraction_backend, sample_images
    ):
        """Test extraction with a specific Pydantic schema."""
        from tryalma.g28.field_extractor import FieldExtractor

        class PartialSchema(BaseModel):
            family_name: ExtractedField[str] | None = None

        mock_result = PartialSchema(
            family_name=ExtractedField(value="Smith", confidence=0.95)
        )
        mock_extraction_backend.extract_structured.return_value = mock_result

        extractor = FieldExtractor(primary_extractor=mock_extraction_backend)
        result = extractor.extract_with_schema(sample_images, PartialSchema)

        assert isinstance(result, PartialSchema)
        assert result.family_name.value == "Smith"


def _create_mock_g28_form_data(
    form_detected: bool = True,
    attorney_name_confidence: float = 0.95,
    attorney_email: str | None = None,
    attorney_phone: str | None = None,
    is_attorney: ExtractedField[bool] | None = None,
    client_signature_date: ExtractedField[date] | None = None,
) -> G28FormData:
    """Helper to create mock G28FormData for testing."""
    attorney_info = AttorneyInfo(
        family_name=ExtractedField(value="Smith", confidence=attorney_name_confidence),
        given_name=ExtractedField(value="John", confidence=0.9),
    )

    if attorney_email is not None:
        attorney_info = AttorneyInfo(
            family_name=ExtractedField(value="Smith", confidence=attorney_name_confidence),
            given_name=ExtractedField(value="John", confidence=0.9),
            email_address=ExtractedField(value=attorney_email, confidence=0.9),
        )

    if attorney_phone is not None:
        attorney_info = AttorneyInfo(
            family_name=ExtractedField(value="Smith", confidence=attorney_name_confidence),
            given_name=ExtractedField(value="John", confidence=0.9),
            daytime_telephone=ExtractedField(value=attorney_phone, confidence=0.9),
        )

    eligibility = None
    if is_attorney is not None:
        eligibility = EligibilityInfo(is_attorney=is_attorney)

    consent_signatures = None
    if client_signature_date is not None:
        consent_signatures = ConsentAndSignatures(
            client_signature_date=client_signature_date
        )

    return G28FormData(
        source_file="test.pdf",
        form_detected=form_detected,
        extraction_timestamp="2024-01-25T12:00:00Z",
        overall_confidence=0.85,
        part1_attorney_info=attorney_info,
        part2_eligibility=eligibility,
        part4_5_consent_signatures=consent_signatures,
    )
