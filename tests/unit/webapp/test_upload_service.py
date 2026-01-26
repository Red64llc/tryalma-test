"""Tests for upload service orchestration.

TDD: RED phase - These tests define expected behavior for the UploadService.

Task 4.1: Upload service for document processing orchestration.
Requirements: 3.1, 3.2, 4.1, 4.2
"""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from werkzeug.datastructures import FileStorage

from tryalma.passport.models import ExtractionResult, PassportData
from tryalma.g28.models import (
    G28ExtractionResult,
    G28FormData,
    AttorneyInfo,
    ClientInfo,
    ExtractedField,
)
from tryalma.webapp.exceptions import (
    DocumentTypeRequiredError,
    ExtractionFailedError,
    UnsupportedFormatError,
)
from tryalma.webapp.field_mapper import FieldMapper, MappedField
from tryalma.webapp.validators import FileValidator, ValidationResult


class TestUploadServiceInit:
    """Tests for UploadService initialization."""

    def test_upload_service_requires_passport_service(self):
        """UploadService should accept PassportExtractionService."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        service = UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

        assert service._passport_service is passport_service

    def test_upload_service_requires_g28_service(self):
        """UploadService should accept G28ParserService."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        service = UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

        assert service._g28_service is g28_service

    def test_upload_service_requires_file_validator(self):
        """UploadService should accept FileValidator."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        service = UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

        assert service._file_validator is file_validator

    def test_upload_service_requires_field_mapper(self):
        """UploadService should accept FieldMapper."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        service = UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

        assert service._field_mapper is field_mapper


