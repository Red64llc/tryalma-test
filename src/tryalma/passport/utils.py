"""Utility functions for passport extraction.

Contains Tesseract OCR dependency detection and installation guidance.
Requirements: 5.3 (missing dependency instructions)
"""

import platform
import shutil


def check_tesseract_installed() -> bool:
    """Check if Tesseract OCR is installed and accessible.

    Returns:
        True if Tesseract is found in the system PATH, False otherwise.
    """
    return shutil.which("tesseract") is not None


def get_tesseract_install_instructions() -> str:
    """Get platform-specific Tesseract installation instructions.

    Returns:
        A string containing installation instructions for the current platform.
    """
    system = platform.system().lower()

    instructions = "Tesseract OCR is required for passport MRZ extraction.\n\n"

    if system == "darwin":  # macOS
        instructions += "Install on macOS using Homebrew:\n"
        instructions += "  brew install tesseract\n"
    elif system == "linux":
        instructions += "Install on Linux (Debian/Ubuntu):\n"
        instructions += "  sudo apt-get install tesseract-ocr\n\n"
        instructions += "Install on Linux (Fedora/RHEL):\n"
        instructions += "  sudo dnf install tesseract\n"
    elif system == "windows":
        instructions += "Install on Windows:\n"
        instructions += "  1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki\n"
        instructions += "  2. Run the installer and follow the prompts\n"
        instructions += "  3. Add Tesseract to your PATH environment variable\n"
    else:
        instructions += "Please install Tesseract OCR for your platform.\n"
        instructions += "Visit: https://github.com/tesseract-ocr/tesseract\n"

    instructions += "\nVerify installation by running: tesseract --version"

    return instructions
