"""Population reporter for tracking and generating form population reports.

This module provides the PopulationReporter class for tracking field population
results and generating comprehensive reports in JSON format.

Requirements Coverage:
- 12.1: Generate structured report in JSON format
- 12.2: Include lists of successfully populated fields with their values
- 12.3: Include lists of fields that were skipped due to missing data
- 12.4: Include lists of fields that encountered errors with error descriptions
- 12.5: Include fields requiring manual attention (signatures, unmatched values)
- 12.6: Include timestamp and target form URL
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from tryalma.form_populator.models import FieldStatus, FieldResult


@dataclass
class PopulationReport:
    """Complete report of form population operation.

    Attributes:
        success: Whether population completed without errors.
        form_url: Target form URL that was populated.
        timestamp: ISO format timestamp of report generation.
        duration_ms: Operation duration in milliseconds.
        populated_fields: List of successfully populated fields.
        skipped_fields: List of skipped fields with reasons.
        error_fields: List of fields with errors.
        manual_attention_fields: List of fields requiring manual attention.

    Requirements: 12.1, 12.6
    """

    success: bool
    form_url: str
    timestamp: str
    duration_ms: int
    populated_fields: list[FieldResult]
    skipped_fields: list[FieldResult]
    error_fields: list[FieldResult]
    manual_attention_fields: list[FieldResult]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary structure.

        Returns:
            Dictionary with all report data including summary counts.

        Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
        """
        total = (
            len(self.populated_fields)
            + len(self.skipped_fields)
            + len(self.error_fields)
            + len(self.manual_attention_fields)
        )

        return {
            "success": self.success,
            "form_url": self.form_url,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "summary": {
                "total_fields": total,
                "populated": len(self.populated_fields),
                "skipped": len(self.skipped_fields),
                "errors": len(self.error_fields),
                "manual_required": len(self.manual_attention_fields),
            },
            "populated_fields": [
                {
                    "field_id": f.field_id,
                    "value": f.value,
                    "selector": f.selector,
                }
                for f in self.populated_fields
            ],
            "skipped_fields": [
                {
                    "field_id": f.field_id,
                    "reason": f.error_message,
                }
                for f in self.skipped_fields
            ],
            "error_fields": [
                {
                    "field_id": f.field_id,
                    "error": f.error_message,
                    "selector": f.selector,
                }
                for f in self.error_fields
            ],
            "manual_attention_fields": [
                {
                    "field_id": f.field_id,
                    "reason": f.error_message,
                }
                for f in self.manual_attention_fields
            ],
        }

    def to_json(self) -> str:
        """Serialize report to JSON format.

        Returns:
            JSON string representation of the report.

        Requirements: 12.1, 12.6
        """
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class PopulationReporter:
    """Reporter for tracking field population results and generating reports.

    Tracks populated, skipped, errored, and manual attention fields during
    form population and generates comprehensive reports.

    Requirements: 12.2, 12.3, 12.4, 12.5
    """

    _populated_fields: list[FieldResult] = field(default_factory=list)
    _skipped_fields: list[FieldResult] = field(default_factory=list)
    _error_fields: list[FieldResult] = field(default_factory=list)
    _manual_attention_fields: list[FieldResult] = field(default_factory=list)

    def record_populated(
        self,
        field_id: str,
        value: str,
        selector: str,
    ) -> None:
        """Record successful field population.

        Args:
            field_id: Identifier for the field.
            value: Value that was populated.
            selector: CSS selector used for the field.

        Requirements: 12.2
        """
        result = FieldResult(
            field_id=field_id,
            status=FieldStatus.POPULATED,
            value=value,
            selector=selector,
        )
        self._populated_fields.append(result)

    def record_skipped(
        self,
        field_id: str,
        reason: str,
        selector: str | None = None,
    ) -> None:
        """Record skipped field with reason.

        Args:
            field_id: Identifier for the field.
            reason: Reason for skipping the field.
            selector: CSS selector for the field (optional).

        Requirements: 12.3
        """
        result = FieldResult(
            field_id=field_id,
            status=FieldStatus.SKIPPED,
            error_message=reason,
            selector=selector,
        )
        self._skipped_fields.append(result)

    def record_error(
        self,
        field_id: str,
        error: str,
        selector: str | None = None,
    ) -> None:
        """Record field error.

        Args:
            field_id: Identifier for the field.
            error: Error description.
            selector: CSS selector for the field (optional).

        Requirements: 12.4
        """
        result = FieldResult(
            field_id=field_id,
            status=FieldStatus.ERROR,
            error_message=error,
            selector=selector,
        )
        self._error_fields.append(result)

    def record_manual_required(
        self,
        field_id: str,
        reason: str,
    ) -> None:
        """Record field requiring manual attention.

        Args:
            field_id: Identifier for the field.
            reason: Reason manual attention is required.

        Requirements: 12.5
        """
        result = FieldResult(
            field_id=field_id,
            status=FieldStatus.MANUAL_REQUIRED,
            error_message=reason,
        )
        self._manual_attention_fields.append(result)

    def generate_report(
        self,
        form_url: str,
        start_time: datetime,
    ) -> PopulationReport:
        """Generate final population report.

        Args:
            form_url: Target form URL that was populated.
            start_time: Time when population started.

        Returns:
            PopulationReport with all tracked results.

        Requirements: 12.1, 12.6
        """
        end_time = datetime.now()
        duration = end_time - start_time
        duration_ms = int(duration.total_seconds() * 1000)

        # Determine success based on error count
        success = len(self._error_fields) == 0

        return PopulationReport(
            success=success,
            form_url=form_url,
            timestamp=end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            duration_ms=duration_ms,
            populated_fields=list(self._populated_fields),
            skipped_fields=list(self._skipped_fields),
            error_fields=list(self._error_fields),
            manual_attention_fields=list(self._manual_attention_fields),
        )

    def reset(self) -> None:
        """Reset all tracked fields.

        Clears all populated, skipped, error, and manual attention fields.
        """
        self._populated_fields.clear()
        self._skipped_fields.clear()
        self._error_fields.clear()
        self._manual_attention_fields.clear()