class TestProcessUploadValidation:
    """Tests for process_upload file validation."""

    @pytest.fixture
    def upload_service(self):
        """Create UploadService with mocked dependencies."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        return UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

    def test_process_upload_rejects_unsupported_format(self, upload_service):
        """Should raise UnsupportedFormatError for unsupported file types."""
        # Create a text file (unsupported)
        file_content = b"This is a text file"
        file = FileStorage(
            stream=BytesIO(file_content),
            filename="test.txt",
            content_type="text/plain",
        )

        with pytest.raises(UnsupportedFormatError):
            upload_service.process_upload(file, "passport")

    def test_process_upload_rejects_empty_file(self, upload_service):
        """Should raise FileValidationError for empty files."""
        from tryalma.webapp.exceptions import FileValidationError

        file = FileStorage(
            stream=BytesIO(b""),
            filename="test.pdf",
            content_type="application/pdf",
        )

        with pytest.raises(FileValidationError):
            upload_service.process_upload(file, "passport")


class TestProcessUploadPassport:
    """Tests for process_upload with passport documents."""

    @pytest.fixture
    def mock_passport_service(self):
        """Create mock PassportExtractionService."""
        service = MagicMock()
        return service

    @pytest.fixture
    def upload_service(self, mock_passport_service):
        """Create UploadService with mocked passport service."""
        from tryalma.webapp.upload_service import UploadService

        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        return UploadService(
            passport_service=mock_passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

    def test_process_upload_routes_passport_to_passport_service(
        self, upload_service, mock_passport_service
    ):
        """Passport documents should be routed to PassportExtractionService."""
        from datetime import date

        # Create PDF file (magic bytes)
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Mock successful extraction
        passport_data = PassportData(
            source_file=Path("/tmp/test.pdf"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=date(1990, 1, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 1, 14),
            confidence=0.95,
        )
        mock_passport_service.extract_single.return_value = ExtractionResult(
            success=True,
            data=passport_data,
            error=None,
            source_file=Path("/tmp/test.pdf"),
        )

        result = upload_service.process_upload(file, "passport")

        mock_passport_service.extract_single.assert_called_once()
        assert result.success is True

    def test_process_upload_passport_returns_upload_result(
        self, upload_service, mock_passport_service
    ):
        """process_upload should return UploadResult with extracted data."""
        from datetime import date
        from tryalma.webapp.upload_service import UploadResult

        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        passport_data = PassportData(
            source_file=Path("/tmp/test.pdf"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=date(1990, 1, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 1, 14),
            confidence=0.95,
        )
        mock_passport_service.extract_single.return_value = ExtractionResult(
            success=True,
            data=passport_data,
            error=None,
            source_file=Path("/tmp/test.pdf"),
        )

        result = upload_service.process_upload(file, "passport")

        assert isinstance(result, UploadResult)
        assert result.success is True
        assert result.document_type == "passport"
        assert "applicant_surname" in result.form_fields

    def test_process_upload_passport_maps_fields_correctly(
        self, upload_service, mock_passport_service
    ):
        """Extracted passport data should be mapped to form fields."""
        from datetime import date

        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        passport_data = PassportData(
            source_file=Path("/tmp/test.pdf"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=date(1990, 1, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 1, 14),
            confidence=0.95,
        )
        mock_passport_service.extract_single.return_value = ExtractionResult(
            success=True,
            data=passport_data,
            error=None,
            source_file=Path("/tmp/test.pdf"),
        )

        result = upload_service.process_upload(file, "passport")

        assert result.form_fields["applicant_surname"].value == "SMITH"
        assert result.form_fields["applicant_given_names"].value == "JOHN"
        assert result.form_fields["passport_number"].value == "123456789"


class TestProcessUploadG28:
    """Tests for process_upload with G-28 documents."""

    @pytest.fixture
    def mock_g28_service(self):
        """Create mock G28ParserService."""
        service = MagicMock()
        return service

    @pytest.fixture
    def upload_service(self, mock_g28_service):
        """Create UploadService with mocked G28 service."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        return UploadService(
            passport_service=passport_service,
            g28_service=mock_g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

    def test_process_upload_routes_g28_to_g28_service(
        self, upload_service, mock_g28_service
    ):
        """G-28 documents should be routed to G28ParserService."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="g28.pdf",
            content_type="application/pdf",
        )

        # Mock successful extraction
        g28_data = G28FormData(
            source_file="g28.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-01T00:00:00",
            overall_confidence=0.9,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.95),
                given_name=ExtractedField(value="SARAH", confidence=0.95),
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField(value="DOE", confidence=0.9),
                given_name=ExtractedField(value="JANE", confidence=0.9),
            ),
        )
        mock_g28_service.parse_bytes.return_value = G28ExtractionResult(
            success=True,
            data=g28_data,
            source_file="g28.pdf",
        )

        result = upload_service.process_upload(file, "g28")

        mock_g28_service.parse_bytes.assert_called_once()
        assert result.success is True

    def test_process_upload_g28_returns_upload_result(
        self, upload_service, mock_g28_service
    ):
        """process_upload should return UploadResult with G-28 extracted data."""
        from tryalma.webapp.upload_service import UploadResult

        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="g28.pdf",
            content_type="application/pdf",
        )

        g28_data = G28FormData(
            source_file="g28.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-01T00:00:00",
            overall_confidence=0.9,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.95),
                given_name=ExtractedField(value="SARAH", confidence=0.95),
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField(value="DOE", confidence=0.9),
                given_name=ExtractedField(value="JANE", confidence=0.9),
            ),
        )
        mock_g28_service.parse_bytes.return_value = G28ExtractionResult(
            success=True,
            data=g28_data,
            source_file="g28.pdf",
        )

        result = upload_service.process_upload(file, "g28")

        assert isinstance(result, UploadResult)
        assert result.success is True
        assert result.document_type == "g28"
        assert "attorney_surname" in result.form_fields

    def test_process_upload_g28_maps_fields_correctly(
        self, upload_service, mock_g28_service
    ):
        """Extracted G-28 data should be mapped to form fields."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="g28.pdf",
            content_type="application/pdf",
        )

        g28_data = G28FormData(
            source_file="g28.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-01T00:00:00",
            overall_confidence=0.9,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.95),
                given_name=ExtractedField(value="SARAH", confidence=0.95),
                email_address=ExtractedField(value="sarah@law.com", confidence=0.9),
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField(value="DOE", confidence=0.9),
                given_name=ExtractedField(value="JANE", confidence=0.9),
            ),
        )
        mock_g28_service.parse_bytes.return_value = G28ExtractionResult(
            success=True,
            data=g28_data,
            source_file="g28.pdf",
        )

        result = upload_service.process_upload(file, "g28")

        assert result.form_fields["attorney_surname"].value == "JONES"
        assert result.form_fields["attorney_given_names"].value == "SARAH"
        assert result.form_fields["attorney_email"].value == "sarah@law.com"


