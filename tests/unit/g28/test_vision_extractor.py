"""Unit tests for VisionExtractor.

Task 4: Vision Extraction Backend tests.

Tests cover:
- 4.1 (P) Claude Vision API client setup
- 4.2 Structured extraction with schema
- 4.3 API error handling and retry logic

Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.4, 5.1-5.6, 6.1-6.6, 7.1-7.3, 8.6, 10.1, 10.2
"""

import base64
import os
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from pydantic import BaseModel

from tryalma.g28.exceptions import ExtractionAPIError
from tryalma.g28.models import (
    AttorneyInfo,
    ExtractedField,
    G28FormData,
)
from tryalma.g28.vision_extractor import VisionExtractor


class SimpleTestSchema(BaseModel):
    """Simple schema for testing extraction."""

    name: ExtractedField[str] | None = None
    age: ExtractedField[int] | None = None


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a simple test image."""
    img = Image.new("RGB", (100, 100), color="white")
    return img


@pytest.fixture
def sample_images(sample_image: Image.Image) -> list[Image.Image]:
    """Create a list of test images."""
    return [sample_image, sample_image]


class TestVisionExtractorInit:
    """Tests for Task 4.1: Claude Vision API client setup."""

    def test_init_with_api_key_parameter(self):
        """Test initialization with API key passed as parameter."""
        extractor = VisionExtractor(api_key="test-api-key")
        assert extractor._api_key == "test-api-key"

    def test_init_with_environment_variable(self, monkeypatch):
        """Test initialization falls back to ANTHROPIC_API_KEY env var."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-api-key")
        extractor = VisionExtractor()
        assert extractor._api_key == "env-api-key"

    def test_init_prefers_parameter_over_env_var(self, monkeypatch):
        """Test that explicit parameter takes precedence over env var."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-api-key")
        extractor = VisionExtractor(api_key="param-api-key")
        assert extractor._api_key == "param-api-key"

    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test that missing API key raises clear error."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key"):
            VisionExtractor()

    def test_model_constant(self):
        """Test that model constant is configured correctly."""
        assert VisionExtractor.MODEL == "claude-sonnet-4-20250514"

    def test_max_tokens_constant(self):
        """Test that max tokens constant is configured."""
        assert VisionExtractor.MAX_TOKENS == 4096

    def test_client_initialization(self):
        """Test that Anthropic client is initialized on first use."""
        extractor = VisionExtractor(api_key="test-key")
        # Client should be created lazily or on init
        assert extractor._client is not None


class TestImageEncoding:
    """Tests for image to base64 encoding (Task 4.2)."""

    def test_encode_image_to_base64(self, sample_image):
        """Test encoding PIL image to base64."""
        extractor = VisionExtractor(api_key="test-key")
        encoded = extractor._encode_image(sample_image)

        # Should be valid base64
        decoded = base64.b64decode(encoded)
        assert len(decoded) > 0

        # Should be PNG format
        assert decoded[:8] == b"\x89PNG\r\n\x1a\n"

    def test_encode_multiple_images(self, sample_images):
        """Test encoding multiple images for multi-page documents."""
        extractor = VisionExtractor(api_key="test-key")
        encoded_list = [extractor._encode_image(img) for img in sample_images]

        assert len(encoded_list) == 2
        for encoded in encoded_list:
            decoded = base64.b64decode(encoded)
            assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


class TestPromptConstruction:
    """Tests for extraction prompt construction (Task 4.2)."""

    def test_builds_g28_extraction_prompt(self):
        """Test that prompt describes G-28 form fields for extraction."""
        extractor = VisionExtractor(api_key="test-key")
        prompt = extractor._build_extraction_prompt(G28FormData)

        # Should mention G-28 form
        assert "G-28" in prompt or "g-28" in prompt.lower() or "form" in prompt.lower()
        # Should be requesting JSON output
        assert "json" in prompt.lower() or "JSON" in prompt

    def test_builds_prompt_for_custom_schema(self):
        """Test prompt construction adapts to provided schema."""
        extractor = VisionExtractor(api_key="test-key")
        prompt = extractor._build_extraction_prompt(SimpleTestSchema)

        # Should mention extracting data
        assert "extract" in prompt.lower()


class TestStructuredExtraction:
    """Tests for structured extraction (Task 4.2)."""

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_extract_structured_calls_api(self, mock_anthropic_class, sample_images):
        """Test that extract_structured calls Claude API correctly."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text='{"name": {"value": "John", "confidence": 0.95}, "age": {"value": 30, "confidence": 0.9}}',
            )
        ]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")
        result = extractor.extract_structured(sample_images, SimpleTestSchema)

        # Verify API was called
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs

        # Should use correct model
        assert call_kwargs["model"] == VisionExtractor.MODEL
        assert call_kwargs["max_tokens"] == VisionExtractor.MAX_TOKENS

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_extract_structured_includes_all_page_images(
        self, mock_anthropic_class, sample_images
    ):
        """Test multi-page documents include all pages in single request."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text='{"name": {"value": "Test", "confidence": 0.9}, "age": null}',
            )
        ]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")
        extractor.extract_structured(sample_images, SimpleTestSchema)

        # Check that all images were included
        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]

        # Messages should contain image content blocks
        content = messages[0]["content"]
        image_blocks = [c for c in content if c.get("type") == "image"]
        assert len(image_blocks) == len(sample_images)

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_extract_structured_parses_response_to_schema(
        self, mock_anthropic_class, sample_images
    ):
        """Test Claude response is parsed into provided Pydantic schema."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text='{"name": {"value": "Alice", "confidence": 0.95}, "age": {"value": 25, "confidence": 0.88}}',
            )
        ]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")
        result = extractor.extract_structured(sample_images, SimpleTestSchema)

        assert isinstance(result, SimpleTestSchema)
        assert result.name is not None
        assert result.name.value == "Alice"
        assert result.name.confidence == 0.95

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_extract_structured_handles_null_fields(
        self, mock_anthropic_class, sample_images
    ):
        """Test extraction handles null/missing fields gracefully."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text", text='{"name": {"value": "Test", "confidence": 0.9}}'
            )
        ]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")
        result = extractor.extract_structured(sample_images, SimpleTestSchema)

        assert result.name is not None
        assert result.age is None


class TestConfidenceCalculation:
    """Tests for per-field confidence scoring (Task 4.2)."""

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_extracts_confidence_from_response(
        self, mock_anthropic_class, sample_images
    ):
        """Test confidence scores are extracted from Claude's response."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text='{"name": {"value": "Bob", "confidence": 0.75}, "age": {"value": 40, "confidence": 0.60}}',
            )
        ]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")
        result = extractor.extract_structured(sample_images, SimpleTestSchema)

        assert result.name.confidence == 0.75
        assert result.age.confidence == 0.60


