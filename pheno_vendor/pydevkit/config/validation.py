"""Configuration validation utilities."""

from typing import Any, Callable, Dict, List, Optional, Set, Type, Union


class ValidationError(Exception):
    """Configuration validation error."""
    pass


class FieldValidator:
    """
    Field-level validator.

    Example:
        validator = FieldValidator('port', int, required=True, min_value=1, max_value=65535)
        validator.validate(8080)  # OK
        validator.validate(99999)  # Raises ValidationError
    """

    def __init__(
        self,
        name: str,
        field_type: Type,
        required: bool = False,
        default: Any = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        choices: Optional[Set[Any]] = None,
        pattern: Optional[str] = None,
        custom_validator: Optional[Callable[[Any], bool]] = None,
    ):
        """
        Initialize field validator.

        Args:
            name: Field name
            field_type: Expected type (str, int, bool, etc.)
            required: Whether field is required
            default: Default value if not provided
            min_value: Minimum numeric value
            max_value: Maximum numeric value
            min_length: Minimum string/list length
            max_length: Maximum string/list length
            choices: Set of allowed values
            pattern: Regex pattern for string values
            custom_validator: Custom validation function
        """
        self.name = name
        self.field_type = field_type
        self.required = required
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.choices = choices
        self.pattern = pattern
        self.custom_validator = custom_validator

    def validate(self, value: Any) -> Any:
        """
        Validate field value.

        Args:
            value: Value to validate

        Returns:
            Validated value (possibly with default applied)

        Raises:
            ValidationError: If validation fails
        """
        # Handle missing values
        if value is None:
            if self.required:
                raise ValidationError(f"Required field missing: {self.name}")
            return self.default

        # Type validation
        if not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Invalid type for {self.name}: expected {self.field_type.__name__}, got {type(value).__name__}"
                )

        # Numeric range validation
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(f"{self.name} must be >= {self.min_value}, got {value}")
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(f"{self.name} must be <= {self.max_value}, got {value}")

        # Length validation
        if isinstance(value, (str, list, dict)):
            length = len(value)
            if self.min_length is not None and length < self.min_length:
                raise ValidationError(f"{self.name} must have length >= {self.min_length}, got {length}")
            if self.max_length is not None and length > self.max_length:
                raise ValidationError(f"{self.name} must have length <= {self.max_length}, got {length}")

        # Choices validation
        if self.choices is not None and value not in self.choices:
            raise ValidationError(f"{self.name} must be one of {self.choices}, got {value}")

        # Pattern validation
        if self.pattern is not None and isinstance(value, str):
            import re
            if not re.match(self.pattern, value):
                raise ValidationError(f"{self.name} does not match pattern: {self.pattern}")

        # Custom validation
        if self.custom_validator is not None:
            if not self.custom_validator(value):
                raise ValidationError(f"{self.name} failed custom validation")

        return value


class ConfigSchema:
    """
    Configuration schema with validation.

    Example:
        schema = ConfigSchema()
        schema.add_field('port', int, required=True, min_value=1, max_value=65535)
        schema.add_field('host', str, default='localhost')
        schema.add_field('debug', bool, default=False)

        config = {'port': 8080}
        validated = schema.validate(config)
    """

    def __init__(self):
        """Initialize configuration schema."""
        self.fields: Dict[str, FieldValidator] = {}

    def add_field(self, name: str, *args, **kwargs) -> 'ConfigSchema':
        """
        Add field to schema.

        Args:
            name: Field name
            *args, **kwargs: Arguments for FieldValidator

        Returns:
            Self for chaining
        """
        self.fields[name] = FieldValidator(name, *args, **kwargs)
        return self

    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration against schema.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration with defaults applied

        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        errors = []

        # Validate all fields
        for field_name, validator in self.fields.items():
            try:
                value = config.get(field_name)
                validated[field_name] = validator.validate(value)
            except ValidationError as e:
                errors.append(str(e))

        # Check for unknown fields
        unknown = set(config.keys()) - set(self.fields.keys())
        if unknown:
            errors.append(f"Unknown fields: {', '.join(unknown)}")

        if errors:
            raise ValidationError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return validated

    def validate_partial(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate partial configuration (only provided fields).

        Args:
            config: Partial configuration dictionary

        Returns:
            Validated configuration

        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        errors = []

        for field_name, value in config.items():
            if field_name not in self.fields:
                errors.append(f"Unknown field: {field_name}")
                continue

            try:
                validator = self.fields[field_name]
                validated[field_name] = validator.validate(value)
            except ValidationError as e:
                errors.append(str(e))

        if errors:
            raise ValidationError(f"Validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return validated


def validate_config(config: Dict[str, Any], schema: ConfigSchema) -> Dict[str, Any]:
    """
    Validate configuration against schema.

    Args:
        config: Configuration dictionary
        schema: Configuration schema

    Returns:
        Validated configuration

    Raises:
        ValidationError: If validation fails
    """
    return schema.validate(config)


def create_schema_from_dict(schema_dict: Dict[str, Dict[str, Any]]) -> ConfigSchema:
    """
    Create ConfigSchema from dictionary definition.

    Example:
        schema_dict = {
            'port': {'type': int, 'required': True, 'min_value': 1},
            'host': {'type': str, 'default': 'localhost'},
            'debug': {'type': bool, 'default': False},
        }
        schema = create_schema_from_dict(schema_dict)

    Args:
        schema_dict: Dictionary defining schema

    Returns:
        ConfigSchema instance
    """
    schema = ConfigSchema()

    for field_name, field_def in schema_dict.items():
        field_type = field_def.pop('type')
        schema.add_field(field_name, field_type, **field_def)

    return schema
