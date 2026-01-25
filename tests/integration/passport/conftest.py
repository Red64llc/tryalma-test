"""Test fixtures for passport CLI integration tests."""

from pathlib import Path

import pytest
from PIL import Image


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
