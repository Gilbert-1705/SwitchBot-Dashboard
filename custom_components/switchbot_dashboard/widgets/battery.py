from .base import BaseWidget, DashboardItem
from ..icons import Icons


class BatteryWidget(BaseWidget):
    """Generic battery widget: PV storage, e-bike, vacuum, ...

        🔋 eBike 15%    battery low -> charge (important)
        🔋 eBike 85%    with show_always: background info
        (nothing)       battery ok and show_always off

    Configure one widget instance per battery with its own name.
    """

    def __init__(
        self,
        hass,
        entity: str,
        name: str = "",
        icon: str = Icons.BATTERY,
        min_level: float = 20.0,
        show_always: bool = False,
        priority: int = 620,
    ):
        super().__init__(hass)

        self.entity = entity
        self.name = name
        self.icon = icon
        self.min_level = min_level
        self.show_always = show_always
        self.priority = priority

    def render(self):

        state = self.hass.states.get(self.entity)

        if state is None:
            return None

        try:
            level = float(state.state)
        except (ValueError, TypeError):
            return None

        value = f"{self.name} {level:.0f}%".strip()

        if level <= self.min_level:
            importance = 65
        elif self.show_always:
            importance = 15
        else:
            return None

        return DashboardItem(
            icon=self.icon,
            value=value,
            priority=self.priority,
            importance=importance,
        )
