"""Config flow for Komfovent integration."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    OPT_STEP_CO2,
    OPT_STEP_FLOW,
    OPT_STEP_HUMIDITY,
    OPT_STEP_TEMPERATURE,
    OPT_STEP_TIMER,
    OPT_STEP_VOC,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(OPT_STEP_FLOW): vol.Coerce(float),
        vol.Optional(OPT_STEP_TEMPERATURE): vol.Coerce(float),
        vol.Optional(OPT_STEP_HUMIDITY): vol.Coerce(float),
        vol.Optional(OPT_STEP_CO2): vol.Coerce(float),
        vol.Optional(OPT_STEP_VOC): vol.Coerce(float),
        vol.Optional(OPT_STEP_TIMER): vol.Coerce(float),
    }
)


class KomfoventConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Komfovent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CONFIG_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration."""
        errors = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry=reconfigure_entry,
                title=user_input[CONF_NAME],
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONFIG_SCHEMA, user_input or reconfigure_entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler for Komfovent."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
