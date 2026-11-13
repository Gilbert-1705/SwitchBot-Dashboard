"""Widget registry: connects widget types to classes and configs.

Custom widgets can be registered from outside:

    from custom_components.switchbot_dashboard.widgets.registry import (
        register_widget_type,
    )

    register_widget_type("mein_widget", MeinWidget, MeinWidgetConfig)

Afterwards the type is usable in the configuration (Python and
YAML). See docs/configuration.md.
"""

from dataclasses import dataclass

from .alert import AlertWidget
from .appliance import ApplianceWidget
from .battery import BatteryWidget
from .calendar import CalendarWidget
from .config_models import (
    AlertWidgetConfig,
    ApplianceWidgetConfig,
    BatteryWidgetConfig,
    CalendarWidgetConfig,
    DoorWidgetConfig,
    EntityWidgetConfig,
    EvWidgetConfig,
    FuelWidgetConfig,
    PresenceWidgetConfig,
    SolarWidgetConfig,
    StatusWidgetConfig,
    ThresholdWidgetConfig,
    WallboxWidgetConfig,
    WasteWidgetConfig,
    WeatherWidgetConfig,
    WidgetConfig,
    WindowWidgetConfig,
)
from .door import DoorWidget
from .entity import EntityWidget
from .ev import EvWidget
from .fuel import FuelWidget
from .presence import PresenceWidget
from .solar import SolarWidget
from .status import StatusWidget
from .threshold import ThresholdWidget
from .wallbox import WallboxWidget
from .waste import WasteWidget
from .weather import WeatherWidget
from .window import WindowWidget


@dataclass(slots=True)
class WidgetRegistration:
    widget_cls: type
    config_cls: type
    # required fields in the YAML configuration
    required: tuple = ()
    # optional extra check: config -> error text or None
    validator: object = None


_REGISTRY: dict[str, WidgetRegistration] = {}


def register_widget_type(
    name: str,
    widget_cls: type,
    config_cls: type = WidgetConfig,
    required: tuple = (),
    validator=None,
):
    """Registers a (possibly custom) widget type.

    ``validator`` may check what the field-by-field validation
    cannot - it receives the built config and returns an error text
    or None.
    """

    _REGISTRY[name] = WidgetRegistration(
        widget_cls=widget_cls,
        config_cls=config_cls,
        required=required,
        validator=validator,
    )


def get_registration(name: str) -> WidgetRegistration | None:
    return _REGISTRY.get(name)


def registered_types() -> list[str]:
    return sorted(_REGISTRY)


# Built-in widgets
register_widget_type("weather", WeatherWidget, WeatherWidgetConfig)
register_widget_type(
    "entity", EntityWidget, EntityWidgetConfig,
    required=("entity", "icon"),
)
register_widget_type("door", DoorWidget, DoorWidgetConfig)
register_widget_type(
    "window", WindowWidget, WindowWidgetConfig,
    required=("entities",),
)
register_widget_type("waste", WasteWidget, WasteWidgetConfig)
register_widget_type(
    "calendar", CalendarWidget, CalendarWidgetConfig,
    required=("entity", "icon"),
)
register_widget_type(
    "presence", PresenceWidget, PresenceWidgetConfig,
    required=("entities",),
)
register_widget_type(
    "fuel", FuelWidget, FuelWidgetConfig,
    required=("level_entity", "price_entity"),
)
register_widget_type(
    "appliance", ApplianceWidget, ApplianceWidgetConfig,
    required=("name", "running_entity"),
)
register_widget_type(
    "solar", SolarWidget, SolarWidgetConfig,
    required=("entity",),
)
register_widget_type(
    "battery", BatteryWidget, BatteryWidgetConfig,
    required=("entity",),
)
register_widget_type(
    "ev", EvWidget, EvWidgetConfig,
    required=("soc_entity",),
)
register_widget_type(
    "alert", AlertWidget, AlertWidgetConfig,
    required=("name", "conditions"),
)


def _threshold_needs_a_bound(config) -> str | None:

    bounds = (
        config.above, config.below,
        config.critical_above, config.critical_below,
    )

    if all(bound is None for bound in bounds):
        return (
            "needs at least one of above, below, critical_above, "
            "critical_below"
        )

    return None


register_widget_type(
    "threshold", ThresholdWidget, ThresholdWidgetConfig,
    required=("entity", "icon"),
    validator=_threshold_needs_a_bound,
)
register_widget_type(
    "status", StatusWidget, StatusWidgetConfig,
    required=("entities",),
)
register_widget_type(
    "wallbox", WallboxWidget, WallboxWidgetConfig,
    required=("status_entity",),
)
