"""Shared render function for services and updater."""

from datetime import datetime

from .const import MAX_ITEMS, PREVIEW_ENTITY_ID, QUIET_MAX_ITEMS, SEPARATOR
from .context import active_boost, apply_boost
from .dashboard import DashboardRenderer
from .simulator import simulate
from .text import keep_items_together
from .widgets.manager import WidgetManager


def render_dashboard(
    hass,
    configs=None,
    max_items: int = MAX_ITEMS,
    quiet_max_items: int = QUIET_MAX_ITEMS,
    fit_display: bool = True,
) -> str:
    """Renders all widgets into one display line."""

    renderer = DashboardRenderer(
        max_items=max_items,
        quiet_max_items=quiet_max_items,
        fit_display=fit_display,
    )
    manager = WidgetManager(hass, configs=configs)

    for widget in manager.widgets():

        item = widget.render()

        if item is None:
            continue

        # pipeline options: groups and day context (see manager)
        if widget.group:
            item.group = widget.group

        if widget.boost:
            delta = active_boost(widget.boost)
            if delta:
                item.importance = apply_boost(item.importance, delta)

        renderer.add(item)

    return renderer.render()


def publish_preview(hass, text: str, sent: bool):
    """Mirrors the rendered line as a local entity.

    ``sensor.switchbot_dashboard`` always shows the current display
    content in Home Assistant — handy for development (history,
    dashboards, template debugging) without looking at the e-paper.
    """

    # predicted layout on the panel (see simulator.py)
    layout = simulate(keep_items_together(text, SEPARATOR))

    hass.states.async_set(
        PREVIEW_ENTITY_ID,
        text,
        {
            "friendly_name": "SwitchBot Dashboard",
            "icon": "mdi:monitor-dashboard",
            "sent_to_device": sent,
            "rendered_at": datetime.now().isoformat(timespec="seconds"),
            "display_lines": layout.readable_lines(),
            "display_fits": layout.fits,
            "display_scale": layout.scale,
        },
    )
