from .base import BaseWidget, DashboardItem
from ..ramp import time_based_importance

# States are compared case-insensitively; appliance sensors
# report e.g. "run", "pause", "stop"
RUNNING_STATES = ("on", "true", "running", "run")
PAUSED_STATES = ("pause", "paused")

# The done reminder gets more urgent the longer the laundry waits:
# side note right away, prominent after 1 h, always shown after 3 h.
# Capped at 95: waiting laundry is loud, but never an alarm
DONE_RAMP = ((0, 30), (3600, 60), (10800, 95))


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

        done = self.hass.states.get(self.done_entity)

        if done is not None and str(done.state).lower() in RUNNING_STATES:
            return DashboardItem(
                icon=self.icon,
                value=f"{self.name} Fertig",
                priority=self.priority,
                # The longer the laundry waits, the louder the reminder
                importance=time_based_importance(
                    getattr(done, "last_changed", None),
                    DONE_RAMP,
                ),
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
