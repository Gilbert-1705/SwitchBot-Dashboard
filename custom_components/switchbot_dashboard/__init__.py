import logging
from dataclasses import replace

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.reload import async_integration_yaml_config
from homeassistant.helpers.storage import Store

from .api import SwitchBotAPI
from .config.schema import ConfigError, build_widget_configs
from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_SECRET,
    CONF_DEVICE_ID,
    CONF_DRY_RUN,
    CONF_MAX_ITEMS,
    CONF_QUIET_MAX_ITEMS,
    CONF_FIT_DISPLAY,
    CONF_WIDGETS,
    PREVIEW_ENTITY_ID,
)
from .i18n import LANGUAGE_KEY
from .services import async_register_services
from .settings import (
    Settings,
    credentials_from,
    settings_from_yaml,
    with_options,
)
from .tracker import TRACKER_KEY, SinceTracker
from .updater import DashboardUpdater
from .widget_forms import SUBENTRY_TYPE

_LOGGER = logging.getLogger(__name__)

# keys in hass.data[DOMAIN]
KEY_YAML_SETTINGS = "yaml_settings"
KEY_ENTRY_OPTIONS = "entry_options"
KEY_CREDENTIALS = "credentials"
KEY_UPDATER = "updater"
KEY_API = "api"
KEY_ENTRY_WIDGETS = "entry_widgets"

ISSUE_YAML_MIGRATED = "yaml_migrated"

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.since"

SERVICE_RELOAD = "reload"


async def async_setup(hass: HomeAssistant, config: dict):
    """YAML setup (configuration.yaml).

    The block may hold everything (credentials, options, widgets) or
    only options and widgets - then the credentials come from a
    config entry created in the UI.
    """

    conf = config.get(DOMAIN)

    if conf is None:
        _clear_yaml_leftover(hass)
        return True

    try:
        settings = settings_from_yaml(conf)
        credentials = credentials_from(conf)
    except ConfigError as err:
        _LOGGER.error("Invalid configuration: %s", err)
        return False

    data = hass.data.setdefault(DOMAIN, {})
    data[KEY_YAML_SETTINGS] = settings

    if credentials is None:
        # options/widgets only: a config entry starts the integration
        return True

    config_entries = getattr(hass, "config_entries", None)

    if config_entries is not None:

        if config_entries.async_entries(DOMAIN):
            # already in the UI: the config entry runs the dashboard,
            # the YAML block is a leftover
            _report_yaml_leftover(hass)
            return True

        # first start with a full YAML block: move it into the UI once
        hass.async_create_task(
            _async_import_or_run_yaml(hass, conf, credentials, settings)
        )
        return True

    data[KEY_CREDENTIALS] = credentials

    await _async_register_services(hass)
    await _async_start(hass, settings)

    return True


async def _async_import_or_run_yaml(hass, conf, credentials, settings):
    """Imports the YAML block into a config entry.

    Should the import fail, the dashboard keeps running from YAML as
    before - a failed migration must not leave the display dark.
    """

    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=dict(conf),
        )
    except Exception as err:  # noqa: BLE001 - keep the display running
        _LOGGER.error("Import into the UI failed, using YAML: %s", err)
        result = None

    if result is not None and result.get("type") in (
        "create_entry", "abort"
    ):
        # create_entry: the new entry starts the dashboard
        # abort: an entry for this device exists already
        return

    data = hass.data[DOMAIN]
    data[KEY_CREDENTIALS] = credentials
    await _async_register_services(hass)
    await _async_start(hass, settings)


async def async_setup_entry(hass: HomeAssistant, entry):
    """UI setup (config flow).

    Widgets come from the widget subentries of the entry; without any,
    from the ``widgets:`` list in configuration.yaml.
    """

    data = hass.data.setdefault(DOMAIN, {})

    data[KEY_CREDENTIALS] = (
        entry.data[CONF_TOKEN],
        entry.data[CONF_SECRET],
        entry.data[CONF_DEVICE_ID],
    )
    data[KEY_ENTRY_OPTIONS] = dict(entry.options)
    data[KEY_ENTRY_WIDGETS] = entry_widgets(entry)

    await _async_register_services(hass)
    await _async_start(hass, _effective_settings(hass))

    # Options changed in the UI: reload the entry, no restart needed
    entry.async_on_unload(
        entry.add_update_listener(_async_options_updated)
    )

    return True


async def _async_options_updated(hass: HomeAssistant, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry):

    _stop_updater(hass)

    return True


def entry_widgets(entry) -> list:
    """Widget configs from the subentries; invalid ones are skipped."""

    configs = []
    subentries = getattr(entry, "subentries", None) or {}

    for subentry in subentries.values():

        if subentry.subentry_type != SUBENTRY_TYPE:
            continue

        try:
            configs.extend(build_widget_configs([dict(subentry.data)]))
        except ConfigError as err:
            _LOGGER.error(
                "Widget '%s' is invalid and skipped: %s", subentry.title, err
            )

    return configs


