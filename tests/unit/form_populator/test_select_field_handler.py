"""Tests for SelectFieldHandler - dropdown selection handler.

These tests verify:
- Task 4.2: Dropdown selection handler
  - Select option matching extracted data value using exact match first (Requirement 5.1)
  - Fall back to case-insensitive matching when exact match fails (Requirement 5.2)
  - Support selection by visible text, value attribute, or index (Requirement 5.4)
  - Normalize state names and abbreviations for consistent matching (Requirement 5.5)
  - Normalize country names for consistent matching (Requirement 5.5)
  - Log warning with field name and attempted value when no match found (Requirement 5.3)
"""

import logging

import pytest
from unittest.mock import MagicMock

from tryalma.form_populator.field_handlers import (
    SelectFieldHandler,
    SelectStrategy,
)
from tryalma.form_populator.models import FieldResult, FieldStatus


class TestSelectFieldHandlerPopulate:
    """Tests for SelectFieldHandler.populate() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create SelectFieldHandler with mock browser."""
        return SelectFieldHandler(mock_browser)

    def test_selects_option_by_value_first(self, handler, mock_browser):
        """SelectFieldHandler should try exact value match first.

        Requirements: 5.1
        """
        result = handler.populate("select[name='state']", "CA")

        mock_browser.select_option.assert_called_once_with(
            "select[name='state']", value="CA"
        )
        assert result.status == FieldStatus.POPULATED
        assert result.value == "CA"

    def test_falls_back_to_label_when_value_fails(self, handler, mock_browser):
        """SelectFieldHandler should fall back to label when value match fails.

        Requirements: 5.2
        """
        # First call (value) fails, second call (label) succeeds
        mock_browser.select_option.side_effect = [
            Exception("Value not found"),
            None,  # Success on label
        ]

        result = handler.populate("select[name='state']", "California")

        assert mock_browser.select_option.call_count == 2
        # Second call should use label
        second_call = mock_browser.select_option.call_args_list[1]
        assert second_call[1] == {"label": "California"}
        assert result.status == FieldStatus.POPULATED

    def test_supports_selection_by_value(self, handler, mock_browser):
        """SelectFieldHandler should support selection by value attribute.

        Requirements: 5.4
        """
        result = handler.populate(
            "select[name='country']",
            "US",
            strategies=[SelectStrategy.VALUE],
        )

        mock_browser.select_option.assert_called_with(
            "select[name='country']", value="US"
        )

    def test_supports_selection_by_label(self, handler, mock_browser):
        """SelectFieldHandler should support selection by visible text.

        Requirements: 5.4
        """
        result = handler.populate(
            "select[name='country']",
            "United States",
            strategies=[SelectStrategy.LABEL],
        )

        mock_browser.select_option.assert_called_with(
            "select[name='country']", label="United States"
        )

    def test_supports_selection_by_index(self, handler, mock_browser):
        """SelectFieldHandler should support selection by index.

        Requirements: 5.4
        """
        result = handler.populate(
            "select[name='country']",
            "5",
            strategies=[SelectStrategy.INDEX],
        )

        mock_browser.select_option.assert_called_with(
            "select[name='country']", index=5
        )

    def test_logs_warning_when_no_match_found(self, handler, mock_browser, caplog):
        """SelectFieldHandler should log warning when no match found.

        Requirements: 5.3
        """
        mock_browser.select_option.side_effect = Exception("No match")

        with caplog.at_level(logging.WARNING):
            result = handler.populate("select[name='state']", "InvalidState")

        assert result.status == FieldStatus.ERROR
        assert "No matching option found" in result.error_message
        assert any(
            "InvalidState" in record.message and "select[name='state']" in record.message
            for record in caplog.records
        )

    def test_returns_error_result_when_all_strategies_fail(self, handler, mock_browser):
        """SelectFieldHandler should return error when all strategies fail.

        Requirements: 5.3
        """
        mock_browser.select_option.side_effect = Exception("No match")

        result = handler.populate("select[name='country']", "Unknown")

        assert result.status == FieldStatus.ERROR
        assert result.error_message is not None

    def test_returns_field_result_on_success(self, handler, mock_browser):
        """SelectFieldHandler should return FieldResult with success status."""
        result = handler.populate("select[name='state']", "NY")

        assert isinstance(result, FieldResult)
        assert result.status == FieldStatus.POPULATED
        assert result.value == "NY"
        assert result.selector == "select[name='state']"

    def test_default_strategies_are_value_then_label(self, handler, mock_browser):
        """SelectFieldHandler should default to VALUE then LABEL strategies.

        Requirements: 5.1, 5.2
        """
        # Both fail to test full cascade
        mock_browser.select_option.side_effect = Exception("No match")

        handler.populate("select[name='state']", "Test")

        # Should have tried both value and label
        assert mock_browser.select_option.call_count == 2


