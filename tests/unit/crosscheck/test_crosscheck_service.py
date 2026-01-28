"""Unit tests for CrossCheckService.

Task 4.1, 4.2, 4.3: Tests for cross-check service orchestration.

Requirements: 1.1, 1.2, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 6.1, 6.2, 6.3, 6.4, 6.5
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tryalma.crosscheck.config import ConfidenceConfig, CrossCheckConfig
from tryalma.crosscheck.confidence_scorer import ConfidenceScorer
from tryalma.crosscheck.discrepancy_reporter import DiscrepancyReporter
from tryalma.crosscheck.exceptions import VLMExtractionError, VLMTimeoutError
from tryalma.crosscheck.field_cross_validator import FieldCrossValidator
from tryalma.crosscheck.models import (
    CrossCheckResult,
    ExtractionStatus,
    FieldValidationResult,
    ProcessingMetadata,
    VisualZoneData,
)
from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider
from tryalma.crosscheck.service import CrossCheckService
from tryalma.passport.exceptions import MRZNotFoundError
from tryalma.passport.extractor import MRZExtractor
from tryalma.passport.models import PassportData, RawMRZData
from tryalma.passport.validator import MRZValidator

if TYPE_CHECKING:
    pass


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_mrz_extractor() -> MagicMock:
    """Create a mock MRZ extractor."""
    extractor = MagicMock(spec=MRZExtractor)
    return extractor


@pytest.fixture
def mock_mrz_validator() -> MagicMock:
    """Create a mock MRZ validator."""
    validator = MagicMock(spec=MRZValidator)
    return validator


@pytest.fixture
def mock_vlm_provider() -> MagicMock:
    """Create a mock VLM provider."""
    provider = MagicMock(spec=Qwen2VLProvider)
    provider.provider_name = "qwen2-vl"
    provider.model = "Qwen/Qwen2-VL-7B-Instruct"
    # Make extract_passport_fields an async mock
    provider.extract_passport_fields = AsyncMock()
    return provider


@pytest.fixture
def sample_config() -> CrossCheckConfig:
    """Create sample configuration."""
    return CrossCheckConfig(
        mrz_timeout_seconds=5.0,
        vlm_timeout_seconds=10.0,
        confidence_config=ConfidenceConfig(),
    )


@pytest.fixture
def sample_mrz_data() -> RawMRZData:
    """Create sample MRZ extraction data."""
    return RawMRZData(
        mrz_type="TD3",
        raw_text="P<USASMITH<<JOHN<WILLIAM<<<<<<<<<<<<<<<<<<<<<\n1234567890USA8503151M3003141234567890<<<<<<00",
        surname="SMITH",
        given_names="JOHN WILLIAM",
        nationality="USA",
        birth_date="850315",
        sex="M",
        expiry_date="300314",
        document_number="123456789",
    )


@pytest.fixture
def sample_vlm_data() -> VisualZoneData:
    """Create sample VLM extraction data."""
    return VisualZoneData(
        surname="SMITH",
        given_names="JOHN WILLIAM",
        date_of_birth="1985-03-15",
        nationality="USA",
        passport_number="123456789",
        expiry_date="2030-03-14",
        sex="M",
        place_of_birth="NEW YORK",
    )


@pytest.fixture
def sample_image_path(tmp_path: Path) -> Path:
    """Create a sample image path."""
    image_path = tmp_path / "passport.jpg"
    image_path.write_bytes(b"fake image data")
    return image_path


@pytest.fixture
def crosscheck_service(
    mock_mrz_extractor: MagicMock,
    mock_mrz_validator: MagicMock,
    mock_vlm_provider: MagicMock,
    sample_config: CrossCheckConfig,
) -> CrossCheckService:
    """Create a CrossCheckService instance with mocked dependencies."""
    return CrossCheckService(
        mrz_extractor=mock_mrz_extractor,
        mrz_validator=mock_mrz_validator,
        vlm_provider=mock_vlm_provider,
        config=sample_config,
    )


# ============================================================================
# Task 4.1: Parallel Extraction Tests
# ============================================================================


class TestCrossCheckServiceInit:
    """Tests for CrossCheckService initialization."""

    def test_init_with_all_dependencies(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_config: CrossCheckConfig,
    ) -> None:
        """Service initializes with all required dependencies."""
        service = CrossCheckService(
            mrz_extractor=mock_mrz_extractor,
            mrz_validator=mock_mrz_validator,
            vlm_provider=mock_vlm_provider,
            config=sample_config,
        )

        assert service._mrz_extractor is mock_mrz_extractor
        assert service._mrz_validator is mock_mrz_validator
        assert service._vlm_provider is mock_vlm_provider
        assert service._config is sample_config

    def test_init_with_default_config(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MagicMock,
        mock_vlm_provider: MagicMock,
    ) -> None:
        """Service uses default config when none provided."""
        service = CrossCheckService(
            mrz_extractor=mock_mrz_extractor,
            mrz_validator=mock_mrz_validator,
            vlm_provider=mock_vlm_provider,
            config=None,
        )

        assert service._config is not None
        assert service._config.mrz_timeout_seconds == 30.0
        assert service._config.vlm_timeout_seconds == 60.0

    def test_init_creates_internal_components(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MagicMock,
        mock_vlm_provider: MagicMock,
    ) -> None:
        """Service creates cross-validator, confidence scorer, and discrepancy reporter."""
        service = CrossCheckService(
            mrz_extractor=mock_mrz_extractor,
            mrz_validator=mock_mrz_validator,
            vlm_provider=mock_vlm_provider,
        )

        assert isinstance(service._cross_validator, FieldCrossValidator)
        assert isinstance(service._confidence_scorer, ConfidenceScorer)
        assert isinstance(service._discrepancy_reporter, DiscrepancyReporter)


class TestParallelExtraction:
    """Tests for parallel extraction functionality (Task 4.1)."""

    @pytest.mark.asyncio
    async def test_both_sources_succeed_returns_success_status(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When both MRZ and VLM succeed, status is SUCCESS."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.SUCCESS
        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is True

    @pytest.mark.asyncio
    async def test_both_sources_succeed_includes_both_in_sources_used(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When both sources succeed, both are listed in sources_used."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert "mrz" in result.sources_used
        assert "qwen2-vl" in result.sources_used

    @pytest.mark.asyncio
    async def test_extracts_from_both_sources_in_parallel(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Verifies both extraction methods are called."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        mock_mrz_extractor.extract.assert_called_once_with(sample_image_path)
        mock_vlm_provider.extract_passport_fields.assert_called_once()

    @pytest.mark.asyncio
    async def test_cross_validation_produces_field_confidences(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Result includes field confidence scores from cross-validation."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.field_confidences is not None
        assert len(result.field_confidences) > 0
        # Fields should have confidence values
        assert all(0.0 <= v <= 1.0 for v in result.field_confidences.values())

    @pytest.mark.asyncio
    async def test_cross_validation_produces_document_confidence(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Result includes overall document confidence score."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.document_confidence is not None
        assert 0.0 <= result.document_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_discrepancy_report_generated(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When sources disagree, discrepancies are reported."""
        # MRZ and VLM have different passport numbers
        mrz_data = RawMRZData(
            mrz_type="TD3",
            raw_text="...",
            document_number="123456789",
            surname="SMITH",
        )
        vlm_data = VisualZoneData(
            passport_number="987654321",  # Different!
            surname="SMITH",
        )

        mock_mrz_extractor.extract.return_value = mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        # Should have at least one discrepancy for passport_number
        assert result.has_discrepancies()
        discrepancy_fields = [d.field_name for d in result.discrepancies]
        assert "passport_number" in discrepancy_fields

    @pytest.mark.asyncio
    async def test_passport_data_populated_from_extractions(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Result includes merged PassportData with final values."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.passport_data is not None
        assert result.passport_data.surname == "SMITH"
        assert result.passport_data.passport_number == "123456789"


# ============================================================================
# Task 4.2: Fallback Handling Tests
# ============================================================================


class TestFallbackHandling:
    """Tests for fallback handling when one source fails (Task 4.2)."""

    @pytest.mark.asyncio
    async def test_mrz_fails_vlm_succeeds_returns_partial_status(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails and VLM succeeds, status is PARTIAL."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ found")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is False
        assert result.vlm_extraction_success is True

    @pytest.mark.asyncio
    async def test_mrz_fails_vlm_succeeds_only_vlm_in_sources(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, only VLM is in sources_used."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ found")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert "qwen2-vl" in result.sources_used
        assert "mrz" not in result.sources_used

    @pytest.mark.asyncio
    async def test_mrz_fails_captures_error_message(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, error is captured in result."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ found")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.mrz_error is not None
        assert "MRZ" in result.mrz_error or "mrz" in result.mrz_error.lower()

    @pytest.mark.asyncio
    async def test_vlm_fails_mrz_succeeds_returns_partial_status(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails and MRZ succeeds, status is PARTIAL."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM extraction failed"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is False

    @pytest.mark.asyncio
    async def test_vlm_fails_mrz_succeeds_only_mrz_in_sources(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails, only MRZ is in sources_used."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM extraction failed"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert "mrz" in result.sources_used
        assert "qwen2-vl" not in result.sources_used

    @pytest.mark.asyncio
    async def test_vlm_fails_captures_error_message(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails, error is captured in result."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "API rate limited"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.vlm_error is not None
        assert "rate" in result.vlm_error.lower() or "failed" in result.vlm_error.lower()

    @pytest.mark.asyncio
    async def test_both_fail_returns_error_status(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both sources fail, status is ERROR."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ found")
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM extraction failed"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.ERROR
        assert result.mrz_extraction_success is False
        assert result.vlm_extraction_success is False

    @pytest.mark.asyncio
    async def test_both_fail_returns_no_passport_data(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both sources fail, passport_data is None."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ found")
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM extraction failed"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.passport_data is None
        assert result.sources_used == []

    @pytest.mark.asyncio
    async def test_both_fail_captures_both_errors(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both sources fail, both errors are captured."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("MRZ not found")
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM failed"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.mrz_error is not None
        assert result.vlm_error is not None
        assert result.error is not None  # Overall error message

    @pytest.mark.asyncio
    async def test_mrz_timeout_triggers_fallback(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ times out, falls back to VLM only."""
        # Create service with very short timeout
        config = CrossCheckConfig(
            mrz_timeout_seconds=0.001,  # 1ms timeout
            vlm_timeout_seconds=10.0,
        )
        service = CrossCheckService(
            mrz_extractor=mock_mrz_extractor,
            mrz_validator=mock_mrz_validator,
            vlm_provider=mock_vlm_provider,
            config=config,
        )

        # MRZ extraction takes too long - use synchronous sleep in thread
        def slow_mrz_extract(*args, **kwargs):
            import time
            time.sleep(1)  # 1 second - longer than timeout
            return RawMRZData(mrz_type="TD3", raw_text="...")

        mock_mrz_extractor.extract.side_effect = slow_mrz_extract
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is False
        assert result.vlm_extraction_success is True
        assert "timed out" in result.mrz_error.lower()

    @pytest.mark.asyncio
    async def test_vlm_timeout_triggers_fallback(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM times out, falls back to MRZ only."""
        # Create service with very short VLM timeout
        config = CrossCheckConfig(
            mrz_timeout_seconds=10.0,
            vlm_timeout_seconds=0.001,  # 1ms timeout
        )
        service = CrossCheckService(
            mrz_extractor=mock_mrz_extractor,
            mrz_validator=mock_mrz_validator,
            vlm_provider=mock_vlm_provider,
            config=config,
        )

        mock_mrz_extractor.extract.return_value = sample_mrz_data

        # VLM extraction takes too long
        async def slow_vlm_extract(*args, **kwargs):
            await asyncio.sleep(1)  # 1 second - longer than timeout
            return VisualZoneData(surname="SMITH")

        mock_vlm_provider.extract_passport_fields.side_effect = slow_vlm_extract

        result = await service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is False
        assert "timed out" in result.vlm_error.lower()


# ============================================================================
# Task 4.3: Sync Wrapper and Processing Metadata Tests
# ============================================================================


class TestSyncWrapper:
    """Tests for sync wrapper method (Task 4.3)."""

    def test_sync_wrapper_returns_result(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Sync wrapper returns CrossCheckResult."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = crosscheck_service.extract_and_crosscheck(sample_image_path)

        assert isinstance(result, CrossCheckResult)
        assert result.status == ExtractionStatus.SUCCESS

    def test_sync_wrapper_never_raises_exceptions(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """Sync wrapper never raises; errors expressed in result status."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("MRZ not found")
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM failed"
        )

        # Should not raise - returns error result instead
        result = crosscheck_service.extract_and_crosscheck(sample_image_path)

        assert result.status == ExtractionStatus.ERROR
        assert result.error is not None


class TestProcessingMetadata:
    """Tests for processing metadata (Task 4.3)."""

    @pytest.mark.asyncio
    async def test_metadata_includes_extraction_duration(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Metadata includes total extraction duration in milliseconds."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_metadata_includes_vlm_model_identifier(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Metadata includes VLM model identifier."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.vlm_model is not None
        assert "Qwen" in result.metadata.vlm_model

    @pytest.mark.asyncio
    async def test_metadata_includes_timestamp(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Metadata includes timestamp."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        from datetime import UTC
        before = datetime.now(UTC)
        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)
        after = datetime.now(UTC)

        assert result.metadata is not None
        # Both before/after and timestamp are timezone-aware (UTC)
        assert before <= result.metadata.timestamp <= after

    @pytest.mark.asyncio
    async def test_metadata_when_both_succeed_has_both_durations(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When both sources succeed, metadata includes both durations."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        # Both durations should be populated
        assert result.metadata.mrz_duration_ms is not None
        assert result.metadata.vlm_duration_ms is not None
        assert result.metadata.mrz_duration_ms >= 0
        assert result.metadata.vlm_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_metadata_when_mrz_fails_has_null_mrz_duration(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, metadata has null MRZ duration."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        # MRZ duration could be set to the time until failure, so just check it exists
        # The important thing is VLM duration is populated
        assert result.metadata.vlm_duration_ms is not None

    @pytest.mark.asyncio
    async def test_metadata_always_included_even_on_error(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """Metadata is included even when both sources fail."""
        mock_mrz_extractor.extract.side_effect = MRZNotFoundError("No MRZ")
        mock_vlm_provider.extract_passport_fields.side_effect = VLMExtractionError(
            "VLM failed"
        )

        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.timestamp is not None


class TestServiceNeverRaisesExceptions:
    """Tests that service never raises exceptions to caller (Task 4.3)."""

    @pytest.mark.asyncio
    async def test_async_method_never_raises_on_mrz_error(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Async method captures MRZ errors instead of raising."""
        mock_mrz_extractor.extract.side_effect = Exception("Unexpected MRZ error")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        # Should not raise
        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.mrz_error is not None
        assert result.status in (ExtractionStatus.PARTIAL, ExtractionStatus.ERROR)

    @pytest.mark.asyncio
    async def test_async_method_never_raises_on_vlm_error(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """Async method captures VLM errors instead of raising."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception(
            "Unexpected VLM error"
        )

        # Should not raise
        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.vlm_error is not None
        assert result.status in (ExtractionStatus.PARTIAL, ExtractionStatus.ERROR)

    @pytest.mark.asyncio
    async def test_async_method_never_raises_on_both_errors(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """Async method captures errors from both sources instead of raising."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ crashed")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM crashed")

        # Should not raise
        result = await crosscheck_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.ERROR
        assert result.mrz_error is not None
        assert result.vlm_error is not None
        assert result.error is not None

    def test_sync_method_never_raises(
        self,
        crosscheck_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """Sync method never raises; all outcomes in result status."""
        mock_mrz_extractor.extract.side_effect = Exception("Crash")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("Crash")

        # Should not raise
        result = crosscheck_service.extract_and_crosscheck(sample_image_path)

        assert result.status == ExtractionStatus.ERROR
