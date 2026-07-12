"""Widget-Registry: verbindet Widget-Typen mit Klassen und Configs.

Eigene Widgets lassen sich von außen registrieren:

    from custom_components.switchbot_dashboard.widgets.registry import (
        register_widget_type,
    )

    register_widget_type("mein_widget", MeinWidget, MeinWidgetConfig)

Danach ist der Typ in der Konfiguration (Python und YAML) nutzbar.
Siehe docs/configuration.md.
"""

from dataclasses import dataclass

from .appliance import ApplianceWidget
from .battery import BatteryWidget
from .calendar import CalendarWidget
from .config_models import (
    ApplianceWidgetConfig,
    BatteryWidgetConfig,
    CalendarWidgetConfig,
    DoorWidgetConfig,
    EntityWidgetConfig,
    EvWidgetConfig,
    FuelWidgetConfig,
    PresenceWidgetConfig,
    SolarWidgetConfig,
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
from .waste import WasteWidget
from .weather import WeatherWidget
from .window import WindowWidget


@dataclass(slots=True)
class WidgetRegistration:
    widget_cls: type
    config_cls: type
    # Pflichtfelder in der YAML-Konfiguration
    required: tuple = ()


_REGISTRY: dict[str, WidgetRegistration] = {}


def register_widget_type(
    name: str,
    widget_cls: type,
    config_cls: type = WidgetConfig,
    required: tuple = (),
):
    """Registriert einen (auch eigenen) Widget-Typ."""

    _REGISTRY[name] = WidgetRegistration(
        widget_cls=widget_cls,
        config_cls=config_cls,
        required=required,
    )


def get_registration(name: str) -> WidgetRegistration | None:
    return _REGISTRY.get(name)


def registered_types() -> list[str]:
    return sorted(_REGISTRY)


# Eingebaute Widgets
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
    required=("name", "running_entity", "done_entity"),
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