class TestSelectFieldHandlerNormalizeState:
    """Tests for SelectFieldHandler.normalize_state() method."""

    @pytest.fixture
    def handler(self):
        """Create SelectFieldHandler with mock browser."""
        return SelectFieldHandler(MagicMock())

    def test_normalizes_state_abbreviation_to_full_name(self, handler):
        """normalize_state should convert abbreviations to full names.

        Requirements: 5.5
        """
        assert handler.normalize_state("CA") == "California"
        assert handler.normalize_state("NY") == "New York"
        assert handler.normalize_state("TX") == "Texas"

    def test_normalizes_lowercase_abbreviation(self, handler):
        """normalize_state should handle lowercase abbreviations.

        Requirements: 5.5
        """
        assert handler.normalize_state("ca") == "California"
        assert handler.normalize_state("ny") == "New York"

    def test_preserves_full_state_name(self, handler):
        """normalize_state should preserve full state names.

        Requirements: 5.5
        """
        assert handler.normalize_state("California") == "California"
        assert handler.normalize_state("New York") == "New York"

    def test_handles_dc_abbreviation(self, handler):
        """normalize_state should handle DC abbreviation.

        Requirements: 5.5
        """
        assert handler.normalize_state("DC") == "District of Columbia"

    def test_returns_original_for_unknown_value(self, handler):
        """normalize_state should return original for unknown values.

        Requirements: 5.5
        """
        assert handler.normalize_state("Unknown") == "Unknown"

    def test_strips_whitespace(self, handler):
        """normalize_state should strip whitespace from input.

        Requirements: 5.5
        """
        assert handler.normalize_state("  CA  ") == "California"
        assert handler.normalize_state("  California  ") == "California"


class TestSelectFieldHandlerNormalizeCountry:
    """Tests for SelectFieldHandler.normalize_country() method."""

    @pytest.fixture
    def handler(self):
        """Create SelectFieldHandler with mock browser."""
        return SelectFieldHandler(MagicMock())

    def test_normalizes_usa_variations(self, handler):
        """normalize_country should normalize USA variations.

        Requirements: 5.5
        """
        assert handler.normalize_country("USA") == "United States"
        assert handler.normalize_country("US") == "United States"
        assert handler.normalize_country("U.S.") == "United States"
        assert handler.normalize_country("U.S.A.") == "United States"

    def test_normalizes_uk_variations(self, handler):
        """normalize_country should normalize UK variations.

        Requirements: 5.5
        """
        assert handler.normalize_country("UK") == "United Kingdom"
        assert handler.normalize_country("U.K.") == "United Kingdom"
        assert handler.normalize_country("Great Britain") == "United Kingdom"

    def test_preserves_standard_country_names(self, handler):
        """normalize_country should preserve standard country names.

        Requirements: 5.5
        """
        assert handler.normalize_country("United States") == "United States"
        assert handler.normalize_country("Canada") == "Canada"
        assert handler.normalize_country("Mexico") == "Mexico"

    def test_handles_lowercase_input(self, handler):
        """normalize_country should handle lowercase input.

        Requirements: 5.5
        """
        assert handler.normalize_country("usa") == "United States"
        assert handler.normalize_country("uk") == "United Kingdom"

    def test_strips_whitespace(self, handler):
        """normalize_country should strip whitespace.

        Requirements: 5.5
        """
        assert handler.normalize_country("  USA  ") == "United States"


class TestSelectStrategy:
    """Tests for SelectStrategy enumeration."""

    def test_value_strategy_exists(self):
        """SelectStrategy should have VALUE option."""
        assert SelectStrategy.VALUE.value == "value"

    def test_label_strategy_exists(self):
        """SelectStrategy should have LABEL option."""
        assert SelectStrategy.LABEL.value == "label"

    def test_index_strategy_exists(self):
        """SelectStrategy should have INDEX option."""
        assert SelectStrategy.INDEX.value == "index"
