"""Exception hierarchy for form population errors.

This module defines specialized exceptions for form population operations,
all extending ProcessingError to integrate with existing CLI error handling.
"""

from tryalma.exceptions import ProcessingError


class FormPopulationError(ProcessingError):
    """Base exception for form population errors.

    Extends ProcessingError (exit code 3) to integrate with CLI error handling.
    """

    message: str = "Form population failed"


class NavigationError(FormPopulationError):
    """Failed to navigate to form URL.

    Attributes:
        url: The URL that could not be reached.
        reason: Description of the navigation failure.
    """

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Navigation to {url} failed: {reason}")


class FormNotFoundError(FormPopulationError):
    """Expected form elements not found on page.

    Attributes:
        missing_elements: List of CSS selectors or element descriptions
                          that were not found on the page.
    """

    def __init__(self, missing_elements: list[str]) -> None:
        self.missing_elements = missing_elements
        if missing_elements:
            elements_str = ", ".join(missing_elements)
            super().__init__(f"Form elements not found: {elements_str}")
        else:
            super().__init__("Form elements not found")


class BrowserError(FormPopulationError):
    """Browser operation failed.

    Attributes:
        operation: The browser operation that failed (e.g., 'launch', 'click').
        reason: Description of the failure.
    """

    def __init__(self, operation: str, reason: str) -> None:
        self.operation = operation
        self.reason = reason
        super().__init__(f"Browser {operation} failed: {reason}")


class PageNavigationError(FormPopulationError):
    """Page unexpectedly navigated away during population.

    Raised when the page URL changes unexpectedly during form population,
    such as from redirects or JavaScript navigation.
    """

    message: str = "Page unexpectedly navigated away during form population"
