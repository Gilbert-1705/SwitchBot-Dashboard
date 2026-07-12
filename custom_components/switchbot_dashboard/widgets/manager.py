from .calendar import CalendarWidget
from .config import WIDGETS
from .config_models import (
    CalendarWidgetConfig,
    EntityWidgetConfig,
    WidgetConfig,
    WindowWidgetConfig,
)
from .door import DoorWidget
from .entity import EntityWidget
from .weather import WeatherWidget
from .window import WindowWidget
from .waste import WasteWidget


WIDGET_TYPES = {
    "weather": WeatherWidget,
    "entity": EntityWidget,
    "door": DoorWidget,
    "window": WindowWidget,
    "waste": WasteWidget,
    "calendar": CalendarWidget,
}


class WidgetManager:

    def __init__(self, hass):
        self.hass = hass

    def widgets(self):

        widgets = []

        for cfg in WIDGETS:

            widget_cls = WIDGET_TYPES.get(cfg.type)

            if widget_cls is None:
                continue

            # Widgets ohne Konfiguration
            if not widget_cls.requires_config:
                widgets.append(widget_cls(self.hass))
                continue

            # Fenster-Widget
            if isinstance(cfg, WindowWidgetConfig):
                widgets.append(
                    widget_cls(
                        hass=self.hass,
                        entities=cfg.entities,
                        priority=cfg.priority,
                    )
                )
                continue

            # Kalender-Widget
            if isinstance(cfg, CalendarWidgetConfig):
                widgets.append(
                    widget_cls(
                        hass=self.hass,
                        entity=cfg.entity,
                        icon=cfg.icon,
                        days=cfg.days,
                        priority=cfg.priority,
                    )
                )
                continue

            # Normales Entity-Widget
            if isinstance(cfg, EntityWidgetConfig):
                widgets.append(
                    widget_cls(
                        hass=self.hass,
                        entity=cfg.entity,
                        icon=cfg.icon,
                        formatter=cfg.formatter,
                        priority=cfg.priority,
                    )
                )
                continue

            raise TypeError(
                f"Unsupported widget config: {type(cfg).__name__}"
            )

        return sorted(
            widgets,
            key=lambda widget: widget.priority,
        )