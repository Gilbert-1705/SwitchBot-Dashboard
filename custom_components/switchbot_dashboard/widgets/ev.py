from .base import BaseWidget, DashboardItem
from ..icons import Icons

CHARGING_STATES = ("on", "true", "charging", "laedt", "lädt")


class EvWidget(BaseWidget):
    """Electric vehicle: state of charge with charging status.

        🔌 64% lädt    currently charging
        🔌 12%         SoC low -> plug in (important)
        🔌 82%         with show_always: background info
        (nothing)      SoC ok and show_always off
    """

    def __init__(
        self,
        hass,
        soc_entity: str,
        charging_entity: str = "",
        name: str = "",
        icon: str = Icons.PLUG,
        min_level: float = 20.0,
        show_always: bool = False,
        priority: int = 630,
    ):
        super().__init__(hass)

        self.soc_entity = soc_entity
        self.charging_entity = charging_entity
        self.name = name
        self.icon = icon
        self.min_level = min_level
        self.show_always = show_always
        self.priority = priority

    def render(self):

        state = self.hass.states.get(self.soc_entity)

        if state is None:
            return None

        try:
            soc = float(state.state)
        except (ValueError, TypeError):
            return None

        base = f"{self.name} {soc:.0f}%".strip()

        if self._is_charging():
            return DashboardItem(
                icon=self.icon,
                value=f"{base} lädt",
                priority=self.priority,
                importance=30,
            )

        if soc <= self.min_level:
            # low SoC and not charging: plug in!
            return DashboardItem(
                icon=self.icon,
                value=base,
                priority=self.priority,
                importance=65,
            )

        if self.show_always:
            return DashboardItem(
                icon=self.icon,
                value=base,
                priority=self.priority,
                importance=15,
            )

        return None

    def _is_charging(self) -> bool:

        if not self.charging_entity:
            return False

        state = self.hass.states.get(self.charging_entity)

        if state is None:
            return False

        return str(state.state).lower() in CHARGING_STATES
