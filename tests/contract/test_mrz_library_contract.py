"""Contract tests for mrz library (ICAO 9303 validation).

Task 8.3: Test mrz library checker behavior for validation scenarios.

These tests verify that the mrz library behaves as expected by our
MRZValidator implementation. They document the contract between our code
and the external library for future compatibility verification.

Requirements: 6.1, 6.2
"""

import pytest

from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td3 import TD3CodeChecker


class TestTD3CodeCheckerContract:
    """Contract tests for mrz.checker.td3.TD3CodeChecker.

    Documents the expected behavior of the TD3 (passport) MRZ validator.
    """

    @pytest.fixture
    def valid_td3_mrz(self) -> str:
        """Provide a valid TD3 MRZ for contract testing."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        return f"{line1}\n{line2}"

    @pytest.fixture
    def invalid_td3_mrz(self) -> str:
        """Provide an invalid TD3 MRZ (wrong check digit)."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        # Changed check digit from 6 to 9
        line2 = "L898902C39UTO7408122F1204159ZE184226B<<<<<10"
        return f"{line1}\n{line2}"

    def test_td3_checker_accepts_valid_mrz(self, valid_td3_mrz: str):
        """TD3CodeChecker should accept valid MRZ without raising."""
        # Contract: valid MRZ is accepted without exception
        checker = TD3CodeChecker(valid_td3_mrz)
        assert checker is not None

    def test_td3_checker_has_result_attribute(self, valid_td3_mrz: str):
        """TD3CodeChecker should have result attribute (bool)."""
        checker = TD3CodeChecker(valid_td3_mrz)

        # Contract: checker.result is a boolean
        assert hasattr(checker, "result")
        assert isinstance(checker.result, bool)

    def test_td3_checker_result_true_for_valid_mrz(self, valid_td3_mrz: str):
        """checker.result should be True for valid MRZ."""
        checker = TD3CodeChecker(valid_td3_mrz)

        # Contract: valid MRZ returns result=True
        assert checker.result is True

    def test_td3_checker_result_false_for_invalid_mrz(self, invalid_td3_mrz: str):
        """checker.result should be False for invalid check digit."""
        checker = TD3CodeChecker(invalid_td3_mrz)

        # Contract: invalid check digit returns result=False
        assert checker.result is False

    def test_td3_checker_has_report_attribute(self, valid_td3_mrz: str):
        """TD3CodeChecker should have report attribute."""
        checker = TD3CodeChecker(valid_td3_mrz)

        # Contract: checker has report attribute
        assert hasattr(checker, "report")

    def test_td3_checker_report_has_fields(self, valid_td3_mrz: str):
        """Report should have fields attribute listing check results."""
        checker = TD3CodeChecker(valid_td3_mrz)

        # Contract: report.fields is iterable of (field_name, is_valid) tuples
        assert hasattr(checker.report, "fields")
        fields = list(checker.report.fields)
        assert len(fields) > 0

        for field_name, is_valid in fields:
            assert isinstance(field_name, str)
            assert isinstance(is_valid, bool)

    def test_td3_checker_report_includes_hash_fields(self, valid_td3_mrz: str):
        """Report should include hash (check digit) validation fields."""
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = list(checker.report.fields)

        # Contract: report includes check digit fields
        field_names = [name.lower() for name, _ in fields]

        # At least some hash fields should be present
        hash_fields = [name for name in field_names if "hash" in name]
        assert len(hash_fields) > 0

    def test_td3_checker_report_has_warnings(self, valid_td3_mrz: str):
        """Report should have warnings attribute (list)."""
        checker = TD3CodeChecker(valid_td3_mrz)

        # Contract: report.warnings is a list (may be empty)
        assert hasattr(checker.report, "warnings")
        assert isinstance(checker.report.warnings, (list, tuple))

    def test_td3_checker_validates_document_number_hash(self, valid_td3_mrz: str):
        """Report should include document number check digit validation."""
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = dict(checker.report.fields)

        # Contract: document number hash is validated
        doc_hash_fields = [k for k in fields.keys() if "document" in k.lower()]
        assert len(doc_hash_fields) > 0

    def test_td3_checker_validates_birth_date_hash(self, valid_td3_mrz: str):
        """Report should include birth date check digit validation."""
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = dict(checker.report.fields)

        # Contract: birth date hash is validated
        birth_hash_fields = [k for k in fields.keys() if "birth" in k.lower()]
        assert len(birth_hash_fields) > 0

    def test_td3_checker_validates_expiry_date_hash(self, valid_td3_mrz: str):
        """Report should include expiry date check digit validation."""
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = dict(checker.report.fields)

        # Contract: expiry date hash is validated
        expiry_hash_fields = [k for k in fields.keys() if "expir" in k.lower()]
        assert len(expiry_hash_fields) > 0

    def test_td3_checker_validates_final_hash(self, valid_td3_mrz: str):
        """Report should include composite (final) check digit validation."""
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = dict(checker.report.fields)

        # Contract: final/composite hash is validated
        final_hash_fields = [k for k in fields.keys() if "final" in k.lower()]
        assert len(final_hash_fields) > 0


