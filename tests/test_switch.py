"""Tests for Komfovent switch platform."""

import pytest
from homeassistant.components.switch import SwitchEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.switch import KomfoventSwitch, create_switches

# ==================== Data Tables ====================

EXPECTED_SWITCH_KEYS = {
    "power",
    "eco_mode",
    "auto_mode",
    "aq_impurity_control",
    "aq_humidity_control",
    "aq_electric_heater",
    "eco_free_heat_cool",
    "eco_heater_blocking",
    "eco_cooler_blocking",
    "away_electric_heater",
    "normal_electric_heater",
    "intensive_electric_heater",
    "boost_electric_heater",
    "kitchen_electric_heater",
    "fireplace_electric_heater",
    "override_electric_heater",
    "holidays_electric_heater",
}


# ==================== Base Switch Tests ====================


class TestKomfoventSwitch:
    """Tests for KomfoventSwitch entity."""

    def test_initialization(self, mock_coordinator):
        """Test switch entity initialization."""
        description = SwitchEntityDescription(key="test_switch", name="Test Switch")
        switch = KomfoventSwitch(mock_coordinator, 100, description)

        assert switch.register_id == 100
        assert switch.entity_description.key == "test_switch"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = SwitchEntityDescription(key="test_switch", name="Test")
        switch = KomfoventSwitch(mock_coordinator, 100, description)

        assert switch.unique_id == "test_entry_id_test_switch"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = SwitchEntityDescription(key="test_switch", name="Test")
        switch = KomfoventSwitch(mock_coordinator, 100, description)

        device_info = switch.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


# ==================== Is On Tests ====================


class TestIsOn:
    """Tests for is_on property."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({100: 1}, True),
            ({100: 0}, False),
            (None, None),
            ({}, None),
        ],
    )
    def test_is_on(self, mock_coordinator, data, expected):
        """Test is_on for various data states."""
        mock_coordinator.data = data
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(mock_coordinator, 100, description)

        assert switch.is_on is expected


# ==================== Turn On/Off Tests ====================


class TestTurnOnOff:
    """Tests for async_turn_on and async_turn_off methods."""

    @pytest.mark.parametrize(
        ("method", "expected_value"),
        [
            ("async_turn_on", 1),
            ("async_turn_off", 0),
        ],
    )
    async def test_turn(self, mock_coordinator, method, expected_value):
        """Test turn on/off writes correct value to register."""
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(mock_coordinator, 100, description)

        await getattr(switch, method)()

        mock_coordinator.client.write.assert_called_once_with(100, expected_value)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.parametrize(
        ("method", "expected_value"),
        [
            ("async_turn_on", 1),
            ("async_turn_off", 0),
        ],
    )
    async def test_turn_power_switch(self, mock_coordinator, method, expected_value):
        """Test turn on/off for power switch."""
        description = SwitchEntityDescription(key="power", name="Power")
        switch = KomfoventSwitch(mock_coordinator, registers.REG_POWER, description)

        await getattr(switch, method)()

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_POWER, expected_value
        )


# ==================== Factory Function Tests ====================


class TestCreateSwitches:
    """Tests for create_switches factory function."""

    async def test_creates_all_switches(self, mock_coordinator):
        """Test that all switch entities are created."""
        switches = await create_switches(mock_coordinator)

        assert len(switches) == 17
        switch_keys = {s.entity_description.key for s in switches}
        assert switch_keys == EXPECTED_SWITCH_KEYS
