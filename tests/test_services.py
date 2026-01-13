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

# ==================== Data Tables ====================

STANDARD_MODES = [
    ("away", OperationMode.AWAY),
    ("normal", OperationMode.NORMAL),
    ("intensive", OperationMode.INTENSIVE),
    ("boost", OperationMode.BOOST),
]

TIMER_MODES = [
    ("kitchen", registers.REG_KITCHEN_TIMER),
    ("fireplace", registers.REG_FIREPLACE_TIMER),
    ("override", registers.REG_OVERRIDE_TIMER),
]


# ==================== Clean Filters Calibration ====================


class TestCleanFiltersCalibration:
    """Tests for clean_filters_calibration function."""

    async def test_writes_register(self, mock_coordinator):
        """Test clean_filters_calibration writes to REG_CLEAN_FILTERS."""
        await clean_filters_calibration(mock_coordinator)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_CLEAN_FILTERS, 1
        )


# ==================== Set Operation Mode ====================


class TestSetOperationMode:
    """Tests for set_operation_mode function."""

    async def test_off_mode(self, mock_coordinator):
        """Test OFF mode sets power to 0."""
        await set_operation_mode(mock_coordinator, "off")

        mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 0)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_air_quality_mode(self, mock_coordinator):
        """Test AIR_QUALITY mode enables auto mode."""
        await set_operation_mode(mock_coordinator, "air_quality")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_AUTO_MODE, 1
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.parametrize(("mode_name", "mode_enum"), STANDARD_MODES)
    async def test_standard_modes(self, mock_coordinator, mode_name, mode_enum):
        """Test standard modes write to operation mode register."""
        await set_operation_mode(mock_coordinator, mode_name)

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_OPERATION_MODE, mode_enum.value
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.parametrize(("mode", "timer_reg"), TIMER_MODES)
    async def test_timer_mode_with_minutes(self, mock_coordinator, mode, timer_reg):
        """Test timer modes write to timer register with provided minutes."""
        await set_operation_mode(mock_coordinator, mode, minutes=30)

        mock_coordinator.client.write.assert_called_once_with(timer_reg, 30)

    @pytest.mark.parametrize(("mode", "timer_reg"), TIMER_MODES)
    async def test_timer_mode_uses_existing(self, mock_coordinator, mode, timer_reg):
        """Test timer modes use existing timer value from data."""
        mock_coordinator.data = {timer_reg: 45}

        await set_operation_mode(mock_coordinator, mode)

        mock_coordinator.client.write.assert_called_once_with(timer_reg, 45)

    @pytest.mark.parametrize(("mode", "timer_reg"), TIMER_MODES)
    async def test_timer_mode_uses_default(self, mock_coordinator, mode, timer_reg):
        """Test timer modes use default timer when no value available."""
        mock_coordinator.data = {}

        await set_operation_mode(mock_coordinator, mode)

        mock_coordinator.client.write.assert_called_once_with(
            timer_reg, DEFAULT_MODE_TIMER
        )

    async def test_case_insensitive_mode(self, mock_coordinator):
        """Test mode names are case insensitive."""
        await set_operation_mode(mock_coordinator, "AWAY")

        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_OPERATION_MODE, OperationMode.AWAY.value
        )

    @pytest.mark.parametrize("mode", ["standby", "holiday"])
    async def test_unsupported_mode_logs_warning(self, mock_coordinator, mode):
        """Test unsupported modes log warning but still refresh."""
        with patch("custom_components.komfovent.services._LOGGER") as mock_logger:
            await set_operation_mode(mock_coordinator, mode)

            mock_logger.warning.assert_called_once()
            mock_coordinator.async_request_refresh.assert_called_once()


# ==================== Set System Time ====================


class TestSetSystemTime:
    """Tests for set_system_time function."""

    async def test_writes_epoch_time(self, mock_coordinator):
        """Test set_system_time writes to REG_EPOCH_TIME."""
        mock_coordinator.hass.config.time_zone = "UTC"

        await set_system_time(mock_coordinator)

        mock_coordinator.client.write.assert_called_once()
        call_args = mock_coordinator.client.write.call_args
        assert call_args[0][0] == registers.REG_EPOCH_TIME
        assert isinstance(call_args[0][1], int)
        assert call_args[0][1] > 0


# ==================== Get Coordinator For Device ====================


class TestGetCoordinatorForDevice:
    """Tests for get_coordinator_for_device function."""

    @pytest.mark.parametrize(
        ("setup_device", "expected_result"),
        [
            (True, True),  # Valid device returns coordinator
            (False, False),  # Unknown device returns None
        ],
    )
    def test_get_coordinator(self, hass, setup_device, expected_result):
        """Test get_coordinator_for_device returns correct result."""
        mock_coordinator = MagicMock()
        hass.data[DOMAIN] = {"test_entry_id": mock_coordinator} if setup_device else {}

        mock_device = MagicMock() if setup_device else None
        if mock_device:
            mock_device.config_entries = ["test_entry_id"]

        with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
            mock_registry = MagicMock()
            mock_registry.async_get.return_value = mock_device
            mock_get.return_value = mock_registry

            result = get_coordinator_for_device(hass, "device_123")

            if expected_result:
                assert result is mock_coordinator
            else:
                assert result is None

    def test_device_without_coordinator(self, hass):
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


# ==================== Service Registration ====================


class TestAsyncRegisterServices:
    """Tests for async_register_services function."""

    async def test_registers_all_services(self, hass):
        """Test that all services are registered."""
        hass.data[DOMAIN] = {}

        await async_register_services(hass)

        assert hass.services.async_register.call_count == 3
        registered_services = [
            call[0][1] for call in hass.services.async_register.call_args_list
        ]
        assert "clean_filters_calibration" in registered_services
        assert "set_operation_mode" in registered_services
        assert "set_system_time" in registered_services
