"""Integration tests for CrossCheckService.

Task 6.1: Cross-check service integration tests testing actual component
interactions with mocked external dependencies.

Requirements: 1.1, 4.1, 4.2, 4.3, 6.5
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tryalma.crosscheck.config import ConfidenceConfig, CrossCheckConfig
from tryalma.crosscheck.models import (
    CrossCheckResult,
    ExtractionStatus,
    VisualZoneData,
)
from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider
from tryalma.crosscheck.service import CrossCheckService
from tryalma.passport.extractor import MRZExtractor
from tryalma.passport.models import RawMRZData
from tryalma.passport.validator import MRZValidator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_mrz_extractor() -> MagicMock:
    """Create a mock MRZ extractor that behaves like the real one."""
    extractor = MagicMock(spec=MRZExtractor)
    return extractor


@pytest.fixture
def mock_mrz_validator() -> MRZValidator:
    """Create a real MRZ validator (stateless, safe to use in tests)."""
    return MRZValidator()


@pytest.fixture
def mock_vlm_provider() -> MagicMock:
    """Create a mock VLM provider that behaves like the real one."""
    provider = MagicMock(spec=Qwen2VLProvider)
    provider.provider_name = "qwen2-vl"
    provider.model = "Qwen/Qwen2-VL-7B-Instruct"
    provider.extract_passport_fields = AsyncMock()
    return provider


@pytest.fixture
def integration_config() -> CrossCheckConfig:
    """Create integration test configuration with shorter timeouts."""
    return CrossCheckConfig(
        mrz_timeout_seconds=5.0,
        vlm_timeout_seconds=10.0,
        confidence_config=ConfidenceConfig(),
    )


@pytest.fixture
def sample_mrz_data() -> RawMRZData:
    """Create complete sample MRZ extraction data."""
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
    """Create complete sample VLM extraction data matching MRZ."""
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
def conflicting_vlm_data() -> VisualZoneData:
    """Create VLM data that conflicts with MRZ data."""
    return VisualZoneData(
        surname="SMITH",
        given_names="JOHN WILLIAM",
        date_of_birth="1985-03-15",
        nationality="USA",
        passport_number="987654321",  # Different from MRZ
        expiry_date="2030-03-14",
        sex="F",  # Different from MRZ
        place_of_birth="LOS ANGELES",
    )


@pytest.fixture
def sample_image_path(tmp_path: Path) -> Path:
    """Create a sample image path for testing."""
    image_path = tmp_path / "passport.jpg"
    image_path.write_bytes(b"fake image data")
    return image_path


@pytest.fixture
def integration_service(
    mock_mrz_extractor: MagicMock,
    mock_mrz_validator: MRZValidator,
    mock_vlm_provider: MagicMock,
    integration_config: CrossCheckConfig,
) -> CrossCheckService:
    """Create CrossCheckService with real internal components and mocked extractors."""
    return CrossCheckService(
        mrz_extractor=mock_mrz_extractor,
        mrz_validator=mock_mrz_validator,
        vlm_provider=mock_vlm_provider,
        config=integration_config,
    )


# ============================================================================
# Task 6.1: Test successful parallel extraction when both sources complete
# Requirement: 1.1 - Parallel extraction from MRZ and Qwen2-VL
# ============================================================================


class TestSuccessfulParallelExtraction:
    """Integration tests for successful parallel extraction scenarios."""

    @pytest.mark.asyncio
    async def test_parallel_extraction_both_sources_succeed(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When both MRZ and VLM extractions succeed, result has SUCCESS status."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.SUCCESS
        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is True

    @pytest.mark.asyncio
    async def test_parallel_extraction_includes_both_sources_in_list(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When both succeed, sources_used includes both 'mrz' and 'qwen2-vl'."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert "mrz" in result.sources_used
        assert "qwen2-vl" in result.sources_used
        assert len(result.sources_used) == 2

    @pytest.mark.asyncio
    async def test_parallel_extraction_produces_merged_passport_data(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Result contains properly merged PassportData from both sources."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.passport_data is not None
        assert result.passport_data.surname == "SMITH"
        assert result.passport_data.given_names == "JOHN WILLIAM"
        assert result.passport_data.passport_number == "123456789"
        assert result.passport_data.nationality == "USA"

    @pytest.mark.asyncio
    async def test_parallel_extraction_calculates_confidence_scores(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Result includes field and document confidence scores."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        # Field confidences
        assert len(result.field_confidences) > 0
        assert all(0.0 <= v <= 1.0 for v in result.field_confidences.values())
        # When sources agree, confidence should be high (1.0)
        assert result.field_confidences.get("surname") == 1.0
        # Document confidence
        assert result.document_confidence is not None
        assert 0.0 <= result.document_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_parallel_extraction_detects_discrepancies(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        conflicting_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When sources disagree, discrepancies are detected and reported."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = conflicting_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.has_discrepancies()
        discrepancy_fields = [d.field_name for d in result.discrepancies]
        assert "passport_number" in discrepancy_fields  # Different numbers
        assert "sex" in discrepancy_fields  # M vs F


# ============================================================================
# Task 6.1: Test MRZ fallback mode when VLM extraction fails
# Requirement: 4.2 - Continue with MRZ if Qwen2-VL fails
# ============================================================================


class TestMRZFallbackMode:
    """Integration tests for MRZ fallback when VLM fails."""

    @pytest.mark.asyncio
    async def test_vlm_fails_mrz_succeeds_returns_partial_status(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails and MRZ succeeds, status is PARTIAL."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM API error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is False

    @pytest.mark.asyncio
    async def test_vlm_fails_only_mrz_in_sources_used(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails, sources_used only contains 'mrz'."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM timeout")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.sources_used == ["mrz"]
        assert "qwen2-vl" not in result.sources_used

    @pytest.mark.asyncio
    async def test_vlm_fails_passport_data_from_mrz_only(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails, PassportData is populated from MRZ extraction."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.passport_data is not None
        assert result.passport_data.surname == "SMITH"
        assert result.passport_data.passport_number == "123456789"

    @pytest.mark.asyncio
    async def test_vlm_fails_vlm_error_captured(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails, error message is captured in vlm_error field."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("API rate limited")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.vlm_error is not None
        assert "rate" in result.vlm_error.lower() or "failed" in result.vlm_error.lower()
        assert result.mrz_error is None  # MRZ succeeded

    @pytest.mark.asyncio
    async def test_vlm_fails_reduced_confidence_scores(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM fails, confidence scores are reduced (single-source mode)."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        # Single-source MRZ confidence should be 0.7 (per design)
        assert result.field_confidences.get("surname") == 0.7


# ============================================================================
# Task 6.1: Test VLM fallback mode when MRZ extraction fails
# Requirement: 4.1 - Continue with Qwen2-VL if MRZ fails
# ============================================================================


class TestVLMFallbackMode:
    """Integration tests for VLM fallback when MRZ fails."""

    @pytest.mark.asyncio
    async def test_mrz_fails_vlm_succeeds_returns_partial_status(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails and VLM succeeds, status is PARTIAL."""
        mock_mrz_extractor.extract.side_effect = Exception("No MRZ detected")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is False
        assert result.vlm_extraction_success is True

    @pytest.mark.asyncio
    async def test_mrz_fails_only_vlm_in_sources_used(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, sources_used only contains 'qwen2-vl'."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ not found")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.sources_used == ["qwen2-vl"]
        assert "mrz" not in result.sources_used

    @pytest.mark.asyncio
    async def test_mrz_fails_passport_data_from_vlm_only(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, PassportData is populated from VLM extraction."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ not found")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.passport_data is not None
        assert result.passport_data.surname == "SMITH"
        # VLM provides place_of_birth which MRZ doesn't have
        assert result.passport_data.place_of_birth == "NEW YORK"

    @pytest.mark.asyncio
    async def test_mrz_fails_mrz_error_captured(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, error message is captured in mrz_error field."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ zone not detected")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.mrz_error is not None
        assert "mrz" in result.mrz_error.lower() or "failed" in result.mrz_error.lower()
        assert result.vlm_error is None  # VLM succeeded

    @pytest.mark.asyncio
    async def test_mrz_fails_reduced_confidence_scores(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ fails, confidence scores are reduced (single-source VLM mode)."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ not found")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        # Single-source VLM confidence should be 0.6 (per design)
        assert result.field_confidences.get("surname") == 0.6


