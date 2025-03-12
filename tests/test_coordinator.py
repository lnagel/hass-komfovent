"""Tests for the Komfovent coordinator."""

from unittest.mock import AsyncMock, create_autospec, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.komfovent.coordinator import KomfoventCoordinator


async def test_coordinator_updates_data(hass: HomeAssistant, mock_modbus_client):
    """Test that the coordinator can update and process data."""
    # Create async mock for connect method
    mock_modbus_client.connect = AsyncMock(return_value=True)
    mock_modbus_client.read_holding_registers = AsyncMock(return_value={1: 42})

    # Patch the client
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_modbus_client,
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
        assert mock_modbus_client.connect.called
        assert mock_modbus_client.read_holding_registers.called


async def test_coordinator_handles_connection_failure(hass: HomeAssistant):
    """Test that the coordinator handles connection failures gracefully."""
    # Create a mock client that fails to connect
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=False)

    # Patch both the modbus client class and the pymodbus client
    with (
        patch(
            "custom_components.komfovent.modbus.KomfoventModbusClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.komfovent.modbus.AsyncModbusTcpClient",
        ),
    ):
        # Create coordinator
        coordinator = KomfoventCoordinator(hass, "localhost", 502)

        # Test connection - should fail
        assert not await coordinator.connect()
