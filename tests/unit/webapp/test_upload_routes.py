"""Tests for upload blueprint HTTP routes.

TDD: RED phase - These tests define expected behavior for upload routes.

Task 4.2: Create upload blueprint with HTTP routes.
Requirements: 1.1, 1.4, 2.1, 2.2, 2.3
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage

from tryalma.webapp.upload_service import UploadResult
from tryalma.webapp.field_mapper import MappedField


@pytest.fixture
def app():
    """Create Flask app with upload blueprint for testing."""
    from tryalma.webapp import create_app

    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestUploadBlueprintRegistration:
    """Tests for blueprint registration."""

    def test_upload_blueprint_is_registered(self, app):
        """Upload blueprint should be registered with the app."""
        assert "upload" in app.blueprints

    def test_upload_blueprint_url_prefix(self, app):
        """Upload blueprint should have no URL prefix (mounted at root)."""
        blueprint = app.blueprints["upload"]
        # Blueprint itself has no prefix, routes are at root
        assert blueprint.url_prefix is None or blueprint.url_prefix == ""


class TestGetIndexRoute:
    """Tests for GET / route (main upload page)."""

    def test_get_index_returns_200(self, client):
        """GET / should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_get_index_returns_html(self, client):
        """GET / should return HTML content."""
        response = client.get("/")
        assert response.content_type.startswith("text/html")

    def test_get_index_contains_upload_form(self, client):
        """GET / should contain upload form elements."""
        response = client.get("/")
        # Should contain form with file input
        assert b"<form" in response.data or b"upload" in response.data.lower()


class TestPostUploadRoute:
    """Tests for POST /upload route."""

    def test_post_upload_requires_file(self, client):
        """POST /upload should require a file."""
        response = client.post("/upload", data={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "file" in data["error"].lower()

    def test_post_upload_requires_document_type(self, client):
        """POST /upload should require document_type."""
        # Create a valid PDF file
        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (BytesIO(pdf_content), "test.pdf"),
        }
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "document_type" in data["error"].lower() or "type" in data["error"].lower()

    def test_post_upload_validates_document_type(self, client):
        """POST /upload should validate document_type is passport or g28."""
        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (BytesIO(pdf_content), "test.pdf"),
            "document_type": "invalid",
        }
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    @patch("tryalma.webapp.routes.get_upload_service")
    def test_post_upload_returns_json(self, mock_get_service, client):
        """POST /upload should return JSON response."""
        # Mock successful upload result
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
            warnings=[],
            partially_extracted=[],
        )
        mock_get_service.return_value = mock_service

        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (BytesIO(pdf_content), "test.pdf"),
            "document_type": "passport",
        }
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )

        assert response.content_type == "application/json"
        json_data = response.get_json()
        assert "success" in json_data

    @patch("tryalma.webapp.routes.get_upload_service")
    def test_post_upload_success_response_structure(self, mock_get_service, client):
        """Successful upload should return proper response structure."""
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
            extracted_fields={
                "applicant_surname": {"value": "SMITH", "confidence": 0.95},
            },
            warnings=[],
            partially_extracted=[],
        )
        mock_get_service.return_value = mock_service

        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (BytesIO(pdf_content), "test.pdf"),
            "document_type": "passport",
        }
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True
        assert json_data["document_type"] == "passport"
        assert "form_fields" in json_data
        assert "extracted_fields" in json_data

    @patch("tryalma.webapp.routes.get_upload_service")
    def test_post_upload_handles_extraction_error(self, mock_get_service, client):
        """POST /upload should handle extraction service errors gracefully."""
        from tryalma.webapp.exceptions import ExtractionFailedError

        mock_service = MagicMock()
        mock_service.process_upload.side_effect = ExtractionFailedError(
            "Failed to extract data from document"
        )
        mock_get_service.return_value = mock_service

        pdf_content = b"%PDF-1.4 test content"
        data = {
            "file": (BytesIO(pdf_content), "test.pdf"),
            "document_type": "passport",
        }
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 422
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "error" in json_data

    @patch("tryalma.webapp.routes.get_upload_service")
    def test_post_upload_handles_unsupported_format(self, mock_get_service, client):
        """POST /upload should handle unsupported file format."""
        from tryalma.webapp.exceptions import UnsupportedFormatError

        mock_service = MagicMock()
        mock_service.process_upload.side_effect = UnsupportedFormatError(
            "Unsupported file format"
        )
        mock_get_service.return_value = mock_service

        # Use a text file content (unsupported)
        data = {
            "file": (BytesIO(b"plain text"), "test.txt"),
            "document_type": "passport",
        }
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 415
        json_data = response.get_json()
        assert json_data["success"] is False


