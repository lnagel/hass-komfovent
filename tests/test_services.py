"""Tests for Komfovent services."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, call, patch

import pytest
from homeassistant.config_entries import ConfigEntryState

from custom_components.komfovent import registers
from custom_components.komfovent.const import (
    ALARM_RESET_COMMAND,
    DOMAIN,
    Controller,
    OperationMode,
)
from custom_components.komfovent.coordinator import KomfoventRuntimeData
from custom_components.komfovent.services import (
    DEFAULT_MODE_TIMER,
    async_register_services,
    clean_filters_calibration,
    clear_active_alarms,
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

# ==================== Tests ====================


async def test_clear_active_alarms(mock_coordinator):
    """Test clear_active_alarms writes reset command to alarm count register."""
    await clear_active_alarms(mock_coordinator)
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_ACTIVE_ALARMS_COUNT, ALARM_RESET_COMMAND
    )
    mock_coordinator.set_cooldown.assert_called_once_with(1.0)
    mock_coordinator.async_request_refresh.assert_called_once()


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


async def test_set_system_time_legacy_c6_writes_29_30_31(mock_coordinator):
    """Legacy C6 firmware (func_version < 21) writes regs 29/30/31, not 33."""
    mock_coordinator.hass.config.time_zone = "UTC"
    mock_coordinator.controller = Controller.C6
    mock_coordinator.func_version = 20

    frozen = datetime(2026, 5, 18, 14, 35, 12, tzinfo=UTC)
    with patch("custom_components.komfovent.services.datetime") as mock_datetime:
        mock_datetime.now.return_value = frozen
        await set_system_time(mock_coordinator)

    assert mock_coordinator.client.write.call_args_list == [
        call(registers.REG_TIME, (14 << 8) | 35),
        call(registers.REG_YEAR, 2026),
        call(registers.REG_MONTH_DAY, (5 << 8) | 18),
    ]


@pytest.mark.parametrize(
    ("controller", "func_version"),
    [
        (Controller.C6, 21),  # boundary: first version where reg 33 is RW
        (Controller.C6, 67),  # typical modern C6
        (Controller.C6M, 20),  # C6M is unaffected by the C6-only fix
        (Controller.C6M, 71),  # typical modern C6M
        (Controller.C8, 20),  # C8 is unaffected even at low func_version
        (Controller.C8, 27),  # typical C8
    ],
)
async def test_set_system_time_writes_epoch(mock_coordinator, controller, func_version):
    """All non-legacy-C6 combinations write the 32-bit REG_EPOCH_TIME."""
    mock_coordinator.hass.config.time_zone = "UTC"
    mock_coordinator.controller = controller
    mock_coordinator.func_version = func_version

    await set_system_time(mock_coordinator)

    mock_coordinator.client.write.assert_called_once()
    reg, value = mock_coordinator.client.write.call_args[0]
    assert reg == registers.REG_EPOCH_TIME
    assert isinstance(value, int)
    assert value > 0


def _mock_loaded_entry(coordinator):
    """Build a mock LOADED komfovent config entry exposing the coordinator."""
    entry = MagicMock()
    entry.domain = DOMAIN
    entry.state = ConfigEntryState.LOADED
    entry.runtime_data = KomfoventRuntimeData(coordinator=coordinator)
    return entry


@pytest.mark.parametrize(("setup", "expected"), [(True, True), (False, False)])
def test_get_coordinator_for_device(hass, setup, expected):
    """Test get_coordinator_for_device returns correct result."""
    mock_coordinator = MagicMock()
    hass.config_entries.async_get_entry.return_value = (
        _mock_loaded_entry(mock_coordinator) if setup else None
    )
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
    hass.config_entries.async_get_entry.return_value = None
    mock_device = MagicMock()
    mock_device.config_entries = ["nonexistent_entry"]
    with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
        mock_registry = MagicMock()
        mock_registry.async_get.return_value = mock_device
        mock_get.return_value = mock_registry
        assert get_coordinator_for_device(hass, "device_123") is None


async def test_handle_clear_active_alarms(hass, mock_coordinator):
    """Test handle_clear_active_alarms service handler."""
    hass.config_entries.async_get_entry.return_value = _mock_loaded_entry(
        mock_coordinator
    )
    await async_register_services(hass)

    # Get the handler that was registered for clear_active_alarms
    calls = hass.services.async_register.call_args_list
    handler = next(c[0][2] for c in calls if c[0][1] == "clear_active_alarms")

    # Mock device registry lookup
    mock_call = MagicMock()
    mock_call.data = {"device_id": "device_123"}
    mock_device = MagicMock()
    mock_device.config_entries = ["test_entry_id"]
    with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
        mock_registry = MagicMock()
        mock_registry.async_get.return_value = mock_device
        mock_get.return_value = mock_registry
        await handler(mock_call)

    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_ACTIVE_ALARMS_COUNT, ALARM_RESET_COMMAND
    )


async def test_handle_clear_active_alarms_device_not_found(hass):
    """Test handle_clear_active_alarms when device not found."""
    await async_register_services(hass)

    calls = hass.services.async_register.call_args_list
    handler = next(c[0][2] for c in calls if c[0][1] == "clear_active_alarms")

    mock_call = MagicMock()
    mock_call.data = {"device_id": "nonexistent"}
    with patch("custom_components.komfovent.services.dr.async_get") as mock_get:
        mock_registry = MagicMock()
        mock_registry.async_get.return_value = None
        mock_get.return_value = mock_registry
        await handler(mock_call)


async def test_registers_all_services(hass):
    """Test that all services are registered."""
    await async_register_services(hass)
    assert hass.services.async_register.call_count == 4
    services = [call[0][1] for call in hass.services.async_register.call_args_list]
    assert set(services) == {
        "clear_active_alarms",
        "clean_filters_calibration",
        "set_operation_mode",
        "set_system_time",
    }
