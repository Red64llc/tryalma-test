# Requirements Document

## Introduction

This document specifies the requirements for the LLM Passport Cross-Check feature, which implements dual-source passport data extraction with LLM vision cross-validation. The system extracts passport data using both passporteye (MRZ-based extraction) and a vision LLM (Claude/Gemini), then cross-validates results to achieve higher accuracy and confidence scoring. The feature enables parallel extraction from MRZ and visual zones, field-by-field cross-validation, confidence scoring, fallback handling when one source fails, and comprehensive discrepancy reporting.

## Requirements

### Requirement 1: Dual-Source Data Extraction

**Objective:** As a developer, I want the system to extract passport data from both MRZ and visual zones in parallel, so that I can obtain comprehensive data from multiple sources for validation.

#### Acceptance Criteria
1. When a passport image is provided, the Cross-Check Service shall initiate extraction from both MRZ (via passporteye) and visual zones (via vision LLM) in parallel.
2. When MRZ extraction completes, the Cross-Check Service shall return structured data containing surname, given names, nationality, date of birth, passport number, sex, and expiration date.
3. When vision LLM extraction completes, the Cross-Check Service shall return structured data containing the same fields extracted from the visual zone of the passport.
4. The Cross-Check Service shall support Claude and Gemini as vision LLM providers.
5. When both extraction sources complete, the Cross-Check Service shall combine results into a unified extraction response.

### Requirement 2: Field-by-Field Cross-Validation

**Objective:** As a developer, I want the system to compare extracted data field by field, so that I can identify discrepancies and determine the most accurate values.

#### Acceptance Criteria
1. When both MRZ and vision LLM extractions are available, the Cross-Check Service shall compare each corresponding field between the two sources.
2. When comparing text fields, the Cross-Check Service shall normalize values before comparison (case insensitivity, whitespace trimming, diacritics handling).
3. When comparing date fields, the Cross-Check Service shall use standardized date format (YYYY-MM-DD) for comparison.
4. When fields match between sources, the Cross-Check Service shall mark the field as validated with high confidence.
5. When fields differ between sources, the Cross-Check Service shall record the discrepancy with both source values.

### Requirement 3: Confidence Scoring

**Objective:** As a developer, I want the system to calculate confidence scores for extracted data, so that I can assess the reliability of the extraction results.

#### Acceptance Criteria
1. When cross-validation completes, the Cross-Check Service shall assign a confidence score (0.0 to 1.0) to each extracted field.
2. When both sources agree on a field value, the Cross-Check Service shall assign a confidence score of 1.0 to that field.
3. When sources disagree on a field value, the Cross-Check Service shall assign a reduced confidence score based on the disagreement severity.
4. When only one source provides a field value, the Cross-Check Service shall assign a moderate confidence score (0.5-0.7) to that field.
5. When extraction completes, the Cross-Check Service shall calculate an overall document confidence score as a weighted average of field confidence scores.

### Requirement 4: Fallback Handling

**Objective:** As a developer, I want the system to gracefully handle failures in one extraction source, so that I can still obtain usable results when one source is unavailable.

#### Acceptance Criteria
1. If MRZ extraction fails, the Cross-Check Service shall continue with vision LLM extraction alone and return results with reduced confidence.
2. If vision LLM extraction fails, the Cross-Check Service shall continue with MRZ extraction alone and return results with reduced confidence.
3. If both extraction sources fail, the Cross-Check Service shall return an error response with detailed failure reasons.
4. When fallback mode is active, the Cross-Check Service shall indicate in the response that only single-source extraction was performed.
5. If MRZ extraction times out after a configurable duration, the Cross-Check Service shall proceed with available results.
6. If vision LLM extraction times out after a configurable duration, the Cross-Check Service shall proceed with available results.

### Requirement 5: Discrepancy Reporting

**Objective:** As a developer, I want the system to provide detailed discrepancy reports, so that I can understand and resolve data inconsistencies.

#### Acceptance Criteria
1. When discrepancies exist between sources, the Cross-Check Service shall generate a discrepancy report listing all mismatched fields.
2. When generating a discrepancy report, the Cross-Check Service shall include the MRZ value, vision LLM value, and recommended value for each discrepancy.
3. When recommending a value for discrepant fields, the Cross-Check Service shall apply source-specific reliability rules (MRZ preferred for machine-readable data, vision LLM preferred for human-readable names with special characters).
4. When no discrepancies exist, the Cross-Check Service shall indicate full agreement between sources in the response.
5. The Cross-Check Service shall categorize discrepancies by severity level (critical, warning, informational).

### Requirement 6: Extraction Result Structure

**Objective:** As a developer, I want the extraction results to follow a consistent structure, so that I can easily integrate the service with other components.

#### Acceptance Criteria
1. The Cross-Check Service shall return extraction results containing: extracted fields, confidence scores, source indicators, discrepancy report, and overall status.
2. When extraction succeeds, the Cross-Check Service shall return a status of "success" with complete field data.
3. When extraction partially succeeds (one source fails), the Cross-Check Service shall return a status of "partial" with available field data.
4. When extraction fails completely, the Cross-Check Service shall return a status of "error" with error details.
5. The Cross-Check Service shall include processing metadata (extraction duration, sources used, API versions) in the response.

### Requirement 7: Configuration and Provider Management

**Objective:** As a developer, I want to configure extraction providers and parameters, so that I can customize the system behavior for different use cases.

#### Acceptance Criteria
1. The Cross-Check Service shall support configuration of vision LLM provider (Claude or Gemini).
2. The Cross-Check Service shall support configuration of timeout values for each extraction source.
3. The Cross-Check Service shall support configuration of confidence thresholds for field validation.
4. When no configuration is provided, the Cross-Check Service shall use sensible default values.
5. If an invalid LLM provider is configured, the Cross-Check Service shall raise a configuration error with guidance on valid options.
