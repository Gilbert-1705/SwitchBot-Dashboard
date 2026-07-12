from ..dashboard.item import DashboardItem


class BaseWidget:
    """Base class for all dashboard widgets."""

    def __init__(self, hass):
        self.hass = hass

    def render(self) -> DashboardItem | None:
        raise NotImplementedError
