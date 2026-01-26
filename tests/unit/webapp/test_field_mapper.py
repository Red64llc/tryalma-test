"""Tests for field mapper module.

Task 3.1, 3.2, 3.3: Field mapping for passport and G-28 data, plus merge logic.
Requirements: 5.1, 5.2, 5.3, 5.4
"""

from datetime import date
from pathlib import Path

import pytest

from tryalma.passport.models import PassportData
from tryalma.webapp.field_mapper import FieldMapper, MappedField


class TestMappedField:
    """Tests for MappedField dataclass."""

    def test_mapped_field_creation(self):
        """MappedField stores all field metadata."""
        field = MappedField(
            field_id="applicant_surname",
            value="SMITH",
            confidence=0.95,
            source="passport",
            auto_populated=True,
        )

        assert field.field_id == "applicant_surname"
        assert field.value == "SMITH"
        assert field.confidence == 0.95
        assert field.source == "passport"
        assert field.auto_populated is True

    def test_mapped_field_with_none_value(self):
        """MappedField accepts None as value."""
        field = MappedField(
            field_id="applicant_middle_name",
            value=None,
            confidence=None,
            source="passport",
            auto_populated=True,
        )

        assert field.value is None
        assert field.confidence is None


class TestFieldMapperPassport:
    """Tests for passport data mapping (Task 3.1)."""

    @pytest.fixture
    def mapper(self):
        """Create FieldMapper instance."""
        return FieldMapper()

    @pytest.fixture
    def sample_passport_data(self):
        """Create sample PassportData for testing."""
        return PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="SMITH",
            given_names="JOHN WILLIAM",
            date_of_birth=date(1985, 3, 15),
            nationality="USA",
            passport_number="123456789",
            expiry_date=date(2028, 3, 14),
            sex="M",
            confidence=0.92,
        )

    def test_map_passport_surname(self, mapper, sample_passport_data):
        """Maps passport surname to applicant_surname field."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "applicant_surname" in result
        assert result["applicant_surname"].value == "SMITH"
        assert result["applicant_surname"].source == "passport"
        assert result["applicant_surname"].auto_populated is True

    def test_map_passport_given_names(self, mapper, sample_passport_data):
        """Maps passport given_names to applicant_given_names field."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "applicant_given_names" in result
        assert result["applicant_given_names"].value == "JOHN WILLIAM"
        assert result["applicant_given_names"].source == "passport"

    def test_map_passport_date_of_birth(self, mapper, sample_passport_data):
        """Maps passport date_of_birth to applicant_dob field with ISO format."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "applicant_dob" in result
        assert result["applicant_dob"].value == "1985-03-15"
        assert result["applicant_dob"].source == "passport"

    def test_map_passport_number(self, mapper, sample_passport_data):
        """Maps passport_number directly."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "passport_number" in result
        assert result["passport_number"].value == "123456789"

    def test_map_passport_nationality(self, mapper, sample_passport_data):
        """Maps nationality directly."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "nationality" in result
        assert result["nationality"].value == "USA"

    def test_map_passport_expiry_date(self, mapper, sample_passport_data):
        """Maps expiry_date to passport_expiry field with ISO format."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "passport_expiry" in result
        assert result["passport_expiry"].value == "2028-03-14"

    def test_map_passport_sex(self, mapper, sample_passport_data):
        """Maps sex to applicant_sex field."""
        result = mapper.map_passport_data(sample_passport_data)

        assert "applicant_sex" in result
        assert result["applicant_sex"].value == "M"

    def test_map_passport_preserves_confidence(self, mapper, sample_passport_data):
        """Preserves confidence scores for display purposes."""
        result = mapper.map_passport_data(sample_passport_data)

        # All fields should have the overall confidence from PassportData
        for field in result.values():
            assert field.confidence == 0.92

    def test_map_passport_with_missing_fields(self, mapper):
        """Handles passport data with missing optional fields."""
        partial_data = PassportData(
            source_file=Path("/test/passport.jpg"),
            surname="DOE",
            given_names=None,
            date_of_birth=None,
            nationality="GBR",
            passport_number="987654321",
            expiry_date=None,
            sex=None,
            confidence=0.75,
        )

        result = mapper.map_passport_data(partial_data)

        assert result["applicant_surname"].value == "DOE"
        assert result["applicant_given_names"].value is None
        assert result["applicant_dob"].value is None
        assert result["nationality"].value == "GBR"
        assert result["passport_expiry"].value is None
        assert result["applicant_sex"].value is None

    def test_map_passport_returns_all_expected_fields(self, mapper, sample_passport_data):
        """Returns all expected form fields from passport mapping."""
        result = mapper.map_passport_data(sample_passport_data)

        expected_fields = {
            "applicant_surname",
            "applicant_given_names",
            "applicant_dob",
            "passport_number",
            "nationality",
            "passport_expiry",
            "applicant_sex",
        }

        assert set(result.keys()) == expected_fields


