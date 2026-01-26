"""Tests for base Jinja2 template with Bootstrap 5 integration.

TDD: GREEN phase - Testing the base template implementation.
Task 5.1: Create base Jinja2 template with Bootstrap 5 integration
Requirements: 7.1, 7.2
"""

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a Flask app with templates for testing."""
    from tryalma.webapp import create_app

    return create_app("testing")


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def render_template_in_request_context(app, template_name):
    """Helper to render template within request context.

    This is needed because csrf_token() requires a request context.
    """
    with app.test_request_context():
        template = app.jinja_env.get_template(template_name)
        return template.render()


class TestBaseTemplateExists:
    """Tests for base template existence and basic structure."""

    def test_base_template_exists(self, app):
        """Base template file should exist in templates directory."""
        # The template should be loadable by Flask
        with app.app_context():
            template = app.jinja_env.get_template("base.html")
            assert template is not None

    def test_base_template_renders(self, app):
        """Base template should render without errors."""
        rendered = render_template_in_request_context(app, "base.html")
        assert "<!DOCTYPE html>" in rendered or "<!doctype html>" in rendered.lower()


class TestBootstrapIntegration:
    """Tests for Bootstrap 5 CDN integration."""

    def test_bootstrap_css_included(self, app):
        """Bootstrap 5 CSS should be included via CDN."""
        rendered = render_template_in_request_context(app, "base.html")

        # Check for Bootstrap 5 CSS CDN link
        assert "bootstrap" in rendered.lower()
        assert "cdn" in rendered.lower() or "jsdelivr" in rendered.lower() or "cloudflare" in rendered.lower()
        # Check for CSS link
        assert "stylesheet" in rendered.lower()

    def test_bootstrap_js_included(self, app):
        """Bootstrap 5 JS should be included via CDN."""
        rendered = render_template_in_request_context(app, "base.html")

        # Check for Bootstrap 5 JS bundle
        assert "bootstrap" in rendered.lower()
        # Should include the JS bundle
        assert ".js" in rendered or "bundle" in rendered.lower()

    def test_responsive_viewport_meta(self, app):
        """Template should include viewport meta tag for responsive design."""
        rendered = render_template_in_request_context(app, "base.html")

        # Check for responsive viewport meta tag
        assert "viewport" in rendered.lower()
        assert "width=device-width" in rendered.lower()


class TestTemplateBlocks:
    """Tests for Jinja2 template blocks."""

    def test_title_block_exists(self, app):
        """Template should have a title block for page-specific titles."""
        with app.app_context():
            # Check the source for block definition
            source = app.jinja_env.loader.get_source(app.jinja_env, "base.html")[0]
            assert "{% block title %}" in source or "{%block title%}" in source.replace(" ", "")

    def test_content_block_exists(self, app):
        """Template should have a content block for page content."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "base.html")[0]
            assert "{% block content %}" in source or "{%block content%}" in source.replace(" ", "")

    def test_scripts_block_exists(self, app):
        """Template should have a scripts block for page-specific scripts."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "base.html")[0]
            assert "{% block scripts %}" in source or "{%block scripts%}" in source.replace(" ", "")


class TestFlashMessages:
    """Tests for flash message display area."""

    def test_flash_message_area_exists(self, app):
        """Template should have an area for displaying flash messages."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "base.html")[0]

            # Should use get_flashed_messages
            assert "get_flashed_messages" in source

    def test_flash_message_with_categories(self, app):
        """Flash message handling should support categories."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "base.html")[0]

            # Should use with_categories=true for Bootstrap alert styling
            assert "with_categories" in source


class TestCSRFToken:
    """Tests for CSRF token availability for AJAX requests."""

    def test_csrf_token_available(self, app):
        """Template should include CSRF token for AJAX requests."""
        with app.app_context():
            source = app.jinja_env.loader.get_source(app.jinja_env, "base.html")[0]

            # Should include csrf_token() function call
            assert "csrf_token" in source

    def test_csrf_token_in_meta_tag(self, app):
        """CSRF token should be in a meta tag for easy JavaScript access."""
        rendered = render_template_in_request_context(app, "base.html")

        # Should have a meta tag with csrf token
        assert 'name="csrf-token"' in rendered.lower() or 'name="csrf_token"' in rendered.lower()


class TestHTMLStructure:
    """Tests for proper HTML5 document structure."""

    def test_html5_doctype(self, app):
        """Template should have HTML5 doctype."""
        rendered = render_template_in_request_context(app, "base.html")
        assert "<!DOCTYPE html>" in rendered or "<!doctype html>" in rendered.lower()

    def test_html_lang_attribute(self, app):
        """HTML tag should have lang attribute for accessibility."""
        rendered = render_template_in_request_context(app, "base.html")
        assert '<html lang="en">' in rendered or "<html lang='en'>" in rendered

    def test_charset_meta(self, app):
        """Template should specify UTF-8 charset."""
        rendered = render_template_in_request_context(app, "base.html")
        assert "utf-8" in rendered.lower()

    def test_main_container(self, app):
        """Template should have a main content container."""
        rendered = render_template_in_request_context(app, "base.html")
        # Should have a container class for Bootstrap layout
        assert "container" in rendered.lower()
