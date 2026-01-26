"""Tests for form population exception hierarchy.

These tests verify:
- FormPopulationError extends ProcessingError (Requirements: 1.5)
- NavigationError has url and reason attributes (Requirements: 2.3)
- FormNotFoundError has missing_elements list (Requirements: 2.4)
- BrowserError has operation and reason attributes (Requirements: 10.5)
- PageNavigationError for unexpected page navigation (Requirements: 10.3)
- All exceptions integrate with CLI error handling patterns
"""

import pytest

from tryalma.exceptions import ProcessingError, CLIError
from tryalma.form_populator.exceptions import (
    FormPopulationError,
    NavigationError,
    FormNotFoundError,
    BrowserError,
    PageNavigationError,
)


class TestFormPopulationError:
    """Tests for base FormPopulationError."""

    def test_extends_processing_error(self):
        """FormPopulationError should extend ProcessingError."""
        error = FormPopulationError("Test error")

        assert isinstance(error, ProcessingError)
        assert isinstance(error, CLIError)

    def test_message_attribute(self):
        """FormPopulationError should accept custom message."""
        error = FormPopulationError("Custom form error")

        assert error.message == "Custom form error"
        assert str(error) == "Custom form error"

    def test_default_message(self):
        """FormPopulationError should have default message."""
        error = FormPopulationError()

        assert error.message == "Form population failed"

    def test_inherits_exit_code(self):
        """FormPopulationError should inherit exit code 3 from ProcessingError."""
        error = FormPopulationError()

        assert error.exit_code == 3


class TestNavigationError:
    """Tests for NavigationError."""

    def test_extends_form_population_error(self):
        """NavigationError should extend FormPopulationError."""
        error = NavigationError(url="https://example.com", reason="Connection refused")

        assert isinstance(error, FormPopulationError)
        assert isinstance(error, ProcessingError)

    def test_url_attribute(self):
        """NavigationError should have url attribute."""
        error = NavigationError(url="https://example.com/form", reason="Timeout")

        assert error.url == "https://example.com/form"

    def test_reason_attribute(self):
        """NavigationError should have reason attribute."""
        error = NavigationError(url="https://example.com", reason="Connection refused")

        assert error.reason == "Connection refused"

    def test_message_format(self):
        """NavigationError should format message with url and reason."""
        error = NavigationError(
            url="https://example.com/form",
            reason="Connection timed out",
        )

        assert "https://example.com/form" in str(error)
        assert "Connection timed out" in str(error)

    def test_inherits_exit_code(self):
        """NavigationError should inherit exit code from ProcessingError."""
        error = NavigationError(url="https://example.com", reason="Failed")

        assert error.exit_code == 3


class TestFormNotFoundError:
    """Tests for FormNotFoundError."""

    def test_extends_form_population_error(self):
        """FormNotFoundError should extend FormPopulationError."""
        error = FormNotFoundError(missing_elements=["form", "input[name='email']"])

        assert isinstance(error, FormPopulationError)
        assert isinstance(error, ProcessingError)

    def test_missing_elements_attribute(self):
        """FormNotFoundError should have missing_elements list."""
        missing = ["form", "input[name='email']", "select[name='country']"]
        error = FormNotFoundError(missing_elements=missing)

        assert error.missing_elements == missing

    def test_empty_missing_elements(self):
        """FormNotFoundError should accept empty list."""
        error = FormNotFoundError(missing_elements=[])

        assert error.missing_elements == []

    def test_message_format(self):
        """FormNotFoundError should format message with missing elements."""
        error = FormNotFoundError(missing_elements=["form", "input[name='email']"])

        assert "form" in str(error)
        assert "input[name='email']" in str(error)

    def test_inherits_exit_code(self):
        """FormNotFoundError should inherit exit code from ProcessingError."""
        error = FormNotFoundError(missing_elements=["form"])

        assert error.exit_code == 3


class TestBrowserError:
    """Tests for BrowserError."""

    def test_extends_form_population_error(self):
        """BrowserError should extend FormPopulationError."""
        error = BrowserError(operation="launch", reason="Browser crashed")

        assert isinstance(error, FormPopulationError)
        assert isinstance(error, ProcessingError)

    def test_operation_attribute(self):
        """BrowserError should have operation attribute."""
        error = BrowserError(operation="launch", reason="Failed to start")

        assert error.operation == "launch"

    def test_reason_attribute(self):
        """BrowserError should have reason attribute."""
        error = BrowserError(operation="screenshot", reason="Page not loaded")

        assert error.reason == "Page not loaded"

    def test_message_format(self):
        """BrowserError should format message with operation and reason."""
        error = BrowserError(operation="click", reason="Element not interactable")

        assert "click" in str(error)
        assert "Element not interactable" in str(error)

    def test_various_operations(self):
        """BrowserError should accept various operation types."""
        operations = ["launch", "navigate", "click", "fill", "screenshot", "close"]

        for op in operations:
            error = BrowserError(operation=op, reason="Test failure")
            assert error.operation == op

    def test_inherits_exit_code(self):
        """BrowserError should inherit exit code from ProcessingError."""
        error = BrowserError(operation="launch", reason="Failed")

        assert error.exit_code == 3


class TestPageNavigationError:
    """Tests for PageNavigationError."""

    def test_extends_form_population_error(self):
        """PageNavigationError should extend FormPopulationError."""
        error = PageNavigationError("Page unexpectedly navigated away")

        assert isinstance(error, FormPopulationError)
        assert isinstance(error, ProcessingError)

    def test_message_attribute(self):
        """PageNavigationError should accept message."""
        error = PageNavigationError("Page redirected to login")

        assert error.message == "Page redirected to login"
        assert str(error) == "Page redirected to login"

    def test_default_message(self):
        """PageNavigationError should have default message."""
        error = PageNavigationError()

        assert "navigation" in error.message.lower() or "navigated" in error.message.lower()

    def test_inherits_exit_code(self):
        """PageNavigationError should inherit exit code from ProcessingError."""
        error = PageNavigationError()

        assert error.exit_code == 3


class TestExceptionHierarchy:
    """Tests for overall exception hierarchy integration."""

    def test_all_exceptions_are_cli_errors(self):
        """All form population exceptions should be CLIError subclasses."""
        exceptions = [
            FormPopulationError("test"),
            NavigationError(url="https://test.com", reason="test"),
            FormNotFoundError(missing_elements=["test"]),
            BrowserError(operation="test", reason="test"),
            PageNavigationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, CLIError), f"{type(exc).__name__} is not a CLIError"
            assert hasattr(exc, "exit_code"), f"{type(exc).__name__} missing exit_code"
            assert exc.exit_code == 3, f"{type(exc).__name__} has wrong exit_code"

    def test_all_exceptions_have_message(self):
        """All form population exceptions should have message attribute."""
        exceptions = [
            FormPopulationError("test message"),
            NavigationError(url="https://test.com", reason="test"),
            FormNotFoundError(missing_elements=["test"]),
            BrowserError(operation="test", reason="test"),
            PageNavigationError("test message"),
        ]

        for exc in exceptions:
            assert hasattr(exc, "message"), f"{type(exc).__name__} missing message"
            assert str(exc), f"{type(exc).__name__} has empty string representation"
