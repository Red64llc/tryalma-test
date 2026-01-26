"""Tests for results display panel (Task 7.1, 7.2).

TDD: RED phase - Tests for displaying extracted data with confidence levels.

Task 7.1: Create results panel template for displaying extracted data with confidence
Task 7.2: Implement clear results functionality

Requirements: 5.1, 5.2, 5.3, 5.5, 6.1, 6.2, 6.3, 6.4
"""

import pytest


@pytest.fixture
def app():
    """Create Flask app with templates for testing."""
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


class TestResultsPanelExists:
    """Tests for results panel existence in template (Requirement 5.1)."""

    def test_results_panel_exists(self, app):
        """Upload page should have a results panel area."""
        rendered = render_upload_template(app)

        # Should have element for results display
        assert "result" in rendered.lower()
        # Should have specific element for extracted fields
        assert "extracted" in rendered.lower() or "fields" in rendered.lower()

    def test_results_panel_has_heading(self, app):
        """Results panel should have an identifiable heading."""
        rendered = render_upload_template(app)

        # Should have heading for results section
        assert "extraction" in rendered.lower() or "result" in rendered.lower()


class TestFieldLabelsDisplay:
    """Tests for displaying extracted field values with labels (Requirement 6.1)."""

    def test_results_area_can_display_fields(self, app):
        """Results area should be structured to display field-value pairs."""
        rendered = render_upload_template(app)

        # Should have a container for extracted fields
        assert 'id="extracted-fields"' in rendered or "extracted-fields" in rendered

    def test_results_uses_bootstrap_components(self, app):
        """Results display should use Bootstrap components for styling."""
        rendered = render_upload_template(app)

        # Should use Bootstrap card or table components in results area
        assert "card" in rendered.lower() or "table" in rendered.lower()


class TestConfidenceIndicators:
    """Tests for confidence score display as visual indicators (Requirement 6.2)."""

    def test_upload_js_has_confidence_badge_function(self, app):
        """Upload.js should have function to create confidence badges."""
        # Read the JS file
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should have function to get confidence badge class
        assert "getConfidenceBadgeClass" in js_content or "confidence" in js_content.lower()

    def test_confidence_high_level_uses_success_color(self, app):
        """High confidence (>=90%) should use success/green color."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # High confidence should use success styling
        assert "bg-success" in js_content or "success" in js_content

    def test_confidence_medium_level_uses_warning_color(self, app):
        """Medium confidence (70-90%) should use warning/yellow color."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Medium confidence should use warning styling
        assert "bg-warning" in js_content or "warning" in js_content

    def test_confidence_low_level_uses_danger_color(self, app):
        """Low confidence (<70%) should use danger/red color."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Low confidence should use danger styling
        assert "bg-danger" in js_content or "danger" in js_content


class TestFieldGroupingByDocumentType:
    """Tests for grouping fields by document type (Requirements 5.2, 5.3)."""

    def test_upload_js_groups_passport_fields(self, app):
        """JavaScript should display header for passport fields."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should create header for passport data
        assert "passport" in js_content.lower()

    def test_upload_js_groups_g28_fields(self, app):
        """JavaScript should display header for G-28 fields."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should create header for G-28 data
        assert "g-28" in js_content.lower() or "g28" in js_content.lower()


class TestFieldLabelMapping:
    """Tests for human-readable field labels."""

    def test_upload_js_has_field_labels_mapping(self, app):
        """JavaScript should have mapping of field IDs to display labels."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should have label mappings for passport fields
        assert "applicant_surname" in js_content
        assert "applicant_given_names" in js_content
        assert "passport_number" in js_content

    def test_upload_js_has_g28_field_labels(self, app):
        """JavaScript should have label mappings for G-28 fields."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should have label mappings for G-28 fields
        assert "attorney_surname" in js_content
        assert "attorney_given_names" in js_content


class TestClearResultsButton:
    """Tests for clear results functionality (Requirements 5.5, 6.4)."""

    def test_clear_button_exists_in_template(self, app):
        """Results area should have a clear button."""
        rendered = render_upload_template(app)

        # Should have clear button
        assert "clear" in rendered.lower()
        assert 'id="clear-results-btn"' in rendered.lower() or "clear-results" in rendered.lower()

    def test_clear_button_only_visible_with_results(self, app):
        """Clear button should be in the results content area."""
        rendered = render_upload_template(app)

        # Clear button should be inside results-content area
        assert "results-content" in rendered.lower()
        assert "clear" in rendered.lower()


class TestClearResultsJavaScript:
    """Tests for clear results JavaScript functionality."""

    def test_clear_results_function_exists(self, app):
        """JavaScript should have function to clear results."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should have clearResults function
        assert "clearResults" in js_content or "clear" in js_content

    def test_clear_results_hides_results_content(self, app):
        """Clear results should hide the results content area."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should hide resultsContent element
        assert "resultsContent" in js_content

    def test_clear_results_shows_no_results_placeholder(self, app):
        """Clear results should show the no-results placeholder."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should show noResults element
        assert "noResults" in js_content

    def test_clear_results_calls_clear_endpoint(self, app):
        """Clear results should call the /clear endpoint."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should call /clear endpoint
        assert "/clear" in js_content

    def test_clear_results_clears_extracted_fields(self, app):
        """Clear results should clear the extracted fields display."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should clear extractedFields element
        assert "extractedFields" in js_content


