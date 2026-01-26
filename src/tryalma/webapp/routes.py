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

from flask import Blueprint, jsonify, render_template_string, request

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


# Simple upload page template (will be replaced with full template in Task 5)
UPLOAD_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Upload</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .upload-form { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .btn { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        select, input[type="file"] { margin: 10px 0; padding: 10px; }
    </style>
</head>
<body>
    <h1>Document Upload</h1>
    <form id="upload-form" class="upload-form" method="POST" action="/upload" enctype="multipart/form-data">
        <div>
            <label for="document_type">Document Type:</label>
            <select name="document_type" id="document_type" required>
                <option value="">Select document type...</option>
                <option value="passport">Passport</option>
                <option value="g28">G-28 Form</option>
            </select>
        </div>
        <div>
            <label for="file">Select File:</label>
            <input type="file" name="file" id="file" accept=".pdf,.jpg,.jpeg,.png" required>
        </div>
        <p>Supported formats: PDF, JPEG, PNG (max 10MB)</p>
        <button type="submit" class="btn">Upload</button>
    </form>
    <div id="results"></div>
</body>
</html>
"""


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

    GET / - Returns HTML upload page.

    Returns:
        HTML page with upload form
    """
    return render_template_string(UPLOAD_PAGE_TEMPLATE)


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


# Error handlers for blueprint
@upload_bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors."""
    return jsonify({
        "success": False,
        "error": "File size exceeds maximum allowed (10MB)",
        "error_code": "FILE_TOO_LARGE",
    }), 413