class TestTD1CodeCheckerContract:
    """Contract tests for mrz.checker.td1.TD1CodeChecker.

    Documents the expected behavior of the TD1 (ID card) MRZ validator.
    """

    @pytest.fixture
    def valid_td1_mrz(self) -> str:
        """Provide a valid TD1 MRZ for contract testing."""
        line1 = "I<UTOD231458907<<<<<<<<<<<<<<<"
        line2 = "7408122F1204159UTO<<<<<<<<<<<6"
        line3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<"
        return f"{line1}\n{line2}\n{line3}"

    def test_td1_checker_accepts_valid_mrz(self, valid_td1_mrz: str):
        """TD1CodeChecker should accept valid MRZ without raising."""
        # Contract: valid MRZ is accepted without exception
        checker = TD1CodeChecker(valid_td1_mrz)
        assert checker is not None

    def test_td1_checker_has_result_attribute(self, valid_td1_mrz: str):
        """TD1CodeChecker should have result attribute (bool)."""
        checker = TD1CodeChecker(valid_td1_mrz)

        # Contract: checker.result is a boolean
        assert hasattr(checker, "result")
        assert isinstance(checker.result, bool)

    def test_td1_checker_result_true_for_valid_mrz(self, valid_td1_mrz: str):
        """checker.result should be True for valid MRZ."""
        checker = TD1CodeChecker(valid_td1_mrz)

        # Contract: valid MRZ returns result=True
        assert checker.result is True

    def test_td1_checker_has_report_with_fields(self, valid_td1_mrz: str):
        """TD1CodeChecker report should have fields attribute."""
        checker = TD1CodeChecker(valid_td1_mrz)

        # Contract: report structure same as TD3
        assert hasattr(checker, "report")
        assert hasattr(checker.report, "fields")

        fields = list(checker.report.fields)
        assert len(fields) > 0

    def test_td1_checker_validates_document_number_hash(self, valid_td1_mrz: str):
        """Report should include document number check digit validation."""
        checker = TD1CodeChecker(valid_td1_mrz)
        fields = dict(checker.report.fields)

        # Contract: document number hash is validated
        doc_hash_fields = [k for k in fields.keys() if "document" in k.lower()]
        assert len(doc_hash_fields) > 0

    def test_td1_checker_validates_birth_date_hash(self, valid_td1_mrz: str):
        """Report should include birth date check digit validation."""
        checker = TD1CodeChecker(valid_td1_mrz)
        fields = dict(checker.report.fields)

        # Contract: birth date hash is validated
        birth_hash_fields = [k for k in fields.keys() if "birth" in k.lower()]
        assert len(birth_hash_fields) > 0


class TestMRZLibraryErrorHandling:
    """Contract tests for mrz library error handling."""

    def test_td3_checker_raises_for_invalid_format(self):
        """TD3CodeChecker should raise for malformed MRZ."""
        invalid_mrz = "TOO SHORT"

        # Contract: invalid format raises exception
        with pytest.raises(Exception):
            TD3CodeChecker(invalid_mrz)

    def test_td1_checker_raises_for_invalid_format(self):
        """TD1CodeChecker should raise for malformed MRZ."""
        invalid_mrz = "TOO SHORT"

        # Contract: invalid format raises exception
        with pytest.raises(Exception):
            TD1CodeChecker(invalid_mrz)

    def test_td3_checker_raises_for_wrong_line_count(self):
        """TD3CodeChecker should raise for single line MRZ."""
        single_line = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"

        # Contract: wrong number of lines raises exception
        with pytest.raises(Exception):
            TD3CodeChecker(single_line)

    def test_td3_checker_raises_for_wrong_length(self):
        """TD3CodeChecker should raise for incorrect line lengths."""
        short_mrz = "P<UTO\nL898"

        # Contract: incorrect length raises exception
        with pytest.raises(Exception):
            TD3CodeChecker(short_mrz)


class TestMRZLibraryFieldNaming:
    """Contract tests documenting field naming conventions.

    These tests document the exact field names used by the mrz library
    so our _FIELD_NAME_MAP in MRZValidator stays accurate.
    """

    @pytest.fixture
    def valid_td3_mrz(self) -> str:
        """Provide valid TD3 MRZ."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        return f"{line1}\n{line2}"

    def test_hash_field_names_contain_hash_keyword(self, valid_td3_mrz: str):
        """Check digit fields should contain 'hash' in their names."""
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = list(checker.report.fields)

        # Collect all hash fields
        hash_fields = [name for name, _ in fields if "hash" in name.lower()]

        # Contract: multiple hash fields exist
        assert len(hash_fields) >= 3  # At least doc, birth, expiry, and final

    def test_expected_hash_field_names_exist(self, valid_td3_mrz: str):
        """Verify specific expected hash field names.

        These names are used in our _FIELD_NAME_MAP for translation.
        """
        checker = TD3CodeChecker(valid_td3_mrz)
        fields = dict(checker.report.fields)

        # Contract: these exact field names exist (case-insensitive check)
        field_names_lower = {k.lower(): k for k in fields.keys()}

        expected_patterns = [
            "final hash",
            "document number hash",
            "birth date hash",
            "expiry date hash",
        ]

        for pattern in expected_patterns:
            matching = [k for k in field_names_lower if pattern in k]
            assert len(matching) > 0, f"Missing field matching: {pattern}"


class TestMRZLibraryWarningsContract:
    """Contract tests for warnings behavior."""

    @pytest.fixture
    def expired_td3_mrz(self) -> str:
        """Provide TD3 MRZ with past expiry date."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"  # Expiry: 120415 (2012)
        return f"{line1}\n{line2}"

    def test_warnings_is_list_type(self, expired_td3_mrz: str):
        """Report warnings should be a list or tuple."""
        checker = TD3CodeChecker(expired_td3_mrz)

        # Contract: warnings is always iterable collection
        assert hasattr(checker.report, "warnings")
        warnings = checker.report.warnings
        assert isinstance(warnings, (list, tuple))

    def test_warnings_contain_strings(self, expired_td3_mrz: str):
        """Warning items should be strings."""
        checker = TD3CodeChecker(expired_td3_mrz)
        warnings = checker.report.warnings

        # Contract: each warning is a string
        for warning in warnings:
            assert isinstance(warning, str)