class TestFieldMapperG28:
    """Tests for G-28 form data mapping (Task 3.2)."""

    @pytest.fixture
    def mapper(self):
        """Create FieldMapper instance."""
        return FieldMapper()

    @pytest.fixture
    def sample_g28_data(self):
        """Create sample G28FormData for testing."""
        from tryalma.g28.models import (
            Address,
            AttorneyInfo,
            ClientInfo,
            ExtractedField,
            G28FormData,
        )

        return G28FormData(
            source_file="/test/g28.pdf",
            extraction_timestamp="2024-01-15T10:00:00Z",
            overall_confidence=0.88,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.95),
                given_name=ExtractedField(value="SARAH", confidence=0.93),
                middle_name=ExtractedField(value="M", confidence=0.90),
                email_address=ExtractedField(value="sjones@lawfirm.com", confidence=0.91),
                daytime_telephone=ExtractedField(value="555-123-4567", confidence=0.89),
                address=Address(
                    street_number_and_name="123 Law Street",
                    city_or_town="Legal City",
                    state="CA",
                    zip_code="90210",
                ),
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField(value="DOE", confidence=0.97),
                given_name=ExtractedField(value="JANE", confidence=0.96),
                alien_registration_number=ExtractedField(value="123456789", confidence=0.94),
                email_address=ExtractedField(value="jane.doe@email.com", confidence=0.92),
                daytime_telephone=ExtractedField(value="555-987-6543", confidence=0.90),
            ),
        )

    def test_map_g28_attorney_surname(self, mapper, sample_g28_data):
        """Maps attorney family_name to attorney_surname field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "attorney_surname" in result
        assert result["attorney_surname"].value == "JONES"
        assert result["attorney_surname"].source == "g28"
        assert result["attorney_surname"].auto_populated is True

    def test_map_g28_attorney_given_names(self, mapper, sample_g28_data):
        """Maps attorney given_name to attorney_given_names field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "attorney_given_names" in result
        assert result["attorney_given_names"].value == "SARAH"
        assert result["attorney_given_names"].source == "g28"

    def test_map_g28_attorney_email(self, mapper, sample_g28_data):
        """Maps attorney email_address to attorney_email field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "attorney_email" in result
        assert result["attorney_email"].value == "sjones@lawfirm.com"

    def test_map_g28_attorney_phone(self, mapper, sample_g28_data):
        """Maps attorney daytime_telephone to attorney_phone field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "attorney_phone" in result
        assert result["attorney_phone"].value == "555-123-4567"

    def test_map_g28_applicant_surname(self, mapper, sample_g28_data):
        """Maps client family_name to applicant_surname field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "applicant_surname" in result
        assert result["applicant_surname"].value == "DOE"
        assert result["applicant_surname"].source == "g28"

    def test_map_g28_applicant_given_names(self, mapper, sample_g28_data):
        """Maps client given_name to applicant_given_names field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "applicant_given_names" in result
        assert result["applicant_given_names"].value == "JANE"

    def test_map_g28_a_number(self, mapper, sample_g28_data):
        """Maps client alien_registration_number to a_number field."""
        result = mapper.map_g28_data(sample_g28_data)

        assert "a_number" in result
        assert result["a_number"].value == "123456789"

    def test_map_g28_preserves_field_confidence(self, mapper, sample_g28_data):
        """Preserves individual field confidence scores from G-28 extraction."""
        result = mapper.map_g28_data(sample_g28_data)

        # G-28 has per-field confidence scores
        assert result["attorney_surname"].confidence == 0.95
        assert result["applicant_surname"].confidence == 0.97
        assert result["attorney_email"].confidence == 0.91

    def test_map_g28_with_missing_attorney_info(self, mapper):
        """Handles G-28 data with missing attorney information."""
        from tryalma.g28.models import (
            ClientInfo,
            ExtractedField,
            G28FormData,
        )

        partial_data = G28FormData(
            source_file="/test/g28.pdf",
            extraction_timestamp="2024-01-15T10:00:00Z",
            overall_confidence=0.75,
            part1_attorney_info=None,
            part3_client_info=ClientInfo(
                family_name=ExtractedField(value="SMITH", confidence=0.90),
                given_name=ExtractedField(value="JOHN", confidence=0.88),
            ),
        )

        result = mapper.map_g28_data(partial_data)

        # Attorney fields should be None but present
        assert result["attorney_surname"].value is None
        assert result["attorney_given_names"].value is None
        assert result["attorney_email"].value is None
        # Client fields should be populated
        assert result["applicant_surname"].value == "SMITH"
        assert result["applicant_given_names"].value == "JOHN"

    def test_map_g28_with_missing_client_info(self, mapper):
        """Handles G-28 data with missing client information."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ExtractedField,
            G28FormData,
        )

        partial_data = G28FormData(
            source_file="/test/g28.pdf",
            extraction_timestamp="2024-01-15T10:00:00Z",
            overall_confidence=0.75,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.90),
                given_name=ExtractedField(value="SARAH", confidence=0.88),
            ),
            part3_client_info=None,
        )

        result = mapper.map_g28_data(partial_data)

        # Attorney fields should be populated
        assert result["attorney_surname"].value == "JONES"
        # Client fields should be None but present
        assert result["applicant_surname"].value is None
        assert result["applicant_given_names"].value is None

    def test_map_g28_with_partial_extracted_fields(self, mapper):
        """Handles G-28 data with some ExtractedField values being None."""
        from tryalma.g28.models import (
            AttorneyInfo,
            ClientInfo,
            ExtractedField,
            G28FormData,
        )

        partial_data = G28FormData(
            source_file="/test/g28.pdf",
            extraction_timestamp="2024-01-15T10:00:00Z",
            overall_confidence=0.80,
            part1_attorney_info=AttorneyInfo(
                family_name=ExtractedField(value="JONES", confidence=0.90),
                given_name=None,  # Completely missing
                email_address=ExtractedField(value=None, confidence=0.50),  # Extracted but empty
            ),
            part3_client_info=ClientInfo(
                family_name=ExtractedField(value="DOE", confidence=0.85),
            ),
        )

        result = mapper.map_g28_data(partial_data)

        assert result["attorney_surname"].value == "JONES"
        assert result["attorney_given_names"].value is None
        assert result["attorney_email"].value is None
        assert result["applicant_surname"].value == "DOE"

    def test_map_g28_returns_all_expected_fields(self, mapper, sample_g28_data):
        """Returns all expected form fields from G-28 mapping."""
        result = mapper.map_g28_data(sample_g28_data)

        expected_fields = {
            "attorney_surname",
            "attorney_given_names",
            "attorney_email",
            "attorney_phone",
            "applicant_surname",
            "applicant_given_names",
            "a_number",
        }

        assert set(result.keys()) == expected_fields


class TestFieldMapperMerge:
    """Tests for field merge logic (Task 3.3)."""

    @pytest.fixture
    def mapper(self):
        """Create FieldMapper instance."""
        return FieldMapper()

    def test_merge_adds_new_fields(self, mapper):
        """Merge adds new fields from new extraction to existing."""
        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.95,
                source="passport",
                auto_populated=True,
            ),
        }
        new = {
            "attorney_surname": MappedField(
                field_id="attorney_surname",
                value="JONES",
                confidence=0.90,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(existing, new)

        assert "applicant_surname" in result
        assert "attorney_surname" in result
        assert result["applicant_surname"].value == "SMITH"
        assert result["attorney_surname"].value == "JONES"

    def test_merge_preserves_existing_populated_fields(self, mapper):
        """Merge does not overwrite existing populated fields (Requirement 5.4)."""
        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.95,
                source="passport",
                auto_populated=True,
            ),
        }
        new = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="DOE",
                confidence=0.97,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(existing, new)

        # Original value should be preserved
        assert result["applicant_surname"].value == "SMITH"
        assert result["applicant_surname"].source == "passport"

    def test_merge_fills_empty_existing_fields(self, mapper):
        """Merge fills in fields that were None in existing."""
        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value=None,
                confidence=None,
                source="passport",
                auto_populated=True,
            ),
        }
        new = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="DOE",
                confidence=0.97,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(existing, new)

        # New value should replace the None value
        assert result["applicant_surname"].value == "DOE"
        assert result["applicant_surname"].source == "g28"

    def test_merge_handles_empty_existing(self, mapper):
        """Merge works with empty existing dictionary."""
        existing: dict[str, MappedField] = {}
        new = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="DOE",
                confidence=0.97,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(existing, new)

        assert result["applicant_surname"].value == "DOE"

    def test_merge_handles_empty_new(self, mapper):
        """Merge works with empty new dictionary."""
        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.95,
                source="passport",
                auto_populated=True,
            ),
        }
        new: dict[str, MappedField] = {}

        result = mapper.merge_fields(existing, new)

        assert result["applicant_surname"].value == "SMITH"

    def test_merge_handles_conflict_gracefully(self, mapper):
        """Merge handles passport-g28 conflicts by preserving first-in values."""
        # Passport data comes first
        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="PASSPORT_NAME",
                confidence=0.90,
                source="passport",
                auto_populated=True,
            ),
            "applicant_given_names": MappedField(
                field_id="applicant_given_names",
                value="JOHN",
                confidence=0.88,
                source="passport",
                auto_populated=True,
            ),
        }
        # G-28 data comes second
        new = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="G28_NAME",
                confidence=0.95,
                source="g28",
                auto_populated=True,
            ),
            "applicant_given_names": MappedField(
                field_id="applicant_given_names",
                value="JANE",
                confidence=0.93,
                source="g28",
                auto_populated=True,
            ),
            "a_number": MappedField(
                field_id="a_number",
                value="123456789",
                confidence=0.97,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(existing, new)

        # Passport values preserved (first-in wins)
        assert result["applicant_surname"].value == "PASSPORT_NAME"
        assert result["applicant_given_names"].value == "JOHN"
        # New field from G-28 added
        assert result["a_number"].value == "123456789"

    def test_merge_preserves_metadata(self, mapper):
        """Merge preserves all metadata (confidence, source, auto_populated)."""
        existing = {
            "passport_number": MappedField(
                field_id="passport_number",
                value="123456789",
                confidence=0.99,
                source="passport",
                auto_populated=True,
            ),
        }
        new = {
            "attorney_email": MappedField(
                field_id="attorney_email",
                value="attorney@law.com",
                confidence=0.91,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(existing, new)

        assert result["passport_number"].confidence == 0.99
        assert result["passport_number"].source == "passport"
        assert result["attorney_email"].confidence == 0.91
        assert result["attorney_email"].source == "g28"

    def test_merge_does_not_mutate_inputs(self, mapper):
        """Merge does not modify input dictionaries."""
        existing = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.95,
                source="passport",
                auto_populated=True,
            ),
        }
        new = {
            "attorney_surname": MappedField(
                field_id="attorney_surname",
                value="JONES",
                confidence=0.90,
                source="g28",
                auto_populated=True,
            ),
        }

        # Copy keys before merge
        existing_keys_before = set(existing.keys())
        new_keys_before = set(new.keys())

        result = mapper.merge_fields(existing, new)

        # Original dictionaries should be unchanged
        assert set(existing.keys()) == existing_keys_before
        assert set(new.keys()) == new_keys_before
        # Result should have both keys
        assert "attorney_surname" in result

    def test_merge_multiple_documents_scenario(self, mapper):
        """Full scenario: passport uploaded first, then G-28."""
        # Simulate passport upload
        passport_fields = {
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="SMITH",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
            "applicant_given_names": MappedField(
                field_id="applicant_given_names",
                value="JOHN WILLIAM",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
            "applicant_dob": MappedField(
                field_id="applicant_dob",
                value="1985-03-15",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
            "passport_number": MappedField(
                field_id="passport_number",
                value="123456789",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
            "nationality": MappedField(
                field_id="nationality",
                value="USA",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
            "passport_expiry": MappedField(
                field_id="passport_expiry",
                value="2028-03-14",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
            "applicant_sex": MappedField(
                field_id="applicant_sex",
                value="M",
                confidence=0.92,
                source="passport",
                auto_populated=True,
            ),
        }

        # Simulate G-28 upload
        g28_fields = {
            "attorney_surname": MappedField(
                field_id="attorney_surname",
                value="JONES",
                confidence=0.95,
                source="g28",
                auto_populated=True,
            ),
            "attorney_given_names": MappedField(
                field_id="attorney_given_names",
                value="SARAH",
                confidence=0.93,
                source="g28",
                auto_populated=True,
            ),
            "attorney_email": MappedField(
                field_id="attorney_email",
                value="sjones@law.com",
                confidence=0.91,
                source="g28",
                auto_populated=True,
            ),
            "attorney_phone": MappedField(
                field_id="attorney_phone",
                value="555-123-4567",
                confidence=0.89,
                source="g28",
                auto_populated=True,
            ),
            # G-28 also has applicant info - should NOT overwrite passport data
            "applicant_surname": MappedField(
                field_id="applicant_surname",
                value="DIFFERENT_NAME",
                confidence=0.97,
                source="g28",
                auto_populated=True,
            ),
            "applicant_given_names": MappedField(
                field_id="applicant_given_names",
                value="DIFFERENT_GIVEN",
                confidence=0.96,
                source="g28",
                auto_populated=True,
            ),
            "a_number": MappedField(
                field_id="a_number",
                value="A123456789",
                confidence=0.94,
                source="g28",
                auto_populated=True,
            ),
        }

        result = mapper.merge_fields(passport_fields, g28_fields)

        # Passport data preserved
        assert result["applicant_surname"].value == "SMITH"
        assert result["applicant_surname"].source == "passport"
        assert result["applicant_given_names"].value == "JOHN WILLIAM"
        assert result["passport_number"].value == "123456789"
        assert result["nationality"].value == "USA"

        # G-28 attorney data added
        assert result["attorney_surname"].value == "JONES"
        assert result["attorney_email"].value == "sjones@law.com"
        assert result["a_number"].value == "A123456789"

        # All expected fields present
        expected_merge_fields = {
            "applicant_surname",
            "applicant_given_names",
            "applicant_dob",
            "passport_number",
            "nationality",
            "passport_expiry",
            "applicant_sex",
            "attorney_surname",
            "attorney_given_names",
            "attorney_email",
            "attorney_phone",
            "a_number",
        }
        assert set(result.keys()) == expected_merge_fields
