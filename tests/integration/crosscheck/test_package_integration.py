"""Integration tests for cross-check package exports and architecture integration.

Task 5.1: Tests for integrating cross-check service with existing architecture.

Requirements: 1.1, 1.4
"""

import pytest


class TestPackageExports:
    """Test that all cross-check types and services are exported from main package."""

    def test_export_crosscheck_service_from_main_package(self):
        """CrossCheckService should be importable from tryalma package."""
        from tryalma import CrossCheckService

        assert CrossCheckService is not None

    def test_export_crosscheck_config_from_main_package(self):
        """CrossCheckConfig should be importable from tryalma package."""
        from tryalma import CrossCheckConfig

        assert CrossCheckConfig is not None

    def test_export_qwen2vl_provider_from_main_package(self):
        """Qwen2VLProvider should be importable from tryalma package."""
        from tryalma import Qwen2VLProvider

        assert Qwen2VLProvider is not None

    def test_export_crosscheck_result_from_main_package(self):
        """CrossCheckResult should be importable from tryalma package."""
        from tryalma import CrossCheckResult

        assert CrossCheckResult is not None

    def test_export_extraction_status_from_main_package(self):
        """ExtractionStatus should be importable from tryalma package."""
        from tryalma import ExtractionStatus

        assert ExtractionStatus is not None

    def test_export_crosscheck_exceptions_from_main_package(self):
        """Cross-check exceptions should be importable from tryalma package."""
        from tryalma import (
            ConfigurationError,
            CrossCheckError,
            VLMExtractionError,
            VLMTimeoutError,
        )

        assert ConfigurationError is not None
        assert CrossCheckError is not None
        assert VLMExtractionError is not None
        assert VLMTimeoutError is not None

    def test_export_confidence_scorer_from_main_package(self):
        """ConfidenceScorer should be importable from tryalma package."""
        from tryalma import ConfidenceScorer

        assert ConfidenceScorer is not None

    def test_export_field_cross_validator_from_main_package(self):
        """FieldCrossValidator should be importable from tryalma package."""
        from tryalma import FieldCrossValidator

        assert FieldCrossValidator is not None

    def test_export_discrepancy_reporter_from_main_package(self):
        """DiscrepancyReporter should be importable from tryalma package."""
        from tryalma import DiscrepancyReporter

        assert DiscrepancyReporter is not None


class TestDependencyInjection:
    """Test that cross-check service integrates with existing DI pattern."""

    def test_crosscheck_service_accepts_mrz_extractor(self):
        """CrossCheckService should accept MRZExtractor via dependency injection."""
        from tryalma import CrossCheckService
        from tryalma.passport.extractor import MRZExtractor
        from tryalma.passport.validator import MRZValidator
        from tryalma.crosscheck import Qwen2VLProvider

        mrz_extractor = MRZExtractor()
        mrz_validator = MRZValidator()
        vlm_provider = Qwen2VLProvider(hf_token="test_token")

        service = CrossCheckService(
            mrz_extractor=mrz_extractor,
            mrz_validator=mrz_validator,
            vlm_provider=vlm_provider,
        )

        assert service is not None
        assert service._mrz_extractor is mrz_extractor
        assert service._mrz_validator is mrz_validator
        assert service._vlm_provider is vlm_provider

    def test_crosscheck_service_accepts_config(self):
        """CrossCheckService should accept optional CrossCheckConfig."""
        from tryalma import CrossCheckService, CrossCheckConfig
        from tryalma.passport.extractor import MRZExtractor
        from tryalma.passport.validator import MRZValidator
        from tryalma.crosscheck import Qwen2VLProvider

        config = CrossCheckConfig(
            hf_token="test_token",
            mrz_timeout_seconds=15.0,
            vlm_timeout_seconds=45.0,
        )

        service = CrossCheckService(
            mrz_extractor=MRZExtractor(),
            mrz_validator=MRZValidator(),
            vlm_provider=Qwen2VLProvider(hf_token="test_token"),
            config=config,
        )

        assert service._config is config
        assert service._config.mrz_timeout_seconds == 15.0
        assert service._config.vlm_timeout_seconds == 45.0

    def test_crosscheck_service_uses_default_config(self):
        """CrossCheckService should use default config when none provided."""
        from tryalma import CrossCheckService
        from tryalma.passport.extractor import MRZExtractor
        from tryalma.passport.validator import MRZValidator
        from tryalma.crosscheck import Qwen2VLProvider

        service = CrossCheckService(
            mrz_extractor=MRZExtractor(),
            mrz_validator=MRZValidator(),
            vlm_provider=Qwen2VLProvider(hf_token="test_token"),
        )

        assert service._config is not None
        assert service._config.mrz_timeout_seconds == 30.0  # default
        assert service._config.vlm_timeout_seconds == 60.0  # default


class TestServiceCoexistence:
    """Test that cross-check service works alongside existing services."""

    def test_crosscheck_service_alongside_passport_service(self):
        """Both PassportExtractionService and CrossCheckService can coexist."""
        from tryalma.passport.service import PassportExtractionService
        from tryalma import CrossCheckService
        from tryalma.passport.extractor import MRZExtractor
        from tryalma.passport.validator import MRZValidator
        from tryalma.crosscheck import Qwen2VLProvider

        # Create shared components
        mrz_extractor = MRZExtractor()
        mrz_validator = MRZValidator()

        # Create passport extraction service
        passport_service = PassportExtractionService(mrz_extractor, mrz_validator)

        # Create cross-check service with same MRZ components
        crosscheck_service = CrossCheckService(
            mrz_extractor=mrz_extractor,
            mrz_validator=mrz_validator,
            vlm_provider=Qwen2VLProvider(hf_token="test_token"),
        )

        # Both services should be functional
        assert passport_service is not None
        assert crosscheck_service is not None

        # They share the same MRZ components
        assert crosscheck_service._mrz_extractor is passport_service._extractor
        assert crosscheck_service._mrz_validator is passport_service._validator
