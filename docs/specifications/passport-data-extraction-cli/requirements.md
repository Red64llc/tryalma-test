# Requirements Document

## Introduction

This specification defines the requirements for a command-line interface (CLI) tool that extracts structured data from passport images. The tool accepts either a single image file or a directory containing multiple images, processes them using optical character recognition (OCR) or machine learning techniques, and outputs extracted passport information including name, first name, date of birth, nationality, and other relevant fields. The CLI is built following the project's Python CLI standards using Typer, with clean separation between the CLI layer and core extraction logic.

## Requirements

### Requirement 1: Image Input Handling

**Objective:** As a user, I want to provide a single image file or a directory of images, so that I can extract passport data from one or multiple documents in a single command.

#### Acceptance Criteria
1. When the user provides a valid image file path as argument, the CLI shall process that single image for passport data extraction.
2. When the user provides a valid directory path as argument, the CLI shall process all supported image files within that directory.
3. If the provided path does not exist, the CLI shall display an error message indicating the path is invalid and exit with code 2.
4. If the provided directory contains no supported image files, the CLI shall display an informational message indicating no processable files were found.
5. The CLI shall support common image formats including JPEG, PNG, and TIFF.

### Requirement 2: Passport Data Extraction

**Objective:** As a user, I want to extract key passport information from images, so that I can obtain structured data for further processing or verification.

#### Acceptance Criteria
1. When processing a valid passport image, the CLI shall extract the holder's surname (family name).
2. When processing a valid passport image, the CLI shall extract the holder's given names (first name and middle names).
3. When processing a valid passport image, the CLI shall extract the date of birth.
4. When processing a valid passport image, the CLI shall extract the nationality.
5. When processing a valid passport image, the CLI shall extract the passport number.
6. When processing a valid passport image, the CLI shall extract the expiration date.
7. When processing a valid passport image, the CLI shall extract the gender/sex field.
8. When processing a valid passport image, the CLI shall extract the place of birth when available.
9. If a field cannot be extracted or recognized, the CLI shall indicate that field as unavailable or unrecognized in the output.

### Requirement 3: Output Display

**Objective:** As a user, I want to see extracted passport data in a clear and readable format, so that I can quickly review the information.

#### Acceptance Criteria
1. When extraction completes successfully for a single image, the CLI shall display all extracted fields with clear labels.
2. When extraction completes successfully for multiple images, the CLI shall display results for each image with clear separation between records.
3. The CLI shall display the source file name or path alongside each extraction result.
4. If the verbose option is enabled, the CLI shall display additional processing details including confidence scores when available.

### Requirement 4: Output Format Options

**Objective:** As a user, I want to choose how extracted data is formatted, so that I can integrate it with other tools or workflows.

#### Acceptance Criteria
1. The CLI shall support human-readable table format as the default output.
2. When the user specifies JSON output format, the CLI shall output extracted data as valid JSON.
3. When the user specifies CSV output format, the CLI shall output extracted data as valid CSV.
4. When an output file option is provided, the CLI shall write results to the specified file instead of standard output.

### Requirement 5: Error Handling

**Objective:** As a user, I want clear error messages when something goes wrong, so that I can understand and resolve issues.

#### Acceptance Criteria
1. If the image file cannot be read or is corrupted, the CLI shall display an error message identifying the problematic file and continue processing remaining files if in batch mode.
2. If the extraction service or library encounters an error, the CLI shall display a user-friendly error message without exposing internal stack traces.
3. If required dependencies or API credentials are missing, the CLI shall display instructions for resolving the configuration issue.
4. The CLI shall exit with code 0 on successful completion, code 1 for general errors, code 2 for input validation errors, and code 3 for processing errors.

### Requirement 6: Machine Readable Zone (MRZ) Processing

**Objective:** As a user, I want the tool to extract data from the MRZ section, so that I can obtain standardized machine-readable passport data.

#### Acceptance Criteria
1. When a passport image contains a Machine Readable Zone (MRZ), the CLI shall extract and decode MRZ data.
2. When MRZ data is successfully decoded, the CLI shall validate the check digits according to ICAO 9303 standards.
3. If MRZ check digit validation fails, the CLI shall indicate the validation failure in the output while still displaying the extracted data.
4. The CLI shall support both TD1 (ID card) and TD3 (passport) MRZ formats.

### Requirement 7: Help and Documentation

**Objective:** As a user, I want built-in help and usage examples, so that I can learn how to use the CLI effectively.

#### Acceptance Criteria
1. When the user invokes the CLI with the --help flag, the CLI shall display usage information, available options, and argument descriptions.
2. The CLI shall provide descriptive help text for each command-line option and argument.
3. When the user provides no arguments, the CLI shall display a brief usage message indicating required arguments.
