# Requirements Document

## Project Description (Input)
g28-form-parser: extract all relevant information from a form g28, the form can be provided as a PDF or image format
there's an example form in docs/Example_G-28.pdf

## Introduction

The G-28 Form Parser is a tool designed to extract structured data from USCIS Form G-28 (Notice of Entry of Appearance as Attorney or Accredited Representative). The form contains information about attorneys/representatives, their clients, eligibility details, and consent signatures. The parser shall support both PDF and image formats as input and output structured data containing all relevant fields from the form.

## Requirements

### Requirement 1: Document Input Handling

**Objective:** As a user, I want to provide a G-28 form in either PDF or image format, so that I can extract information regardless of how the document was digitized.

#### Acceptance Criteria
1. When a PDF file is provided, the G28 Parser shall accept and process the document for extraction.
2. When an image file (PNG, JPG, JPEG, TIFF) is provided, the G28 Parser shall accept and process the document for extraction.
3. If an unsupported file format is provided, the G28 Parser shall return an error indicating the supported formats.
4. If the provided file does not exist or is unreadable, the G28 Parser shall return an appropriate error message.
5. When a multi-page PDF is provided, the G28 Parser shall process all pages (up to 4 pages for standard G-28 forms).

### Requirement 2: Attorney/Representative Information Extraction

**Objective:** As a user, I want to extract all attorney or accredited representative information from Part 1 of the form, so that I can identify who is representing the client.

#### Acceptance Criteria
1. When processing a G-28 form, the G28 Parser shall extract the USCIS Online Account Number (if present).
2. When processing a G-28 form, the G28 Parser shall extract the attorney/representative name fields (family name, given name, middle name).
3. When processing a G-28 form, the G28 Parser shall extract the complete address (street, apt/ste/flr, city, state, ZIP code, province, postal code, country).
4. When processing a G-28 form, the G28 Parser shall extract contact information (daytime telephone, mobile telephone, email address, fax number).
5. If any field in Part 1 is empty or marked N/A, the G28 Parser shall represent it as null or empty in the output.

### Requirement 3: Eligibility Information Extraction

**Objective:** As a user, I want to extract eligibility information from Part 2 of the form, so that I can verify the representative's qualifications.

#### Acceptance Criteria
1. When processing a G-28 form, the G28 Parser shall extract whether the representative is an attorney eligible to practice law (checkbox 1.a).
2. When processing a G-28 form, the G28 Parser shall extract the licensing authority/state bar information.
3. When processing a G-28 form, the G28 Parser shall extract the bar number (if applicable).
4. When processing a G-28 form, the G28 Parser shall extract whether the attorney is subject to any disciplinary orders (checkbox 1.c).
5. When processing a G-28 form, the G28 Parser shall extract the law firm or organization name (if applicable).
6. When processing a G-28 form, the G28 Parser shall extract accredited representative information including organization name and accreditation date (if applicable).
7. When processing a G-28 form, the G28 Parser shall extract association information (checkbox 3) and law student/graduate information (checkboxes 4.a, 4.b) if present.

### Requirement 4: Notice of Appearance Extraction

**Objective:** As a user, I want to extract the notice of appearance details from Part 3, so that I can understand the scope of representation.

#### Acceptance Criteria
1. When processing a G-28 form, the G28 Parser shall identify which agency the appearance relates to (USCIS, ICE, or CBP checkboxes).
2. When processing a G-28 form, the G28 Parser shall extract the specific matter or form numbers listed for each selected agency.
3. When processing a G-28 form, the G28 Parser shall extract the receipt number (if any).
4. When processing a G-28 form, the G28 Parser shall identify the representation type (Applicant, Petitioner, Requestor, Beneficiary/Derivative, or Respondent).

### Requirement 5: Client Information Extraction

**Objective:** As a user, I want to extract all client information from Part 3, so that I can identify who is being represented.

