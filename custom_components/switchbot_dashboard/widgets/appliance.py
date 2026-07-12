from .base import BaseWidget, DashboardItem

ON_STATES = ("on", "true", "running")


class ApplianceWidget(BaseWidget):
    """Haushaltsgerät (Waschmaschine, Trockner, ...) mit Fertig-Flag.

        🧺 WM Fertig    Gerät ist durchgelaufen, noch nicht geleert
        🧺 WM läuft     Gerät läuft gerade (Hintergrundinfo)
        (nichts)        Gerät ist aus und geleert

    Da der Türstatus nicht abfragbar ist, ist das Fertig-Flag ein
    input_boolean in Home Assistant: eine Automation setzt es, wenn
    das Gerät fertig ist; zurückgesetzt wird es manuell — per App,
    Dashboard oder Display-Button (Matter). Siehe docs/examples.md.
    """

    requires_config = True

    def __init__(
        self,
        hass,
        name: str,
        running_entity: str,
        done_entity: str,
        icon: str,
        priority: int = 700,
    ):
        super().__init__(hass)

        self.name = name
        self.running_entity = running_entity
        self.done_entity = done_entity
        self.icon = icon
        self.priority = priority

    def render(self):

        if self._is_on(self.done_entity):
            return DashboardItem(
                icon=self.icon,
                value=f"{self.name} Fertig",
                priority=self.priority,
                importance=80,
            )

        if self._is_on(self.running_entity):
            return DashboardItem(
                icon=self.icon,
                value=f"{self.name} läuft",
                priority=self.priority,
                importance=15,
            )

        return None

    def _is_on(self, entity: str) -> bool:

        state = self.hass.states.get(entity)

        if state is None:
            return False

        return state.state in ON_STATES
