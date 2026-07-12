from .base import BaseWidget, DashboardItem
from ..config.entities import Entities
from ..icons import Icons


# (lock_state, tür_offen) -> (icon, text, importance)
DOOR_STATES = {
    ("locked", False): (Icons.DOOR, "Zu", 20),
    ("locking", False): (Icons.DOOR, "Zu", 20),

    ("unlocked", False): (Icons.DOOR, "Auf", 60),
    ("unlocking", False): (Icons.DOOR, "Auf", 60),

    ("unlocked", True): (Icons.DOOR, "Offen", 75),
    ("unlocking", True): (Icons.DOOR, "Offen", 75),

    ("locked", True): (Icons.WARNING, "Offen", 100),
    ("locking", True): (Icons.WARNING, "Offen", 100),
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

        icon, value, importance = DOOR_STATES.get(
            (lock_state, door_open),
            (Icons.WARNING, "?", 100),
        )

        return DashboardItem(
            icon=icon,
            value=value,
            priority=self.priority,
            importance=importance,
        )
