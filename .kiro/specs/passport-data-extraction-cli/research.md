# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: `passport-data-extraction-cli`
- **Discovery Scope**: New Feature
- **Key Findings**:
  - PassportEye 2.2.2 provides robust MRZ extraction with ~80% accuracy for clear images
  - The `mrz` library (0.6.2) offers comprehensive ICAO 9303 compliant validation for TD1/TD3 formats
  - Tesseract OCR is the underlying engine, requiring system installation
  - Existing project structure supports Typer CLI patterns with clear separation of concerns

## Research Log

### MRZ Extraction Libraries Evaluation

- **Context**: Need to identify the best Python library for extracting Machine Readable Zone (MRZ) data from passport images.
- **Sources Consulted**:
  - [PassportEye PyPI](https://pypi.org/project/PassportEye/)
  - [PassportEye GitHub](https://github.com/konstantint/PassportEye)
  - [passport-mrz-extractor PyPI](https://pypi.org/project/passport-mrz-extractor/)
  - [FastMRZ GitHub](https://github.com/sivakumar-mahalingam/fastmrz)
- **Findings**:
  - PassportEye 2.2.2 (March 2025): Most mature, MIT licensed, ~80% accuracy, 10+ seconds processing
  - passport-mrz-extractor 1.0.13: Newer, uses mrz library for validation, requires Python >= 3.10
  - FastMRZ: Good for multiple input formats (Base64, NumPy arrays), ICAO 9303 compliant
  - All libraries depend on Tesseract OCR as the underlying engine
- **Implications**: PassportEye selected as primary extraction engine due to maturity, documentation, and MIT license compatibility. The `mrz` library will be used for additional validation.

### MRZ Validation and ICAO 9303 Compliance

- **Context**: Requirement 6 specifies MRZ check digit validation according to ICAO 9303 standards.
- **Sources Consulted**:
  - [mrz PyPI](https://pypi.org/project/mrz/)
  - [mrz GitHub](https://github.com/Arg0s1080/mrz)
  - [ICAO 9303 MRZ Validator](https://mrzcode.org/en/mrz-validator)
- **Findings**:
  - `mrz` library 0.6.2 provides TD1CodeChecker, TD3CodeChecker for validation
  - Supports check_expiry and compute_warnings parameters
  - Full ICAO 9303 compliance for TD1, TD2, TD3, MRVA, MRVB formats
  - Check digit validation built-in for document number, birth date, expiry date, and composite
  - Python 3.4+ compatible (compatible with project's 3.12 requirement)
- **Implications**: Use `mrz` library's checker classes for validation after PassportEye extraction. This provides an additional validation layer and detailed field parsing.

### Tesseract OCR Dependency

- **Context**: All MRZ extraction libraries depend on Tesseract OCR.
- **Sources Consulted**:
  - [Tesseract OCR Guide](https://unstract.com/blog/guide-to-optical-character-recognition-with-tesseract-ocr/)
  - [PyImageSearch Passport OCR](https://pyimagesearch.com/2021/12/01/ocr-passports-with-opencv-and-tesseract/)
- **Findings**:
  - Tesseract must be installed at system level (not pip installable)
  - Installation varies by platform: `brew install tesseract` (macOS), `apt-get install tesseract-ocr` (Linux)
  - Legacy Tesseract model performs better for MRZ text detection
  - Processing time approximately 10+ seconds per document
- **Implications**: Document Tesseract as a prerequisite. CLI should detect missing Tesseract and provide helpful installation instructions (Requirement 5.3).

### Image Format Support

- **Context**: Requirement 1.5 specifies support for JPEG, PNG, and TIFF formats.
- **Sources Consulted**:
  - [Pillow Image File Formats](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
- **Findings**:
  - Pillow 12.1.0 (already in project) supports JPEG, PNG, and TIFF with full read/write
  - PassportEye accepts file path or byte stream, compatible with Pillow's image handling
  - File extensions to support: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`
- **Implications**: Use Pillow for image validation and format detection. PassportEye handles the actual OCR processing.

### Existing Project Structure Analysis

- **Context**: Understand current codebase patterns for integration.
- **Sources Consulted**: Local codebase analysis
- **Findings**:
  - Project uses Typer for CLI (`src/tryalma/cli.py`)
  - Exception hierarchy exists in `src/tryalma/exceptions.py` with CLIError, ValidationError, ProcessingError
  - Exit codes defined: 0 (success), 1 (general), 2 (validation), 3 (processing)
  - Core business logic separated in `src/tryalma/core.py`
  - Python 3.12+ required, UV for package management
  - Pillow and OpenCV already installed as dependencies
- **Implications**: Follow existing patterns. Extend exception hierarchy for passport-specific errors. Add new CLI command for passport extraction.

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Ports & Adapters | Core extraction logic with adapters for OCR engines | Testable core, swappable OCR | Slight overhead for simple CLI | Aligns with existing cli.py/core.py separation |
| Simple Layered | CLI -> Service -> OCR Library | Simple, direct | Harder to test, tight coupling | Quick implementation |
| Plugin Architecture | Extensible OCR backends | Future-proof, modular | Over-engineered for current scope | Not needed for single OCR engine |

**Selected**: Ports & Adapters (simplified) - Matches existing project patterns with CLI layer calling core extraction service.

## Design Decisions

### Decision: Primary OCR Library Selection

- **Context**: Multiple Python libraries available for passport MRZ extraction
- **Alternatives Considered**:
  1. PassportEye - Mature, well-documented, MIT license, ~80% accuracy
  2. passport-mrz-extractor - Newer, uses mrz library internally
  3. FastMRZ - Good multi-format support, less documentation
  4. Custom Tesseract + OpenCV - Full control, high development effort
- **Selected Approach**: PassportEye as primary extraction engine with mrz library for validation
- **Rationale**:
  - PassportEye is the most mature and documented option
  - MIT license compatible with project
  - Already handles image preprocessing and MRZ detection
  - mrz library provides additional validation layer for ICAO compliance
- **Trade-offs**:
  - Benefits: Fast integration, proven accuracy, good documentation
  - Compromises: ~10 second processing time, ~80% accuracy requires error handling
- **Follow-up**: Monitor PassportEye releases for accuracy improvements

### Decision: Output Format Implementation

- **Context**: Requirements 4.1-4.4 specify multiple output formats (table, JSON, CSV)
- **Alternatives Considered**:
  1. Rich library for table formatting
  2. Typer's built-in echo with manual formatting
  3. Tabulate library for tables
- **Selected Approach**: Use Rich for table display, stdlib json for JSON, csv module for CSV
- **Rationale**:
  - Rich provides beautiful table output with minimal code
  - Aligns with modern CLI UX expectations
  - JSON and CSV handled by Python stdlib (no additional dependencies)
- **Trade-offs**:
  - Benefits: Professional output, color support, progress indicators
  - Compromises: Additional dependency (Rich)
- **Follow-up**: Consider making Rich optional for minimal installations

### Decision: Extracted Data Model

- **Context**: Need consistent data structure for passport information across formats
- **Alternatives Considered**:
  1. Dictionary-based approach
  2. Dataclass with typed fields
  3. Pydantic model with validation
- **Selected Approach**: Dataclass with typed fields, converting to Pydantic for JSON serialization
- **Rationale**:
  - Dataclass provides type hints and IDE support
  - Easy conversion to dict for JSON/CSV output
  - Pydantic already available via FastAPI dependency
  - Strong typing aligns with project standards
- **Trade-offs**:
  - Benefits: Type safety, easy serialization, IDE support
  - Compromises: Slight overhead for simple use case
- **Follow-up**: None required

### Decision: Batch Processing Strategy

- **Context**: Requirement 1.2 requires processing directories of images
- **Alternatives Considered**:
  1. Sequential processing with progress bar
  2. Concurrent processing with ThreadPoolExecutor
  3. Async processing with asyncio
- **Selected Approach**: Sequential processing with Rich progress bar
- **Rationale**:
  - Tesseract OCR is CPU-bound, threading provides limited benefit
  - Sequential processing is simpler to implement and debug
  - Progress bar gives user feedback during long operations
  - Error handling per-file easier to implement (Requirement 5.1)
- **Trade-offs**:
  - Benefits: Simple, predictable, good error isolation
  - Compromises: Slower for large batches (but OCR is the bottleneck anyway)
- **Follow-up**: Consider optional parallel mode in future if user demand exists

## Risks & Mitigations

- **Tesseract Not Installed**: CLI detects missing dependency and shows platform-specific installation instructions
- **Low Quality Images**: Return partial results with confidence indicators; document best practices for input images
- **MRZ Not Detected**: Return structured error indicating no MRZ found; suggest image quality improvements
- **Check Digit Validation Fails**: Display extracted data with validation failure flag (per Requirement 6.3)
- **Large Batch Processing**: Show progress indicator; allow Ctrl+C graceful termination

## References

- [PassportEye Documentation](https://passporteye.readthedocs.io/en/latest/)
- [PassportEye PyPI](https://pypi.org/project/PassportEye/) - Version 2.2.2
- [mrz Library GitHub](https://github.com/Arg0s1080/mrz) - ICAO 9303 compliance
- [ICAO 9303 Standard](https://www.icao.int/publications/Documents/9303_p3_cons_en.pdf) - Machine Readable Travel Documents specification
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Underlying OCR engine
- [Pillow Documentation](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) - Image format support
- [Typer Documentation](https://typer.tiangolo.com/) - CLI framework
- [Rich Documentation](https://rich.readthedocs.io/) - Terminal formatting library
