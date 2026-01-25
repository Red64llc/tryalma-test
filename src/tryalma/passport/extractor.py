"""MRZ extractor using PassportEye.

Task 3.1, 3.2: MRZExtractor class that wraps PassportEye for MRZ extraction,
including Tesseract dependency detection.

Requirements: 1.5, 2.1-2.8, 5.3, 6.1
"""

from pathlib import Path

from passporteye import read_mrz

from tryalma.passport.exceptions import (
    ImageReadError,
    MRZNotFoundError,
    TesseractNotFoundError,
    UnsupportedFormatError,
)
from tryalma.passport.models import RawMRZData
from tryalma.passport.utils import (
    check_tesseract_installed,
    get_tesseract_install_instructions,
)


class MRZExtractor:
    """Extracts MRZ data from passport images using PassportEye.

    Wraps the PassportEye library to provide a clean interface for MRZ
    extraction with proper error handling.

    Attributes:
        SUPPORTED_EXTENSIONS: Set of supported image file extensions.
    """

    SUPPORTED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

    def is_supported_format(self, path: Path) -> bool:
        """Check if the file has a supported image format.

        Args:
            path: Path to the file to check.

        Returns:
            True if the file extension is supported, False otherwise.
        """
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    @staticmethod
    def check_tesseract_installed() -> bool:
        """Verify Tesseract OCR is installed and accessible.

        Returns:
            True if Tesseract is found in the system PATH, False otherwise.
        """
        return check_tesseract_installed()

    @staticmethod
    def get_tesseract_install_instructions() -> str:
        """Return platform-specific Tesseract installation instructions.

        Returns:
            A string containing installation instructions for the current platform.
        """
        return get_tesseract_install_instructions()

    def extract(self, image_path: Path) -> RawMRZData:
        """Extract MRZ data from a passport image.

        Args:
            image_path: Path to the passport image file.

        Returns:
            RawMRZData containing extracted MRZ fields.

        Raises:
            UnsupportedFormatError: If the image format is not supported.
            MRZNotFoundError: If no MRZ is detected in the image.
            TesseractNotFoundError: If Tesseract OCR is not installed.
            ImageReadError: If the image cannot be read or is corrupted.
        """
        # Validate file format
        if not self.is_supported_format(image_path):
            raise UnsupportedFormatError(
                f"Unsupported image format: {image_path.suffix}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        try:
            # Call PassportEye to extract MRZ
            mrz_result = read_mrz(str(image_path))
        except Exception as e:
            error_msg = str(e).lower()
            # Check if the error is Tesseract-related
            if "tesseract" in error_msg:
                if not check_tesseract_installed():
                    raise TesseractNotFoundError()
            # Otherwise treat as image read error
            raise ImageReadError(f"Could not read image file: {image_path.name}. {e}")

        # Check if MRZ was found
        if mrz_result is None:
            raise MRZNotFoundError(
                f"No Machine Readable Zone (MRZ) detected in image: {image_path.name}"
            )

        # Extract raw MRZ text from aux attribute if available
        raw_text = ""
        if hasattr(mrz_result, "aux") and mrz_result.aux is not None:
            if hasattr(mrz_result.aux, "text"):
                raw_text = mrz_result.aux.text

        # Convert empty strings to None for optional fields
        def to_optional(value: str | None) -> str | None:
            if value is None or value == "":
                return None
            return value

        # Build RawMRZData from PassportEye result
        return RawMRZData(
            mrz_type=mrz_result.mrz_type,
            raw_text=raw_text,
            surname=to_optional(mrz_result.surname),
            given_names=to_optional(mrz_result.names),
            country=to_optional(mrz_result.country),
            nationality=to_optional(mrz_result.nationality),
            birth_date=to_optional(mrz_result.date_of_birth),
            sex=to_optional(mrz_result.sex),
            expiry_date=to_optional(mrz_result.expiration_date),
            document_number=to_optional(mrz_result.number),
            optional_data=to_optional(mrz_result.personal_number),
            confidence=mrz_result.valid_score if hasattr(mrz_result, "valid_score") else None,
        )
