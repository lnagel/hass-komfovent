"""Tests for Komfovent climate platform."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.komfovent import registers
from custom_components.komfovent.climate import KomfoventClimate
from custom_components.komfovent.const import DOMAIN, OperationMode, TemperatureControl

# ==================== Data Tables ====================

TEMP_CONTROL_MODES = [
    (TemperatureControl.SUPPLY, registers.REG_SUPPLY_TEMP, 215),
    (TemperatureControl.EXTRACT, registers.REG_EXTRACT_TEMP, 220),
    (TemperatureControl.ROOM, registers.REG_PANEL1_TEMP, 235),
    (TemperatureControl.BALANCE, registers.REG_EXTRACT_TEMP, 210),
]

TARGET_TEMP_MODES = [
    (OperationMode.NORMAL, registers.REG_NORMAL_SETPOINT, 21.0),
    (OperationMode.AWAY, registers.REG_AWAY_TEMP, 18.0),
    (OperationMode.INTENSIVE, registers.REG_INTENSIVE_TEMP, 22.0),
    (OperationMode.BOOST, registers.REG_BOOST_TEMP, 23.0),
    (OperationMode.KITCHEN, registers.REG_KITCHEN_TEMP, 20.0),
    (OperationMode.FIREPLACE, registers.REG_FIREPLACE_TEMP, 19.0),
    (OperationMode.OVERRIDE, registers.REG_OVERRIDE_TEMP, 24.0),
    (OperationMode.HOLIDAY, registers.REG_HOLIDAYS_TEMP, 17.0),
    (OperationMode.AIR_QUALITY, registers.REG_AQ_TEMP_SETPOINT, 21.5),
]

ALL_PRESETS = [(m, m.name.lower()) for m in OperationMode]

# ==================== Entity Tests ====================


class TestKomfoventClimate:
    """Tests for KomfoventClimate entity."""

    def test_initialization(self, mock_coordinator):
        """Test climate entity initialization."""
        c = KomfoventClimate(mock_coordinator)
        assert c.unique_id == "test_entry_id_climate"
        assert c._attr_has_entity_name is True

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        assert KomfoventClimate(mock_coordinator).device_info["identifiers"] == {
            (DOMAIN, "test_entry_id")
        }

    def test_modes(self, mock_coordinator):
        """Test preset_modes and hvac_modes lists."""
        c = KomfoventClimate(mock_coordinator)
        assert c.preset_modes == [m.name.lower() for m in OperationMode]
        assert HVACMode.OFF in c.hvac_modes
        assert HVACMode.HEAT_COOL in c.hvac_modes


# ==================== Property Tests ====================


@pytest.mark.parametrize(("mode", "register", "temp_value"), TEMP_CONTROL_MODES)
def test_current_temperature(mock_coordinator, mode, register, temp_value):
    """Test current temp with various temperature control modes."""
    mock_coordinator.data = {registers.REG_TEMP_CONTROL: mode, register: temp_value}
    assert KomfoventClimate(mock_coordinator).current_temperature == temp_value / 10


@pytest.mark.parametrize(("mode", "register", "expected"), TARGET_TEMP_MODES)
def test_target_temperature(mock_coordinator, mode, register, expected):
    """Test target temperature for different operation modes."""
    mock_coordinator.data = {
        registers.REG_OPERATION_MODE: mode,
        register: int(expected * 10),
    }
    assert KomfoventClimate(mock_coordinator).target_temperature == expected


@pytest.mark.parametrize(("mode", "expected"), ALL_PRESETS)
def test_preset_mode(mock_coordinator, mode, expected):
    """Test preset_mode for all operation modes."""
    mock_coordinator.data = {registers.REG_OPERATION_MODE: mode}
    assert KomfoventClimate(mock_coordinator).preset_mode == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({registers.REG_POWER: 1}, HVACMode.HEAT_COOL),
        ({registers.REG_POWER: 0}, HVACMode.OFF),
        (None, None),
        ({}, None),
    ],
)
def test_hvac_mode(mock_coordinator, data, expected):
    """Test hvac_mode for various power states."""
    mock_coordinator.data = data
    assert KomfoventClimate(mock_coordinator).hvac_mode == expected


@pytest.mark.parametrize(
    ("data", "attr"),
    [
        (None, "current_temperature"),
        ({registers.REG_TEMP_CONTROL: 99}, "current_temperature"),
        (None, "target_temperature"),
        ({registers.REG_OPERATION_MODE: 99}, "target_temperature"),
        (None, "preset_mode"),
        ({registers.REG_OPERATION_MODE: 99}, "preset_mode"),
    ],
)
def test_property_edge_cases(mock_coordinator, data, attr):
    """Test property edge cases return None."""
    mock_coordinator.data = data
    assert getattr(KomfoventClimate(mock_coordinator), attr) is None


# ==================== Async Methods ====================


@pytest.mark.parametrize(
    ("mode", "temp", "expected_reg", "expected_val"),
    [
        (OperationMode.NORMAL, 22.5, registers.REG_NORMAL_SETPOINT, 225),
        (OperationMode.AWAY, 18.0, registers.REG_AWAY_TEMP, 180),
    ],
)
async def test_set_temperature(
    mock_coordinator, mode, temp, expected_reg, expected_val
):
    """Test setting temperature in various modes."""
    mock_coordinator.data = {registers.REG_OPERATION_MODE: mode}
    await KomfoventClimate(mock_coordinator).async_set_temperature(
        **{ATTR_TEMPERATURE: temp}
    )
    mock_coordinator.client.write.assert_called_once_with(expected_reg, expected_val)


@pytest.mark.parametrize(
    ("temp", "should_write"),
    [(None, False), (45.0, False), (3.0, False), (5.0, True), (40.0, True)],
)
async def test_set_temperature_boundaries(mock_coordinator, temp, should_write):
    """Test temperature boundary conditions."""
    mock_coordinator.data = {registers.REG_OPERATION_MODE: OperationMode.NORMAL}
    c = KomfoventClimate(mock_coordinator)
    if temp is None:
        await c.async_set_temperature()
    else:
        await c.async_set_temperature(**{ATTR_TEMPERATURE: temp})
    assert mock_coordinator.client.write.called == should_write


async def test_set_temperature_invalid_mode(mock_coordinator):
    """Test set_temperature falls back to normal setpoint on invalid mode."""
    mock_coordinator.data = {registers.REG_OPERATION_MODE: 99}
    await KomfoventClimate(mock_coordinator).async_set_temperature(
        **{ATTR_TEMPERATURE: 21.0}
    )
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_NORMAL_SETPOINT, 210
    )


async def test_set_temperature_connection_error(mock_coordinator):
    """Test set_temperature handles connection errors."""
    mock_coordinator.data = {registers.REG_OPERATION_MODE: OperationMode.NORMAL}
    mock_coordinator.client.write = AsyncMock(side_effect=ConnectionError())
    await KomfoventClimate(mock_coordinator).async_set_temperature(
        **{ATTR_TEMPERATURE: 21.0}
    )


@pytest.mark.parametrize(
    ("hvac_mode", "value"), [(HVACMode.OFF, 0), (HVACMode.HEAT_COOL, 1)]
)
async def test_set_hvac_mode(mock_coordinator, hvac_mode, value):
    """Test setting HVAC mode."""
    await KomfoventClimate(mock_coordinator).async_set_hvac_mode(hvac_mode)
    mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, value)


@pytest.mark.parametrize("mode", ["away", "intensive"])
async def test_set_preset_mode(mock_coordinator, mode):
    """Test setting preset mode calls services.set_operation_mode."""
    with patch(
        "custom_components.komfovent.climate.services.set_operation_mode",
        new_callable=AsyncMock,
    ) as mock_set:
        await KomfoventClimate(mock_coordinator).async_set_preset_mode(mode)
        mock_set.assert_called_once_with(mock_coordinator, mode)
