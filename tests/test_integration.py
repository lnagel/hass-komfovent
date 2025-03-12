"""Tests for Komfovent integration initialization."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.komfovent import async_setup_entry
from custom_components.komfovent.const import DOMAIN


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
def mock_modbus_client(register_data):
    """Create a mock modbus client."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    # Set up read_holding_registers to return data from our fixture
    async def mock_read_registers(address, count):
        result = {}
        for reg in range(address, address + count):
            if reg in register_data:
                result[reg] = register_data[reg]
        return result

    mock_client.read_holding_registers = AsyncMock(side_effect=mock_read_registers)
    mock_client.write_register = AsyncMock()

    return mock_client


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {CONF_HOST: "localhost", CONF_PORT: 502}
    entry.entry_id = "test_entry_id"
    return entry


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_modbus_client):
    """Test the integration sets up successfully."""
    # Initialize HomeAssistant data
    hass.data.setdefault(DOMAIN, {})

    # Patch the ModbusClient class
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_modbus_client,
    ):
        # Setup the entry
        assert await async_setup_entry(hass, mock_config_entry)

        # Verify data structures were created
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert "coordinator" in hass.data[DOMAIN][mock_config_entry.entry_id]

        # Get the coordinator
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

        # Verify coordinator has data
        assert coordinator.data is not None

        # Verify connection methods were called
        assert mock_modbus_client.connect.called
        assert mock_modbus_client.read_holding_registers.called
