from dataclasses import dataclass


@dataclass(slots=True)
class WidgetConfig:
    type: str
    # display order (lower = further left); None: the widget's own
    # default, e.g. alerts and status warnings at the front
    priority: int | None = None
    # widgets sharing a group render at most one item (the most
    # important one), e.g. door + window + alarm as group "haus"
    group: str = ""
    # day context: time windows that raise/lower importance,
    # e.g. [{"between": ["06:00", "09:00"], "add": 20}]
    boost: list | None = None


@dataclass(slots=True)
class WeatherWidgetConfig(WidgetConfig):
    temperature_entity: str = ""
    trend_entity: str = ""
    icon: str = ""
    # optional second sensor; used when the local one is off by
    # more than max_deviation (sun on the sensor) or unavailable
    reference_entity: str = ""
    max_deviation: float = 4.0
    # shown degree changes only after moving this far (0 = off)
    hysteresis: float = 0.75


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
class AlertWidgetConfig(WidgetConfig):
    # display text, e.g. "Regen rein"
    name: str = ""
    icon: str = ""
    importance: int = 100
    # list of condition mappings, see widgets/alert.py
    conditions: list | None = None


@dataclass(slots=True)
class ThresholdWidgetConfig(WidgetConfig):
    entity: str = ""
    icon: str = ""
    # short label in front of the value, e.g. "CO₂"
    name: str = ""
    # bounds that make the value worth showing
    above: float | None = None
    below: float | None = None
    # bounds that raise it to the always-shown band
    critical_above: float | None = None
    critical_below: float | None = None
    unit: str = ""
    precision: int = 0
    importance: int = 55


@dataclass(slots=True)
class StatusWidgetConfig(WidgetConfig):
    # entity_id -> display name
    entities: dict[str, str] | None = None
    icon: str = ""
    # states that mean "fine"; default: on, home, up, online, ...
    ok_states: list | None = None
    unavailable_is_problem: bool = True
    importance: int = 85


@dataclass(slots=True)
class WallboxWidgetConfig(WidgetConfig):
    status_entity: str = ""
    # optional: charging power in W
    power_entity: str = ""
    name: str = ""
    icon: str = ""


@dataclass(slots=True)
class MediaWidgetConfig(WidgetConfig):
    # one player ...
    entity: str = ""
    # ... or several: the first one playing wins
    entities: list | None = None
    icon: str = ""
    # title, artist or both
    show: str = "title"
    # titles are longer than other widget texts
    max_length: int = 20
    importance: int = 30


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
    # status entity: simple run/pause/stop sensor or a WashData
    # state sensor (running/clean/delay_wait/...)
    running_entity: str = ""
    # optional input_boolean: on = finished but not emptied yet
    # (not needed when the status entity reports that itself)
    done_entity: str = ""
    # optional: remaining time in minutes
    remaining_entity: str = ""
    # optional: current phase, shown while running
    phase_entity: str = ""
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
    # optional reference price (e.g. lowest price of the last 7 days);
    # replaces the fixed max_price while it has a value
    max_price_entity: str = ""
    # allowed surcharge on the reference price (EUR/l)
    price_margin: float = 0.0
