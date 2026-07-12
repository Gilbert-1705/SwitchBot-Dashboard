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
