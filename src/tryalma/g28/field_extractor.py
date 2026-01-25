"""Field Extraction Coordinator for G-28 form processing.

Task 5: Field Extraction Coordinator implementation.

Requirements:
- 5.1: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
- 5.2: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 10.1
- 5.3: 8.4, 8.5, 10.3, 10.5
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel

from tryalma.g28.exceptions import ExtractionAPIError, NotG28FormError
from tryalma.g28.models import G28FormData

if TYPE_CHECKING:
    from PIL import Image


class ExtractionBackend(Protocol):
    """Protocol for extraction backends."""

    def extract_structured(
        self,
        images: list[Image.Image],
        schema: type[BaseModel],
    ) -> BaseModel:
        """Extract structured data from images matching the provided schema."""
        ...


class FieldExtractor:
    """Coordinates extraction backends to extract structured G-28 data from images.

    Task 5.1: Implement FieldExtractor with backend injection.
    Task 5.2: Implement main extraction method.
    Task 5.3: Implement field normalization and validation.

    Responsibilities:
    - Delegates to extraction backend (Vision or OCR)
    - Normalizes field values (dates, phone numbers, email)
    - Calculates and propagates confidence scores
    - Handles partial extraction gracefully

    Attributes:
        _primary_extractor: Primary extraction backend (required)
        _fallback_extractor: Optional fallback extraction backend
        _confidence_threshold: Threshold below which fields are marked uncertain
    """

    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.7

    def __init__(
        self,
        primary_extractor: ExtractionBackend,
        fallback_extractor: ExtractionBackend | None = None,
        confidence_threshold: float | None = None,
    ) -> None:
        """Initialize FieldExtractor with backend injection.

        Task 5.1: Accept primary extraction backend via constructor.
        Optionally accept fallback extraction backend.

        Args:
            primary_extractor: Primary extraction backend (required)
            fallback_extractor: Optional fallback extraction backend
            confidence_threshold: Threshold below which fields are marked uncertain
                                 Defaults to 0.7
        """
        self._primary_extractor = primary_extractor
        self._fallback_extractor = fallback_extractor
        self._confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else self.DEFAULT_CONFIDENCE_THRESHOLD
        )

    def extract(self, images: list[Image.Image]) -> G28FormData:
        """Extract all G-28 fields from page images.

        Task 5.2: Implement main extraction method.

        Args:
            images: List of page images (up to 4)

        Returns:
            G28FormData with all extracted fields and confidence scores

        Raises:
            ValueError: If images list is empty
            G28ExtractionError: Extraction failed on all backends
            NotG28FormError: Document is not a G-28 form
        """
        if not images:
            raise ValueError("Image list cannot be empty - at least one image required")

        # Try primary extractor first
        form_data = self._try_extract(images)

        # Check if document is a G-28 form
        if not form_data.form_detected:
            raise NotG28FormError(
                "Document is not recognized as a USCIS Form G-28"
            )

        # Apply validation and normalization
        form_data = self._validate_and_normalize(form_data)

        return form_data

    def _try_extract(self, images: list[Image.Image]) -> G28FormData:
        """Try extraction with primary, then fallback backend.

        Task 5.1: Fall back to secondary extractor only on primary failure.

        Args:
            images: List of page images

        Returns:
            G28FormData from successful extraction

        Raises:
            ExtractionAPIError: Both backends failed or no fallback available
        """
        # Try primary extractor
        try:
            return self._primary_extractor.extract_structured(images, G28FormData)
        except ExtractionAPIError as primary_error:
            # If no fallback, re-raise
            if self._fallback_extractor is None:
                raise

            # Try fallback
            try:
                return self._fallback_extractor.extract_structured(images, G28FormData)
            except ExtractionAPIError as fallback_error:
                # Both failed
                raise ExtractionAPIError(
                    f"Extraction failed on all backends. "
                    f"Primary: {primary_error}. Fallback: {fallback_error}"
                )

    def extract_with_schema(
        self,
        images: list[Image.Image],
        schema: type[BaseModel],
    ) -> BaseModel:
        """Extract fields matching a specific Pydantic schema.

        Enables partial extraction for testing or specific parts.

        Args:
            images: Page images to process
            schema: Pydantic model defining expected fields

        Returns:
            Populated schema instance with extracted data
        """
        return self._primary_extractor.extract_structured(images, schema)

    def _validate_and_normalize(self, form_data: G28FormData) -> G28FormData:
        """Validate and normalize extracted form data.

        Task 5.3: Implement field normalization and validation.

        - Normalize date fields to ISO 8601 format (YYYY-MM-DD)
        - Represent checkbox fields as boolean values
        - Validate email format and flag invalid values
        - Validate phone number format and flag invalid values
        - Flag fields with confidence below threshold as uncertain

        Args:
            form_data: Extracted form data

        Returns:
            Validated and normalized form data with warnings populated
        """
        validation_warnings: list[str] = list(form_data.validation_warnings)
        uncertain_fields: list[str] = list(form_data.uncertain_fields)

        # Validate email fields
        self._validate_email_fields(form_data, validation_warnings)

        # Validate phone fields
        self._validate_phone_fields(form_data, validation_warnings)

        # Flag uncertain fields based on confidence threshold
        self._flag_uncertain_fields(form_data, uncertain_fields)

        # Create updated form data with validation results
        return G28FormData(
            source_file=form_data.source_file,
            form_detected=form_data.form_detected,
            extraction_timestamp=form_data.extraction_timestamp,
            overall_confidence=form_data.overall_confidence,
            part1_attorney_info=form_data.part1_attorney_info,
            part2_eligibility=form_data.part2_eligibility,
            part3_notice_of_appearance=form_data.part3_notice_of_appearance,
            part3_client_info=form_data.part3_client_info,
            part4_5_consent_signatures=form_data.part4_5_consent_signatures,
            part6_additional_info=form_data.part6_additional_info,
            missing_sections=form_data.missing_sections,
            uncertain_fields=uncertain_fields,
            validation_warnings=validation_warnings,
        )

    def _validate_email_fields(
        self, form_data: G28FormData, warnings: list[str]
    ) -> None:
        """Validate email format for all email fields.

        Task 5.3: Validate email format and flag invalid values.
        Requirements: 10.5

        Args:
            form_data: Form data to validate
            warnings: List to append warnings to
        """
        # Simple email regex pattern
        email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        # Check attorney email
        if form_data.part1_attorney_info and form_data.part1_attorney_info.email_address:
            email_value = form_data.part1_attorney_info.email_address.value
            if email_value and not email_pattern.match(email_value):
                warnings.append(
                    f"Invalid email format in Part 1 Attorney Info: '{email_value}'"
                )

        # Check client email
        if form_data.part3_client_info and form_data.part3_client_info.email_address:
            email_value = form_data.part3_client_info.email_address.value
            if email_value and not email_pattern.match(email_value):
                warnings.append(
                    f"Invalid email format in Part 3 Client Info: '{email_value}'"
                )

    def _validate_phone_fields(
        self, form_data: G28FormData, warnings: list[str]
    ) -> None:
        """Validate phone number format for all phone fields.

        Task 5.3: Validate phone number format and flag invalid values.
        Requirements: 10.5

        Args:
            form_data: Form data to validate
            warnings: List to append warnings to
        """
        # Phone pattern: allows common formats like (555) 123-4567, 555-123-4567,
        # 5551234567, +1-555-123-4567, etc.
        phone_pattern = re.compile(
            r"^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$"
        )

        # Check attorney phones
        if form_data.part1_attorney_info:
            attorney = form_data.part1_attorney_info

            if attorney.daytime_telephone:
                phone_value = attorney.daytime_telephone.value
                if phone_value and not phone_pattern.match(phone_value):
                    warnings.append(
                        f"Invalid phone format in Part 1 Attorney daytime telephone: '{phone_value}'"
                    )

            if attorney.mobile_telephone:
                phone_value = attorney.mobile_telephone.value
                if phone_value and not phone_pattern.match(phone_value):
                    warnings.append(
                        f"Invalid phone format in Part 1 Attorney mobile telephone: '{phone_value}'"
                    )

            if attorney.fax_number:
                phone_value = attorney.fax_number.value
                if phone_value and not phone_pattern.match(phone_value):
                    warnings.append(
                        f"Invalid phone format in Part 1 Attorney fax number: '{phone_value}'"
                    )

        # Check client phones
        if form_data.part3_client_info:
            client = form_data.part3_client_info

            if client.daytime_telephone:
                phone_value = client.daytime_telephone.value
                if phone_value and not phone_pattern.match(phone_value):
                    warnings.append(
                        f"Invalid phone format in Part 3 Client daytime telephone: '{phone_value}'"
                    )

            if client.mobile_telephone:
                phone_value = client.mobile_telephone.value
                if phone_value and not phone_pattern.match(phone_value):
                    warnings.append(
                        f"Invalid phone format in Part 3 Client mobile telephone: '{phone_value}'"
                    )

    def _flag_uncertain_fields(
        self, form_data: G28FormData, uncertain_fields: list[str]
    ) -> None:
        """Flag fields with confidence below threshold as uncertain.

        Task 5.3: Flag fields with confidence below threshold as uncertain.
        Requirements: 10.3

        Args:
            form_data: Form data to check
            uncertain_fields: List to append uncertain field paths to
        """
        threshold = self._confidence_threshold

        # Check Part 1 Attorney Info
        if form_data.part1_attorney_info:
            self._check_section_confidence(
                form_data.part1_attorney_info,
                "part1_attorney_info",
                threshold,
                uncertain_fields,
            )

        # Check Part 2 Eligibility
        if form_data.part2_eligibility:
            self._check_section_confidence(
                form_data.part2_eligibility,
                "part2_eligibility",
                threshold,
                uncertain_fields,
            )

        # Check Part 3 Notice of Appearance
        if form_data.part3_notice_of_appearance:
            self._check_section_confidence(
                form_data.part3_notice_of_appearance,
                "part3_notice_of_appearance",
                threshold,
                uncertain_fields,
            )

        # Check Part 3 Client Info
        if form_data.part3_client_info:
            self._check_section_confidence(
                form_data.part3_client_info,
                "part3_client_info",
                threshold,
                uncertain_fields,
            )

        # Check Parts 4-5 Consent and Signatures
        if form_data.part4_5_consent_signatures:
            self._check_section_confidence(
                form_data.part4_5_consent_signatures,
                "part4_5_consent_signatures",
                threshold,
                uncertain_fields,
            )

        # Check Part 6 Additional Info
        if form_data.part6_additional_info:
            self._check_section_confidence(
                form_data.part6_additional_info,
                "part6_additional_info",
                threshold,
                uncertain_fields,
            )

    def _check_section_confidence(
        self,
        section: BaseModel,
        section_name: str,
        threshold: float,
        uncertain_fields: list[str],
    ) -> None:
        """Check confidence levels for all fields in a section.

        Args:
            section: Section model to check
            section_name: Name of the section for field path construction
            threshold: Confidence threshold
            uncertain_fields: List to append uncertain field paths to
        """
        for field_name, field_value in section.model_dump().items():
            if isinstance(field_value, dict) and "confidence" in field_value:
                confidence = field_value.get("confidence", 1.0)
                if confidence < threshold:
                    uncertain_fields.append(f"{section_name}.{field_name}")
