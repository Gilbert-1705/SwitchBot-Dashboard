"""Gemeinsame Render-Funktion für Services und Updater."""

from .const import MAX_ITEMS
from .dashboard import DashboardRenderer
from .widgets.manager import WidgetManager


def render_dashboard(hass, configs=None, max_items: int = MAX_ITEMS) -> str:
    """Rendert alle Widgets zu einer Displayzeile."""

    renderer = DashboardRenderer(max_items=max_items)
    manager = WidgetManager(hass, configs=configs)

    for widget in manager.widgets():
        renderer.add(widget.render())

    return renderer.render()
