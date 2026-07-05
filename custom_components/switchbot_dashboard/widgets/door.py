from .base import BaseWidget, DashboardItem
from ..config.entities import Entities
from ..icons import Icons


STATE_ICONS = {
    "locked": Icons.CLOSED,
    "locking": Icons.CLOSED,
    "unlocked": Icons.OPEN,
    "unlocking": Icons.OPEN,
}


class DoorWidget(BaseWidget):

    def __init__(self, hass):
        super().__init__(hass)
        self.priority = 300

    def render(self):

        state = self.hass.states.get(Entities.DOOR)

        if state is None or state.state in ("unknown", "unavailable"):
            return None

        icon = STATE_ICONS.get(
            state.state,
            Icons.CLOSED,
        )

        return DashboardItem(
            icon=icon,
            value="",
            priority=self.priority,
        )