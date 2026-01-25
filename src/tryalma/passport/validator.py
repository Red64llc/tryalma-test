"""MRZ validator using mrz library for ICAO 9303 compliance.

Task 4.1: MRZValidator class with check digit validation.

Requirements: 6.2, 6.3, 6.4
"""

from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td3 import TD3CodeChecker

from tryalma.passport.models import CheckDigitResult, MRZType, ValidationResult


class MRZValidator:
    """Validates MRZ data according to ICAO 9303 standards.

    Uses the mrz library to perform check digit validation for TD1 (ID card)
    and TD3 (passport) MRZ formats per ICAO Doc 9303 standards.

    Attributes:
        TD3_LENGTH: Expected length of TD3 MRZ (2 lines x 44 chars + newline = 89).
        TD1_LENGTH: Expected length of TD1 MRZ (3 lines x 30 chars + 2 newlines = 92).
    """

    TD3_LENGTH = 89  # 44 + 1 + 44 (with newline)
    TD1_LENGTH = 92  # 30 + 1 + 30 + 1 + 30 (with newlines)

    # Map mrz library field names to user-friendly names
    _FIELD_NAME_MAP = {
        "final hash": "composite_check_digit",
        "document number hash": "document_number_check_digit",
        "birth date hash": "birth_date_check_digit",
        "expiry date hash": "expiry_date_check_digit",
        "optional data hash": "optional_data_check_digit",
    }

    def validate(
        self, raw_mrz: str, mrz_type: MRZType | None = None
    ) -> ValidationResult:
        """Validate MRZ string and check digits.

        Args:
            raw_mrz: Complete MRZ string (2 or 3 lines with newlines).
            mrz_type: Expected MRZ type, or None to auto-detect.

        Returns:
            ValidationResult with check digit details.
        """
        # Handle empty or invalid input
        if not raw_mrz or not raw_mrz.strip():
            return ValidationResult(
                is_valid=False,
                mrz_type=mrz_type or MRZType.TD3,  # Default to TD3 for empty
                check_digits=[],
                warnings=["Empty MRZ string provided"],
            )

        # Auto-detect MRZ type if not specified
        if mrz_type is None:
            mrz_type = self._detect_mrz_type(raw_mrz)

        # Dispatch to specific validator
        if mrz_type == MRZType.TD1:
            return self.validate_td1(raw_mrz)
        elif mrz_type == MRZType.TD3:
            return self.validate_td3(raw_mrz)
        else:
            # For other types (TD2, MRVA, MRVB), fall back to TD3 or return warning
            return ValidationResult(
                is_valid=False,
                mrz_type=mrz_type,
                check_digits=[],
                warnings=[f"MRZ type {mrz_type.value} validation not yet supported"],
            )

    def validate_td1(self, mrz_lines: str) -> ValidationResult:
        """Validate TD1 format MRZ (ID cards, 3 lines of 30 chars).

        Args:
            mrz_lines: MRZ string with 3 lines separated by newlines.

        Returns:
            ValidationResult with check digit status for each field.
        """
        try:
            checker = TD1CodeChecker(mrz_lines)
            return self._build_validation_result(
                checker=checker,
                mrz_type=MRZType.TD1,
            )
        except Exception as e:
            return self._handle_validation_error(e, MRZType.TD1)

    def validate_td3(self, mrz_lines: str) -> ValidationResult:
        """Validate TD3 format MRZ (passports, 2 lines of 44 chars).

        Args:
            mrz_lines: MRZ string with 2 lines separated by newline.

        Returns:
            ValidationResult with check digit status for each field.
        """
        try:
            checker = TD3CodeChecker(mrz_lines)
            return self._build_validation_result(
                checker=checker,
                mrz_type=MRZType.TD3,
            )
        except Exception as e:
            return self._handle_validation_error(e, MRZType.TD3)

    def _detect_mrz_type(self, raw_mrz: str) -> MRZType:
        """Auto-detect MRZ type from string format.

        TD3 (passport): 2 lines of 44 chars = 89 chars with newline
        TD1 (ID card): 3 lines of 30 chars = 92 chars with newlines

        Args:
            raw_mrz: The MRZ string to analyze.

        Returns:
            Detected MRZType (defaults to TD3 if ambiguous).
        """
        # Count lines
        lines = raw_mrz.strip().split("\n")
        num_lines = len(lines)

        if num_lines == 3:
            return MRZType.TD1
        elif num_lines == 2:
            return MRZType.TD3
        else:
            # Check by total length
            total_len = len(raw_mrz)
            if total_len >= self.TD1_LENGTH - 2:  # Allow some tolerance
                return MRZType.TD1
            else:
                return MRZType.TD3

    def _build_validation_result(
        self,
        checker: TD1CodeChecker | TD3CodeChecker,
        mrz_type: MRZType,
    ) -> ValidationResult:
        """Build ValidationResult from mrz library checker.

        Args:
            checker: The mrz library checker instance with results.
            mrz_type: The MRZ type being validated.

        Returns:
            ValidationResult with all check digit details.
        """
        check_digits: list[CheckDigitResult] = []
        warnings: list[str] = []

        # Extract check digit results from report
        for field_name, is_valid in checker.report.fields:
            # Only include hash/check digit fields in check_digits list
            if "hash" in field_name.lower():
                friendly_name = self._FIELD_NAME_MAP.get(field_name, field_name)
                check_digits.append(
                    CheckDigitResult(
                        field_name=friendly_name,
                        is_valid=is_valid,
                        expected=None,  # mrz library doesn't expose expected values
                        actual=None,
                    )
                )

        # Add warnings from report
        if checker.report.warnings:
            warnings.extend(checker.report.warnings)

        return ValidationResult(
            is_valid=checker.result,
            mrz_type=mrz_type,
            check_digits=check_digits,
            warnings=warnings,
        )

    def _handle_validation_error(
        self, error: Exception, mrz_type: MRZType
    ) -> ValidationResult:
        """Handle validation errors gracefully.

        Args:
            error: The exception that occurred during validation.
            mrz_type: The MRZ type being validated.

        Returns:
            ValidationResult indicating failure with error details.
        """
        error_message = str(error)

        # Create a descriptive warning
        warning = f"MRZ validation failed: {error_message}"

        return ValidationResult(
            is_valid=False,
            mrz_type=mrz_type,
            check_digits=[],
            warnings=[warning],
        )
