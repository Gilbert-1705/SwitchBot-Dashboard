from .base import BaseWidget, DashboardItem
from ..icons import Icons


class BatteryWidget(BaseWidget):
    """Generisches Akku-Widget: PV-Speicher, E-Bike, Staubsauger, ...

        🔋 eBike 15%    Akku niedrig -> laden (wichtig)
        🔋 eBike 85%    mit show_always: Hintergrundinfo
        (nichts)        Akku ok und show_always aus

    Konfiguration pro Akku eine Widget-Instanz mit eigenem Namen.
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
