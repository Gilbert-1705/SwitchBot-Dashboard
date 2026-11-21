from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_DRY_RUN,
    CONF_MAX_ITEMS,
    CONF_QUIET_MAX_ITEMS,
    CONF_WIDGETS,
    DOMAIN,
    MAX_ITEMS,
    QUIET_MAX_ITEMS,
    SEPARATOR,
)
from .render import publish_preview, render_dashboard
from .text import keep_items_together


async def async_send_text(call: ServiceCall):

    api = call.hass.data[DOMAIN]["api"]

    text = call.data.get("text", "")

    result = await api.send_text(text)

    return result


async def async_refresh(call: ServiceCall):
    """Forces an immediate refresh (bypasses the rate limit)."""

    data = call.hass.data[DOMAIN]
    updater = data.get("updater")

    if updater is not None:
        await updater.async_refresh(force=True)
        return

    # Without an updater (auto_refresh: false): render and send directly
    await async_preview(call)


async def async_preview(call: ServiceCall):

    data = call.hass.data[DOMAIN]

    text = render_dashboard(
        call.hass,
        configs=data.get(CONF_WIDGETS),
        max_items=data.get(CONF_MAX_ITEMS, MAX_ITEMS),
        quiet_max_items=data.get(CONF_QUIET_MAX_ITEMS, QUIET_MAX_ITEMS),
    )

    dry_run = data.get(CONF_DRY_RUN, False)

    publish_preview(call.hass, text, sent=not dry_run)

    if dry_run:
        return

    await data["api"].send_text(keep_items_together(text, SEPARATOR))


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
