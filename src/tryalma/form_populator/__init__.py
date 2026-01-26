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
from tryalma.form_populator.models import (
    FieldStatus,
    FieldResult,
)
from tryalma.form_populator.field_handlers import (
    TextFieldConfig,
    TextFieldHandler,
    SelectStrategy,
    SelectFieldHandler,
    CheckboxHandler,
    RadioHandler,
    DateFormat,
    DateFieldHandler,
)

__all__ = [
    # Exceptions
    "FormPopulationError",
    "NavigationError",
    "FormNotFoundError",
    "BrowserError",
    "PageNavigationError",
    # Browser
    "BrowserController",
    # Field Mapping
    "FieldType",
    "FieldMapping",
    "FieldMappingConfig",
    "FORM_FIELD_MAPPINGS",
    # Models
    "FieldStatus",
    "FieldResult",
    # Field Handlers
    "TextFieldConfig",
    "TextFieldHandler",
    "SelectStrategy",
    "SelectFieldHandler",
    "CheckboxHandler",
    "RadioHandler",
    "DateFormat",
    "DateFieldHandler",
]
