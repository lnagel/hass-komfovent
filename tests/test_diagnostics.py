"""Tests for Komfovent diagnostics."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pymodbus import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.diagnostics import (
    ERR_READ_FAILED,
    RANGES,
    _check_response,
    async_get_config_entry_diagnostics,
    dump_registers,
)

MODBUS_CLIENT = "custom_components.komfovent.diagnostics.AsyncModbusTcpClient"


@pytest.fixture
def mock_entry(hass):
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="test_entry_id",
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 502},
    )
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"test": "data"}
    # Create mock runtime data with coordinator attribute
    mock_runtime_data = MagicMock()
    mock_runtime_data.coordinator = mock_coordinator
    hass.data[DOMAIN] = {entry.entry_id: mock_runtime_data}
    return entry


# ==================== Helper Tests ====================


def test_check_response_valid():
    """Test valid response does not raise."""
    _check_response(MagicMock(isError=lambda: False))


def test_check_response_error():
    """Test error response raises ModbusException."""
    with pytest.raises(ModbusException, match=ERR_READ_FAILED):
        _check_response(MagicMock(isError=lambda: True))


def test_ranges_defined():
    """Test RANGES constant is properly defined."""
    assert len(RANGES) > 0
    assert all(isinstance(s, int) and isinstance(c, int) for s, c in RANGES)


# ==================== Dump Registers Tests ====================


async def test_dump_connection_failure():
    """Test connection failure raises ConnectionError."""
    with patch(MODBUS_CLIENT) as mock_class:
        mock_class.return_value.connect = AsyncMock(return_value=False)
        with pytest.raises(ConnectionError, match="Failed to connect"):
            await dump_registers("192.168.1.100", 502)


async def test_dump_successful_block_read():
    """Test successful block read returns registers."""
    with patch(MODBUS_CLIENT) as mock_class:
        mock = MagicMock()
        mock.connect = AsyncMock(return_value=True)
        mock.close = MagicMock()
        mock.read_holding_registers = AsyncMock(
            return_value=MagicMock(isError=lambda: False, registers=[1, 2, 3])
        )
        mock_class.return_value = mock
        result = await dump_registers("192.168.1.100", 502)
        assert len(result) > 0
        mock.close.assert_called_once()


async def test_dump_block_fallback_to_individual():
    """Test block read failure falls back to individual reads."""
    with patch(MODBUS_CLIENT) as mock_class:
        mock = MagicMock()
        mock.connect = AsyncMock(return_value=True)
        mock.close = MagicMock()
        call_count = [0]

        def make_response(*args, **kwargs):
            call_count[0] += 1
            resp = MagicMock()
            resp.isError = lambda: call_count[0] % 2 == 1
            resp.registers = [42]
            return resp

        mock.read_holding_registers = AsyncMock(side_effect=make_response)
        mock_class.return_value = mock
        result = await dump_registers("192.168.1.100", 502)
        assert len(result) > 0


async def test_dump_all_reads_fail():
    """Test when all reads fail returns empty dict."""
    with patch(MODBUS_CLIENT) as mock_class:
        mock = MagicMock()
        mock.connect = AsyncMock(return_value=True)
        mock.close = MagicMock()
        mock.read_holding_registers = AsyncMock(
            return_value=MagicMock(isError=lambda: True)
        )
        mock_class.return_value = mock
        assert await dump_registers("192.168.1.100", 502) == {}


async def test_dump_client_closed_on_exception():
    """Test client is closed even when exception occurs."""
    with patch(MODBUS_CLIENT) as mock_class:
        mock = MagicMock()
        mock.connect = AsyncMock(return_value=True)
        mock.close = MagicMock()
        mock.read_holding_registers = AsyncMock(side_effect=RuntimeError("Unexpected"))
        mock_class.return_value = mock
        with pytest.raises(RuntimeError):
            await dump_registers("192.168.1.100", 502)
        mock.close.assert_called_once()


# ==================== Diagnostics Entry Tests ====================


@pytest.mark.parametrize(
    ("side_effect", "expected_registers"),
    [
        (None, {1: [1, 2, 3]}),
        (ConnectionError("Failed to connect"), {}),
        (ModbusException("Read failed"), {}),
    ],
)
async def test_diagnostics_entry(hass, mock_entry, side_effect, expected_registers):
    """Test async_get_config_entry_diagnostics."""
    mock_dump = AsyncMock()
    if side_effect is None:
        mock_dump.return_value = {1: [1, 2, 3]}
    else:
        mock_dump.side_effect = side_effect
    with patch(
        "custom_components.komfovent.diagnostics.dump_registers",
        mock_dump,
    ):
        result = await async_get_config_entry_diagnostics(hass, mock_entry)
    assert "config_entry" in result
    assert result["registers"] == expected_registers
    assert result["coordinator_data"] == {"test": "data"}
