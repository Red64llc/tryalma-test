"""Upload service for document processing orchestration.

Task 4.1: Upload service for document processing orchestration.
Requirements: 3.1, 3.2, 4.1, 4.2

Accepts file uploads and routes to appropriate extraction service based on
document type. Integrates with PassportExtractionService for passport documents
and G28ParserService for G-28 documents.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from werkzeug.datastructures import FileStorage

from tryalma.webapp.exceptions import (
    ExtractionFailedError,
    FileValidationError,
    UnsupportedFormatError,
)
from tryalma.webapp.field_mapper import FieldMapper, MappedField
from tryalma.webapp.validators import FileValidator

if TYPE_CHECKING:
    from tryalma.g28.parser_service import G28ParserService
    from tryalma.passport.service import PassportExtractionService


@dataclass
class UploadResult:
    """Result of an upload and extraction operation.

    Contains unified response format for both passport and G-28 extractions.

    Attributes:
        success: True if extraction succeeded
        document_type: Type of document processed ("passport" or "g28")
        source_filename: Original filename of uploaded document
        form_fields: Mapped fields ready for form population
        extracted_fields: Raw extracted field values with metadata
        warnings: Non-fatal warnings during extraction
        partially_extracted: List of fields that had extraction issues
    """

    success: bool
    document_type: Literal["passport", "g28"]
    source_filename: str
    form_fields: dict[str, MappedField]
    extracted_fields: dict[str, dict]
    warnings: list[str] = field(default_factory=list)
    partially_extracted: list[str] = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dictionary for API responses.

        Returns:
            Dictionary with simplified structure for JSON serialization.
        """
        # Simplify form_fields to just values for JSON response
        simple_form_fields = {
            field_id: mapped_field.value
            for field_id, mapped_field in self.form_fields.items()
        }

        # Build extracted_fields with confidence scores
        extracted = {}
        for field_id, mapped_field in self.form_fields.items():
            extracted[field_id] = {
                "value": mapped_field.value,
                "confidence": mapped_field.confidence,
            }

        return {
            "success": self.success,
            "document_type": self.document_type,
            "form_fields": simple_form_fields,
            "extracted_fields": extracted,
            "warnings": self.warnings,
            "partially_extracted": self.partially_extracted,
        }


