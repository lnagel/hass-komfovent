"""Tests for Komfovent modbus client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymodbus import ModbusException

from custom_components.komfovent.modbus import KomfoventModbusClient

# Patch paths
MODBUS_CLIENT = "custom_components.komfovent.modbus.AsyncModbusTcpClient"
REG_32U = "custom_components.komfovent.modbus.REGISTERS_32BIT_UNSIGNED"
REG_16U = "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED"
REG_16S = "custom_components.komfovent.modbus.REGISTERS_16BIT_SIGNED"


@pytest.fixture
def mock_pymodbus():
    """Create a mock pymodbus client."""
    with patch(MODBUS_CLIENT) as mock_class:
        mock = MagicMock()
        mock_class.return_value = mock
        yield mock


# ==================== Init Tests ====================


def test_init_creates_client():
    """Test client initialization creates AsyncModbusTcpClient."""
    with patch(MODBUS_CLIENT) as mock_class:
        client = KomfoventModbusClient("192.168.1.100", 502)
        mock_class.assert_called_once()
        assert client._lock is not None


# ==================== Read Tests ====================


async def test_read_32bit_missing_second_register(mock_pymodbus):
    """Test read raises ValueError when 32-bit register pair is incomplete."""
    mock_pymodbus.read_holding_registers = AsyncMock(
        return_value=MagicMock(isError=lambda: False, registers=[1234])
    )
    with (
        patch(REG_32U, {1000}),
        patch(REG_16U, set()),
        patch(REG_16S, set()),
        pytest.raises(ValueError, match="value not retrieved"),
    ):
        await KomfoventModbusClient("192.168.1.100", 502).read(1000, 1)


async def test_read_unknown_register_type(mock_pymodbus):
    """Test read raises NotImplementedError for unknown register type."""
    mock_pymodbus.read_holding_registers = AsyncMock(
        return_value=MagicMock(isError=lambda: False, registers=[1234])
    )
    with (
        patch(REG_32U, set()),
        patch(REG_16U, set()),
        patch(REG_16S, set()),
        pytest.raises(NotImplementedError, match="not found"),
    ):
        await KomfoventModbusClient("192.168.1.100", 502).read(500, 1)


# ==================== Write Tests ====================


@pytest.mark.parametrize(
    ("register_set", "register", "value", "method", "expected_args"),
    [
        (REG_16U, 100, 42, "write_register", (99, 42)),
        (REG_16S, 100, -10, "write_register", (99, 65526)),
    ],
)
async def test_write_16bit(
    mock_pymodbus, register_set, register, value, method, expected_args
):
    """Test write to 16-bit registers."""
    mock_pymodbus.write_register = AsyncMock(
        return_value=MagicMock(isError=lambda: False)
    )
    patches = [(REG_16U, set()), (REG_16S, set()), (REG_32U, set())]
    patches = [(p, {register} if p == register_set else s) for p, s in patches]
    with (
        patch(patches[0][0], patches[0][1]),
        patch(patches[1][0], patches[1][1]),
        patch(patches[2][0], patches[2][1]),
    ):
        await KomfoventModbusClient("192.168.1.100", 502).write(register, value)
    getattr(mock_pymodbus, method).assert_called_once_with(*expected_args)


async def test_write_32bit_unsigned(mock_pymodbus):
    """Test write to 32-bit unsigned register splits into two words."""
    mock_pymodbus.write_registers = AsyncMock(
        return_value=MagicMock(isError=lambda: False)
    )
    with patch(REG_16U, set()), patch(REG_16S, set()), patch(REG_32U, {100}):
        await KomfoventModbusClient("192.168.1.100", 502).write(100, 0x12345678)
    mock_pymodbus.write_registers.assert_called_once_with(
        address=99, values=[0x1234, 0x5678]
    )


async def test_write_unknown_register_type(mock_pymodbus):
    """Test write raises NotImplementedError for unknown register type."""
    with (
        patch(REG_16U, set()),
        patch(REG_16S, set()),
        patch(REG_32U, set()),
        pytest.raises(NotImplementedError, match="not found"),
    ):
        await KomfoventModbusClient("192.168.1.100", 502).write(500, 42)


async def test_write_error_response(mock_pymodbus):
    """Test write raises ModbusException on error response."""
    mock_pymodbus.write_register = AsyncMock(
        return_value=MagicMock(isError=lambda: True)
    )
    with (
        patch(REG_16U, {100}),
        pytest.raises(ModbusException, match="Error writing register"),
    ):
        await KomfoventModbusClient("192.168.1.100", 502).write(100, 42)
