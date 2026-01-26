"""Form populator module for automated web form population."""

from tryalma.form_populator.exceptions import (
    FormPopulationError,
    NavigationError,
    FormNotFoundError,
    BrowserError,
    PageNavigationError,
)
from tryalma.form_populator.browser_controller import BrowserController
from tryalma.form_populator.field_mapping_config import (
    FieldType,
    FieldMapping,
    FieldMappingConfig,
    FORM_FIELD_MAPPINGS,
)

__all__ = [
    "FormPopulationError",
    "NavigationError",
    "FormNotFoundError",
    "BrowserError",
    "PageNavigationError",
    "BrowserController",
    "FieldType",
    "FieldMapping",
    "FieldMappingConfig",
    "FORM_FIELD_MAPPINGS",
]
