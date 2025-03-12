"""Configure pytest for Home Assistant test suite."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
def hass():
    """Create a Home Assistant instance for testing."""
    hass_obj = MagicMock(spec=HomeAssistant)
    hass_obj.data = {}
    hass_obj.states = MagicMock()
    hass_obj.config_entries = MagicMock()
    hass_obj.bus = MagicMock()
    hass_obj.bus.async_fire = AsyncMock()
    hass_obj.async_block_till_done = AsyncMock()
    return hass_obj


@pytest.fixture
def register_data():
    """Load register data from JSON file."""
    json_file = Path("documentation/C6_holding_registers.json")

    with json_file.open() as f:
        data = json.load(f)

    # Transform data to match expected format (address+1 for Modbus offset)
    transformed_data = {}
    for block_start, values in data.items():
        block_start_int = int(block_start)
        for i, value in enumerate(values):
            transformed_data[block_start_int + i + 1] = value

    return transformed_data


@pytest.fixture
def mock_pymodbus_client():
    """Create a mock for the AsyncModbusTcpClient."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    # Create mock methods needed by the modbus implementation
    mock_client.read_holding_registers = AsyncMock()
    mock_client.read_holding_registers.return_value = MagicMock(registers=[0] * 10)

    mock_client.write_register = AsyncMock()

    return mock_client


@pytest.fixture
def mock_modbus_client(register_data, mock_pymodbus_client):
    """Create a mock KomfoventModbusClient."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    # Set up read_holding_registers to return data from our fixture
    async def mock_read_registers(address, count):
        result = {}
        for reg in range(address, address + count):
            if reg in register_data:
                result[reg] = register_data[reg]
            else:
                result[reg] = 0
        return result

    mock_client.read_holding_registers = AsyncMock(side_effect=mock_read_registers)
    mock_client.write_register = AsyncMock()

    return mock_client
