"""Config flow for Komfovent integration."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPT_STEP_CO2,
    OPT_STEP_FLOW,
    OPT_STEP_HUMIDITY,
    OPT_STEP_TEMPERATURE,
    OPT_STEP_TIMER,
    OPT_STEP_VOC,
    OPT_UPDATE_INTERVAL,
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
        vol.Optional(
            OPT_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
        ): NumberSelector(
            NumberSelectorConfig(
                min=10,
                max=300,
                step=5,
                mode=NumberSelectorMode.SLIDER,
                unit_of_measurement="seconds",
            )
        ),
        vol.Optional(OPT_STEP_FLOW): vol.Coerce(float),
        vol.Optional(OPT_STEP_TEMPERATURE): vol.Coerce(float),
        vol.Optional(OPT_STEP_HUMIDITY): vol.Coerce(float),
        vol.Optional(OPT_STEP_CO2): vol.Coerce(float),
        vol.Optional(OPT_STEP_VOC): vol.Coerce(float),
        vol.Optional(OPT_STEP_TIMER): vol.Coerce(float),
    }
)


class KomfoventConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Komfovent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:  # noqa: ARG004
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(OptionsFlow):
    """Options flow handler for Komfovent."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
