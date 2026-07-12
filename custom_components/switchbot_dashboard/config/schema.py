"""Validation and parsing of the YAML widget configuration.

Translates the ``widgets:`` list from configuration.yaml into the
typed config dataclasses. Allowed keys and their types are derived
directly from the dataclasses, required fields come from the widget
registry — custom widgets are validated automatically.

Error messages always name widget position, type and field.
"""

from dataclasses import fields as dataclass_fields

from ..widgets.registry import get_registration, registered_types


class ConfigError(Exception):
    """Human-readable configuration error."""


# Field values with a restricted set of choices
CHOICES = {
    "mode": ("rooms", "state"),
    "unit": ("%", "l"),
}


def build_widget_configs(raw: list) -> list:
    """Builds the config dataclasses from the YAML list."""

    configs = []

    for index, item in enumerate(raw, start=1):
        configs.append(_build_one(index, item))

    return configs


def _build_one(index: int, item):

    if not isinstance(item, dict):
        raise ConfigError(
            f"Widget {index}: expected a mapping, got {type(item).__name__}"
        )

    widget_type = item.get("type")

    if not widget_type:
        raise ConfigError(f"Widget {index}: missing 'type'")

    registration = get_registration(widget_type)

    if registration is None:
        raise ConfigError(
            f"Widget {index}: unknown type '{widget_type}'. "
            f"Available: {', '.join(registered_types())}"
        )

    config_cls = registration.config_cls
    allowed = {
        field.name: field
        for field in dataclass_fields(config_cls)
    }

    prefix = f"Widget {index} ({widget_type})"

    for key in item:
        if key not in allowed:
            options = ", ".join(sorted(set(allowed) - {"type"}))
            raise ConfigError(
                f"{prefix}: unknown option '{key}'. Available: {options}"
            )

    for key in registration.required:
        if key not in item:
            raise ConfigError(f"{prefix}: missing required option '{key}'")

    kwargs = {}

    for key, value in item.items():

        if key == "type":
            continue

        kwargs[key] = _coerce(prefix, key, value, allowed[key].type)

    return config_cls(type=widget_type, **kwargs)


def _coerce(prefix: str, key: str, value, field_type):

    choices = CHOICES.get(key)

    if choices is not None and value not in choices:
        raise ConfigError(
            f"{prefix}: '{key}' must be one of "
            f"{', '.join(choices)} (got '{value}')"
        )

    type_name = str(field_type)

    if "dict" in type_name:
        if not isinstance(value, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in value.items()
        ):
            raise ConfigError(
                f"{prefix}: '{key}' must be a mapping of "
                "entity_id to name"
            )
        return value

    if type_name in ("<class 'bool'>", "bool"):
        if isinstance(value, bool):
            return value
        if str(value).lower() in ("true", "yes", "on", "1"):
            return True
        if str(value).lower() in ("false", "no", "off", "0"):
            return False
        raise ConfigError(
            f"{prefix}: '{key}' must be true or false (got '{value}')"
        )

    if type_name in ("<class 'int'>", "int"):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ConfigError(
                f"{prefix}: '{key}' must be a number (got '{value}')"
            )

    if type_name in ("<class 'float'>", "float"):
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ConfigError(
                f"{prefix}: '{key}' must be a number (got '{value}')"
            )

    if type_name in ("<class 'str'>", "str"):
        if not isinstance(value, str):
            raise ConfigError(
                f"{prefix}: '{key}' must be a string (got '{value}')"
            )
        return value

    return value
