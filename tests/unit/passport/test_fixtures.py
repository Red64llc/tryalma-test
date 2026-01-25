"""Tests for passport extraction test fixtures.

Task 1: Set up project dependencies and configuration.
Verifies that pytest fixtures for passport extraction testing are available.
"""

import pytest
from pathlib import Path


class TestPassportFixturesAvailable:
    """Verify passport-specific fixtures are defined and work correctly."""

    def test_sample_mrz_td3_data_fixture(self, sample_mrz_td3_data):
        """sample_mrz_td3_data fixture should provide valid TD3 MRZ string."""
        # TD3 format: 2 lines of 44 characters each
        assert isinstance(sample_mrz_td3_data, str)
        lines = sample_mrz_td3_data.strip().split("\n")
        assert len(lines) == 2, "TD3 MRZ should have exactly 2 lines"
        assert all(
            len(line) == 44 for line in lines
        ), "Each TD3 MRZ line should be 44 characters"

    def test_sample_mrz_td1_data_fixture(self, sample_mrz_td1_data):
        """sample_mrz_td1_data fixture should provide valid TD1 MRZ string."""
        # TD1 format: 3 lines of 30 characters each
        assert isinstance(sample_mrz_td1_data, str)
        lines = sample_mrz_td1_data.strip().split("\n")
        assert len(lines) == 3, "TD1 MRZ should have exactly 3 lines"
        assert all(
            len(line) == 30 for line in lines
        ), "Each TD1 MRZ line should be 30 characters"

    def test_sample_passport_data_fixture(self, sample_passport_data):
        """sample_passport_data fixture should provide mock passport field data."""
        assert isinstance(sample_passport_data, dict)
        # Required fields per design.md
        required_fields = [
            "surname",
            "given_names",
            "date_of_birth",
            "nationality",
            "passport_number",
            "expiry_date",
            "sex",
        ]
        for field in required_fields:
            assert field in sample_passport_data, f"Missing required field: {field}"

    def test_mock_passporteye_result_fixture(self, mock_passporteye_result):
        """mock_passporteye_result fixture should mimic PassportEye output."""
        # Should have the structure returned by passporteye.read_mrz()
        assert mock_passporteye_result is not None
        # PassportEye returns an MRZ object directly with these attributes
        required_attrs = ["mrz_type", "surname", "names", "number", "date_of_birth", "sex"]
        for attr in required_attrs:
            assert hasattr(mock_passporteye_result, attr), f"Missing attribute: {attr}"

    def test_temp_passport_image_fixture(self, temp_passport_image):
        """temp_passport_image fixture should create a temporary image file."""
        assert isinstance(temp_passport_image, Path)
        assert temp_passport_image.exists()
        assert temp_passport_image.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
