from ..dashboard.item import DashboardItem
from ..i18n import language_of, translate


class BaseWidget:
    """Base class for all dashboard widgets."""

    # pipeline options, set by the widget manager (see render.py)
    group: str = ""
    boost = None

    def __init__(self, hass):
        self.hass = hass

    def t(self, key: str) -> str:
        """Display text in the configured language (see i18n.py)."""

        return translate(language_of(self.hass), key)

    def render(self) -> DashboardItem | None:
        raise NotImplementedError
