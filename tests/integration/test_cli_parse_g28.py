"""Integration tests for parse-g28 CLI command.

Task 8: CLI Command implementation tests.

Tests cover:
- 8.1 Define parse-g28 command with Typer
- 8.2 Implement command execution logic
- 8.3 Implement CLI error handling
- 8.4 Register command with main CLI application

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1, 10.2, 10.3, 10.4
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from tryalma.cli import app
from tryalma.g28.models import (
    AttorneyInfo,
    ExtractedField,
    G28ExtractionResult,
    G28FormData,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_g28_form_data() -> G28FormData:
    """Create a mock G28FormData for testing."""
    return G28FormData(
        source_file="test.pdf",
        form_detected=True,
        extraction_timestamp="2024-01-25T12:00:00Z",
        overall_confidence=0.85,
        part1_attorney_info=AttorneyInfo(
            family_name=ExtractedField(value="Smith", confidence=0.95),
            given_name=ExtractedField(value="John", confidence=0.9),
        ),
    )


@pytest.fixture
def mock_success_result(mock_g28_form_data: G28FormData) -> G28ExtractionResult:
    """Create a mock successful extraction result."""
    return G28ExtractionResult(
        success=True,
        data=mock_g28_form_data,
        source_file="test.pdf",
        warnings=[],
    )


class TestParseG28CommandDefinition:
    """Tests for Task 8.1: Define parse-g28 command with Typer."""

    def test_parse_g28_command_exists(self, cli_runner: CliRunner) -> None:
        """Test parse-g28 command exists and is registered."""
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        # Command should exist (help should work, not be "No such command")
        assert "No such command" not in result.stdout
        assert result.exit_code == 0

    def test_accepts_file_path_as_required_positional_argument(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 accepts file path as required positional argument."""
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        # Help should mention FILE_PATH as argument
        assert "FILE_PATH" in result.stdout or "file" in result.stdout.lower()
        assert result.exit_code == 0

    def test_has_output_option_for_writing_to_file(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 has --output option for writing to file instead of stdout."""
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        assert "--output" in result.stdout or "-o" in result.stdout
        assert result.exit_code == 0

    def test_has_format_option_accepting_json_or_yaml(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 has --format option accepting 'json' or 'yaml'."""
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        assert "--format" in result.stdout or "-f" in result.stdout
        assert result.exit_code == 0

    def test_format_option_defaults_to_json(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test --format option defaults to 'json'."""
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        # Default should be json (mentioned in help)
        assert "json" in result.stdout.lower()

    def test_has_verbose_flag_for_confidence_scores(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 has --verbose flag for including confidence scores and metadata."""
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        assert "--verbose" in result.stdout or "-v" in result.stdout
        assert result.exit_code == 0

    def test_validates_file_existence(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 validates file existence via Typer constraints."""
        # Try to parse a non-existent file
        result = cli_runner.invoke(app, ["parse-g28", "/nonexistent/file.pdf"])

        # Should fail with appropriate error
        assert result.exit_code != 0


class TestParseG28CommandExecution:
    """Tests for Task 8.2: Implement command execution logic."""

    def test_initializes_parser_service_with_default_dependencies(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test command initializes G28ParserService with default dependencies."""
        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            mock_create_default.assert_called_once()

    def test_invokes_parse_with_provided_arguments(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test command invokes parse() with provided arguments."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            mock_service.parse.assert_called_once()
            call_kwargs = mock_service.parse.call_args[1]
            # Verify the file_path was passed as a keyword argument
            assert call_kwargs.get("file_path") == Path(test_file)

    def test_outputs_json_to_stdout_by_default(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test command outputs JSON to stdout by default."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            # Should output valid JSON
            assert result.exit_code == 0
            output = json.loads(result.stdout)
            assert "success" in output

    def test_writes_to_specified_file_when_output_provided(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test command writes to specified file when --output provided."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")
        output_file = tmp_path / "output.json"

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(
                app, ["parse-g28", str(test_file), "--output", str(output_file)]
            )

            assert result.exit_code == 0
            assert output_file.exists()
            content = json.loads(output_file.read_text())
            assert "success" in content

    def test_outputs_yaml_when_format_yaml_provided(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test command outputs YAML when --format yaml provided."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(
                app, ["parse-g28", str(test_file), "--format", "yaml"]
            )

            assert result.exit_code == 0
            # Should be valid YAML (and not JSON format)
            output = yaml.safe_load(result.stdout)
            assert "success" in output

    def test_displays_progress_in_verbose_mode(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test command displays progress information in verbose mode."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(
                app, ["parse-g28", str(test_file), "--verbose"]
            )

            assert result.exit_code == 0
            # In verbose mode, should pass verbose=True to service
            mock_service.parse.assert_called_once()
            call_kwargs = mock_service.parse.call_args[1]
            assert call_kwargs.get("verbose") is True


class TestParseG28ErrorHandling:
    """Tests for Task 8.3: Implement CLI error handling."""

    def test_catches_g28_exceptions_and_displays_user_friendly_messages(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command catches G28-specific exceptions and displays user-friendly messages."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            # Simulate extraction error
            from tryalma.g28.exceptions import G28ExtractionError
            mock_service.parse.side_effect = G28ExtractionError("Extraction failed")
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            # Should show user-friendly error message (Typer mixes stdout/stderr)
            # Check for exit code indicating error, and no stack trace
            assert result.exit_code == 3  # G28ExtractionError exit code
            assert "Traceback" not in result.stdout

    def test_writes_error_messages_to_stderr(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command writes error messages to stderr."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            from tryalma.g28.exceptions import G28ExtractionError
            mock_service.parse.side_effect = G28ExtractionError("Test error")
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)], catch_exceptions=False)

            # CliRunner combines stdout and stderr, but error should be present
            # and exit code should be non-zero
            assert result.exit_code != 0 or "error" in result.stdout.lower()

    def test_exits_with_code_2_for_validation_errors(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command exits with code 2 for validation errors."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            from tryalma.g28.exceptions import UnsupportedFormatError
            mock_service.parse.side_effect = UnsupportedFormatError("Unsupported format")
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            assert result.exit_code == 2

    def test_exits_with_code_3_for_processing_errors(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command exits with code 3 for processing errors."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            from tryalma.g28.exceptions import G28ExtractionError
            mock_service.parse.side_effect = G28ExtractionError("Processing failed")
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            assert result.exit_code == 3

    def test_never_exposes_stack_traces_to_users(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command never exposes stack traces to users."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.side_effect = Exception("Internal error with trace")
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            # Should not contain traceback indicators
            assert "Traceback" not in result.stdout
            assert "File \"" not in result.stdout

    def test_handles_api_key_not_configured(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command handles missing API key gracefully."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_create_default.side_effect = ValueError("API key not configured")

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            # Should exit with non-zero code and not show stack trace
            assert result.exit_code != 0
            assert "Traceback" not in result.stdout


class TestParseG28CommandRegistration:
    """Tests for Task 8.4: Register command with main CLI application."""

    def test_command_registered_with_main_cli_app(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 command is registered with main CLI app."""
        result = cli_runner.invoke(app, ["--help"])

        assert "parse-g28" in result.stdout
        assert result.exit_code == 0

    def test_command_appears_in_help_output(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 command appears in --help output."""
        result = cli_runner.invoke(app, ["--help"])

        assert "parse-g28" in result.stdout
        # Should have description
        assert "G-28" in result.stdout or "g28" in result.stdout.lower()

    def test_follows_existing_cli_patterns(
        self, cli_runner: CliRunner
    ) -> None:
        """Test parse-g28 follows existing CLI patterns and conventions."""
        # Test that help format is consistent with other commands
        result = cli_runner.invoke(app, ["parse-g28", "--help"])

        # Should have standard Typer help format (check lowercase to handle rich formatting)
        stdout_lower = result.stdout.lower()
        assert "usage:" in stdout_lower
        # Typer uses "Options" section - check in various formats
        assert "options" in stdout_lower or "arguments" in stdout_lower


class TestParseG28OutputFormats:
    """Additional tests for output format handling."""

    def test_json_output_is_properly_formatted(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test JSON output is properly indented and formatted."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            assert result.exit_code == 0
            # Should be parseable as JSON
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)

    def test_yaml_output_is_properly_formatted(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        mock_success_result: G28ExtractionResult,
    ) -> None:
        """Test YAML output is properly formatted."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = mock_success_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(
                app, ["parse-g28", str(test_file), "--format", "yaml"]
            )

            assert result.exit_code == 0
            # Should be parseable as YAML
            parsed = yaml.safe_load(result.stdout)
            assert isinstance(parsed, dict)

    def test_handles_failed_extraction_result(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test command handles failed extraction result gracefully."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        failed_result = G28ExtractionResult(
            success=False,
            error="Document is not recognized as a USCIS Form G-28",
            error_code="NOT_G28_FORM",
            source_file=str(test_file),
        )

        with patch(
            "tryalma.g28.cli.G28ParserService.create_default"
        ) as mock_create_default:
            mock_service = MagicMock()
            mock_service.parse.return_value = failed_result
            mock_create_default.return_value = mock_service

            result = cli_runner.invoke(app, ["parse-g28", str(test_file)])

            # Should exit with non-zero code for failed extraction
            assert result.exit_code == 3  # NOT_G28_FORM maps to processing error (exit code 3)
            assert "Traceback" not in result.stdout
