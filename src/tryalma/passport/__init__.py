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
from tryalma.passport.extractor import MRZExtractor
from tryalma.passport.formatter import OutputFormat, OutputFormatter
from tryalma.passport.models import (
    CheckDigitResult,
    ExtractionResult,
    MRZType,
    PassportData,
    RawMRZData,
    ValidationResult,
)
from tryalma.passport.service import PassportExtractionService
from tryalma.passport.validator import MRZValidator

__all__ = [
    # Models
    "PassportData",
    "ExtractionResult",
    "RawMRZData",
    "MRZType",
    "ValidationResult",
    "CheckDigitResult",
    # Extractor
    "MRZExtractor",
    # Service
    "PassportExtractionService",
    # Validator
    "MRZValidator",
    # Formatter
    "OutputFormat",
    "OutputFormatter",
    # Exceptions
    "PassportExtractionError",
    "MRZNotFoundError",
    "UnsupportedFormatError",
    "TesseractNotFoundError",
    "ImageReadError",
]
