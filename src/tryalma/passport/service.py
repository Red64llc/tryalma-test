"""Passport extraction service layer.

Task 5.1: Single image extraction workflow
Task 5.2: Batch directory processing

Requirements: 1.1, 1.2, 1.4, 5.1, 5.2

Provides a framework-agnostic service that orchestrates passport extraction
and validation. This service can be used by CLI, Flask, FastAPI, or any
other Python application.
"""

from collections.abc import Callable
from datetime import date
from pathlib import Path

from tryalma.passport.exceptions import PassportExtractionError
from tryalma.passport.extractor import MRZExtractor
from tryalma.passport.models import (
    ExtractionResult,
    PassportData,
    RawMRZData,
    ValidationResult,
)
from tryalma.passport.validator import MRZValidator


class PassportExtractionService:
    """Service for extracting passport data from images.

    Framework-agnostic service that orchestrates the extraction workflow:
    1. Extract MRZ data from image using MRZExtractor
    2. Validate MRZ check digits using MRZValidator
    3. Convert raw data to PassportData with proper date parsing

    This service can be injected into CLI, Flask, FastAPI, or any other
    Python application.

    Attributes:
        _extractor: MRZExtractor instance for OCR extraction.
        _validator: MRZValidator instance for ICAO 9303 validation.
    """

    def __init__(
        self,
        extractor: MRZExtractor,
        validator: MRZValidator,
    ) -> None:
        """Initialize the service with dependencies.

        Args:
            extractor: MRZExtractor instance for MRZ extraction.
            validator: MRZValidator instance for check digit validation.
        """
        self._extractor = extractor
        self._validator = validator

    def extract_single(self, image_path: Path) -> ExtractionResult:
        """Extract passport data from a single image.

        Orchestrates extraction and validation, converting raw MRZ data
        to PassportData with proper date parsing.

        Args:
            image_path: Path to the passport image file.

        Returns:
            ExtractionResult with passport data or error details.
            Success is True even if MRZ validation fails (data is still extracted).
        """
        try:
            # Step 1: Extract MRZ from image
            raw_mrz = self._extractor.extract(image_path)

            # Step 2: Validate MRZ check digits
            validation_result = self._validator.validate(raw_mrz.raw_text)

            # Step 3: Convert to PassportData
            passport_data = self._convert_to_passport_data(
                raw_mrz=raw_mrz,
                validation_result=validation_result,
                source_file=image_path,
            )

            return ExtractionResult(
                success=True,
                data=passport_data,
                error=None,
                source_file=image_path,
            )

        except PassportExtractionError as e:
            # Known extraction errors - return user-friendly message
            return ExtractionResult(
                success=False,
                data=None,
                error=str(e),
                source_file=image_path,
            )
        except Exception as e:
            # Unexpected errors - still return user-friendly message
            return ExtractionResult(
                success=False,
                data=None,
                error=f"Extraction failed: {e}",
                source_file=image_path,
            )

    def extract_batch(
        self,
        directory: Path,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> list[ExtractionResult]:
        """Extract passport data from all images in a directory.

        Processes all supported image files, continuing on individual
        file errors and collecting all results.

        Args:
            directory: Path to directory containing passport images.
            on_progress: Optional callback for progress updates (current, total).

        Returns:
            List of ExtractionResult objects, one per image processed.
        """
        # Find all supported image files
        image_files = self._find_supported_images(directory)

        if not image_files:
            return []

        results: list[ExtractionResult] = []
        total = len(image_files)

        for current, image_path in enumerate(image_files, start=1):
            # Process each image
            result = self.extract_single(image_path)
            results.append(result)

            # Call progress callback if provided
            if on_progress is not None:
                on_progress(current, total)

        return results

    def get_supported_extensions(self) -> set[str]:
        """Return set of supported image file extensions.

        Delegates to the extractor's SUPPORTED_EXTENSIONS.

        Returns:
            Set of file extensions (e.g., {'.jpg', '.png'}).
        """
        return self._extractor.SUPPORTED_EXTENSIONS

    def _find_supported_images(self, directory: Path) -> list[Path]:
        """Find all supported image files in a directory.

        Args:
            directory: Directory to scan.

        Returns:
            Sorted list of paths to supported image files.
        """
        image_files = []

        for path in directory.iterdir():
            if path.is_file() and self._extractor.is_supported_format(path):
                image_files.append(path)

        # Sort for consistent ordering
        return sorted(image_files)

    def _convert_to_passport_data(
        self,
        raw_mrz: RawMRZData,
        validation_result: ValidationResult,
        source_file: Path,
    ) -> PassportData:
        """Convert raw MRZ data to PassportData.

        Parses dates from YYMMDD format and assembles all fields.

        Args:
            raw_mrz: Raw extraction data from PassportEye.
            validation_result: Validation result from MRZValidator.
            source_file: Path to the source image.

        Returns:
            PassportData with all fields populated.
        """
        # Extract check digit error messages
        check_digit_errors = [
            cd.field_name
            for cd in validation_result.check_digits
            if not cd.is_valid
        ]

        return PassportData(
            source_file=source_file,
            surname=raw_mrz.surname,
            given_names=raw_mrz.given_names,
            date_of_birth=self._parse_mrz_date(raw_mrz.birth_date),
            nationality=raw_mrz.nationality,
            passport_number=raw_mrz.document_number,
            expiry_date=self._parse_mrz_date(raw_mrz.expiry_date, is_expiry=True),
            sex=self._normalize_sex(raw_mrz.sex),
            place_of_birth=None,  # Not available in MRZ
            mrz_type=raw_mrz.mrz_type,
            mrz_valid=validation_result.is_valid,
            check_digit_errors=check_digit_errors,
            confidence=raw_mrz.confidence,
            raw_mrz=raw_mrz.raw_text,
        )

    def _parse_mrz_date(
        self,
        date_str: str | None,
        is_expiry: bool = False,
    ) -> date | None:
        """Parse MRZ date from YYMMDD format to Python date.

        Handles century crossover:
        - Birth dates: 00-99 maps to 1900-1999 or 2000-2099
        - Expiry dates: generally in the future, so 00-99 maps differently

        Args:
            date_str: Date string in YYMMDD format, or None.
            is_expiry: If True, treat as expiry date (likely future).

        Returns:
            Python date object, or None if parsing fails.
        """
        if date_str is None or len(date_str) != 6:
            return None

        try:
            year_2d = int(date_str[0:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])

            # Determine century
            # For birth dates: assume 1900s for 50-99, 2000s for 00-49
            # For expiry dates: assume 2000s for most, but handle edge cases
            if is_expiry:
                # Expiry dates are typically in the near future
                # Use 2000s for all (passports expire within ~10 years)
                year = 2000 + year_2d
            else:
                # Birth dates: people born 50+ years ago are common
                # 00-29 -> 2000-2029 (young people)
                # 30-99 -> 1930-1999 (older people)
                if year_2d >= 30:
                    year = 1900 + year_2d
                else:
                    year = 2000 + year_2d

            return date(year, month, day)

        except (ValueError, TypeError):
            # Invalid date components
            return None

    def _normalize_sex(self, sex: str | None) -> str | None:
        """Normalize sex field from MRZ format.

        MRZ uses 'M', 'F', or '<' (unspecified).

        Args:
            sex: Sex value from MRZ.

        Returns:
            'M', 'F', or None.
        """
        if sex is None:
            return None
        sex = sex.upper()
        if sex in ("M", "F"):
            return sex
        return None  # '<' or invalid values become None
