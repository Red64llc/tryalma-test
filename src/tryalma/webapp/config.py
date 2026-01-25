"""Configuration classes for Flask application.

Provides configuration for development, testing, and production environments
following the Flask application factory pattern.
"""

import os


class Config:
    """Base configuration with common settings."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    DEBUG: bool = False
    TESTING: bool = False

    # File upload settings
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB

    # CSRF protection (Flask-WTF)
    WTF_CSRF_ENABLED: bool = True


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""

    DEBUG: bool = True


class ProductionConfig(Config):
    """Production configuration with strict security settings."""

    DEBUG: bool = False

    @property
    def SECRET_KEY(self) -> str:  # type: ignore[override]
        """Require SECRET_KEY from environment in production."""
        key = os.environ.get("SECRET_KEY")
        if not key:
            raise ValueError("SECRET_KEY environment variable is required in production")
        return key


class TestingConfig(Config):
    """Testing configuration with CSRF disabled for test convenience."""

    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False
    SECRET_KEY: str = "test-secret-key"


# Configuration mapping
config: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
