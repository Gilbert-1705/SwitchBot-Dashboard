from homeassistant.core import HomeAssistant

import logging

_LOGGER = logging.getLogger(__name__)

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
    
    _LOGGER.warning("CONF = %s", conf)
    _LOGGER.warning("TOKEN KEY = %s", CONF_TOKEN)
    _LOGGER.warning("SECRET KEY = %s", CONF_SECRET)
    _LOGGER.warning("DEVICE KEY = %s", CONF_DEVICE_ID)

    if conf is None:
        return True

    _LOGGER.warning("CONFIG KEYS = %s", list(conf.keys()))

    api = SwitchBotAPI(
        conf[CONF_TOKEN],
        conf[CONF_SECRET],
        conf[CONF_DEVICE_ID],
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["api"] = api

    await async_register_services(hass)

    return True