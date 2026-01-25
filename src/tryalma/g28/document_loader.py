"""Document loading service for G-28 form processing.

Task 3: Document Loading implementation.
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from io import BytesIO
from pathlib import Path

from pdf2image import convert_from_bytes, convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from PIL import Image

from tryalma.g28.exceptions import DocumentLoadError, UnsupportedFormatError


class DocumentLoader:
    """Loads documents and converts to images for extraction.

    Supports PDF and image files (PNG, JPG, JPEG, TIFF).
    Validates file format using both extension and magic bytes for security.
    """

    SUPPORTED_FORMATS: frozenset[str] = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".tiff"})
    MAX_PAGES: int = 4

    # Magic bytes signatures for supported formats
    MAGIC_BYTES = {
        ".pdf": (b"%PDF",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".tiff": (b"II\x2a\x00", b"MM\x00\x2a"),  # Little and big endian
    }

    def validate_format(self, file_path: Path) -> None:
        """Validate file format is supported based on extension.

        Args:
            file_path: Path to document file

        Raises:
            UnsupportedFormatError: Format not in SUPPORTED_FORMATS
        """
        extension = file_path.suffix.lower()
        if extension not in self.SUPPORTED_FORMATS:
            supported_list = ", ".join(sorted(fmt.upper().lstrip(".") for fmt in self.SUPPORTED_FORMATS))
            raise UnsupportedFormatError(
                f"Unsupported file format '{extension}'. Supported formats: {supported_list}"
            )

    def validate_format_from_filename(self, filename: str) -> None:
        """Validate file format from filename string (for web uploads).

        Args:
            filename: Original filename for format detection

        Raises:
            UnsupportedFormatError: Format not in SUPPORTED_FORMATS
        """
        self.validate_format(Path(filename))

    def validate_magic_bytes(self, file_path: Path) -> None:
        """Validate file content matches expected format using magic bytes.

        Security measure to prevent malicious file upload attacks.

        Args:
            file_path: Path to document file

        Raises:
            UnsupportedFormatError: File content doesn't match extension
        """
        extension = file_path.suffix.lower()
        if extension not in self.MAGIC_BYTES:
            return  # Skip validation for formats without known magic bytes

        expected_signatures = self.MAGIC_BYTES[extension]

        try:
            with open(file_path, "rb") as f:
                header = f.read(16)  # Read enough bytes for any signature
        except OSError as e:
            raise DocumentLoadError(f"Failed to read file: {e}")

        if not any(header.startswith(sig) for sig in expected_signatures):
            raise UnsupportedFormatError(
                f"File content doesn't match {extension} format. "
                f"Magic bytes validation failed - file may be corrupted or mislabeled."
            )

    def validate_magic_bytes_from_data(self, data: bytes, filename: str) -> None:
        """Validate raw bytes match expected format based on filename.

        Args:
            data: Raw file bytes
            filename: Original filename for format detection

        Raises:
            UnsupportedFormatError: File content doesn't match extension
        """
        extension = Path(filename).suffix.lower()
        if extension not in self.MAGIC_BYTES:
            return  # Skip validation for formats without known magic bytes

        expected_signatures = self.MAGIC_BYTES[extension]

        if not any(data.startswith(sig) for sig in expected_signatures):
            raise UnsupportedFormatError(
                f"File content doesn't match {extension} format. "
                f"Magic bytes validation failed - file may be corrupted or mislabeled."
            )

    def convert_pdf_to_images(self, file_path: Path) -> list[Image.Image]:
        """Convert PDF pages to PIL Image objects using pdf2image.

        Task 3.2: Implement PDF to image conversion.
        Requirements: 1.1, 1.5

        Args:
            file_path: Path to PDF file

        Returns:
            List of PIL Image objects in RGB mode, one per page (max MAX_PAGES)

        Raises:
            DocumentLoadError: Failed to convert PDF
        """
        try:
            # Convert with page limit enforcement
            images = convert_from_path(
                file_path,
                last_page=self.MAX_PAGES,
                fmt="RGB",
            )
        except (PDFPageCountError, PDFSyntaxError) as e:
            raise DocumentLoadError(f"Failed to convert PDF: {e}")
        except Exception as e:
            raise DocumentLoadError(f"Failed to convert PDF: {e}")

        # Ensure all images are in RGB mode
        rgb_images = []
        for img in images:
            if img.mode != "RGB":
                img = img.convert("RGB")
            rgb_images.append(img)

        return rgb_images

    def convert_pdf_bytes_to_images(self, data: bytes) -> list[Image.Image]:
        """Convert PDF bytes to PIL Image objects.

        Task 3.2: Implement PDF to image conversion for Flask integration.
        Requirements: 1.1, 1.5

        Args:
            data: Raw PDF bytes

        Returns:
            List of PIL Image objects in RGB mode, one per page (max MAX_PAGES)

        Raises:
            DocumentLoadError: Failed to convert PDF
        """
        try:
            images = convert_from_bytes(
                data,
                last_page=self.MAX_PAGES,
                fmt="RGB",
            )
        except (PDFPageCountError, PDFSyntaxError) as e:
            raise DocumentLoadError(f"Failed to convert PDF bytes: {e}")
        except Exception as e:
            raise DocumentLoadError(f"Failed to convert PDF bytes: {e}")

        # Ensure all images are in RGB mode
        rgb_images = []
        for img in images:
            if img.mode != "RGB":
                img = img.convert("RGB")
            rgb_images.append(img)

        return rgb_images

    def load_image(self, file_path: Path) -> list[Image.Image]:
        """Load PNG, JPG, JPEG, TIFF images using Pillow.

        Task 3.3: Implement image file loading.
        Requirements: 1.2, 1.4

        Args:
            file_path: Path to image file

        Returns:
            List containing single PIL Image in RGB mode

        Raises:
            DocumentLoadError: Failed to load or decode image
        """
        try:
            img = Image.open(file_path)
            # Force load to catch deferred decoding errors
            img.load()
        except Exception as e:
            raise DocumentLoadError(f"Failed to load image: {e}")

        # Normalize to RGB mode
        if img.mode != "RGB":
            img = img.convert("RGB")

        return [img]

    def load_image_bytes(self, data: bytes, filename: str) -> list[Image.Image]:
        """Load image from raw bytes.

        Task 3.3: Implement image file loading for Flask integration.
        Requirements: 1.2, 1.4

        Args:
            data: Raw image bytes
            filename: Original filename (for error messages)

        Returns:
            List containing single PIL Image in RGB mode

        Raises:
            DocumentLoadError: Failed to load or decode image
        """
        try:
            img = Image.open(BytesIO(data))
            # Force load to catch deferred decoding errors
            img.load()
        except Exception as e:
            raise DocumentLoadError(f"Failed to load image from bytes: {e}")

        # Normalize to RGB mode
        if img.mode != "RGB":
            img = img.convert("RGB")

        return [img]

    def _is_pdf(self, extension: str) -> bool:
        """Check if extension indicates a PDF file."""
        return extension.lower() == ".pdf"

    def load(self, file_path: Path) -> list[Image.Image]:
        """Load document from file path and return list of page images.

        Task 3.4: Assemble DocumentLoader service.
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5

        Args:
            file_path: Path to document file

        Returns:
            List of PIL Image objects, one per page

        Raises:
            FileNotFoundError: File does not exist
            UnsupportedFormatError: File format not supported
            DocumentLoadError: Failed to read or convert file
        """
        # Check file existence
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate extension
        self.validate_format(file_path)

        # Validate magic bytes for security
        self.validate_magic_bytes(file_path)

        # Route to appropriate loader
        extension = file_path.suffix.lower()
        if self._is_pdf(extension):
            return self.convert_pdf_to_images(file_path)
        else:
            return self.load_image(file_path)

    def load_bytes(self, data: bytes, filename: str) -> list[Image.Image]:
        """Load document from in-memory bytes (Flask/web upload support).

        Task 3.4: Assemble DocumentLoader service.
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5

        Args:
            data: Raw file bytes
            filename: Original filename for format detection

        Returns:
            List of PIL Image objects, one per page

        Raises:
            UnsupportedFormatError: File format not supported
            DocumentLoadError: Failed to read or convert bytes
        """
        # Validate extension
        self.validate_format_from_filename(filename)

        # Validate magic bytes for security
        self.validate_magic_bytes_from_data(data, filename)

        # Route to appropriate loader
        extension = Path(filename).suffix.lower()
        if self._is_pdf(extension):
            return self.convert_pdf_bytes_to_images(data)
        else:
            return self.load_image_bytes(data, filename)
