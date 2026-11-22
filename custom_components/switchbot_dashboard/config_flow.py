"""UI setup: credentials, options and widgets in the interface.

The config flow asks for token, secret and device ID - or imports an
existing ``switchbot_dashboard:`` YAML block once. The options flow
(the "Configure" button) changes the display options at runtime.
Widgets are config subentries: "Add widget" on the integration page,
each with its own edit form (see widget_forms.py).
"""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_AUTO_REFRESH,
    CONF_DEVICE_ID,
    CONF_DRY_RUN,
    CONF_FIT_DISPLAY,
    CONF_MAX_ITEMS,
    CONF_QUIET_MAX_ITEMS,
    CONF_SECRET,
    CONF_TOKEN,
    MAX_ITEMS,
    QUIET_MAX_ITEMS,
)
from .config.schema import ConfigError
from .i18n import DEFAULT_LANGUAGE, LANGUAGES
from .settings import CONF_LANGUAGE, MAX_SLOTS, OPTION_KEYS
from .widget_forms import (
    SUBENTRY_TYPE,
    clean_input,
    describe_fields,
    import_payload,
    validate_widget,
    widget_title,
    widget_types,
)

_LOGGER = logging.getLogger(__name__)

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
        vol.Optional(
            CONF_FIT_DISPLAY,
            default=options.get(CONF_FIT_DISPLAY, True),
        ): bool,
    })


def widget_schema(widget_type: str, values=None) -> vol.Schema:
    """Form of one widget type, pre-filled with ``values``."""

    values = values or {}
    schema = {}

    for spec in describe_fields(widget_type):

        suggested = values.get(spec.name, spec.default)
        options = {}
        if suggested is not None:
            options["description"] = {"suggested_value": suggested}

        key = (
            vol.Required(spec.name, **options) if spec.required
            else vol.Optional(spec.name, **options)
        )

        if spec.kind == "entity":
            field = selector.EntitySelector()
        elif spec.kind == "bool":
            field = selector.BooleanSelector()
        elif spec.kind in ("int", "float"):
            field = selector.NumberSelector(selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                step=1 if spec.kind == "int" else "any",
            ))
        elif spec.kind == "select":
            field = selector.SelectSelector(selector.SelectSelectorConfig(
                options=list(spec.choices),
                mode=selector.SelectSelectorMode.DROPDOWN,
            ))
        elif spec.kind == "object":
            field = selector.ObjectSelector()
        else:
            field = selector.TextSelector()

        schema[key] = field

    return vol.Schema(schema)


def type_schema() -> vol.Schema:
    return vol.Schema({
        vol.Required("type"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=widget_types(),
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="widget_type",
            )
        ),
    })


class SwitchBotDashboardConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SwitchBotDashboardOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry):
        return {SUBENTRY_TYPE: WidgetSubentryFlow}

    async def async_step_import(self, import_data):
        """One-time import of the YAML block (credentials, options, widgets)."""

        payload = import_payload(import_data, OPTION_KEYS)

        await self.async_set_unique_id(payload["data"][CONF_DEVICE_ID])
        self._abort_if_unique_id_configured()

        subentries = []

        for widget in payload["widgets"]:
            subentries.append({
                "data": widget,
                "subentry_type": SUBENTRY_TYPE,
                "title": widget_title(widget),
                "unique_id": None,
            })

        _LOGGER.warning(
            "Imported the switchbot_dashboard YAML block (%d widgets) "
            "into the UI; the block in configuration.yaml can be removed",
            len(subentries),
        )

        return self.async_create_entry(
            title="SwitchBot Dashboard",
            data=payload["data"],
            options=payload["options"],
            subentries=subentries,
        )

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


class WidgetSubentryFlow(config_entries.ConfigSubentryFlow):
    """Add and edit one widget."""

    _type: str | None = None

    async def async_step_user(self, user_input=None):
        """First pick the widget type."""

        if user_input is not None:
            self._type = user_input["type"]
            return await self.async_step_widget()

        return self.async_show_form(step_id="user", data_schema=type_schema())

    async def async_step_widget(self, user_input=None):
        """The fields of the chosen type."""

        errors = {}
        placeholders = {"error": ""}

        if user_input is not None:
            data = clean_input(self._type, user_input)
            try:
                validate_widget(data)
            except ConfigError as err:
                errors["base"] = "invalid_widget"
                placeholders["error"] = str(err)
            else:
                self.hass.config_entries.async_schedule_reload(
                    self._get_entry().entry_id
                )
                return self.async_create_entry(
                    title=widget_title(data), data=data,
                )

        return self.async_show_form(
            step_id="widget",
            data_schema=widget_schema(self._type, user_input),
            errors=errors,
            description_placeholders={
                **placeholders, "type": self._type,
            },
        )

    async def async_step_reconfigure(self, user_input=None):
        """Edit an existing widget (its type stays)."""

        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        widget_type = subentry.data["type"]
        errors = {}
        placeholders = {"error": "", "type": widget_type}

        if user_input is not None:
            data = clean_input(widget_type, user_input)
            try:
                validate_widget(data)
            except ConfigError as err:
                errors["base"] = "invalid_widget"
                placeholders["error"] = str(err)
            else:
                self.hass.config_entries.async_schedule_reload(
                    entry.entry_id
                )
                return self.async_update_and_abort(
                    entry, subentry, data=data, title=widget_title(data),
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=widget_schema(
                widget_type, user_input or subentry.data
            ),
            errors=errors,
            description_placeholders=placeholders,
        )
