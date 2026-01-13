"""Tests for Komfovent config flow."""

from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.config_flow import (
    CONFIG_SCHEMA,
    OPTIONS_SCHEMA,
    KomfoventConfigFlow,
    OptionsFlowHandler,
)
from custom_components.komfovent.const import (
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


class TestKomfoventConfigFlow:
    """Tests for KomfoventConfigFlow."""

    async def test_user_step_shows_form(self, hass):
        """Test user step shows form when no input."""
        flow = KomfoventConfigFlow()
        flow.hass = hass

        result = await flow.async_step_user()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_user_step_creates_entry(self, hass):
        """Test user step creates entry with valid input."""
        flow = KomfoventConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_NAME: "My Komfovent",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "My Komfovent"
        assert result["data"] == user_input

    async def test_user_step_default_values(self, hass):
        """Test user step uses default values."""
        flow = KomfoventConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_NAME: DEFAULT_NAME,
            CONF_HOST: "10.0.0.50",
            CONF_PORT: DEFAULT_PORT,
        }

        result = await flow.async_step_user(user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_NAME] == DEFAULT_NAME
        assert result["data"][CONF_PORT] == DEFAULT_PORT


class TestReconfigureStep:
    """Tests for reconfigure step."""

    async def test_reconfigure_step_shows_form(self, hass):
        """Test reconfigure step shows form with existing data."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            title="Existing Device",
            data={
                CONF_NAME: "Existing Device",
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 502,
            },
        )

        flow = KomfoventConfigFlow()
        flow.hass = hass

        with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
            result = await flow.async_step_reconfigure()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        assert result["errors"] == {}

    async def test_reconfigure_step_updates_entry(self, hass):
        """Test reconfigure step updates entry with new data."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            title="Old Name",
            data={
                CONF_NAME: "Old Name",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
            },
        )

        flow = KomfoventConfigFlow()
        flow.hass = hass

        user_input = {
            CONF_NAME: "New Name",
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 503,
        }

        with (
            patch.object(flow, "_get_reconfigure_entry", return_value=entry),
            patch.object(
                flow,
                "async_update_reload_and_abort",
                return_value={
                    "type": FlowResultType.ABORT,
                    "reason": "reconfigure_successful",
                },
            ) as mock_update,
        ):
            await flow.async_step_reconfigure(user_input)

            mock_update.assert_called_once_with(
                entry=entry,
                title="New Name",
                data_updates=user_input,
            )


class TestOptionsFlow:
    """Tests for options flow."""

    async def test_async_get_options_flow(self):
        """Test getting options flow handler."""
        entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
        handler = KomfoventConfigFlow.async_get_options_flow(entry)

        assert isinstance(handler, OptionsFlowHandler)

    async def test_options_step_shows_form(self, hass):
        """Test options step shows form with current options."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            options={
                OPT_STEP_FLOW: 10.0,
                OPT_STEP_TEMPERATURE: 0.5,
            },
        )

        flow = OptionsFlowHandler()
        flow.hass = hass
        # Use internal attribute to avoid deprecation
        flow._config_entry = entry

        result = await flow.async_step_init()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_step_saves_options(self, hass):
        """Test options step saves new options."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            options={},
        )

        flow = OptionsFlowHandler()
        flow.hass = hass
        flow._config_entry = entry

        user_input = {
            OPT_STEP_FLOW: 5.0,
            OPT_STEP_TEMPERATURE: 1.0,
            OPT_STEP_HUMIDITY: 5.0,
            OPT_STEP_CO2: 50.0,
            OPT_STEP_VOC: 10.0,
            OPT_STEP_TIMER: 1.0,
        }

        result = await flow.async_step_init(user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == user_input

    async def test_options_step_partial_options(self, hass):
        """Test options step with only some options provided."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            options={},
        )

        flow = OptionsFlowHandler()
        flow.hass = hass
        flow._config_entry = entry

        user_input = {
            OPT_STEP_TEMPERATURE: 0.5,
        }

        result = await flow.async_step_init(user_input)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == user_input


class TestSchemas:
    """Tests for config and options schemas."""

    def test_config_schema_validates_required_fields(self):
        """Test config schema requires host."""
        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA({CONF_NAME: "Test"})  # Missing host

    def test_config_schema_accepts_valid_data(self):
        """Test config schema accepts valid data."""
        data = {
            CONF_NAME: "Test Device",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
        }
        result = CONFIG_SCHEMA(data)
        assert result == data

    def test_config_schema_uses_defaults(self):
        """Test config schema applies default values."""
        data = {
            CONF_HOST: "192.168.1.100",
        }
        result = CONFIG_SCHEMA(data)
        assert result[CONF_NAME] == DEFAULT_NAME
        assert result[CONF_PORT] == DEFAULT_PORT

    def test_options_schema_accepts_valid_data(self):
        """Test options schema accepts valid data."""
        data = {
            OPT_STEP_FLOW: 10.0,
            OPT_STEP_TEMPERATURE: 0.5,
        }
        result = OPTIONS_SCHEMA(data)
        assert result == data

    def test_options_schema_coerces_types(self):
        """Test options schema coerces string to float."""
        data = {
            OPT_STEP_FLOW: "10",  # String instead of float
        }
        result = OPTIONS_SCHEMA(data)
        assert result[OPT_STEP_FLOW] == 10.0
        assert isinstance(result[OPT_STEP_FLOW], float)

    def test_options_schema_accepts_empty(self):
        """Test options schema accepts empty dict."""
        result = OPTIONS_SCHEMA({})
        assert result == {}
