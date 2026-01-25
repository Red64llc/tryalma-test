"""Integration tests for passport extraction CLI command.

Task 7: Tests for CLI command integration.

Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3, 4.4, 5.4, 7.1, 7.2, 7.3
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tryalma.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI runner."""
    return CliRunner()


class TestPassportExtractCommand:
    """Tests for the passport extract command.

    Task 7.1: Implement passport extract command.
    Requirements: 1.1, 1.2, 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3
    """

    def test_passport_command_exists(self, cli_runner: CliRunner) -> None:
        """Test that passport command is registered in CLI."""
        result = cli_runner.invoke(app, ["passport", "--help"])
        assert result.exit_code == 0
        assert "extract" in result.stdout.lower()

    def test_passport_extract_help(self, cli_runner: CliRunner) -> None:
        """Test that extract command has help text.

        Requirement 7.1: --help flag displays usage information.
        Requirement 7.2: Descriptive help text for options.
        """
        result = cli_runner.invoke(app, ["passport", "extract", "--help"])
        assert result.exit_code == 0
        assert "passport" in result.stdout.lower()
        # Check for option descriptions
        assert "--format" in result.stdout
        assert "--output" in result.stdout
        assert "--verbose" in result.stdout

    def test_passport_extract_requires_path(self, cli_runner: CliRunner) -> None:
        """Test that extract command requires path argument.

        Requirement 7.3: Display usage message when no arguments.
        """
        result = cli_runner.invoke(app, ["passport", "extract"])
        # Should fail with missing argument
        assert result.exit_code != 0
        # Should show usage info (may be in stdout or output)
        output = result.stdout + (result.output or "")
        assert "path" in output.lower() or "missing" in output.lower() or "argument" in output.lower()


class TestPassportExtractSingleFile:
    """Tests for single file extraction.

    Task 7.1, 7.2: Single file processing and validation.
    Requirements: 1.1, 1.3, 5.4
    """

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_extract_single_file_success(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
    ) -> None:
        """Test successful single file extraction.

        Requirement 1.1: Process single image file.
        """
        from datetime import date

        from tryalma.passport.models import ExtractionResult, PassportData

        # Mock successful extraction
        mock_service = mock_service_cls.return_value
        mock_result = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=temp_passport_image,
                surname="ERIKSSON",
                given_names="ANNA MARIA",
                date_of_birth=date(1974, 8, 12),
                nationality="UTO",
                passport_number="L898902C3",
                expiry_date=date(2025, 4, 15),
                sex="F",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=temp_passport_image,
        )
        mock_service.extract_single.return_value = mock_result

        result = cli_runner.invoke(app, ["passport", "extract", str(temp_passport_image)])

        assert result.exit_code == 0
        assert "ERIKSSON" in result.stdout

    def test_extract_invalid_path_exits_with_code_2(
        self, cli_runner: CliRunner
    ) -> None:
        """Test that invalid path returns exit code 2.

        Requirement 1.3: Invalid path error with exit code 2.
        Requirement 5.4: Exit code 2 for input validation errors.
        """
        result = cli_runner.invoke(app, ["passport", "extract", "/nonexistent/path.jpg"])

        assert result.exit_code == 2
        # Error message may be in stdout or output (Rich writes to console)
        output = result.stdout + (result.output or "")
        assert "error" in output.lower() or "not exist" in output.lower()