class TestAPIErrorHandling:
    """Tests for Task 4.3: API error handling and retry logic."""

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_handles_rate_limit_error_with_retry(
        self, mock_anthropic_class, sample_images
    ):
        """Test 429 rate limit errors trigger exponential backoff retry."""
        from anthropic import RateLimitError

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Create a proper mock response for RateLimitError
        mock_http_response = MagicMock()
        mock_http_response.status_code = 429
        mock_http_response.headers = {}

        # First two calls fail with rate limit, third succeeds
        mock_client.messages.create.side_effect = [
            RateLimitError(
                message="Rate limit exceeded",
                response=mock_http_response,
                body={"error": {"message": "Rate limit exceeded"}},
            ),
            RateLimitError(
                message="Rate limit exceeded",
                response=mock_http_response,
                body={"error": {"message": "Rate limit exceeded"}},
            ),
            MagicMock(
                content=[
                    MagicMock(
                        type="text", text='{"name": {"value": "Test", "confidence": 0.9}}'
                    )
                ]
            ),
        ]

        extractor = VisionExtractor(api_key="test-key")

        # Should succeed after retries
        with patch("time.sleep"):  # Don't actually wait
            result = extractor.extract_structured(sample_images, SimpleTestSchema)

        assert result.name.value == "Test"
        assert mock_client.messages.create.call_count == 3

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_handles_server_error_with_retry(
        self, mock_anthropic_class, sample_images
    ):
        """Test 500 server errors trigger retry."""
        from anthropic import InternalServerError

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_http_response = MagicMock()
        mock_http_response.status_code = 500
        mock_http_response.headers = {}

        # First call fails, second succeeds
        mock_client.messages.create.side_effect = [
            InternalServerError(
                message="Server error",
                response=mock_http_response,
                body={"error": {"message": "Internal error"}},
            ),
            MagicMock(
                content=[
                    MagicMock(
                        type="text",
                        text='{"name": {"value": "Success", "confidence": 0.85}}',
                    )
                ]
            ),
        ]

        extractor = VisionExtractor(api_key="test-key")

        with patch("time.sleep"):
            result = extractor.extract_structured(sample_images, SimpleTestSchema)

        assert result.name.value == "Success"

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_handles_authentication_error_with_clear_message(
        self, mock_anthropic_class, sample_images
    ):
        """Test 401 auth errors raise ExtractionAPIError with clear message."""
        from anthropic import AuthenticationError

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_http_response = MagicMock()
        mock_http_response.status_code = 401
        mock_http_response.headers = {}

        mock_client.messages.create.side_effect = AuthenticationError(
            message="Invalid API key",
            response=mock_http_response,
            body={"error": {"message": "Invalid API key"}},
        )

        extractor = VisionExtractor(api_key="invalid-key")

        with pytest.raises(ExtractionAPIError) as exc_info:
            extractor.extract_structured(sample_images, SimpleTestSchema)

        # Should have clear authentication error message
        assert "authentication" in str(exc_info.value).lower() or "api key" in str(
            exc_info.value
        ).lower()

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_raises_extraction_api_error_on_persistent_failure(
        self, mock_anthropic_class, sample_images
    ):
        """Test persistent failures raise ExtractionAPIError with details."""
        from anthropic import RateLimitError

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_http_response = MagicMock()
        mock_http_response.status_code = 429
        mock_http_response.headers = {}

        # All retries fail
        mock_client.messages.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=mock_http_response,
            body={"error": {"message": "Rate limit exceeded"}},
        )

        extractor = VisionExtractor(api_key="test-key")

        with patch("time.sleep"):
            with pytest.raises(ExtractionAPIError) as exc_info:
                extractor.extract_structured(sample_images, SimpleTestSchema)

        # Should include details about the failure
        assert "rate" in str(exc_info.value).lower() or "429" in str(exc_info.value)

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_max_retries_configurable(self, mock_anthropic_class, sample_images):
        """Test that max retries is respected."""
        from anthropic import RateLimitError

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_http_response = MagicMock()
        mock_http_response.status_code = 429
        mock_http_response.headers = {}

        mock_client.messages.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=mock_http_response,
            body={"error": {"message": "Rate limit exceeded"}},
        )

        extractor = VisionExtractor(api_key="test-key")

        with patch("time.sleep"):
            with pytest.raises(ExtractionAPIError):
                extractor.extract_structured(sample_images, SimpleTestSchema)

        # Default max retries is 3, so total calls = 1 + 3 = 4
        assert mock_client.messages.create.call_count == VisionExtractor.MAX_RETRIES + 1


class TestResponseParsing:
    """Tests for parsing Claude's JSON response."""

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_handles_json_in_markdown_code_block(
        self, mock_anthropic_class, sample_images
    ):
        """Test extraction handles JSON wrapped in markdown code blocks."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type="text",
                text='```json\n{"name": {"value": "Test", "confidence": 0.9}}\n```',
            )
        ]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")
        result = extractor.extract_structured(sample_images, SimpleTestSchema)

        assert result.name.value == "Test"

    @patch("tryalma.g28.vision_extractor.Anthropic")
    def test_handles_invalid_json_response(self, mock_anthropic_class, sample_images):
        """Test invalid JSON raises ExtractionAPIError."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="not valid json {{{")]
        mock_client.messages.create.return_value = mock_response

        extractor = VisionExtractor(api_key="test-key")

        with pytest.raises(ExtractionAPIError) as exc_info:
            extractor.extract_structured(sample_images, SimpleTestSchema)

        assert "parse" in str(exc_info.value).lower() or "json" in str(
            exc_info.value
        ).lower()
