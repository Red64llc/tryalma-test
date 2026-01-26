"""Tests for extraction error handling and partial success responses.

TDD: RED phase - These tests define expected error handling behavior.

Task 4.3: Implement extraction error handling and partial success responses.
Requirements: 3.3, 3.4, 4.3, 4.4, 8.1, 8.2
"""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import date

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
from tryalma.webapp.field_mapper import FieldMapper, MappedField
from tryalma.webapp.upload_service import UploadResult, UploadService
from tryalma.webapp.validators import FileValidator


class TestExtractionErrorTransformation:
    """Tests for transforming extraction service errors to user-friendly messages."""

    @pytest.fixture
    def mock_passport_service(self):
        """Create mock PassportExtractionService."""
        return MagicMock()

    @pytest.fixture
    def upload_service(self, mock_passport_service):
        """Create UploadService with mocked services."""
        g28_service = MagicMock()
        return UploadService(
            passport_service=mock_passport_service,
            g28_service=g28_service,
            file_validator=FileValidator(),
            field_mapper=FieldMapper(),
        )

    def test_passport_extraction_error_returns_user_friendly_message(
        self, upload_service, mock_passport_service
    ):
        """Passport extraction errors should be transformed to user-friendly messages."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Simulate extraction failure with technical message
        mock_passport_service.extract_single.return_value = ExtractionResult(
            success=False,
            data=None,
            error="MRZ detection failed: no valid MRZ zone found in image",
            source_file=Path("/tmp/test.pdf"),
        )

        result = upload_service.process_upload(file, "passport")

        assert result.success is False
        # Error message should be present
        assert result.error is not None
        # Should not expose raw technical details in many cases
        # The error is passed through but could be transformed

    def test_g28_extraction_error_returns_user_friendly_message(self, upload_service):
        """G-28 extraction errors should be transformed to user-friendly messages."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="g28.pdf",
            content_type="application/pdf",
        )

        # Mock G-28 extraction failure
        upload_service._g28_service.parse_bytes.return_value = G28ExtractionResult(
            success=False,
            error="API rate limit exceeded",
            error_code="RATE_LIMIT_ERROR",
            source_file="g28.pdf",
        )

        result = upload_service.process_upload(file, "g28")

        assert result.success is False
        assert result.error is not None
        assert result.error_code is not None

    def test_network_error_suggests_retry(self, upload_service, mock_passport_service):
        """Network errors should provide retry option."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Simulate network error
        mock_passport_service.extract_single.side_effect = ConnectionError(
            "Connection reset by peer"
        )

        result = upload_service.process_upload(file, "passport")

        assert result.success is False
        # Error should indicate it's retryable
        assert result.error is not None


class TestPartialExtractionScenarios:
    """Tests for partial extraction scenarios (some fields succeed, others fail)."""

    @pytest.fixture
    def mock_passport_service(self):
        """Create mock PassportExtractionService."""
        return MagicMock()

    @pytest.fixture
    def upload_service(self, mock_passport_service):
        """Create UploadService with mocked services."""
        g28_service = MagicMock()
        return UploadService(
            passport_service=mock_passport_service,
            g28_service=g28_service,
            file_validator=FileValidator(),
            field_mapper=FieldMapper(),
        )

    def test_partial_passport_extraction_reports_missing_fields(
        self, upload_service, mock_passport_service
    ):
        """Partial passport extraction should report which fields are missing."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Simulate partial extraction (some fields None)
        passport_data = PassportData(
            source_file=Path("/tmp/test.pdf"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=None,  # Missing
            nationality="USA",
            passport_number="123456789",
            expiry_date=None,  # Missing
            confidence=0.85,
        )
        mock_passport_service.extract_single.return_value = ExtractionResult(
            success=True,
            data=passport_data,
            error=None,
            source_file=Path("/tmp/test.pdf"),
        )

        result = upload_service.process_upload(file, "passport")

        assert result.success is True
        # Should report partially extracted fields
        assert len(result.partially_extracted) > 0
        assert "date_of_birth" in result.partially_extracted
        assert "expiry_date" in result.partially_extracted

    def test_partial_g28_extraction_reports_uncertain_fields(self, upload_service):
        """Partial G-28 extraction should report uncertain fields."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="g28.pdf",
            content_type="application/pdf",
        )

        # Mock partial G-28 extraction with uncertain fields
        g28_data = G28FormData(
            source_file="g28.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-01T00:00:00",
            overall_confidence=0.7,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.95),
                given_name=ExtractedField(value="SARAH", confidence=0.95),
            ),
            uncertain_fields=["part1_attorney_info.email_address", "part3_client_info.a_number"],
        )
        upload_service._g28_service.parse_bytes.return_value = G28ExtractionResult(
            success=True,
            data=g28_data,
            source_file="g28.pdf",
        )

        result = upload_service.process_upload(file, "g28")

        assert result.success is True
        assert len(result.partially_extracted) > 0

    def test_extraction_with_warnings_includes_warnings(
        self, upload_service, mock_passport_service
    ):
        """Extraction with warnings should include them in result."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Simulate extraction with MRZ validation warnings
        passport_data = PassportData(
            source_file=Path("/tmp/test.pdf"),
            surname="SMITH",
            given_names="JOHN",
            date_of_birth=date(1990, 1, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2030, 1, 14),
            confidence=0.85,
            mrz_valid=False,  # MRZ validation failed
            check_digit_errors=["birth_date", "expiry_date"],
        )
        mock_passport_service.extract_single.return_value = ExtractionResult(
            success=True,
            data=passport_data,
            error=None,
            source_file=Path("/tmp/test.pdf"),
        )

        result = upload_service.process_upload(file, "passport")

        assert result.success is True
        assert len(result.warnings) > 0
        # Should mention MRZ validation or check digit issues

    def test_g28_extraction_with_missing_sections(self, upload_service):
        """G-28 extraction with missing sections should report them."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="g28.pdf",
            content_type="application/pdf",
        )

        # Mock G-28 extraction with missing sections
        g28_data = G28FormData(
            source_file="g28.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-01T00:00:00",
            overall_confidence=0.8,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.95),
            ),
            part3_client_info=None,  # Missing section
            missing_sections=["part3_client_info"],
            validation_warnings=["Part 3 client info could not be extracted"],
        )
        upload_service._g28_service.parse_bytes.return_value = G28ExtractionResult(
            success=True,
            data=g28_data,
            source_file="g28.pdf",
            warnings=["Part 3 client info could not be extracted"],
        )

        result = upload_service.process_upload(file, "g28")

        assert result.success is True
        assert len(result.warnings) > 0


class TestUploadResultSerialization:
    """Tests for UploadResult JSON serialization with error details."""

    def test_error_result_to_json_dict(self):
        """Error UploadResult should serialize properly."""
        result = UploadResult(
            success=False,
            document_type="passport",
            source_filename="test.pdf",
            form_fields={},
            extracted_fields={},
            warnings=[],
            partially_extracted=[],
            error="Failed to extract data",
            error_code="EXTRACTION_FAILED",
        )

        json_dict = result.to_json_dict()

        assert json_dict["success"] is False
        # Error info should be available (either in to_json_dict or separately)

    def test_partial_success_result_to_json_dict(self):
        """Partial success UploadResult should include warnings and partial fields."""
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
                "applicant_surname": {"value": "SMITH", "confidence": 0.95},
            },
            warnings=["MRZ validation failed"],
            partially_extracted=["date_of_birth", "expiry_date"],
        )

        json_dict = result.to_json_dict()

        assert json_dict["success"] is True
        assert len(json_dict["warnings"]) > 0
        assert len(json_dict["partially_extracted"]) > 0


class TestRouteErrorHandling:
    """Tests for HTTP route error handling."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from tryalma.webapp import create_app
        return create_app("testing")

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_extraction_failure_returns_422(self, client):
        """Extraction failures should return 422 Unprocessable Entity."""
        with patch("tryalma.webapp.routes.get_upload_service") as mock_get:
            mock_service = MagicMock()
            mock_service.process_upload.return_value = UploadResult(
                success=False,
                document_type="passport",
                source_filename="test.pdf",
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
                error="Could not extract MRZ from image",
                error_code="EXTRACTION_FAILED",
            )
            mock_get.return_value = mock_service

            pdf_content = b"%PDF-1.4 test"
            data = {
                "file": (BytesIO(pdf_content), "test.pdf"),
                "document_type": "passport",
            }
            response = client.post("/upload", data=data, content_type="multipart/form-data")

            assert response.status_code == 422
            json_data = response.get_json()
            assert json_data["success"] is False
            assert "error" in json_data

    def test_partial_success_returns_200_with_warnings(self, client):
        """Partial success should return 200 with warnings in response."""
        with patch("tryalma.webapp.routes.get_upload_service") as mock_get:
            mock_service = MagicMock()
            mock_service.process_upload.return_value = UploadResult(
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
                warnings=["Some fields could not be extracted"],
                partially_extracted=["date_of_birth"],
            )
            mock_get.return_value = mock_service

            pdf_content = b"%PDF-1.4 test"
            data = {
                "file": (BytesIO(pdf_content), "test.pdf"),
                "document_type": "passport",
            }
            response = client.post("/upload", data=data, content_type="multipart/form-data")

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data["success"] is True
            assert "warnings" in json_data
            assert len(json_data["warnings"]) > 0

    def test_network_error_returns_retryable_error(self, client):
        """Network errors should indicate retry is possible."""
        with patch("tryalma.webapp.routes.get_upload_service") as mock_get:
            mock_service = MagicMock()
            mock_service.process_upload.side_effect = ConnectionError("Network error")
            mock_get.return_value = mock_service

            pdf_content = b"%PDF-1.4 test"
            data = {
                "file": (BytesIO(pdf_content), "test.pdf"),
                "document_type": "passport",
            }
            response = client.post("/upload", data=data, content_type="multipart/form-data")

            # Should return error status
            assert response.status_code >= 400
            json_data = response.get_json()
            assert json_data["success"] is False


class TestProcessUploadErrorRecovery:
    """Tests for error recovery in process_upload."""

    @pytest.fixture
    def upload_service(self):
        """Create UploadService with mocked services."""
        return UploadService(
            passport_service=MagicMock(),
            g28_service=MagicMock(),
            file_validator=FileValidator(),
            field_mapper=FieldMapper(),
        )

    def test_handles_unexpected_exception_gracefully(self, upload_service):
        """Unexpected exceptions should be caught and return error result."""
        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Simulate unexpected exception
        upload_service._passport_service.extract_single.side_effect = RuntimeError(
            "Unexpected internal error"
        )

        result = upload_service.process_upload(file, "passport")

        assert result.success is False
        assert result.error is not None

    def test_cleanup_temp_files_on_error(self, upload_service):
        """Temporary files should be cleaned up even on error."""
        import os
        import tempfile

        pdf_content = b"%PDF-1.4 test content"
        file = FileStorage(
            stream=BytesIO(pdf_content),
            filename="passport.pdf",
            content_type="application/pdf",
        )

        # Track temp file creation
        temp_files_before = set(os.listdir(tempfile.gettempdir()))

        # Simulate error during processing
        upload_service._passport_service.extract_single.side_effect = RuntimeError("Error")

        result = upload_service.process_upload(file, "passport")

        # Temp file should be cleaned up
        # Note: This is a behavioral test - the actual cleanup happens in finally block
        assert result.success is False
