# Implementation Plan

## Task 1: Core Data Models

- [x] 1.1 (P) Create the base extracted field model with confidence scoring
  - Implement a generic field wrapper that holds a value alongside a confidence score
  - Support marking fields as uncertain when confidence falls below a configurable threshold
  - Ensure the model is immutable and JSON-serializable via Pydantic
  - _Requirements: 8.6_

- [x] 1.2 (P) Create address and contact information models
  - Define an address structure covering US and international fields (street, city, state, ZIP, province, postal code, country)
  - Support apartment/suite/floor designations
  - Allow all fields to be optional since forms may have partial data
  - _Requirements: 2.3, 5.6_

- [x] 1.3 Create Part 1 attorney information model
  - Capture attorney name fields (family name, given name, middle name)
  - Include USCIS Online Account Number
  - Include contact fields (daytime telephone, mobile telephone, email, fax)
  - Embed the address model for attorney address
  - Represent empty or N/A fields as null
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 1.4 (P) Create Part 2 eligibility information model
  - Capture attorney eligibility checkbox (is_attorney)
  - Include licensing authority, bar number, and disciplinary order status
  - Include law firm or organization name
  - Capture accredited representative details (organization name, accreditation date)
  - Support association and law student/graduate checkboxes with associated names
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 1.5 (P) Create Part 3 notice of appearance model
  - Capture agency checkboxes (USCIS, ICE, CBP) as booleans
  - Include form numbers or matter descriptions for each agency
  - Include receipt number field
  - Capture representation type as a literal enum (Applicant, Petitioner, Requestor, Beneficiary/Derivative, Respondent)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 1.6 (P) Create Part 3 client information model
  - Capture client name fields (family name, given name, middle name)
  - Include entity information (entity name, signatory title)
  - Include USCIS Online Account Number and Alien Registration Number
  - Include client contact information (telephones, email)
  - Embed address model for client mailing address
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 1.7 (P) Create Parts 4-5 consent and signatures model
  - Capture notice delivery preference checkboxes
  - Include signature presence detection fields for client and attorney (boolean)
  - Include signature date fields normalized to ISO 8601 format
  - Include law student/graduate signature date
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 1.8 (P) Create Part 6 additional information model
  - Capture name fields for Part 6 identification
  - Define an entry structure with page number, part number, item number, and content
  - Support a list of additional information entries
  - Return empty collection when Part 6 is absent
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 1.9 Create the aggregate G28FormData model
  - Combine all part models into a single aggregate root
  - Include metadata fields (source file, form detected flag, extraction timestamp, overall confidence)
  - Include validation result lists (missing sections, uncertain fields, validation warnings)
  - Implement to_dict method for JSON serialization with optional confidence inclusion
  - Organize output fields by form section
  - Use consistent field naming matching form identifiers
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 1.10 Create the extraction result wrapper model
  - Wrap extraction outcome with success/failure status
  - Include data field for G28FormData on success
  - Include error message and error code on failure
  - Include warnings list for non-fatal issues
  - Implement to_output method supporting JSON and YAML serialization
  - _Requirements: 9.2, 10.1, 10.2, 10.3, 10.4_

## Task 2: Exception Hierarchy

- [x] 2. Create G28-specific exception classes
  - Define G28ExtractionError as base exception extending ProcessingError with exit code 3
  - Create NotG28FormError for document type mismatch detection
  - Create DocumentLoadError for file loading failures
  - Create ExtractionAPIError for external API failures
  - Create UnsupportedFormatError extending ValidationError with exit code 2
  - Create LowQualityWarning for poor document quality scenarios
  - Include descriptive default messages for each exception type
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

## Task 3: Document Loading

- [x] 3.1 Implement document format validation
  - Define supported formats constant (PDF, PNG, JPG, JPEG, TIFF)
  - Validate file extension against supported formats
  - Validate using magic bytes for security, not just extension
  - Raise UnsupportedFormatError with list of supported formats on invalid input
  - Support validation from both file path and filename string (for web uploads)
  - _Requirements: 1.3_

