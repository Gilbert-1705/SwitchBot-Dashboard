from ..dashboard.item import DashboardItem

class BaseWidget:
    """Base class for all dashboard widgets."""
    
    NAME = "base"

    def __init__(self, hass):
        self.hass = hass

    def enabled(self) -> bool:
        return True

    def render(self) -> DashboardItem | None:
        raise NotImplementedError