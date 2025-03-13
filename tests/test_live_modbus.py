"""Integration tests that use actual socket connections."""

import asyncio
import contextlib
import json
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant

from custom_components.komfovent.coordinator import KomfoventCoordinator
from custom_components.komfovent.modbus import KomfoventModbusClient
from modbus_server import run_server


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_live_modbus_connection(hass: HomeAssistant):
    """
    Test actual connection to modbus server.

    This test requires a running modbus server and will be skipped by default.
    To run with socket connections enabled: pytest tests/test_live_modbus.py -v --socket-enabled
    """
    # Load test data
    test_data_path = Path("documentation/C6_holding_registers.json")
    with test_data_path.open() as f:
        register_data = json.load(f)

    # Use non-privileged port for testing
    test_port = 5502
    server_task = asyncio.create_task(run_server("127.0.0.1", test_port, register_data))

    # Wait for server to start
    await asyncio.sleep(0.1)

    # Create and connect to the server
    client = KomfoventModbusClient("127.0.0.1", test_port)

    try:
        # Test connection
        connected = await client.connect()
        assert connected

        # Read some registers
        data = await client.read_holding_registers(0, 34)

        # Verify we got data back
        assert data
        assert len(data) == 34

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
    """
    Test coordinator with actual modbus server.

    This test requires a running modbus server and will be skipped by default.
    To run with socket connections enabled: pytest tests/test_live_modbus.py -v --socket-enabled
    """
    # Load test data
    test_data_path = Path("documentation/C6_holding_registers.json")
    with test_data_path.open() as f:
        register_data = json.load(f)

    # Use non-privileged port for testing
    test_port = 5503
    server_task = asyncio.create_task(run_server("127.0.0.1", test_port, register_data))

    # Wait for server to start
    await asyncio.sleep(0.1)

    # Create coordinator
    coordinator = KomfoventCoordinator(hass, "127.0.0.1", test_port)

    try:
        # Connect
        connected = await coordinator.connect()
        assert connected

        # Update data
        await coordinator.async_refresh()

        # Verify data
        assert coordinator.data is not None
        assert len(coordinator.data) > 0
        assert coordinator.data[0] == 1
        assert coordinator.data[999] == 20037670
        assert coordinator.data[1001] == 17838105

    finally:
        # Ensure client is closed
        if hasattr(coordinator, "client") and coordinator.client:
            await coordinator.client.close()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
