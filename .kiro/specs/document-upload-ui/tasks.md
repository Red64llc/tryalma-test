# Implementation Plan

## Task Overview

This implementation plan covers the Document Upload UI feature - a Flask-based web application for uploading passport and G-28 documents with automatic data extraction and form population.

---

## Tasks

- [x] 1. Flask Application Foundation
- [x] 1.1 (P) Create Flask application factory with configuration and CSRF protection
  - Set up Flask app factory following steering patterns (development, testing, production configs)
  - Configure CSRF protection via Flask-WTF
  - Set maximum upload file size to 10MB
  - Register error handlers for common HTTP errors
  - _Requirements: 7.1_

- [x] 1.2 (P) Define WebApp exception hierarchy for HTTP error responses
  - Create base WebAppError with status_code and error_code attributes
  - Implement FileValidationError, UnsupportedFormatError, FileTooLargeError
  - Implement DocumentTypeRequiredError and ExtractionFailedError
  - Ensure exceptions integrate with existing application exception patterns
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 2. File Validation
- [x] 2.1 Implement file validator for uploaded documents
  - Validate file extensions against allowed list (PDF, JPEG, PNG)
  - Check file content-type using magic bytes to prevent extension spoofing
  - Enforce maximum file size limit
  - Return validation results with user-friendly error messages
  - _Requirements: 1.2, 1.3, 1.6_

- [ ] 3. Field Mapping
- [ ] 3.1 (P) Implement field mapper for passport data
  - Map PassportExtractionService output fields to form field schema
  - Preserve confidence scores for display purposes
  - Track auto-populated flag for visual distinction
  - _Requirements: 5.1, 5.2_

- [ ] 3.2 (P) Implement field mapper for G-28 form data
  - Map G28ParserService output fields to form field schema
  - Handle attorney information and applicant information sections
  - Preserve confidence scores and source tracking
  - _Requirements: 5.1, 5.3_

- [ ] 3.3 Implement field merge logic for multiple document uploads
  - Merge new extraction results with existing form data
  - Preserve previously populated fields (no overwriting)
  - Handle conflicts between passport and G-28 data gracefully
  - _Requirements: 5.4_

- [ ] 4. Upload Service and Routes
- [ ] 4.1 Implement upload service for document processing orchestration
  - Accept file uploads and route to appropriate extraction service based on document type
  - Integrate with PassportExtractionService for passport documents
  - Integrate with G28ParserService for G-28 documents
  - Handle extraction results and transform to unified response format
  - _Requirements: 3.1, 3.2, 4.1, 4.2_

- [ ] 4.2 Create upload blueprint with HTTP routes
  - Implement GET / to serve the main upload page
  - Implement POST /upload to handle file submissions and return JSON responses
  - Implement POST /clear to reset form state
  - Validate document type is selected before processing
  - _Requirements: 1.1, 1.4, 2.1, 2.2, 2.3_

- [ ] 4.3 Implement extraction error handling and partial success responses
  - Catch and transform extraction service errors to user-friendly messages
  - Support partial extraction scenarios (some fields succeed, others fail)
  - Provide retry option for network errors
  - _Requirements: 3.3, 3.4, 4.3, 4.4, 8.1, 8.2_

- [ ] 5. Base Template and Layout
- [ ] 5.1 (P) Create base Jinja2 template with Bootstrap 5 integration
  - Set up page structure with blocks for title, content, and scripts
  - Include Bootstrap 5 via CDN for responsive styling
  - Configure flash message display area
  - Include CSRF token for AJAX requests
  - _Requirements: 7.1, 7.2_

- [ ] 6. Upload Interface Components
- [ ] 6.1 Create upload page template with document type selector and upload zone
  - Implement drag-and-drop upload area using HTML5 drag events
  - Add document type selector with passport and G-28 options
  - Display loading indicator during file upload and processing
  - Show supported file formats guidance
  - _Requirements: 1.1, 1.4, 1.5, 2.1, 7.3, 7.4_

