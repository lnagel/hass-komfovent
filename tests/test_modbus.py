"""Tests for Komfovent modbus client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymodbus import ModbusException

from custom_components.komfovent.modbus import KomfoventModbusClient


class TestKomfoventModbusClientInit:
    """Tests for KomfoventModbusClient initialization."""

    def test_init_creates_client(self):
        """Test client initialization creates AsyncModbusTcpClient."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            client = KomfoventModbusClient("192.168.1.100", 502)

            mock_client_class.assert_called_once_with(
                host="192.168.1.100",
                port=502,
                timeout=5,
                retries=3,
                reconnect_delay=5,
                reconnect_delay_max=60,
            )
            assert client._lock is not None


class TestModbusReadErrors:
    """Tests for read error handling."""

    async def test_read_32bit_missing_second_register(self):
        """Test read raises ValueError when 32-bit register pair is incomplete."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            # Only return one value but register 1000 is 32-bit unsigned
            mock_response.registers = [1234]
            mock_pymodbus.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            # Register 1000 (firmware version) is 32-bit unsigned
            with (
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_32BIT_UNSIGNED",
                    {1000},
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_SIGNED",
                    set(),
                ),
                pytest.raises(ValueError, match="value not retrieved"),
            ):
                await client.read(1000, 1)

    async def test_read_unknown_register_type(self):
        """Test read raises NotImplementedError for unknown register type."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            mock_response.registers = [1234]
            mock_pymodbus.read_holding_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            # Make register 500 not in any known set
            with (
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_32BIT_UNSIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_SIGNED",
                    set(),
                ),
                pytest.raises(NotImplementedError, match="not found"),
            ):
                await client.read(500, 1)


class TestModbusWrite:
    """Tests for write operations."""

    async def test_write_16bit_unsigned(self):
        """Test write to 16-bit unsigned register."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            mock_pymodbus.write_register = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            with patch(
                "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                {100},
            ):
                await client.write(100, 42)

            mock_pymodbus.write_register.assert_called_once_with(99, 42)

    async def test_write_16bit_signed(self):
        """Test write to 16-bit signed register converts negative values."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            mock_pymodbus.write_register = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            with (
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_SIGNED",
                    {100},
                ),
            ):
                # -10 as unsigned 16-bit is 65526
                await client.write(100, -10)

            mock_pymodbus.write_register.assert_called_once_with(99, 65526)

    async def test_write_32bit_unsigned(self):
        """Test write to 32-bit unsigned register splits into two words."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_response = MagicMock()
            mock_response.isError.return_value = False
            mock_pymodbus.write_registers = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            with (
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_SIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_32BIT_UNSIGNED",
                    {100},
                ),
            ):
                # 0x12345678 should be split into 0x1234 and 0x5678
                await client.write(100, 0x12345678)

            mock_pymodbus.write_registers.assert_called_once_with(
                address=99, values=[0x1234, 0x5678]
            )

    async def test_write_unknown_register_type(self):
        """Test write raises NotImplementedError for unknown register type."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            with (
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_SIGNED",
                    set(),
                ),
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_32BIT_UNSIGNED",
                    set(),
                ),
                pytest.raises(NotImplementedError, match="not found"),
            ):
                await client.write(500, 42)

    async def test_write_error_response(self):
        """Test write raises ModbusException on error response."""
        with patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient"
        ) as mock_client_class:
            mock_pymodbus = MagicMock()
            mock_response = MagicMock()
            mock_response.isError.return_value = True
            mock_pymodbus.write_register = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_pymodbus

            client = KomfoventModbusClient("192.168.1.100", 502)

            with (
                patch(
                    "custom_components.komfovent.modbus.REGISTERS_16BIT_UNSIGNED",
                    {100},
                ),
                pytest.raises(ModbusException, match="Error writing register"),
            ):
                await client.write(100, 42)
