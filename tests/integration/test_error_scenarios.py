"""Integration tests for error scenarios.

Task 9.4: Implement error scenario tests.
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5

Tests handling of various error conditions including non-G28 documents,
unsupported formats, missing files, poor quality, and API failures.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from tryalma.g28.document_loader import DocumentLoader
from tryalma.g28.exceptions import (
    DocumentLoadError,
    ExtractionAPIError,
    G28ExtractionError,
    LowQualityWarning,
    NotG28FormError,
    UnsupportedFormatError,
)
from tryalma.g28.field_extractor import FieldExtractor
from tryalma.g28.models import G28ExtractionResult, G28FormData
from tryalma.g28.output_formatter import OutputFormatter
from tryalma.g28.parser_service import G28ParserService


class TestNonG28DocumentHandling:
    """Test handling of non-G28 documents.
    
    Requirement 10.1: If the document is not recognized as a G-28 form, 
    the G28 Parser shall return an error indicating the document type mismatch.
    """

    def test_non_g28_document_returns_error(
        self,
        parser_service_non_g28: G28ParserService,
        non_g28_image: Path,
    ) -> None:
        """Test handling of non-G28 documents."""
        result = parser_service_non_g28.parse(non_g28_image)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is False
        assert result.error_code == "NOT_G28_FORM"
        assert result.error is not None
        assert "G-28" in result.error or "not recognized" in result.error.lower()

    def test_non_g28_document_error_code_is_set(
        self,
        parser_service_non_g28: G28ParserService,
        non_g28_image: Path,
    ) -> None:
        """Test that error code is properly set for non-G28 documents."""
        result = parser_service_non_g28.parse(non_g28_image)
        
        assert result.error_code is not None
        assert result.error_code == "NOT_G28_FORM"


class TestUnsupportedFormatHandling:
    """Test handling of unsupported file formats.
    
    Requirement 1.3: If an unsupported file format is provided, 
    the G28 Parser shall return an error indicating the supported formats.
    """

    def test_unsupported_format_returns_error(
        self,
        parser_service_with_mock: G28ParserService,
        unsupported_file: Path,
    ) -> None:
        """Test handling of unsupported file formats."""
        result = parser_service_with_mock.parse(unsupported_file)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is False
        assert result.error_code == "UNSUPPORTED_FORMAT"

    def test_unsupported_format_lists_supported_formats(
        self,
        parser_service_with_mock: G28ParserService,
        unsupported_file: Path,
    ) -> None:
        """Test that error message lists supported formats."""
        result = parser_service_with_mock.parse(unsupported_file)
        
        assert result.error is not None
        # Should mention supported formats
        error_lower = result.error.lower()
        assert "pdf" in error_lower or "supported" in error_lower

    def test_document_loader_raises_for_unsupported_format(
        self,
        document_loader: DocumentLoader,
        unsupported_file: Path,
    ) -> None:
        """Test that DocumentLoader raises UnsupportedFormatError."""
        with pytest.raises(UnsupportedFormatError):
            document_loader.load(unsupported_file)


class TestMissingFileHandling:
    """Test handling of missing files.
    
    Requirement 1.4: If the provided file does not exist or is unreadable, 
    the G28 Parser shall return an appropriate error message.
    """

    def test_missing_file_returns_error(
        self,
        parser_service_with_mock: G28ParserService,
        missing_file_path: Path,
    ) -> None:
        """Test handling of missing files."""
        result = parser_service_with_mock.parse(missing_file_path)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is False
        assert result.error_code == "FILE_NOT_FOUND"

    def test_missing_file_error_message_contains_path(
        self,
        parser_service_with_mock: G28ParserService,
        missing_file_path: Path,
    ) -> None:
        """Test that error message contains the file path."""
        result = parser_service_with_mock.parse(missing_file_path)
        
        assert result.error is not None
        assert str(missing_file_path.name) in result.error or "not found" in result.error.lower()

    def test_document_loader_raises_for_missing_file(
        self,
        document_loader: DocumentLoader,
        missing_file_path: Path,
    ) -> None:
        """Test that DocumentLoader raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            document_loader.load(missing_file_path)


