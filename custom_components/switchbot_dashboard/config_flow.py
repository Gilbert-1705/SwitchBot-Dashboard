"""UI setup: credentials via the interface, options changeable later.

The config flow asks for token, secret and device ID. The options
flow (the "Configure" button of the integration) changes the
display options at runtime - no restart needed. Widgets are still
configured via YAML (see docs/configuration.md).
"""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_AUTO_REFRESH,
    CONF_DEVICE_ID,
    CONF_DRY_RUN,
    CONF_MAX_ITEMS,
    CONF_QUIET_MAX_ITEMS,
    CONF_SECRET,
    CONF_TOKEN,
    MAX_ITEMS,
    QUIET_MAX_ITEMS,
)
from .i18n import DEFAULT_LANGUAGE, LANGUAGES
from .settings import CONF_LANGUAGE, MAX_SLOTS

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_TOKEN): str,
    vol.Required(CONF_SECRET): str,
    vol.Required(CONF_DEVICE_ID): str,
})


def options_schema(options) -> vol.Schema:
    """Form of the options flow, pre-filled with the current values."""

    slots = vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_SLOTS))

    return vol.Schema({
        vol.Optional(
            CONF_MAX_ITEMS,
            default=options.get(CONF_MAX_ITEMS, MAX_ITEMS),
        ): slots,
        vol.Optional(
            CONF_QUIET_MAX_ITEMS,
            default=options.get(CONF_QUIET_MAX_ITEMS, QUIET_MAX_ITEMS),
        ): slots,
        vol.Optional(
            CONF_AUTO_REFRESH,
            default=options.get(CONF_AUTO_REFRESH, True),
        ): bool,
        vol.Optional(
            CONF_DRY_RUN,
            default=options.get(CONF_DRY_RUN, False),
        ): bool,
        vol.Optional(
            CONF_LANGUAGE,
            default=options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
        ): vol.In(LANGUAGES),
    })


class SwitchBotDashboardConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SwitchBotDashboardOptionsFlow()

    async def async_step_user(self, user_input=None):

        errors = {}

        if user_input is not None:

            await self.async_set_unique_id(
                user_input[CONF_DEVICE_ID]
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="SwitchBot Dashboard",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )


class SwitchBotDashboardOptionsFlow(config_entries.OptionsFlow):
    """Display options, applied without a restart."""

    async def async_step_init(self, user_input=None):

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(self.config_entry.options),
        )
