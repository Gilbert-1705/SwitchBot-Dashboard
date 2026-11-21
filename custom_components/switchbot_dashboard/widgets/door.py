from .base import BaseWidget, DashboardItem
from ..config.entities import Entities
from ..icons import Icons


# (lock_state, door_open) -> (icon, text key, importance)
DOOR_STATES = {
    ("locked", False): (Icons.DOOR, "locked", 20),
    ("locking", False): (Icons.DOOR, "locked", 20),

    ("unlocked", False): (Icons.DOOR, "unlocked", 60),
    ("unlocking", False): (Icons.DOOR, "unlocked", 60),

    ("unlocked", True): (Icons.DOOR, "open", 75),
    ("unlocking", True): (Icons.DOOR, "open", 75),

    # "open": the latch is pulled (smart locks with an unlatch
    # function). Brief transition while someone opens the door.
    ("open", False): (Icons.DOOR, "unlocked", 60),
    ("opening", False): (Icons.DOOR, "unlocked", 60),
    ("open", True): (Icons.DOOR, "open", 75),
    ("opening", True): (Icons.DOOR, "open", 75),

    ("locked", True): (Icons.WARNING, "open", 100),
    ("locking", True): (Icons.WARNING, "open", 100),
}


class DoorWidget(BaseWidget):

    def __init__(
        self,
        hass,
        lock_entity: str = Entities.DOOR_LOCK,
        contact_entity: str = Entities.DOOR_CONTACT,
        priority: int = 300,
    ):
        super().__init__(hass)
        self.lock_entity = lock_entity
        self.contact_entity = contact_entity
        self.priority = priority

    def render(self):

        lock = self.hass.states.get(self.lock_entity)
        contact = self.hass.states.get(self.contact_entity)

        if lock is None or contact is None:
            return None

        if (
            lock.state in ("unknown", "unavailable")
            or contact.state in ("unknown", "unavailable")
        ):
            return None

        lock_state = lock.state
        door_open = contact.state == "on"

        icon, text_key, importance = DOOR_STATES.get(
            (lock_state, door_open),
            (Icons.WARNING, None, 100),
        )

        return DashboardItem(
            icon=icon,
            value=self.t(text_key) if text_key else "?",
            priority=self.priority,
            importance=importance,
        )
