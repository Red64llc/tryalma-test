"""Vision extraction backend using Claude Vision API.

Task 4: Vision Extraction Backend implementation.

Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.4, 5.1-5.6, 6.1-6.6, 7.1-7.3, 8.6, 10.1, 10.2
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any

from anthropic import Anthropic, APIError as AnthropicAPIError
from pydantic import BaseModel

from tryalma.g28.exceptions import ExtractionAPIError

if TYPE_CHECKING:
    from PIL import Image


class VisionExtractor:
    """Claude Vision API extraction backend.

    Task 4.1: Implement Claude Vision API client setup.
    Task 4.2: Implement structured extraction with schema.
    Task 4.3: Implement API error handling and retry logic.

    Extracts structured data using Claude Vision API with schema enforcement.
    Handles multi-page documents by including all pages in a single request.
    Reports per-field confidence based on extraction certainty indicators.

    Attributes:
        MODEL: The Claude model to use for extraction.
        MAX_TOKENS: Maximum tokens for API response.
        MAX_RETRIES: Maximum number of retry attempts for transient errors.
        BASE_RETRY_DELAY: Base delay in seconds for exponential backoff.
    """

    MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 4096
    MAX_RETRIES: int = 3
    BASE_RETRY_DELAY: float = 1.0

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize with API key from parameter or ANTHROPIC_API_KEY env var.

        Task 4.1 (P): Implement Claude Vision API client setup.
        Requirements: 8.6

        Args:
            api_key: Optional Anthropic API key. If not provided, falls back to
                     ANTHROPIC_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self._api_key:
            raise ValueError(
                "API key must be provided either as parameter or via "
                "ANTHROPIC_API_KEY environment variable"
            )

        self._client = Anthropic(api_key=self._api_key)

    def _encode_image(self, image: Image.Image) -> str:
        """Encode PIL Image to base64 PNG string.

        Task 4.2: Encode page images to base64 for API submission.

        Args:
            image: PIL Image to encode.

        Returns:
            Base64-encoded PNG string.
        """
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    def _build_extraction_prompt(self, schema: type[BaseModel]) -> str:
        """Build extraction prompt that describes fields for extraction.

        Task 4.2: Construct prompts that describe G-28 form fields for extraction.

        Args:
            schema: Pydantic model defining expected fields.

        Returns:
            Extraction prompt string.
        """
        # Get schema JSON for reference
        schema_json = schema.model_json_schema()

        prompt = f"""You are an expert document parser specialized in USCIS Form G-28
(Notice of Entry of Appearance as Attorney or Accredited Representative).

Analyze the provided form image(s) and extract all fields into a structured JSON format.

IMPORTANT INSTRUCTIONS:
1. Extract all visible text and form fields accurately
2. For each extracted field, provide a confidence score (0.0 to 1.0) indicating extraction certainty
3. If a field is empty, marked N/A, or illegible, set its value to null
4. For checkbox fields, return boolean values (true/false)
5. For date fields, use ISO 8601 format (YYYY-MM-DD) when possible
6. Return ONLY valid JSON, no additional text or explanation

The output should match this schema structure:
{json.dumps(schema_json, indent=2)}

For each field that you extract, wrap it in this structure:
{{"value": <extracted_value>, "confidence": <0.0-1.0>}}

Confidence scoring guidelines:
- 1.0: Perfectly clear and unambiguous
- 0.8-0.9: Clear with minor artifacts
- 0.6-0.7: Partially obscured but readable
- 0.4-0.5: Difficult to read, uncertain
- Below 0.4: Very uncertain, consider null

