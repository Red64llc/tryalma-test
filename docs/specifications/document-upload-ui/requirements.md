# Requirements Document

## Introduction
This document defines the requirements for a Flask-based web application that enables users to upload passport and G-28 documents, automatically extract relevant data using existing extraction services, and populate a web form with the extracted information. The application provides a professional, simple interface without authentication requirements.

## Requirements

### Requirement 1: Document Upload Interface
**Objective:** As a user, I want to upload passport and G-28 documents through a simple web interface, so that I can have their data automatically extracted.

#### Acceptance Criteria
1. The Upload UI shall display a file upload area that accepts PDF and image files (JPEG, PNG)
2. When a user selects a file, the Upload UI shall validate that the file type is PDF, JPEG, or PNG
3. If an unsupported file type is selected, the Upload UI shall display an error message indicating supported formats
4. When a user uploads a file, the Upload UI shall display a loading indicator during processing
5. The Upload UI shall allow users to upload both passport and G-28 documents in the same session
6. If a file upload fails, the Upload UI shall display an actionable error message

### Requirement 2: Document Type Selection
**Objective:** As a user, I want to specify the type of document I am uploading (passport or G-28), so that the correct extraction service is used.

#### Acceptance Criteria
1. The Upload UI shall provide a document type selector with options for passport and G-28 documents
2. When a document type is selected, the Upload UI shall route the upload to the appropriate extraction service
3. If no document type is selected before upload, the Upload UI shall prompt the user to select a document type

### Requirement 3: Passport Data Extraction Integration
**Objective:** As a user, I want my uploaded passport to be processed by the Passport Extraction Service, so that personal information is automatically extracted.

#### Acceptance Criteria
1. When a passport document is uploaded, the Upload UI shall send the document to the Passport Extraction Service
2. When the Passport Extraction Service returns extracted data, the Upload UI shall display the extracted fields to the user
3. If the Passport Extraction Service returns an error, the Upload UI shall display a user-friendly error message
4. While the Passport Extraction Service is processing, the Upload UI shall display a processing status indicator

### Requirement 4: G-28 Form Data Extraction Integration
**Objective:** As a user, I want my uploaded G-28 form to be processed by the G28 Form Extractor Service, so that attorney and applicant information is automatically extracted.

#### Acceptance Criteria
1. When a G-28 document is uploaded, the Upload UI shall send the document to the G28 Form Extractor Service
2. When the G28 Form Extractor Service returns extracted data, the Upload UI shall display the extracted fields to the user
3. If the G28 Form Extractor Service returns an error, the Upload UI shall display a user-friendly error message
4. While the G28 Form Extractor Service is processing, the Upload UI shall display a processing status indicator

### Requirement 5: Extraction Results Display
**Objective:** As a user, I want to see the extracted data with confidence levels, so that I can review the parsing results.

#### Acceptance Criteria
1. When extraction is complete, the Upload UI shall display the extracted field values
2. The Upload UI shall display extracted passport fields (name, date of birth, passport number, nationality, expiration date) with their confidence scores
3. The Upload UI shall display extracted G-28 fields (attorney information, applicant information) with their confidence scores
4. When multiple documents are processed, the Upload UI shall display results from both documents
5. The Upload UI shall allow users to clear all extracted data and start over

### Requirement 6: Confidence Level Display
**Objective:** As a user, I want to see confidence levels for each extracted field, so that I can assess the reliability of the extracted data.

#### Acceptance Criteria
1. The Upload UI shall display extracted data in a clear, organized format with field labels
2. The Upload UI shall show confidence scores as visual indicators (e.g., badges, colors) for each field
3. The Upload UI shall visually distinguish high-confidence values from low-confidence values
4. The Upload UI shall allow users to clear all results and upload new documents

### Requirement 7: Professional User Interface
**Objective:** As a user, I want a professional and clean interface, so that the application is easy to use and trustworthy.

#### Acceptance Criteria
1. The Upload UI shall use a clean, professional visual design with consistent styling
2. The Upload UI shall be responsive and usable on both desktop and tablet devices
3. The Upload UI shall provide clear visual feedback for all user actions (uploads, processing, errors)
4. The Upload UI shall display form labels and instructions clearly
5. The Upload UI shall use intuitive navigation between upload and form sections

### Requirement 8: Error Handling and User Feedback
**Objective:** As a user, I want clear feedback when errors occur, so that I understand what went wrong and how to proceed.

#### Acceptance Criteria
1. If a network error occurs during upload, the Upload UI shall display a retry option
2. If extraction partially succeeds (some fields extracted, others failed), the Upload UI shall display which fields were successfully extracted
3. The Upload UI shall validate form fields before allowing submission
4. If form validation fails, the Upload UI shall highlight invalid fields with descriptive error messages
