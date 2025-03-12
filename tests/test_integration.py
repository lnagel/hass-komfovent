"""Tests for Komfovent integration initialization."""

from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.komfovent import async_setup_entry
from custom_components.komfovent.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = pytest.MagicMock()
    entry.data = {CONF_HOST: "localhost", CONF_PORT: 502}
    entry.entry_id = "test_entry_id"
    return entry


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_modbus_client):
    """Test the integration sets up successfully."""
    # Initialize HomeAssistant data
    hass.data.setdefault(DOMAIN, {})

    # Patch both the modbus client class and the pymodbus client
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_modbus_client,
    ), patch(
        "custom_components.komfovent.modbus.AsyncModbusTcpClient",
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
