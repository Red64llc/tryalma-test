"""Tests for BrowserController - browser lifecycle management and element interactions.

These tests verify:
- Task 2.1: Browser lifecycle management (Requirements: 1.1, 1.2, 1.3, 1.4, 1.5)
- Task 2.2: Page navigation and form readiness (Requirements: 2.1, 2.2, 2.3, 2.4, 2.5)
- Task 2.3: Element interaction utilities (Requirements: 4.1, 4.2, 5.4, 6.1, 6.2, 10.4)
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from tryalma.form_populator.browser_controller import BrowserController
from tryalma.form_populator.exceptions import (
    BrowserError,
    NavigationError,
    FormNotFoundError,
)


class TestBrowserLifecycleManagement:
    """Tests for Task 2.1: Browser lifecycle management."""

    def test_context_manager_pattern_normal_exit(self):
        """BrowserController should support context manager for automatic cleanup.

        Requirements: 1.1, 1.5
        """
        controller = BrowserController()

        with patch.object(controller, "_create_browser") as mock_create:
            with patch.object(controller, "_close_browser") as mock_close:
                mock_browser = MagicMock()
                mock_create.return_value = mock_browser

                with controller.launch() as ctx:
                    assert ctx is controller
                    mock_create.assert_called_once()

                mock_close.assert_called_once()

    def test_context_manager_pattern_error_cleanup(self):
        """BrowserController should cleanup resources on error.

        Requirements: 1.5
        """
        controller = BrowserController()

        with patch.object(controller, "_create_browser") as mock_create:
            with patch.object(controller, "_close_browser") as mock_close:
                mock_browser = MagicMock()
                mock_create.return_value = mock_browser

                with pytest.raises(ValueError):
                    with controller.launch():
                        raise ValueError("Test error")

                mock_close.assert_called_once()

    def test_headless_mode_by_default(self):
        """BrowserController should launch in headless mode by default.

        Requirements: 1.2
        """
        controller = BrowserController()

        assert controller.headless is True

    def test_headed_mode_for_debug(self):
        """BrowserController should support headed mode for debug scenarios.

        Requirements: 1.3
        """
        controller = BrowserController(headless=False)

        assert controller.headless is False

    def test_configurable_timeout_with_default(self):
        """BrowserController should have configurable timeout with 30-second default.

        Requirements: 1.4
        """
        # Default timeout
        controller_default = BrowserController()
        assert controller_default.timeout_ms == 30000

        # Custom timeout
        controller_custom = BrowserController(timeout_ms=60000)
        assert controller_custom.timeout_ms == 60000

    def test_browser_initialization_failure_raises_browser_error(self):
        """BrowserController should raise BrowserError on initialization failure.

        Requirements: 1.5
        """
        controller = BrowserController()

        with patch.object(controller, "_create_browser") as mock_create:
            mock_create.side_effect = Exception("Browser binary not found")

            with pytest.raises(BrowserError) as exc_info:
                with controller.launch():
                    pass

            assert "launch" in exc_info.value.operation
            assert "Browser binary not found" in exc_info.value.reason

    def test_close_method_releases_resources(self):
        """BrowserController close() should release browser resources.

        Requirements: 1.5
        """
        controller = BrowserController()
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_browser = MagicMock()
        controller._browser = mock_browser
        controller._context = mock_context
        controller._page = mock_page

        controller.close()

        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        # After close, all resources should be None
        assert controller._page is None
        assert controller._context is None
        assert controller._browser is None

    def test_close_handles_missing_resources_gracefully(self):
        """BrowserController close() should handle missing resources.

        Requirements: 1.5
        """
        controller = BrowserController()
        controller._browser = None
        controller._context = None
        controller._page = None

        # Should not raise
        controller.close()


class TestPageNavigationAndFormReadiness:
    """Tests for Task 2.2: Page navigation and form readiness detection."""

    def test_navigate_to_provided_url(self):
        """BrowserController should navigate to provided form URL.

        Requirements: 2.1
        """
        controller = BrowserController()
        controller._page = MagicMock()

        controller.navigate("https://example.com/form")

        controller._page.goto.assert_called_once()
        call_args = controller._page.goto.call_args
        assert call_args[0][0] == "https://example.com/form"

    def test_navigate_with_configurable_wait_conditions(self):
        """BrowserController should support configurable wait conditions.

        Requirements: 2.1
        """
        controller = BrowserController()
        controller._page = MagicMock()

        controller.navigate("https://example.com/form", wait_until="networkidle")

        call_args = controller._page.goto.call_args
        assert call_args[1].get("wait_until") == "networkidle"

    def test_wait_for_form_ready_waits_for_interactive_elements(self):
        """BrowserController should wait for form elements to become interactive.

        Requirements: 2.2
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.wait_for_form_ready(form_selector="form#myform")

        controller._page.locator.assert_called_with("form#myform")
        mock_locator.wait_for.assert_called()

    def test_configurable_navigation_timeout(self):
        """BrowserController should support configurable navigation timeout.

        Requirements: 2.5
        """
        controller = BrowserController(timeout_ms=45000)
        controller._page = MagicMock()

        controller.navigate("https://example.com/form")

        call_args = controller._page.goto.call_args
        assert call_args[1].get("timeout") == 45000

    def test_navigation_failure_raises_navigation_error(self):
        """BrowserController should raise NavigationError on navigation failure.

        Requirements: 2.3
        """
        controller = BrowserController()
        controller._page = MagicMock()
        controller._page.goto.side_effect = Exception("net::ERR_CONNECTION_REFUSED")

        with pytest.raises(NavigationError) as exc_info:
            controller.navigate("https://unreachable.example.com")

        assert exc_info.value.url == "https://unreachable.example.com"
        assert "ERR_CONNECTION_REFUSED" in exc_info.value.reason

    def test_form_not_found_raises_form_not_found_error(self):
        """BrowserController should raise FormNotFoundError if form missing.

        Requirements: 2.4
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator
        mock_locator.wait_for.side_effect = Exception("Timeout waiting for element")

        with pytest.raises(FormNotFoundError) as exc_info:
            controller.wait_for_form_ready(form_selector="form#nonexistent")

        assert "form#nonexistent" in exc_info.value.missing_elements


class TestElementInteractionUtilities:
    """Tests for Task 2.3: Element interaction utilities."""

    def test_fill_clears_existing_content_and_enters_text(self):
        """BrowserController fill() should clear existing content and enter new text.

        Requirements: 4.1
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.fill("input[name='email']", "test@example.com")

        controller._page.locator.assert_called_with("input[name='email']")
        mock_locator.fill.assert_called_once_with("test@example.com")

    def test_type_slowly_character_by_character(self):
        """BrowserController type_slowly() should type character-by-character.

        Requirements: 4.2
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.type_slowly("input[name='name']", "John", delay_ms=50)

        controller._page.locator.assert_called_with("input[name='name']")
        mock_locator.press_sequentially.assert_called_once_with("John", delay=50)

    def test_check_method_for_checkbox(self):
        """BrowserController check() should check checkbox.

        Requirements: 6.1
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.check("input[name='agree']")

        controller._page.locator.assert_called_with("input[name='agree']")
        mock_locator.check.assert_called_once()

    def test_uncheck_method_for_checkbox(self):
        """BrowserController uncheck() should uncheck checkbox.

        Requirements: 6.2
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.uncheck("input[name='agree']")

        controller._page.locator.assert_called_with("input[name='agree']")
        mock_locator.uncheck.assert_called_once()

    def test_select_option_by_value(self):
        """BrowserController select_option() should support value selection.

        Requirements: 5.4
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.select_option("select[name='country']", value="US")

        controller._page.locator.assert_called_with("select[name='country']")
        mock_locator.select_option.assert_called_once_with(value="US")

    def test_select_option_by_label(self):
        """BrowserController select_option() should support label selection.

        Requirements: 5.4
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.select_option("select[name='country']", label="United States")

        mock_locator.select_option.assert_called_once_with(label="United States")

    def test_select_option_by_index(self):
        """BrowserController select_option() should support index selection.

        Requirements: 5.4
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator

        controller.select_option("select[name='country']", index=5)

        mock_locator.select_option.assert_called_once_with(index=5)

    def test_is_visible_returns_element_visibility(self):
        """BrowserController is_visible() should return element visibility state.

        Requirements: related to element inspection
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator
        mock_locator.is_visible.return_value = True

        result = controller.is_visible("input[name='email']")

        assert result is True
        mock_locator.is_visible.assert_called_once()

    def test_get_attribute_returns_element_attribute(self):
        """BrowserController get_attribute() should return element attribute value.

        Requirements: related to attribute inspection
        """
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator
        mock_locator.get_attribute.return_value = "20"

        result = controller.get_attribute("input[name='name']", "maxlength")

        assert result == "20"
        mock_locator.get_attribute.assert_called_once_with("maxlength")

    def test_capture_screenshot_saves_to_path(self):
        """BrowserController capture_screenshot() should save screenshot to path.

        Requirements: 10.4
        """
        controller = BrowserController()
        controller._page = MagicMock()
        screenshot_path = Path("/tmp/test_screenshot.png")

        controller.capture_screenshot(screenshot_path)

        controller._page.screenshot.assert_called_once_with(path=screenshot_path)

    def test_get_input_value_returns_current_value(self):
        """BrowserController get_input_value() should return current input value."""
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator
        mock_locator.input_value.return_value = "current text"

        result = controller.get_input_value("input[name='email']")

        assert result == "current text"

    def test_is_checked_returns_checkbox_state(self):
        """BrowserController is_checked() should return checkbox checked state."""
        controller = BrowserController()
        controller._page = MagicMock()
        mock_locator = MagicMock()
        controller._page.locator.return_value = mock_locator
        mock_locator.is_checked.return_value = True

        result = controller.is_checked("input[name='agree']")

        assert result is True