Return ONLY the JSON object, starting with {{ and ending with }}."""

        return prompt

    def _build_message_content(
        self, images: list[Image.Image], prompt: str
    ) -> list[dict[str, Any]]:
        """Build message content with images and text prompt.

        Task 4.2: Process multi-page documents by including all pages in single request.

        Args:
            images: List of page images.
            prompt: Extraction prompt.

        Returns:
            List of content blocks for API message.
        """
        content: list[dict[str, Any]] = []

        # Add all images first
        for image in images:
            encoded = self._encode_image(image)
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": encoded,
                    },
                }
            )

        # Add text prompt
        content.append({"type": "text", "text": prompt})

        return content

    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        """Parse JSON from Claude's response, handling markdown code blocks.

        Args:
            response_text: Raw response text from Claude.

        Returns:
            Parsed JSON dictionary.

        Raises:
            ExtractionAPIError: If JSON parsing fails.
        """
        # Strip whitespace
        text = response_text.strip()

        # Handle markdown code blocks
        code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ExtractionAPIError(
                f"Failed to parse JSON response from Claude: {e}. "
                f"Response text: {text[:200]}..."
            )

    def _call_api_with_retry(
        self, messages: list[dict[str, Any]]
    ) -> str:
        """Call Claude API with exponential backoff retry for transient errors.

        Task 4.3: Implement API error handling and retry logic.

        Args:
            messages: Message list for API call.

        Returns:
            Response text from successful API call.

        Raises:
            ExtractionAPIError: On authentication errors or after max retries.
        """
        from anthropic import (
            AuthenticationError,
            InternalServerError,
            RateLimitError,
        )

        last_error: Exception | None = None
        retry_count = 0

        while retry_count <= self.MAX_RETRIES:
            try:
                response = self._client.messages.create(
                    model=self.MODEL,
                    max_tokens=self.MAX_TOKENS,
                    messages=messages,
                )

                # Extract text from response
                for block in response.content:
                    if hasattr(block, "type") and block.type == "text":
                        return block.text

                raise ExtractionAPIError("No text content in Claude response")

            except AuthenticationError as e:
                # Auth errors should not be retried
                raise ExtractionAPIError(
                    f"Authentication failed - invalid API key or unauthorized access: {e}"
                )

            except RateLimitError as e:
                last_error = e
                if retry_count < self.MAX_RETRIES:
                    delay = self.BASE_RETRY_DELAY * (2**retry_count)
                    time.sleep(delay)
                    retry_count += 1
                else:
                    break

            except InternalServerError as e:
                last_error = e
                if retry_count < self.MAX_RETRIES:
                    delay = self.BASE_RETRY_DELAY * (2**retry_count)
                    time.sleep(delay)
                    retry_count += 1
                else:
                    break

            except AnthropicAPIError as e:
                # Other API errors - don't retry
                raise ExtractionAPIError(f"Claude API error: {e}")

        # Max retries exceeded
        raise ExtractionAPIError(
            f"API call failed after {self.MAX_RETRIES} retries. "
            f"Last error: {last_error}"
        )

    def extract_structured(
        self,
        images: list[Image.Image],
        schema: type[BaseModel],
    ) -> BaseModel:
        """Extract data matching schema from images.

        Task 4.2: Implement structured extraction with schema.
        Requirements: 2.1-2.5, 3.1-3.7, 4.1-4.4, 5.1-5.6, 6.1-6.6, 7.1-7.3, 8.6

        Args:
            images: Page images to process.
            schema: Pydantic model defining expected fields.

        Returns:
            Populated schema instance with extracted data.

        Raises:
            ExtractionAPIError: API call failed.
        """
        # Build prompt for this schema
        prompt = self._build_extraction_prompt(schema)

        # Build message content with all images
        content = self._build_message_content(images, prompt)

        # Build messages
        messages = [{"role": "user", "content": content}]

        # Call API with retry logic
        response_text = self._call_api_with_retry(messages)

        # Parse JSON response
        data = self._parse_json_response(response_text)

        # Validate and return as schema instance
        try:
            return schema.model_validate(data)
        except Exception as e:
            raise ExtractionAPIError(
                f"Failed to validate extraction response against schema: {e}"
            )
