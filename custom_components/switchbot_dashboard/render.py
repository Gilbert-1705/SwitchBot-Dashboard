"""Gemeinsame Render-Funktion für Services und Updater."""

from datetime import datetime

from .const import MAX_ITEMS, PREVIEW_ENTITY_ID
from .dashboard import DashboardRenderer
from .widgets.manager import WidgetManager


def render_dashboard(hass, configs=None, max_items: int = MAX_ITEMS) -> str:
    """Rendert alle Widgets zu einer Displayzeile."""

    renderer = DashboardRenderer(max_items=max_items)
    manager = WidgetManager(hass, configs=configs)

    for widget in manager.widgets():
        renderer.add(widget.render())

    return renderer.render()


def publish_preview(hass, text: str, sent: bool):
    """Spiegelt die gerenderte Zeile als lokale Entity.

    ``sensor.switchbot_dashboard`` zeigt in Home Assistant immer den
    aktuellen Displayinhalt — praktisch für Entwicklung (History,
    Dashboards, Template-Debugging) ohne aufs E-Paper zu schauen.
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