- [x] 3.2 Implement PDF to image conversion
  - Convert PDF pages to PIL Image objects using pdf2image
  - Enforce maximum page limit (4 pages for standard G-28)
  - Handle multi-page PDF documents
  - Convert images to RGB mode for consistency
  - Raise DocumentLoadError on conversion failure
  - _Requirements: 1.1, 1.5_

- [x] 3.3 Implement image file loading
  - Load PNG, JPG, JPEG, TIFF images using Pillow
  - Normalize images to RGB mode
  - Handle image format variations gracefully
  - Raise appropriate error for corrupted or unreadable files
  - _Requirements: 1.2, 1.4_

- [x] 3.4 Assemble DocumentLoader service
  - Implement load() method accepting file path and returning list of images
  - Implement load_bytes() method accepting raw bytes and filename for Flask integration
  - Check file existence before processing for path-based loading
  - Route to PDF or image loading based on detected format
  - Return non-empty list of RGB images on success
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

## Task 4: Vision Extraction Backend

- [x] 4.1 (P) Implement Claude Vision API client setup
  - Initialize Anthropic client with API key from parameter or environment variable
  - Configure model constant (claude-sonnet-4-20250514) and max tokens
  - Handle authentication errors gracefully
  - _Requirements: 8.6_

- [x] 4.2 Implement structured extraction with schema
  - Construct prompts that describe G-28 form fields for extraction
  - Encode page images to base64 for API submission
  - Process multi-page documents by including all pages in single request
  - Parse Claude response into provided Pydantic schema
  - Calculate per-field confidence based on extraction certainty indicators
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 8.6_

- [x] 4.3 Implement API error handling and retry logic
  - Handle rate limit errors (429) with exponential backoff
  - Handle server errors (500) with retry
  - Handle authentication errors (401) with clear message
  - Raise ExtractionAPIError with details on persistent failure
  - _Requirements: 10.1, 10.2_

## Task 5: Field Extraction Coordinator

- [x] 5.1 Implement FieldExtractor with backend injection
  - Accept primary extraction backend via constructor
  - Optionally accept fallback extraction backend
  - Fall back to secondary extractor only on primary failure
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 5.2 Implement main extraction method
  - Accept list of page images
  - Delegate to extraction backend with G28FormData schema
  - Detect if document is not a G-28 form and raise NotG28FormError
  - Return fully populated G28FormData with confidence scores
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 10.1_

- [x] 5.3 Implement field normalization and validation
  - Normalize date fields to ISO 8601 format (YYYY-MM-DD)
  - Represent checkbox fields as boolean values
  - Validate email format and flag invalid values
  - Validate phone number format and flag invalid values
  - Flag fields with confidence below threshold as uncertain
  - _Requirements: 8.4, 8.5, 10.3, 10.5_

## Task 6: Output Formatting

- [x] 6. Implement OutputFormatter for JSON and YAML
  - Format G28FormData to JSON string with proper indentation
  - Format G28FormData to YAML string using PyYAML
  - Support verbose mode that includes confidence scores and metadata
  - Support non-verbose mode that returns simplified output
  - _Requirements: 8.1, 9.2, 9.4_

## Task 7: Parser Service Orchestration

- [ ] 7.1 Implement G28ParserService constructor with dependency injection
  - Accept DocumentLoader, FieldExtractor, and OutputFormatter as dependencies
  - Accept configurable confidence threshold with default of 0.7
  - Design as stateless and thread-safe for singleton usage
  - _Requirements: 1.1, 1.2, 10.3_

- [ ] 7.2 Implement parse() method for file path input
  - Accept file path, output format, and verbose flag
  - Coordinate document loading, field extraction, and output formatting
  - Apply confidence threshold to flag uncertain fields
  - Track missing sections and validation warnings
  - Return G28ExtractionResult with success status and data
  - Handle exceptions and return appropriate error result
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 10.1, 10.2, 10.3, 10.4_

- [ ] 7.3 Implement parse_bytes() method for web upload support
  - Accept raw bytes, filename, output format, and verbose flag
  - Detect format from filename and validate
  - Delegate to DocumentLoader.load_bytes() for image conversion
  - Process through same extraction pipeline as parse()
  - Return G28ExtractionResult suitable for Flask/web integration
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 7.4 Implement parse_images() method for pre-loaded images
  - Accept list of PIL Images directly
  - Bypass document loading phase
  - Process through extraction and formatting pipeline
  - Support use cases where images are already loaded or preprocessed
  - _Requirements: 1.1, 1.2_

