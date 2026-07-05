from .dashboard import DashboardRenderer
from .widgets.manager import WidgetManager
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN


async def async_send_text(call: ServiceCall):

    api = call.hass.data[DOMAIN]["api"]

    text = call.data.get("text", "")

    result = await api.send_text(text)

    return result


async def async_refresh(call: ServiceCall):
    pass

async def async_preview(call: ServiceCall):

    renderer = DashboardRenderer()
    manager = WidgetManager(call.hass)

    for widget in manager.widgets():

        item = widget.render()

        if item is not None:
            renderer.add(item)

    api = call.hass.data[DOMAIN]["api"]

    await api.send_text(
        renderer.render()
    )

async def async_register_services(hass: HomeAssistant):

    hass.services.async_register(
        DOMAIN,
        "send_text",
        async_send_text,
    )

    hass.services.async_register(
        DOMAIN,
        "refresh",
        async_refresh,
    )
    hass.services.async_register(
        DOMAIN,
        "preview",
        async_preview,
    )