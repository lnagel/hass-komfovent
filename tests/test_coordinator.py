"""Tests for the Komfovent coordinator."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.komfovent.coordinator import KomfoventCoordinator


@pytest.fixture
def register_data():
    """Load register data from JSON file."""
    json_file = Path("documentation/C6_holding_registers.json")
    
    with json_file.open() as f:
        data = json.load(f)
    
    # Transform data to match expected format
    transformed_data = {}
    for block_start, values in data.items():
        block_start_int = int(block_start)
        for i, value in enumerate(values):
            transformed_data[block_start_int + i + 1] = value
    
    return transformed_data


async def test_coordinator_updates_data(hass: HomeAssistant, register_data):
    """Test that the coordinator can update and process data."""
    # Create a mock modbus client
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    
    # Configure read_holding_registers to return test data
    async def mock_read_registers(address, count):
        result = {}
        for reg in range(address, address + count):
            if reg in register_data:
                result[reg] = register_data[reg]
        return result
    
    mock_client.read_holding_registers = AsyncMock(side_effect=mock_read_registers)
    
    # Patch the modbus client
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_client
    ):
        # Create and initialize coordinator
        coordinator = KomfoventCoordinator(hass, "localhost", 502)
        
        # Test connection
        assert await coordinator.connect()
        
        # Force a data update
        await coordinator.async_refresh()
        
        # Verify coordinator has data
        assert coordinator.data is not None
        
        # Verify the client was called correctly
        assert mock_client.connect.called
        assert mock_client.read_holding_registers.called


async def test_coordinator_handles_connection_failure(hass: HomeAssistant):
    """Test that the coordinator handles connection failures gracefully."""
    # Create a mock client that fails to connect
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=False)
    
    # Patch the modbus client
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_client
    ):
        # Create coordinator
        coordinator = KomfoventCoordinator(hass, "localhost", 502)
        
        # Test connection - should fail
        assert not await coordinator.connect()
