"""Passport extraction test fixtures.

Task 1: Set up project dependencies and configuration.
Provides pytest fixtures for passport extraction testing (sample images, mock data).
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def sample_mrz_td3_data() -> str:
    """Provide a sample TD3 MRZ string (passport format).

    TD3 format: 2 lines of 44 characters each.
    This is a valid test MRZ that follows ICAO 9303 format.
    """
    # Sample TD3 MRZ (passport)
    # Line 1: Type, Country, Surname, Given Names (44 chars)
    # Line 2: Passport number, Nationality, DOB, Sex, Expiry, Optional (44 chars)
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    return f"{line1}\n{line2}"


@pytest.fixture
def sample_mrz_td1_data() -> str:
    """Provide a sample TD1 MRZ string (ID card format).

    TD1 format: 3 lines of 30 characters each.
    This is a valid test MRZ that follows ICAO 9303 format.
    """
    # Sample TD1 MRZ (ID card)
    # Line 1: Type, Country, Document number (30 chars)
    # Line 2: DOB, Sex, Expiry, Nationality, Optional (30 chars)
    # Line 3: Surname, Given Names (30 chars)
    line1 = "I<UTOD231458907<<<<<<<<<<<<<<<"
    line2 = "7408122F1204159UTO<<<<<<<<<<<6"
    line3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<"
    return f"{line1}\n{line2}\n{line3}"


@pytest.fixture
def sample_passport_data() -> dict:
    """Provide mock passport field data for testing.

    Returns a dictionary with all expected passport fields per design.md.
    """
    return {
        "surname": "ERIKSSON",
        "given_names": "ANNA MARIA",
        "date_of_birth": date(1974, 8, 12),
        "nationality": "UTO",
        "passport_number": "L898902C3",
        "expiry_date": date(2012, 4, 15),
        "sex": "F",
        "place_of_birth": None,  # Optional field
        "mrz_type": "TD3",
        "mrz_valid": True,
        "check_digit_errors": [],
        "confidence": 0.95,
    }


@dataclass
class MockMRZResult:
    """Mock object mimicking PassportEye MRZ result structure."""

    mrz_type: str
    valid: bool
    valid_score: float
    country: str
    nationality: str
    surname: str
    names: str
    number: str
    date_of_birth: str
    sex: str
    expiration_date: str
    personal_number: str
    optional1: str
    optional2: str


@pytest.fixture
def mock_passporteye_result() -> MockMRZResult:
    """Provide a mock object mimicking PassportEye's read_mrz() output.

    PassportEye returns an MRZ object with various attributes.
    This fixture mimics that structure for unit testing without OCR.
    """
    return MockMRZResult(
        mrz_type="TD3",
        valid=True,
        valid_score=1.0,
        country="UTO",
        nationality="UTO",
        surname="ERIKSSON",
        names="ANNA MARIA",
        number="L898902C3",
        date_of_birth="740812",  # YYMMDD format
        sex="F",
        expiration_date="120415",  # YYMMDD format
        personal_number="ZE184226B",
        optional1="",
        optional2="",
    )


@pytest.fixture
def temp_passport_image(tmp_path: Path) -> Path:
    """Create a temporary test image file.

    Creates a minimal JPEG image in a temporary directory for testing
    image handling without requiring actual passport images.
    """
    image_path = tmp_path / "test_passport.jpg"

    # Create a minimal test image (100x100 white image)
    img = Image.new("RGB", (100, 100), color="white")
    img.save(image_path, "JPEG")

    return image_path


@pytest.fixture
def temp_passport_images_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with multiple test images.

    Useful for testing batch processing functionality.
    """
    images_dir = tmp_path / "passports"
    images_dir.mkdir()

    # Create several test images with different formats
    for i, ext in enumerate(["jpg", "png", "tiff"]):
        image_path = images_dir / f"passport_{i}.{ext}"
        img = Image.new("RGB", (100, 100), color="white")

        if ext == "tiff":
            img.save(image_path, "TIFF")
        else:
            img.save(image_path)

    return images_dir


@pytest.fixture
def invalid_image_file(tmp_path: Path) -> Path:
    """Create an invalid/corrupted image file for error handling tests."""
    invalid_path = tmp_path / "corrupted.jpg"
    invalid_path.write_bytes(b"not a valid image content")
    return invalid_path
