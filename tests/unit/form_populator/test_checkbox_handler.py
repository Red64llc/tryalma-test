"""Tests for CheckboxHandler - checkbox field handler.

These tests verify:
- Task 4.3: Checkbox handler
  - Check checkbox when provided value is truthy (Requirement 6.1)
  - Uncheck checkbox when provided value is falsy (Requirement 6.2)
  - Support checkbox groups where multiple selections are allowed (Requirement 6.5)
  - Return population result with success status
"""

import pytest
from unittest.mock import MagicMock

from tryalma.form_populator.field_handlers import CheckboxHandler
from tryalma.form_populator.models import FieldResult, FieldStatus


class TestCheckboxHandlerPopulate:
    """Tests for CheckboxHandler.populate() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create CheckboxHandler with mock browser."""
        return CheckboxHandler(mock_browser)

    def test_checks_checkbox_when_value_is_true(self, handler, mock_browser):
        """CheckboxHandler should check checkbox when value is True.

        Requirements: 6.1
        """
        result = handler.populate("input[name='agree']", True)

        mock_browser.check.assert_called_once_with("input[name='agree']")
        assert result.status == FieldStatus.POPULATED
        assert result.value == "True"

    def test_unchecks_checkbox_when_value_is_false(self, handler, mock_browser):
        """CheckboxHandler should uncheck checkbox when value is False.

        Requirements: 6.2
        """
        result = handler.populate("input[name='agree']", False)

        mock_browser.uncheck.assert_called_once_with("input[name='agree']")
        assert result.status == FieldStatus.POPULATED
        assert result.value == "False"

    def test_returns_field_result_with_success_status(self, handler, mock_browser):
        """CheckboxHandler should return FieldResult with success status."""
        result = handler.populate("input[name='terms']", True)

        assert isinstance(result, FieldResult)
        assert result.status == FieldStatus.POPULATED
        assert result.selector == "input[name='terms']"

    def test_returns_error_result_on_browser_exception(self, handler, mock_browser):
        """CheckboxHandler should return error result on browser exception."""
        mock_browser.check.side_effect = Exception("Element not found")

        result = handler.populate("input[name='agree']", True)

        assert result.status == FieldStatus.ERROR
        assert "Element not found" in result.error_message

    def test_handles_check_exception_gracefully(self, handler, mock_browser):
        """CheckboxHandler should handle check exception gracefully."""
        mock_browser.check.side_effect = Exception("Checkbox disabled")

        result = handler.populate("input[name='disabled']", True)

        assert result.status == FieldStatus.ERROR
        assert result.error_message is not None

    def test_handles_uncheck_exception_gracefully(self, handler, mock_browser):
        """CheckboxHandler should handle uncheck exception gracefully."""
        mock_browser.uncheck.side_effect = Exception("Checkbox disabled")

        result = handler.populate("input[name='disabled']", False)

        assert result.status == FieldStatus.ERROR
        assert result.error_message is not None


class TestCheckboxHandlerPopulateGroup:
    """Tests for CheckboxHandler.populate_group() method."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create CheckboxHandler with mock browser."""
        return CheckboxHandler(mock_browser)

    def test_populates_multiple_checkboxes_in_group(self, handler, mock_browser):
        """populate_group should handle multiple checkboxes.

        Requirements: 6.5
        """
        selectors = [
            ("input[name='option1']", True),
            ("input[name='option2']", False),
            ("input[name='option3']", True),
        ]

        results = handler.populate_group(selectors)

        assert len(results) == 3
        # First checkbox checked
        mock_browser.check.assert_any_call("input[name='option1']")
        # Second checkbox unchecked
        mock_browser.uncheck.assert_called_with("input[name='option2']")
        # Third checkbox checked
        mock_browser.check.assert_any_call("input[name='option3']")

    def test_returns_list_of_field_results(self, handler, mock_browser):
        """populate_group should return list of FieldResults.

        Requirements: 6.5
        """
        selectors = [
            ("input[name='a']", True),
            ("input[name='b']", True),
        ]

        results = handler.populate_group(selectors)

        assert all(isinstance(r, FieldResult) for r in results)
        assert all(r.status == FieldStatus.POPULATED for r in results)

    def test_handles_partial_failures_in_group(self, handler, mock_browser):
        """populate_group should handle partial failures.

        Requirements: 6.5
        """
        # First succeeds, second fails, third succeeds
        mock_browser.check.side_effect = [None, Exception("Error"), None]

        selectors = [
            ("input[name='a']", True),
            ("input[name='b']", True),
            ("input[name='c']", True),
        ]

        results = handler.populate_group(selectors)

        assert results[0].status == FieldStatus.POPULATED
        assert results[1].status == FieldStatus.ERROR
        assert results[2].status == FieldStatus.POPULATED

    def test_handles_empty_group(self, handler, mock_browser):
        """populate_group should handle empty list."""
        results = handler.populate_group([])

        assert results == []
        mock_browser.check.assert_not_called()
        mock_browser.uncheck.assert_not_called()

    def test_group_returns_correct_values(self, handler, mock_browser):
        """populate_group should return correct values for each checkbox."""
        selectors = [
            ("input[name='newsletter']", True),
            ("input[name='marketing']", False),
        ]

        results = handler.populate_group(selectors)

        assert results[0].value == "True"
        assert results[1].value == "False"


class TestCheckboxHandlerTruthyFalsyValues:
    """Tests for truthy/falsy value handling."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock BrowserController."""
        return MagicMock()

    @pytest.fixture
    def handler(self, mock_browser):
        """Create CheckboxHandler with mock browser."""
        return CheckboxHandler(mock_browser)

    def test_checks_for_truthy_boolean_true(self, handler, mock_browser):
        """Should check for True.

        Requirements: 6.1
        """
        handler.populate("input[name='cb']", True)
        mock_browser.check.assert_called_once()

    def test_unchecks_for_falsy_boolean_false(self, handler, mock_browser):
        """Should uncheck for False.

        Requirements: 6.2
        """
        handler.populate("input[name='cb']", False)
        mock_browser.uncheck.assert_called_once()
