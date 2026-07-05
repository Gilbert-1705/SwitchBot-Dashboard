from .config import WIDGETS
from .door import DoorWidget
from .weather import WeatherWidget
from .entity import EntityWidget


WIDGET_TYPES = {
    "weather": WeatherWidget,
    "entity": EntityWidget,
    "door": DoorWidget,
}


class WidgetManager:

    def __init__(self, hass):
        self.hass = hass

    def widgets(self):

        widgets = []

        for cfg in WIDGETS:

            widget_cls = WIDGET_TYPES.get(cfg["type"])

            if widget_cls is None:
                continue

            if widget_cls.requires_config:

                widgets.append(
                    widget_cls(
                        hass=self.hass,
                        entity=cfg["entity"],
                        icon=cfg["icon"],
                        formatter=cfg.get("formatter", ""),
                        priority=cfg.get("priority", 100),
                    )
                )

            else:

                widgets.append(
                    widget_cls(self.hass)
                )

        return sorted(
            widgets,
            key=lambda widget: widget.priority,
        )