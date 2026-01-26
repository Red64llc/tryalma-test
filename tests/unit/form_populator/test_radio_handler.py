"""Tests for RadioHandler - radio button group handler.

These tests verify:
- Task 4.4: Radio button handler
  - Select radio button in group matching extracted value (Requirement 6.3)
  - Support selection by both value attribute and label text (Requirement 6.3)
  - Log warning and leave group unselected when no matching option found (Requirement 6.4)
  - Return population result with selection status
"""

import logging

import pytest
from unittest.mock import MagicMock

from tryalma.form_populator.field_handlers import RadioHandler
from tryalma.form_populator.models import FieldResult, FieldStatus


class TestRadioHandlerPopulate:
    """Tests for RadioHandler.populate() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create RadioHandler with mock browser."""
        return RadioHandler(mock_browser)

    def test_selects_radio_by_value(self, handler, mock_browser):
        """RadioHandler should select radio button by value attribute.

        Requirements: 6.3
        """
        result = handler.populate("gender", "male")

        mock_browser.check.assert_called_once_with(
            "input[name='gender'][value='male']"
        )
        assert result.status == FieldStatus.POPULATED
        assert result.value == "male"

    def test_returns_field_result_on_success(self, handler, mock_browser):
        """RadioHandler should return FieldResult with success status."""
        result = handler.populate("status", "active")

        assert isinstance(result, FieldResult)
        assert result.status == FieldStatus.POPULATED
        assert result.selector == "input[name='status'][value='active']"

    def test_logs_warning_when_no_match_found(self, handler, mock_browser, caplog):
        """RadioHandler should log warning when no matching option found.

        Requirements: 6.4
        """
        mock_browser.check.side_effect = Exception("Radio not found")

        with caplog.at_level(logging.WARNING):
            result = handler.populate("gender", "unknown")

        assert result.status == FieldStatus.ERROR
        assert any(
            "gender" in record.message and "unknown" in record.message
            for record in caplog.records
        )

    def test_returns_error_when_no_match_found(self, handler, mock_browser):
        """RadioHandler should return error result when no match found.

        Requirements: 6.4
        """
        mock_browser.check.side_effect = Exception("Radio not found")

        result = handler.populate("gender", "invalid")

        assert result.status == FieldStatus.ERROR
        assert "No matching radio option found" in result.error_message

    def test_builds_correct_selector_for_value(self, handler, mock_browser):
        """RadioHandler should build correct CSS selector for value.

        Requirements: 6.3
        """
        handler.populate("restrictionStatus", "yes")

        mock_browser.check.assert_called_with(
            "input[name='restrictionStatus'][value='yes']"
        )


class TestRadioHandlerPopulateByLabel:
    """Tests for RadioHandler.populate_by_label() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create RadioHandler with mock browser."""
        return RadioHandler(mock_browser)

    def test_selects_radio_by_label_text(self, handler, mock_browser):
        """RadioHandler should select radio by associated label text.

        Requirements: 6.3
        """
        result = handler.populate_by_label("gender", "Male")

        mock_browser.check.assert_called()
        assert result.status == FieldStatus.POPULATED
        assert result.value == "Male"

    def test_returns_field_result_on_success(self, handler, mock_browser):
        """RadioHandler populate_by_label should return FieldResult."""
        result = handler.populate_by_label("status", "Active")

        assert isinstance(result, FieldResult)
        assert result.status == FieldStatus.POPULATED

    def test_logs_warning_when_label_not_found(self, handler, mock_browser, caplog):
        """RadioHandler should log warning when label not found.

        Requirements: 6.4
        """
        mock_browser.check.side_effect = Exception("Label not found")

        with caplog.at_level(logging.WARNING):
            result = handler.populate_by_label("gender", "Nonexistent")

        assert result.status == FieldStatus.ERROR
        assert any(
            "gender" in record.message
            for record in caplog.records
        )

    def test_returns_error_when_label_not_found(self, handler, mock_browser):
        """RadioHandler should return error when label not found.

        Requirements: 6.4
        """
        mock_browser.check.side_effect = Exception("Label not found")

        result = handler.populate_by_label("gender", "Invalid")

        assert result.status == FieldStatus.ERROR
        assert result.error_message is not None

    def test_tries_label_selector_first(self, handler, mock_browser):
        """RadioHandler should try label selector pattern first.

        Requirements: 6.3
        """
        result = handler.populate_by_label("sex", "Female")

        # Should use label:has-text pattern
        first_call = mock_browser.check.call_args_list[0]
        assert "label:has-text" in first_call[0][0] or "sex" in first_call[0][0]

    def test_falls_back_to_value_match(self, handler, mock_browser):
        """RadioHandler should fall back to value match if label fails.

        Requirements: 6.3
        """
        # Label selector fails, value selector succeeds
        mock_browser.check.side_effect = [
            Exception("Label not found"),
            None,  # Success on second try
        ]

        result = handler.populate_by_label("gender", "M")

        # Should have tried twice
        assert mock_browser.check.call_count == 2
        assert result.status == FieldStatus.POPULATED


class TestRadioHandlerEdgeCases:
    """Tests for RadioHandler edge cases."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create RadioHandler with mock browser."""
        return RadioHandler(mock_browser)

    def test_handles_special_characters_in_value(self, handler, mock_browser):
        """RadioHandler should handle special characters in value."""
        result = handler.populate("option", "yes/no")

        mock_browser.check.assert_called_once()
        assert result.status == FieldStatus.POPULATED

    def test_handles_numeric_values(self, handler, mock_browser):
        """RadioHandler should handle numeric values."""
        result = handler.populate("rating", "5")

        mock_browser.check.assert_called_with("input[name='rating'][value='5']")
        assert result.status == FieldStatus.POPULATED

    def test_handles_empty_string_value(self, handler, mock_browser):
        """RadioHandler should handle empty string value."""
        result = handler.populate("optional", "")

        mock_browser.check.assert_called_with("input[name='optional'][value='']")
