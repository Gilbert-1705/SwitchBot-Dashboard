from .base import BaseWidget, DashboardItem
from ..formatters.power import PowerFormatter
from ..icons import Icons


class SolarWidget(BaseWidget):
    """PV production.

        ☀ 3.2kW    producing (background info)
        (nothing)  at night or below min_power

    Production is never urgent — the widget fills free slots but
    never displaces anything important.
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
