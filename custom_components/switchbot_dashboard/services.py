from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_MAX_ITEMS, CONF_WIDGETS, DOMAIN, MAX_ITEMS
from .render import render_dashboard


async def async_send_text(call: ServiceCall):

    api = call.hass.data[DOMAIN]["api"]

    text = call.data.get("text", "")

    result = await api.send_text(text)

    return result


async def async_refresh(call: ServiceCall):
    """Erzwingt einen sofortigen Refresh (umgeht das Rate-Limit)."""

    data = call.hass.data[DOMAIN]
    updater = data.get("updater")

    if updater is not None:
        await updater.async_refresh(force=True)
        return

    # Ohne Updater (auto_refresh: false): direkt rendern und senden
    await async_preview(call)


async def async_preview(call: ServiceCall):

    data = call.hass.data[DOMAIN]

    text = render_dashboard(
        call.hass,
        configs=data.get(CONF_WIDGETS),
        max_items=data.get(CONF_MAX_ITEMS, MAX_ITEMS),
    )

    await data["api"].send_text(text)


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
