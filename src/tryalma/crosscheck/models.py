"""Domain models for cross-check passport extraction.

Task 1.1: Data models for cross-check functionality.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tryalma.passport.models import PassportData


class ExtractionStatus(str, Enum):
    """Status of cross-check extraction operation.

    Per Requirement 6.2, 6.3, 6.4:
    - SUCCESS: Both sources succeeded
    - PARTIAL: One source succeeded (fallback mode)
    - ERROR: Both sources failed
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"


class DiscrepancySeverity(str, Enum):
    """Severity level for field discrepancies.

    Per Requirement 5.5:
    - CRITICAL: Identity fields (passport_number, date_of_birth)
    - WARNING: Important fields (surname, given_names, expiry_date)
    - INFORMATIONAL: Optional fields (place_of_birth, sex)
    """

    CRITICAL = "critical"
    WARNING = "warning"
    INFORMATIONAL = "informational"


@dataclass
class VisualZoneData:
    """Extracted data from passport visual zone via VLM.

    Holds structured passport field data extracted by Qwen2-VL
    from the visual (human-readable) zone of the passport.
    Per Requirement 1.3.
    """

    surname: str | None = None
    given_names: str | None = None
    date_of_birth: str | None = None  # ISO format YYYY-MM-DD
    nationality: str | None = None
    passport_number: str | None = None
    expiry_date: str | None = None  # ISO format YYYY-MM-DD
    sex: str | None = None
    place_of_birth: str | None = None
    raw_response: str | None = None


@dataclass
class FieldDiscrepancy:
    """Discrepancy between MRZ and visual zone extraction.

    Records differences between extraction sources for a single field.
    Per Requirements 5.1, 5.2, 5.3, 5.5.
    """

    field_name: str
    mrz_value: str | None
    vlm_value: str | None
    recommended_value: str | None
    severity: DiscrepancySeverity
    reason: str


@dataclass
class FieldValidationResult:
    """Result of validating a single field between sources.

    Tracks the comparison outcome for one passport field.
    Per Requirements 2.4, 2.5.
    """

    field_name: str
    validated: bool  # True if sources agree (or only one source has value)
    mrz_value: str | None
    vlm_value: str | None
    final_value: str | None  # Determined/recommended value
    discrepancy: FieldDiscrepancy | None


@dataclass
class ProcessingMetadata:
    """Metadata about the extraction process.

    Provides timing and diagnostic information.
    Per Requirement 6.5.
    """

    extraction_duration_ms: int
    mrz_duration_ms: int | None
    vlm_duration_ms: int | None
    vlm_model: str | None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CrossCheckResult:
    """Complete result of dual-source passport extraction.

    Container for all cross-check extraction results including
    validated data, confidence scores, discrepancies, and metadata.
    Per Requirements 6.1-6.5.
    """

    # Core result (Requirement 6.1)
    status: ExtractionStatus
    passport_data: "PassportData | None"

    # Confidence information (Requirements 3.1-3.5)
    field_confidences: dict[str, float] = field(default_factory=dict)
    document_confidence: float | None = None

    # Discrepancy information (Requirements 5.1-5.5)
    discrepancies: list[FieldDiscrepancy] = field(default_factory=list)

    # Source tracking (Requirement 4.4)
    sources_used: list[str] = field(default_factory=list)
    mrz_extraction_success: bool = False
    vlm_extraction_success: bool = False

    # Metadata (Requirement 6.5)
    metadata: ProcessingMetadata | None = None

    # Error handling (Requirements 6.3, 6.4)
    error: str | None = None
    mrz_error: str | None = None
    vlm_error: str | None = None

    def to_dict(self, include_metadata: bool = True) -> dict:
        """Convert to dictionary for JSON serialization.

        Args:
            include_metadata: If True, include processing metadata.

        Returns:
            Dictionary representation suitable for JSON output.
        """
        result: dict = {
            "status": self.status.value,
            "passport_data": self.passport_data.to_dict() if self.passport_data else None,
            "field_confidences": self.field_confidences,
            "document_confidence": self.document_confidence,
            "discrepancies": [
                {
                    "field_name": d.field_name,
                    "mrz_value": d.mrz_value,
                    "vlm_value": d.vlm_value,
                    "recommended_value": d.recommended_value,
                    "severity": d.severity.value,
                    "reason": d.reason,
                }
                for d in self.discrepancies
            ],
            "sources_used": self.sources_used,
            "mrz_extraction_success": self.mrz_extraction_success,
            "vlm_extraction_success": self.vlm_extraction_success,
            "error": self.error,
            "mrz_error": self.mrz_error,
            "vlm_error": self.vlm_error,
        }

        if include_metadata and self.metadata:
            result["metadata"] = {
                "extraction_duration_ms": self.metadata.extraction_duration_ms,
                "mrz_duration_ms": self.metadata.mrz_duration_ms,
                "vlm_duration_ms": self.metadata.vlm_duration_ms,
                "vlm_model": self.metadata.vlm_model,
                "timestamp": self.metadata.timestamp.isoformat(),
            }

        return result

    def has_discrepancies(self) -> bool:
        """Return True if any discrepancies exist.

        Per Requirement 5.4, indicates whether sources disagree.
        """
        return len(self.discrepancies) > 0

    def get_critical_discrepancies(self) -> list[FieldDiscrepancy]:
        """Return only critical severity discrepancies.

        Filters to discrepancies affecting identity fields.
        """
        return [d for d in self.discrepancies if d.severity == DiscrepancySeverity.CRITICAL]
