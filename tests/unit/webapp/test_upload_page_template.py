"""Tests for upload page template with document type selector and upload zone.

TDD: RED phase - Testing the upload page template.
Task 6.1: Create upload page template with document type selector and upload zone
Requirements: 1.1, 1.4, 1.5, 2.1, 7.3, 7.4
"""

import pytest


@pytest.fixture
def app():
    """Create a Flask app with templates for testing."""
    from tryalma.webapp import create_app

    return create_app("testing")


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def render_upload_template(app):
    """Helper to render upload template within request context."""
    with app.test_request_context():
        template = app.jinja_env.get_template("upload.html")
        return template.render()


class TestUploadTemplateExists:
    """Tests for upload page template existence."""

    def test_upload_template_exists(self, app):
        """Upload page template should exist in templates directory."""
        with app.app_context():
            template = app.jinja_env.get_template("upload.html")
            assert template is not None

    def test_upload_template_extends_base(self, app):
        """Upload template should extend base template."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "upload.html")[0]
            assert "{% extends" in source
            assert "base.html" in source


class TestDocumentTypeSelector:
    """Tests for document type selector (Requirement 2.1)."""

    def test_document_type_selector_exists(self, app):
        """Upload page should have a document type selector."""
        rendered = render_upload_template(app)

        # Should have a select element for document type
        assert "document_type" in rendered
        assert "<select" in rendered.lower()

    def test_document_type_has_passport_option(self, app):
        """Document type selector should have passport option."""
        rendered = render_upload_template(app)

        assert "passport" in rendered.lower()
        assert 'value="passport"' in rendered.lower()

    def test_document_type_has_g28_option(self, app):
        """Document type selector should have G-28 option."""
        rendered = render_upload_template(app)

        assert "g28" in rendered.lower() or "g-28" in rendered.lower()
        assert 'value="g28"' in rendered.lower()

    def test_document_type_has_placeholder_option(self, app):
        """Document type selector should have a placeholder/prompt option."""
        rendered = render_upload_template(app)

        # Should have a default "select" prompt option
        assert "select" in rendered.lower() or "choose" in rendered.lower()


class TestUploadZone:
    """Tests for upload zone component (Requirement 1.1)."""

    def test_upload_zone_exists(self, app):
        """Upload page should have a drag-and-drop upload zone."""
        rendered = render_upload_template(app)

        # Should have an element identifiable as upload zone
        assert "upload" in rendered.lower()
        # Should have drop-related class or id
        assert "drop" in rendered.lower() or "dropzone" in rendered.lower()

    def test_upload_zone_has_file_input(self, app):
        """Upload zone should have a file input element."""
        rendered = render_upload_template(app)

        assert 'type="file"' in rendered.lower()
        assert 'name="file"' in rendered.lower()

    def test_upload_zone_accepts_supported_formats(self, app):
        """File input should specify accepted file formats."""
        rendered = render_upload_template(app)

        # Should have accept attribute with supported formats
        assert "accept=" in rendered.lower()
        # Should accept PDF, JPEG, PNG
        assert ".pdf" in rendered.lower() or "application/pdf" in rendered.lower()
        assert ".jpg" in rendered.lower() or ".jpeg" in rendered.lower() or "image/jpeg" in rendered.lower()
        assert ".png" in rendered.lower() or "image/png" in rendered.lower()


class TestSupportedFormatsGuidance:
    """Tests for supported file formats guidance (Requirement 7.4)."""

    def test_shows_supported_formats(self, app):
        """Upload page should display supported file formats."""
        rendered = render_upload_template(app)

        # Should mention PDF
        assert "pdf" in rendered.lower()
        # Should mention JPEG/JPG
        assert "jpeg" in rendered.lower() or "jpg" in rendered.lower()
        # Should mention PNG
        assert "png" in rendered.lower()

    def test_shows_file_size_limit(self, app):
        """Upload page should show maximum file size."""
        rendered = render_upload_template(app)

        # Should mention 10MB limit
        assert "10" in rendered and ("mb" in rendered.lower() or "megabyte" in rendered.lower())


class TestLoadingIndicator:
    """Tests for loading indicator during upload (Requirement 1.4)."""

    def test_loading_indicator_element_exists(self, app):
        """Upload page should have a loading indicator element."""
        rendered = render_upload_template(app)

        # Should have loading/spinner element (hidden by default)
        assert "loading" in rendered.lower() or "spinner" in rendered.lower() or "progress" in rendered.lower()

    def test_loading_indicator_initially_hidden(self, app):
        """Loading indicator should be hidden by default."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "upload.html")[0]
            # Should have CSS to hide loading indicator initially
            assert "d-none" in source or "hidden" in source.lower() or "display: none" in source.lower() or "style=\"display:none\"" in source.lower()


class TestFormStructure:
    """Tests for form structure (Requirements 7.3, 7.4)."""

    def test_has_form_element(self, app):
        """Upload page should have a form element."""
        rendered = render_upload_template(app)

        assert "<form" in rendered.lower()
        # Should have enctype for file upload
        assert "multipart/form-data" in rendered.lower()

    def test_form_action_is_upload(self, app):
        """Form should post to /upload endpoint."""
        rendered = render_upload_template(app)

        # Should have action pointing to upload
        assert "upload" in rendered.lower()

    def test_has_clear_labels(self, app):
        """Form should have clear labels for inputs (Requirement 7.4)."""
        rendered = render_upload_template(app)

        # Should have label elements
        assert "<label" in rendered.lower()

    def test_uses_bootstrap_styling(self, app):
        """Form should use Bootstrap classes for styling (Requirement 7.1)."""
        rendered = render_upload_template(app)

        # Should use Bootstrap form classes
        assert "form-" in rendered.lower()


class TestVisualFeedback:
    """Tests for visual feedback elements (Requirement 7.3)."""

    def test_upload_zone_has_visual_styling(self, app):
        """Upload zone should have visual styling for drop area."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "upload.html")[0]
            # Should have CSS for upload zone styling (border, dashed, etc.)
            assert "border" in source.lower() or "upload-zone" in source.lower()

    def test_has_error_display_area(self, app):
        """Upload page should have an area for displaying errors."""
        rendered = render_upload_template(app)

        # Should have element for error messages
        assert "error" in rendered.lower() or "alert" in rendered.lower()

    def test_has_results_area(self, app):
        """Upload page should have an area for displaying results."""
        rendered = render_upload_template(app)

        # Should have element for results
        assert "result" in rendered.lower()


class TestAccessibility:
    """Tests for accessibility features."""

    def test_file_input_has_id(self, app):
        """File input should have an id for label association."""
        rendered = render_upload_template(app)

        # File input should have id attribute
        assert 'id="' in rendered and 'type="file"' in rendered.lower()

    def test_document_type_has_id(self, app):
        """Document type selector should have an id for label association."""
        rendered = render_upload_template(app)

        # Select should have id attribute
        assert 'id="' in rendered.lower() and "<select" in rendered.lower()


class TestRouteServesUploadTemplate:
    """Tests that the route serves the upload template."""

    def test_index_route_serves_upload_page(self, client):
        """GET / should serve the upload page with proper template."""
        response = client.get("/")

        assert response.status_code == 200
        # Should have the upload components
        data = response.get_data(as_text=True)
        assert "document_type" in data.lower()
        assert "upload" in data.lower()
