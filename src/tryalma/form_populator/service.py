"""Form Population Service for orchestrating web form population.

This module provides the FormPopulationService class that orchestrates
the complete form population workflow using browser automation.

Requirements Coverage:
- 8.1: Populate fields in order defined by mapping configuration
- 8.2: Provide summary report of populated, skipped, and error fields
- 8.3: Add configurable delays between interactions to avoid bot detection
- 8.4: Stop and report error with partial completion on critical errors
- 8.5: Never submit form or interact with submit buttons
- 9.1: Never populate signature fields
- 9.2: Never populate signature date fields
- 9.3: Log signature fields for manual completion
- 11.1: Accept extracted data in structured dictionary format
- 11.2: Validate extracted data contains minimum required fields
- 11.3: Populate available fields when data is incomplete
- 11.4: Support data from multiple document types
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from tryalma.form_populator.browser_controller import BrowserController
from tryalma.form_populator.field_mapping_config import (
    FieldMapping,
    FieldMappingConfig,
    FieldType,
)
from tryalma.form_populator.models import FieldStatus, FieldResult
from tryalma.form_populator.reporter import PopulationReport, PopulationReporter

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PopulationConfig:
    """Configuration for form population.

    Attributes:
        headless: Run browser in headless mode (default True).
        timeout_ms: Default timeout for operations in milliseconds (default 30000).
        inter_field_delay_ms: Delay between field interactions in ms (default 50).
        retry_count: Number of retries for failed operations (default 3).
        debug_mode: Enable debug mode for visual inspection (default False).
    """

    headless: bool = True
    timeout_ms: int = 30000
    inter_field_delay_ms: int = 50
    retry_count: int = 3
    debug_mode: bool = False


class FormPopulationService:
    """Service for orchestrating form population workflow.

    Coordinates browser lifecycle, field population using handlers,
    and report generation. Follows the mapping configuration to populate
    fields in order while excluding signature fields.

    Requirements: 8.1-8.5, 9.1-9.3, 11.1-11.4
    """

    def __init__(
        self,
        config: PopulationConfig | None = None,
        mapping_config: FieldMappingConfig | None = None,
    ) -> None:
        """Initialize FormPopulationService.

        Args:
            config: Population configuration (defaults to PopulationConfig()).
            mapping_config: Field mapping configuration (defaults to FieldMappingConfig()).
        """
        self._config = config or PopulationConfig()
        self._mapping_config = mapping_config or FieldMappingConfig()
        self._reporter = PopulationReporter()

    def validate_extracted_data(
        self,
        extracted_data: dict[str, Any],
    ) -> list[str]:
        """Validate extracted data contains minimum required fields.

        Args:
            extracted_data: Dictionary of field_id -> value from extraction.

        Returns:
            List of missing required field IDs (empty if all present).

        Requirements: 11.2
        """
        return self._mapping_config.validate_data(extracted_data)

    def populate(
        self,
        form_url: str,
        extracted_data: dict[str, Any],
    ) -> PopulationReport:
        """Populate web form with extracted data.

        Orchestrates the complete form population workflow:
        1. Launch browser
        2. Navigate to form URL
        3. Wait for form to be ready
        4. Populate fields in order (excluding signatures)
        5. Close browser
        6. Generate and return report

        Args:
            form_url: Target form URL to populate.
            extracted_data: Dictionary of field_id -> value from extraction.

        Returns:
            PopulationReport with success status and field details.

        Requirements: 8.1, 8.2, 8.5, 9.1-9.3, 11.1, 11.3, 11.4
        """
        start_time = datetime.now()
        self._reporter.reset()

        # Create browser controller with config
        browser = BrowserController(
            headless=self._config.headless,
            timeout_ms=self._config.timeout_ms,
        )

        # Record signature fields as manual required
        self._record_signature_fields_as_manual_required()

        try:
            with browser.launch():
                # Navigate to form
                browser.navigate(form_url)
                # Wait for form container or first input to be ready
                # Some pages use <form>, others use <div class="form-container">
                browser.wait_for_form_ready(form_selector=".form-container, form, input")

                # Populate fields in order
                self._populate_fields(browser, extracted_data)

        except Exception as e:
            logger.error("Form population failed: %s", str(e))
            # Report generation will reflect the error

        return self._reporter.generate_report(form_url, start_time)

    def _record_signature_fields_as_manual_required(self) -> None:
        """Record all signature fields as requiring manual attention.

        Requirements: 9.1, 9.2, 9.3
        """
        for mapping in self._mapping_config.get_signature_mappings():
            self._reporter.record_manual_required(
                field_id=mapping.field_id,
                reason="Signature requires manual completion",
            )

    def _populate_fields(
        self,
        browser: BrowserController,
        extracted_data: dict[str, Any],
    ) -> None:
        """Populate form fields from extracted data.

        Args:
            browser: BrowserController instance.
            extracted_data: Dictionary of field_id -> value.

        Requirements: 8.1, 8.3, 11.3
        """
        populatable_mappings = self._mapping_config.get_populatable_mappings()
        first_field = True

        # Debug: Log mapping info
        print(f"[DEBUG] Populatable mappings: {[m.field_id for m in populatable_mappings]}")
        print(f"[DEBUG] Extracted data keys: {list(extracted_data.keys())}")

        for mapping in populatable_mappings:
            # Add delay between fields (skip for first field)
            if not first_field and self._config.inter_field_delay_ms > 0:
                time.sleep(self._config.inter_field_delay_ms / 1000.0)
            first_field = False

            # Check if we have data for this field
            if mapping.field_id not in extracted_data or extracted_data[mapping.field_id] is None:
                print(f"[DEBUG] Skipping {mapping.field_id} - no data available")
                self._reporter.record_skipped(
                    field_id=mapping.field_id,
                    reason="No data available",
                    selector=mapping.selector,
                )
                continue

            value = extracted_data[mapping.field_id]
            print(f"[DEBUG] Populating {mapping.field_id} with value '{value}' using selector '{mapping.selector}'")

            # Populate based on field type
            try:
                self._populate_single_field(browser, mapping, value)
                print(f"[DEBUG] Successfully populated {mapping.field_id}")
                self._reporter.record_populated(
                    field_id=mapping.field_id,
                    value=str(value),
                    selector=mapping.selector,
                )
            except Exception as e:
                print(f"[DEBUG] Failed to populate {mapping.field_id}: {e}")
                logger.warning(
                    "Failed to populate field %s: %s",
                    mapping.field_id,
                    str(e),
                )
                self._reporter.record_error(
                    field_id=mapping.field_id,
                    error=str(e),
                    selector=mapping.selector,
                )

    def _populate_single_field(
        self,
        browser: BrowserController,
        mapping: FieldMapping,
        value: Any,
    ) -> None:
        """Populate a single form field.

        Args:
            browser: BrowserController instance.
            mapping: Field mapping configuration.
            value: Value to populate.

        Requirements: 4.1-4.5, 5.1-5.5, 6.1-6.5, 7.1-7.5
        """
        if mapping.field_type == FieldType.TEXT:
            self._populate_text_field(browser, mapping, value)
        elif mapping.field_type == FieldType.DROPDOWN:
            self._populate_dropdown_field(browser, mapping, value)
        elif mapping.field_type == FieldType.CHECKBOX:
            self._populate_checkbox_field(browser, mapping, value)
        elif mapping.field_type == FieldType.RADIO:
            self._populate_radio_field(browser, mapping, value)
        elif mapping.field_type == FieldType.DATE:
            self._populate_date_field(browser, mapping, value)
        # FieldType.SIGNATURE is never populated (handled earlier)

    def _populate_text_field(
        self,
        browser: BrowserController,
        mapping: FieldMapping,
        value: Any,
    ) -> None:
        """Populate text input field.

        Args:
            browser: BrowserController instance.
            mapping: Field mapping configuration.
            value: Value to populate.
        """
        str_value = str(value)

        # Check for maxlength and truncate if needed
        maxlength = browser.get_attribute(mapping.selector, "maxlength")
        if maxlength is not None:
            try:
                max_len = int(maxlength)
                str_value = str_value[:max_len]
            except ValueError:
                pass

        # Format phone numbers if needed
        if mapping.format_pattern and mapping.format_pattern == "###-###-####":
            str_value = self._format_phone(str_value)

        browser.fill(mapping.selector, str_value)

    def _format_phone(self, value: str) -> str:
        """Format phone number to ###-###-#### pattern.

        Args:
            value: Phone number string.

        Returns:
            Formatted phone number.
        """
        import re
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:10]}"
        return value

    def _populate_dropdown_field(
        self,
        browser: BrowserController,
        mapping: FieldMapping,
        value: Any,
    ) -> None:
        """Populate dropdown/select field.

        Args:
            browser: BrowserController instance.
            mapping: Field mapping configuration.
            value: Value to select.
        """
        str_value = str(value)
        try:
            browser.select_option(mapping.selector, value=str_value)
        except Exception:
            # Try by label
            try:
                browser.select_option(mapping.selector, label=str_value)
            except Exception:
                raise

    def _populate_checkbox_field(
        self,
        browser: BrowserController,
        mapping: FieldMapping,
        value: Any,
    ) -> None:
        """Populate checkbox field.

        Args:
            browser: BrowserController instance.
            mapping: Field mapping configuration.
            value: Boolean or truthy value.
        """
        if value:
            browser.check(mapping.selector)
        else:
            browser.uncheck(mapping.selector)

    def _populate_radio_field(
        self,
        browser: BrowserController,
        mapping: FieldMapping,
        value: Any,
    ) -> None:
        """Populate radio button field.

        Args:
            browser: BrowserController instance.
            mapping: Field mapping configuration.
            value: Value to select.
        """
        str_value = str(value)
        # Build selector with value
        selector = f"{mapping.selector}[value='{str_value}']"
        browser.check(selector)

    def _populate_date_field(
        self,
        browser: BrowserController,
        mapping: FieldMapping,
        value: Any,
    ) -> None:
        """Populate date field.

        Args:
            browser: BrowserController instance.
            mapping: Field mapping configuration.
            value: Date value (string or date object).
        """
        from datetime import date as date_type
        import re

        str_value = str(value)

        # HTML date inputs require ISO format (YYYY-MM-DD)
        if isinstance(value, date_type):
            str_value = value.strftime("%Y-%m-%d")
        elif re.match(r"^\d{2}/\d{2}/\d{4}$", str_value):
            # US format (MM/DD/YYYY) - convert to ISO format
            parts = str_value.split("/")
            str_value = f"{parts[2]}-{parts[0]}-{parts[1]}"
        # If already ISO format (YYYY-MM-DD), use as-is

        browser.fill(mapping.selector, str_value)
