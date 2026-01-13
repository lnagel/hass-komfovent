"""Tests for Komfovent services."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN, OperationMode
from custom_components.komfovent.services import (
    DEFAULT_MODE_TIMER,
    async_register_services,
    clean_filters_calibration,
    get_coordinator_for_device,
    set_operation_mode,
    set_system_time,
)


class TestCleanFiltersCalibration:
    """Tests for clean_filters_calibration function."""

    async def test_clean_filters_writes_register(self, mock_coordinator):
        """Test clean_filters_calibration writes to REG_CLEAN_FILTERS."""
        await clean_filters_calibration(mock_coordinator)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_CLEAN_FILTERS, 1
        )


class TestSetOperationMode:
    """Tests for set_operation_mode function."""

    async def test_off_mode_sets_power_off(self, mock_coordinator):
        """Test OFF mode sets power to 0."""
        await set_operation_mode(mock_coordinator, "off")

        mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 0)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_air_quality_mode_enables_auto(self, mock_coordinator):
        """Test AIR_QUALITY mode enables auto mode."""
        await set_operation_mode(mock_coordinator, "air_quality")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_AUTO_MODE, 1
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.parametrize(
        ("mode_name", "mode_enum"),
        [
            ("away", OperationMode.AWAY),
            ("normal", OperationMode.NORMAL),
            ("intensive", OperationMode.INTENSIVE),
            ("boost", OperationMode.BOOST),
        ],
    )
    async def test_standard_modes(self, mock_coordinator, mode_name, mode_enum):
        """Test standard modes write to operation mode register."""
        await set_operation_mode(mock_coordinator, mode_name)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_OPERATION_MODE, mode_enum.value
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_kitchen_mode_with_minutes(self, mock_coordinator):
        """Test KITCHEN mode writes to kitchen timer with provided minutes."""
        await set_operation_mode(mock_coordinator, "kitchen", minutes=30)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_KITCHEN_TIMER, 30
        )

    async def test_kitchen_mode_uses_existing_timer(self, mock_coordinator):
        """Test KITCHEN mode uses existing timer value from data."""
        mock_coordinator.data = {registers.REG_KITCHEN_TIMER: 45}

        await set_operation_mode(mock_coordinator, "kitchen")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_KITCHEN_TIMER, 45
        )

    async def test_kitchen_mode_uses_default(self, mock_coordinator):
        """Test KITCHEN mode uses default timer when no value available."""
        mock_coordinator.data = {}

        await set_operation_mode(mock_coordinator, "kitchen")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_KITCHEN_TIMER, DEFAULT_MODE_TIMER
        )

    async def test_fireplace_mode_with_minutes(self, mock_coordinator):
        """Test FIREPLACE mode writes to fireplace timer."""
        await set_operation_mode(mock_coordinator, "fireplace", minutes=20)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_FIREPLACE_TIMER, 20
        )

    async def test_fireplace_mode_uses_existing_timer(self, mock_coordinator):
        """Test FIREPLACE mode uses existing timer value from data."""
        mock_coordinator.data = {registers.REG_FIREPLACE_TIMER: 35}

        await set_operation_mode(mock_coordinator, "fireplace")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_FIREPLACE_TIMER, 35
        )

    async def test_override_mode_with_minutes(self, mock_coordinator):
        """Test OVERRIDE mode writes to override timer."""
        await set_operation_mode(mock_coordinator, "override", minutes=15)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_OVERRIDE_TIMER, 15
        )

    async def test_override_mode_uses_existing_timer(self, mock_coordinator):
        """Test OVERRIDE mode uses existing timer value from data."""
        mock_coordinator.data = {registers.REG_OVERRIDE_TIMER: 25}

        await set_operation_mode(mock_coordinator, "override")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_OVERRIDE_TIMER, 25
        )

    async def test_case_insensitive_mode(self, mock_coordinator):
        """Test mode names are case insensitive."""
        await set_operation_mode(mock_coordinator, "AWAY")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_OPERATION_MODE, OperationMode.AWAY.value
        )

    async def test_unsupported_mode_logs_warning(self, mock_coordinator):
        """Test unsupported mode (STANDBY) logs warning but still refreshes."""
        with patch("custom_components.komfovent.services._LOGGER") as mock_logger:
            await set_operation_mode(mock_coordinator, "standby")

            mock_logger.warning.assert_called_once()
            mock_coordinator.async_request_refresh.assert_called_once()

    async def test_holiday_mode_logs_warning(self, mock_coordinator):
        """Test HOLIDAY mode logs warning (unsupported)."""
        with patch("custom_components.komfovent.services._LOGGER") as mock_logger:
            await set_operation_mode(mock_coordinator, "holiday")

            mock_logger.warning.assert_called_once()


class TestSetSystemTime:
    """Tests for set_system_time function."""

    async def test_writes_epoch_time(self, mock_coordinator):
        """Test set_system_time writes to REG_EPOCH_TIME."""
        mock_coordinator.hass.config.time_zone = "UTC"

        await set_system_time(mock_coordinator)

        mock_coordinator.client.write.assert_called_once()
        call_args = mock_coordinator.client.write.call_args
        assert call_args[0][0] == registers.REG_EPOCH_TIME
        # Value should be a positive integer (seconds since epoch)
        assert isinstance(call_args[0][1], int)
        assert call_args[0][1] > 0


class TestGetCoordinatorForDevice:
    """Tests for get_coordinator_for_device function."""

    def test_returns_coordinator_for_valid_device(self, hass):
        """Test returns coordinator for a valid device ID."""
        mock_coordinator = MagicMock()
        hass.data[DOMAIN] = {"test_entry_id": mock_coordinator}

        mock_device = MagicMock()
        mock_device.config_entries = ["test_entry_id"]

        with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_get.return_value = mock_registry

            result = get_coordinator_for_device(hass, "device_123")

            assert result is mock_coordinator

    def test_returns_none_for_unknown_device(self, hass):
        """Test returns None for unknown device ID."""
        hass.data[DOMAIN] = {}

        with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = None
            mock_get.return_value = mock_registry

            result = get_coordinator_for_device(hass, "unknown_device")

            assert result is None

    def test_returns_none_for_device_without_coordinator(self, hass):
        """Test returns None when device has no matching coordinator."""
        hass.data[DOMAIN] = {}

        mock_device = MagicMock()
        mock_device.config_entries = ["nonexistent_entry"]

        with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_get.return_value = mock_registry

            result = get_coordinator_for_device(hass, "device_123")

            assert result is None


class TestAsyncRegisterServices:
    """Tests for async_register_services function."""

    async def test_registers_all_services(self, hass):
        """Test that all services are registered."""
        hass.data[DOMAIN] = {}

        await async_register_services(hass)

        # Verify services were registered by checking async_register was called
        assert hass.services.async_register.call_count == 3

        # Verify the service names
        registered_services = [
            call[0][1] for call in hass.services.async_register.call_args_list
        ]
        assert "clean_filters_calibration" in registered_services
        assert "set_operation_mode" in registered_services
        assert "set_system_time" in registered_services
