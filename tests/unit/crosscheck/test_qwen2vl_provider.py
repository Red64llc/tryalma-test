"""Unit tests for Qwen2-VL provider.

Task 2.2: Tests for Qwen2-VL Hugging Face Inference API provider.

Requirements: 1.3, 1.4
"""

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestQwen2VLProviderInitialization:
    """Tests for Qwen2VLProvider initialization."""

    def test_provider_accepts_hf_token_parameter(self):
        """Provider should accept HF token as constructor parameter."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token_123")

        assert provider.hf_token == "hf_test_token_123"

    def test_provider_accepts_model_parameter(self):
        """Provider should accept custom model ID."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(
            hf_token="hf_test_token", model="Qwen/Qwen2-VL-72B-Instruct"
        )

        assert provider.model == "Qwen/Qwen2-VL-72B-Instruct"

    def test_provider_has_default_model(self):
        """Provider should default to Qwen2-VL-7B-Instruct model."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")

        assert provider.model == "Qwen/Qwen2-VL-7B-Instruct"

    def test_provider_falls_back_to_env_variable(self, monkeypatch):
        """Provider should fall back to HF_TOKEN environment variable."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        monkeypatch.setenv("HF_TOKEN", "hf_env_token_456")

        provider = Qwen2VLProvider()

        assert provider.hf_token == "hf_env_token_456"

    def test_provider_prefers_parameter_over_env(self, monkeypatch):
        """Provider should prefer explicit parameter over env variable."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        monkeypatch.setenv("HF_TOKEN", "hf_env_token")

        provider = Qwen2VLProvider(hf_token="hf_param_token")

        assert provider.hf_token == "hf_param_token"

    def test_provider_has_provider_name(self):
        """Provider should expose its name as 'qwen2-vl'."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")

        assert provider.provider_name == "qwen2-vl"


class TestQwen2VLProviderClientInitialization:
    """Tests for lazy client initialization."""

    def test_client_not_initialized_on_construction(self):
        """Client should not be initialized during construction."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")

        assert provider._client is None

    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    def test_client_initialized_on_first_access(self, mock_client_class):
        """Client should be initialized lazily on first access."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        # Access client property
        client = provider.client

        mock_client_class.assert_called_once_with(api_key="hf_test_token")
        assert client is mock_client

    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    def test_client_reused_on_subsequent_access(self, mock_client_class):
        """Client should be reused for subsequent accesses."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        # Access client twice
        client1 = provider.client
        client2 = provider.client

        mock_client_class.assert_called_once()
        assert client1 is client2

    def test_client_raises_configuration_error_when_token_missing(self):
        """Client access should raise ConfigurationError when token missing."""
        from tryalma.crosscheck.exceptions import ConfigurationError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token=None)

        with pytest.raises(ConfigurationError) as exc_info:
            _ = provider.client

        assert "HF_TOKEN" in str(exc_info.value)
        assert "required" in str(exc_info.value).lower()

    def test_client_configuration_error_provides_guidance(self):
        """ConfigurationError should provide guidance on setting token."""
        from tryalma.crosscheck.exceptions import ConfigurationError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token=None)

        with pytest.raises(ConfigurationError) as exc_info:
            _ = provider.client

        error_message = str(exc_info.value).lower()
        assert "environment variable" in error_message or "hf_token" in error_message


class TestQwen2VLProviderImageEncoding:
    """Tests for base64 image encoding with MIME type detection."""

    def test_encode_jpeg_image(self, tmp_path):
        """Provider should encode JPEG image with correct MIME type."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        # Create a minimal JPEG file
        image_path = tmp_path / "test.jpg"
        image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"  # JPEG header
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/jpeg;base64,")
        encoded_data = result.split(",")[1]
        assert base64.b64decode(encoded_data) == image_data

    def test_encode_jpeg_with_jpeg_extension(self, tmp_path):
        """Provider should handle .jpeg extension."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "test.jpeg"
        image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/jpeg;base64,")

    def test_encode_png_image(self, tmp_path):
        """Provider should encode PNG image with correct MIME type."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "test.png"
        image_data = b"\x89PNG\r\n\x1a\n"  # PNG header
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/png;base64,")
        encoded_data = result.split(",")[1]
        assert base64.b64decode(encoded_data) == image_data

    def test_encode_webp_image(self, tmp_path):
        """Provider should encode WebP image with correct MIME type."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "test.webp"
        image_data = b"RIFF\x00\x00\x00\x00WEBP"  # WebP header
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/webp;base64,")

    def test_encode_gif_image(self, tmp_path):
        """Provider should encode GIF image with correct MIME type."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "test.gif"
        image_data = b"GIF89a"  # GIF header
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/gif;base64,")

    def test_encode_handles_uppercase_extension(self, tmp_path):
        """Provider should handle uppercase file extensions."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "test.JPG"
        image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/jpeg;base64,")

    def test_encode_defaults_unknown_extension_to_jpeg(self, tmp_path):
        """Provider should default unknown extensions to JPEG MIME type."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "test.unknown"
        image_data = b"some binary data"
        image_path.write_bytes(image_data)
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = provider._encode_image_base64(image_path)

        assert result.startswith("data:image/jpeg;base64,")