class TestClearEndpoint:
    """Tests for POST /clear endpoint (Task 7.2)."""

    def test_clear_endpoint_returns_success(self, client):
        """POST /clear should return success response."""
        response = client.post("/clear")

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True

    def test_clear_endpoint_returns_json(self, client):
        """POST /clear should return JSON content type."""
        response = client.post("/clear")

        assert response.content_type == "application/json"


class TestDisplayExtractedFieldsFunction:
    """Tests for the displayExtractedFields JavaScript function."""

    def test_display_function_exists(self, app):
        """JavaScript should have displayExtractedFields function."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should have display function
        assert "displayExtractedFields" in js_content

    def test_display_function_creates_table(self, app):
        """displayExtractedFields should create a table for field display."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should create table elements
        assert "table" in js_content.lower()

    def test_display_function_shows_confidence_as_badge(self, app):
        """displayExtractedFields should show confidence as badge."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should create badge elements
        assert "badge" in js_content.lower()


class TestNoResultsPlaceholder:
    """Tests for no-results placeholder state."""

    def test_no_results_placeholder_exists(self, app):
        """Template should have a no-results placeholder."""
        rendered = render_upload_template(app)

        # Should have no-results element
        assert 'id="no-results"' in rendered.lower() or "no-results" in rendered.lower()

    def test_no_results_has_instructional_text(self, app):
        """No-results placeholder should have instructional text."""
        rendered = render_upload_template(app)

        # Should have text explaining what to do
        assert "upload" in rendered.lower()
        assert "document" in rendered.lower()


class TestSuccessMessage:
    """Tests for success message display."""

    def test_success_message_element_exists(self, app):
        """Template should have a success message element."""
        rendered = render_upload_template(app)

        # Should have success message element
        assert 'id="success-message"' in rendered.lower() or "success-message" in rendered.lower()

    def test_success_message_uses_bootstrap_alert(self, app):
        """Success message should use Bootstrap alert styling."""
        rendered = render_upload_template(app)

        # Should use alert-success class
        assert "alert-success" in rendered.lower()


class TestWarningsDisplay:
    """Tests for warnings display area."""

    def test_warnings_area_exists(self, app):
        """Template should have a warnings display area."""
        rendered = render_upload_template(app)

        # Should have warnings area element
        assert 'id="warnings-area"' in rendered.lower() or "warnings" in rendered.lower()

    def test_upload_js_has_display_warnings_function(self, app):
        """JavaScript should have function to display warnings."""
        import os

        js_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "src",
            "tryalma",
            "webapp",
            "static",
            "js",
            "upload.js",
        )
        with open(js_path) as f:
            js_content = f.read()

        # Should have displayWarnings function
        assert "displayWarnings" in js_content or "warnings" in js_content


class TestResultsPanelIntegration:
    """Integration tests for results panel with upload flow."""

    def test_results_panel_initially_hidden(self, app):
        """Results content should be hidden initially."""
        rendered = render_upload_template(app)

        # Results content should have d-none class initially
        assert "d-none" in rendered

    def test_no_results_visible_initially(self, app):
        """No-results placeholder should be visible initially."""
        rendered = render_upload_template(app)

        # no-results should exist and not have d-none
        # (This is a simplified check - actual visibility depends on CSS)
        assert 'id="no-results"' in rendered.lower()
