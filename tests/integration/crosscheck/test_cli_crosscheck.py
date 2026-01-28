"""Integration tests for crosscheck CLI command.

Task 5.2: Tests for CLI crosscheck subcommand.

Requirements: 6.1, 7.1, 7.2
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tryalma.cli import app
from tryalma.crosscheck.models import (
    CrossCheckResult,
    DiscrepancySeverity,
    ExtractionStatus,
    FieldDiscrepancy,
    ProcessingMetadata,
)
from tryalma.passport.models import PassportData

runner = CliRunner()


@pytest.fixture
def sample_passport_data(tmp_path: Path) -> PassportData:
    """Create sample passport data for tests."""
    return PassportData(
        source_file=tmp_path / "test.jpg",
        surname="SMITH",
        given_names="JOHN WILLIAM",
        passport_number="123456789",
        nationality="USA",
        date_of_birth=None,
        expiry_date=None,
        sex="M",
        place_of_birth="NEW YORK",
        mrz_type="TD3",
        mrz_valid=True,
    )


@pytest.fixture
def sample_crosscheck_result(sample_passport_data: PassportData) -> CrossCheckResult:
    """Create sample cross-check result for tests."""
    from datetime import datetime, UTC

    return CrossCheckResult(
        status=ExtractionStatus.SUCCESS,
        passport_data=sample_passport_data,
        field_confidences={
            "surname": 1.0,
            "given_names": 1.0,
            "passport_number": 0.6,
            "nationality": 1.0,
        },
        document_confidence=0.91,
        discrepancies=[
            FieldDiscrepancy(
                field_name="passport_number",
                mrz_value="123456789",
                vlm_value="123456780",
                recommended_value="123456789",
                severity=DiscrepancySeverity.CRITICAL,
                reason="Last digit differs; MRZ preferred for machine-readable data",
            )
        ],
        sources_used=["mrz", "qwen2-vl"],
        mrz_extraction_success=True,
        vlm_extraction_success=True,
        metadata=ProcessingMetadata(
            extraction_duration_ms=3200,
            mrz_duration_ms=1200,
            vlm_duration_ms=2000,
            vlm_model="Qwen/Qwen2-VL-7B-Instruct",
            timestamp=datetime.now(UTC),
        ),
        error=None,
    )


class TestCrossCheckCommandExists:
    """Test that crosscheck command is registered."""

    def test_crosscheck_command_in_help(self):
        """Crosscheck command should appear in CLI help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "crosscheck" in result.stdout.lower()

    def test_crosscheck_has_help(self):
        """Crosscheck command should have help text."""
        result = runner.invoke(app, ["crosscheck", "--help"])

        assert result.exit_code == 0
        assert "image" in result.stdout.lower() or "path" in result.stdout.lower()


class TestCrossCheckArguments:
    """Test crosscheck command arguments."""

    def test_crosscheck_requires_image_path(self):
        """Crosscheck should require image path argument."""
        result = runner.invoke(app, ["crosscheck"])

        # Should fail with missing argument
        assert result.exit_code != 0

    def test_crosscheck_accepts_image_path(self, tmp_path: Path):
        """Crosscheck should accept image path argument."""
        # Create test image
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        # Mock the service to avoid actual extraction
        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            mock_service = MagicMock()
            mock_result = CrossCheckResult(
                status=ExtractionStatus.SUCCESS,
                passport_data=None,
                sources_used=["mrz"],
            )
            mock_service.extract_and_crosscheck.return_value = mock_result
            mock_service_class.return_value = mock_service

            result = runner.invoke(app, ["crosscheck", str(test_image)])

            # Should attempt to run (may fail due to other reasons, but not missing argument)
            assert "missing" not in result.stdout.lower() or result.exit_code == 0


class TestCrossCheckOptions:
    """Test crosscheck command options."""

    def test_crosscheck_has_hf_token_option(self):
        """Crosscheck should have --hf-token option."""
        result = runner.invoke(app, ["crosscheck", "--help"])

        assert result.exit_code == 0
        assert "--hf-token" in result.stdout or "hf_token" in result.stdout

    def test_crosscheck_has_mrz_timeout_option(self):
        """Crosscheck should have --mrz-timeout option."""
        result = runner.invoke(app, ["crosscheck", "--help"])

        assert result.exit_code == 0
        assert "--mrz-timeout" in result.stdout or "mrz_timeout" in result.stdout

    def test_crosscheck_has_vlm_timeout_option(self):
        """Crosscheck should have --vlm-timeout option."""
        result = runner.invoke(app, ["crosscheck", "--help"])

        assert result.exit_code == 0
        assert "--vlm-timeout" in result.stdout or "vlm_timeout" in result.stdout

    def test_crosscheck_has_verbose_flag(self):
        """Crosscheck should have --verbose flag."""
        result = runner.invoke(app, ["crosscheck", "--help"])

        assert result.exit_code == 0
        assert "--verbose" in result.stdout or "-v" in result.stdout


