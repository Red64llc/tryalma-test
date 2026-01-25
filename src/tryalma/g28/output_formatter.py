"""Output formatting for G28 form extraction results.

Task 6: Implement OutputFormatter for JSON and YAML.

Provides formatting of G28FormData to JSON and YAML formats with support
for verbose mode (includes confidence scores and metadata) and non-verbose
mode (simplified output with just values).

Requirements: 8.1, 9.2, 9.4
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Literal

import yaml
from pydantic import BaseModel

from tryalma.g28.models import G28FormData


class OutputFormatter:
    """Formats G28 extraction results for JSON and YAML output.

    Supports verbose mode that includes confidence scores and metadata,
    and non-verbose mode that returns simplified output with just values.

    Requirements:
    - 8.1: Structured JSON-serializable output
    - 9.2: JSON output to stdout by default
    - 9.4: YAML output with --format yaml option
    """

    def format(
        self,
        data: G28FormData,
        format: Literal["json", "yaml"] = "json",
        verbose: bool = False,
    ) -> str:
        """Format G28FormData in the specified format.

        Args:
            data: G28FormData to format
            format: Output format - "json" or "yaml"
            verbose: If True, include confidence scores and metadata.
                     If False, return simplified output with just values.

        Returns:
            Formatted string in the requested format.
        """
        if format == "yaml":
            return self.format_yaml(data, verbose=verbose)
        return self.format_json(data, verbose=verbose)

    def format_json(
        self,
        data: G28FormData,
        verbose: bool = False,
    ) -> str:
        """Format G28FormData as JSON string with proper indentation.

        Args:
            data: G28FormData to format
            verbose: If True, include confidence scores and metadata.
                     If False, return simplified output with just values.

        Returns:
            JSON string with 2-space indentation.
        """
        if verbose:
            output_dict = self._to_verbose_dict(data)
        else:
            output_dict = self._to_simplified_dict(data)

        return json.dumps(output_dict, indent=2, default=self._json_serializer)

    def format_yaml(
        self,
        data: G28FormData,
        verbose: bool = False,
    ) -> str:
        """Format G28FormData as YAML string using PyYAML.

        Args:
            data: G28FormData to format
            verbose: If True, include confidence scores and metadata.
                     If False, return simplified output with just values.

        Returns:
            YAML string in block style with unicode support.
        """
        if verbose:
            output_dict = self._to_verbose_dict(data)
        else:
            output_dict = self._to_simplified_dict(data)

        # Pre-process dates for YAML serialization
        output_dict = self._prepare_for_yaml(output_dict)

        return yaml.dump(
            output_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    def _to_verbose_dict(self, data: G28FormData) -> dict[str, Any]:
        """Convert G28FormData to verbose dictionary with full field wrappers.

        Includes confidence scores, uncertain_fields, validation_warnings,
        and all metadata.

        Args:
            data: G28FormData to convert

        Returns:
            Dictionary with full ExtractedField wrappers and metadata.
        """
        return data.model_dump()

    def _to_simplified_dict(self, data: G28FormData) -> dict[str, Any]:
        """Convert G28FormData to simplified dictionary with just values.

        Excludes confidence metadata and unwraps ExtractedField values.

        Args:
            data: G28FormData to convert

        Returns:
            Dictionary with just field values (no confidence wrappers).
        """
        # Start with full dump
        full_dict = data.model_dump()

        # Create simplified output excluding metadata fields
        simplified = {
            "source_file": full_dict["source_file"],
            "form_detected": full_dict["form_detected"],
            "extraction_timestamp": full_dict["extraction_timestamp"],
        }

        # Process form sections
        section_keys = [
            "part1_attorney_info",
            "part2_eligibility",
            "part3_notice_of_appearance",
            "part3_client_info",
            "part4_5_consent_signatures",
            "part6_additional_info",
        ]

        for key in section_keys:
            section_data = full_dict.get(key)
            if section_data is not None:
                simplified[key] = self._simplify_section(section_data)
            else:
                simplified[key] = None

        return simplified

    def _simplify_section(self, section: dict[str, Any]) -> dict[str, Any]:
        """Recursively simplify a section by extracting values from ExtractedField.

        Args:
            section: Dictionary representing a form section

        Returns:
            Simplified dictionary with just values.
        """
        if section is None:
            return None

        result = {}
        for key, value in section.items():
            result[key] = self._simplify_value(value)
        return result

    def _simplify_value(self, value: Any) -> Any:
        """Simplify a single value by extracting from ExtractedField wrapper.

        Args:
            value: Value to simplify (may be ExtractedField, dict, list, or primitive)

        Returns:
            Simplified value.
        """
        if value is None:
            return None

        # Check if this is an ExtractedField dict (has 'value' and 'confidence')
        if isinstance(value, dict):
            if "value" in value and "confidence" in value:
                # This is an ExtractedField - extract just the value
                return value["value"]
            else:
                # This is a nested object (like Address) - recurse
                return self._simplify_section(value)

        # Check if this is a list (like additional_info entries)
        if isinstance(value, list):
            return [self._simplify_value(item) for item in value]

        # Primitive value - return as-is
        return value

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation.

        Raises:
            TypeError: If object cannot be serialized.
        """
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    def _prepare_for_yaml(self, data: Any) -> Any:
        """Recursively prepare data for YAML serialization.

        Converts date objects to ISO format strings for consistent output.

        Args:
            data: Data to prepare

        Returns:
            YAML-ready data structure.
        """
        if isinstance(data, dict):
            return {key: self._prepare_for_yaml(value) for key, value in data.items()}
        if isinstance(data, list):
            return [self._prepare_for_yaml(item) for item in data]
        if isinstance(data, (date, datetime)):
            return data.isoformat()
        return data
