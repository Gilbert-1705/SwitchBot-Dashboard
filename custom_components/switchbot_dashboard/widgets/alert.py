"""Smart alerts: rules across multiple entities.

Home Assistant knows all these states but normally never combines
them. An alert widget renders a single item when ALL of its
conditions hold (AND) — build OR by configuring several alerts.

    - type: alert
      name: Regen rein
      conditions:
        - entity: binary_sensor.fenster_wohnen
          state: Offen
        - entity: sensor.regen_wahrscheinlichkeit
          above: 70

Supported condition keys (each condition needs ``entity`` plus at
least one criterion):

    state      state equals (case-insensitive), string or list
    not_state  state does not equal (string or list)
    above      numeric state > value
    below      numeric state < value
    duration   entity has been in its current state for at least
               this many seconds (e.g. door open for 10 minutes)

Unknown/unavailable entities make a condition false — an alert
never fires on missing data.
"""

from datetime import datetime, timezone

from .base import BaseWidget, DashboardItem
from ..const import IMPORTANCE_ALARM
from ..icons import Icons
from ..tracker import state_since

SKIP_STATES = ("unknown", "unavailable", "none")


class AlertWidget(BaseWidget):

    def __init__(
        self,
        hass,
        name: str,
        conditions: list,
        icon: str = Icons.WARNING,
        importance: int = IMPORTANCE_ALARM,
        priority: int = 50,
    ):
        super().__init__(hass)

        self.name = name
        self.conditions = conditions or []
        self.icon = icon
        self.importance = importance
        self.priority = priority

    def render(self):

        if not self.conditions:
            return None

        # Durations are measured by the tracker, which has to see
        # the entity on every render - also when an earlier
        # condition already fails
        since = {
            index: state_since(
                self.hass,
                condition.get("entity"),
                self.hass.states.get(condition.get("entity")),
            )
            for index, condition in enumerate(self.conditions)
            if "duration" in condition
        }

        for index, condition in enumerate(self.conditions):
            if not self._holds(condition, since.get(index)):
                return None

        return DashboardItem(
            icon=self.icon,
            value=self.name,
            priority=self.priority,
            importance=self.importance,
        )

    def _holds(self, condition: dict, since=None) -> bool:

        state = self.hass.states.get(condition.get("entity"))

        if state is None:
            return False

        value = str(state.state)

        if value.lower() in SKIP_STATES:
            return False

        if "state" in condition:
            if not self._matches(value, condition["state"]):
                return False

        if "not_state" in condition:
            if self._matches(value, condition["not_state"]):
                return False

        if "above" in condition:
            number = self._number(value)
            if number is None or number <= float(condition["above"]):
                return False

        if "below" in condition:
            number = self._number(value)
            if number is None or number >= float(condition["below"]):
                return False

        if "duration" in condition:
            if since is None:
                return False
            elapsed = (
                datetime.now(timezone.utc) - since
            ).total_seconds()
            if elapsed < float(condition["duration"]):
                return False

        return True

    @staticmethod
    def _matches(value: str, expected) -> bool:

        if isinstance(expected, (list, tuple)):
            options = expected
        else:
            options = (expected,)

        return value.lower() in (
            str(option).lower() for option in options
        )

    @staticmethod
    def _number(value: str):

        try:
            return float(value)
        except (ValueError, TypeError):
            return None
