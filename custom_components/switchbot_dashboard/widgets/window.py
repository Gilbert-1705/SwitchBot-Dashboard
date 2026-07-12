from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names

OPEN_STATES = ("on", "open", "true")


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

        for entity, name in self.entities.items():

            state = self.hass.states.get(entity)

            if state is None:
                continue

            if state.state in OPEN_STATES:
                open_rooms.append(name)

        if not open_rooms:
            return DashboardItem(
                icon="",
                value=Icons.CLOSED,
                priority=self.priority,
                importance=15,
            )

        return DashboardItem(
            icon=Icons.OPEN,
            # "Wohnen", "Wohnen+Essen", ab drei Räumen "Wohnen+2"
            value=join_names(open_rooms),
            priority=self.priority,
            importance=65,
        )
