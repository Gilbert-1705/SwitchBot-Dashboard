"""Shared render function for services and updater."""

from datetime import datetime

from .const import MAX_ITEMS, PREVIEW_ENTITY_ID
from .dashboard import DashboardRenderer
from .widgets.manager import WidgetManager


def render_dashboard(hass, configs=None, max_items: int = MAX_ITEMS) -> str:
    """Renders all widgets into one display line."""

    renderer = DashboardRenderer(max_items=max_items)
    manager = WidgetManager(hass, configs=configs)

    for widget in manager.widgets():
        renderer.add(widget.render())

    return renderer.render()


def publish_preview(hass, text: str, sent: bool):
    """Mirrors the rendered line as a local entity.

    ``sensor.switchbot_dashboard`` always shows the current display
    content in Home Assistant — handy for development (history,
    dashboards, template debugging) without looking at the e-paper.
    """

    hass.states.async_set(
        PREVIEW_ENTITY_ID,
        text,
        {
            "friendly_name": "SwitchBot Dashboard",
            "icon": "mdi:monitor-dashboard",
            "sent_to_device": sent,
            "rendered_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