#### Acceptance Criteria
1. When processing a G-28 form, the G28 Parser shall extract the client's name fields (family name, given name, middle name).
2. When processing a G-28 form, the G28 Parser shall extract entity information (name and title of authorized signatory) if applicable.
3. When processing a G-28 form, the G28 Parser shall extract the client's USCIS Online Account Number (if any).
4. When processing a G-28 form, the G28 Parser shall extract the client's Alien Registration Number (A-Number) (if any).
5. When processing a G-28 form, the G28 Parser shall extract the client's contact information (daytime telephone, mobile telephone, email address).
6. When processing a G-28 form, the G28 Parser shall extract the client's complete mailing address (street, apt/ste/flr, city, state, ZIP code, province, postal code, country).

### Requirement 6: Consent and Signature Information Extraction

**Objective:** As a user, I want to extract consent options and signature information from Parts 4 and 5, so that I can verify proper authorization.

#### Acceptance Criteria
1. When processing a G-28 form, the G28 Parser shall extract the notice delivery preferences (checkboxes 1.a, 1.b, 1.c in Part 4).
2. When processing a G-28 form, the G28 Parser shall detect whether a client signature is present.
3. When processing a G-28 form, the G28 Parser shall extract the client signature date (if legible).
4. When processing a G-28 form, the G28 Parser shall detect whether an attorney/representative signature is present.
5. When processing a G-28 form, the G28 Parser shall extract the attorney/representative signature date (if legible).
6. Where a law student or law graduate signature section is completed, the G28 Parser shall extract that signature date as well.

### Requirement 7: Additional Information Extraction

**Objective:** As a user, I want to extract any additional information from Part 6, so that I capture supplementary details provided on the form.

#### Acceptance Criteria
1. When processing a G-28 form, the G28 Parser shall extract the name fields from Part 6 (family name, given name, middle name).
2. When processing a G-28 form, the G28 Parser shall extract all additional information entries including their page number, part number, item number, and content.
3. If Part 6 is empty or not present, the G28 Parser shall return an empty collection for additional information.

### Requirement 8: Structured Output Format

**Objective:** As a user, I want the extracted data in a structured format, so that I can easily integrate it with other systems.

#### Acceptance Criteria
1. The G28 Parser shall output extracted data as a structured object (JSON-serializable).
2. The G28 Parser shall organize output fields by form section (Part 1 through Part 6).
3. The G28 Parser shall use consistent field naming conventions matching form field identifiers (e.g., "family_name", "given_name", "street_number_and_name").
4. When a checkbox field is extracted, the G28 Parser shall represent it as a boolean value.
5. When a date field is extracted, the G28 Parser shall normalize it to ISO 8601 format (YYYY-MM-DD) when possible.
6. The G28 Parser shall include a confidence score for each extracted field when available from the underlying extraction engine.

### Requirement 9: CLI Interface

**Objective:** As a user, I want to invoke the parser from the command line, so that I can easily process forms without writing code.

#### Acceptance Criteria
1. When invoked with a file path argument, the G28 Parser CLI shall process the specified G-28 form.
2. The G28 Parser CLI shall output the extracted data to stdout in JSON format by default.
3. When the --output option is provided, the G28 Parser CLI shall write the extracted data to the specified file.
4. When the --format option is provided with value "json" or "yaml", the G28 Parser CLI shall output in the specified format.
5. If an error occurs during processing, the G28 Parser CLI shall output an error message to stderr and exit with a non-zero code.
6. When the --verbose option is provided, the G28 Parser CLI shall output additional processing information.

### Requirement 10: Error Handling and Validation

**Objective:** As a user, I want clear feedback when extraction fails or produces uncertain results, so that I can take appropriate action.

#### Acceptance Criteria
1. If the document is not recognized as a G-28 form, the G28 Parser shall return an error indicating the document type mismatch.
2. If the document quality is too poor for reliable extraction, the G28 Parser shall return a warning with details about the quality issues.
3. When extraction confidence for a field falls below a threshold, the G28 Parser shall flag that field as uncertain in the output.
4. If required form sections are missing or illegible, the G28 Parser shall include a list of missing/incomplete sections in the output.
5. The G28 Parser shall validate extracted data formats (e.g., email format, phone number format, date format) and flag invalid values.
