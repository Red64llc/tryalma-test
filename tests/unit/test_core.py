"""Unit tests for core business logic."""

import pytest

from tryalma.core import get_greeting


class TestGetGreeting:
    """Tests for get_greeting function."""

    def test_greeting_with_name(self) -> None:
        """Test greeting with a provided name."""
        result = get_greeting("Alice")
        assert result == "Hello, Alice!"

    def test_greeting_with_empty_string(self) -> None:
        """Test greeting with empty string defaults to World."""
        result = get_greeting("")
        assert result == "Hello, World!"

    def test_greeting_with_whitespace_only(self) -> None:
        """Test greeting with whitespace only defaults to World."""
        result = get_greeting("   ")
        assert result == "Hello, World!"

    def test_greeting_strips_whitespace(self) -> None:
        """Test greeting strips leading/trailing whitespace from name."""
        result = get_greeting("  Bob  ")
        assert result == "Hello, Bob!"

    @pytest.mark.parametrize(
        "name,expected",
        [
            ("World", "Hello, World!"),
            ("Test", "Hello, Test!"),
            ("123", "Hello, 123!"),
        ],
    )
    def test_greeting_parametrized(self, name: str, expected: str) -> None:
        """Test greeting with various inputs."""
        assert get_greeting(name) == expected
