from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names

# Zustände werden case-insensitive verglichen (z.B. Homematic:
# "Offen", "Geschlossen", "Gekippt")
OPEN_STATES = ("on", "open", "true", "offen")
TILTED_STATES = ("tilted", "gekippt")
SKIP_STATES = ("unknown", "unavailable", "none")


class WindowWidget(BaseWidget):
    """Fenster-/Balkontür-Widget mit zwei Anzeigemodi.

    mode="rooms" (Standard): zeigt die Namen offener Räume
        ○ Wohnen        ○ Wohnen+Essen      ○ Wohnen+2

    mode="state": zeigt nur den Zustand — für Fälle, in denen die
    Sensoren zusammengehören (z.B. zwei Türen desselben Balkons)
    und der Name egal ist. Kürzer, bricht auf dem Display nicht um.
        ○ Offen         ○ Gekippt           ○ Offen+Gekippt

    Gekippt gilt als unkritisch (man darf gekippt aus dem Haus)
    und wird deshalb nur als Hintergrundinfo gewichtet.
    """

    requires_config = True

    def __init__(
        self,
        hass,
        entities: dict[str, str],
        mode: str = "rooms",
        priority: int = 250,
    ):
        super().__init__(hass)

        # entity_id -> Raumname, z.B. {"binary_sensor.wohnen": "Wohnen"}
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

    def _render_state(self, open_rooms, tilted_rooms):

        if open_rooms and tilted_rooms:
            value = "Offen+Gekippt"
            importance = 65
        elif open_rooms:
            value = "Offen"
            importance = 65
        else:
            # Nur gekippt: darf so bleiben, reine Hintergrundinfo
            value = "Gekippt"
            importance = 25

        return DashboardItem(
            icon=Icons.OPEN,
            value=value,
            priority=self.priority,
            importance=importance,
        )
