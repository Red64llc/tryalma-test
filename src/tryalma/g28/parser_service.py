"""G28 Parser Service for orchestrating G-28 form parsing workflow.

Task 7: Parser Service Orchestration implementation.

Requirements:
- 7.1: Constructor with dependency injection (1.1, 1.2, 10.3)
- 7.2: parse() method for file path input (1.1-1.5, 9.1, 10.1-10.4)
- 7.3: parse_bytes() method for web upload support (1.1-1.5)
- 7.4: parse_images() method for pre-loaded images (1.1, 1.2)
- 7.5: create_default() factory method (1.1, 1.2, 9.1)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from tryalma.g28.document_loader import DocumentLoader
from tryalma.g28.exceptions import (
    DocumentLoadError,
    ExtractionAPIError,
    G28ExtractionError,
    NotG28FormError,
    UnsupportedFormatError,
)
from tryalma.g28.field_extractor import FieldExtractor
from tryalma.g28.models import G28ExtractionResult, G28FormData
from tryalma.g28.output_formatter import OutputFormatter
from tryalma.g28.vision_extractor import VisionExtractor

if TYPE_CHECKING:
    from PIL import Image


class G28ParserService:
    """Main service for parsing G-28 forms.

    Task 7: Parser Service Orchestration.

    Designed for reuse across CLI, Flask, and other contexts.
    Stateless and thread-safe after initialization.

    Responsibilities:
    - Coordinates document loading, field extraction, and output formatting
    - Enforces validation rules and confidence thresholds
    - Handles error aggregation and reporting
    - Transaction scope: Single document processing (stateless)
    """

    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.7

    def __init__(
        self,
        document_loader: DocumentLoader,
        field_extractor: FieldExtractor,
        output_formatter: OutputFormatter,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        """Initialize G28ParserService with dependency injection.

        Task 7.1: Implement G28ParserService constructor with dependency injection.
        Requirements: 1.1, 1.2, 10.3

        Args:
            document_loader: DocumentLoader for loading PDF/image files
            field_extractor: FieldExtractor for data extraction
            output_formatter: OutputFormatter for formatting results
            confidence_threshold: Threshold below which fields are flagged uncertain
                                 Defaults to 0.7
        """
        self._document_loader = document_loader
        self._field_extractor = field_extractor
        self._output_formatter = output_formatter
        self._confidence_threshold = confidence_threshold

    def parse(
        self,
        file_path: Path,
        output_format: Literal["json", "yaml"] = "json",
        verbose: bool = False,
    ) -> G28ExtractionResult:
        """Parse a G-28 form from file path and return structured data.

        Task 7.2: Implement parse() method for file path input.
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 10.1, 10.2, 10.3, 10.4

        Args:
            file_path: Path to PDF or image file
            output_format: Output serialization format ("json" or "yaml")
            verbose: Include confidence scores and metadata

        Returns:
            G28ExtractionResult with extracted data or error details
        """
        source_file = str(file_path)

        try:
            # Load document into images
            images = self._document_loader.load(file_path)

            # Extract form data
            form_data = self._field_extractor.extract(images)

            # Update source file in form data
            form_data = self._update_form_data_source(form_data, source_file)

            # Build successful result
            return G28ExtractionResult(
                success=True,
                data=form_data,
                source_file=source_file,
                warnings=list(form_data.validation_warnings),
            )

        except FileNotFoundError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="FILE_NOT_FOUND",
                source_file=source_file,
            )

        except UnsupportedFormatError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="UNSUPPORTED_FORMAT",
                source_file=source_file,
            )

        except NotG28FormError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="NOT_G28_FORM",
                source_file=source_file,
            )

        except (ExtractionAPIError, G28ExtractionError) as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="EXTRACTION_ERROR",
                source_file=source_file,
            )

        except DocumentLoadError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="DOCUMENT_LOAD_ERROR",
                source_file=source_file,
            )

    def parse_bytes(
        self,
        data: bytes,
        filename: str,
        output_format: Literal["json", "yaml"] = "json",
        verbose: bool = False,
    ) -> G28ExtractionResult:
        """Parse a G-28 form from in-memory bytes (Flask/web upload support).

        Task 7.3: Implement parse_bytes() method for web upload support.
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5

        Args:
            data: Raw file bytes (PDF or image)
            filename: Original filename for format detection
            output_format: Output serialization format
            verbose: Include confidence scores and metadata

        Returns:
            G28ExtractionResult with extracted data or error details

        Example (Flask):
            @app.route('/api/parse-g28', methods=['POST'])
            def parse_g28_endpoint():
                file = request.files['document']
                result = parser_service.parse_bytes(
                    data=file.read(),
                    filename=file.filename,
                )
                return jsonify(result.data.model_dump())
        """
        source_file = filename

        try:
            # Load document from bytes
            images = self._document_loader.load_bytes(data, filename)

            # Extract form data using same pipeline as parse()
            form_data = self._field_extractor.extract(images)

            # Update source file in form data
            form_data = self._update_form_data_source(form_data, source_file)

            # Build successful result
            return G28ExtractionResult(
                success=True,
                data=form_data,
                source_file=source_file,
                warnings=list(form_data.validation_warnings),
            )

        except UnsupportedFormatError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="UNSUPPORTED_FORMAT",
                source_file=source_file,
            )

        except NotG28FormError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="NOT_G28_FORM",
                source_file=source_file,
            )

        except (ExtractionAPIError, G28ExtractionError) as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="EXTRACTION_ERROR",
                source_file=source_file,
            )

        except DocumentLoadError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="DOCUMENT_LOAD_ERROR",
                source_file=source_file,
            )

    def parse_images(
        self,
        images: list[Image.Image],
        source_name: str = "upload",
        output_format: Literal["json", "yaml"] = "json",
        verbose: bool = False,
    ) -> G28ExtractionResult:
        """Parse a G-28 form from pre-loaded PIL Images.

        Task 7.4: Implement parse_images() method for pre-loaded images.
        Requirements: 1.1, 1.2

        Useful when images are already loaded or preprocessed.

        Args:
            images: List of PIL Image objects (one per page)
            source_name: Identifier for the source document
            output_format: Output serialization format
            verbose: Include confidence scores and metadata

        Returns:
            G28ExtractionResult with extracted data or error details
        """
        try:
            # Bypass document loading - use images directly
            form_data = self._field_extractor.extract(images)

            # Update source file in form data
            form_data = self._update_form_data_source(form_data, source_name)

            # Build successful result
            return G28ExtractionResult(
                success=True,
                data=form_data,
                source_file=source_name,
                warnings=list(form_data.validation_warnings),
            )

        except NotG28FormError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="NOT_G28_FORM",
                source_file=source_name,
            )

        except (ExtractionAPIError, G28ExtractionError) as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="EXTRACTION_ERROR",
                source_file=source_name,
            )

        except ValueError as e:
            return G28ExtractionResult(
                success=False,
                error=str(e),
                error_code="INVALID_INPUT",
                source_file=source_name,
            )

    def _update_form_data_source(
        self, form_data: G28FormData, source_file: str
    ) -> G28FormData:
        """Update source_file in form data.

        Creates a new G28FormData with updated source_file.

        Args:
            form_data: Original form data
            source_file: New source file path/name

        Returns:
            Updated G28FormData with new source_file
        """
        return G28FormData(
            source_file=source_file,
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
            uncertain_fields=form_data.uncertain_fields,
            validation_warnings=form_data.validation_warnings,
        )

    @classmethod
    def create_default(cls, api_key: str | None = None) -> "G28ParserService":
        """Factory method to create service with default dependencies.

        Task 7.5: Implement create_default() factory method.
        Requirements: 1.1, 1.2, 9.1

        Convenient for Flask app initialization:

            # In Flask app factory
            parser_service = G28ParserService.create_default()
            app.extensions['g28_parser'] = parser_service

        Args:
            api_key: Optional Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

        Returns:
            Configured G28ParserService instance ready for use

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        # Resolve API key
        resolved_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not resolved_api_key:
            raise ValueError(
                "API key must be provided either as parameter or via "
                "ANTHROPIC_API_KEY environment variable"
            )

        # Create default dependencies
        document_loader = DocumentLoader()

        # Create VisionExtractor with API key
        vision_extractor = VisionExtractor(api_key=resolved_api_key)

        # Create FieldExtractor with VisionExtractor as primary backend
        field_extractor = FieldExtractor(
            primary_extractor=vision_extractor,
            confidence_threshold=cls.DEFAULT_CONFIDENCE_THRESHOLD,
        )

        output_formatter = OutputFormatter()

        # Create and return configured service
        return cls(
            document_loader=document_loader,
            field_extractor=field_extractor,
            output_formatter=output_formatter,
            confidence_threshold=cls.DEFAULT_CONFIDENCE_THRESHOLD,
        )
