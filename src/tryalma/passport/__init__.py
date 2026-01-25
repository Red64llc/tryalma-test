"""Passport data extraction module.

Provides domain models, exceptions, and utilities for extracting
structured data from passport images using MRZ (Machine Readable Zone)
OCR technology.
"""

from tryalma.passport.exceptions import (
    ImageReadError,
    MRZNotFoundError,
    PassportExtractionError,
    TesseractNotFoundError,
    UnsupportedFormatError,
)
from tryalma.passport.models import (
    CheckDigitResult,
    ExtractionResult,
    MRZType,
    PassportData,
    RawMRZData,
    ValidationResult,
)

__all__ = [
    # Models
    "PassportData",
    "ExtractionResult",
    "RawMRZData",
    "MRZType",
    "ValidationResult",
    "CheckDigitResult",
    # Exceptions
    "PassportExtractionError",
    "MRZNotFoundError",
    "UnsupportedFormatError",
    "TesseractNotFoundError",
    "ImageReadError",
]
