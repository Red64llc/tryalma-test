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
        prompt = """You are an expert document parser specialized in USCIS Form G-28
(Notice of Entry of Appearance as Attorney or Accredited Representative).

Analyze the provided form image(s) and extract ALL fields into a structured JSON format.

## FORM FIELD MAPPINGS

### Part 1: Attorney or Accredited Representative Information
- Field 1 "USCIS Online Account Number" -> part1_attorney_info.uscis_online_account_number
- Field 2.a "Family Name (Last Name)" -> part1_attorney_info.family_name
- Field 2.b "Given Name (First Name)" -> part1_attorney_info.given_name
- Field 2.c "Middle Name" -> part1_attorney_info.middle_name
- Field 3.a "Street Number and Name" -> part1_attorney_info.address.street_number_and_name
- Field 3.b "Apt. Ste. Flr." -> part1_attorney_info.address.apt_ste_flr
- Field 3.c "City or Town" -> part1_attorney_info.address.city_or_town
- Field 3.d "State" -> part1_attorney_info.address.state
- Field 3.e "ZIP Code" -> part1_attorney_info.address.zip_code
- Field 3.f "Province" -> part1_attorney_info.address.province
- Field 3.g "Postal Code" -> part1_attorney_info.address.postal_code
- Field 3.h "Country" -> part1_attorney_info.address.country
- Field 4 "Daytime Telephone Number" -> part1_attorney_info.daytime_telephone
- Field 5 "Mobile Telephone Number" -> part1_attorney_info.mobile_telephone
- Field 6 "Email Address" -> part1_attorney_info.email_address
- Field 7 "Fax Number" -> part1_attorney_info.fax_number

### Part 2: Eligibility Information
- Field 1.a checkbox "I am an attorney eligible to practice law..." -> part2_eligibility.is_attorney (boolean)
- Field "Licensing Authority" (text below 1.a) -> part2_eligibility.licensing_authority
- Field 1.b "Bar Number" -> part2_eligibility.bar_number
- Field 1.c checkbox for "am not"/"am" subject to orders -> part2_eligibility.is_subject_to_disciplinary_order (true if "am" is checked, false if "am not" is checked)
- Field 1.d "Name of Law Firm or Organization" -> part2_eligibility.law_firm_name
- Field 2.a checkbox "I am an accredited representative..." -> part2_eligibility.is_accredited_representative (boolean)
- Field 2.b "Name of Recognized Organization" -> part2_eligibility.recognized_organization_name
- Field 2.c "Date of Accreditation" -> part2_eligibility.accreditation_date (YYYY-MM-DD format)
- Field 3 checkbox "I am associated with..." -> part2_eligibility.is_associated (boolean)
- Field 3 text field for associated attorney name -> part2_eligibility.associated_attorney_name
- Field 4.a checkbox "I am a law student or law graduate..." -> part2_eligibility.is_law_student_or_graduate (boolean)
- Field 4.b "Name of Law Student or Law Graduate" -> part2_eligibility.law_student_name

### Part 3: Notice of Appearance
- Field 1.a checkbox "U.S. Citizenship and Immigration Services (USCIS)" -> part3_notice_of_appearance.agency_uscis (boolean)
- Field 1.b "List the form numbers or specific matter..." -> part3_notice_of_appearance.uscis_form_numbers
- Field 2.a checkbox "U.S. Immigration and Customs Enforcement (ICE)" -> part3_notice_of_appearance.agency_ice (boolean)
- Field 2.b "List the specific matter..." (ICE) -> part3_notice_of_appearance.ice_matter
- Field 3.a checkbox "U.S. Customs and Border Protection (CBP)" -> part3_notice_of_appearance.agency_cbp (boolean)
- Field 3.b "List the specific matter..." (CBP) -> part3_notice_of_appearance.cbp_matter
- Field 4 "Receipt Number" -> part3_notice_of_appearance.receipt_number
- Field 5 checkboxes "Applicant/Petitioner/Requestor/Beneficiary/Derivative/Respondent" -> part3_notice_of_appearance.representation_type (one of: "Applicant", "Petitioner", "Requestor", "Beneficiary/Derivative", "Respondent")

### Part 3: Client Information
- Field 6.a "Family Name (Last Name)" -> part3_client_info.family_name
- Field 6.b "Given Name (First Name)" -> part3_client_info.given_name
- Field 6.c "Middle Name" -> part3_client_info.middle_name
- Field 7.a "Name of Entity" -> part3_client_info.entity_name
- Field 7.b "Title of Authorized Signatory for Entity" -> part3_client_info.entity_signatory_title
- Field 8 "Client's USCIS Online Account Number" -> part3_client_info.uscis_online_account_number
- Field 9 "Client's Alien Registration Number (A-Number)" -> part3_client_info.alien_registration_number
- Field 10 "Daytime Telephone Number" -> part3_client_info.daytime_telephone
- Field 11 "Mobile Telephone Number" -> part3_client_info.mobile_telephone
- Field 12 "Email Address" -> part3_client_info.email_address
- Field 13.a "Street Number and Name" -> part3_client_info.mailing_address.street_number_and_name
- Field 13.b "Apt. Ste. Flr." -> part3_client_info.mailing_address.apt_ste_flr
- Field 13.c "City or Town" -> part3_client_info.mailing_address.city_or_town
- Field 13.d "State" -> part3_client_info.mailing_address.state
- Field 13.e "ZIP Code" -> part3_client_info.mailing_address.zip_code
- Field 13.f "Province" -> part3_client_info.mailing_address.province
- Field 13.g "Postal Code" -> part3_client_info.mailing_address.postal_code
- Field 13.h "Country" -> part3_client_info.mailing_address.country

### Part 4: Client's Consent Options (Page 3)
- Field 1.a checkbox "I request that USCIS send original notices..." -> part4_5_consent_signatures.send_notices_to_attorney (boolean)
- Field 1.b checkbox "I request that USCIS send any secure identity document..." -> part4_5_consent_signatures.send_secure_documents_to_attorney (boolean)
- Field 1.c checkbox "I request that USCIS send my notice containing Form I-94..." -> part4_5_consent_signatures.send_i94_to_client (boolean)
- Field 2.a "Signature of Client..." -> part4_5_consent_signatures.client_signature_present (boolean - true if signed)
- Field 2.b "Date of Signature" (client) -> part4_5_consent_signatures.client_signature_date (YYYY-MM-DD format)

### Part 5: Attorney/Representative Signatures (Page 3)
- Field 1.a "Signature of Attorney..." -> part4_5_consent_signatures.attorney_signature_present (boolean - true if signed)
- Field 1.b "Date of Signature" (attorney) -> part4_5_consent_signatures.attorney_signature_date (YYYY-MM-DD format)
- Field 2.b "Date of Signature" (law student) -> part4_5_consent_signatures.law_student_signature_date (YYYY-MM-DD format)

### Part 6: Additional Information (Page 4)
- Field 1.a "Family Name" -> part6_additional_info.family_name
- Field 1.b "Given Name" -> part6_additional_info.given_name
- Field 1.c "Middle Name" -> part6_additional_info.middle_name
- Additional entries (2.a-2.d, 3.a-3.d, etc.) -> part6_additional_info.entries[] with page_number, part_number, item_number, content

## EXTRACTION INSTRUCTIONS
1. Extract ALL visible text and form fields accurately
2. For EACH extracted field, provide a confidence score (0.0 to 1.0)
3. If a field is empty, marked "N/A", blank, or illegible, set its value to null
4. For checkbox fields, return boolean values (true if checked, false if not checked)
5. For date fields, use ISO 8601 format (YYYY-MM-DD)
6. Address fields should be extracted as nested objects
7. Return ONLY valid JSON, no additional text

## OUTPUT FORMAT
For most fields, wrap the value in this structure:
{"value": <extracted_value_or_null>, "confidence": <0.0-1.0>}

IMPORTANT: Address objects are DIFFERENT - they use PLAIN STRING values, NOT wrapped:
{
  "street_number_and_name": "545 Bryant Street",
  "apt_ste_flr": null,
  "city_or_town": "Palo Alto",
  "state": "CA",
  "zip_code": "94301",
  "province": null,
  "postal_code": null,
  "country": "United States of America"
}

Do NOT wrap address fields in {"value": ..., "confidence": ...} - use plain strings or null directly.

Confidence scoring:
- 1.0: Perfectly clear and unambiguous
- 0.8-0.9: Clear with minor artifacts
- 0.6-0.7: Partially obscured but readable
- 0.4-0.5: Difficult to read, uncertain
- Below 0.4: Very uncertain, consider null

## REQUIRED METADATA FIELDS
Include these at the root level:
- source_file: "extraction"
- form_detected: true (if this is a G-28 form, false otherwise)
- extraction_timestamp: current ISO timestamp
- overall_confidence: average confidence of all extracted fields

Return ONLY the JSON object, starting with { and ending with }."""

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
