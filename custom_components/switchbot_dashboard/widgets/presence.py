from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..text import join_names

HOME_STATES = ("home", "on")


class PresenceWidget(BaseWidget):
    """Zeigt, wer zu Hause ist.

        ⌂ Jan          eine Person
        ⌂ Jan+Anna     zwei Personen
        ⌂ Jan+2        ab drei Personen
        ⌂ Leer         niemand zu Hause

    Ein leeres Haus ist die wichtigere Information (Abschieds-
    Check: alles zu?), Anwesenheit ist Hintergrundinfo.
    """


    def __init__(
        self,
        hass,
        entities: dict[str, str],
        priority: int = 600,
    ):
        super().__init__(hass)

        # person-Entity -> Anzeigename
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
                value="Leer",
                priority=self.priority,
                importance=45,
            )

        return DashboardItem(
            icon=Icons.HOME,
            value=join_names(home),
            priority=self.priority,
            importance=15,
        )