class TestProcessUploadUnifiedResponse:
    """Tests for unified response format."""

    @pytest.fixture
    def upload_service(self):
        """Create UploadService with mocked services."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        return UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

    def test_upload_result_has_success_field(self, upload_service):
        """UploadResult should have success boolean field."""
        from tryalma.webapp.upload_service import UploadResult

        result = UploadResult(
            success=True,
            document_type="passport",
            source_filename="test.pdf",
            form_fields={},
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
        )

        assert hasattr(result, "success")
        assert isinstance(result.success, bool)

    def test_upload_result_has_document_type(self, upload_service):
        """UploadResult should have document_type field."""
        from tryalma.webapp.upload_service import UploadResult

        result = UploadResult(
            success=True,
            document_type="g28",
            source_filename="test.pdf",
            form_fields={},
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
        )

        assert result.document_type == "g28"

    def test_upload_result_has_form_fields(self, upload_service):
        """UploadResult should have form_fields dictionary."""
        from tryalma.webapp.upload_service import UploadResult

        result = UploadResult(
            success=True,
            document_type="passport",
            source_filename="test.pdf",
            form_fields={
                "applicant_surname": MappedField(
                    field_id="applicant_surname",
                    value="SMITH",
                    confidence=0.95,
                    source="passport",
                    auto_populated=True,
                ),
            },
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
        )

        assert "applicant_surname" in result.form_fields

    def test_upload_result_has_warnings(self, upload_service):
        """UploadResult should have warnings list."""
        from tryalma.webapp.upload_service import UploadResult

        result = UploadResult(
            success=True,
            document_type="passport",
            source_filename="test.pdf",
            form_fields={},
            extracted_fields={},
            warnings=["Low confidence on date of birth"],
            partially_extracted=[],
        )

        assert len(result.warnings) == 1

    def test_upload_result_to_json_dict(self, upload_service):
        """UploadResult should be serializable to JSON-compatible dict."""
        from tryalma.webapp.upload_service import UploadResult

        result = UploadResult(
            success=True,
            document_type="passport",
            source_filename="test.pdf",
            form_fields={
                "applicant_surname": MappedField(
                    field_id="applicant_surname",
                    value="SMITH",
                    confidence=0.95,
                    source="passport",
                    auto_populated=True,
                ),
            },
            extracted_fields={
                "surname": {"value": "SMITH", "confidence": 0.95},
            },
            warnings=[],
            partially_extracted=[],
        )

        json_dict = result.to_json_dict()

        assert json_dict["success"] is True
        assert json_dict["document_type"] == "passport"
        assert "form_fields" in json_dict
        assert json_dict["form_fields"]["applicant_surname"] == "SMITH"


class TestMergeExtractionResults:
    """Tests for merge_extraction_results functionality."""

    @pytest.fixture
    def upload_service(self):
        """Create UploadService with dependencies."""
        from tryalma.webapp.upload_service import UploadService

        passport_service = MagicMock()
        g28_service = MagicMock()
        file_validator = FileValidator()
        field_mapper = FieldMapper()

        return UploadService(
            passport_service=passport_service,
            g28_service=g28_service,
            file_validator=file_validator,
            field_mapper=field_mapper,
        )

    def test_merge_adds_new_fields(self, upload_service):
        """New fields from extraction should be added to existing."""
        from tryalma.webapp.upload_service import UploadResult

        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.95,
                source="passport",
                auto_populated=True,
            ),
        }

        new_result = UploadResult(
            success=True,
            document_type="g28",
            source_filename="g28.pdf",
            form_fields={
                "attorney_surname": MappedField(
                    field_id="attorney_surname",
                    value="JONES",
                    confidence=0.9,
                    source="g28",
                    auto_populated=True,
                ),
            },
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
        )

        merged = upload_service.merge_extraction_results(existing, new_result)

        assert "applicant_surname" in merged
        assert "attorney_surname" in merged

    def test_merge_preserves_existing_values(self, upload_service):
        """Existing non-null values should not be overwritten."""
        from tryalma.webapp.upload_service import UploadResult

        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.95,
                source="passport",
                auto_populated=True,
            ),
        }

        new_result = UploadResult(
            success=True,
            document_type="g28",
            source_filename="g28.pdf",
            form_fields={
                "applicant_surname": MappedField(
                    field_id="applicant_surname",
                    value="DOE",  # Different value from G-28
                    confidence=0.9,
                    source="g28",
                    auto_populated=True,
                ),
            },
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
        )

        merged = upload_service.merge_extraction_results(existing, new_result)

        # Original value should be preserved (first-in wins)
        assert merged["applicant_surname"].value == "SMITH"

    def test_merge_fills_none_values(self, upload_service):
        """None values in existing should be filled by new extraction."""
        from tryalma.webapp.upload_service import UploadResult

        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value=None,  # Empty from previous extraction
                confidence=None,
                source="passport",
                auto_populated=True,
            ),
        }

        new_result = UploadResult(
            success=True,
            document_type="g28",
            source_filename="g28.pdf",
            form_fields={
                "applicant_surname": MappedField(
                    field_id="applicant_surname",
                    value="DOE",
                    confidence=0.9,
                    source="g28",
                    auto_populated=True,
                ),
            },
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
        )

        merged = upload_service.merge_extraction_results(existing, new_result)

        # New value should fill the None
        assert merged["applicant_surname"].value == "DOE"
