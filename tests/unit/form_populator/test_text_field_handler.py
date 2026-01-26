"""Tests for TextFieldHandler - text input field population.

These tests verify:
- Task 4.1: Text field population handler
  - Clear existing content before entering new data (Requirement 4.1)
  - Support optional character-by-character typing for human simulation (Requirement 4.2)
  - Detect and respect maxlength attribute, truncate input accordingly (Requirement 4.3)
  - Handle special characters without corruption or encoding issues (Requirement 4.4)
  - Format phone numbers according to expected pattern (Requirement 4.5)
"""

import pytest
from unittest.mock import MagicMock

from tryalma.form_populator.field_handlers import TextFieldHandler, TextFieldConfig
from tryalma.form_populator.models import FieldResult, FieldStatus


class TestTextFieldHandlerPopulate:
    """Tests for TextFieldHandler.populate() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        browser = MagicMock()
        browser.get_attribute.return_value = None  # No maxlength by default
        return browser

    @pytest.fixture
    def handler(self, mock_browser):
        """Create TextFieldHandler with mock browser."""
        return TextFieldHandler(mock_browser)

    def test_clears_existing_content_before_entering_new_data(
        self, handler, mock_browser
    ):
        """TextFieldHandler should clear existing content before entering new text.

        Requirements: 4.1
        """
        result = handler.populate("input[name='email']", "test@example.com")

        mock_browser.fill.assert_called_once()
        call_args = mock_browser.fill.call_args
        assert call_args[0][0] == "input[name='email']"
        assert call_args[0][1] == "test@example.com"

    def test_returns_field_result_on_success(self, handler, mock_browser):
        """TextFieldHandler should return FieldResult with success status.

        Requirements: 4.1
        """
        result = handler.populate("input[name='email']", "test@example.com")

        assert isinstance(result, FieldResult)
        assert result.status == FieldStatus.POPULATED
        assert result.value == "test@example.com"

    def test_supports_character_by_character_typing(self, handler, mock_browser):
        """TextFieldHandler should support character-by-character typing for human simulation.

        Requirements: 4.2
        """
        config = TextFieldConfig(simulate_typing=True, typing_delay_ms=50)

        result = handler.populate(
            "input[name='name']", "John Doe", config=config
        )

        mock_browser.type_slowly.assert_called_once()
        call_args = mock_browser.type_slowly.call_args
        assert call_args[0][0] == "input[name='name']"
        assert call_args[0][1] == "John Doe"
        assert call_args[1]["delay_ms"] == 50

    def test_respects_maxlength_attribute_truncates_input(self, handler, mock_browser):
        """TextFieldHandler should truncate input to respect maxlength attribute.

        Requirements: 4.3
        """
        mock_browser.get_attribute.return_value = "10"

        result = handler.populate("input[name='name']", "This is a very long name")

        mock_browser.fill.assert_called_once()
        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "This is a "  # Truncated to 10 chars
        assert result.value == "This is a "

    def test_handles_special_characters_without_corruption(self, handler, mock_browser):
        """TextFieldHandler should handle special characters without corruption.

        Requirements: 4.4
        """
        special_chars = "John O'Brien-Smith & Co. <test@example.com>"

        result = handler.populate("input[name='name']", special_chars)

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == special_chars
        assert result.value == special_chars

    def test_handles_unicode_characters(self, handler, mock_browser):
        """TextFieldHandler should handle unicode characters without encoding issues.

        Requirements: 4.4
        """
        unicode_text = "Jose Garcia Martinez"

        result = handler.populate("input[name='name']", unicode_text)

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == unicode_text
        assert result.value == unicode_text

    def test_handles_empty_string_input(self, handler, mock_browser):
        """TextFieldHandler should handle empty string input."""
        result = handler.populate("input[name='optional']", "")

        mock_browser.fill.assert_called_once()
        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == ""
        assert result.status == FieldStatus.POPULATED

    def test_returns_error_result_on_browser_exception(self, handler, mock_browser):
        """TextFieldHandler should return error result on browser exception."""
        mock_browser.fill.side_effect = Exception("Element not found")

        result = handler.populate("input[name='email']", "test@example.com")

        assert result.status == FieldStatus.ERROR
        assert "Element not found" in result.error_message

    def test_default_config_uses_fast_fill(self, handler, mock_browser):
        """TextFieldHandler should use fast fill by default (no typing simulation)."""
        result = handler.populate("input[name='email']", "test@example.com")

        mock_browser.fill.assert_called_once()
        mock_browser.type_slowly.assert_not_called()

    def test_maxlength_not_applied_when_respect_maxlength_false(
        self, handler, mock_browser
    ):
        """TextFieldHandler should not truncate when respect_maxlength is False.

        Requirements: 4.3
        """
        mock_browser.get_attribute.return_value = "5"
        config = TextFieldConfig(respect_maxlength=False)

        result = handler.populate("input[name='name']", "LongName", config=config)

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "LongName"  # Not truncated

    def test_handles_none_maxlength_attribute(self, handler, mock_browser):
        """TextFieldHandler should handle None maxlength attribute gracefully."""
        mock_browser.get_attribute.return_value = None

        result = handler.populate("input[name='name']", "Any length text here")

        call_args = mock_browser.fill.call_args
        assert call_args[0][1] == "Any length text here"  # Not truncated


class TestTextFieldHandlerFormatPhone:
    """Tests for TextFieldHandler.format_phone() method."""

    @pytest.fixture
    def handler(self):
        """Create TextFieldHandler with mock browser."""
        return TextFieldHandler(MagicMock())

    def test_formats_phone_with_default_pattern(self, handler):
        """format_phone should format using default pattern ###-###-####.

        Requirements: 4.5
        """
        result = handler.format_phone("1234567890")

        assert result == "123-456-7890"

    def test_formats_phone_with_custom_pattern(self, handler):
        """format_phone should support custom patterns.

        Requirements: 4.5
        """
        result = handler.format_phone("1234567890", pattern="(###) ###-####")

        assert result == "(123) 456-7890"

    def test_formats_phone_removing_non_digits(self, handler):
        """format_phone should extract digits from input before formatting.

        Requirements: 4.5
        """
        result = handler.format_phone("(123) 456-7890")

        assert result == "123-456-7890"

    def test_formats_phone_with_country_code(self, handler):
        """format_phone should handle numbers with country codes.

        Requirements: 4.5
        """
        result = handler.format_phone("+1-234-567-8901", pattern="###-###-####")

        # Takes first 10 digits after stripping
        assert result == "123-456-7890"

    def test_formats_phone_with_fewer_digits_than_pattern(self, handler):
        """format_phone should handle numbers with fewer digits than expected.

        Requirements: 4.5
        """
        result = handler.format_phone("12345", pattern="###-###-####")

        # Should fill what it can
        assert result == "123-45"

    def test_formats_phone_empty_string_returns_empty(self, handler):
        """format_phone should return empty string for empty input.

        Requirements: 4.5
        """
        result = handler.format_phone("")

        assert result == ""

    def test_formats_phone_with_spaces_only(self, handler):
        """format_phone should handle input with only spaces."""
        result = handler.format_phone("   ")

        assert result == ""


class TestTextFieldConfig:
    """Tests for TextFieldConfig dataclass."""

    def test_default_values(self):
        """TextFieldConfig should have sensible defaults."""
        config = TextFieldConfig()

        assert config.simulate_typing is False
        assert config.typing_delay_ms == 50
        assert config.respect_maxlength is True

    def test_custom_values(self):
        """TextFieldConfig should accept custom values."""
        config = TextFieldConfig(
            simulate_typing=True,
            typing_delay_ms=100,
            respect_maxlength=False,
        )

        assert config.simulate_typing is True
        assert config.typing_delay_ms == 100
        assert config.respect_maxlength is False
