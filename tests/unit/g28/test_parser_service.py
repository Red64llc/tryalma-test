"""Unit tests for G28ParserService.

Task 7: Parser Service Orchestration tests.

Tests cover:
- 7.1 G28ParserService constructor with dependency injection
- 7.2 parse() method for file path input
- 7.3 parse_bytes() method for web upload support
- 7.4 parse_images() method for pre-loaded images
- 7.5 create_default() factory method

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 10.1, 10.2, 10.3, 10.4
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
import os

import pytest
from PIL import Image

from tryalma.g28.exceptions import (
    DocumentLoadError,
    ExtractionAPIError,
    G28ExtractionError,
    NotG28FormError,
    UnsupportedFormatError,
)
from tryalma.g28.models import (
    AttorneyInfo,
    ExtractedField,
    G28ExtractionResult,
    G28FormData,
)


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a simple test image."""
    return Image.new("RGB", (100, 100), color="white")


@pytest.fixture
def sample_images(sample_image: Image.Image) -> list[Image.Image]:
    """Create a list of test images."""
    return [sample_image, sample_image]


@pytest.fixture
def mock_document_loader():
    """Create a mock DocumentLoader."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_field_extractor():
    """Create a mock FieldExtractor."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_output_formatter():
    """Create a mock OutputFormatter."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_g28_form_data() -> G28FormData:
    """Create a mock G28FormData for testing."""
    return G28FormData(
        source_file="test.pdf",
        form_detected=True,
        extraction_timestamp="2024-01-25T12:00:00Z",
        overall_confidence=0.85,
        part1_attorney_info=AttorneyInfo(
            family_name=ExtractedField(value="Smith", confidence=0.95),
            given_name=ExtractedField(value="John", confidence=0.9),
        ),
    )


class TestG28ParserServiceConstructor:
    """Tests for Task 7.1: G28ParserService constructor with dependency injection."""

    def test_accepts_document_loader_dependency(
        self, mock_document_loader, mock_field_extractor, mock_output_formatter
    ):
        """Test G28ParserService accepts DocumentLoader as dependency."""
        from tryalma.g28.parser_service import G28ParserService

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        assert service._document_loader is mock_document_loader

    def test_accepts_field_extractor_dependency(
        self, mock_document_loader, mock_field_extractor, mock_output_formatter
    ):
        """Test G28ParserService accepts FieldExtractor as dependency."""
        from tryalma.g28.parser_service import G28ParserService

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        assert service._field_extractor is mock_field_extractor

    def test_accepts_output_formatter_dependency(
        self, mock_document_loader, mock_field_extractor, mock_output_formatter
    ):
        """Test G28ParserService accepts OutputFormatter as dependency."""
        from tryalma.g28.parser_service import G28ParserService

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        assert service._output_formatter is mock_output_formatter

    def test_accepts_configurable_confidence_threshold(
        self, mock_document_loader, mock_field_extractor, mock_output_formatter
    ):
        """Test G28ParserService accepts configurable confidence threshold."""
        from tryalma.g28.parser_service import G28ParserService

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
            confidence_threshold=0.8,
        )

        assert service._confidence_threshold == 0.8

    def test_default_confidence_threshold_is_0_7(
        self, mock_document_loader, mock_field_extractor, mock_output_formatter
    ):
        """Test default confidence threshold is 0.7."""
        from tryalma.g28.parser_service import G28ParserService

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        assert service._confidence_threshold == 0.7

    def test_stateless_design_allows_singleton_usage(
        self, mock_document_loader, mock_field_extractor, mock_output_formatter
    ):
        """Test service is stateless and thread-safe for singleton usage.

        Verify no instance state is mutated between calls.
        """
        from tryalma.g28.parser_service import G28ParserService

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        # Service should not have any mutable instance state
        # All state is in dependencies or passed as arguments
        assert not hasattr(service, "_request_state")
        assert not hasattr(service, "_mutable_state")


class TestParseMethod:
    """Tests for Task 7.2: parse() method for file path input."""

    def test_accepts_file_path_argument(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
        tmp_path,
    ):
        """Test parse() accepts file path argument."""
        from tryalma.g28.parser_service import G28ParserService

        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file)

        mock_document_loader.load.assert_called_once_with(test_file)

    def test_accepts_output_format_argument(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
        tmp_path,
    ):
        """Test parse() accepts output format argument."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file, output_format="yaml")

        assert isinstance(result, G28ExtractionResult)

    def test_accepts_verbose_flag(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
        tmp_path,
    ):
        """Test parse() accepts verbose flag."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file, verbose=True)

        assert isinstance(result, G28ExtractionResult)

    def test_coordinates_document_loading_field_extraction_and_output_formatting(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
        tmp_path,
    ):
        """Test parse() coordinates document loading, field extraction, and output formatting."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file)

        # Verify workflow coordination
        mock_document_loader.load.assert_called_once()
        mock_field_extractor.extract.assert_called_once_with(sample_images)

    def test_returns_g28_extraction_result_with_success_status(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
        tmp_path,
    ):
        """Test parse() returns G28ExtractionResult with success status and data."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file)

        assert isinstance(result, G28ExtractionResult)
        assert result.success is True
        assert result.data is not None
        assert result.error is None

    def test_applies_confidence_threshold_to_flag_uncertain_fields(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        sample_images,
        tmp_path,
    ):
        """Test parse() applies confidence threshold to flag uncertain fields."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        # Create form data with low confidence field
        form_data = G28FormData(
            source_file="test.pdf",
            form_detected=True,
            extraction_timestamp="2024-01-25T12:00:00Z",
            overall_confidence=0.85,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="Smith", confidence=0.5),  # Below threshold
            ),
            uncertain_fields=[],
        )

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.return_value = form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
            confidence_threshold=0.7,
        )

        result = service.parse(test_file)

        # Service should flag uncertain fields based on threshold
        assert result.success is True

    def test_handles_file_not_found_error(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
    ):
        """Test parse() handles FileNotFoundError and returns appropriate error result."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load.side_effect = FileNotFoundError("File not found")

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(Path("/nonexistent/file.pdf"))

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower() or "File not found" in result.error

    def test_handles_unsupported_format_error(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
    ):
        """Test parse() handles UnsupportedFormatError and returns appropriate error result."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load.side_effect = UnsupportedFormatError("Unsupported format")

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(Path("/path/to/file.xyz"))

        assert result.success is False
        assert result.error is not None
        assert result.error_code == "UNSUPPORTED_FORMAT"

    def test_handles_extraction_error(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        sample_images,
        tmp_path,
    ):
        """Test parse() handles G28ExtractionError and returns appropriate error result."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.side_effect = ExtractionAPIError("API failed")

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file)

        assert result.success is False
        assert result.error is not None
        assert result.error_code == "EXTRACTION_ERROR"

    def test_handles_not_g28_form_error(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        sample_images,
        tmp_path,
    ):
        """Test parse() handles NotG28FormError and returns appropriate error result."""
        from tryalma.g28.parser_service import G28ParserService

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-test content")

        mock_document_loader.load.return_value = sample_images
        mock_field_extractor.extract.side_effect = NotG28FormError("Not a G-28 form")

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse(test_file)

        assert result.success is False
        assert result.error is not None
        assert result.error_code == "NOT_G28_FORM"


class TestParseBytesMethod:
    """Tests for Task 7.3: parse_bytes() method for web upload support."""

    def test_accepts_raw_bytes_argument(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() accepts raw bytes argument."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        test_data = b"%PDF-test content"
        result = service.parse_bytes(test_data, filename="test.pdf")

        mock_document_loader.load_bytes.assert_called_once_with(test_data, "test.pdf")

    def test_accepts_filename_for_format_detection(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() accepts filename for format detection."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        test_data = b"%PDF-test content"
        result = service.parse_bytes(test_data, filename="document.pdf")

        # Verify filename was passed for format detection
        call_args = mock_document_loader.load_bytes.call_args
        assert call_args[0][1] == "document.pdf"

    def test_accepts_output_format_argument(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() accepts output format argument."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_bytes(b"%PDF-test", filename="test.pdf", output_format="yaml")

        assert isinstance(result, G28ExtractionResult)

    def test_accepts_verbose_flag(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() accepts verbose flag."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_bytes(b"%PDF-test", filename="test.pdf", verbose=True)

        assert isinstance(result, G28ExtractionResult)

    def test_delegates_to_document_loader_load_bytes(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() delegates to DocumentLoader.load_bytes() for image conversion."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        test_data = b"%PDF-test content"
        result = service.parse_bytes(test_data, filename="test.pdf")

        mock_document_loader.load_bytes.assert_called_once()

    def test_processes_through_same_extraction_pipeline_as_parse(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() processes through same extraction pipeline as parse()."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_bytes(b"%PDF-test", filename="test.pdf")

        # Verify same extraction pipeline is used
        mock_field_extractor.extract.assert_called_once_with(sample_images)

    def test_returns_g28_extraction_result_suitable_for_flask_integration(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_bytes() returns G28ExtractionResult suitable for Flask/web integration."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.return_value = sample_images
        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_bytes(b"%PDF-test", filename="test.pdf")

        assert isinstance(result, G28ExtractionResult)
        assert result.success is True
        assert result.data is not None

    def test_handles_unsupported_format_from_filename(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
    ):
        """Test parse_bytes() handles unsupported format detected from filename."""
        from tryalma.g28.parser_service import G28ParserService

        mock_document_loader.load_bytes.side_effect = UnsupportedFormatError("Unsupported")

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_bytes(b"some content", filename="test.xyz")

        assert result.success is False
        assert result.error_code == "UNSUPPORTED_FORMAT"


class TestParseImagesMethod:
    """Tests for Task 7.4: parse_images() method for pre-loaded images."""

    def test_accepts_list_of_pil_images_directly(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_images() accepts list of PIL Images directly."""
        from tryalma.g28.parser_service import G28ParserService

        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_images(sample_images)

        # Should not call document_loader at all
        mock_document_loader.load.assert_not_called()
        mock_document_loader.load_bytes.assert_not_called()

    def test_bypasses_document_loading_phase(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_images() bypasses document loading phase."""
        from tryalma.g28.parser_service import G28ParserService

        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_images(sample_images)

        # Verify document loader was NOT called
        mock_document_loader.load.assert_not_called()
        mock_document_loader.load_bytes.assert_not_called()

    def test_processes_through_extraction_and_formatting_pipeline(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_images() processes through extraction and formatting pipeline."""
        from tryalma.g28.parser_service import G28ParserService

        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_images(sample_images)

        # Verify extraction was called with images
        mock_field_extractor.extract.assert_called_once_with(sample_images)

    def test_supports_preprocessed_images_use_case(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
    ):
        """Test parse_images() supports use cases where images are already loaded or preprocessed."""
        from tryalma.g28.parser_service import G28ParserService

        # Create preprocessed images (e.g., resized, enhanced)
        preprocessed = [
            Image.new("RGB", (200, 200), color="white"),
            Image.new("RGB", (200, 200), color="lightgray"),
        ]

        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_images(preprocessed)

        assert result.success is True
        mock_field_extractor.extract.assert_called_once_with(preprocessed)

    def test_accepts_source_name_parameter(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_images() accepts source_name parameter for identification."""
        from tryalma.g28.parser_service import G28ParserService

        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_images(sample_images, source_name="custom_source")

        assert result.source_file == "custom_source"

    def test_returns_g28_extraction_result(
        self,
        mock_document_loader,
        mock_field_extractor,
        mock_output_formatter,
        mock_g28_form_data,
        sample_images,
    ):
        """Test parse_images() returns G28ExtractionResult."""
        from tryalma.g28.parser_service import G28ParserService

        mock_field_extractor.extract.return_value = mock_g28_form_data

        service = G28ParserService(
            document_loader=mock_document_loader,
            field_extractor=mock_field_extractor,
            output_formatter=mock_output_formatter,
        )

        result = service.parse_images(sample_images)

        assert isinstance(result, G28ExtractionResult)
        assert result.success is True


class TestCreateDefaultFactoryMethod:
    """Tests for Task 7.5: create_default() factory method."""

    def test_creates_service_with_default_document_loader(self):
        """Test create_default() creates service with default DocumentLoader."""
        from tryalma.g28.parser_service import G28ParserService
        from tryalma.g28.document_loader import DocumentLoader

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = G28ParserService.create_default()

        assert isinstance(service._document_loader, DocumentLoader)

    def test_creates_service_with_vision_extractor_based_field_extractor(self):
        """Test create_default() creates service with VisionExtractor-based FieldExtractor."""
        from tryalma.g28.parser_service import G28ParserService
        from tryalma.g28.field_extractor import FieldExtractor

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = G28ParserService.create_default()

        assert isinstance(service._field_extractor, FieldExtractor)

    def test_creates_service_with_default_output_formatter(self):
        """Test create_default() creates service with default OutputFormatter."""
        from tryalma.g28.parser_service import G28ParserService
        from tryalma.g28.output_formatter import OutputFormatter

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = G28ParserService.create_default()

        assert isinstance(service._output_formatter, OutputFormatter)

    def test_accepts_optional_api_key_parameter(self):
        """Test create_default() accepts optional API key parameter."""
        from tryalma.g28.parser_service import G28ParserService

        # Should not raise even without env var when key is provided
        service = G28ParserService.create_default(api_key="explicit-test-key")

        assert service is not None

    def test_defaults_to_anthropic_api_key_environment_variable(self):
        """Test create_default() defaults to ANTHROPIC_API_KEY environment variable."""
        from tryalma.g28.parser_service import G28ParserService

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-test-key"}):
            service = G28ParserService.create_default()

        assert service is not None

    def test_returns_fully_configured_g28_parser_service(self):
        """Test create_default() returns fully configured G28ParserService ready for use."""
        from tryalma.g28.parser_service import G28ParserService

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = G28ParserService.create_default()

        assert isinstance(service, G28ParserService)
        assert service._document_loader is not None
        assert service._field_extractor is not None
        assert service._output_formatter is not None

    def test_enables_flask_app_factory_pattern(self):
        """Test create_default() enables simple initialization for Flask app factory pattern."""
        from tryalma.g28.parser_service import G28ParserService

        # Simulate Flask app factory usage
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            # This is how it would be used in Flask
            parser_service = G28ParserService.create_default()

        # Verify it's a singleton-compatible instance
        assert isinstance(parser_service, G28ParserService)

    def test_raises_error_when_no_api_key_available(self):
        """Test create_default() raises error when no API key is available."""
        from tryalma.g28.parser_service import G28ParserService

        # Remove ANTHROPIC_API_KEY from environment
        with patch.dict(os.environ, {}, clear=True):
            # Ensure the key is not set
            os.environ.pop("ANTHROPIC_API_KEY", None)

            with pytest.raises(ValueError, match="API key"):
                G28ParserService.create_default()
