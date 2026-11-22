"""Widget editor: forms and data for widgets configured in the UI.

Every widget is a config subentry of type ``widget`` whose data is the
same mapping as one item of the YAML ``widgets:`` list. The forms are
derived from the config dataclasses (like the YAML validation), so new
widget types get an editor without extra code.

Free of Home Assistant imports: config_flow.py turns the field
descriptions into selectors, everything here is testable on its own.
"""

from dataclasses import MISSING, dataclass, fields as dataclass_fields

from .config.schema import CHOICES, ConfigError, build_widget_configs
from .const import CONF_WIDGETS
from .widgets.registry import get_registration, registered_types

SUBENTRY_TYPE = "widget"

# not offered in the type picker (example in the docs)
HIDDEN_TYPES = {"mein_widget"}

# fields edited as YAML/JSON in the form (lists and mappings)
OBJECT_FIELDS = {"entities", "conditions", "boost", "ok_states"}

# shown first, in this order; the rest follows alphabetically
FIELD_ORDER = (
    "name", "entity", "entities", "temperature_entity", "trend_entity",
    "reference_entity", "running_entity", "done_entity", "status_entity",
    "lock_entity", "contact_entity", "level_entity", "price_entity",
    "icon", "priority", "group",
)

TYPE_LABELS = {
    "weather": "Weather",
    "entity": "Entity",
    "door": "Door",
    "window": "Window",
    "waste": "Waste",
    "calendar": "Calendar",
    "presence": "Presence",
    "fuel": "Fuel",
    "appliance": "Appliance",
    "solar": "Solar",
    "battery": "Battery",
    "ev": "EV",
    "alert": "Alert",
    "threshold": "Threshold",
    "status": "Status",
    "wallbox": "Wallbox",
    "media": "Media",
}


@dataclass(slots=True)
class FieldSpec:
    name: str
    # entity, text, int, float, bool, select, object
    kind: str
    required: bool
    default: object = None
    choices: tuple = ()


def widget_types() -> list[str]:
    return [t for t in registered_types() if t not in HIDDEN_TYPES]


def describe_fields(widget_type: str) -> list[FieldSpec]:
    """The form fields of one widget type."""

    registration = get_registration(widget_type)

    if registration is None:
        raise ConfigError(f"unknown widget type '{widget_type}'")

    specs = []

    for field in dataclass_fields(registration.config_cls):

        if field.name == "type":
            continue

        type_name = str(field.type).replace(" | None", "")
        default = None if field.default is MISSING else field.default

        # "" means "the widget's own default" - no value to suggest
        if default == "":
            default = None

        if field.name in OBJECT_FIELDS:
            kind = "object"
        elif field.name in CHOICES:
            kind = "select"
        elif type_name in ("<class 'bool'>", "bool"):
            kind = "bool"
        elif type_name in ("<class 'int'>", "int"):
            kind = "int"
        elif type_name in ("<class 'float'>", "float"):
            kind = "float"
        elif field.name == "entity" or field.name.endswith("_entity"):
            kind = "entity"
        else:
            kind = "text"

        specs.append(FieldSpec(
            name=field.name,
            kind=kind,
            required=field.name in registration.required,
            default=default,
            choices=tuple(CHOICES.get(field.name, ())),
        ))

    def order(spec):
        if spec.name in FIELD_ORDER:
            return (0, FIELD_ORDER.index(spec.name))
        return (1, spec.name)

    return sorted(specs, key=order)


def clean_input(widget_type: str, user_input: dict) -> dict:
    """Form values as widget data: empty values dropped, ints as int."""

    specs = {spec.name: spec for spec in describe_fields(widget_type)}
    data = {"type": widget_type}

    for key, value in (user_input or {}).items():

        if key not in specs:
            continue

        if value is None or value == "" or value == [] or value == {}:
            continue

        if specs[key].kind == "int" and isinstance(value, float):
            value = int(value)

        data[key] = value

    return data


def validate_widget(data: dict) -> None:
    """Raises ConfigError with a readable message."""

    build_widget_configs([data])


def widget_title(data: dict) -> str:
    """Name of the widget in the list of the integration."""

    label = TYPE_LABELS.get(data.get("type"), str(data.get("type", "?")))

    detail = data.get("name")

    if not detail:
        for key in ("entity", "temperature_entity", "running_entity",
                    "status_entity", "lock_entity", "level_entity"):
            if data.get(key):
                detail = data[key]
                break

    if not detail and isinstance(data.get("entities"), dict):
        detail = ", ".join(data["entities"].values())

    return f"{label}: {detail}" if detail else label


def import_payload(conf: dict, option_keys) -> dict:
    """Turns a validated YAML block into config entry data.

    Returns ``data`` (credentials), ``options`` and ``widgets`` (one
    mapping per widget, in YAML order).
    """

    from .const import CONF_DEVICE_ID, CONF_SECRET, CONF_TOKEN

    return {
        "data": {
            key: str(conf[key])
            for key in (CONF_TOKEN, CONF_SECRET, CONF_DEVICE_ID)
        },
        "options": {
            key: conf[key] for key in option_keys if key in conf
        },
        "widgets": [dict(item) for item in conf.get(CONF_WIDGETS) or []],
    }
