from dataclasses import dataclass


@dataclass(slots=True)
class WidgetConfig:
    type: str
    priority: int = 100


@dataclass(slots=True)
class EntityWidgetConfig(WidgetConfig):
    entity: str = ""
    icon: str = ""
    formatter: str = ""
    importance: int = 10


@dataclass(slots=True)
class WindowWidgetConfig(WidgetConfig):
    # entity_id -> Raumname
    entities: dict[str, str] | None = None


@dataclass(slots=True)
class CalendarWidgetConfig(WidgetConfig):
    entity: str = ""
    icon: str = ""
    # Vorlaufzeit in Tagen, ab der ein Termin angezeigt wird
    days: int = 3


@dataclass(slots=True)
class PresenceWidgetConfig(WidgetConfig):
    # person-Entity -> Anzeigename
    entities: dict[str, str] | None = None


@dataclass(slots=True)
class FuelWidgetConfig(WidgetConfig):
    level_entity: str = ""
    price_entity: str = ""
    # Füllstand, ab dem Tanken relevant wird (in `unit`)
    min_level: float = 20.0
    # Preis (EUR/l), bis zu dem sich Tanken lohnt
    max_price: float = 1.75
    # Einheit des Füllstandsensors: "%" oder "l"
    unit: str = "%"
