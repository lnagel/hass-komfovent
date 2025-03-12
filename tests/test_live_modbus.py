"""Integration tests that use actual socket connections."""

import asyncio
import json
from pathlib import Path

from modbus_server import run_server

import pytest
from homeassistant.core import HomeAssistant

from custom_components.komfovent.coordinator import KomfoventCoordinator
from custom_components.komfovent.modbus import KomfoventModbusClient


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_live_modbus_connection(hass: HomeAssistant):
    """Test actual connection to modbus server.

    This test requires a running modbus server and will be skipped by default.
    To run with socket connections enabled: pytest tests/test_live_modbus.py -v --socket-enabled
    """
    # Load test data
    test_data_path = Path("documentation/C6M_holding_registers.json")
    with test_data_path.open() as f:
        register_data = json.load(f)
        registers = {int(k) + 1: v for k, v in register_data.items()}

    # Start server in background task
    server_task = asyncio.create_task(run_server("localhost", 502, registers))

    # Wait for server to start
    await asyncio.sleep(2)

    # Create and connect to the server
    client = KomfoventModbusClient("localhost", 502)

    try:
        # Test connection
        connected = await client.connect()
        assert connected

        # Read some registers
        data = await client.read_holding_registers(1, 10)

        # Verify we got data back
        assert data
        assert len(data) > 0

    finally:
        # Clean up
        await client.close()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_live_coordinator(hass: HomeAssistant):
    """Test coordinator with actual modbus server.

    This test requires a running modbus server and will be skipped by default.
    To run with socket connections enabled: pytest tests/test_live_modbus.py -v --socket-enabled
    """
    # Create coordinator
    coordinator = KomfoventCoordinator(hass, "localhost", 502)

    try:
        # Connect
        connected = await coordinator.connect()
        assert connected

        # Update data
        await coordinator.async_refresh()

        # Verify data
        assert coordinator.data is not None
        assert len(coordinator.data) > 0

    finally:
        # Ensure client is closed
        if hasattr(coordinator, "client") and coordinator.client:
            await coordinator.client.close()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