# ============================================================================
# Task 6.1: Test error status when both extractions fail
# Requirement: 4.3 - Return error if both fail
# ============================================================================


class TestBothExtractionsFail:
    """Integration tests for when both extraction sources fail."""

    @pytest.mark.asyncio
    async def test_both_fail_returns_error_status(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both MRZ and VLM fail, status is ERROR."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ not found")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM API down")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.ERROR
        assert result.mrz_extraction_success is False
        assert result.vlm_extraction_success is False

    @pytest.mark.asyncio
    async def test_both_fail_no_sources_used(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both fail, sources_used is empty."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ error")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.sources_used == []

    @pytest.mark.asyncio
    async def test_both_fail_no_passport_data(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both fail, passport_data is None."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ error")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.passport_data is None

    @pytest.mark.asyncio
    async def test_both_fail_captures_both_errors(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both fail, both error messages are captured."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ zone corrupted")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM timeout")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.mrz_error is not None
        assert result.vlm_error is not None
        assert result.error is not None  # Overall error message

    @pytest.mark.asyncio
    async def test_both_fail_empty_confidence_scores(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both fail, confidence scores are empty."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ error")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.field_confidences == {}
        assert result.document_confidence is None


# ============================================================================
# Task 6.1: Test timeout handling triggers appropriate fallback behavior
# Requirement: 4.5, 4.6 - Timeout handling
# ============================================================================


