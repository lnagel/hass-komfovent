"""Tests for Komfovent services."""

from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture(autouse=True)
def fast_sleep():
    """Patch asyncio.sleep to avoid 1-second delays in set_operation_mode."""
    with patch("custom_components.komfovent.services.asyncio.sleep", new=AsyncMock()):
        yield


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

# ==================== Tests ====================


async def test_clean_filters_calibration(mock_coordinator):
    """Test clean_filters_calibration writes to register."""
    await clean_filters_calibration(mock_coordinator)
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_CLEAN_FILTERS, 1
    )


async def test_set_operation_mode_off(mock_coordinator):
    """Test OFF mode sets power to 0."""
    await set_operation_mode(mock_coordinator, "off")
    mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 0)


async def test_set_operation_mode_air_quality(mock_coordinator):
    """Test AIR_QUALITY mode enables auto mode."""
    await set_operation_mode(mock_coordinator, "air_quality")
    mock_coordinator.client.write.assert_called_once_with(registers.REG_AUTO_MODE, 1)


@pytest.mark.parametrize(("mode_name", "mode_enum"), STANDARD_MODES)
async def test_standard_modes(mock_coordinator, mode_name, mode_enum):
    """Test standard modes write to operation mode register."""
    await set_operation_mode(mock_coordinator, mode_name)
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_OPERATION_MODE, mode_enum.value
    )


@pytest.mark.parametrize(("mode", "timer_reg"), TIMER_MODES)
async def test_timer_modes_with_minutes(mock_coordinator, mode, timer_reg):
    """Test timer modes write provided minutes."""
    await set_operation_mode(mock_coordinator, mode, minutes=30)
    mock_coordinator.client.write.assert_called_once_with(timer_reg, 30)


@pytest.mark.parametrize(("mode", "timer_reg"), TIMER_MODES)
async def test_timer_modes_use_existing(mock_coordinator, mode, timer_reg):
    """Test timer modes use existing timer value."""
    mock_coordinator.data = {timer_reg: 45}
    await set_operation_mode(mock_coordinator, mode)
    mock_coordinator.client.write.assert_called_once_with(timer_reg, 45)


@pytest.mark.parametrize(("mode", "timer_reg"), TIMER_MODES)
async def test_timer_modes_use_default(mock_coordinator, mode, timer_reg):
    """Test timer modes use default when no value available."""
    mock_coordinator.data = {}
    await set_operation_mode(mock_coordinator, mode)
    mock_coordinator.client.write.assert_called_once_with(timer_reg, DEFAULT_MODE_TIMER)


async def test_case_insensitive_mode(mock_coordinator):
    """Test mode names are case insensitive."""
    await set_operation_mode(mock_coordinator, "AWAY")
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_OPERATION_MODE, OperationMode.AWAY.value
    )


@pytest.mark.parametrize("mode", ["standby", "holiday"])
async def test_unsupported_mode_logs_warning(mock_coordinator, mode):
    """Test unsupported modes log warning."""
    with patch("custom_components.komfovent.services._LOGGER") as mock_logger:
        await set_operation_mode(mock_coordinator, mode)
        mock_logger.warning.assert_called_once()


async def test_set_system_time(mock_coordinator):
    """Test set_system_time writes epoch time."""
    mock_coordinator.hass.config.time_zone = "UTC"
    await set_system_time(mock_coordinator)
    call_args = mock_coordinator.client.write.call_args[0]
    assert call_args[0] == registers.REG_EPOCH_TIME
    assert isinstance(call_args[1], int)
    assert call_args[1] > 0


@pytest.mark.parametrize(("setup", "expected"), [(True, True), (False, False)])
def test_get_coordinator_for_device(hass, setup, expected):
    """Test get_coordinator_for_device returns correct result."""
    mock_coordinator = MagicMock()
    hass.data[DOMAIN] = {"test_entry_id": mock_coordinator} if setup else {}
    mock_device = MagicMock() if setup else None
    if mock_device:
        mock_device.config_entries = ["test_entry_id"]
    with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
        mock_registry = MagicMock()
        mock_registry.async_get.return_value = mock_device
        mock_get.return_value = mock_registry
        result = get_coordinator_for_device(hass, "device_123")
        assert (result is mock_coordinator) if expected else (result is None)


def test_device_without_coordinator(hass):
    """Test returns None when device has no matching coordinator."""
    hass.data[DOMAIN] = {}
    mock_device = MagicMock()
    mock_device.config_entries = ["nonexistent_entry"]
    with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
        mock_registry = MagicMock()
        mock_registry.async_get.return_value = mock_device
        mock_get.return_value = mock_registry
        assert get_coordinator_for_device(hass, "device_123") is None


async def test_registers_all_services(hass):
    """Test that all services are registered."""
    hass.data[DOMAIN] = {}
    await async_register_services(hass)
    assert hass.services.async_register.call_count == 3
    services = [call[0][1] for call in hass.services.async_register.call_args_list]
    assert set(services) == {
        "clean_filters_calibration",
        "set_operation_mode",
        "set_system_time",
    }
