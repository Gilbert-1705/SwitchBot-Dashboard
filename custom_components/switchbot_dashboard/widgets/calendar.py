from datetime import date

from .base import BaseWidget, DashboardItem


class CalendarWidget(BaseWidget):
    """Zeigt das nächste Ereignis eines Kalenders an.

    Ein Widget pro Kalender (Geburtstage, Termine, Feiertage,
    Urlaub). Angezeigt wird nur, wenn das Ereignis innerhalb der
    konfigurierten Vorlaufzeit liegt:

        Heute   -> "Oma"
        Morgen  -> "Oma Morgen"
        X Tage  -> "Oma 3T"
    """

    requires_config = True

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

        if days_until == 0:
            value = message
        elif days_until == 1:
            value = f"{message} Morgen"
        else:
            value = f"{message} {days_until}T"

        return DashboardItem(
            icon=self.icon,
            value=value,
            priority=self.priority,
        )

    @staticmethod
    def _parse_date(value: str) -> date | None:
        """Parst '2026-07-15', '2026-07-15 09:00:00' und ISO-Formate."""

        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
