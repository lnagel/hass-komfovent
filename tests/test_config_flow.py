"""Tests for Komfovent config flow."""

from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT
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

# ==================== Config Flow Tests ====================


class TestKomfoventConfigFlow:
    """Tests for KomfoventConfigFlow."""

    async def test_user_step_shows_form(self, hass):
        """Test user step shows form when no input."""
        flow = KomfoventConfigFlow()
        flow.hass = hass
        result = await flow.async_step_user()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    @pytest.mark.parametrize(
        ("input_data", "expected_title"),
        [
            (
                {CONF_NAME: "My Komfovent", CONF_HOST: "192.168.1.100", CONF_PORT: 502},
                "My Komfovent",
            ),
            (
                {
                    CONF_NAME: DEFAULT_NAME,
                    CONF_HOST: "10.0.0.50",
                    CONF_PORT: DEFAULT_PORT,
                },
                DEFAULT_NAME,
            ),
            (
                {
                    CONF_NAME: "With Password",
                    CONF_HOST: "192.168.1.100",
                    CONF_PORT: 502,
                    CONF_PASSWORD: "secret123",
                },
                "With Password",
            ),
        ],
    )
    async def test_user_step_creates_entry(self, hass, input_data, expected_title):
        """Test user step creates entry with valid input."""
        flow = KomfoventConfigFlow()
        flow.hass = hass
        result = await flow.async_step_user(input_data)
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == expected_title
        assert result["data"] == input_data


class TestReconfigureStep:
    """Tests for reconfigure step."""

    @pytest.fixture
    def existing_entry(self):
        """Create existing entry for reconfigure tests."""
        return MockConfigEntry(
            domain=DOMAIN,
            entry_id="test_entry_id",
            title="Existing Device",
            data={
                CONF_NAME: "Existing Device",
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 502,
            },
        )

    async def test_reconfigure_shows_form(self, hass, existing_entry):
        """Test reconfigure step shows form with existing data."""
        flow = KomfoventConfigFlow()
        flow.hass = hass
        with patch.object(flow, "_get_reconfigure_entry", return_value=existing_entry):
            result = await flow.async_step_reconfigure()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

    async def test_reconfigure_updates_entry(self, hass, existing_entry):
        """Test reconfigure step updates entry with new data."""
        flow = KomfoventConfigFlow()
        flow.hass = hass
        new_data = {CONF_NAME: "New Name", CONF_HOST: "192.168.1.200", CONF_PORT: 503}
        with (
            patch.object(flow, "_get_reconfigure_entry", return_value=existing_entry),
            patch.object(
                flow,
                "async_update_reload_and_abort",
                return_value={
                    "type": FlowResultType.ABORT,
                    "reason": "reconfigure_successful",
                },
            ) as mock_update,
        ):
            await flow.async_step_reconfigure(new_data)
            mock_update.assert_called_once_with(
                entry=existing_entry, title="New Name", data_updates=new_data
            )

    async def test_reconfigure_updates_entry_with_password(self, hass, existing_entry):
        """Test reconfigure step updates entry with password."""
        flow = KomfoventConfigFlow()
        flow.hass = hass
        new_data = {
            CONF_NAME: "New Name",
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 503,
            CONF_PASSWORD: "newpassword",
        }
        with (
            patch.object(flow, "_get_reconfigure_entry", return_value=existing_entry),
            patch.object(
                flow,
                "async_update_reload_and_abort",
                return_value={
                    "type": FlowResultType.ABORT,
                    "reason": "reconfigure_successful",
                },
            ) as mock_update,
        ):
            await flow.async_step_reconfigure(new_data)
            mock_update.assert_called_once_with(
                entry=existing_entry, title="New Name", data_updates=new_data
            )


class TestOptionsFlow:
    """Tests for options flow."""

    async def test_async_get_options_flow(self):
        """Test getting options flow handler."""
        entry = MockConfigEntry(domain=DOMAIN, entry_id="test")
        assert isinstance(
            KomfoventConfigFlow.async_get_options_flow(entry), OptionsFlowHandler
        )

    @pytest.mark.parametrize(
        ("options", "user_input", "expected_type"),
        [
            (
                {OPT_STEP_FLOW: 10.0, OPT_STEP_TEMPERATURE: 0.5},
                None,
                FlowResultType.FORM,
            ),
            ({}, {OPT_STEP_TEMPERATURE: 0.5}, FlowResultType.CREATE_ENTRY),
            (
                {},
                {
                    OPT_STEP_FLOW: 5.0,
                    OPT_STEP_TEMPERATURE: 1.0,
                    OPT_STEP_HUMIDITY: 5.0,
                    OPT_STEP_CO2: 50.0,
                    OPT_STEP_VOC: 10.0,
                    OPT_STEP_TIMER: 1.0,
                },
                FlowResultType.CREATE_ENTRY,
            ),
        ],
    )
    async def test_options_step(self, hass, options, user_input, expected_type):
        """Test options step shows form or saves options."""
        entry = MockConfigEntry(
            domain=DOMAIN, entry_id="test_entry_id", options=options
        )
        flow = OptionsFlowHandler()
        flow.hass = hass
        flow._config_entry = entry
        result = await flow.async_step_init(user_input)
        assert result["type"] == expected_type


# ==================== Schema Tests ====================


class TestSchemas:
    """Tests for config and options schemas."""

    def test_config_schema_requires_host(self):
        """Test config schema requires host."""
        with pytest.raises(vol.MultipleInvalid):
            CONFIG_SCHEMA({CONF_NAME: "Test"})

    @pytest.mark.parametrize(
        ("data", "expected_name", "expected_port"),
        [
            ({CONF_HOST: "192.168.1.100"}, DEFAULT_NAME, DEFAULT_PORT),
            (
                {CONF_NAME: "Test", CONF_HOST: "192.168.1.100", CONF_PORT: 502},
                "Test",
                502,
            ),
        ],
    )
    def test_config_schema_defaults(self, data, expected_name, expected_port):
        """Test config schema applies default values."""
        result = CONFIG_SCHEMA(data)
        assert result[CONF_NAME] == expected_name
        assert result[CONF_PORT] == expected_port

    def test_config_schema_password_optional(self):
        """Test config schema accepts data without password."""
        data = {CONF_NAME: "Test", CONF_HOST: "192.168.1.100", CONF_PORT: 502}
        result = CONFIG_SCHEMA(data)
        assert CONF_PASSWORD not in result

    def test_config_schema_password_included(self):
        """Test config schema accepts data with password."""
        data = {
            CONF_NAME: "Test",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_PASSWORD: "test_password",
        }
        result = CONFIG_SCHEMA(data)
        assert result[CONF_PASSWORD] == "test_password"

    def test_options_schema_accepts_valid(self):
        """Test options schema accepts valid data."""
        data = {OPT_STEP_FLOW: 10.0, OPT_STEP_TEMPERATURE: 0.5}
        result = OPTIONS_SCHEMA(data)
        assert result[OPT_STEP_FLOW] == data[OPT_STEP_FLOW]
        assert result[OPT_STEP_TEMPERATURE] == data[OPT_STEP_TEMPERATURE]
        assert result[OPT_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL

    def test_options_schema_coerces_types(self):
        """Test options schema coerces string to float."""
        result = OPTIONS_SCHEMA({OPT_STEP_FLOW: "10"})
        assert result[OPT_STEP_FLOW] == 10.0

    def test_options_schema_accepts_empty(self):
        """Test options schema accepts empty dict and applies defaults."""
        result = OPTIONS_SCHEMA({})
        assert result[OPT_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL
