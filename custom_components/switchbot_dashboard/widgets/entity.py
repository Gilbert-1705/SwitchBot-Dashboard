import logging

from homeassistant.core import HomeAssistant
from homeassistant.core import State

from .base import BaseWidget, DashboardItem
from ..formatters.factory import FormatterFactory

_LOGGER = logging.getLogger(__name__)


class EntityWidget(BaseWidget):
    """Widget that renders the state of a Home Assistant entity."""
    requires_config = True

    def __init__(
        self,
        hass: HomeAssistant,
        entity: str,
        icon: str,
        formatter: str = "",
        priority: int = 100,
        importance: int = 10,
    ):
        super().__init__(hass)

        self.entity = entity
        self.icon = icon
        self.priority = priority
        self.importance = importance
        self.formatter = FormatterFactory.create(formatter)

    def get_state(self) -> State | None:
        return self.hass.states.get(self.entity)

    def available(self) -> bool:

        state = self.get_state()

        if state is None:
            _LOGGER.debug("%s: state is None", self.entity)
            return False

        if state.state in ("unknown", "unavailable", None):
            _LOGGER.debug("%s: unavailable", self.entity)
            return False

        return True

    def format_value(self, state: State) -> str:
        return self.formatter.format(state.state)

    def render(self):

        if not self.available():
            return None

        state = self.get_state()

        value = self.format_value(state)

        _LOGGER.debug("Rendering %s: %s", self.entity, value)

        return DashboardItem(
            icon=self.icon,
            value=value,
            priority=self.priority,
            importance=self.importance,
        )
