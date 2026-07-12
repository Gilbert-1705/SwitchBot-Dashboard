import logging

from homeassistant.core import HomeAssistant

from .api import SwitchBotAPI
from .config.schema import ConfigError, build_widget_configs
from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_SECRET,
    CONF_DEVICE_ID,
    CONF_MAX_ITEMS,
    CONF_WIDGETS,
    MAX_ITEMS,
)
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)


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

    # Widgets aus configuration.yaml; ohne "widgets:"-Block gilt
    # weiterhin die Python-Konfiguration (widgets/config.py)
    widgets_conf = conf.get(CONF_WIDGETS)

    if widgets_conf is not None:
        try:
            hass.data[DOMAIN][CONF_WIDGETS] = build_widget_configs(
                widgets_conf
            )
        except ConfigError as err:
            _LOGGER.error("Invalid widget configuration: %s", err)
            return False
    else:
        hass.data[DOMAIN][CONF_WIDGETS] = None

    hass.data[DOMAIN][CONF_MAX_ITEMS] = conf.get(
        CONF_MAX_ITEMS, MAX_ITEMS
    )

    await async_register_services(hass)

    return True