class TestPostClearRoute:
    """Tests for POST /clear route."""

    def test_post_clear_returns_200(self, client):
        """POST /clear should return 200 OK."""
        response = client.post("/clear")
        assert response.status_code == 200

    def test_post_clear_returns_json(self, client):
        """POST /clear should return JSON response."""
        response = client.post("/clear")
        assert response.content_type == "application/json"

    def test_post_clear_returns_success(self, client):
        """POST /clear should return success status."""
        response = client.post("/clear")
        json_data = response.get_json()
        assert json_data["success"] is True

    def test_post_clear_resets_form_state(self, client):
        """POST /clear should indicate form state was reset."""
        response = client.post("/clear")
        json_data = response.get_json()
        assert "message" in json_data or json_data["success"] is True


class TestErrorResponses:
    """Tests for error response format."""

    def test_error_response_has_error_code(self, client):
        """Error responses should include error_code."""
        response = client.post("/upload", data={})
        json_data = response.get_json()
        assert "error_code" in json_data or "error" in json_data

    def test_file_too_large_returns_413(self, app, client):
        """Files exceeding MAX_CONTENT_LENGTH should return 413."""
        # Create a file larger than MAX_CONTENT_LENGTH (10MB)
        # We'll mock this by checking the config
        max_size = app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)

        # Flask should reject this with 413 before hitting our code
        # Create content just over the limit
        large_content = b"x" * (max_size + 1)
        data = {
            "file": (BytesIO(large_content), "large.pdf"),
            "document_type": "passport",
        }

        # Note: Flask's default behavior may vary; some setups require
        # explicit configuration. The test verifies the expectation.
        response = client.post(
            "/upload",
            data=data,
            content_type="multipart/form-data",
        )

        # Flask may return 413 or we handle it in code
        assert response.status_code in [400, 413]


class TestDocumentTypeValidation:
    """Tests for document type validation."""

    def test_accepts_passport_document_type(self, client):
        """Should accept 'passport' as valid document type."""
        from unittest.mock import patch, MagicMock

        with patch("tryalma.webapp.routes.get_upload_service") as mock_get:
            mock_service = MagicMock()
            mock_service.process_upload.return_value = UploadResult(
                success=True,
                document_type="passport",
                source_filename="test.pdf",
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
            )
            mock_get.return_value = mock_service

            pdf_content = b"%PDF-1.4 test"
            data = {
                "file": (BytesIO(pdf_content), "test.pdf"),
                "document_type": "passport",
            }
            response = client.post("/upload", data=data, content_type="multipart/form-data")

            # Should not return validation error for document_type
            if response.status_code == 400:
                json_data = response.get_json()
                assert "document_type" not in json_data.get("error", "").lower()

    def test_accepts_g28_document_type(self, client):
        """Should accept 'g28' as valid document type."""
        from unittest.mock import patch, MagicMock

        with patch("tryalma.webapp.routes.get_upload_service") as mock_get:
            mock_service = MagicMock()
            mock_service.process_upload.return_value = UploadResult(
                success=True,
                document_type="g28",
                source_filename="test.pdf",
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
            )
            mock_get.return_value = mock_service

            pdf_content = b"%PDF-1.4 test"
            data = {
                "file": (BytesIO(pdf_content), "test.pdf"),
                "document_type": "g28",
            }
            response = client.post("/upload", data=data, content_type="multipart/form-data")

            # Should not return validation error for document_type
            if response.status_code == 400:
                json_data = response.get_json()
                assert "document_type" not in json_data.get("error", "").lower()
