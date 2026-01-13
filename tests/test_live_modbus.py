"""Integration tests that use actual socket connections."""

import asyncio
import contextlib
import random

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN, Controller
from custom_components.komfovent.coordinator import KomfoventCoordinator
from custom_components.komfovent.modbus import KomfoventModbusClient
from modbus_server import run_server


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_live_modbus_connection(hass: HomeAssistant, mock_registers):
    """
    Test actual connection to modbus server.

    This test requires a running modbus server and will be skipped by default.
    To run: pytest tests/test_live_modbus.py -v --socket-enabled
    """
    _register_name, register_data = mock_registers

    # Use non-privileged port for testing
    test_port = random.randint(1024, 50000)
    server_task = asyncio.create_task(run_server("127.0.0.1", test_port, register_data))

    # Wait for server to start
    await asyncio.sleep(0.1)

    # Create and connect to the server
    client = KomfoventModbusClient("127.0.0.1", test_port)

    try:
        # Test connection - should not raise
        await client.connect()

        # Read some registers
        data = await client.read(registers.REG_POWER, 34)

        # Verify we got data back
        assert data
        assert len(data) == 29

    finally:
        # Clean up
        await client.close()
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_live_coordinator(hass: HomeAssistant, mock_registers):
    """
    Test coordinator with actual modbus server.

    This test requires a running modbus server and will be skipped by default.
    To run: pytest tests/test_live_modbus.py -v --socket-enabled
    """
    register_name, register_data = mock_registers
    controller = Controller[register_name.split("_registers_")[0]]

    # Use non-privileged port for testing
    test_port = random.randint(1024, 50000)
    server_task = asyncio.create_task(run_server("127.0.0.1", test_port, register_data))

    # Wait for server to start
    await asyncio.sleep(0.1)

    # Create mock config entry
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: test_port},
        entry_id="test_entry_id",
    )

    # Create coordinator
    coordinator = KomfoventCoordinator(hass, config_entry=mock_config_entry)

    try:
        # Connect - should not raise
        await coordinator.connect()

        # Update data
        await coordinator.async_refresh()

        # Verify data
        assert coordinator.data is not None
        assert len(coordinator.data) > 0

        # Verify 16-bit register
        assert coordinator.data[1] == register_data["1"][0]

        # Verify 32-bit register
        assert (
            coordinator.data[1000]
            == (register_data["1000"][0] << 16) + register_data["1000"][1]
        )

        # Verify controller type
        assert coordinator.controller == controller

    finally:
        # Ensure client is closed
        if hasattr(coordinator, "client") and coordinator.client:
            await coordinator.client.close()
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task
