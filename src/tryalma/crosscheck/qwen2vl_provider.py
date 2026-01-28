"""Qwen2-VL provider for Hugging Face Inference API.

Task 2.1: Qwen2-VL Hugging Face Inference API integration for passport extraction.

Requirements: 1.3, 1.4, 7.1, 7.5
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from huggingface_hub import InferenceClient

from tryalma.crosscheck.exceptions import (
    ConfigurationError,
    VLMExtractionError,
    VLMTimeoutError,
)
from tryalma.crosscheck.models import VisualZoneData

if TYPE_CHECKING:
    pass


class Qwen2VLProvider:
    """Qwen2-VL Hugging Face Inference API provider for passport extraction.

    Extracts passport data from images using Qwen2-VL vision language model
    via the Hugging Face Inference API.

    Attributes:
        SUPPORTED_FORMATS: Set of supported image file extensions.
        DEFAULT_MODEL: Default model ID for Qwen2-VL.
        EXTRACTION_PROMPT: Prompt for passport field extraction.
    """

    SUPPORTED_FORMATS: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    DEFAULT_MODEL: str = "Qwen/Qwen2.5-VL-7B-Instruct"

    EXTRACTION_PROMPT: str = """Extract the following fields from this passport image.
Return ONLY a JSON object with these exact keys (use null for missing fields):
{
  "surname": "family name in uppercase",
  "given_names": "first and middle names",
  "date_of_birth": "YYYY-MM-DD format",
  "nationality": "3-letter country code",
  "passport_number": "alphanumeric passport number",
  "expiry_date": "YYYY-MM-DD format",
  "sex": "M or F",
  "place_of_birth": "city or country name"
}
Extract from the VISUAL ZONE (printed text), not the MRZ."""

    def __init__(
        self,
        hf_token: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize with Hugging Face token.

        Args:
            hf_token: Hugging Face API token. Falls back to HF_TOKEN env var.
            model: Model ID to use. Defaults to Qwen/Qwen2-VL-7B-Instruct.
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.model = model or self.DEFAULT_MODEL
        self._client: InferenceClient | None = None

    @property
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        return "qwen2-vl"

    @property
    def client(self) -> InferenceClient:
        """Lazy initialization of InferenceClient.

        Returns:
            Configured InferenceClient instance.

        Raises:
            ConfigurationError: If HF_TOKEN is not set.
        """
        if self._client is None:
            if not self.hf_token:
                raise ConfigurationError(
                    "HF_TOKEN required. Set HF_TOKEN environment variable or pass hf_token parameter."
                )
            self._client = InferenceClient(api_key=self.hf_token)
        return self._client

    def _encode_image_base64(self, image_path: Path) -> str:
        """Encode image to base64 data URL.

        Args:
            image_path: Path to the image file.

        Returns:
            Base64 data URL string with MIME type prefix.
        """
        suffix = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        mime_type = mime_types.get(suffix, "image/jpeg")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{image_data}"

    def _parse_response(self, response: str) -> VisualZoneData:
        """Parse VLM JSON response into VisualZoneData.

        Handles:
        - Plain JSON responses
        - JSON wrapped in markdown code blocks (```json ... ``` or ``` ... ```)
        - Malformed JSON (raises VLMExtractionError)

        Args:
            response: Raw response string from the VLM.

        Returns:
            VisualZoneData with extracted fields.

        Raises:
            VLMExtractionError: If response cannot be parsed as JSON.
        """
        if not response or not response.strip():
            raise VLMExtractionError("Empty response from VLM")

        raw_response = response

        # Try to extract JSON from markdown code blocks
        # Pattern matches ```json\n...\n``` or ```\n...\n```
        code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        match = re.search(code_block_pattern, response)
        if match:
            response = match.group(1).strip()

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            raise VLMExtractionError(
                f"Failed to parse VLM response as JSON: {e}"
            ) from e

        # Validate that we got an object, not an array or primitive
        if not isinstance(data, dict):
            raise VLMExtractionError(
                f"Expected JSON object, got {type(data).__name__}"
            )

        return VisualZoneData(
            surname=data.get("surname"),
            given_names=data.get("given_names"),
            date_of_birth=data.get("date_of_birth"),
            nationality=data.get("nationality"),
            passport_number=data.get("passport_number"),
            expiry_date=data.get("expiry_date"),
            sex=data.get("sex"),
            place_of_birth=data.get("place_of_birth"),
            raw_response=raw_response,
        )

    async def extract_passport_fields(
        self,
        image_path: Path,
        timeout: float | None = None,
    ) -> VisualZoneData:
        """Extract passport fields using Qwen2-VL via HF Inference API.

        Args:
            image_path: Path to passport image.
            timeout: Optional timeout in seconds.

        Returns:
            VisualZoneData with extracted fields.

        Raises:
            VLMExtractionError: If extraction fails.
            VLMTimeoutError: If timeout exceeded.
        """
        # Encode image to base64 data URL
        image_data_url = self._encode_image_base64(image_path)

        # Build the API request
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            }
        ]

        try:
            if timeout is not None:
                # Use asyncio.timeout for timeout handling
                async with asyncio.timeout(timeout):
                    completion = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=messages,
                        max_tokens=500,
                    )
            else:
                completion = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    max_tokens=500,
                )
        except TimeoutError as e:
            raise VLMTimeoutError(
                f"Qwen2-VL extraction timed out after {timeout}s"
            ) from e
        except Exception as e:
            raise VLMExtractionError(
                f"Qwen2-VL extraction failed: {e}"
            ) from e

        # Extract response content
        response_text = completion.choices[0].message.content

        # Parse the response
        return self._parse_response(response_text)
