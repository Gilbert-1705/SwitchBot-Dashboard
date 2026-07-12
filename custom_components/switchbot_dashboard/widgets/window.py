from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names

# Zustände werden case-insensitive verglichen (z.B. Homematic:
# "Offen", "Geschlossen", "Gekippt")
OPEN_STATES = ("on", "open", "true", "offen")
TILTED_STATES = ("tilted", "gekippt")
SKIP_STATES = ("unknown", "unavailable", "none")


class WindowWidget(BaseWidget):

    requires_config = True

    def __init__(
        self,
        hass,
        entities: dict[str, str],
        priority: int = 250,
    ):
        super().__init__(hass)

        # entity_id -> Raumname, z.B. {"binary_sensor.wohnen": "Wohnen"}
        self.entities = entities
        self.priority = priority

    def render(self):

        open_rooms = []
        tilted_rooms = []

        for entity, name in self.entities.items():

            state = self.hass.states.get(entity)

            if state is None:
                continue

            value = str(state.state).lower()

            if value in SKIP_STATES:
                continue

            if value in OPEN_STATES:
                open_rooms.append(name)
            elif value in TILTED_STATES:
                tilted_rooms.append(name)

        if not open_rooms and not tilted_rooms:
            return DashboardItem(
                icon="",
                value=Icons.CLOSED,
                priority=self.priority,
                importance=15,
            )

        # Gekippte Fenster zählen als offen, sind aber weniger
        # dringend, solange nichts ganz offen steht
        importance = 65 if open_rooms else 40

        return DashboardItem(
            icon=Icons.OPEN,
            # "Wohnen", "Wohnen+Essen", ab drei Räumen "Wohnen+2"
            value=join_names(open_rooms + tilted_rooms),
            priority=self.priority,
            importance=importance,
        )
