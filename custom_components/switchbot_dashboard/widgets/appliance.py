from .base import BaseWidget, DashboardItem

# Zustände werden case-insensitive verglichen; Gerätesensoren
# liefern z.B. "run", "pause", "stop"
RUNNING_STATES = ("on", "true", "running", "run")
PAUSED_STATES = ("pause", "paused")


class ApplianceWidget(BaseWidget):
    """Haushaltsgerät (Waschmaschine, Trockner, ...) mit Fertig-Flag.

        🧺 WM Fertig    Gerät ist durchgelaufen, noch nicht geleert
        🧺 WM läuft     Gerät läuft gerade (Hintergrundinfo)
        🧺 WM Pause     Gerät pausiert (Hintergrundinfo)
        (nichts)        Gerät ist aus und geleert

    Da der Türstatus nicht abfragbar ist, ist das Fertig-Flag ein
    input_boolean in Home Assistant: eine Automation setzt es, wenn
    das Gerät fertig ist; zurückgesetzt wird es manuell — per App,
    Dashboard oder Display-Button (Matter). Siehe docs/examples.md.
    """

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

        running = self._state(self.running_entity)

        # Läuft die Maschine wieder, ist der alte Reminder obsolet
        if running in RUNNING_STATES:
            return DashboardItem(
                icon=self.icon,
                value=f"{self.name} läuft",
                priority=self.priority,
                importance=15,
            )

        if self._state(self.done_entity) in RUNNING_STATES:
            return DashboardItem(
                icon=self.icon,
                value=f"{self.name} Fertig",
                priority=self.priority,
                importance=80,
            )

        if running in PAUSED_STATES:
            return DashboardItem(
                icon=self.icon,
                value=f"{self.name} Pause",
                priority=self.priority,
                importance=15,
            )

        return None

    def _state(self, entity: str) -> str:

        state = self.hass.states.get(entity)

        if state is None:
            return ""

        return str(state.state).lower()
