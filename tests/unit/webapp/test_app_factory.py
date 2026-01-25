"""Tests for Flask application factory.

TDD: RED phase - These tests define expected behavior for the Flask app factory.
"""

import pytest
from flask import Flask


class TestCreateApp:
    """Tests for create_app factory function."""

    def test_create_app_returns_flask_instance(self):
        """Application factory should return a Flask instance."""
        from tryalma.webapp import create_app

        app = create_app()

        assert isinstance(app, Flask)

    def test_create_app_with_default_config(self):
        """Default config should be development mode."""
        from tryalma.webapp import create_app

        app = create_app()

        assert app.config["DEBUG"] is True
        assert app.config["TESTING"] is False

    def test_create_app_with_testing_config(self):
        """Testing config should enable TESTING flag."""
        from tryalma.webapp import create_app

        app = create_app("testing")

        assert app.config["TESTING"] is True
        assert app.config["WTF_CSRF_ENABLED"] is False  # Disabled for tests

    def test_create_app_with_production_config(self):
        """Production config should disable DEBUG."""
        from tryalma.webapp import create_app
        import os

        # Production requires SECRET_KEY
        os.environ["SECRET_KEY"] = "test-secret-key-for-production"

        app = create_app("production")

        assert app.config["DEBUG"] is False
        assert app.config["TESTING"] is False

        # Clean up
        del os.environ["SECRET_KEY"]

    def test_create_app_sets_max_content_length(self):
        """App should set maximum upload file size to 10MB."""
        from tryalma.webapp import create_app

        app = create_app()

        # 10MB = 10 * 1024 * 1024 bytes
        assert app.config["MAX_CONTENT_LENGTH"] == 10 * 1024 * 1024

    def test_create_app_has_secret_key(self):
        """App should have a secret key configured."""
        from tryalma.webapp import create_app

        app = create_app()

        assert app.config["SECRET_KEY"] is not None
        assert len(app.config["SECRET_KEY"]) > 0


class TestCSRFProtection:
    """Tests for CSRF protection configuration."""

    def test_csrf_protection_enabled_by_default(self):
        """CSRF protection should be enabled by default."""
        from tryalma.webapp import create_app

        app = create_app()

        assert app.config.get("WTF_CSRF_ENABLED", True) is True

    def test_csrf_protection_disabled_in_testing(self):
        """CSRF protection should be disabled in testing config."""
        from tryalma.webapp import create_app

        app = create_app("testing")

        assert app.config["WTF_CSRF_ENABLED"] is False


class TestErrorHandlers:
    """Tests for registered error handlers."""

    def test_404_error_handler_returns_json_for_json_request(self):
        """404 handler should return JSON for API requests."""
        from tryalma.webapp import create_app

        app = create_app("testing")

        with app.test_client() as client:
            response = client.get(
                "/nonexistent-path",
                headers={"Accept": "application/json"},
            )

            assert response.status_code == 404
            data = response.get_json()
            assert data is not None
            assert "error" in data

    def test_404_error_handler_returns_html_for_browser(self):
        """404 handler should return HTML for browser requests."""
        from tryalma.webapp import create_app

        app = create_app("testing")

        with app.test_client() as client:
            response = client.get(
                "/nonexistent-path",
                headers={"Accept": "text/html"},
            )

            assert response.status_code == 404
            assert response.content_type.startswith("text/html")
