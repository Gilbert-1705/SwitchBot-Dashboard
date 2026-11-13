import math
import re

from .base import BaseWidget, DashboardItem
from ..icons import Icons
from ..ramp import time_based_importance
from ..tracker import state_since

# States are compared case-insensitively. Covers simple sensors
# ("run", "pause", "stop") as well as the WashData integration
# ("starting", "running", "clean", "delay_wait", ...).
RUNNING_STATES = ("on", "true", "running", "run", "starting", "ending")
PAUSED_STATES = ("pause", "paused", "user_paused")
WAITING_STATES = ("delay_wait",)
DONE_STATES = ("finished", "clean", "anti_wrinkle")
FAILED_STATES = ("interrupted", "force_stopped")

# states of the optional done flag (input_boolean)
FLAG_ON_STATES = ("on", "true")

# values that mean "no detail available"
EMPTY_STATES = ("", "unknown", "unavailable", "none", "off", "idle")

# A running appliance is not background noise: it sits in the normal
# band so it gets a slot even on a quiet day (fillers like "door
# closed" would otherwise always win against it)
ACTIVE_IMPORTANCE = 30

# The done reminder gets more urgent the longer the appliance waits:
# side note right away, prominent after 1 h, always shown after 3 h.
# Capped at 95: waiting laundry is loud, but never an alarm
DONE_RAMP = ((0, 30), (3600, 60), (10800, 95))

# Remaining time is rounded up to this step so the e-paper does not
# refresh every single minute while a cycle is running
REMAINING_STEP_MINUTES = 5

# trailing temperature etc. in phase names ("Reinigen 45")
TRAILING_NUMBER = re.compile(r"\s+\d+$")


class ApplianceWidget(BaseWidget):
    """Household appliance (washer, dryer, dishwasher, ...).

        🧺 WM Fertig      cycle finished, not emptied yet
        🧺 WM läuft       currently running
        🍽 GS Trocknen    running, with phase (phase_entity)
        🍽 GS 45min       running, with remaining time
        🧺 WM Pause       paused
        🍽 GS wartet      delayed start pending
        🍽 GS Abbruch     cycle interrupted
        (nothing)         idle and emptied

    Two ways to know that a finished appliance still needs emptying:

    1. The status entity reports it itself — e.g. WashData's
       ``clean``/``finished`` until "mark as unloaded" is pressed.
       No helper needed.
    2. A manual done flag (``done_entity``, an input_boolean): an
       automation sets it when the cycle finishes, it is reset
       manually. See docs/examples.md.
    """

    def __init__(
        self,
        hass,
        name: str,
        running_entity: str,
        done_entity: str = "",
        remaining_entity: str = "",
        phase_entity: str = "",
        icon: str = Icons.LAUNDRY,
        priority: int = 700,
    ):
        super().__init__(hass)

        self.name = name
        self.running_entity = running_entity
        self.done_entity = done_entity
        self.remaining_entity = remaining_entity
        self.phase_entity = phase_entity
        self.icon = icon
        self.priority = priority

    def render(self):

        status = self.hass.states.get(self.running_entity)
        running = self._lower(status)

        done = None
        if self.done_entity:
            done = self.hass.states.get(self.done_entity)

        # Reported on every render, whatever the state: the tracker
        # must see each transition to know when a period began
        status_since = state_since(self.hass, self.running_entity, status)
        done_since = state_since(self.hass, self.done_entity, done)

        # A new cycle makes the old done reminder obsolete
        if running in RUNNING_STATES:
            return self._item(self._running_detail(), ACTIVE_IMPORTANCE)

        # Manual done flag (input_boolean)
        if self._lower(done) in FLAG_ON_STATES:
            return self._done_item(done_since)

        # The status entity itself reports "finished, not emptied"
        if running in DONE_STATES:
            return self._done_item(status_since)

        if running in FAILED_STATES:
            return self._item(self.t("aborted"), 65)

        if running in PAUSED_STATES:
            return self._item(self.t("paused"), ACTIVE_IMPORTANCE)

        if running in WAITING_STATES:
            return self._item(self.t("waiting"), 15)

        return None

    # -- helpers --------------------------------------------------

    def _item(self, text: str, importance: int) -> DashboardItem:

        return DashboardItem(
            icon=self.icon,
            value=f"{self.name} {text}",
            priority=self.priority,
            importance=importance,
        )

    def _done_item(self, since) -> DashboardItem:

        # The longer it waits, the louder the reminder
        return self._item(
            self.t("done"),
            time_based_importance(since, DONE_RAMP),
        )

    def _running_detail(self) -> str:
        """Phase if known, else remaining time, else 'läuft'."""

        if self.phase_entity:
            phase = self.hass.states.get(self.phase_entity)

            if self._lower(phase) not in EMPTY_STATES:
                # "Klarspülen 69" -> "Klarspülen": the temperature
                # suffix costs display width without adding meaning
                return TRAILING_NUMBER.sub("", str(phase.state))

        if self.remaining_entity:
            remaining = self.hass.states.get(self.remaining_entity)

            try:
                minutes = float(remaining.state)
            except (AttributeError, ValueError, TypeError):
                minutes = 0

            if minutes > 0:
                step = REMAINING_STEP_MINUTES
                rounded = int(math.ceil(minutes / step) * step)
                return f"{rounded}{self.t('minutes')}"

        return self.t("running")

    @staticmethod
    def _lower(state) -> str:

        if state is None:
            return ""

        return str(state.state).lower()