class TestQwen2VLProviderSupportedFormats:
    """Tests for supported format constants."""

    def test_supported_formats_includes_jpg(self):
        """Provider should support .jpg format."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        assert ".jpg" in Qwen2VLProvider.SUPPORTED_FORMATS

    def test_supported_formats_includes_jpeg(self):
        """Provider should support .jpeg format."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        assert ".jpeg" in Qwen2VLProvider.SUPPORTED_FORMATS

    def test_supported_formats_includes_png(self):
        """Provider should support .png format."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        assert ".png" in Qwen2VLProvider.SUPPORTED_FORMATS

    def test_supported_formats_includes_webp(self):
        """Provider should support .webp format."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        assert ".webp" in Qwen2VLProvider.SUPPORTED_FORMATS

    def test_supported_formats_includes_gif(self):
        """Provider should support .gif format."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        assert ".gif" in Qwen2VLProvider.SUPPORTED_FORMATS


class TestQwen2VLProviderResponseParsing:
    """Tests for parsing VLM JSON responses."""

    def test_parse_valid_json_response(self):
        """Provider should parse valid JSON response into VisualZoneData."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        json_response = json.dumps(
            {
                "surname": "SMITH",
                "given_names": "JOHN WILLIAM",
                "date_of_birth": "1985-03-15",
                "nationality": "USA",
                "passport_number": "123456789",
                "expiry_date": "2030-03-14",
                "sex": "M",
                "place_of_birth": "NEW YORK",
            }
        )

        result = provider._parse_response(json_response)

        assert result.surname == "SMITH"
        assert result.given_names == "JOHN WILLIAM"
        assert result.date_of_birth == "1985-03-15"
        assert result.nationality == "USA"
        assert result.passport_number == "123456789"
        assert result.expiry_date == "2030-03-14"
        assert result.sex == "M"
        assert result.place_of_birth == "NEW YORK"

    def test_parse_stores_raw_response(self):
        """Provider should store raw response in VisualZoneData."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        json_response = '{"surname": "SMITH"}'

        result = provider._parse_response(json_response)

        assert result.raw_response == json_response

    def test_parse_markdown_wrapped_json(self):
        """Provider should handle JSON wrapped in markdown code blocks."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        markdown_response = """```json
{
    "surname": "JOHNSON",
    "given_names": "ALICE",
    "date_of_birth": "1990-07-22",
    "nationality": "GBR",
    "passport_number": "987654321",
    "expiry_date": "2028-07-21",
    "sex": "F",
    "place_of_birth": "LONDON"
}
```"""

        result = provider._parse_response(markdown_response)

        assert result.surname == "JOHNSON"
        assert result.given_names == "ALICE"
        assert result.nationality == "GBR"

    def test_parse_markdown_without_language_tag(self):
        """Provider should handle markdown code blocks without language tag."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        markdown_response = """```
{"surname": "DOE", "given_names": "JANE"}
```"""

        result = provider._parse_response(markdown_response)

        assert result.surname == "DOE"
        assert result.given_names == "JANE"

    def test_parse_handles_null_values(self):
        """Provider should handle null values in JSON response."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        json_response = json.dumps(
            {
                "surname": "SMITH",
                "given_names": null if False else None,  # JSON null
                "date_of_birth": None,
                "nationality": "USA",
                "passport_number": None,
                "expiry_date": None,
                "sex": None,
                "place_of_birth": None,
            }
        )

        result = provider._parse_response(json_response)

        assert result.surname == "SMITH"
        assert result.given_names is None
        assert result.date_of_birth is None

    def test_parse_handles_missing_fields(self):
        """Provider should handle missing fields by setting them to None."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        json_response = '{"surname": "SMITH", "nationality": "USA"}'

        result = provider._parse_response(json_response)

        assert result.surname == "SMITH"
        assert result.nationality == "USA"
        assert result.given_names is None
        assert result.date_of_birth is None
        assert result.passport_number is None
        assert result.expiry_date is None
        assert result.sex is None
        assert result.place_of_birth is None

    def test_parse_malformed_json_raises_error(self):
        """Provider should raise VLMExtractionError for malformed JSON."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")
        malformed_response = "This is not valid JSON {broken"

        with pytest.raises(VLMExtractionError) as exc_info:
            provider._parse_response(malformed_response)

        assert "parse" in str(exc_info.value).lower() or "json" in str(
            exc_info.value
        ).lower()

    def test_parse_empty_response_raises_error(self):
        """Provider should raise VLMExtractionError for empty response."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMExtractionError):
            provider._parse_response("")

    def test_parse_non_object_json_raises_error(self):
        """Provider should raise VLMExtractionError for non-object JSON."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMExtractionError):
            provider._parse_response('["array", "not", "object"]')


