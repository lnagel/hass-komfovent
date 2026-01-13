"""Tests for Komfovent climate platform."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.komfovent import registers
from custom_components.komfovent.climate import KomfoventClimate
from custom_components.komfovent.const import (
    DOMAIN,
    OperationMode,
    TemperatureControl,
)

# ==================== Data Tables ====================

# Temperature control mode test data: (mode, register, temp_value)
TEMP_CONTROL_MODES = [
    (TemperatureControl.SUPPLY, registers.REG_SUPPLY_TEMP, 215),
    (TemperatureControl.EXTRACT, registers.REG_EXTRACT_TEMP, 220),
    (TemperatureControl.ROOM, registers.REG_PANEL1_TEMP, 235),
    (TemperatureControl.BALANCE, registers.REG_EXTRACT_TEMP, 210),
]

# Target temperature by mode: (mode, register, expected_temp)
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

# All preset modes
ALL_PRESET_MODES = [
    (OperationMode.STANDBY, "standby"),
    (OperationMode.AWAY, "away"),
    (OperationMode.NORMAL, "normal"),
    (OperationMode.INTENSIVE, "intensive"),
    (OperationMode.BOOST, "boost"),
    (OperationMode.KITCHEN, "kitchen"),
    (OperationMode.FIREPLACE, "fireplace"),
    (OperationMode.OVERRIDE, "override"),
    (OperationMode.HOLIDAY, "holiday"),
    (OperationMode.AIR_QUALITY, "air_quality"),
    (OperationMode.OFF, "off"),
]


# ==================== Entity Tests ====================


class TestKomfoventClimate:
    """Tests for KomfoventClimate entity."""

    def test_initialization(self, mock_coordinator):
        """Test climate entity initialization."""
        climate = KomfoventClimate(mock_coordinator)

        assert climate.unique_id == "test_entry_id_climate"
        assert climate._attr_has_entity_name is True
        assert climate._attr_name is None

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        climate = KomfoventClimate(mock_coordinator)

        device_info = climate.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"

    def test_preset_modes(self, mock_coordinator):
        """Test preset_modes list."""
        climate = KomfoventClimate(mock_coordinator)

        expected_modes = [mode.name.lower() for mode in OperationMode]
        assert climate.preset_modes == expected_modes

    def test_hvac_modes(self, mock_coordinator):
        """Test hvac_modes list."""
        climate = KomfoventClimate(mock_coordinator)

        assert HVACMode.OFF in climate.hvac_modes
        assert HVACMode.HEAT_COOL in climate.hvac_modes


# ==================== Current Temperature ====================


class TestCurrentTemperature:
    """Tests for current_temperature property."""

    @pytest.mark.parametrize(("mode", "register", "temp_value"), TEMP_CONTROL_MODES)
    def test_temp_control_modes(self, mock_coordinator, mode, register, temp_value):
        """Test current temp with various temperature control modes."""
        mock_coordinator.data = {
            registers.REG_TEMP_CONTROL: mode,
            register: temp_value,
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature == temp_value / 10

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, None),
            ({registers.REG_TEMP_CONTROL: 99}, None),
        ],
    )
    def test_edge_cases(self, mock_coordinator, data, expected):
        """Test current_temperature edge cases."""
        mock_coordinator.data = data
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature == expected


# ==================== Target Temperature ====================


class TestTargetTemperature:
    """Tests for target_temperature property."""

    @pytest.mark.parametrize(("mode", "register", "expected_temp"), TARGET_TEMP_MODES)
    def test_target_temp_by_mode(self, mock_coordinator, mode, register, expected_temp):
        """Test target temperature for different operation modes."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: mode,
            register: int(expected_temp * 10),
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.target_temperature == expected_temp

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, None),
            ({registers.REG_OPERATION_MODE: 99}, None),
        ],
    )
    def test_edge_cases(self, mock_coordinator, data, expected):
        """Test target_temperature edge cases."""
        mock_coordinator.data = data
        climate = KomfoventClimate(mock_coordinator)

        assert climate.target_temperature == expected


# ==================== HVAC Mode ====================


class TestHvacMode:
    """Tests for hvac_mode property."""

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({registers.REG_POWER: 1}, HVACMode.HEAT_COOL),
            ({registers.REG_POWER: 0}, HVACMode.OFF),
            (None, None),
            ({}, None),
        ],
    )
    def test_hvac_mode(self, mock_coordinator, data, expected):
        """Test hvac_mode for various power states."""
        mock_coordinator.data = data
        climate = KomfoventClimate(mock_coordinator)

        assert climate.hvac_mode == expected


