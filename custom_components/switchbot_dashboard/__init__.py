from homeassistant.core import HomeAssistant

from .api import SwitchBotAPI
from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_SECRET,
    CONF_DEVICE_ID,
)
from .services import async_register_services


async def async_setup(hass: HomeAssistant, config: dict):

    conf = config.get(DOMAIN)

    if conf is None:
        return True

    api = SwitchBotAPI(
        conf[CONF_TOKEN],
        conf[CONF_SECRET],
        conf[CONF_DEVICE_ID],
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["api"] = api

    await async_register_services(hass)

    return True