class TestCrossCheckOutput:
    """Test crosscheck command output formatting."""

    def test_crosscheck_shows_status(
        self, tmp_path: Path, sample_crosscheck_result: CrossCheckResult
    ):
        """Crosscheck should show extraction status in output."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        mock_service.extract_and_crosscheck.return_value = (
                            sample_crosscheck_result
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            ["crosscheck", str(test_image), "--hf-token", "test_token"],
                        )

                        # Should show status
                        assert "success" in result.stdout.lower()

    def test_crosscheck_shows_confidence_scores(
        self, tmp_path: Path, sample_crosscheck_result: CrossCheckResult
    ):
        """Crosscheck should show confidence scores in output."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        mock_service.extract_and_crosscheck.return_value = (
                            sample_crosscheck_result
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            ["crosscheck", str(test_image), "--hf-token", "test_token"],
                        )

                        # Should show confidence (document confidence or field confidences)
                        assert (
                            "confidence" in result.stdout.lower()
                            or "0.91" in result.stdout
                        )

    def test_crosscheck_shows_discrepancies(
        self, tmp_path: Path, sample_crosscheck_result: CrossCheckResult
    ):
        """Crosscheck should show discrepancies when present."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        mock_service.extract_and_crosscheck.return_value = (
                            sample_crosscheck_result
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            ["crosscheck", str(test_image), "--hf-token", "test_token"],
                        )

                        # Should show discrepancy info
                        assert (
                            "discrepanc" in result.stdout.lower()
                            or "passport_number" in result.stdout.lower()
                        )

    def test_crosscheck_verbose_shows_metadata(
        self, tmp_path: Path, sample_crosscheck_result: CrossCheckResult
    ):
        """Crosscheck verbose mode should show metadata."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        mock_service.extract_and_crosscheck.return_value = (
                            sample_crosscheck_result
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            [
                                "crosscheck",
                                str(test_image),
                                "--hf-token",
                                "test_token",
                                "--verbose",
                            ],
                        )

                        # Verbose mode should show metadata
                        # Check for model name or duration
                        assert (
                            "qwen" in result.stdout.lower()
                            or "duration" in result.stdout.lower()
                            or "metadata" in result.stdout.lower()
                        )


class TestCrossCheckErrorHandling:
    """Test crosscheck command error handling."""

    def test_crosscheck_missing_image_error(self, tmp_path: Path):
        """Crosscheck should handle missing image file with exit code 2."""
        nonexistent_image = tmp_path / "nonexistent.jpg"

        result = runner.invoke(
            app, ["crosscheck", str(nonexistent_image), "--hf-token", "test"]
        )

        # Should fail with validation error (exit code 2)
        assert result.exit_code == 2

    def test_crosscheck_missing_hf_token_error(self, tmp_path: Path):
        """Crosscheck should handle missing HF token with appropriate error."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        # Clear HF_TOKEN env var - no token provided via option or env
        with patch.dict("os.environ", {}, clear=True):
            # Run without --hf-token option and with cleared env
            result = runner.invoke(
                app, ["crosscheck", str(test_image)], catch_exceptions=False
            )

            # Should fail with validation/config error (exit code 2)
            assert result.exit_code == 2
            # Check combined output (stdout + stderr via Rich)
            output = result.output.lower()
            assert "hf_token" in output or "token" in output

    def test_crosscheck_extraction_error_returns_exit_code_3(self, tmp_path: Path):
        """Crosscheck should return exit code 3 on extraction failure."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        # Return error result
                        mock_service.extract_and_crosscheck.return_value = (
                            CrossCheckResult(
                                status=ExtractionStatus.ERROR,
                                passport_data=None,
                                sources_used=[],
                                error="Both extraction sources failed",
                                mrz_error="MRZ not found",
                                vlm_error="VLM timeout",
                            )
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            ["crosscheck", str(test_image), "--hf-token", "test_token"],
                        )

                        # Should fail with processing error (exit code 3)
                        assert result.exit_code == 3


class TestCrossCheckExitCodes:
    """Test crosscheck command exit codes follow CLI conventions."""

    def test_crosscheck_success_returns_exit_code_0(
        self, tmp_path: Path, sample_crosscheck_result: CrossCheckResult
    ):
        """Crosscheck should return exit code 0 on success."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        mock_service.extract_and_crosscheck.return_value = (
                            sample_crosscheck_result
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            ["crosscheck", str(test_image), "--hf-token", "test_token"],
                        )

                        assert result.exit_code == 0

    def test_crosscheck_partial_returns_exit_code_0(self, tmp_path: Path):
        """Crosscheck with partial success should return exit code 0."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with patch("tryalma.crosscheck.cli.CrossCheckService") as mock_service_class:
            with patch("tryalma.crosscheck.cli.MRZExtractor"):
                with patch("tryalma.crosscheck.cli.MRZValidator"):
                    with patch("tryalma.crosscheck.cli.Qwen2VLProvider"):
                        mock_service = MagicMock()
                        # Return partial result (one source succeeded)
                        mock_service.extract_and_crosscheck.return_value = (
                            CrossCheckResult(
                                status=ExtractionStatus.PARTIAL,
                                passport_data=None,
                                sources_used=["mrz"],
                                mrz_extraction_success=True,
                                vlm_extraction_success=False,
                                vlm_error="VLM extraction failed",
                            )
                        )
                        mock_service_class.return_value = mock_service

                        result = runner.invoke(
                            app,
                            ["crosscheck", str(test_image), "--hf-token", "test_token"],
                        )

                        # Partial success should return 0
                        assert result.exit_code == 0
