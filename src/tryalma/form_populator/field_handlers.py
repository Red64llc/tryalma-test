"""Field population handlers for different form field types.

This module provides handler classes for populating various form field types:
- TextFieldHandler: Text inputs, textareas
- SelectFieldHandler: Dropdown/select elements
- CheckboxHandler: Checkboxes
- RadioHandler: Radio button groups
- DateFieldHandler: Date inputs

Each handler receives a BrowserController instance and uses it to interact
with form fields. Handlers do NOT launch browsers - they expect an already
configured browser controller.

Requirements Coverage:
- 4.1-4.5: Text field population
- 5.1-5.5: Dropdown selection
- 6.1-6.5: Checkbox and radio button handling
- 7.1-7.5: Date field population
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

from tryalma.form_populator.models import FieldResult, FieldStatus

if TYPE_CHECKING:
    from tryalma.form_populator.browser_controller import BrowserController

logger = logging.getLogger(__name__)


# =============================================================================
# Text Field Handler (Task 4.1)
# =============================================================================


@dataclass(frozen=True)
class TextFieldConfig:
    """Configuration for text field population.

    Attributes:
        simulate_typing: Whether to type character-by-character (default False).
        typing_delay_ms: Delay between keystrokes in milliseconds (default 50).
        respect_maxlength: Whether to truncate to maxlength attribute (default True).

    Requirements: 4.2, 4.3
    """

    simulate_typing: bool = False
    typing_delay_ms: int = 50
    respect_maxlength: bool = True


class TextFieldHandler:
    """Handler for text input field population.

    Provides methods to populate text fields with proper clearing,
    optional human-like typing, maxlength respect, and phone formatting.

    Requirements: 4.1-4.5
    """

    def __init__(self, browser: BrowserController) -> None:
        """Initialize TextFieldHandler.

        Args:
            browser: BrowserController instance for browser interactions.
        """
        self._browser = browser

    def populate(
        self,
        selector: str,
        value: str,
        config: TextFieldConfig | None = None,
    ) -> FieldResult:
        """Populate text input field.

        Clears existing content before entering new data.
        Optionally types character-by-character for human simulation.
        Respects maxlength attribute when configured.

        Args:
            selector: CSS selector for input element.
            value: Text value to enter.
            config: Optional configuration overrides.

        Returns:
            FieldResult with population status.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        if config is None:
            config = TextFieldConfig()

        try:
            # Get maxlength attribute and truncate if needed
            final_value = value
            if config.respect_maxlength:
                maxlength = self._browser.get_attribute(selector, "maxlength")
                if maxlength is not None:
                    try:
                        max_len = int(maxlength)
                        final_value = value[:max_len]
                    except ValueError:
                        pass  # Invalid maxlength, ignore

            # Populate using appropriate method
            if config.simulate_typing:
                self._browser.type_slowly(
                    selector, final_value, delay_ms=config.typing_delay_ms
                )
            else:
                self._browser.fill(selector, final_value)

            return FieldResult(
                field_id="",  # Will be set by caller
                status=FieldStatus.POPULATED,
                value=final_value,
                selector=selector,
            )
        except Exception as e:
            logger.error("Failed to populate text field %s: %s", selector, str(e))
            return FieldResult(
                field_id="",
                status=FieldStatus.ERROR,
                value=value,
                error_message=str(e),
                selector=selector,
            )

    def format_phone(self, value: str, pattern: str = "###-###-####") -> str:
        """Format phone number according to pattern.

        Extracts digits from input and formats according to the pattern.
        Pattern uses '#' as digit placeholder.

        Args:
            value: Phone number string (may contain non-digits).
            pattern: Format pattern (default "###-###-####").

        Returns:
            Formatted phone number string.

        Requirements: 4.5
        """
        if not value:
            return ""

        # Extract digits only
        digits = re.sub(r"\D", "", value)
        if not digits:
            return ""

        # Build formatted string from pattern
        result = []
        digit_index = 0
        for char in pattern:
            if digit_index >= len(digits):
                break
            if char == "#":
                result.append(digits[digit_index])
                digit_index += 1
            else:
                result.append(char)

        return "".join(result)


# =============================================================================
# Select Field Handler (Task 4.2)
# =============================================================================


class SelectStrategy(Enum):
    """Strategy for matching dropdown options.

    Requirements: 5.4
    """

    VALUE = "value"
    LABEL = "label"
    INDEX = "index"


