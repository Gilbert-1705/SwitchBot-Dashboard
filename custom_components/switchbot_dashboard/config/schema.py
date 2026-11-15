"""Validation and parsing of the YAML widget configuration.

Translates the ``widgets:`` list from configuration.yaml into the
typed config dataclasses. Allowed keys and their types are derived
directly from the dataclasses, required fields come from the widget
registry — custom widgets are validated automatically.

Error messages always name widget position, type and field.
"""

from dataclasses import fields as dataclass_fields

from ..text import state_text
from ..widgets.registry import get_registration, registered_types


class ConfigError(Exception):
    """Human-readable configuration error."""


# Field values with a restricted set of choices
CHOICES = {
    "mode": ("rooms", "state"),
    "unit": ("%", "l"),
    "show": ("title", "artist", "both"),
}

# Allowed keys inside an alert condition (see widgets/alert.py)
CONDITION_KEYS = (
    "entity", "state", "not_state", "above", "below", "duration",
)


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

    config = config_cls(type=widget_type, **kwargs)

    if registration.validator is not None:
        problem = registration.validator(config)

        if problem:
            raise ConfigError(f"{prefix}: {problem}")

    return config


def _coerce(prefix: str, key: str, value, field_type):

    if key == "conditions":
        return _validate_conditions(prefix, value)

    if key == "boost":
        return _validate_boost(prefix, value)

    choices = CHOICES.get(key)

    if choices is not None and value not in choices:
        raise ConfigError(
            f"{prefix}: '{key}' must be one of "
            f"{', '.join(choices)} (got '{value}')"
        )

    # "float | None" is validated like "float"
    type_name = str(field_type).replace(" | None", "")

    if key == "ok_states":
        if not isinstance(value, list) or not all(
            isinstance(state, (str, bool, int)) for state in value
        ):
            raise ConfigError(
                f"{prefix}: '{key}' must be a list of states"
            )
        return [state_text(state) for state in value]

    if key == "entities" and "list" in type_name:
        if not isinstance(value, list) or not value or not all(
            isinstance(entity, str) for entity in value
        ):
            raise ConfigError(
                f"{prefix}: '{key}' must be a list of entity IDs"
            )
        return value

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


def _validate_boost(prefix: str, value):

    if not isinstance(value, list) or not value:
        raise ConfigError(
            f"{prefix}: 'boost' must be a non-empty list"
        )

    for index, window in enumerate(value, start=1):

        where = f"{prefix}, boost {index}"

        if not isinstance(window, dict):
            raise ConfigError(f"{where}: expected a mapping")

        for key in window:
            if key not in ("between", "add"):
                raise ConfigError(
                    f"{where}: unknown option '{key}'. "
                    "Available: between, add"
                )

        between = window.get("between")

        if (
            not isinstance(between, (list, tuple))
            or len(between) != 2
        ):
            raise ConfigError(
                f"{where}: 'between' must be a list of two times, "
                "e.g. [\"06:00\", \"09:00\"]"
            )

        for moment in between:
            try:
                hours, minutes = str(moment).split(":")
                if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                    raise ValueError
            except ValueError:
                raise ConfigError(
                    f"{where}: invalid time '{moment}' (use HH:MM)"
                )

        try:
            int(window.get("add"))
        except (ValueError, TypeError):
            raise ConfigError(
                f"{where}: 'add' must be a number "
                f"(got '{window.get('add')}')"
            )

    return value


def _validate_conditions(prefix: str, value):

    if not isinstance(value, list) or not value:
        raise ConfigError(
            f"{prefix}: 'conditions' must be a non-empty list"
        )

    for index, condition in enumerate(value, start=1):

        where = f"{prefix}, condition {index}"

        if not isinstance(condition, dict):
            raise ConfigError(f"{where}: expected a mapping")

        for key in condition:
            if key not in CONDITION_KEYS:
                raise ConfigError(
                    f"{where}: unknown option '{key}'. "
                    f"Available: {', '.join(CONDITION_KEYS)}"
                )

        if "entity" not in condition:
            raise ConfigError(f"{where}: missing 'entity'")

        if len(condition) < 2:
            raise ConfigError(
                f"{where}: needs at least one criterion "
                "(state, not_state, above, below, duration)"
            )

        for key in ("above", "below", "duration"):
            if key in condition:
                try:
                    float(condition[key])
                except (ValueError, TypeError):
                    raise ConfigError(
                        f"{where}: '{key}' must be a number "
                        f"(got '{condition[key]}')"
                    )

    return value
