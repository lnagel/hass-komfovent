"""Config flow for Komfovent integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN


class KomfoventConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Komfovent."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
