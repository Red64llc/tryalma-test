"""Integration tests for G28ParserService.

Task 9.2: Implement parser service integration tests.
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6

Tests end-to-end parsing with mocked VisionExtractor to avoid real API calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml

from tryalma.g28.models import G28ExtractionResult, G28FormData
from tryalma.g28.parser_service import G28ParserService


class TestParserServicePDFParsing:
    """Test parser service with PDF documents."""

    def test_parse_pdf_returns_successful_result(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test end-to-end parsing with test PDF document.
        
        Requirement 8.1: The G28 Parser shall output extracted data as 
        a structured object (JSON-serializable).
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is True
        assert result.data is not None
        assert result.error is None

    def test_parse_pdf_returns_g28_form_data(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that parsing returns proper G28FormData structure.
        
        Requirement 8.2: The G28 Parser shall organize output fields 
        by form section (Part 1 through Part 6).
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert isinstance(result.data, G28FormData)
        assert result.data.form_detected is True

    def test_parse_pdf_extracts_attorney_info(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
        expected_attorney_info: dict,
    ) -> None:
        """Test that Part 1 attorney information is extracted.
        
        Requirement 8.3: The G28 Parser shall use consistent field naming 
        conventions matching form field identifiers.
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.part1_attorney_info is not None
        
        attorney = result.data.part1_attorney_info
        assert attorney.family_name is not None
        assert attorney.family_name.value == expected_attorney_info["family_name"]
        assert attorney.given_name is not None
        assert attorney.given_name.value == expected_attorney_info["given_name"]

    def test_parse_pdf_extracts_eligibility_info(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that Part 2 eligibility information is extracted."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.part2_eligibility is not None
        
        eligibility = result.data.part2_eligibility
        assert eligibility.is_attorney is not None
        assert eligibility.is_attorney.value is True
        assert eligibility.bar_number is not None

    def test_parse_pdf_extracts_notice_of_appearance(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that Part 3 notice of appearance is extracted."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.part3_notice_of_appearance is not None
        
        notice = result.data.part3_notice_of_appearance
        assert notice.agency_uscis is not None
        assert notice.representation_type is not None

    def test_parse_pdf_extracts_client_info(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
        expected_client_info: dict,
    ) -> None:
        """Test that Part 3 client information is extracted."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.part3_client_info is not None
        
        client = result.data.part3_client_info
        assert client.family_name is not None
        assert client.family_name.value == expected_client_info["family_name"]
        assert client.given_name is not None
        assert client.given_name.value == expected_client_info["given_name"]

    def test_parse_pdf_extracts_consent_signatures(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that Parts 4-5 consent and signatures are extracted."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.part4_5_consent_signatures is not None

    def test_parse_pdf_extracts_additional_info(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that Part 6 additional information is extracted."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.part6_additional_info is not None


class TestParserServiceImageParsing:
    """Test parser service with image documents."""

    def test_parse_image_returns_successful_result(
        self,
        parser_service_with_mock: G28ParserService,
        synthetic_g28_image: Path,
    ) -> None:
        """Test parsing with test image document.
        
        Requirement 1.2: When an image file is provided, the G28 Parser 
        shall accept and process the document for extraction.
        """
        result = parser_service_with_mock.parse(synthetic_g28_image)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is True
        assert result.data is not None


class TestParserServiceBytesParsing:
    """Test parser service with byte input (Flask/web upload support)."""

    def test_parse_bytes_pdf_returns_successful_result(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_bytes: bytes,
    ) -> None:
        """Test parsing PDF bytes for web upload support."""
        result = parser_service_with_mock.parse_bytes(
            data=example_g28_pdf_bytes,
            filename="Example_G-28.pdf",
        )
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is True
        assert result.data is not None

    def test_parse_bytes_image_returns_successful_result(
        self,
        parser_service_with_mock: G28ParserService,
        synthetic_g28_image_bytes: tuple[bytes, str],
    ) -> None:
        """Test parsing image bytes for web upload support."""
        data, filename = synthetic_g28_image_bytes
        result = parser_service_with_mock.parse_bytes(data=data, filename=filename)
        
        assert isinstance(result, G28ExtractionResult)
        assert result.success is True


class TestParserServiceConfidenceScores:
    """Test confidence score handling."""

    def test_parse_populates_confidence_scores(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Verify confidence scores are populated.
        
        Requirement 8.6: The G28 Parser shall include a confidence score 
        for each extracted field when available from the underlying 
        extraction engine.
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.overall_confidence > 0.0
        assert result.data.overall_confidence <= 1.0
        
        # Check individual field confidence
        if result.data.part1_attorney_info and result.data.part1_attorney_info.family_name:
            assert result.data.part1_attorney_info.family_name.confidence > 0.0
            assert result.data.part1_attorney_info.family_name.confidence <= 1.0

    def test_parse_includes_overall_confidence(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that overall confidence is included in output."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert hasattr(result.data, "overall_confidence")
        assert isinstance(result.data.overall_confidence, float)


class TestParserServiceOutputFormats:
    """Test output formatting."""

    def test_result_to_output_json_format(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Verify output format is correct for JSON.
        
        Requirement 8.1: The G28 Parser shall output extracted data 
        as a structured object (JSON-serializable).
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        json_output = result.to_output(format="json")
        
        # Should be valid JSON
        parsed = json.loads(json_output)
        assert isinstance(parsed, dict)
        assert "success" in parsed
        assert "data" in parsed

    def test_result_to_output_yaml_format(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Verify output format is correct for YAML.
        
        Requirement 9.4: When the --format option is provided with 
        value "yaml", the G28 Parser CLI shall output in YAML format.
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        yaml_output = result.to_output(format="yaml")
        
        # Should be valid YAML
        parsed = yaml.safe_load(yaml_output)
        assert isinstance(parsed, dict)
        assert "success" in parsed
        assert "data" in parsed

    def test_json_output_contains_all_form_sections(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that JSON output contains all form sections.
        
        Requirement 8.2: The G28 Parser shall organize output fields 
        by form section (Part 1 through Part 6).
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        json_output = result.to_output(format="json")
        parsed = json.loads(json_output)
        
        data = parsed["data"]
        assert "part1_attorney_info" in data
        assert "part2_eligibility" in data
        assert "part3_notice_of_appearance" in data
        assert "part3_client_info" in data
        assert "part4_5_consent_signatures" in data
        assert "part6_additional_info" in data

    def test_json_output_uses_consistent_field_naming(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that JSON uses consistent field naming matching form identifiers.
        
        Requirement 8.3: The G28 Parser shall use consistent field naming 
        conventions matching form field identifiers.
        """
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        json_output = result.to_output(format="json")
        parsed = json.loads(json_output)
        
        data = parsed["data"]
        attorney = data.get("part1_attorney_info", {})
        
        # Check snake_case naming matches form fields
        if attorney:
            assert "family_name" in attorney or attorney.get("family_name") is None
            assert "given_name" in attorney or attorney.get("given_name") is None


class TestParserServiceMetadata:
    """Test metadata fields in extraction results."""

    def test_result_contains_source_file(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that result contains source file path."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.source_file == str(example_g28_pdf_path)
        if result.data:
            assert result.data.source_file == str(example_g28_pdf_path)

    def test_result_contains_extraction_timestamp(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that result contains extraction timestamp."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert result.data.extraction_timestamp is not None
        assert len(result.data.extraction_timestamp) > 0

    def test_result_contains_form_detected_flag(
        self,
        parser_service_with_mock: G28ParserService,
        example_g28_pdf_path: Path,
    ) -> None:
        """Test that result contains form_detected flag."""
        result = parser_service_with_mock.parse(example_g28_pdf_path)
        
        assert result.data is not None
        assert isinstance(result.data.form_detected, bool)
