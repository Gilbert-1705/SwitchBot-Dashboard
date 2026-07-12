from ..dashboard.item import DashboardItem


class BaseWidget:
    """Base class for all dashboard widgets."""

    # pipeline options, set by the widget manager (see render.py)
    group: str = ""
    boost = None

    def __init__(self, hass):
        self.hass = hass

    def render(self) -> DashboardItem | None:
        raise NotImplementedError
