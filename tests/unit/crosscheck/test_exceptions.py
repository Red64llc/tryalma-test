"""Unit tests for cross-check exception types.

Task 1.2: Test exception hierarchy for cross-check operations.

Requirements: 7.4, 7.5
"""

import pytest


class TestCrossCheckError:
    """Tests for CrossCheckError base exception."""

    def test_crosscheck_error_extends_processing_error(self):
        """CrossCheckError should extend ProcessingError."""
        from tryalma.crosscheck.exceptions import CrossCheckError
        from tryalma.exceptions import ProcessingError

        error = CrossCheckError()

        assert isinstance(error, ProcessingError)

    def test_crosscheck_error_has_default_message(self):
        """CrossCheckError should have default message."""
        from tryalma.crosscheck.exceptions import CrossCheckError

        error = CrossCheckError()

        assert "cross-check" in error.message.lower() or "cross check" in error.message.lower()

    def test_crosscheck_error_accepts_custom_message(self):
        """CrossCheckError should accept custom message."""
        from tryalma.crosscheck.exceptions import CrossCheckError

        error = CrossCheckError("Custom error message")

        assert error.message == "Custom error message"

    def test_crosscheck_error_has_exit_code_3(self):
        """CrossCheckError should have exit code 3 (processing error)."""
        from tryalma.crosscheck.exceptions import CrossCheckError

        error = CrossCheckError()

        assert error.exit_code == 3


class TestVLMExtractionError:
    """Tests for VLMExtractionError exception."""

    def test_vlm_extraction_error_extends_crosscheck_error(self):
        """VLMExtractionError should extend CrossCheckError."""
        from tryalma.crosscheck.exceptions import CrossCheckError, VLMExtractionError

        error = VLMExtractionError()

        assert isinstance(error, CrossCheckError)

    def test_vlm_extraction_error_has_default_message(self):
        """VLMExtractionError should have descriptive default message."""
        from tryalma.crosscheck.exceptions import VLMExtractionError

        error = VLMExtractionError()

        assert "qwen2-vl" in error.message.lower() or "vlm" in error.message.lower()
        assert "extract" in error.message.lower() or "failed" in error.message.lower()

    def test_vlm_extraction_error_accepts_custom_message(self):
        """VLMExtractionError should accept custom message."""
        from tryalma.crosscheck.exceptions import VLMExtractionError

        error = VLMExtractionError("Failed to parse VLM response")

        assert error.message == "Failed to parse VLM response"

    def test_vlm_extraction_error_has_exit_code_3(self):
        """VLMExtractionError should inherit exit code 3."""
        from tryalma.crosscheck.exceptions import VLMExtractionError

        error = VLMExtractionError()

        assert error.exit_code == 3


class TestVLMTimeoutError:
    """Tests for VLMTimeoutError exception."""

    def test_vlm_timeout_error_extends_crosscheck_error(self):
        """VLMTimeoutError should extend CrossCheckError."""
        from tryalma.crosscheck.exceptions import CrossCheckError, VLMTimeoutError

        error = VLMTimeoutError()

        assert isinstance(error, CrossCheckError)

    def test_vlm_timeout_error_has_default_message(self):
        """VLMTimeoutError should have descriptive default message."""
        from tryalma.crosscheck.exceptions import VLMTimeoutError

        error = VLMTimeoutError()

        assert "timeout" in error.message.lower() or "timed out" in error.message.lower()

    def test_vlm_timeout_error_accepts_custom_message(self):
        """VLMTimeoutError should accept custom message."""
        from tryalma.crosscheck.exceptions import VLMTimeoutError

        error = VLMTimeoutError("VLM extraction timed out after 60s")

        assert error.message == "VLM extraction timed out after 60s"


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_extends_validation_error(self):
        """ConfigurationError should extend ValidationError."""
        from tryalma.crosscheck.exceptions import ConfigurationError
        from tryalma.exceptions import ValidationError

        error = ConfigurationError()

        assert isinstance(error, ValidationError)

    def test_configuration_error_has_default_message(self):
        """ConfigurationError should have descriptive default message."""
        from tryalma.crosscheck.exceptions import ConfigurationError

        error = ConfigurationError()

        assert "configuration" in error.message.lower() or "config" in error.message.lower()

    def test_configuration_error_accepts_custom_message(self):
        """ConfigurationError should accept custom message."""
        from tryalma.crosscheck.exceptions import ConfigurationError

        error = ConfigurationError("HF_TOKEN is required")

        assert error.message == "HF_TOKEN is required"

    def test_configuration_error_has_exit_code_2(self):
        """ConfigurationError should have exit code 2 (validation error)."""
        from tryalma.crosscheck.exceptions import ConfigurationError

        error = ConfigurationError()

        assert error.exit_code == 2

    def test_configuration_error_provides_guidance_for_missing_token(self):
        """ConfigurationError should be usable for missing HF token guidance. (Requirement 7.5)"""
        from tryalma.crosscheck.exceptions import ConfigurationError

        error = ConfigurationError(
            "HF_TOKEN required. Set HF_TOKEN environment variable or pass hf_token parameter."
        )

        assert "HF_TOKEN" in error.message
        assert "environment" in error.message.lower() or "parameter" in error.message.lower()