- [ ] 6.2 Implement upload zone JavaScript for AJAX file handling
  - Handle drag-and-drop events with visual feedback
  - Perform client-side file type validation before upload
  - Submit files via AJAX with progress indication
  - Display upload errors and allow retry
  - _Requirements: 1.1, 1.4, 1.6, 8.1_

- [ ] 7. Form Display and Editing
- [ ] 7.1 Create form panel template for displaying extracted data
  - Render form fields with labels and pre-populated values
  - Map all passport fields (name, DOB, passport number, nationality, expiry)
  - Map all G-28 fields (attorney info, applicant info)
  - Use Bootstrap form components for consistent styling
  - _Requirements: 5.1, 5.2, 5.3, 6.1, 7.4_

- [ ] 7.2 Implement results panel for extraction review
  - Display extracted fields alongside populated form
  - Show confidence indicators for auto-populated values
  - Visually distinguish auto-populated vs manually entered fields
  - _Requirements: 6.1, 6.3_

- [ ] 7.3 Implement form editing and clear functionality
  - Enable editing of any pre-populated field
  - Track user modifications to preserve changes during merge
  - Implement clear all functionality to reset form state
  - Highlight validation errors on individual fields
  - _Requirements: 5.5, 6.2, 6.4, 8.3, 8.4_

- [ ] 8. Responsive Design and Navigation
- [ ] 8.1 Implement responsive layout for desktop and tablet
  - Configure Bootstrap grid for multi-column layout on larger screens
  - Ensure upload zone and form panels stack on smaller screens
  - Test usability at tablet breakpoints
  - _Requirements: 7.2, 7.5_

- [ ] 9. Integration Testing
- [ ] 9.1 Test upload routes with Flask test client
  - Verify GET / returns upload page with correct components
  - Test POST /upload with valid files and document types
  - Test error responses for invalid files and missing document type
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [ ] 9.2 Test passport extraction integration flow
  - Submit passport document through upload route
  - Verify PassportExtractionService is called correctly
  - Confirm extracted fields are mapped to form schema
  - Test extraction error handling
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 9.3 Test G-28 extraction integration flow
  - Submit G-28 document through upload route
  - Verify G28ParserService is called correctly
  - Confirm extracted fields are mapped to form schema
  - Test extraction error handling
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 9.4 Test multi-document upload and merge workflow
  - Upload passport, then upload G-28 in same session
  - Verify form fields merge without overwriting existing values
  - Confirm user edits are preserved during merge
  - _Requirements: 1.5, 5.4, 6.2_

---

## Requirements Coverage

| Requirement | Tasks |
|-------------|-------|
| 1.1 | 4.2, 6.1, 6.2, 9.1 |
| 1.2 | 2.1, 9.1 |
| 1.3 | 2.1, 9.1 |
| 1.4 | 4.2, 6.1, 6.2 |
| 1.5 | 6.1, 9.4 |
| 1.6 | 2.1, 6.2 |
| 2.1 | 4.2, 6.1, 9.1 |
| 2.2 | 4.2, 9.1 |
| 2.3 | 4.2, 9.1 |
| 3.1 | 4.1, 9.2 |
| 3.2 | 4.1, 9.2 |
| 3.3 | 4.3, 9.2 |
| 3.4 | 4.3, 9.2 |
| 4.1 | 4.1, 9.3 |
| 4.2 | 4.1, 9.3 |
| 4.3 | 4.3, 9.3 |
| 4.4 | 4.3, 9.3 |
| 5.1 | 3.1, 3.2, 7.1 |
| 5.2 | 3.1, 7.1 |
| 5.3 | 3.2, 7.1 |
| 5.4 | 3.3, 9.4 |
| 5.5 | 7.3 |
| 6.1 | 7.1, 7.2 |
| 6.2 | 7.3, 9.4 |
| 6.3 | 7.2 |
| 6.4 | 7.3 |
| 7.1 | 1.1, 5.1 |
| 7.2 | 5.1, 8.1 |
| 7.3 | 6.1 |
| 7.4 | 6.1, 7.1 |
| 7.5 | 8.1 |
| 8.1 | 4.3, 6.2 |
| 8.2 | 1.2, 4.3 |
| 8.3 | 7.3 |
| 8.4 | 1.2, 7.3 |
