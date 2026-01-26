"""Upload blueprint with HTTP routes.

Task 4.2: Create upload blueprint with HTTP routes.
Requirements: 1.1, 1.4, 2.1, 2.2, 2.3

Implements:
- GET / - Serve main upload page
- POST /upload - Handle file submissions and return JSON responses
- POST /clear - Reset form state
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from flask import Blueprint, jsonify, render_template, request

from tryalma.webapp.exceptions import (
    DocumentTypeRequiredError,
    ExtractionFailedError,
    FileValidationError,
    UnsupportedFormatError,
    WebAppError,
)

if TYPE_CHECKING:
    from flask import Response


# Create blueprint
upload_bp = Blueprint("upload", __name__)


def get_upload_service():
    """Get the upload service from app extensions or create a mock.

    In production, this will be set up in the app factory.
    For testing, this function can be mocked.

    Returns:
        UploadService instance
    """
    from flask import current_app

    # Try to get from app extensions
    if "upload_service" in current_app.extensions:
        return current_app.extensions["upload_service"]

    # Create a default instance (for development/testing without full setup)
    from tryalma.webapp.field_mapper import FieldMapper
    from tryalma.webapp.upload_service import UploadService
    from tryalma.webapp.validators import FileValidator
    from unittest.mock import MagicMock

    # In a real setup, these would be properly configured services
    # For basic testing, we create minimal mocks
    passport_service = MagicMock()
    g28_service = MagicMock()

    return UploadService(
        passport_service=passport_service,
        g28_service=g28_service,
        file_validator=FileValidator(),
        field_mapper=FieldMapper(),
    )


@upload_bp.route("/")
def index() -> str:
    """Serve the main upload page.

    GET / - Returns HTML upload page with drag-and-drop upload zone.

    Returns:
        HTML page with upload form and document type selector
    """
    return render_template("upload.html")


@upload_bp.route("/upload", methods=["POST"])
def upload() -> tuple["Response", int]:
    """Handle file upload submissions.

    POST /upload - Process uploaded document and return JSON response.

    Expected form data:
    - file: The uploaded file (required)
    - document_type: "passport" or "g28" (required)

    Returns:
        JSON response with extraction results or error
    """
    # Validate file is present
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file provided. Please select a file to upload.",
            "error_code": "NO_FILE",
        }), 400

    file = request.files["file"]

    # Check if file was actually selected
    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "No file selected. Please choose a file to upload.",
            "error_code": "NO_FILE",
        }), 400

    # Validate document_type is present
    document_type = request.form.get("document_type", "").strip()
    if not document_type:
        return jsonify({
            "success": False,
            "error": "Document type is required. Please select passport or g28.",
            "error_code": "DOCUMENT_TYPE_REQUIRED",
        }), 400

    # Validate document_type value
    if document_type not in ("passport", "g28"):
        return jsonify({
            "success": False,
            "error": f"Invalid document type '{document_type}'. Must be 'passport' or 'g28'.",
            "error_code": "INVALID_DOCUMENT_TYPE",
        }), 400

    # Get upload service and process
    try:
        service = get_upload_service()
        result = service.process_upload(file, document_type)  # type: ignore[arg-type]

        # Return success or error based on result
        if result.success:
            return jsonify(result.to_json_dict()), 200
        else:
            return jsonify({
                "success": False,
                "error": result.error or "Extraction failed",
                "error_code": result.error_code or "EXTRACTION_FAILED",
            }), 422

    except UnsupportedFormatError as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_code": "UNSUPPORTED_FORMAT",
        }), 415

    except FileValidationError as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_code": "VALIDATION_ERROR",
        }), 400

    except ExtractionFailedError as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_code": "EXTRACTION_FAILED",
        }), 422

    except WebAppError as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_code": e.error_code,
        }), e.status_code

    except Exception as e:
        # Log unexpected errors in production
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
            "error_code": "INTERNAL_ERROR",
        }), 500


@upload_bp.route("/clear", methods=["POST"])
def clear() -> tuple["Response", int]:
    """Reset form state.

    POST /clear - Clear all extracted data and reset form.

    Returns:
        JSON success response
    """
    # In a stateful app, this would clear session data
    # For now, it just returns success to indicate the form can be reset
    return jsonify({
        "success": True,
        "message": "Form state cleared successfully",
    }), 200


@upload_bp.route("/populate-form", methods=["POST"])
def populate_form() -> tuple["Response", int]:
    """Populate an external form with extracted data.

    POST /populate-form - Use Playwright to auto-fill a form with extracted data.

    Expected JSON body:
    - form_url: URL of the target form (required)
    - extracted_data: Dictionary of field values to populate (required)

    Returns:
        JSON response with population results or error
    """
    # Validate request is JSON
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Request must be JSON",
            "error_code": "INVALID_REQUEST",
        }), 400

    data = request.get_json()

    # Validate required fields
    form_url = data.get("form_url", "").strip()
    if not form_url:
        return jsonify({
            "success": False,
            "error": "Target form URL is required",
            "error_code": "FORM_URL_REQUIRED",
        }), 400

    extracted_data = data.get("extracted_data", {})
    if not extracted_data:
        return jsonify({
            "success": False,
            "error": "No extracted data provided",
            "error_code": "NO_DATA",
        }), 400

    # Validate URL format
    from urllib.parse import urlparse
    parsed = urlparse(form_url)
    if not parsed.scheme or not parsed.netloc:
        return jsonify({
            "success": False,
            "error": "Invalid form URL format",
            "error_code": "INVALID_URL",
        }), 400

    # Use the FormPopulationService to actually populate the form
    try:
        from tryalma.form_populator.service import FormPopulationService, PopulationConfig

        # Create service with headed mode so user can see the automation
        # Use non-headless for development/demo, headless for production
        config = PopulationConfig(
            headless=False,  # Show browser window for user to see
            timeout_ms=60000,  # 60 second timeout
            inter_field_delay_ms=100,  # Small delay between fields
        )

        service = FormPopulationService(config=config)
        report = service.populate(form_url, extracted_data)

        return jsonify({
            "success": report.success,
            "message": "Form populated successfully" if report.success else "Form population had issues",
            "report": report.to_dict(),
        }), 200 if report.success else 422

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Form population failed: {str(e)}",
            "error_code": "POPULATION_FAILED",
        }), 500


# Error handlers for blueprint
@upload_bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors."""
    return jsonify({
        "success": False,
        "error": "File size exceeds maximum allowed (10MB)",
        "error_code": "FILE_TOO_LARGE",
    }), 413