class TestQwen2VLProviderExtractionPrompt:
    """Tests for extraction prompt."""

    def test_provider_has_extraction_prompt(self):
        """Provider should have extraction prompt defined."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        assert Qwen2VLProvider.EXTRACTION_PROMPT is not None
        assert len(Qwen2VLProvider.EXTRACTION_PROMPT) > 0

    def test_extraction_prompt_requests_json_output(self):
        """Extraction prompt should request JSON output."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        prompt = Qwen2VLProvider.EXTRACTION_PROMPT.lower()

        assert "json" in prompt

    def test_extraction_prompt_lists_required_fields(self):
        """Extraction prompt should list all required passport fields."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        prompt = Qwen2VLProvider.EXTRACTION_PROMPT.lower()

        assert "surname" in prompt
        assert "given_names" in prompt or "given names" in prompt
        assert "date_of_birth" in prompt or "date of birth" in prompt
        assert "nationality" in prompt
        assert "passport_number" in prompt or "passport number" in prompt
        assert "expiry_date" in prompt or "expiry date" in prompt
        assert "sex" in prompt


class TestQwen2VLProviderAsyncExtraction:
    """Tests for async extraction method."""

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_passport_fields_returns_visual_zone_data(
        self, mock_client_class, tmp_path
    ):
        """Extraction should return VisualZoneData on success."""
        from tryalma.crosscheck.models import VisualZoneData
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        # Setup mock response
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(
            {
                "surname": "SMITH",
                "given_names": "JOHN",
                "date_of_birth": "1985-03-15",
                "nationality": "USA",
                "passport_number": "123456789",
                "expiry_date": "2030-03-14",
                "sex": "M",
                "place_of_birth": "NEW YORK",
            }
        )
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        # Create test image
        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = await provider.extract_passport_fields(image_path)

        assert isinstance(result, VisualZoneData)
        assert result.surname == "SMITH"
        assert result.given_names == "JOHN"
        assert result.passport_number == "123456789"

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_sends_image_and_prompt_to_api(
        self, mock_client_class, tmp_path
    ):
        """Extraction should send image and prompt to HF API."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = '{"surname": "SMITH"}'
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        await provider.extract_passport_fields(image_path)

        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs

        # Verify model
        assert call_kwargs["model"] == "Qwen/Qwen2-VL-7B-Instruct"

        # Verify messages structure
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

        # Verify content has text and image
        content = messages[0]["content"]
        assert len(content) == 2
        text_part = next(c for c in content if c["type"] == "text")
        image_part = next(c for c in content if c["type"] == "image_url")
        assert text_part["text"] == Qwen2VLProvider.EXTRACTION_PROMPT
        assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_uses_configured_model(self, mock_client_class, tmp_path):
        """Extraction should use configured model ID."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = '{"surname": "SMITH"}'
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(
            hf_token="hf_test_token", model="Qwen/Qwen2-VL-72B-Instruct"
        )

        await provider.extract_passport_fields(image_path)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "Qwen/Qwen2-VL-72B-Instruct"


class TestQwen2VLProviderTimeoutHandling:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_accepts_timeout_parameter(self, mock_client_class, tmp_path):
        """Extraction should accept timeout parameter."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = '{"surname": "SMITH"}'
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        # Should not raise
        result = await provider.extract_passport_fields(image_path, timeout=30.0)

        assert result.surname == "SMITH"

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_raises_vlm_timeout_error_on_timeout(
        self, mock_client_class, tmp_path
    ):
        """Extraction should raise VLMTimeoutError when timeout exceeded."""
        import time

        from tryalma.crosscheck.exceptions import VLMTimeoutError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")

        # Mock client to simulate slow response using sync sleep
        # (asyncio.to_thread runs sync functions in a thread)
        def slow_api_call(*args, **kwargs):
            time.sleep(10)  # Longer than timeout

        mock_client = MagicMock()
        mock_client.chat.completions.create = slow_api_call
        mock_client_class.return_value = mock_client

        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMTimeoutError):
            await provider.extract_passport_fields(image_path, timeout=0.1)


class TestQwen2VLProviderErrorHandling:
    """Tests for error handling and propagation."""

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_raises_vlm_extraction_error_on_api_error(
        self, mock_client_class, tmp_path
    ):
        """Extraction should raise VLMExtractionError on API error."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "API rate limit exceeded"
        )
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMExtractionError) as exc_info:
            await provider.extract_passport_fields(image_path)

        assert "rate limit" in str(exc_info.value).lower() or "failed" in str(
            exc_info.value
        ).lower()

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_raises_vlm_extraction_error_on_empty_response(
        self, mock_client_class, tmp_path
    ):
        """Extraction should raise VLMExtractionError on empty API response."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = ""
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMExtractionError):
            await provider.extract_passport_fields(image_path)

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_extract_raises_vlm_extraction_error_on_malformed_response(
        self, mock_client_class, tmp_path
    ):
        """Extraction should raise VLMExtractionError on malformed JSON response."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = (
            "I'm sorry, I cannot extract passport data from this image."
        )
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMExtractionError):
            await provider.extract_passport_fields(image_path)
