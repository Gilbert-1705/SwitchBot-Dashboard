from datetime import date

from .base import BaseWidget, DashboardItem
from ..text import shorten

# Keep event names compact so the suffix (Morgen/3T) still fits
MAX_MESSAGE_LENGTH = 10


class CalendarWidget(BaseWidget):
    """Shows the next event of a calendar.

    One widget per calendar (birthdays, appointments, holidays,
    vacation). Only shown when the event is within the configured
    lookahead:

        today     -> "Oma"
        tomorrow  -> "Oma Morgen"
        X days    -> "Oma 3T"
    """

    def __init__(
        self,
        hass,
        entity: str,
        icon: str,
        days: int = 3,
        priority: int = 350,
    ):
        super().__init__(hass)

        self.entity = entity
        self.icon = icon
        self.days = days
        self.priority = priority

    def render(self):

        state = self.hass.states.get(self.entity)

        if state is None or state.state in ("unknown", "unavailable"):
            return None

        message = state.attributes.get("message")
        start = state.attributes.get("start_time")

        if not message or not start:
            return None

        event_date = self._parse_date(start)

        if event_date is None:
            return None

        days_until = (event_date - date.today()).days

        if days_until < 0 or days_until > self.days:
            return None

        message = shorten(message, MAX_MESSAGE_LENGTH)

        if days_until == 0:
            value = message
            importance = 80
        elif days_until == 1:
            value = f"{message} Morgen"
            importance = 65
        else:
            value = f"{message} {days_until}T"
            importance = 45

        return DashboardItem(
            icon=self.icon,
            value=value,
            priority=self.priority,
            importance=importance,
        )

    @staticmethod
    def _parse_date(value: str) -> date | None:
        """Parses '2026-07-15', '2026-07-15 09:00:00' and ISO formats."""

        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
