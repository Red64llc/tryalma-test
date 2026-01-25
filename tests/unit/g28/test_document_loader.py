"""Unit tests for G28 DocumentLoader service.

Task 3: Document Loading implementation tests using TDD methodology.
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from pathlib import Path

import pytest


class TestDocumentFormatValidation:
    """Test document format validation.

    Task 3.1: Implement document format validation
    Requirements: 1.3
    """

    def test_supported_formats_constant_includes_all_required_formats(self):
        """SUPPORTED_FORMATS constant includes PDF, PNG, JPG, JPEG, TIFF."""
        from tryalma.g28.document_loader import DocumentLoader

        expected_formats = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}

        assert expected_formats.issubset(DocumentLoader.SUPPORTED_FORMATS)

    def test_supported_formats_is_frozen_set(self):
        """SUPPORTED_FORMATS is immutable (frozenset)."""
        from tryalma.g28.document_loader import DocumentLoader

        assert isinstance(DocumentLoader.SUPPORTED_FORMATS, frozenset)

    def test_validate_format_accepts_pdf_extension(self):
        """validate_format accepts .pdf files."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise
        loader.validate_format(Path("document.pdf"))

    def test_validate_format_accepts_png_extension(self):
        """validate_format accepts .png files."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise
        loader.validate_format(Path("document.png"))

    def test_validate_format_accepts_jpg_extension(self):
        """validate_format accepts .jpg files."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise
        loader.validate_format(Path("document.jpg"))

    def test_validate_format_accepts_jpeg_extension(self):
        """validate_format accepts .jpeg files."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise
        loader.validate_format(Path("document.jpeg"))

    def test_validate_format_accepts_tiff_extension(self):
        """validate_format accepts .tiff files."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise
        loader.validate_format(Path("document.tiff"))

    def test_validate_format_case_insensitive(self):
        """validate_format is case insensitive for extensions."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise for uppercase extensions
        loader.validate_format(Path("document.PDF"))
        loader.validate_format(Path("document.PNG"))
        loader.validate_format(Path("document.JPG"))

    def test_validate_format_raises_unsupported_format_error_for_doc(self):
        """validate_format raises UnsupportedFormatError for .doc files."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError) as exc_info:
            loader.validate_format(Path("document.doc"))

        assert "supported" in str(exc_info.value).lower()

    def test_validate_format_raises_unsupported_format_error_for_txt(self):
        """validate_format raises UnsupportedFormatError for .txt files."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.validate_format(Path("document.txt"))

    def test_validate_format_raises_unsupported_format_error_for_docx(self):
        """validate_format raises UnsupportedFormatError for .docx files."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.validate_format(Path("document.docx"))

    def test_validate_format_from_filename_accepts_valid_extension(self):
        """validate_format_from_filename accepts valid format from filename string."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        # Should not raise
        loader.validate_format_from_filename("upload.pdf")
        loader.validate_format_from_filename("image.PNG")
        loader.validate_format_from_filename("scan.jpeg")

    def test_validate_format_from_filename_raises_for_invalid_extension(self):
        """validate_format_from_filename raises for invalid format."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.validate_format_from_filename("document.xls")


