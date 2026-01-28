"""Cross-check service for dual-source passport extraction with validation.

Task 4.1, 4.2, 4.3: CrossCheckService orchestrating parallel extraction.

Requirements: 1.1, 1.2, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 6.1, 6.2, 6.3, 6.4, 6.5
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, date
from pathlib import Path
from typing import TYPE_CHECKING

from tryalma.crosscheck.config import CrossCheckConfig
from tryalma.crosscheck.confidence_scorer import ConfidenceScorer
from tryalma.crosscheck.discrepancy_reporter import DiscrepancyReporter
from tryalma.crosscheck.field_cross_validator import FieldCrossValidator
from tryalma.crosscheck.models import (
    CrossCheckResult,
    ExtractionStatus,
    FieldValidationResult,
    ProcessingMetadata,
    VisualZoneData,
)
from tryalma.passport.models import PassportData, RawMRZData

if TYPE_CHECKING:
    from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider
    from tryalma.passport.extractor import MRZExtractor
    from tryalma.passport.validator import MRZValidator


class CrossCheckService:
    """Orchestrates dual-source passport extraction with cross-validation.

    Coordinates parallel extraction from MRZ (via PassportEye) and VLM (via
    Qwen2-VL Hugging Face Inference API), cross-validates results, calculates
    confidence scores, and generates discrepancy reports.

    This service never raises exceptions to callers; all outcomes are expressed
    through the CrossCheckResult status and error fields.

    Attributes:
        _mrz_extractor: MRZ extraction component.
        _mrz_validator: MRZ validation component.
        _vlm_provider: VLM extraction provider.
        _config: Service configuration.
    """

    def __init__(
        self,
        mrz_extractor: MRZExtractor,
        mrz_validator: MRZValidator,
        vlm_provider: Qwen2VLProvider,
        config: CrossCheckConfig | None = None,
    ) -> None:
        """Initialize the cross-check service.

        Args:
            mrz_extractor: Component for MRZ extraction.
            mrz_validator: Component for MRZ validation.
            vlm_provider: Provider for VLM extraction.
            config: Optional configuration. Uses defaults if None.
        """
        self._mrz_extractor = mrz_extractor
        self._mrz_validator = mrz_validator
        self._vlm_provider = vlm_provider
        self._config = config or CrossCheckConfig()

        # Internal components for cross-validation
        self._cross_validator = FieldCrossValidator()
        self._confidence_scorer = ConfidenceScorer(self._config.confidence_config)
        self._discrepancy_reporter = DiscrepancyReporter()

    def extract_and_crosscheck(self, image_path: Path) -> CrossCheckResult:
        """Extract passport data from both sources and cross-validate.

        Synchronous wrapper for backward compatibility. Runs the async
        extraction method using asyncio.run().

        This method never raises exceptions; all outcomes are expressed
        through the result status and error fields.

        Args:
            image_path: Path to the passport image file.

        Returns:
            CrossCheckResult with validated data, confidence scores, and discrepancies.
        """
        try:
            return asyncio.run(self.extract_and_crosscheck_async(image_path))
        except Exception as e:
            # Should not happen, but ensure we never raise
            return self._create_error_result(
                image_path=image_path,
                mrz_error=None,
                vlm_error=None,
                overall_error=f"Unexpected error: {e}",
                start_time=time.perf_counter(),
            )

    async def extract_and_crosscheck_async(self, image_path: Path) -> CrossCheckResult:
        """Extract passport data from both sources and cross-validate asynchronously.

        Runs MRZ and VLM extraction in parallel with configurable timeouts.
        Cross-validates results and calculates confidence scores.

        This method never raises exceptions; all outcomes are expressed
        through the result status and error fields.

        Args:
            image_path: Path to the passport image file.

        Returns:
            CrossCheckResult with validated data, confidence scores, and discrepancies.
        """
        start_time = time.perf_counter()

        # Run extractions in parallel with individual timeout handling
        mrz_result, mrz_error, mrz_duration = await self._extract_mrz_with_timeout(
            image_path
        )
        vlm_result, vlm_error, vlm_duration = await self._extract_vlm_with_timeout(
            image_path
        )

        # Determine extraction success
        mrz_success = mrz_result is not None
        vlm_success = vlm_result is not None

        # Build sources used list
        sources_used: list[str] = []
        if mrz_success:
            sources_used.append("mrz")
        if vlm_success:
            sources_used.append("qwen2-vl")

        # Determine status
        if mrz_success and vlm_success:
            status = ExtractionStatus.SUCCESS
        elif mrz_success or vlm_success:
            status = ExtractionStatus.PARTIAL
        else:
            status = ExtractionStatus.ERROR

        # Handle complete failure case
        if status == ExtractionStatus.ERROR:
            return self._create_error_result(
                image_path=image_path,
                mrz_error=mrz_error,
                vlm_error=vlm_error,
                overall_error="Both extraction sources failed",
                start_time=start_time,
                mrz_duration=mrz_duration,
                vlm_duration=vlm_duration,
            )

        # Cross-validate extracted data
        validation_results = self._cross_validator.cross_validate(
            mrz_data=mrz_result,
            visual_data=vlm_result,
        )

        # Calculate confidence scores
        field_confidences = self._calculate_field_confidences(
            validation_results, sources_used
        )
        document_confidence = self._confidence_scorer.calculate_document_confidence(
            field_confidences
        )

        # Generate discrepancy report
        discrepancies = self._discrepancy_reporter.generate_report(validation_results)

        # Build merged passport data
        passport_data = self._build_passport_data(
            image_path=image_path,
            mrz_data=mrz_result,
            vlm_data=vlm_result,
            validation_results=validation_results,
        )

        # Build processing metadata
        end_time = time.perf_counter()
        metadata = ProcessingMetadata(
            extraction_duration_ms=int((end_time - start_time) * 1000),
            mrz_duration_ms=mrz_duration,
            vlm_duration_ms=vlm_duration,
            vlm_model=self._vlm_provider.model,
            timestamp=datetime.now(UTC),
        )

        return CrossCheckResult(
            status=status,
            passport_data=passport_data,
            field_confidences=field_confidences,
            document_confidence=document_confidence,
            discrepancies=discrepancies,
            sources_used=sources_used,
            mrz_extraction_success=mrz_success,
            vlm_extraction_success=vlm_success,
            metadata=metadata,
            error=None,
            mrz_error=mrz_error,
            vlm_error=vlm_error,
        )

    async def _extract_mrz_with_timeout(
        self, image_path: Path
    ) -> tuple[RawMRZData | None, str | None, int | None]:
        """Extract MRZ data with timeout handling.

        Args:
            image_path: Path to the passport image.

        Returns:
            Tuple of (mrz_data, error_message, duration_ms).
            On success: (data, None, duration).
            On failure: (None, error_message, duration or None).
        """
        start = time.perf_counter()
        try:
            async with asyncio.timeout(self._config.mrz_timeout_seconds):
                # MRZ extraction is synchronous, run in thread pool
                result = await asyncio.to_thread(
                    self._mrz_extractor.extract, image_path
                )
                duration_ms = int((time.perf_counter() - start) * 1000)
                return result, None, duration_ms
        except TimeoutError:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return None, f"MRZ extraction timed out after {self._config.mrz_timeout_seconds}s", duration_ms
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return None, f"MRZ extraction failed: {e}", duration_ms

    async def _extract_vlm_with_timeout(
        self, image_path: Path
    ) -> tuple[VisualZoneData | None, str | None, int | None]:
        """Extract VLM data with timeout handling.

        Args:
            image_path: Path to the passport image.

        Returns:
            Tuple of (vlm_data, error_message, duration_ms).
            On success: (data, None, duration).
            On failure: (None, error_message, duration or None).
        """
        start = time.perf_counter()
        try:
            async with asyncio.timeout(self._config.vlm_timeout_seconds):
                result = await self._vlm_provider.extract_passport_fields(
                    image_path, timeout=self._config.vlm_timeout_seconds
                )
                duration_ms = int((time.perf_counter() - start) * 1000)
                return result, None, duration_ms
        except TimeoutError:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return None, f"VLM extraction timed out after {self._config.vlm_timeout_seconds}s", duration_ms
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return None, f"VLM extraction failed: {e}", duration_ms

    def _calculate_field_confidences(
        self,
        validation_results: list[FieldValidationResult],
        sources_used: list[str],
    ) -> dict[str, float]:
        """Calculate confidence scores for each field.

        Args:
            validation_results: Results from cross-validation.
            sources_used: List of sources that succeeded.

        Returns:
            Dictionary mapping field names to confidence scores.
        """
        field_confidences: dict[str, float] = {}
        for result in validation_results:
            confidence = self._confidence_scorer.calculate_field_confidence(
                result, sources_used
            )
            field_confidences[result.field_name] = confidence
        return field_confidences

    def _build_passport_data(
        self,
        image_path: Path,
        mrz_data: RawMRZData | None,
        vlm_data: VisualZoneData | None,
        validation_results: list[FieldValidationResult],
    ) -> PassportData:
        """Build merged PassportData from validation results.

        Args:
            image_path: Source image path.
            mrz_data: MRZ extraction data (if available).
            vlm_data: VLM extraction data (if available).
            validation_results: Cross-validation results with final values.

        Returns:
            PassportData with merged field values.
        """
        # Build a map of final values from validation results
        final_values: dict[str, str | None] = {}
        for result in validation_results:
            final_values[result.field_name] = result.final_value

        # Parse dates from string format
        date_of_birth = self._parse_date(final_values.get("date_of_birth"))
        expiry_date = self._parse_date(final_values.get("expiry_date"))

        # Determine MRZ validity from validator if MRZ was available
        mrz_valid = False
        mrz_type = None
        if mrz_data is not None:
            mrz_type = mrz_data.mrz_type
            # Validate MRZ if we have raw text
            if mrz_data.raw_text:
                validation_result = self._mrz_validator.validate(mrz_data.raw_text)
                mrz_valid = validation_result.is_valid

        return PassportData(
            source_file=image_path,
            surname=final_values.get("surname"),
            given_names=final_values.get("given_names"),
            date_of_birth=date_of_birth,
            nationality=final_values.get("nationality"),
            passport_number=final_values.get("passport_number"),
            expiry_date=expiry_date,
            sex=final_values.get("sex"),
            place_of_birth=final_values.get("place_of_birth"),
            mrz_type=mrz_type,
            mrz_valid=mrz_valid,
        )

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse a date string to a date object.

        Handles ISO format (YYYY-MM-DD) and MRZ format (YYMMDD).

        Args:
            date_str: Date string to parse.

        Returns:
            date object or None if parsing fails.
        """
        if not date_str:
            return None

        # Try ISO format first
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            pass

        # Try MRZ format (YYMMDD)
        if len(date_str) == 6 and date_str.isdigit():
            try:
                yy = int(date_str[:2])
                mm = int(date_str[2:4])
                dd = int(date_str[4:6])
                # Interpret YY as 19xx if >= 50, else 20xx
                year = 1900 + yy if yy >= 50 else 2000 + yy
                return date(year, mm, dd)
            except ValueError:
                pass

        return None

    def _create_error_result(
        self,
        image_path: Path,
        mrz_error: str | None,
        vlm_error: str | None,
        overall_error: str,
        start_time: float,
        mrz_duration: int | None = None,
        vlm_duration: int | None = None,
    ) -> CrossCheckResult:
        """Create an error result when extraction fails completely.

        Args:
            image_path: Source image path.
            mrz_error: MRZ error message if any.
            vlm_error: VLM error message if any.
            overall_error: Overall error message.
            start_time: Start time for duration calculation.
            mrz_duration: MRZ extraction duration if available.
            vlm_duration: VLM extraction duration if available.

        Returns:
            CrossCheckResult with ERROR status.
        """
        end_time = time.perf_counter()
        metadata = ProcessingMetadata(
            extraction_duration_ms=int((end_time - start_time) * 1000),
            mrz_duration_ms=mrz_duration,
            vlm_duration_ms=vlm_duration,
            vlm_model=self._vlm_provider.model,
            timestamp=datetime.now(UTC),
        )

        return CrossCheckResult(
            status=ExtractionStatus.ERROR,
            passport_data=None,
            field_confidences={},
            document_confidence=None,
            discrepancies=[],
            sources_used=[],
            mrz_extraction_success=False,
            vlm_extraction_success=False,
            metadata=metadata,
            error=overall_error,
            mrz_error=mrz_error,
            vlm_error=vlm_error,
        )
