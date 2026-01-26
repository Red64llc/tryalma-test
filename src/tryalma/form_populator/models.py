"""Data models for form population results and status tracking.

This module defines shared data structures used by field handlers
and the population reporter.

Requirements Coverage:
- 12.2-12.5: Field result tracking with status
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FieldStatus(Enum):
    """Status of a field population attempt.

    Requirements: 12.2-12.5
    """

    POPULATED = "populated"
    SKIPPED = "skipped"
    ERROR = "error"
    MANUAL_REQUIRED = "manual_required"


@dataclass(frozen=True)
class FieldResult:
    """Result of a single field population attempt.

    Attributes:
        field_id: Identifier for the field.
        status: Status of the population attempt.
        value: Value that was populated (or attempted).
        error_message: Error description if status is ERROR.
        selector: CSS selector used for the field.

    Requirements: 12.2-12.5
    """

    field_id: str
    status: FieldStatus
    value: str | None = None
    error_message: str | None = None
    selector: str | None = None
