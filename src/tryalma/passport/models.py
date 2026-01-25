"""Domain models for passport data extraction.

Task 2.1, 2.2: PassportData, ExtractionResult, RawMRZData, ValidationResult,
CheckDigitResult dataclasses and MRZType enum.

Requirements: 2.1-2.9, 3.3, 6.1, 6.2, 6.4
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path


class MRZType(Enum):
    """Machine Readable Zone format types.

    Supports ICAO 9303 standard MRZ formats.
    """

    TD1 = "TD1"  # ID cards: 3 lines, 30 chars each
    TD2 = "TD2"  # ID cards: 2 lines, 36 chars each
    TD3 = "TD3"  # Passports: 2 lines, 44 chars each
    MRVA = "MRVA"  # Visa type A: 2 lines, 44 chars each
    MRVB = "MRVB"  # Visa type B: 2 lines, 36 chars each


@dataclass
class PassportData:
    """Extracted passport information.

    Contains all passport fields per Requirements 2.1-2.8, with MRZ validation
    metadata per Requirements 6.2-6.3.
    """

    # Source information (Requirement 3.3)
    source_file: Path

    # Personal information (Requirements 2.1-2.8)
    surname: str | None = None
    given_names: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    passport_number: str | None = None
    expiry_date: date | None = None
    sex: str | None = None  # M, F, or None
    place_of_birth: str | None = None  # Optional field (2.8)

    # MRZ validation (Requirements 6.2-6.3)
    mrz_type: str | None = None  # TD1, TD3, etc.
    mrz_valid: bool = False
    check_digit_errors: list[str] = field(default_factory=list)

    # Extraction metadata
    confidence: float | None = None
    raw_mrz: str | None = None

    def to_dict(self, verbose: bool = False) -> dict:
        """Convert to dictionary for JSON serialization.

        Args:
            verbose: If True, include confidence scores and raw MRZ.

        Returns:
            Dictionary representation of passport data.
        """
        result = {
            "source_file": str(self.source_file),
            "surname": self.surname,
            "given_names": self.given_names,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "nationality": self.nationality,
            "passport_number": self.passport_number,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "sex": self.sex,
            "place_of_birth": self.place_of_birth,
            "mrz_type": self.mrz_type,
            "mrz_valid": self.mrz_valid,
            "check_digit_errors": self.check_digit_errors,
        }

        if verbose:
            result["confidence"] = self.confidence
            result["raw_mrz"] = self.raw_mrz

        return result

    def get_unavailable_fields(self) -> list[str]:
        """Return list of fields that could not be extracted.

        Per Requirement 2.9, identifies fields that are None.

        Returns:
            List of field names that have None values.
        """
        personal_fields = [
            "surname",
            "given_names",
            "date_of_birth",
            "nationality",
            "passport_number",
            "expiry_date",
            "sex",
            "place_of_birth",
        ]

        unavailable = []
        for field_name in personal_fields:
            if getattr(self, field_name) is None:
                unavailable.append(field_name)

        return unavailable


@dataclass
class ExtractionResult:
    """Result of extracting passport data from an image.

    Wraps PassportData with success/failure status for service layer.
    """

    success: bool
    data: PassportData | None
    error: str | None
    source_file: Path


@dataclass
class RawMRZData:
    """Raw MRZ extraction result from PassportEye.

    Contains the raw extracted data before validation and conversion.
    Requirements: 6.1
    """

    mrz_type: str  # TD1, TD2, TD3, MRVA, MRVB
    raw_text: str

    # Extracted fields (all optional as extraction may be partial)
    surname: str | None = None
    given_names: str | None = None
    country: str | None = None
    nationality: str | None = None
    birth_date: str | None = None  # YYMMDD format
    sex: str | None = None  # M, F, or <
    expiry_date: str | None = None  # YYMMDD format
    document_number: str | None = None
    optional_data: str | None = None
    confidence: float | None = None  # 0.0 to 1.0 if available


@dataclass
class CheckDigitResult:
    """Result of a single check digit validation.

    Part of ICAO 9303 compliance (Requirement 6.2).
    """

    field_name: str
    is_valid: bool
    expected: str | None
    actual: str | None


@dataclass
class ValidationResult:
    """Complete MRZ validation result.

    Contains all check digit validation results per ICAO 9303 standards.
    Requirements: 6.2, 6.3, 6.4
    """

    is_valid: bool
    mrz_type: MRZType
    check_digits: list[CheckDigitResult]
    warnings: list[str]