# ==================== Preset Mode ====================


class TestPresetMode:
    """Tests for preset_mode property."""

    @pytest.mark.parametrize(("mode", "expected"), ALL_PRESET_MODES)
    def test_preset_mode_values(self, mock_coordinator, mode, expected):
        """Test preset_mode for all operation modes."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: mode}
        climate = KomfoventClimate(mock_coordinator)

        assert climate.preset_mode == expected

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, None),
            ({registers.REG_OPERATION_MODE: 99}, None),
        ],
    )
    def test_edge_cases(self, mock_coordinator, data, expected):
        """Test preset_mode edge cases."""
        mock_coordinator.data = data
        climate = KomfoventClimate(mock_coordinator)

        assert climate.preset_mode == expected


# ==================== Async Set Temperature ====================


class TestAsyncSetTemperature:
    """Tests for async_set_temperature method."""

    @pytest.mark.parametrize(
        ("mode", "temp", "expected_register", "expected_value"),
        [
            (OperationMode.NORMAL, 22.5, registers.REG_NORMAL_SETPOINT, 225),
            (OperationMode.AWAY, 18.0, registers.REG_AWAY_TEMP, 180),
        ],
    )
    async def test_set_temperature(
        self, mock_coordinator, mode, temp, expected_register, expected_value
    ):
        """Test setting temperature in various modes."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: mode}
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: temp})

        mock_coordinator.client.write.assert_called_once_with(
            expected_register, expected_value
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.parametrize(
        ("mode", "temp", "should_write"),
        [
            (OperationMode.NORMAL, None, False),  # No temp arg
            (OperationMode.NORMAL, 45.0, False),  # Above max
            (OperationMode.NORMAL, 3.0, False),  # Below min
            (OperationMode.NORMAL, 5.0, True),  # At min boundary
            (OperationMode.NORMAL, 40.0, True),  # At max boundary
        ],
    )
    async def test_boundary_conditions(
        self, mock_coordinator, mode, temp, should_write
    ):
        """Test temperature boundary conditions."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: mode}
        climate = KomfoventClimate(mock_coordinator)

        if temp is None:
            await climate.async_set_temperature()
        else:
            await climate.async_set_temperature(**{ATTR_TEMPERATURE: temp})

        if should_write:
            mock_coordinator.client.write.assert_called_once()
        else:
            mock_coordinator.client.write.assert_not_called()

    async def test_invalid_mode_fallback(self, mock_coordinator):
        """Test set_temperature falls back to normal setpoint on invalid mode."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: 99}
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 21.0})

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_NORMAL_SETPOINT, 210
        )

    async def test_connection_error(self, mock_coordinator):
        """Test set_temperature handles connection errors."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: OperationMode.NORMAL}
        mock_coordinator.client.write = AsyncMock(side_effect=ConnectionError())
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 21.0})


# ==================== Async Set HVAC Mode ====================


class TestAsyncSetHvacMode:
    """Tests for async_set_hvac_mode method."""

    @pytest.mark.parametrize(
        ("hvac_mode", "expected_value"),
        [
            (HVACMode.OFF, 0),
            (HVACMode.HEAT_COOL, 1),
        ],
    )
    async def test_set_hvac_mode(self, mock_coordinator, hvac_mode, expected_value):
        """Test setting HVAC mode."""
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_hvac_mode(hvac_mode)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_POWER, expected_value
        )
        mock_coordinator.async_request_refresh.assert_called_once()


# ==================== Async Set Preset Mode ====================


class TestAsyncSetPresetMode:
    """Tests for async_set_preset_mode method."""

    @pytest.mark.parametrize("mode", ["away", "intensive"])
    async def test_set_preset_mode(self, mock_coordinator, mode):
        """Test setting preset mode calls services.set_operation_mode."""
        climate = KomfoventClimate(mock_coordinator)

        with patch(
            "custom_components.komfovent.climate.services.set_operation_mode",
            new_callable=AsyncMock,
        ) as mock_set_mode:
            await climate.async_set_preset_mode(mode)

            mock_set_mode.assert_called_once_with(mock_coordinator, mode)
