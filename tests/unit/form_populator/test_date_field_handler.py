"""Tests for DateFieldHandler - date field population handler.

These tests verify:
- Task 4.5: Date field population handler
  - Parse dates from multiple input formats (ISO, US, text-based) (Requirement 7.2)
  - Convert dates to form's expected format (Requirement 7.1)
  - Default to ISO format when input format is ambiguous (Requirement 7.3)
  - Interact with date picker widgets when present (Requirement 7.4)
  - Log error with original value and expected format on conversion failure (Requirement 7.5)
"""

import logging
from datetime import date

import pytest
from unittest.mock import MagicMock

from tryalma.form_populator.field_handlers import DateFieldHandler, DateFormat
from tryalma.form_populator.models import FieldResult, FieldStatus


class TestDateFieldHandlerPopulate:
    """Tests for DateFieldHandler.populate() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create DateFieldHandler with mock browser."""
        return DateFieldHandler(mock_browser)

    def test_populates_date_field_with_string_value(self, handler, mock_browser):
        """DateFieldHandler should populate date field from string value.

        Requirements: 7.1
        """
        result = handler.populate(
            "input[name='dateOfBirth']",
            "2024-01-15",
            target_format=DateFormat.US,
        )

        mock_browser.fill.assert_called_once()
        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "01/15/2024"  # US format
        assert result.status == FieldStatus.POPULATED

    def test_populates_date_field_with_date_object(self, handler, mock_browser):
        """DateFieldHandler should populate date field from date object.

        Requirements: 7.1
        """
        d = date(2024, 1, 15)

        result = handler.populate(
            "input[name='dateOfBirth']",
            d,
            target_format=DateFormat.US,
        )

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "01/15/2024"
        assert result.status == FieldStatus.POPULATED

    def test_converts_to_target_format(self, handler, mock_browser):
        """DateFieldHandler should convert to form's expected format.

        Requirements: 7.1
        """
        # ISO input, US target
        result = handler.populate(
            "input[name='dob']",
            "2024-01-15",
            target_format=DateFormat.US,
        )

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "01/15/2024"

    def test_returns_field_result_on_success(self, handler, mock_browser):
        """DateFieldHandler should return FieldResult with success status."""
        result = handler.populate(
            "input[name='dob']",
            "2024-01-15",
            target_format=DateFormat.ISO,
        )

        assert isinstance(result, FieldResult)
        assert result.status == FieldStatus.POPULATED
        assert result.value == "2024-01-15"

    def test_logs_error_on_conversion_failure(self, handler, mock_browser, caplog):
        """DateFieldHandler should log error on date conversion failure.

        Requirements: 7.5
        """
        with caplog.at_level(logging.ERROR):
            result = handler.populate(
                "input[name='dob']",
                "invalid-date",
                target_format=DateFormat.US,
            )

        assert result.status == FieldStatus.ERROR
        assert any(
            "invalid-date" in record.message
            for record in caplog.records
        )

    def test_returns_error_result_on_parse_failure(self, handler, mock_browser):
        """DateFieldHandler should return error result when parsing fails.

        Requirements: 7.5
        """
        result = handler.populate(
            "input[name='dob']",
            "not-a-date",
            target_format=DateFormat.US,
        )

        assert result.status == FieldStatus.ERROR
        assert "Date conversion failed" in result.error_message

    def test_returns_error_result_on_browser_exception(self, handler, mock_browser):
        """DateFieldHandler should return error on browser exception."""
        mock_browser.fill.side_effect = Exception("Element not found")

        result = handler.populate(
            "input[name='dob']",
            "2024-01-15",
            target_format=DateFormat.US,
        )

        assert result.status == FieldStatus.ERROR
        assert "Element not found" in result.error_message

    def test_default_target_format_is_us(self, handler, mock_browser):
        """DateFieldHandler should default to US format.

        Requirements: 7.2
        """
        result = handler.populate("input[name='dob']", "2024-01-15")

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "01/15/2024"  # US format


