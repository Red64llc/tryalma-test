"""Browser controller for Playwright-based browser automation.

This module provides a clean abstraction over Playwright's browser/page objects
for form population operations. Supports context manager pattern for automatic
resource cleanup.

Requirements Coverage:
- 1.1-1.5: Browser automation setup
- 2.1-2.5: Form navigation
- 4.1, 4.2: Text field population
- 5.4: Dropdown selection
- 6.1, 6.2: Checkbox handling
- 10.4: Screenshot capture for debugging
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Generator

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from tryalma.form_populator.exceptions import (
    BrowserError,
    NavigationError,
    FormNotFoundError,
)

if TYPE_CHECKING:
    pass


class BrowserController:
    """Abstraction over Playwright browser operations.

    Provides context manager pattern for automatic browser lifecycle management
    and clean interface for form population operations.

    Attributes:
        headless: Whether to run browser in headless mode (default True).
        timeout_ms: Default timeout for operations in milliseconds (default 30000).
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        timeout_ms: int = 30000,
    ) -> None:
        """Initialize BrowserController.

        Args:
            headless: Run in headless mode (default True).
            timeout_ms: Default timeout for operations (default 30000).
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @contextmanager
    def launch(self) -> Generator[BrowserController, None, None]:
        """Launch browser as context manager.

        Yields:
            Self for method chaining.

        Raises:
            BrowserError: If browser fails to launch.
        """
        try:
            self._create_browser()
        except BrowserError:
            raise
        except Exception as e:
            raise BrowserError(operation="launch", reason=str(e))

        try:
            yield self
        finally:
            self._close_browser()

    def _create_browser(self) -> Browser:
        """Create and configure browser instance.

        Returns:
            Configured Browser instance.

        Raises:
            Exception: If browser creation fails.
        """
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        return self._browser

    def _close_browser(self) -> None:
        """Close browser and clean up resources."""
        if self._page is not None:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def close(self) -> None:
        """Close browser and clean up resources.

        Safe to call multiple times or when resources don't exist.
        """
        self._close_browser()

    def navigate(
        self,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
    ) -> None:
        """Navigate to URL and wait for page load.

        Args:
            url: Target URL.
            wait_until: Load state to wait for (default 'domcontentloaded').

        Raises:
            NavigationError: If navigation fails or times out.
        """
        if self._page is None:
            raise BrowserError(operation="navigate", reason="Browser not launched")

        try:
            self._page.goto(url, wait_until=wait_until, timeout=self.timeout_ms)
        except Exception as e:
            raise NavigationError(url=url, reason=str(e))

    def wait_for_form_ready(
        self,
        form_selector: str = "form",
        timeout_ms: int | None = None,
    ) -> None:
        """Wait for form elements to be interactive.

        Args:
            form_selector: CSS selector for form container.
            timeout_ms: Override default timeout.

        Raises:
            FormNotFoundError: If form not found within timeout.
        """
        if self._page is None:
            raise BrowserError(
                operation="wait_for_form_ready", reason="Browser not launched"
            )

        timeout = timeout_ms if timeout_ms is not None else self.timeout_ms

        # Try multiple selectors if comma-separated
        selectors = [s.strip() for s in form_selector.split(",")]

        print(f"[DEBUG] Waiting for form ready, trying selectors: {selectors}")
        print(f"[DEBUG] Current URL: {self._page.url}")

        for selector in selectors:
            try:
                print(f"[DEBUG] Trying selector: {selector}")
                locator = self._page.locator(selector).first
                locator.wait_for(state="visible", timeout=min(timeout, 10000))
                print(f"[DEBUG] Found element with selector: {selector}")
                return  # Found one, we're good
            except Exception as e:
                print(f"[DEBUG] Selector {selector} failed: {e}")
                continue  # Try next selector

        # If none worked, raise error
        raise FormNotFoundError(missing_elements=[form_selector])

    def fill(self, selector: str, value: str) -> None:
        """Fill text input field, clearing existing content first.

        Args:
            selector: CSS selector for input element.
            value: Text value to enter.
        """
        if self._page is None:
            raise BrowserError(operation="fill", reason="Browser not launched")

        # Use .first to handle cases where selector matches multiple elements
        locator = self._page.locator(selector).first
        locator.fill(value)

    def type_slowly(
        self,
        selector: str,
        value: str,
        delay_ms: int = 50,
    ) -> None:
        """Type text character-by-character to simulate human input.

        Args:
            selector: CSS selector for input element.
            value: Text value to type.
            delay_ms: Delay between keystrokes in milliseconds.
        """
        if self._page is None:
            raise BrowserError(operation="type_slowly", reason="Browser not launched")

        locator = self._page.locator(selector)
        locator.press_sequentially(value, delay=delay_ms)

    def check(self, selector: str) -> None:
        """Check checkbox or radio button.

        Args:
            selector: CSS selector for checkbox/radio element.
        """
        if self._page is None:
            raise BrowserError(operation="check", reason="Browser not launched")

        # Use .first to handle cases where selector matches multiple elements
        locator = self._page.locator(selector).first
        locator.check()

    def uncheck(self, selector: str) -> None:
        """Uncheck checkbox.

        Args:
            selector: CSS selector for checkbox element.
        """
        if self._page is None:
            raise BrowserError(operation="uncheck", reason="Browser not launched")

        locator = self._page.locator(selector)
        locator.uncheck()

    def select_option(
        self,
        selector: str,
        *,
        value: str | None = None,
        label: str | None = None,
        index: int | None = None,
    ) -> None:
        """Select dropdown option.

        Args:
            selector: CSS selector for select element.
            value: Option value attribute.
            label: Option visible text.
            index: Option index (0-based).
        """
        if self._page is None:
            raise BrowserError(operation="select_option", reason="Browser not launched")

        # Use .first to handle cases where selector matches multiple elements
        locator = self._page.locator(selector).first

        if value is not None:
            locator.select_option(value=value)
        elif label is not None:
            locator.select_option(label=label)
        elif index is not None:
            locator.select_option(index=index)
        else:
            raise ValueError(
                "select_option requires one of: value, label, or index"
            )

    def get_input_value(self, selector: str) -> str:
        """Read current value of input field.

        Args:
            selector: CSS selector for input element.

        Returns:
            Current value of the input field.
        """
        if self._page is None:
            raise BrowserError(
                operation="get_input_value", reason="Browser not launched"
            )

        locator = self._page.locator(selector)
        return locator.input_value()

    def is_checked(self, selector: str) -> bool:
        """Check if checkbox/radio is checked.

        Args:
            selector: CSS selector for checkbox/radio element.

        Returns:
            True if checked, False otherwise.
        """
        if self._page is None:
            raise BrowserError(operation="is_checked", reason="Browser not launched")

        locator = self._page.locator(selector)
        return locator.is_checked()

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible.

        Args:
            selector: CSS selector for element.

        Returns:
            True if visible, False otherwise.
        """
        if self._page is None:
            raise BrowserError(operation="is_visible", reason="Browser not launched")

        locator = self._page.locator(selector)
        return locator.is_visible()

    def get_attribute(self, selector: str, name: str) -> str | None:
        """Get element attribute value.

        Args:
            selector: CSS selector for element.
            name: Attribute name.

        Returns:
            Attribute value or None if not present.
        """
        if self._page is None:
            raise BrowserError(operation="get_attribute", reason="Browser not launched")

        # Use .first to handle cases where selector matches multiple elements
        locator = self._page.locator(selector).first
        return locator.get_attribute(name)

    def capture_screenshot(self, path: Path) -> None:
        """Capture page screenshot for debugging.

        Args:
            path: File path to save screenshot.
        """
        if self._page is None:
            raise BrowserError(
                operation="capture_screenshot", reason="Browser not launched"
            )

        self._page.screenshot(path=path)
