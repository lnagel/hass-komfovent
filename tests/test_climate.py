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


class TestCurrentTemperature:
    """Tests for current_temperature property."""

    def test_supply_temp_control(self, mock_coordinator):
        """Test current temp with supply temperature control."""
        mock_coordinator.data = {
            registers.REG_TEMP_CONTROL: TemperatureControl.SUPPLY,
            registers.REG_SUPPLY_TEMP: 215,  # 21.5°C
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature == 21.5

    def test_extract_temp_control(self, mock_coordinator):
        """Test current temp with extract temperature control."""
        mock_coordinator.data = {
            registers.REG_TEMP_CONTROL: TemperatureControl.EXTRACT,
            registers.REG_EXTRACT_TEMP: 220,  # 22.0°C
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature == 22.0

    def test_room_temp_control(self, mock_coordinator):
        """Test current temp with room temperature control (panel 1)."""
        mock_coordinator.data = {
            registers.REG_TEMP_CONTROL: TemperatureControl.ROOM,
            registers.REG_PANEL1_TEMP: 235,  # 23.5°C
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature == 23.5

    def test_balance_temp_control(self, mock_coordinator):
        """Test current temp with balance temperature control."""
        mock_coordinator.data = {
            registers.REG_TEMP_CONTROL: TemperatureControl.BALANCE,
            registers.REG_EXTRACT_TEMP: 210,  # 21.0°C
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature == 21.0

    def test_no_data(self, mock_coordinator):
        """Test current_temperature with no data."""
        mock_coordinator.data = None
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature is None

    def test_invalid_temp_control_mode(self, mock_coordinator):
        """Test current_temperature with invalid temp control mode."""
        mock_coordinator.data = {
            registers.REG_TEMP_CONTROL: 99,  # Invalid mode
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.current_temperature is None


class TestTargetTemperature:
    """Tests for target_temperature property."""

    @pytest.mark.parametrize(
        ("mode", "register", "expected_temp"),
        [
            (OperationMode.NORMAL, registers.REG_NORMAL_SETPOINT, 21.0),
            (OperationMode.AWAY, registers.REG_AWAY_TEMP, 18.0),
            (OperationMode.INTENSIVE, registers.REG_INTENSIVE_TEMP, 22.0),
            (OperationMode.BOOST, registers.REG_BOOST_TEMP, 23.0),
            (OperationMode.KITCHEN, registers.REG_KITCHEN_TEMP, 20.0),
            (OperationMode.FIREPLACE, registers.REG_FIREPLACE_TEMP, 19.0),
            (OperationMode.OVERRIDE, registers.REG_OVERRIDE_TEMP, 24.0),
            (OperationMode.HOLIDAY, registers.REG_HOLIDAYS_TEMP, 17.0),
            (OperationMode.AIR_QUALITY, registers.REG_AQ_TEMP_SETPOINT, 21.5),
        ],
    )
    def test_target_temp_by_mode(self, mock_coordinator, mode, register, expected_temp):
        """Test target temperature for different operation modes."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: mode,
            register: int(expected_temp * 10),
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.target_temperature == expected_temp

    def test_no_data(self, mock_coordinator):
        """Test target_temperature with no data."""
        mock_coordinator.data = None
        climate = KomfoventClimate(mock_coordinator)

        assert climate.target_temperature is None

    def test_invalid_operation_mode(self, mock_coordinator):
        """Test target_temperature with invalid operation mode."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: 99,  # Invalid mode
        }
        climate = KomfoventClimate(mock_coordinator)

        assert climate.target_temperature is None


class TestHvacMode:
    """Tests for hvac_mode property."""

    def test_power_on(self, mock_coordinator):
        """Test hvac_mode when power is on."""
        mock_coordinator.data = {registers.REG_POWER: 1}
        climate = KomfoventClimate(mock_coordinator)

        assert climate.hvac_mode == HVACMode.HEAT_COOL

    def test_power_off(self, mock_coordinator):
        """Test hvac_mode when power is off."""
        mock_coordinator.data = {registers.REG_POWER: 0}
        climate = KomfoventClimate(mock_coordinator)

        assert climate.hvac_mode == HVACMode.OFF

    def test_no_data(self, mock_coordinator):
        """Test hvac_mode with no data."""
        mock_coordinator.data = None
        climate = KomfoventClimate(mock_coordinator)

        assert climate.hvac_mode is None

    def test_power_none(self, mock_coordinator):
        """Test hvac_mode when power register is None."""
        mock_coordinator.data = {}
        climate = KomfoventClimate(mock_coordinator)

        assert climate.hvac_mode is None


class TestPresetMode:
    """Tests for preset_mode property."""

    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
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
        ],
    )
    def test_preset_mode_values(self, mock_coordinator, mode, expected):
        """Test preset_mode for all operation modes."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: mode}
        climate = KomfoventClimate(mock_coordinator)

        assert climate.preset_mode == expected

    def test_no_data(self, mock_coordinator):
        """Test preset_mode with no data."""
        mock_coordinator.data = None
        climate = KomfoventClimate(mock_coordinator)

        assert climate.preset_mode is None

    def test_invalid_mode(self, mock_coordinator):
        """Test preset_mode with invalid operation mode."""
        mock_coordinator.data = {registers.REG_OPERATION_MODE: 99}
        climate = KomfoventClimate(mock_coordinator)

        assert climate.preset_mode is None


class TestAsyncSetTemperature:
    """Tests for async_set_temperature method."""

    async def test_set_temperature_normal_mode(self, mock_coordinator):
        """Test setting temperature in normal mode."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 22.5})

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_NORMAL_SETPOINT, 225
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_temperature_away_mode(self, mock_coordinator):
        """Test setting temperature in away mode."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.AWAY,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 18.0})

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_AWAY_TEMP, 180
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_temperature_no_temp_arg(self, mock_coordinator):
        """Test set_temperature with no temperature argument."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature()

        mock_coordinator.client.write.assert_not_called()

    async def test_set_temperature_out_of_bounds_high(self, mock_coordinator):
        """Test set_temperature with value above max (40°C)."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 45.0})

        mock_coordinator.client.write.assert_not_called()

    async def test_set_temperature_out_of_bounds_low(self, mock_coordinator):
        """Test set_temperature with value below min (5°C)."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 3.0})

        mock_coordinator.client.write.assert_not_called()

    async def test_set_temperature_min_boundary(self, mock_coordinator):
        """Test set_temperature at minimum boundary (5°C)."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 5.0})

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_NORMAL_SETPOINT, 50
        )

    async def test_set_temperature_max_boundary(self, mock_coordinator):
        """Test set_temperature at maximum boundary (40°C)."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 40.0})

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_NORMAL_SETPOINT, 400
        )

    async def test_set_temperature_invalid_mode_fallback(self, mock_coordinator):
        """Test set_temperature falls back to normal setpoint on invalid mode."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: 99,  # Invalid mode
        }
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 21.0})

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_NORMAL_SETPOINT, 210
        )

    async def test_set_temperature_connection_error(self, mock_coordinator):
        """Test set_temperature handles connection errors."""
        mock_coordinator.data = {
            registers.REG_OPERATION_MODE: OperationMode.NORMAL,
        }
        mock_coordinator.client.write = AsyncMock(side_effect=ConnectionError())
        climate = KomfoventClimate(mock_coordinator)

        # Should not raise, just log
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 21.0})


class TestAsyncSetHvacMode:
    """Tests for async_set_hvac_mode method."""

    async def test_set_hvac_mode_off(self, mock_coordinator):
        """Test setting HVAC mode to OFF."""
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_hvac_mode(HVACMode.OFF)

        mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 0)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_hvac_mode_heat_cool(self, mock_coordinator):
        """Test setting HVAC mode to HEAT_COOL."""
        climate = KomfoventClimate(mock_coordinator)

        await climate.async_set_hvac_mode(HVACMode.HEAT_COOL)

        mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 1)
        mock_coordinator.async_request_refresh.assert_called_once()


class TestAsyncSetPresetMode:
    """Tests for async_set_preset_mode method."""

    async def test_set_preset_mode(self, mock_coordinator):
        """Test setting preset mode calls services.set_operation_mode."""
        climate = KomfoventClimate(mock_coordinator)

        with patch(
            "custom_components.komfovent.climate.services.set_operation_mode",
            new_callable=AsyncMock,
        ) as mock_set_mode:
            await climate.async_set_preset_mode("away")

            mock_set_mode.assert_called_once_with(mock_coordinator, "away")

    async def test_set_preset_mode_intensive(self, mock_coordinator):
        """Test setting preset mode to intensive."""
        climate = KomfoventClimate(mock_coordinator)

        with patch(
            "custom_components.komfovent.climate.services.set_operation_mode",
            new_callable=AsyncMock,
        ) as mock_set_mode:
            await climate.async_set_preset_mode("intensive")

            mock_set_mode.assert_called_once_with(mock_coordinator, "intensive")
