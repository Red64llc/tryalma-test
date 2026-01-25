"""Integration tests for CLI."""

from typer.testing import CliRunner

from tryalma.cli import app


class TestHelloCommand:
    """Tests for the hello CLI command."""

    def test_hello_default(self, cli_runner: CliRunner) -> None:
        """Test hello command with default name."""
        result = cli_runner.invoke(app, ["hello"])
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout

    def test_hello_with_name(self, cli_runner: CliRunner) -> None:
        """Test hello command with custom name."""
        result = cli_runner.invoke(app, ["hello", "--name", "Alice"])
        assert result.exit_code == 0
        assert "Hello, Alice!" in result.stdout

    def test_hello_with_short_option(self, cli_runner: CliRunner) -> None:
        """Test hello command with short -n option."""
        result = cli_runner.invoke(app, ["hello", "-n", "Bob"])
        assert result.exit_code == 0
        assert "Hello, Bob!" in result.stdout


class TestVersionCommand:
    """Tests for the version CLI command."""

    def test_version_shows_version(self, cli_runner: CliRunner) -> None:
        """Test version command shows version string."""
        result = cli_runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "tryalma version" in result.stdout
        assert "0.1.0" in result.stdout