class TestMagicBytesValidation:
    """Test magic bytes validation for security.

    Task 3.1: Validate using magic bytes for security, not just extension
    Requirements: 1.3
    """

    def test_validate_magic_bytes_detects_pdf(self, tmp_path):
        """validate_magic_bytes detects PDF files by magic bytes."""
        from tryalma.g28.document_loader import DocumentLoader

        # PDF magic bytes: %PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        loader = DocumentLoader()
        # Should not raise
        loader.validate_magic_bytes(pdf_file)

    def test_validate_magic_bytes_detects_png(self, tmp_path):
        """validate_magic_bytes detects PNG files by magic bytes."""
        from tryalma.g28.document_loader import DocumentLoader

        # PNG magic bytes: \x89PNG\r\n\x1a\n
        png_file = tmp_path / "test.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"test content")

        loader = DocumentLoader()
        # Should not raise
        loader.validate_magic_bytes(png_file)

    def test_validate_magic_bytes_detects_jpeg(self, tmp_path):
        """validate_magic_bytes detects JPEG files by magic bytes."""
        from tryalma.g28.document_loader import DocumentLoader

        # JPEG magic bytes: \xff\xd8\xff
        jpeg_file = tmp_path / "test.jpg"
        jpeg_file.write_bytes(b"\xff\xd8\xff\xe0" + b"test content")

        loader = DocumentLoader()
        # Should not raise
        loader.validate_magic_bytes(jpeg_file)

    def test_validate_magic_bytes_detects_tiff_little_endian(self, tmp_path):
        """validate_magic_bytes detects TIFF files (little endian)."""
        from tryalma.g28.document_loader import DocumentLoader

        # TIFF little endian magic bytes: II\x2a\x00
        tiff_file = tmp_path / "test.tiff"
        tiff_file.write_bytes(b"II\x2a\x00" + b"test content")

        loader = DocumentLoader()
        # Should not raise
        loader.validate_magic_bytes(tiff_file)

    def test_validate_magic_bytes_detects_tiff_big_endian(self, tmp_path):
        """validate_magic_bytes detects TIFF files (big endian)."""
        from tryalma.g28.document_loader import DocumentLoader

        # TIFF big endian magic bytes: MM\x00\x2a
        tiff_file = tmp_path / "test.tiff"
        tiff_file.write_bytes(b"MM\x00\x2a" + b"test content")

        loader = DocumentLoader()
        # Should not raise
        loader.validate_magic_bytes(tiff_file)

    def test_validate_magic_bytes_raises_for_mismatched_extension(self, tmp_path):
        """validate_magic_bytes raises when extension doesn't match content."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        # File claims to be PDF but contains text
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"This is just text, not a PDF")

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError) as exc_info:
            loader.validate_magic_bytes(fake_pdf)

        assert "magic" in str(exc_info.value).lower() or "content" in str(exc_info.value).lower()

    def test_validate_magic_bytes_from_data_detects_pdf(self):
        """validate_magic_bytes_from_data detects PDF from raw bytes."""
        from tryalma.g28.document_loader import DocumentLoader

        pdf_data = b"%PDF-1.4 test content"

        loader = DocumentLoader()
        # Should not raise
        loader.validate_magic_bytes_from_data(pdf_data, "document.pdf")

    def test_validate_magic_bytes_from_data_raises_for_mismatch(self):
        """validate_magic_bytes_from_data raises for mismatched content."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        fake_data = b"This is not a PDF"

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.validate_magic_bytes_from_data(fake_data, "document.pdf")


class TestPdfToImageConversion:
    """Test PDF to image conversion.

    Task 3.2: Implement PDF to image conversion
    Requirements: 1.1, 1.5
    """

    def test_max_pages_constant_is_4(self):
        """MAX_PAGES constant is 4 for standard G-28 forms."""
        from tryalma.g28.document_loader import DocumentLoader

        assert DocumentLoader.MAX_PAGES == 4

    def test_convert_pdf_to_images_returns_list_of_images(self, sample_pdf_path):
        """convert_pdf_to_images returns a list of PIL Images."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.convert_pdf_to_images(sample_pdf_path)

        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, Image.Image) for img in images)

    def test_convert_pdf_to_images_returns_rgb_images(self, sample_pdf_path):
        """convert_pdf_to_images converts images to RGB mode."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.convert_pdf_to_images(sample_pdf_path)

        for img in images:
            assert img.mode == "RGB"

    def test_convert_pdf_to_images_enforces_max_page_limit(self, multi_page_pdf_path):
        """convert_pdf_to_images enforces maximum page limit."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.convert_pdf_to_images(multi_page_pdf_path)

        assert len(images) <= DocumentLoader.MAX_PAGES

    def test_convert_pdf_to_images_raises_document_load_error_on_failure(self, tmp_path):
        """convert_pdf_to_images raises DocumentLoadError on conversion failure."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import DocumentLoadError

        # Create a corrupted PDF-like file
        corrupted_pdf = tmp_path / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"%PDF-1.4 corrupted content that is not valid PDF")

        loader = DocumentLoader()

        with pytest.raises(DocumentLoadError):
            loader.convert_pdf_to_images(corrupted_pdf)

    def test_convert_pdf_bytes_to_images_returns_list_of_images(self, sample_pdf_bytes):
        """convert_pdf_bytes_to_images converts PDF bytes to images."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.convert_pdf_bytes_to_images(sample_pdf_bytes)

        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, Image.Image) for img in images)

    def test_convert_pdf_bytes_to_images_returns_rgb_images(self, sample_pdf_bytes):
        """convert_pdf_bytes_to_images converts images to RGB mode."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.convert_pdf_bytes_to_images(sample_pdf_bytes)

        for img in images:
            assert img.mode == "RGB"


