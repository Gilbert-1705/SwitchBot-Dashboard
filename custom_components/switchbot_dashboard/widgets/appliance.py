from .base import BaseWidget, DashboardItem

# States are compared case-insensitively; appliance sensors
# report e.g. "run", "pause", "stop"
RUNNING_STATES = ("on", "true", "running", "run")
PAUSED_STATES = ("pause", "paused")


class ApplianceWidget(BaseWidget):
    """Household appliance (washer, dryer, ...) with a done flag.

        🧺 WM Fertig    cycle finished, not emptied yet
        🧺 WM läuft     currently running (background info)
        🧺 WM Pause     paused (background info)
        (nothing)       idle and emptied

    Since the appliance door state is not available, the done flag
    is an input_boolean in Home Assistant: an automation sets it when
    the cycle finishes; it is reset manually — via app, dashboard or
    a display button (Matter). See docs/examples.md.
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

        # A new cycle makes the old done reminder obsolete
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
