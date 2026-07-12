"""UI setup: token, secret and device ID via the interface.

Widgets are still configured via YAML (see docs/configuration.md) —
the config flow only replaces the credentials configuration.
"""

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_SECRET,
    CONF_DEVICE_ID,
)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_TOKEN): str,
    vol.Required(CONF_SECRET): str,
    vol.Required(CONF_DEVICE_ID): str,
})


class SwitchBotDashboardConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):

    VERSION = 1

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