# US State abbreviation to full name mapping
US_STATES: dict[str, str] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

# Reverse mapping: full name to abbreviation
US_STATES_REVERSE: dict[str, str] = {v.upper(): k for k, v in US_STATES.items()}

# Common country name variations
COUNTRY_NORMALIZATIONS: dict[str, str] = {
    "USA": "United States",
    "US": "United States",
    "U.S.": "United States",
    "U.S.A.": "United States",
    "UNITED STATES OF AMERICA": "United States",
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "GREAT BRITAIN": "United Kingdom",
    "ENGLAND": "United Kingdom",
}


class SelectFieldHandler:
    """Handler for dropdown/select field population.

    Provides methods to select dropdown options using various matching
    strategies with case-insensitive fallback.

    Requirements: 5.1-5.5
    """

    def __init__(self, browser: BrowserController) -> None:
        """Initialize SelectFieldHandler.

        Args:
            browser: BrowserController instance for browser interactions.
        """
        self._browser = browser

    def populate(
        self,
        selector: str,
        value: str,
        strategies: list[SelectStrategy] | None = None,
    ) -> FieldResult:
        """Select dropdown option using cascading match strategies.

        Attempts to match the value using the specified strategies in order.
        Falls back to case-insensitive matching when exact match fails.

        Args:
            selector: CSS selector for select element.
            value: Value to match against options.
            strategies: Ordered list of matching strategies to try.
                       Defaults to [VALUE, LABEL].

        Returns:
            FieldResult with selection status.

        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        if strategies is None:
            strategies = [SelectStrategy.VALUE, SelectStrategy.LABEL]

        for strategy in strategies:
            try:
                if strategy == SelectStrategy.VALUE:
                    self._browser.select_option(selector, value=value)
                elif strategy == SelectStrategy.LABEL:
                    self._browser.select_option(selector, label=value)
                elif strategy == SelectStrategy.INDEX:
                    self._browser.select_option(selector, index=int(value))

                return FieldResult(
                    field_id="",
                    status=FieldStatus.POPULATED,
                    value=value,
                    selector=selector,
                )
            except Exception:
                continue  # Try next strategy

        # All strategies failed - log warning
        logger.warning(
            "No matching option found for dropdown %s with value '%s'",
            selector,
            value,
        )
        return FieldResult(
            field_id="",
            status=FieldStatus.ERROR,
            value=value,
            error_message=f"No matching option found for value: {value}",
            selector=selector,
        )

    def normalize_state(self, value: str) -> str:
        """Normalize state name/abbreviation for matching.

        Converts state abbreviations to full names and vice versa.

        Args:
            value: State name or abbreviation.

        Returns:
            Normalized state name.

        Requirements: 5.5
        """
        upper_value = value.upper().strip()

        # Check if it's an abbreviation
        if upper_value in US_STATES:
            return US_STATES[upper_value]

        # Check if it's a full name
        if upper_value in US_STATES_REVERSE:
            return value.strip()  # Return original casing

        # Return as-is if not recognized
        return value.strip()

    def normalize_country(self, value: str) -> str:
        """Normalize country name for matching.

        Handles common country name variations and abbreviations.

        Args:
            value: Country name or abbreviation.

        Returns:
            Normalized country name.

        Requirements: 5.5
        """
        upper_value = value.upper().strip()

        if upper_value in COUNTRY_NORMALIZATIONS:
            return COUNTRY_NORMALIZATIONS[upper_value]

        return value.strip()


# =============================================================================
# Checkbox Handler (Task 4.3)
# =============================================================================


class CheckboxHandler:
    """Handler for checkbox field population.

    Provides methods to check/uncheck checkboxes based on truthy/falsy values
    and support for checkbox groups.

    Requirements: 6.1, 6.2, 6.5
    """

    def __init__(self, browser: BrowserController) -> None:
        """Initialize CheckboxHandler.

        Args:
            browser: BrowserController instance for browser interactions.
        """
        self._browser = browser

    def populate(self, selector: str, checked: bool) -> FieldResult:
        """Set checkbox state.

        Args:
            selector: CSS selector for checkbox element.
            checked: Desired checked state.

        Returns:
            FieldResult with status.

        Requirements: 6.1, 6.2
        """
        try:
            if checked:
                self._browser.check(selector)
            else:
                self._browser.uncheck(selector)

            return FieldResult(
                field_id="",
                status=FieldStatus.POPULATED,
                value=str(checked),
                selector=selector,
            )
        except Exception as e:
            logger.error("Failed to set checkbox %s: %s", selector, str(e))
            return FieldResult(
                field_id="",
                status=FieldStatus.ERROR,
                value=str(checked),
                error_message=str(e),
                selector=selector,
            )

    def populate_group(
        self,
        selectors: list[tuple[str, bool]],
    ) -> list[FieldResult]:
        """Set multiple checkbox states in a group.

        Args:
            selectors: List of (selector, checked) tuples.

        Returns:
            List of FieldResult for each checkbox.

        Requirements: 6.5
        """
        results = []
        for selector, checked in selectors:
            result = self.populate(selector, checked)
            results.append(result)
        return results


# =============================================================================
# Radio Button Handler (Task 4.4)
# =============================================================================


class RadioHandler:
    """Handler for radio button group selection.

    Provides methods to select radio buttons by value or label text.

    Requirements: 6.3, 6.4
    """

    def __init__(self, browser: BrowserController) -> None:
        """Initialize RadioHandler.

        Args:
            browser: BrowserController instance for browser interactions.
        """
        self._browser = browser

    def populate(self, group_name: str, value: str) -> FieldResult:
        """Select radio button in group by value.

        Args:
            group_name: Name attribute of radio group.
            value: Value to select.

        Returns:
            FieldResult with selection status.

        Requirements: 6.3
        """
        selector = f"input[name='{group_name}'][value='{value}']"
        try:
            self._browser.check(selector)
            return FieldResult(
                field_id="",
                status=FieldStatus.POPULATED,
                value=value,
                selector=selector,
            )
        except Exception as e:
            logger.warning(
                "No matching radio option found for group '%s' with value '%s': %s",
                group_name,
                value,
                str(e),
            )
            return FieldResult(
                field_id="",
                status=FieldStatus.ERROR,
                value=value,
                error_message=f"No matching radio option found: {str(e)}",
                selector=selector,
            )

    def populate_by_label(self, group_name: str, label_text: str) -> FieldResult:
        """Select radio button by associated label text.

        Uses case-insensitive matching for label text.

        Args:
            group_name: Name attribute of radio group.
            label_text: Label text to match (case-insensitive).

        Returns:
            FieldResult with selection status.

        Requirements: 6.3, 6.4
        """
        # Try to find radio by label text using Playwright's label selector
        selector = f"input[name='{group_name}']"
        try:
            # Use label text matching via XPath or text selector
            label_selector = f"label:has-text('{label_text}') input[name='{group_name}']"
            self._browser.check(label_selector)
            return FieldResult(
                field_id="",
                status=FieldStatus.POPULATED,
                value=label_text,
                selector=label_selector,
            )
        except Exception:
            # Try alternative: find label for attribute
            try:
                # Fallback: try direct input with similar value
                self._browser.check(f"input[name='{group_name}'][value='{label_text}']")
                return FieldResult(
                    field_id="",
                    status=FieldStatus.POPULATED,
                    value=label_text,
                    selector=f"input[name='{group_name}'][value='{label_text}']",
                )
            except Exception as e:
                logger.warning(
                    "No matching radio option found for group '%s' with label '%s'",
                    group_name,
                    label_text,
                )
                return FieldResult(
                    field_id="",
                    status=FieldStatus.ERROR,
                    value=label_text,
                    error_message=f"No matching radio option found for label: {label_text}",
                    selector=selector,
                )


# =============================================================================
# Date Field Handler (Task 4.5)
# =============================================================================


class DateFormat(Enum):
    """Date format enumeration.

    Requirements: 7.2
    """

    ISO = "YYYY-MM-DD"  # 2024-01-15
    US = "MM/DD/YYYY"  # 01/15/2024
    EU = "DD/MM/YYYY"  # 15/01/2024


class DateFieldHandler:
    """Handler for date field population.

    Provides methods to parse dates from multiple formats, convert to
    the form's expected format, and interact with date picker widgets.

    Requirements: 7.1-7.5
    """

    def __init__(self, browser: BrowserController) -> None:
        """Initialize DateFieldHandler.

        Args:
            browser: BrowserController instance for browser interactions.
        """
        self._browser = browser

    def populate(
        self,
        selector: str,
        value: str | date,
        target_format: DateFormat = DateFormat.US,
    ) -> FieldResult:
        """Populate date field with formatted value.

        Parses the input value, converts to target format, and enters into field.

        Args:
            selector: CSS selector for date input.
            value: Date as string or date object.
            target_format: Format expected by the form (default US).

        Returns:
            FieldResult with population status.

        Requirements: 7.1, 7.2, 7.4
        """
        try:
            # Parse date if string
            if isinstance(value, str):
                parsed_date = self.parse_date(value)
            else:
                parsed_date = value

            # Format to target format
            formatted = self.format_date(parsed_date, target_format)

            # Try to enter the date
            self._browser.fill(selector, formatted)

            return FieldResult(
                field_id="",
                status=FieldStatus.POPULATED,
                value=formatted,
                selector=selector,
            )
        except ValueError as e:
            logger.error(
                "Date conversion failed for value '%s' to format %s: %s",
                value,
                target_format.value,
                str(e),
            )
            return FieldResult(
                field_id="",
                status=FieldStatus.ERROR,
                value=str(value),
                error_message=f"Date conversion failed: {str(e)}",
                selector=selector,
            )
        except Exception as e:
            logger.error("Failed to populate date field %s: %s", selector, str(e))
            return FieldResult(
                field_id="",
                status=FieldStatus.ERROR,
                value=str(value),
                error_message=str(e),
                selector=selector,
            )

    def parse_date(self, value: str) -> date:
        """Parse date string with flexible format detection.

        Supports ISO (YYYY-MM-DD), US (MM/DD/YYYY), EU (DD/MM/YYYY),
        and various text-based formats.

        When format is ambiguous (e.g., 01/02/2024), defaults to ISO
        interpretation if possible, otherwise US.

        Args:
            value: Date string in various formats.

        Returns:
            Parsed date object.

        Raises:
            ValueError: If date cannot be parsed.

        Requirements: 7.2, 7.3
        """
        value = value.strip()
        if not value:
            raise ValueError("Empty date string")

        # Try ISO format first (YYYY-MM-DD)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            parts = value.split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))

        # Try slash-separated format (MM/DD/YYYY or DD/MM/YYYY)
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", value):
            parts = value.split("/")
            first_num = int(parts[0])
            second_num = int(parts[1])
            year = int(parts[2])
            # If first number > 12, it must be EU format (day first)
            if first_num > 12:
                return date(year, second_num, first_num)  # EU: DD/MM/YYYY
            # Otherwise assume US format
            return date(year, first_num, second_num)  # US: MM/DD/YYYY

        # Try date with dashes (MM-DD-YYYY)
        if re.match(r"^\d{1,2}-\d{1,2}-\d{4}$", value):
            parts = value.split("-")
            return date(int(parts[2]), int(parts[0]), int(parts[1]))

        # Try ISO without separators (YYYYMMDD)
        if re.match(r"^\d{8}$", value):
            return date(int(value[:4]), int(value[4:6]), int(value[6:8]))

        # Try text formats like "January 15, 2024" or "15 January 2024"
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }

        # Match "Month Day, Year"
        match = re.match(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", value, re.IGNORECASE)
        if match:
            month_str, day_str, year_str = match.groups()
            month_lower = month_str.lower()
            if month_lower in months:
                return date(int(year_str), months[month_lower], int(day_str))

        # Match "Day Month Year"
        match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", value, re.IGNORECASE)
        if match:
            day_str, month_str, year_str = match.groups()
            month_lower = month_str.lower()
            if month_lower in months:
                return date(int(year_str), months[month_lower], int(day_str))

        raise ValueError(f"Cannot parse date: {value}")

    def format_date(self, d: date, target: DateFormat) -> str:
        """Format date object to target format string.

        Args:
            d: Date object to format.
            target: Target date format.

        Returns:
            Formatted date string.

        Requirements: 7.1, 7.2
        """
        if target == DateFormat.ISO:
            return d.strftime("%Y-%m-%d")
        elif target == DateFormat.US:
            return d.strftime("%m/%d/%Y")
        elif target == DateFormat.EU:
            return d.strftime("%d/%m/%Y")
        else:
            return d.strftime("%Y-%m-%d")  # Default to ISO