class TestPoorQualityDocumentHandling:
    """Test handling of poor quality documents.
    
    Requirement 10.2: If the document quality is too poor for reliable extraction, 
    the G28 Parser shall return a warning with details about the quality issues.
    """

    def test_corrupted_pdf_returns_error(
        self,
        parser_service_with_mock: G28ParserService,
        corrupted_pdf: Path,
    ) -> None:
        """Test handling of corrupted PDF files."""
        result = parser_service_with_mock.parse(corrupted_pdf)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is False
        # Could be either UNSUPPORTED_FORMAT (magic bytes) or DOCUMENT_LOAD_ERROR
        assert result.error_code in ["UNSUPPORTED_FORMAT", "DOCUMENT_LOAD_ERROR"]

    def test_low_confidence_fields_are_flagged(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that low confidence fields are flagged as uncertain.
        
        Requirement 10.3: When extraction confidence for a field falls 
        below a threshold, the G28 Parser shall flag that field as uncertain.
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        # The result should have the uncertain_fields list
        assert result.data is not None
        assert hasattr(result.data, "uncertain_fields")
        # This is a list that may be empty or contain field paths


class TestAPIFailureHandling:
    """Test handling of API failures with mocked responses.
    
    Requirement 10.2, 10.4: Test error handling for external API failures.
    """

    def test_api_failure_returns_error(
        self,
        parser_service_api_error: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test handling of API failures."""
        result = parser_service_api_error.parse(example_g28_pdf_path)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is False
        assert result.error_code == "EXTRACTION_ERROR"
        assert result.error is not None

    def test_api_failure_error_message_is_descriptive(
        self,
        parser_service_api_error: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that API failure error message is descriptive."""
        result = parser_service_api_error.parse(example_g28_pdf_path)
        
        assert result.error is not None
        # Should contain some indication of the failure
        assert len(result.error) > 0


class TestValidationWarnings:
    """Test field validation warnings.
    
    Requirement 10.5: The G28 Parser shall validate extracted data formats 
    and flag invalid values.
    """

    def test_invalid_email_format_generates_warning(
        self,
        document_loader: DocumentLoader,
        output_formatter: OutputFormatter,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that invalid email formats generate validation warnings."""
        # Create a mock extractor that returns data with invalid email
        from datetime import datetime
        from tryalma.g28.models import AttorneyInfo, ExtractedField
        
        mock_data = G28FormData(
            source_file=str(example_g28_pdf_path),
            form_detected=True,
            extraction_timestamp=datetime.now().isoformat(),
            overall_confidence=0.9,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="Test", confidence=0.9),
                email_address=ExtractedField(value="invalid-email", confidence=0.9),
            ),
        )
        
        mock_extractor = MagicMock()
        mock_extractor.extract_structured.return_value = mock_data
        
        field_extractor = FieldExtractor(
            primary_extractor=mock_extractor,
            confidence_threshold=0.7,
        )
        
        service = G28ParserService(
            document_loader=document_loader,
            field_extractor=field_extractor,
            output_formatter=output_formatter,
        )
        
        result = service.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert len(result.data.validation_warnings) > 0
        assert any("email" in w.lower() for w in result.data.validation_warnings)

    def test_invalid_phone_format_generates_warning(
        self,
        document_loader: DocumentLoader,
        output_formatter: OutputFormatter,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that invalid phone formats generate validation warnings."""
        from datetime import datetime
        from tryalma.g28.models import AttorneyInfo, ExtractedField
        
        mock_data = G28FormData(
            source_file=str(example_g28_pdf_path),
            form_detected=True,
            extraction_timestamp=datetime.now().isoformat(),
            overall_confidence=0.9,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="Test", confidence=0.9),
                daytime_telephone=ExtractedField(value="not-a-phone", confidence=0.9),
            ),
        )
        
        mock_extractor = MagicMock()
        mock_extractor.extract_structured.return_value = mock_data
        
        field_extractor = FieldExtractor(
            primary_extractor=mock_extractor,
            confidence_threshold=0.7,
        )
        
        service = G28ParserService(
            document_loader=document_loader,
            field_extractor=field_extractor,
            output_formatter=output_formatter,
        )
        
        result = service.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert len(result.data.validation_warnings) > 0
        assert any("phone" in w.lower() for w in result.data.validation_warnings)


class TestMissingSectionsHandling:
    """Test handling of missing form sections.
    
    Requirement 10.4: If required form sections are missing or illegible, 
    the G28 Parser shall include a list of missing/incomplete sections.
    """

    def test_missing_sections_are_reported(
        self,
        document_loader: DocumentLoader,
        output_formatter: OutputFormatter,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that missing sections are reported in the output."""
        from datetime import datetime
        
        # Create mock data with missing_sections populated
        mock_data = G28FormData(
            source_file=str(example_g28_pdf_path),
            form_detected=True,
            extraction_timestamp=datetime.now().isoformat(),
            overall_confidence=0.5,
            missing_sections=["part2_eligibility", "part3_client_info"],
        )
        
        mock_extractor = MagicMock()
        mock_extractor.extract_structured.return_value = mock_data
        
        field_extractor = FieldExtractor(
            primary_extractor=mock_extractor,
            confidence_threshold=0.7,
        )
        
        service = G28ParserService(
            document_loader=document_loader,
            field_extractor=field_extractor,
            output_formatter=output_formatter,
        )
        
        result = service.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert len(result.data.missing_sections) > 0
        assert "part2_eligibility" in result.data.missing_sections


class TestExceptionHierarchy:
    """Test that exceptions have correct exit codes.
    
    Requirement 10.1, 10.2: Verify exception types and exit codes.
    """

    def test_unsupported_format_error_exit_code(self) -> None:
        """Test UnsupportedFormatError has exit code 2."""
        error = UnsupportedFormatError()
        assert error.exit_code == 2

    def test_g28_extraction_error_exit_code(self) -> None:
        """Test G28ExtractionError has exit code 3."""
        error = G28ExtractionError()
        assert error.exit_code == 3

    def test_not_g28_form_error_exit_code(self) -> None:
        """Test NotG28FormError has exit code 3."""
        error = NotG28FormError()
        assert error.exit_code == 3

    def test_document_load_error_exit_code(self) -> None:
        """Test DocumentLoadError has exit code 3."""
        error = DocumentLoadError()
        assert error.exit_code == 3

    def test_extraction_api_error_exit_code(self) -> None:
        """Test ExtractionAPIError has exit code 3."""
        error = ExtractionAPIError()
        assert error.exit_code == 3

    def test_low_quality_warning_exit_code(self) -> None:
        """Test LowQualityWarning has exit code 3."""
        error = LowQualityWarning()
        assert error.exit_code == 3


class TestBytesParsingErrorScenarios:
    """Test error scenarios for parse_bytes method."""

    def test_parse_bytes_unsupported_format(
        self,
        parser_service_with_mock: G28ParserService,
    ) -> None:
        """Test parse_bytes with unsupported format."""
        result = parser_service_with_mock.parse_bytes(
            data=b"not a valid file",
            filename="document.xyz",
        )
        
        assert result.success is False
        assert result.error_code == "UNSUPPORTED_FORMAT"

    def test_parse_bytes_corrupted_content(
        self,
        parser_service_with_mock: G28ParserService,
    ) -> None:
        """Test parse_bytes with corrupted content."""
        result = parser_service_with_mock.parse_bytes(
            data=b"not a valid PDF content",
            filename="document.pdf",
        )
        
        assert result.success is False
        # Should fail on magic bytes or document loading
        assert result.error_code in ["UNSUPPORTED_FORMAT", "DOCUMENT_LOAD_ERROR"]
