from dataclasses import dataclass


@dataclass(slots=True)
class WidgetConfig:

    priority: int = 100


@dataclass(slots=True)
class EntityWidgetConfig(WidgetConfig):

    entity: str = ""
    icon: str = ""
    formatter: str = ""