def _effective_settings(hass: HomeAssistant) -> Settings:
    """YAML settings with the options and widgets of the entry on top."""

    data = hass.data[DOMAIN]

    settings = data.get(KEY_YAML_SETTINGS) or Settings()

    if data.get(KEY_ENTRY_WIDGETS):
        settings = replace(settings, widgets=data[KEY_ENTRY_WIDGETS])

    try:
        return with_options(settings, data.get(KEY_ENTRY_OPTIONS))
    except ConfigError as err:
        _LOGGER.error("Ignoring invalid options: %s", err)
        return settings


def _report_yaml_leftover(hass: HomeAssistant):
    """Repair notice: the YAML block is no longer used."""

    _LOGGER.warning(
        "switchbot_dashboard is configured in the UI; the YAML block in "
        "configuration.yaml is ignored and can be removed"
    )

    try:
        from homeassistant.helpers import issue_registry as ir
    except ImportError:  # tests without Home Assistant
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_YAML_MIGRATED,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_YAML_MIGRATED,
    )


def _stop_updater(hass: HomeAssistant):

    data = hass.data.get(DOMAIN, {})
    updater = data.get(KEY_UPDATER)

    if updater is not None:
        updater.async_stop()
        data[KEY_UPDATER] = None

    return updater


async def _async_start(hass: HomeAssistant, settings: Settings):
    """(Re)starts the dashboard with the given settings.

    Used at start-up and by reloads. The previous updater is stopped
    first; what it last sent is handed over so an unchanged dashboard
    is not transmitted again.
    """

    data = hass.data[DOMAIN]

    previous = _stop_updater(hass)

    token, secret, device_id = data[KEY_CREDENTIALS]
    api = SwitchBotAPI(token, secret, device_id)

    data[KEY_API] = api
    data[CONF_WIDGETS] = settings.widgets
    data[CONF_MAX_ITEMS] = settings.max_items
    data[CONF_QUIET_MAX_ITEMS] = settings.quiet_max_items
    data[CONF_FIT_DISPLAY] = settings.fit_display
    data[CONF_DRY_RUN] = settings.dry_run
    data[LANGUAGE_KEY] = settings.language

    if TRACKER_KEY not in data:
        tracker = SinceTracker(Store(hass, STORAGE_VERSION, STORAGE_KEY))
        await tracker.async_load()
        data[TRACKER_KEY] = tracker

    if settings.dry_run:
        _LOGGER.warning(
            "Dry run enabled: dashboard is only published to %s, "
            "nothing is sent to the device",
            PREVIEW_ENTITY_ID,
        )

    if not settings.auto_refresh:
        return

    updater = DashboardUpdater(
        hass,
        api=api,
        configs=settings.widgets,
        max_items=settings.max_items,
        dry_run=settings.dry_run,
        quiet_max_items=settings.quiet_max_items,
        fit_display=settings.fit_display,
    )

    if previous is not None and previous.dry_run == settings.dry_run:
        updater.adopt_state(previous)

    data[KEY_UPDATER] = updater
    await updater.async_start()


async def _async_register_services(hass: HomeAssistant):

    await async_register_services(hass)

    async def async_handle_reload(call: ServiceCall):
        await async_reload(hass)

    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD,
        async_handle_reload,
    )


async def async_reload(hass: HomeAssistant) -> bool:
    """Reads configuration.yaml again and applies it without a restart.

    An invalid configuration is reported and the running one is kept.
    """

    data = hass.data[DOMAIN]

    try:
        config = await async_integration_yaml_config(hass, DOMAIN)
    except Exception as err:  # noqa: BLE001 - any YAML problem
        _LOGGER.error("Reload failed, keeping the current config: %s", err)
        return False

    conf = (config or {}).get(DOMAIN)

    if conf is None:
        if KEY_ENTRY_OPTIONS not in data:
            _LOGGER.error(
                "Reload failed: no '%s:' block in configuration.yaml",
                DOMAIN,
            )
            return False

        # UI setup without a YAML block: back to defaults + options
        data.pop(KEY_YAML_SETTINGS, None)
    else:
        try:
            settings = settings_from_yaml(conf)
            credentials = credentials_from(conf)
        except ConfigError as err:
            _LOGGER.error(
                "Invalid configuration, keeping the current one: %s", err
            )
            return False

        data[KEY_YAML_SETTINGS] = settings

        if credentials is not None:
            data[KEY_CREDENTIALS] = credentials

    if KEY_CREDENTIALS not in data:
        _LOGGER.error("Reload failed: no credentials configured")
        return False

    await _async_start(hass, _effective_settings(hass))

    _LOGGER.info("Configuration reloaded")

    return True


def _clear_yaml_leftover(hass: HomeAssistant):

    try:
        from homeassistant.helpers import issue_registry as ir
    except ImportError:  # tests without Home Assistant
        return

    ir.async_delete_issue(hass, DOMAIN, ISSUE_YAML_MIGRATED)
