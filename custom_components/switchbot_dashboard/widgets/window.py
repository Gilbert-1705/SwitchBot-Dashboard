from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names

# States are compared case-insensitively (e.g. Homematic:
# "Offen", "Geschlossen", "Gekippt")
OPEN_STATES = ("on", "open", "true", "offen")
TILTED_STATES = ("tilted", "gekippt")
SKIP_STATES = ("unknown", "unavailable", "none")


class WindowWidget(BaseWidget):
    """Window/balcony-door widget with two display modes.

    mode="rooms" (default): shows the names of open rooms
        ○ Wohnen        ○ Wohnen+Essen      ○ Wohnen+2

    mode="state": shows only the state — for sensors that belong
    together (e.g. two doors of the same balcony) where the name
    doesn't matter. Shorter, never wraps on the display.
        ○ Offen         ○ Gekippt           ○ Offen+Gekippt

    Tilted counts as uncritical (leaving the house with tilted
    windows is fine), so it only ranks as background info.
    """

    def __init__(
        self,
        hass,
        entities: dict[str, str],
        mode: str = "rooms",
        priority: int = 250,
    ):
        super().__init__(hass)

        # entity_id -> room name, e.g. {"binary_sensor.wohnen": "Wohnen"}
        self.entities = entities
        self.mode = mode
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

        if self.mode == "state":
            return self._render_state(open_rooms, tilted_rooms)

        # Tilted windows count as open but are less urgent as long
        # as nothing is fully open
        importance = 65 if open_rooms else 40

        return DashboardItem(
            icon=Icons.OPEN,
            # "Wohnen", "Wohnen+Essen", three or more -> "Wohnen+2"
            value=join_names(open_rooms + tilted_rooms),
            priority=self.priority,
            importance=importance,
        )

    def _render_state(self, open_rooms, tilted_rooms):

        if open_rooms and tilted_rooms:
            value = f"{self.t('open')}+{self.t('tilted')}"
            importance = 65
        elif open_rooms:
            value = self.t("open")
            importance = 65
        else:
            # Tilted only: fine to stay that way, pure background info
            value = self.t("tilted")
            importance = 25

        return DashboardItem(
            icon=Icons.OPEN,
            value=value,
            priority=self.priority,
            importance=importance,
        )