@pytest.fixture
def sample_pdf_path():
    """Provide path to sample G-28 PDF for testing."""
    sample_path = Path(__file__).parent.parent.parent.parent / "docs" / "Example_G-28.pdf"
    if not sample_path.exists():
        pytest.skip("Sample G-28 PDF not found at docs/Example_G-28.pdf")
    return sample_path


@pytest.fixture
def sample_pdf_bytes(sample_pdf_path):
    """Provide sample G-28 PDF bytes for testing."""
    return sample_pdf_path.read_bytes()


@pytest.fixture
def multi_page_pdf_path(sample_pdf_path):
    """Provide path to multi-page PDF for testing.

    Uses the sample G-28 which has multiple pages.
    """
    return sample_pdf_path


class TestImageFileLoading:
    """Test image file loading.

    Task 3.3: Implement image file loading
    Requirements: 1.2, 1.4
    """

    def test_load_png_image_returns_list_with_one_image(self, tmp_path):
        """load_image returns a list with one PIL Image for PNG files."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create a test PNG image
        img = Image.new("RGB", (100, 100), color="white")
        png_path = tmp_path / "test.png"
        img.save(png_path, "PNG")

        loader = DocumentLoader()
        images = loader.load_image(png_path)

        assert isinstance(images, list)
        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    def test_load_jpg_image_returns_list_with_one_image(self, tmp_path):
        """load_image returns a list with one PIL Image for JPG files."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create a test JPG image
        img = Image.new("RGB", (100, 100), color="white")
        jpg_path = tmp_path / "test.jpg"
        img.save(jpg_path, "JPEG")

        loader = DocumentLoader()
        images = loader.load_image(jpg_path)

        assert isinstance(images, list)
        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    def test_load_jpeg_image_returns_list_with_one_image(self, tmp_path):
        """load_image returns a list with one PIL Image for JPEG files."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create a test JPEG image
        img = Image.new("RGB", (100, 100), color="white")
        jpeg_path = tmp_path / "test.jpeg"
        img.save(jpeg_path, "JPEG")

        loader = DocumentLoader()
        images = loader.load_image(jpeg_path)

        assert len(images) == 1

    def test_load_tiff_image_returns_list_with_one_image(self, tmp_path):
        """load_image returns a list with one PIL Image for TIFF files."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create a test TIFF image
        img = Image.new("RGB", (100, 100), color="white")
        tiff_path = tmp_path / "test.tiff"
        img.save(tiff_path, "TIFF")

        loader = DocumentLoader()
        images = loader.load_image(tiff_path)

        assert len(images) == 1

    def test_load_image_normalizes_to_rgb_mode(self, tmp_path):
        """load_image normalizes images to RGB mode."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create an RGBA image (has alpha channel)
        img = Image.new("RGBA", (100, 100), color=(255, 255, 255, 128))
        png_path = tmp_path / "test_rgba.png"
        img.save(png_path, "PNG")

        loader = DocumentLoader()
        images = loader.load_image(png_path)

        assert images[0].mode == "RGB"

    def test_load_image_normalizes_grayscale_to_rgb(self, tmp_path):
        """load_image normalizes grayscale images to RGB mode."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create a grayscale image
        img = Image.new("L", (100, 100), color=128)
        png_path = tmp_path / "test_gray.png"
        img.save(png_path, "PNG")

        loader = DocumentLoader()
        images = loader.load_image(png_path)

        assert images[0].mode == "RGB"

    def test_load_image_raises_document_load_error_for_corrupted_file(self, tmp_path):
        """load_image raises DocumentLoadError for corrupted image files."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import DocumentLoadError

        # Create a corrupted PNG file (PNG magic bytes but invalid content)
        corrupted_png = tmp_path / "corrupted.png"
        corrupted_png.write_bytes(b"\x89PNG\r\n\x1a\ncorrupted data here")

        loader = DocumentLoader()

        with pytest.raises(DocumentLoadError):
            loader.load_image(corrupted_png)

    def test_load_image_raises_document_load_error_for_unreadable_file(self, tmp_path):
        """load_image raises DocumentLoadError for files that cannot be opened."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import DocumentLoadError

        # Create an empty file that looks like an image
        empty_file = tmp_path / "empty.png"
        empty_file.write_bytes(b"")

        loader = DocumentLoader()

        with pytest.raises(DocumentLoadError):
            loader.load_image(empty_file)

    def test_load_image_bytes_returns_rgb_image(self):
        """load_image_bytes returns RGB image from raw bytes."""
        from io import BytesIO

        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create image bytes
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = BytesIO()
        img.save(buffer, "PNG")
        image_bytes = buffer.getvalue()

        loader = DocumentLoader()
        images = loader.load_image_bytes(image_bytes, "test.png")

        assert len(images) == 1
        assert images[0].mode == "RGB"

    def test_load_image_bytes_raises_for_corrupted_data(self):
        """load_image_bytes raises DocumentLoadError for corrupted data."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import DocumentLoadError

        corrupted_data = b"\x89PNG\r\n\x1a\ncorrupted data"

        loader = DocumentLoader()

        with pytest.raises(DocumentLoadError):
            loader.load_image_bytes(corrupted_data, "test.png")


class TestDocumentLoaderService:
    """Test DocumentLoader service orchestration.

    Task 3.4: Assemble DocumentLoader service
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """

    def test_load_checks_file_existence(self, tmp_path):
        """load() raises FileNotFoundError for non-existent files."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        nonexistent_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError):
            loader.load(nonexistent_file)

    def test_load_validates_format_before_processing(self, tmp_path):
        """load() validates format and raises UnsupportedFormatError for invalid formats."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        # Create a .doc file
        doc_file = tmp_path / "document.doc"
        doc_file.write_bytes(b"doc content")

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.load(doc_file)

    def test_load_routes_pdf_to_pdf_conversion(self, sample_pdf_path):
        """load() routes PDF files to PDF conversion."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.load(sample_pdf_path)

        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, Image.Image) for img in images)
        assert all(img.mode == "RGB" for img in images)

    def test_load_routes_png_to_image_loading(self, tmp_path):
        """load() routes PNG files to image loading."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        # Create a valid PNG
        img = Image.new("RGB", (100, 100), color="white")
        png_path = tmp_path / "test.png"
        img.save(png_path, "PNG")

        loader = DocumentLoader()
        images = loader.load(png_path)

        assert isinstance(images, list)
        assert len(images) == 1
        assert images[0].mode == "RGB"

    def test_load_routes_jpg_to_image_loading(self, tmp_path):
        """load() routes JPG files to image loading."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        img = Image.new("RGB", (100, 100), color="white")
        jpg_path = tmp_path / "test.jpg"
        img.save(jpg_path, "JPEG")

        loader = DocumentLoader()
        images = loader.load(jpg_path)

        assert len(images) == 1
        assert images[0].mode == "RGB"

    def test_load_returns_non_empty_list_on_success(self, sample_pdf_path):
        """load() returns non-empty list of images on success."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.load(sample_pdf_path)

        assert len(images) >= 1

    def test_load_bytes_validates_format_from_filename(self):
        """load_bytes() validates format based on filename."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        loader = DocumentLoader()
        fake_data = b"%PDF content here"

        with pytest.raises(UnsupportedFormatError):
            loader.load_bytes(fake_data, "document.doc")

    def test_load_bytes_routes_pdf_to_pdf_conversion(self, sample_pdf_bytes):
        """load_bytes() routes PDF bytes to PDF conversion."""
        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.load_bytes(sample_pdf_bytes, "test.pdf")

        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, Image.Image) for img in images)

    def test_load_bytes_routes_png_to_image_loading(self):
        """load_bytes() routes PNG bytes to image loading."""
        from io import BytesIO

        from PIL import Image

        from tryalma.g28.document_loader import DocumentLoader

        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, "PNG")
        png_bytes = buffer.getvalue()

        loader = DocumentLoader()
        images = loader.load_bytes(png_bytes, "test.png")

        assert len(images) == 1
        assert images[0].mode == "RGB"

    def test_load_bytes_returns_non_empty_list_on_success(self, sample_pdf_bytes):
        """load_bytes() returns non-empty list of images on success."""
        from tryalma.g28.document_loader import DocumentLoader

        loader = DocumentLoader()
        images = loader.load_bytes(sample_pdf_bytes, "test.pdf")

        assert len(images) >= 1

    def test_load_validates_magic_bytes_for_security(self, tmp_path):
        """load() validates magic bytes and raises for mismatched content."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        # Create a file with PDF extension but text content
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"This is just text, not a PDF")

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.load(fake_pdf)

    def test_load_bytes_validates_magic_bytes_for_security(self):
        """load_bytes() validates magic bytes and raises for mismatched content."""
        from tryalma.g28.document_loader import DocumentLoader
        from tryalma.g28.exceptions import UnsupportedFormatError

        fake_data = b"This is just text, not a PDF"

        loader = DocumentLoader()

        with pytest.raises(UnsupportedFormatError):
            loader.load_bytes(fake_data, "test.pdf")
