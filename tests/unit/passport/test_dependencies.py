"""Tests for passport extraction dependencies and configuration.

Task 1: Set up project dependencies and configuration.
Requirements: 5.3 (missing dependency instructions)
"""

import pytest


class TestDependenciesAvailable:
    """Verify required libraries are installed and importable."""

    def test_passporteye_importable(self):
        """PassportEye 2.2.2 should be importable."""
        import passporteye

        # Verify we can access the main functionality
        assert hasattr(passporteye, "read_mrz")

    def test_mrz_library_importable(self):
        """mrz 0.6.2 library should be importable with TD1/TD3 checkers."""
        from mrz.checker import td1, td3

        # Verify TD1 and TD3 checkers are available
        assert hasattr(td1, "TD1CodeChecker")
        assert hasattr(td3, "TD3CodeChecker")

    def test_rich_library_importable(self):
        """Rich 13.0.0 should be importable for table formatting."""
        from rich.console import Console
        from rich.table import Table

        # Verify we can create basic rich objects
        console = Console()
        table = Table()
        assert console is not None
        assert table is not None


class TestTesseractDetection:
    """Tests for Tesseract OCR dependency detection."""

    def test_check_tesseract_installed_returns_bool(self):
        """check_tesseract_installed should return a boolean."""
        from tryalma.passport.utils import check_tesseract_installed

        result = check_tesseract_installed()
        assert isinstance(result, bool)

    def test_get_tesseract_install_instructions_returns_string(self):
        """get_tesseract_install_instructions should return installation guidance."""
        from tryalma.passport.utils import get_tesseract_install_instructions

        instructions = get_tesseract_install_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_get_tesseract_install_instructions_contains_platform_info(self):
        """Instructions should contain platform-specific guidance."""
        from tryalma.passport.utils import get_tesseract_install_instructions

        instructions = get_tesseract_install_instructions()
        # Should contain at least one platform instruction
        has_platform_info = any(
            keyword in instructions.lower()
            for keyword in ["brew", "apt", "windows", "macos", "linux", "install"]
        )
        assert has_platform_info, "Instructions should mention platform-specific install methods"

    def test_get_tesseract_install_instructions_macos(self, monkeypatch):
        """Instructions for macOS should mention Homebrew."""
        from tryalma.passport import utils

        monkeypatch.setattr("platform.system", lambda: "Darwin")
        instructions = utils.get_tesseract_install_instructions()
        assert "brew" in instructions.lower()
        assert "tesseract" in instructions.lower()

    def test_get_tesseract_install_instructions_linux(self, monkeypatch):
        """Instructions for Linux should mention apt or dnf."""
        from tryalma.passport import utils

        monkeypatch.setattr("platform.system", lambda: "Linux")
        instructions = utils.get_tesseract_install_instructions()
        assert "apt" in instructions.lower() or "dnf" in instructions.lower()
        assert "tesseract" in instructions.lower()

    def test_get_tesseract_install_instructions_windows(self, monkeypatch):
        """Instructions for Windows should mention installer download."""
        from tryalma.passport import utils

        monkeypatch.setattr("platform.system", lambda: "Windows")
        instructions = utils.get_tesseract_install_instructions()
        assert "download" in instructions.lower() or "installer" in instructions.lower()
        assert "path" in instructions.lower()

    def test_get_tesseract_install_instructions_unknown_platform(self, monkeypatch):
        """Instructions for unknown platform should provide generic guidance."""
        from tryalma.passport import utils

        monkeypatch.setattr("platform.system", lambda: "UnknownOS")
        instructions = utils.get_tesseract_install_instructions()
        assert "tesseract" in instructions.lower()
        assert "install" in instructions.lower()
