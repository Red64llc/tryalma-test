"""Flask application factory.

Creates and configures the Flask application with blueprints,
CSRF protection, error handlers, and service dependencies.
"""

import os
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

from tryalma.webapp.config import config

# Get the path to this module's directory for templates and static files
_MODULE_DIR = Path(__file__).parent


def create_app(config_name: str = "default") -> Flask:
    """Create and configure the Flask application.

    Application factory for Document Upload UI. Creates Flask app with:
    - CSRF protection enabled (except in testing)
    - Error handlers configured
    - Maximum upload size set to 10MB

    Args:
        config_name: Configuration environment (default, testing, production)

    Returns:
        Configured Flask application instance

    Example:
        app = create_app("production")
        app.run()
    """
    app = Flask(
        __name__,
        template_folder=str(_MODULE_DIR / "templates"),
        static_folder=str(_MODULE_DIR / "static"),
    )

    # Load configuration
    config_class = config.get(config_name, config["default"])
    app.config.from_object(config_class)

    # Initialize CSRF protection
    _init_csrf(app)

    # Initialize services (skip in testing mode to avoid external dependencies)
    if not app.config.get("TESTING"):
        _init_services(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    return app


def _init_csrf(app: Flask) -> None:
    """Initialize CSRF protection.

    Args:
        app: Flask application instance
    """
    from flask_wtf.csrf import CSRFProtect

    csrf = CSRFProtect()
    csrf.init_app(app)


def _init_services(app: Flask) -> None:
    """Initialize application services.

    Creates and wires up the upload service with its dependencies:
    - PassportExtractionService for passport document extraction
    - G28ParserService for G-28 form extraction
    - FileValidator for upload validation
    - FieldMapper for result transformation
    - CrossCheckService for enhanced passport extraction (when HF_TOKEN is set)

    Args:
        app: Flask application instance
    """
    from tryalma.g28.parser_service import G28ParserService
    from tryalma.passport.extractor import MRZExtractor
    from tryalma.passport.service import PassportExtractionService
    from tryalma.passport.validator import MRZValidator
    from tryalma.webapp.field_mapper import FieldMapper
    from tryalma.webapp.upload_service import UploadService
    from tryalma.webapp.validators import FileValidator

    # Create passport extraction service
    extractor = MRZExtractor()
    validator = MRZValidator()
    passport_service = PassportExtractionService(extractor, validator)

    # Create G28 parser service (uses ANTHROPIC_API_KEY from environment)
    g28_service = G28ParserService.create_default()

    # Create crosscheck service if HF_TOKEN is available
    crosscheck_service = _create_crosscheck_service(extractor, validator)

    # Create upload service with all dependencies
    upload_service = UploadService(
        passport_service=passport_service,
        g28_service=g28_service,
        file_validator=FileValidator(),
        field_mapper=FieldMapper(),
        crosscheck_service=crosscheck_service,
    )

    # Register in app extensions for route access
    if not hasattr(app, "extensions"):
        app.extensions = {}
    app.extensions["upload_service"] = upload_service


def _create_crosscheck_service(extractor, validator):
    """Create CrossCheckService if HF_TOKEN is configured.

    The CrossCheckService provides enhanced passport extraction by combining
    MRZ extraction with Qwen2-VL visual extraction for cross-validation.

    Args:
        extractor: MRZExtractor instance
        validator: MRZValidator instance

    Returns:
        CrossCheckService instance or None if HF_TOKEN not configured
    """
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        return None

    try:
        from tryalma.crosscheck.config import CrossCheckConfig
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider
        from tryalma.crosscheck.service import CrossCheckService

        config = CrossCheckConfig(hf_token=hf_token)
        vlm_provider = Qwen2VLProvider(hf_token=hf_token)

        return CrossCheckService(
            mrz_extractor=extractor,
            mrz_validator=validator,
            vlm_provider=vlm_provider,
            config=config,
        )
    except Exception as e:
        # Log but don't fail - fall back to MRZ-only extraction
        print(f"Warning: Could not initialize CrossCheckService: {e}")
        return None


def _register_blueprints(app: Flask) -> None:
    """Register application blueprints.

    Args:
        app: Flask application instance
    """
    from tryalma.webapp.routes import upload_bp

    app.register_blueprint(upload_bp)


def _register_error_handlers(app: Flask) -> None:
    """Register custom error handlers.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(404)
    def not_found_error(error):  # type: ignore[no-untyped-def]
        """Handle 404 Not Found errors."""
        if _wants_json_response():
            return jsonify(error={"code": "NOT_FOUND", "message": "Resource not found"}), 404
        return (
            render_template_string(
                """
<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body>
<h1>404 Not Found</h1>
<p>The requested resource was not found.</p>
</body>
</html>
"""
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):  # type: ignore[no-untyped-def]
        """Handle 500 Internal Server errors."""
        if _wants_json_response():
            return (
                jsonify(error={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}),
                500,
            )
        return (
            render_template_string(
                """
<!DOCTYPE html>
<html>
<head><title>500 Internal Server Error</title></head>
<body>
<h1>500 Internal Server Error</h1>
<p>An unexpected error occurred.</p>
</body>
</html>
"""
            ),
            500,
        )


def _wants_json_response() -> bool:
    """Check if the client prefers JSON response.

    Returns:
        True if client prefers JSON, False otherwise
    """
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return (
        best == "application/json"
        and request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]
    )
