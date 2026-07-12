from .base import BaseWidget, DashboardItem
from ..formatters.power import PowerFormatter
from ..icons import Icons


class SolarWidget(BaseWidget):
    """PV-Erzeugung.

        ☀ 3.2kW    Anlage produziert (Hintergrundinfo)
        (nichts)   nachts bzw. unter min_power

    Erzeugung ist nie dringend — das Widget füllt freie Plätze,
    verdrängt aber nichts Wichtiges.
    """

    def __init__(
        self,
        hass,
        entity: str,
        icon: str = Icons.SUN,
        min_power: float = 50.0,
        priority: int = 210,
    ):
        super().__init__(hass)

        self.entity = entity
        self.icon = icon
        self.min_power = min_power
        self.priority = priority
        self._formatter = PowerFormatter()

    def render(self):

        state = self.hass.states.get(self.entity)

        if state is None:
            return None

        try:
            power = float(state.state)
        except (ValueError, TypeError):
            return None

        if power < self.min_power:
            return None

        return DashboardItem(
            icon=self.icon,
            value=self._formatter.format(power),
            priority=self.priority,
            importance=15,
        )