- [ ] 7.5 Implement create_default() factory method
  - Create service with default DocumentLoader, VisionExtractor-based FieldExtractor, and OutputFormatter
  - Accept optional API key parameter, defaulting to ANTHROPIC_API_KEY environment variable
  - Return fully configured G28ParserService ready for use
  - Enable simple initialization for Flask app factory pattern
  - _Requirements: 1.1, 1.2, 9.1_

## Task 8: CLI Command

- [ ] 8.1 Define parse-g28 command with Typer
  - Accept file path as required positional argument
  - Add --output option for writing to file instead of stdout
  - Add --format option accepting "json" or "yaml" with json default
  - Add --verbose flag for including confidence scores and metadata
  - Validate file existence and readability via Typer constraints
  - _Requirements: 9.1, 9.3, 9.4, 9.6_

- [ ] 8.2 Implement command execution logic
  - Initialize G28ParserService with default dependencies
  - Invoke parse() with provided arguments
  - Output JSON to stdout by default
  - Write to specified file when --output provided
  - Display progress information in verbose mode
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.6_

- [ ] 8.3 Implement CLI error handling
  - Catch G28-specific exceptions and display user-friendly messages
  - Write error messages to stderr
  - Exit with appropriate exit codes (2 for validation, 3 for processing errors)
  - Never expose stack traces to users
  - _Requirements: 9.5, 10.1, 10.2, 10.3, 10.4_

- [ ] 8.4 Register command with main CLI application
  - Add parse-g28 command to existing Typer app in cli.py
  - Ensure command appears in --help output
  - Follow existing CLI patterns and conventions
  - _Requirements: 9.1_

## Task 9: Integration Testing

- [ ] 9.1 Create test fixtures with sample G-28 documents
  - Use example form from docs/Example_G-28.pdf as primary fixture
  - Create synthetic test images with known field values
  - Create edge case documents (partially filled, poor quality, wrong form type)
  - _Requirements: 1.1, 1.2, 1.5_

- [ ] 9.2 Implement parser service integration tests
  - Test end-to-end parsing with test PDF document
  - Test parsing with test image documents
  - Verify all form sections are extracted
  - Verify confidence scores are populated
  - Verify output format is correct for JSON and YAML
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 9.3 Implement CLI integration tests
  - Test CLI invocation with CliRunner
  - Verify JSON output to stdout
  - Verify file output with --output option
  - Verify YAML output with --format yaml
  - Verify verbose mode output
  - Test error handling and exit codes
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 9.4 Implement error scenario tests
  - Test handling of non-G28 documents
  - Test handling of unsupported file formats
  - Test handling of missing files
  - Test handling of poor quality documents
  - Test handling of API failures with mocked responses
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

## Task 10: Unit Test Coverage

- [x] 10.1 (P) Implement DocumentLoader unit tests
  - Test PDF format validation
  - Test image format validation
  - Test unsupported format rejection
  - Test file not found handling
  - Test multi-page PDF conversion
  - Test image loading and RGB conversion
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 10.2 (P) Implement data model unit tests
  - Test Pydantic model validation rules
  - Test field constraint enforcement (confidence range 0.0-1.0)
  - Test date normalization in model validation
  - Test model serialization to dict/JSON
  - Test optional field handling (null representation)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 10.3 (P) Implement exception hierarchy tests
  - Test each exception type has correct exit code
  - Test exception messages are descriptive
  - Test exception inheritance chain
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 10.4 Implement VisionExtractor contract tests
  - Mock Claude API responses with expected schema
  - Test successful extraction parses to model correctly
  - Test API error handling (rate limit, auth, server errors)
  - Test schema validation of API response
  - _Requirements: 8.6, 10.1, 10.2_

- [x] 10.5 (P) Implement OutputFormatter tests
  - Test JSON output formatting
  - Test YAML output formatting
  - Test verbose vs non-verbose output differences
  - _Requirements: 8.1, 9.2, 9.4_
