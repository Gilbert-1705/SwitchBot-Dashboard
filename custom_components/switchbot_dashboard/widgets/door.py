from .base import BaseWidget, DashboardItem
from ..config.entities import Entities
from ..icons import Icons


DOOR_STATES = {
    ("locked", False): (Icons.DOOR, "Zu"),
    ("locking", False): (Icons.DOOR, "Zu"),

    ("unlocked", False): (Icons.DOOR, "Auf"),
    ("unlocking", False): (Icons.DOOR, "Auf"),

    ("unlocked", True): (Icons.DOOR, "Offen"),
    ("unlocking", True): (Icons.DOOR, "Offen"),

    ("locked", True): (Icons.WARNING, "Offen"),
    ("locking", True): (Icons.WARNING, "Offen"),
}


class DoorWidget(BaseWidget):

    requires_config = False

    def __init__(self, hass):
        super().__init__(hass)
        self.priority = 300

    def render(self):

        lock = self.hass.states.get(Entities.DOOR_LOCK)
        contact = self.hass.states.get(Entities.DOOR_CONTACT)

        if lock is None or contact is None:
            return None

        if (
            lock.state in ("unknown", "unavailable")
            or contact.state in ("unknown", "unavailable")
        ):
            return None

        lock_state = lock.state
        door_open = contact.state == "on"

        icon, value = DOOR_STATES.get(
            (lock_state, door_open),
            (Icons.WARNING, "?"),
        )

        return DashboardItem(
            icon=icon,
            value=value,
            priority=self.priority,
        )
