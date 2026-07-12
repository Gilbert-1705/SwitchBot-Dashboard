import logging

from homeassistant.core import HomeAssistant

from .api import SwitchBotAPI
from .config.schema import ConfigError, build_widget_configs
from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_SECRET,
    CONF_DEVICE_ID,
    CONF_AUTO_REFRESH,
    CONF_DRY_RUN,
    CONF_MAX_ITEMS,
    CONF_WIDGETS,
    MAX_ITEMS,
)
from .services import async_register_services
from .updater import DashboardUpdater

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """YAML-Setup (configuration.yaml)."""

    conf = config.get(DOMAIN)

    if conf is None:
        return True

    # Widgets aus configuration.yaml; ohne "widgets:"-Block gilt
    # weiterhin die Python-Konfiguration (widgets/config.py)
    widgets_conf = conf.get(CONF_WIDGETS)
    widgets = None

    if widgets_conf is not None:
        try:
            widgets = build_widget_configs(widgets_conf)
        except ConfigError as err:
            _LOGGER.error("Invalid widget configuration: %s", err)
            return False

    return await _async_setup_integration(
        hass,
        token=conf[CONF_TOKEN],
        secret=conf[CONF_SECRET],
        device_id=conf[CONF_DEVICE_ID],
        widgets=widgets,
        max_items=conf.get(CONF_MAX_ITEMS, MAX_ITEMS),
        auto_refresh=conf.get(CONF_AUTO_REFRESH, True),
        dry_run=conf.get(CONF_DRY_RUN, False),
    )


async def async_setup_entry(hass: HomeAssistant, entry):
    """UI-Setup (Config Flow). Widgets kommen weiterhin aus YAML."""

    data = hass.data.get(DOMAIN, {})

    return await _async_setup_integration(
        hass,
        token=entry.data[CONF_TOKEN],
        secret=entry.data[CONF_SECRET],
        device_id=entry.data[CONF_DEVICE_ID],
        widgets=data.get(CONF_WIDGETS),
        max_items=data.get(CONF_MAX_ITEMS, MAX_ITEMS),
        auto_refresh=True,
        dry_run=data.get(CONF_DRY_RUN, False),
    )


async def async_unload_entry(hass: HomeAssistant, entry):

    data = hass.data.get(DOMAIN, {})
    updater = data.get("updater")

    if updater is not None:
        updater.async_stop()
        data["updater"] = None

    return True


async def _async_setup_integration(
    hass: HomeAssistant,
    token: str,
    secret: str,
    device_id: str,
    widgets,
    max_items: int,
    auto_refresh: bool,
    dry_run: bool = False,
):

    api = SwitchBotAPI(token, secret, device_id)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["api"] = api
    hass.data[DOMAIN][CONF_WIDGETS] = widgets
    hass.data[DOMAIN][CONF_MAX_ITEMS] = max_items
    hass.data[DOMAIN][CONF_DRY_RUN] = dry_run

    if dry_run:
        _LOGGER.warning(
            "Dry run enabled: dashboard is only published to %s, "
            "nothing is sent to the device",
            "sensor.switchbot_dashboard",
        )

    await async_register_services(hass)

    if auto_refresh:
        updater = DashboardUpdater(
            hass,
            api=api,
            configs=widgets,
            max_items=max_items,
            dry_run=dry_run,
        )
        hass.data[DOMAIN]["updater"] = updater
        await updater.async_start()

    return True
