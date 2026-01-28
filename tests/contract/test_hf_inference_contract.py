"""Contract tests for Hugging Face Inference API.

Task 2.2: Contract tests verifying HF Inference API response structure.

These tests verify that our code handles the expected HF Inference API
response structure correctly using mocked responses.

Requirements: 1.3, 1.4
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestHFInferenceAPIResponseContract:
    """Contract tests for HF Inference API chat completions response structure.

    These tests document and verify the expected response structure from
    the Hugging Face Inference API when using chat completions.
    """

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_api_response_has_choices_array(self, mock_client_class, tmp_path):
        """HF API response should have 'choices' array."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        # Create mock response matching HF API contract
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message = MagicMock()
        mock_completion.choices[0].message.content = '{"surname": "SMITH"}'
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        # Should successfully parse response
        result = await provider.extract_passport_fields(image_path)

        assert result is not None
        assert result.surname == "SMITH"

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_api_response_choice_has_message_with_content(
        self, mock_client_class, tmp_path
    ):
        """HF API response choice should have message.content field."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        # Contract: choices[0].message.content contains the model's response
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message = MagicMock()
        mock_completion.choices[0].message.content = json.dumps(
            {
                "surname": "DOE",
                "given_names": "JANE",
                "date_of_birth": "1992-05-20",
                "nationality": "CAN",
                "passport_number": "AB123456",
                "expiry_date": "2029-05-19",
                "sex": "F",
                "place_of_birth": "TORONTO",
            }
        )
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        result = await provider.extract_passport_fields(image_path)

        assert result.surname == "DOE"
        assert result.given_names == "JANE"
        assert result.date_of_birth == "1992-05-20"
        assert result.passport_number == "AB123456"

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_api_request_sends_multimodal_messages(
        self, mock_client_class, tmp_path
    ):
        """HF API request should send messages with text and image_url content types."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message = MagicMock()
        mock_completion.choices[0].message.content = '{"surname": "SMITH"}'
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        await provider.extract_passport_fields(image_path)

        # Verify the request structure matches HF API contract
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs

        # Contract: model parameter specifies the model
        assert "model" in call_kwargs
        assert call_kwargs["model"] == "Qwen/Qwen2-VL-7B-Instruct"

        # Contract: messages is an array of message objects
        assert "messages" in call_kwargs
        messages = call_kwargs["messages"]
        assert isinstance(messages, list)
        assert len(messages) >= 1

        # Contract: user message has role and content
        user_message = messages[0]
        assert user_message["role"] == "user"
        assert "content" in user_message

        # Contract: content is array with text and image_url types
        content = user_message["content"]
        assert isinstance(content, list)
        content_types = {item["type"] for item in content}
        assert "text" in content_types
        assert "image_url" in content_types

        # Contract: image_url has nested url field with data URI
        image_item = next(item for item in content if item["type"] == "image_url")
        assert "image_url" in image_item
        assert "url" in image_item["image_url"]
        assert image_item["image_url"]["url"].startswith("data:image/")

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_api_request_includes_max_tokens(self, mock_client_class, tmp_path):
        """HF API request should include max_tokens parameter."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message = MagicMock()
        mock_completion.choices[0].message.content = '{"surname": "SMITH"}'
        mock_client.chat.completions.create.return_value = mock_completion
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        await provider.extract_passport_fields(image_path)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs

        # Contract: max_tokens limits response length
        assert "max_tokens" in call_kwargs
        assert isinstance(call_kwargs["max_tokens"], int)
        assert call_kwargs["max_tokens"] > 0


class TestHFInferenceAPIClientInitializationContract:
    """Contract tests for HF Inference Client initialization."""

    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    def test_client_initialized_with_api_key(self, mock_client_class):
        """InferenceClient should be initialized with api_key parameter."""
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        provider = Qwen2VLProvider(hf_token="hf_my_api_key")

        # Access client to trigger initialization
        _ = provider.client

        # Contract: InferenceClient takes api_key parameter
        mock_client_class.assert_called_once_with(api_key="hf_my_api_key")


class TestHFInferenceAPIErrorContract:
    """Contract tests for HF Inference API error handling."""

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_api_error_is_propagated_as_vlm_extraction_error(
        self, mock_client_class, tmp_path
    ):
        """API errors should be wrapped in VLMExtractionError."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        # Contract: API may raise exceptions for various error conditions
        mock_client.chat.completions.create.side_effect = Exception(
            "HfHubHTTPError: 401 Unauthorized"
        )
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="invalid_token")

        with pytest.raises(VLMExtractionError):
            await provider.extract_passport_fields(image_path)

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_rate_limit_error_is_propagated(self, mock_client_class, tmp_path):
        """Rate limit errors should be wrapped in VLMExtractionError."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "HfHubHTTPError: 429 Too Many Requests"
        )
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(hf_token="hf_test_token")

        with pytest.raises(VLMExtractionError):
            await provider.extract_passport_fields(image_path)

    @pytest.mark.asyncio
    @patch("tryalma.crosscheck.qwen2vl_provider.InferenceClient")
    async def test_model_not_found_error_is_propagated(
        self, mock_client_class, tmp_path
    ):
        """Model not found errors should be wrapped in VLMExtractionError."""
        from tryalma.crosscheck.exceptions import VLMExtractionError
        from tryalma.crosscheck.qwen2vl_provider import Qwen2VLProvider

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(
            "Model NonExistent/Model not found"
        )
        mock_client_class.return_value = mock_client

        image_path = tmp_path / "passport.jpg"
        image_path.write_bytes(b"\xff\xd8\xff\xe0")
        provider = Qwen2VLProvider(
            hf_token="hf_test_token", model="NonExistent/Model"
        )

        with pytest.raises(VLMExtractionError):
            await provider.extract_passport_fields(image_path)
