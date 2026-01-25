"""G28 Form Parser module.

Provides structured data extraction from USCIS Form G-28
(Notice of Entry of Appearance as Attorney or Accredited Representative).
"""

from tryalma.g28.exceptions import (
    DocumentLoadError,
    ExtractionAPIError,
    G28ExtractionError,
    LowQualityWarning,
    NotG28FormError,
    UnsupportedFormatError,
)
from tryalma.g28.models import (
    AdditionalInfo,
    AdditionalInfoEntry,
    Address,
    AttorneyInfo,
    ClientInfo,
    ConsentAndSignatures,
    EligibilityInfo,
    ExtractedField,
    G28ExtractionResult,
    G28FormData,
    NoticeOfAppearance,
)
from tryalma.g28.cli import parse_g28
from tryalma.g28.field_extractor import FieldExtractor
from tryalma.g28.output_formatter import OutputFormatter
from tryalma.g28.parser_service import G28ParserService
from tryalma.g28.vision_extractor import VisionExtractor

__all__ = [
    # CLI
    "parse_g28",
    # Exceptions
    "G28ExtractionError",
    "NotG28FormError",
    "DocumentLoadError",
    "ExtractionAPIError",
    "UnsupportedFormatError",
    "LowQualityWarning",
    # Models
    "ExtractedField",
    "Address",
    "AttorneyInfo",
    "EligibilityInfo",
    "NoticeOfAppearance",
    "ClientInfo",
    "ConsentAndSignatures",
    "AdditionalInfoEntry",
    "AdditionalInfo",
    "G28FormData",
    "G28ExtractionResult",
    # Services
    "G28ParserService",
    "VisionExtractor",
    "FieldExtractor",
    "OutputFormatter",
]
