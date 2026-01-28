"""Unit tests for cross-check configuration types.

Task 1.2: Test configuration and exception types.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest


class TestConfidenceConfig:
    """Tests for ConfidenceConfig dataclass."""

    def test_confidence_config_has_agreement_confidence(self):
        """ConfidenceConfig should have agreement confidence value."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig()

        assert config.agreement_confidence == 1.0

    def test_confidence_config_has_disagreement_confidence(self):
        """ConfidenceConfig should have disagreement base confidence value."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig()

        assert config.disagreement_base_confidence == 0.4

    def test_confidence_config_has_single_source_mrz_confidence(self):
        """ConfidenceConfig should have MRZ single-source confidence."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig()

        assert config.single_source_mrz_confidence == 0.7

    def test_confidence_config_has_single_source_vlm_confidence(self):
        """ConfidenceConfig should have VLM single-source confidence."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig()

        assert config.single_source_vlm_confidence == 0.6

    def test_confidence_config_has_critical_field_weight(self):
        """ConfidenceConfig should have critical field weight."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig()

        assert config.critical_field_weight == 2.0

    def test_confidence_config_has_standard_field_weight(self):
        """ConfidenceConfig should have standard field weight."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig()

        assert config.standard_field_weight == 1.0

    def test_confidence_config_allows_custom_values(self):
        """ConfidenceConfig should allow customization."""
        from tryalma.crosscheck.config import ConfidenceConfig

        config = ConfidenceConfig(
            agreement_confidence=0.95,
            disagreement_base_confidence=0.5,
            single_source_mrz_confidence=0.8,
            single_source_vlm_confidence=0.65,
            critical_field_weight=3.0,
            standard_field_weight=1.5,
        )

        assert config.agreement_confidence == 0.95
        assert config.disagreement_base_confidence == 0.5
        assert config.single_source_mrz_confidence == 0.8
        assert config.single_source_vlm_confidence == 0.65
        assert config.critical_field_weight == 3.0
        assert config.standard_field_weight == 1.5


class TestCrossCheckConfig:
    """Tests for CrossCheckConfig dataclass."""

    def test_crosscheck_config_accepts_hf_token(self):
        """CrossCheckConfig should accept HF token. (Requirement 7.1)"""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig(hf_token="hf_test_token_123")

        assert config.hf_token == "hf_test_token_123"

    def test_crosscheck_config_hf_token_defaults_to_none(self):
        """CrossCheckConfig HF token should default to None."""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig()

        assert config.hf_token is None

    def test_crosscheck_config_has_model_id(self):
        """CrossCheckConfig should have VLM model ID."""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig()

        assert config.vlm_model == "Qwen/Qwen2-VL-7B-Instruct"

    def test_crosscheck_config_allows_custom_model(self):
        """CrossCheckConfig should allow custom model ID."""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig(vlm_model="Qwen/Qwen2-VL-72B-Instruct")

        assert config.vlm_model == "Qwen/Qwen2-VL-72B-Instruct"

    def test_crosscheck_config_has_mrz_timeout(self):
        """CrossCheckConfig should have MRZ timeout. (Requirement 7.2)"""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig()

        assert config.mrz_timeout_seconds == 30.0

    def test_crosscheck_config_has_vlm_timeout(self):
        """CrossCheckConfig should have VLM timeout. (Requirement 7.2)"""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig()

        assert config.vlm_timeout_seconds == 60.0

    def test_crosscheck_config_allows_custom_timeouts(self):
        """CrossCheckConfig should allow custom timeout values."""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig(
            mrz_timeout_seconds=15.0,
            vlm_timeout_seconds=90.0,
        )

        assert config.mrz_timeout_seconds == 15.0
        assert config.vlm_timeout_seconds == 90.0

    def test_crosscheck_config_has_confidence_thresholds(self):
        """CrossCheckConfig should have confidence thresholds. (Requirement 7.3)"""
        from tryalma.crosscheck.config import ConfidenceConfig, CrossCheckConfig

        config = CrossCheckConfig()

        assert isinstance(config.confidence_config, ConfidenceConfig)

    def test_crosscheck_config_allows_custom_confidence_config(self):
        """CrossCheckConfig should allow custom confidence configuration."""
        from tryalma.crosscheck.config import ConfidenceConfig, CrossCheckConfig

        custom_confidence = ConfidenceConfig(agreement_confidence=0.95)

        config = CrossCheckConfig(confidence_config=custom_confidence)

        assert config.confidence_config.agreement_confidence == 0.95

    def test_crosscheck_config_has_sensible_defaults(self):
        """CrossCheckConfig should have sensible defaults. (Requirement 7.4)"""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig()

        assert config.hf_token is None
        assert config.vlm_model == "Qwen/Qwen2-VL-7B-Instruct"
        assert config.mrz_timeout_seconds == 30.0
        assert config.vlm_timeout_seconds == 60.0
        assert config.confidence_config is not None

    def test_crosscheck_config_validate_rejects_zero_mrz_timeout(self):
        """CrossCheckConfig.validate() should reject zero MRZ timeout."""
        from tryalma.crosscheck.config import CrossCheckConfig
        from tryalma.crosscheck.exceptions import ConfigurationError

        config = CrossCheckConfig(mrz_timeout_seconds=0)

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "mrz_timeout_seconds" in str(exc_info.value).lower()
        assert "positive" in str(exc_info.value).lower()

    def test_crosscheck_config_validate_rejects_negative_mrz_timeout(self):
        """CrossCheckConfig.validate() should reject negative MRZ timeout."""
        from tryalma.crosscheck.config import CrossCheckConfig
        from tryalma.crosscheck.exceptions import ConfigurationError

        config = CrossCheckConfig(mrz_timeout_seconds=-5.0)

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "mrz_timeout_seconds" in str(exc_info.value).lower()

    def test_crosscheck_config_validate_rejects_zero_vlm_timeout(self):
        """CrossCheckConfig.validate() should reject zero VLM timeout."""
        from tryalma.crosscheck.config import CrossCheckConfig
        from tryalma.crosscheck.exceptions import ConfigurationError

        config = CrossCheckConfig(vlm_timeout_seconds=0)

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "vlm_timeout_seconds" in str(exc_info.value).lower()
        assert "positive" in str(exc_info.value).lower()

    def test_crosscheck_config_validate_rejects_negative_vlm_timeout(self):
        """CrossCheckConfig.validate() should reject negative VLM timeout."""
        from tryalma.crosscheck.config import CrossCheckConfig
        from tryalma.crosscheck.exceptions import ConfigurationError

        config = CrossCheckConfig(vlm_timeout_seconds=-10.0)

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "vlm_timeout_seconds" in str(exc_info.value).lower()

    def test_crosscheck_config_validate_passes_for_valid_config(self):
        """CrossCheckConfig.validate() should pass for valid configuration."""
        from tryalma.crosscheck.config import CrossCheckConfig

        config = CrossCheckConfig(
            mrz_timeout_seconds=30.0,
            vlm_timeout_seconds=60.0,
        )

        # Should not raise
        config.validate()