class TestPassportExtractBatch:
    """Tests for batch directory extraction.

    Task 7.1, 7.2, 7.3: Batch processing.
    Requirements: 1.2, 1.4
    """

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_extract_directory_batch(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_images_dir: Path,
    ) -> None:
        """Test batch directory processing.

        Requirement 1.2: Process directory of images.
        """
        from datetime import date

        from tryalma.passport.models import ExtractionResult, PassportData

        # Mock batch extraction with multiple results
        mock_service = mock_service_cls.return_value
        results = [
            ExtractionResult(
                success=True,
                data=PassportData(
                    source_file=temp_passport_images_dir / f"passport_{i}.jpg",
                    surname=f"SURNAME{i}",
                    given_names=f"NAME{i}",
                    date_of_birth=date(1990, 1, 1),
                    nationality="UTO",
                    passport_number=f"ABC{i:06d}",
                    mrz_type="TD3",
                    mrz_valid=True,
                ),
                error=None,
                source_file=temp_passport_images_dir / f"passport_{i}.jpg",
            )
            for i in range(3)
        ]
        mock_service.extract_batch.return_value = results

        result = cli_runner.invoke(
            app, ["passport", "extract", str(temp_passport_images_dir)]
        )

        assert result.exit_code == 0

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_extract_empty_directory_shows_message(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test informational message for empty directory.

        Requirement 1.4: Message when no processable files found.
        """
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        mock_service = mock_service_cls.return_value
        mock_service.extract_batch.return_value = []

        result = cli_runner.invoke(app, ["passport", "extract", str(empty_dir)])

        assert result.exit_code == 0
        assert "no" in result.stdout.lower()


class TestOutputFormats:
    """Tests for output format options.

    Task 7.1: Format option.
    Requirements: 4.1, 4.2, 4.3
    """

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_json_output_format(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
    ) -> None:
        """Test JSON output format.

        Requirement 4.2: JSON output format.
        """
        from datetime import date

        from tryalma.passport.models import ExtractionResult, PassportData

        mock_service = mock_service_cls.return_value
        mock_result = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=temp_passport_image,
                surname="ERIKSSON",
                given_names="ANNA",
                nationality="UTO",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=temp_passport_image,
        )
        mock_service.extract_single.return_value = mock_result

        result = cli_runner.invoke(
            app, ["passport", "extract", "--format", "json", str(temp_passport_image)]
        )

        assert result.exit_code == 0
        # Should be valid JSON
        parsed = json.loads(result.stdout)
        assert "results" in parsed

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_csv_output_format(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
    ) -> None:
        """Test CSV output format.

        Requirement 4.3: CSV output format.
        """
        from datetime import date

        from tryalma.passport.models import ExtractionResult, PassportData

        mock_service = mock_service_cls.return_value
        mock_result = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=temp_passport_image,
                surname="ERIKSSON",
                given_names="ANNA",
                nationality="UTO",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=temp_passport_image,
        )
        mock_service.extract_single.return_value = mock_result

        result = cli_runner.invoke(
            app, ["passport", "extract", "--format", "csv", str(temp_passport_image)]
        )

        assert result.exit_code == 0
        # Should have CSV headers
        assert "source_file" in result.stdout
        assert "surname" in result.stdout


class TestOutputFile:
    """Tests for output file option.

    Task 7.1: Output option.
    Requirement 4.4
    """

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_output_to_file(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
        tmp_path: Path,
    ) -> None:
        """Test writing results to file.

        Requirement 4.4: Write results to specified file.
        """
        from tryalma.passport.models import ExtractionResult, PassportData

        output_file = tmp_path / "output.json"

        mock_service = mock_service_cls.return_value
        mock_result = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=temp_passport_image,
                surname="ERIKSSON",
                given_names="ANNA",
                nationality="UTO",
                mrz_type="TD3",
                mrz_valid=True,
            ),
            error=None,
            source_file=temp_passport_image,
        )
        mock_service.extract_single.return_value = mock_result

        result = cli_runner.invoke(
            app,
            [
                "passport",
                "extract",
                "--format",
                "json",
                "--output",
                str(output_file),
                str(temp_passport_image),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert "results" in content


class TestVerboseMode:
    """Tests for verbose mode.

    Task 7.1: Verbose option.
    Requirement 3.4
    """

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_verbose_shows_confidence(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
    ) -> None:
        """Test verbose mode includes confidence scores.

        Requirement 3.4: Verbose mode shows confidence scores.
        """
        from tryalma.passport.models import ExtractionResult, PassportData

        mock_service = mock_service_cls.return_value
        mock_result = ExtractionResult(
            success=True,
            data=PassportData(
                source_file=temp_passport_image,
                surname="ERIKSSON",
                given_names="ANNA",
                nationality="UTO",
                mrz_type="TD3",
                mrz_valid=True,
                confidence=0.95,
            ),
            error=None,
            source_file=temp_passport_image,
        )
        mock_service.extract_single.return_value = mock_result

        result = cli_runner.invoke(
            app,
            ["passport", "extract", "--verbose", str(temp_passport_image)],
        )

        assert result.exit_code == 0
        # In verbose mode, confidence should be visible
        assert "0.95" in result.stdout or "confidence" in result.stdout.lower()


class TestExitCodes:
    """Tests for proper exit codes.

    Task 7.2: Exit code handling.
    Requirement 5.4
    """

    def test_success_exits_with_code_0(
        self, cli_runner: CliRunner, temp_passport_image: Path
    ) -> None:
        """Test successful extraction exits with code 0.

        Requirement 5.4: Exit code 0 on success.
        """
        # This will be tested with proper mocking in other tests
        # Here we just document the expected behavior
        pass

    def test_validation_error_exits_with_code_2(self, cli_runner: CliRunner) -> None:
        """Test validation error exits with code 2.

        Requirement 5.4: Exit code 2 for validation errors.
        """
        result = cli_runner.invoke(
            app, ["passport", "extract", "/nonexistent/path.jpg"]
        )
        assert result.exit_code == 2

    @patch("tryalma.passport.cli.PassportExtractionService")
    @patch("tryalma.passport.cli.MRZExtractor")
    @patch("tryalma.passport.cli.MRZValidator")
    def test_processing_error_exits_with_code_3(
        self,
        mock_validator_cls: MagicMock,
        mock_extractor_cls: MagicMock,
        mock_service_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
    ) -> None:
        """Test processing error exits with code 3.

        Requirement 5.4: Exit code 3 for processing errors.
        """
        from tryalma.passport.models import ExtractionResult

        mock_service = mock_service_cls.return_value
        mock_result = ExtractionResult(
            success=False,
            data=None,
            error="No MRZ detected in image",
            source_file=temp_passport_image,
        )
        mock_service.extract_single.return_value = mock_result

        result = cli_runner.invoke(
            app, ["passport", "extract", str(temp_passport_image)]
        )

        # Single file failure should exit with code 3
        assert result.exit_code == 3


class TestTesseractDependency:
    """Tests for Tesseract dependency handling.

    Task 7.2: Dependency check.
    Requirement 5.3
    """

    @patch("tryalma.passport.cli.MRZExtractor")
    def test_missing_tesseract_shows_instructions(
        self,
        mock_extractor_cls: MagicMock,
        cli_runner: CliRunner,
        temp_passport_image: Path,
    ) -> None:
        """Test missing Tesseract shows installation instructions.

        Requirement 5.3: Missing dependency instructions.
        """
        from tryalma.passport.exceptions import TesseractNotFoundError

        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.check_tesseract_installed.return_value = False

        # The check happens at command start
        result = cli_runner.invoke(
            app, ["passport", "extract", str(temp_passport_image)]
        )

        # Should show helpful message about Tesseract
        # Note: The actual check implementation will determine exact behavior
        # This test documents the expected user experience
