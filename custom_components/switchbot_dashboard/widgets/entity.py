from homeassistant.core import HomeAssistant
from homeassistant.core import State

from .base import BaseWidget, DashboardItem
from ..formatters.factory import FormatterFactory


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
    ):
        super().__init__(hass)

        self.entity = entity
        self.icon = icon
        self.priority = priority
        self.formatter = FormatterFactory.create(formatter)

    def get_state(self) -> State | None:
        return self.hass.states.get(self.entity)

    def available(self) -> bool:

        state = self.get_state()

        if state is None:
            print(f"{self.entity}: state is None")
            return False

        print(f"{self.entity}: state='{state.state}'")

        if state.state in ("unknown", "unavailable", None):
            print(f"{self.entity}: unavailable")
            return False

        return True

    def format_value(self, state: State) -> str:
        return self.formatter.format(state.state)

    def render(self):

        if not self.available():
            return None

        state = self.get_state()

        value = self.format_value(state)

        print(f"Rendering {self.entity}: {value}")

        return DashboardItem(
            icon=self.icon,
            value=value,
            priority=self.priority,
        )