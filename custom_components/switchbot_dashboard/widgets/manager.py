import logging
from dataclasses import fields as dataclass_fields

from .config import WIDGETS
from .registry import get_registration

_LOGGER = logging.getLogger(__name__)


class WidgetManager:
    """Baut Widgets aus (Python- oder YAML-) Konfigurationen.

    Die Config-Dataclasses spiegeln die Konstruktor-Parameter der
    Widgets: jedes Feld (außer ``type``) wird als Keyword-Argument
    durchgereicht. Neue Widget-Typen brauchen deshalb keinen
    Manager-Code, nur einen Eintrag in der Registry.
    """

    def __init__(self, hass, configs=None):
        self.hass = hass
        self.configs = configs if configs is not None else WIDGETS

    def widgets(self):

        widgets = []

        for cfg in self.configs:

            registration = get_registration(cfg.type)

            if registration is None:
                _LOGGER.warning("Unknown widget type: %s", cfg.type)
                continue

            widgets.append(self._build(registration.widget_cls, cfg))

        return sorted(
            widgets,
            key=lambda widget: widget.priority,
        )

    def _build(self, widget_cls, cfg):

        kwargs = {}

        for field in dataclass_fields(cfg):

            if field.name == "type":
                continue

            value = getattr(cfg, field.name)

            # None/leer heißt: Default des Widgets verwenden
            if value is None or value == "":
                continue

            kwargs[field.name] = value

        return widget_cls(hass=self.hass, **kwargs)