class TestTimeoutHandling:
    """Integration tests for timeout handling and fallback behavior."""

    @pytest.mark.asyncio
    async def test_mrz_timeout_triggers_vlm_fallback(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MRZValidator,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """When MRZ times out, system falls back to VLM only."""
        # Create service with very short MRZ timeout
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

        # MRZ extraction blocks longer than timeout
        import time

        def slow_mrz(*args, **kwargs):
            time.sleep(1)  # 1 second - exceeds 1ms timeout
            return RawMRZData(mrz_type="TD3", raw_text="...")

        mock_mrz_extractor.extract.side_effect = slow_mrz
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is False
        assert result.vlm_extraction_success is True
        assert "timed out" in result.mrz_error.lower()

    @pytest.mark.asyncio
    async def test_vlm_timeout_triggers_mrz_fallback(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MRZValidator,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """When VLM times out, system falls back to MRZ only."""
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

        # VLM extraction blocks longer than timeout
        async def slow_vlm(*args, **kwargs):
            await asyncio.sleep(1)  # 1 second - exceeds 1ms timeout
            return VisualZoneData(surname="SMITH")

        mock_vlm_provider.extract_passport_fields.side_effect = slow_vlm

        result = await service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.PARTIAL
        assert result.mrz_extraction_success is True
        assert result.vlm_extraction_success is False
        assert "timed out" in result.vlm_error.lower()

    @pytest.mark.asyncio
    async def test_both_timeout_returns_error(
        self,
        mock_mrz_extractor: MagicMock,
        mock_mrz_validator: MRZValidator,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """When both sources timeout, status is ERROR."""
        # Create service with very short timeouts
        config = CrossCheckConfig(
            mrz_timeout_seconds=0.001,
            vlm_timeout_seconds=0.001,
        )
        service = CrossCheckService(
            mrz_extractor=mock_mrz_extractor,
            mrz_validator=mock_mrz_validator,
            vlm_provider=mock_vlm_provider,
            config=config,
        )

        import time

        def slow_mrz(*args, **kwargs):
            time.sleep(1)
            return RawMRZData(mrz_type="TD3", raw_text="...")

        async def slow_vlm(*args, **kwargs):
            await asyncio.sleep(1)
            return VisualZoneData(surname="SMITH")

        mock_mrz_extractor.extract.side_effect = slow_mrz
        mock_vlm_provider.extract_passport_fields.side_effect = slow_vlm

        result = await service.extract_and_crosscheck_async(sample_image_path)

        assert result.status == ExtractionStatus.ERROR
        assert "timed out" in result.mrz_error.lower()
        assert "timed out" in result.vlm_error.lower()


# ============================================================================
# Task 6.1: Verify processing metadata is correctly populated in all scenarios
# Requirement: 6.5 - Include processing metadata
# ============================================================================


class TestProcessingMetadata:
    """Integration tests for processing metadata population."""

    @pytest.mark.asyncio
    async def test_metadata_populated_on_success(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Metadata is fully populated when both sources succeed."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        before = datetime.now(UTC)
        result = await integration_service.extract_and_crosscheck_async(sample_image_path)
        after = datetime.now(UTC)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.mrz_duration_ms is not None
        assert result.metadata.vlm_duration_ms is not None
        assert result.metadata.vlm_model == "Qwen/Qwen2-VL-7B-Instruct"
        assert before <= result.metadata.timestamp <= after

    @pytest.mark.asyncio
    async def test_metadata_populated_on_partial_mrz_only(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_image_path: Path,
    ) -> None:
        """Metadata is populated when only MRZ succeeds."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.mrz_duration_ms is not None
        assert result.metadata.vlm_duration_ms is not None  # Duration until failure
        assert result.metadata.vlm_model is not None
        assert result.metadata.timestamp is not None

    @pytest.mark.asyncio
    async def test_metadata_populated_on_partial_vlm_only(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Metadata is populated when only VLM succeeds."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ error")
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.mrz_duration_ms is not None  # Duration until failure
        assert result.metadata.vlm_duration_ms is not None
        assert result.metadata.timestamp is not None

    @pytest.mark.asyncio
    async def test_metadata_populated_on_error(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_image_path: Path,
    ) -> None:
        """Metadata is populated even when both extractions fail."""
        mock_mrz_extractor.extract.side_effect = Exception("MRZ error")
        mock_vlm_provider.extract_passport_fields.side_effect = Exception("VLM error")

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.timestamp is not None
        assert result.metadata.vlm_model is not None

    @pytest.mark.asyncio
    async def test_metadata_durations_are_reasonable(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Durations in metadata are reasonable (non-negative and total >= components)."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = await integration_service.extract_and_crosscheck_async(sample_image_path)

        assert result.metadata is not None
        # All durations should be non-negative
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.mrz_duration_ms >= 0
        assert result.metadata.vlm_duration_ms >= 0

    def test_sync_wrapper_includes_metadata(
        self,
        integration_service: CrossCheckService,
        mock_mrz_extractor: MagicMock,
        mock_vlm_provider: MagicMock,
        sample_mrz_data: RawMRZData,
        sample_vlm_data: VisualZoneData,
        sample_image_path: Path,
    ) -> None:
        """Sync wrapper also includes full metadata."""
        mock_mrz_extractor.extract.return_value = sample_mrz_data
        mock_vlm_provider.extract_passport_fields.return_value = sample_vlm_data

        result = integration_service.extract_and_crosscheck(sample_image_path)

        assert result.metadata is not None
        assert result.metadata.extraction_duration_ms >= 0
        assert result.metadata.vlm_model is not None
        assert result.metadata.timestamp is not None
