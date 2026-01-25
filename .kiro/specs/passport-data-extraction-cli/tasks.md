# Implementation Plan

## Task Overview

This implementation plan covers the passport data extraction CLI feature, which extracts structured data from passport images using OCR technology. Tasks follow a bottom-up approach: domain models first, then core extraction/validation, service orchestration, output formatting, and finally CLI integration.

---

## Tasks

- [x] 1. Set up project dependencies and configuration
  - Add PassportEye 2.2.2, mrz 0.6.2, and Rich 13.0.0 to project dependencies using UV
  - Configure Tesseract OCR system dependency detection and document installation requirements
  - Add pytest fixtures for passport extraction testing (sample images, mock data)
  - _Requirements: 5.3_

- [x] 2. Implement domain models and exception hierarchy
- [x] 2.1 (P) Create passport data structures
  - Define PassportData dataclass with all passport fields (surname, given_names, date_of_birth, nationality, passport_number, expiry_date, sex, place_of_birth)
  - Include MRZ metadata fields (mrz_type, mrz_valid, check_digit_errors, confidence, raw_mrz)
  - Implement to_dict method for serialization with verbose option
  - Implement get_unavailable_fields method to identify missing data
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.3_

- [x] 2.2 (P) Create extraction result and raw MRZ data structures
  - Define ExtractionResult dataclass with success flag, data, error message, and source file
  - Define RawMRZData dataclass for PassportEye output (mrz_type, raw_text, all extracted fields, confidence)
  - Define ValidationResult and CheckDigitResult dataclasses for MRZ validation outcomes
  - Define MRZType enum for TD1, TD2, TD3, MRVA, MRVB formats
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 2.3 (P) Create passport-specific exception classes
  - Define PassportExtractionError as base exception extending ProcessingError
  - Define MRZNotFoundError for images without detectable MRZ
  - Define UnsupportedFormatError for unsupported image formats
  - Define TesseractNotFoundError with platform-specific installation instructions
  - Define ImageReadError for corrupted or unreadable files
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 3. Implement MRZ extraction layer
- [x] 3.1 Implement MRZ extractor core functionality
  - Create MRZExtractor class that wraps PassportEye read_mrz function
  - Define supported image extensions constant (jpg, jpeg, png, tiff, tif)
  - Implement is_supported_format method to validate file extensions
  - Implement extract method that processes an image and returns RawMRZData
  - Handle PassportEye failures and translate to appropriate exceptions
  - _Requirements: 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 6.1_

- [x] 3.2 Implement Tesseract dependency detection
  - Implement check_tesseract_installed static method to verify OCR availability
  - Implement get_tesseract_install_instructions static method with platform detection
  - Provide macOS (brew), Linux (apt), and Windows installation guidance
  - _Requirements: 5.3_

- [x] 4. Implement MRZ validation layer
- [x] 4.1 Implement MRZ validator with ICAO 9303 compliance
  - Create MRZValidator class using mrz library checkers
  - Implement validate method that auto-detects MRZ type and validates check digits
  - Implement validate_td1 method for ID card format (3 lines, 30 chars each)
  - Implement validate_td3 method for passport format (2 lines, 44 chars each)
  - Return detailed ValidationResult with check digit status for each validated field
  - Handle validation failures gracefully and include warnings in result
  - _Requirements: 6.2, 6.3, 6.4_

- [ ] 5. Implement passport extraction service
- [ ] 5.1 Implement single image extraction workflow
  - Create PassportExtractionService class with dependency injection for extractor and validator
  - Implement extract_single method that orchestrates extraction and validation
  - Convert RawMRZData to PassportData with proper date parsing (YYMMDD to date objects)
  - Handle extraction failures and return ExtractionResult with error details
  - Ensure user-friendly error messages without exposing internals
  - _Requirements: 1.1, 5.1, 5.2_

- [ ] 5.2 Implement batch directory processing
  - Implement extract_batch method that processes all images in a directory
  - Scan directory for supported image formats using is_supported_format
  - Implement get_supported_extensions method
  - Support progress callback for CLI progress bar integration
  - Continue processing on individual file errors and collect all results
  - _Requirements: 1.2, 1.4, 5.1_

- [ ] 6. Implement output formatting
- [ ] 6.1 (P) Implement table output formatter
  - Create OutputFormatter class with format method dispatching to specific formatters
  - Implement format_table method using Rich library for human-readable display
  - Support single and batch result display with clear separation between records
  - Include confidence scores and additional details when verbose mode enabled
  - Handle empty results gracefully
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1_

- [ ] 6.2 (P) Implement JSON and CSV output formatters
  - Implement format_json method producing valid JSON with results array and summary
  - Implement format_csv method with proper headers and row formatting
  - Include unavailable_fields in JSON output
  - Support verbose mode for additional metadata in both formats
  - _Requirements: 4.2, 4.3_

- [ ] 7. Implement CLI command and integration
- [ ] 7.1 Implement passport extract command
  - Create passport command module following project CLI patterns
  - Define extract command with path argument (file or directory)
  - Add format option (table/json/csv) with table as default
  - Add output option for file writing
  - Add verbose option for detailed output
  - Register command with existing Typer app
  - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3_

- [ ] 7.2 Implement CLI input validation and error handling
  - Validate path existence and type (file vs directory)
  - Display appropriate error for invalid paths with exit code 2
  - Display informational message when directory contains no supported images
  - Check Tesseract availability at startup and show installation instructions if missing
  - Map exception types to appropriate exit codes (0, 1, 2, 3)
  - _Requirements: 1.3, 1.4, 5.2, 5.3, 5.4_

- [ ] 7.3 Implement progress display and output handling
  - Display Rich progress bar during batch processing
  - Write results to specified output file when option provided
  - Display results to stdout when no output file specified
  - Show summary statistics after batch processing (total, successful, failed)
  - _Requirements: 3.1, 3.2, 4.4_

- [ ] 8. Integration testing and validation
- [ ] 8.1 Implement unit tests for core components
  - Test MRZExtractor with valid passport images and edge cases
  - Test MRZValidator check digit validation for TD1 and TD3 formats
  - Test OutputFormatter produces valid JSON and CSV output
  - Test PassportExtractionService orchestration and error handling
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 6.1, 6.2, 6.3, 6.4_

- [ ] 8.2 Implement CLI integration tests
  - Test extract command with single image file
  - Test extract command with directory batch processing
  - Test all output formats (table, json, csv)
  - Test error handling and exit codes
  - Test help output and usage messages
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 7.1, 7.2, 7.3_

- [ ]* 8.3 Implement contract tests for external libraries
  - Test PassportEye API returns expected structure for valid passports
  - Test mrz library checker behavior for validation scenarios
  - Document expected behavior for future compatibility verification
  - _Requirements: 6.1, 6.2_
