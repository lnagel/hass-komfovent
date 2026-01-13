"""Tests for Komfovent switch platform."""

import pytest
from homeassistant.components.switch import SwitchEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.switch import KomfoventSwitch, create_switches

DESC = SwitchEntityDescription(key="test_switch", name="Test")

# ==================== Data Tables ====================

IS_ON_CASES = [({100: 1}, True), ({100: 0}, False), (None, None), ({}, None)]

TURN_CASES = [("async_turn_on", 1), ("async_turn_off", 0)]

EXPECTED_KEYS = {
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

# ==================== Entity Tests ====================


def test_entity_properties(mock_coordinator):
    """Test switch entity initialization and properties."""
    s = KomfoventSwitch(mock_coordinator, 100, DESC)
    assert s.register_id == 100
    assert s.unique_id == "test_entry_id_test_switch"
    assert s.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}


@pytest.mark.parametrize(("data", "expected"), IS_ON_CASES)
def test_is_on(mock_coordinator, data, expected):
    """Test is_on for various data states."""
    mock_coordinator.data = data
    assert KomfoventSwitch(mock_coordinator, 100, DESC).is_on is expected


@pytest.mark.parametrize(("method", "expected_value"), TURN_CASES)
async def test_turn_on_off(mock_coordinator, method, expected_value):
    """Test turn on/off writes correct value."""
    await getattr(KomfoventSwitch(mock_coordinator, 100, DESC), method)()
    mock_coordinator.client.write.assert_called_once_with(100, expected_value)
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.parametrize(("method", "expected_value"), TURN_CASES)
async def test_power_switch(mock_coordinator, method, expected_value):
    """Test power switch turn on/off."""
    desc = SwitchEntityDescription(key="power", name="Power")
    await getattr(
        KomfoventSwitch(mock_coordinator, registers.REG_POWER, desc), method
    )()
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_POWER, expected_value
    )


# ==================== Factory Tests ====================


async def test_create_switches(mock_coordinator):
    """Test all 17 switch entities are created."""
    switches = await create_switches(mock_coordinator)
    assert len(switches) == 17
    assert {s.entity_description.key for s in switches} == EXPECTED_KEYS
