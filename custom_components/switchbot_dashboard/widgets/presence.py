from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names

HOME_STATES = ("home", "on")


class PresenceWidget(BaseWidget):
    """Shows who is home.

        ⌂ Jan          one person
        ⌂ Jan+Anna     two persons
        ⌂ Jan+2        three or more
        ⌂ Leer         nobody home

    An empty house is the more important information (leaving
    check: everything closed?), presence is background info.
    """

    def __init__(
        self,
        hass,
        entities: dict[str, str],
        priority: int = 600,
    ):
        super().__init__(hass)

        # person entity -> display name
        self.entities = entities
        self.priority = priority

    def render(self):

        home = []
        known = 0

        for entity, name in self.entities.items():

            state = self.hass.states.get(entity)

            if state is None or state.state in ("unknown", "unavailable"):
                continue

            known += 1

            if state.state in HOME_STATES:
                home.append(name)

        if known == 0:
            return None

        if not home:
            return DashboardItem(
                icon=Icons.HOME,
                value=self.t("empty"),
                priority=self.priority,
                importance=45,
            )

        return DashboardItem(
            icon=Icons.HOME,
            value=join_names(home),
            priority=self.priority,
            importance=15,
        )