class UploadService:
    """Service layer for upload processing and extraction orchestration.

    Coordinates file validation, document routing, extraction service calls,
    and result transformation into unified response format.

    Attributes:
        _passport_service: Service for passport extraction
        _g28_service: Service for G-28 form extraction
        _file_validator: Validator for uploaded files
        _field_mapper: Mapper for extraction results to form fields
    """

    def __init__(
        self,
        passport_service: "PassportExtractionService",
        g28_service: "G28ParserService",
        file_validator: FileValidator,
        field_mapper: FieldMapper,
    ) -> None:
        """Initialize UploadService with dependencies.

        Args:
            passport_service: PassportExtractionService for passport extraction
            g28_service: G28ParserService for G-28 form extraction
            file_validator: FileValidator for file validation
            field_mapper: FieldMapper for result mapping
        """
        self._passport_service = passport_service
        self._g28_service = g28_service
        self._file_validator = file_validator
        self._field_mapper = field_mapper

    def process_upload(
        self,
        file_storage: FileStorage,
        document_type: Literal["passport", "g28"],
    ) -> UploadResult:
        """Process uploaded document through appropriate extraction service.

        Args:
            file_storage: Flask FileStorage object from request.files
            document_type: Type of document being uploaded

        Returns:
            UploadResult with extracted data or error details

        Raises:
            UnsupportedFormatError: File type not supported
            FileValidationError: File validation failed
            ExtractionFailedError: Extraction service failed
        """
        # Validate file
        validation_result = self._file_validator.validate(file_storage)
        if not validation_result.is_valid:
            # Check specific error types
            if "Unsupported" in (validation_result.error_message or ""):
                raise UnsupportedFormatError(validation_result.error_message)
            raise FileValidationError(validation_result.error_message)

        filename = file_storage.filename or "unknown"

        # Route to appropriate service based on document type
        if document_type == "passport":
            return self._process_passport(file_storage, filename)
        else:  # g28
            return self._process_g28(file_storage, filename)

    def _process_passport(
        self, file_storage: FileStorage, filename: str
    ) -> UploadResult:
        """Process passport document through PassportExtractionService.

        Args:
            file_storage: The uploaded file
            filename: Original filename

        Returns:
            UploadResult with passport extraction data

        Note:
            This method catches all exceptions and returns error UploadResults
            to ensure graceful error handling and proper cleanup.
        """
        # Save to temp file for extraction
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                file_storage.stream.seek(0)
                tmp.write(file_storage.stream.read())
                tmp_path = Path(tmp.name)

            # Extract using passport service
            result = self._passport_service.extract_single(tmp_path)

            if not result.success:
                return UploadResult(
                    success=False,
                    document_type="passport",
                    source_filename=filename,
                    form_fields={},
                    extracted_fields={},
                    warnings=[],
                    partially_extracted=[],
                    error=result.error or "Extraction failed",
                    error_code="EXTRACTION_FAILED",
                )

            # Map extracted data to form fields
            mapped_fields = self._field_mapper.map_passport_data(result.data)

            # Build extracted_fields dictionary
            extracted_fields = self._build_extracted_fields(mapped_fields)

            # Collect warnings
            warnings = []
            if result.data and not result.data.mrz_valid:
                warnings.append("MRZ validation failed - please verify extracted data")
            if result.data and result.data.check_digit_errors:
                warnings.append(
                    f"Check digit errors: {', '.join(result.data.check_digit_errors)}"
                )

            # Identify partially extracted fields
            partially_extracted = []
            if result.data:
                partially_extracted = result.data.get_unavailable_fields()

            return UploadResult(
                success=True,
                document_type="passport",
                source_filename=filename,
                form_fields=mapped_fields,
                extracted_fields=extracted_fields,
                warnings=warnings,
                partially_extracted=partially_extracted,
            )

        except ConnectionError as e:
            # Network errors - suggest retry
            return UploadResult(
                success=False,
                document_type="passport",
                source_filename=filename,
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
                error="Network error occurred. Please try again.",
                error_code="NETWORK_ERROR",
            )

        except Exception as e:
            # Unexpected errors - return graceful error
            return UploadResult(
                success=False,
                document_type="passport",
                source_filename=filename,
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
                error="An unexpected error occurred during extraction. Please try again.",
                error_code="INTERNAL_ERROR",
            )

        finally:
            # Clean up temp file
            if tmp_path is not None:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def _process_g28(self, file_storage: FileStorage, filename: str) -> UploadResult:
        """Process G-28 document through G28ParserService.

        Args:
            file_storage: The uploaded file
            filename: Original filename

        Returns:
            UploadResult with G-28 extraction data

        Note:
            This method catches all exceptions and returns error UploadResults
            to ensure graceful error handling.
        """
        try:
            # Read file bytes for G28 service
            file_storage.stream.seek(0)
            file_bytes = file_storage.stream.read()

            # Extract using G28 service
            result = self._g28_service.parse_bytes(file_bytes, filename)

            if not result.success:
                return UploadResult(
                    success=False,
                    document_type="g28",
                    source_filename=filename,
                    form_fields={},
                    extracted_fields={},
                    warnings=[],
                    partially_extracted=[],
                    error=result.error or "Extraction failed",
                    error_code=result.error_code or "EXTRACTION_FAILED",
                )

            # Map extracted data to form fields
            mapped_fields = self._field_mapper.map_g28_data(result.data)

            # Build extracted_fields dictionary
            extracted_fields = self._build_extracted_fields(mapped_fields)

            # Collect warnings
            warnings = list(result.warnings) if result.warnings else []

            # Identify partially extracted (uncertain) fields
            partially_extracted = []
            if result.data and result.data.uncertain_fields:
                partially_extracted = list(result.data.uncertain_fields)

            return UploadResult(
                success=True,
                document_type="g28",
                source_filename=filename,
                form_fields=mapped_fields,
                extracted_fields=extracted_fields,
                warnings=warnings,
                partially_extracted=partially_extracted,
            )

        except ConnectionError as e:
            # Network errors - suggest retry
            return UploadResult(
                success=False,
                document_type="g28",
                source_filename=filename,
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
                error="Network error occurred. Please try again.",
                error_code="NETWORK_ERROR",
            )

        except Exception as e:
            # Unexpected errors - return graceful error
            return UploadResult(
                success=False,
                document_type="g28",
                source_filename=filename,
                form_fields={},
                extracted_fields={},
                warnings=[],
                partially_extracted=[],
                error="An unexpected error occurred during extraction. Please try again.",
                error_code="INTERNAL_ERROR",
            )

    def _build_extracted_fields(
        self, mapped_fields: dict[str, MappedField]
    ) -> dict[str, dict]:
        """Build extracted_fields dictionary from mapped fields.

        Args:
            mapped_fields: Dictionary of mapped form fields

        Returns:
            Dictionary with field values and confidence scores
        """
        return {
            field_id: {
                "value": mapped.value,
                "confidence": mapped.confidence,
            }
            for field_id, mapped in mapped_fields.items()
        }

    def merge_extraction_results(
        self,
        existing: dict[str, MappedField],
        new_result: UploadResult,
    ) -> dict[str, MappedField]:
        """Merge new extraction into existing form data without overwriting.

        Implements Requirement 5.4: when multiple documents are processed,
        merge extracted data into the form without overwriting previously
        populated fields.

        Args:
            existing: Current form field values
            new_result: New extraction result to merge

        Returns:
            Merged form data dictionary
        """
        return self._field_mapper.merge_fields(existing, new_result.form_fields)
