from dataclasses import dataclass


@dataclass(slots=True)
class WidgetConfig:
    type: str
    priority: int = 100


@dataclass(slots=True)
class WeatherWidgetConfig(WidgetConfig):
    temperature_entity: str = ""
    trend_entity: str = ""
    icon: str = ""


@dataclass(slots=True)
class DoorWidgetConfig(WidgetConfig):
    lock_entity: str = ""
    contact_entity: str = ""


@dataclass(slots=True)
class WasteWidgetConfig(WidgetConfig):
    entity: str = ""
    # lookahead in days
    days: int = 3


@dataclass(slots=True)
class EntityWidgetConfig(WidgetConfig):
    entity: str = ""
    icon: str = ""
    formatter: str = ""
    importance: int = 10


@dataclass(slots=True)
class WindowWidgetConfig(WidgetConfig):
    # entity_id -> room name
    entities: dict[str, str] | None = None
    # "rooms": show room names, "state": state only
    # (Offen/Gekippt) - compact, for sensors that belong together
    mode: str = "rooms"


@dataclass(slots=True)
class CalendarWidgetConfig(WidgetConfig):
    entity: str = ""
    icon: str = ""
    # lookahead in days for showing an event
    days: int = 3


@dataclass(slots=True)
class PresenceWidgetConfig(WidgetConfig):
    # person entity -> display name
    entities: dict[str, str] | None = None


@dataclass(slots=True)
class SolarWidgetConfig(WidgetConfig):
    entity: str = ""
    icon: str = ""
    # production (W) above which the widget appears
    min_power: float = 50.0


@dataclass(slots=True)
class BatteryWidgetConfig(WidgetConfig):
    entity: str = ""
    # short label, e.g. "eBike" or "Speicher"
    name: str = ""
    icon: str = ""
    # level (%) below which the battery becomes important
    min_level: float = 20.0
    # show as background info even when the level is fine
    show_always: bool = False


@dataclass(slots=True)
class EvWidgetConfig(WidgetConfig):
    soc_entity: str = ""
    charging_entity: str = ""
    name: str = ""
    icon: str = ""
    min_level: float = 20.0
    show_always: bool = False


@dataclass(slots=True)
class ApplianceWidgetConfig(WidgetConfig):
    # short label for the display, e.g. "WM" or "TR"
    name: str = ""
    running_entity: str = ""
    # input_boolean: on = finished but not emptied yet
    done_entity: str = ""
    icon: str = ""


@dataclass(slots=True)
class FuelWidgetConfig(WidgetConfig):
    level_entity: str = ""
    price_entity: str = ""
    # level below which refueling becomes relevant (in `unit`)
    min_level: float = 20.0
    # price (EUR/l) up to which refueling is worth it
    max_price: float = 1.75
    # unit of the level sensor: "%" or "l"
    unit: str = "%"
