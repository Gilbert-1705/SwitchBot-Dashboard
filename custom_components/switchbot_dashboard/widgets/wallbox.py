from .base import BaseWidget, DashboardItem
from ..formatters.power import PowerFormatter
from ..icons import Icons

# compared case-insensitively
CHARGING_STATES = ("charging", "on", "true", "laden", "lädt")
DONE_STATES = ("complete", "completed", "finished", "charged", "full")
ERROR_STATES = ("error", "fault", "faulted", "failed")


class WallboxWidget(BaseWidget):
    """Wallbox / charging station.

        🔌 WB 7.4kW     charging, with power_entity
        🔌 WB lädt      charging, without power reading
        🔌 WB Voll      charging finished, car still plugged in
        🔌 WB Fehler    the wallbox reports an error
        (nothing)       idle

    For the car's state of charge use the ``ev`` widget; this one
    covers the charging point itself.
    """

    def __init__(
        self,
        hass,
        status_entity: str,
        power_entity: str = "",
        name: str = "",
        icon: str = Icons.PLUG,
        priority: int = 640,
    ):
        super().__init__(hass)

        self.status_entity = status_entity
        self.power_entity = power_entity
        self.name = name
        self.icon = icon
        self.priority = priority
        self._formatter = PowerFormatter()

    def render(self):

        state = self.hass.states.get(self.status_entity)

        if state is None:
            return None

        status = str(state.state).lower()

        if status in ERROR_STATES:
            return self._item(self.t("error"), 85)

        if status in CHARGING_STATES:
            return self._item(self._charging_detail(), 30)

        if status in DONE_STATES:
            return self._item(self.t("full"), 45)

        return None

    def _charging_detail(self) -> str:

        if self.power_entity:
            power = self.hass.states.get(self.power_entity)

            try:
                watts = float(power.state)
            except (AttributeError, ValueError, TypeError):
                watts = 0

            if watts > 0:
                return self._formatter.format(watts)

        return self.t("charging")

    def _item(self, text: str, importance: int) -> DashboardItem:

        return DashboardItem(
            icon=self.icon,
            value=f"{self.name} {text}".strip(),
            priority=self.priority,
            importance=importance,
        )