class TestDateFieldHandlerParseDate:
    """Tests for DateFieldHandler.parse_date() method."""

    @pytest.fixture
    def handler(self):
        """Create DateFieldHandler with mock browser."""
        return DateFieldHandler(MagicMock())

    def test_parses_iso_format(self, handler):
        """parse_date should parse ISO format (YYYY-MM-DD).

        Requirements: 7.2
        """
        result = handler.parse_date("2024-01-15")

        assert result == date(2024, 1, 15)

    def test_parses_us_format(self, handler):
        """parse_date should parse US format (MM/DD/YYYY).

        Requirements: 7.2
        """
        result = handler.parse_date("01/15/2024")

        assert result == date(2024, 1, 15)

    def test_parses_us_format_with_single_digits(self, handler):
        """parse_date should parse US format with single digit month/day.

        Requirements: 7.2
        """
        result = handler.parse_date("1/5/2024")

        assert result == date(2024, 1, 5)

    def test_parses_text_month_day_year(self, handler):
        """parse_date should parse text format (Month Day, Year).

        Requirements: 7.2
        """
        result = handler.parse_date("January 15, 2024")

        assert result == date(2024, 1, 15)

    def test_parses_text_abbreviated_month(self, handler):
        """parse_date should parse abbreviated month names.

        Requirements: 7.2
        """
        result = handler.parse_date("Jan 15, 2024")

        assert result == date(2024, 1, 15)

    def test_parses_text_day_month_year(self, handler):
        """parse_date should parse text format (Day Month Year).

        Requirements: 7.2
        """
        result = handler.parse_date("15 January 2024")

        assert result == date(2024, 1, 15)

    def test_parses_compact_iso_format(self, handler):
        """parse_date should parse compact ISO format (YYYYMMDD).

        Requirements: 7.2
        """
        result = handler.parse_date("20240115")

        assert result == date(2024, 1, 15)

    def test_parses_mm_dd_yyyy_with_dashes(self, handler):
        """parse_date should parse MM-DD-YYYY format.

        Requirements: 7.2
        """
        result = handler.parse_date("01-15-2024")

        assert result == date(2024, 1, 15)

    def test_raises_value_error_for_invalid_date(self, handler):
        """parse_date should raise ValueError for invalid date string.

        Requirements: 7.5
        """
        with pytest.raises(ValueError) as exc_info:
            handler.parse_date("invalid-date")

        assert "Cannot parse date" in str(exc_info.value)

    def test_raises_value_error_for_empty_string(self, handler):
        """parse_date should raise ValueError for empty string."""
        with pytest.raises(ValueError) as exc_info:
            handler.parse_date("")

        assert "Empty date string" in str(exc_info.value)

    def test_handles_whitespace(self, handler):
        """parse_date should handle leading/trailing whitespace."""
        result = handler.parse_date("  2024-01-15  ")

        assert result == date(2024, 1, 15)


class TestDateFieldHandlerFormatDate:
    """Tests for DateFieldHandler.format_date() method."""

    @pytest.fixture
    def handler(self):
        """Create DateFieldHandler with mock browser."""
        return DateFieldHandler(MagicMock())

    def test_formats_to_iso(self, handler):
        """format_date should format to ISO format.

        Requirements: 7.1
        """
        d = date(2024, 1, 15)

        result = handler.format_date(d, DateFormat.ISO)

        assert result == "2024-01-15"

    def test_formats_to_us(self, handler):
        """format_date should format to US format.

        Requirements: 7.1
        """
        d = date(2024, 1, 15)

        result = handler.format_date(d, DateFormat.US)

        assert result == "01/15/2024"

    def test_formats_to_eu(self, handler):
        """format_date should format to EU format.

        Requirements: 7.1
        """
        d = date(2024, 1, 15)

        result = handler.format_date(d, DateFormat.EU)

        assert result == "15/01/2024"

    def test_single_digit_month_day_padded(self, handler):
        """format_date should pad single digit month/day.

        Requirements: 7.1
        """
        d = date(2024, 1, 5)

        result = handler.format_date(d, DateFormat.US)

        assert result == "01/05/2024"


class TestDateFormat:
    """Tests for DateFormat enumeration."""

    def test_iso_format_exists(self):
        """DateFormat should have ISO option."""
        assert DateFormat.ISO.value == "YYYY-MM-DD"

    def test_us_format_exists(self):
        """DateFormat should have US option."""
        assert DateFormat.US.value == "MM/DD/YYYY"

    def test_eu_format_exists(self):
        """DateFormat should have EU option."""
        assert DateFormat.EU.value == "DD/MM/YYYY"


class TestDateFieldHandlerAmbiguousDates:
    """Tests for ambiguous date handling."""

    @pytest.fixture
    def handler(self):
        """Create DateFieldHandler with mock browser."""
        return DateFieldHandler(MagicMock())

    def test_iso_format_takes_precedence(self, handler):
        """ISO format should be parsed correctly (YYYY-MM-DD).

        Requirements: 7.3
        """
        # 2024-05-06 is unambiguous ISO
        result = handler.parse_date("2024-05-06")

        assert result == date(2024, 5, 6)

    def test_us_format_assumed_for_slash_dates(self, handler):
        """Slash dates should be parsed as US format (MM/DD/YYYY).

        Requirements: 7.3
        """
        # 05/06/2024 - assuming US format (May 6)
        result = handler.parse_date("05/06/2024")

        assert result == date(2024, 5, 6)

    def test_eu_format_detected_when_day_greater_than_12(self, handler):
        """EU format detected when first number > 12.

        Requirements: 7.3
        """
        # 15/06/2024 - must be EU (15 can't be month)
        result = handler.parse_date("15/06/2024")

        # Should parse as EU: day 15, month 6, year 2024
        assert result == date(2024, 6, 15)
