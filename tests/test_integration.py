"""Tests for Komfovent integration initialization."""

from unittest.mock import AsyncMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry
import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.komfovent import async_setup_entry
from custom_components.komfovent.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "localhost", CONF_PORT: 502},
        entry_id="test_entry_id",
    )


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_modbus_client):
    """Test the integration sets up successfully."""
    # Initialize HomeAssistant mocks
    hass.data.setdefault(DOMAIN, {})
    hass.services = AsyncMock()
    hass.config_entries = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    # Create mock client with required async methods
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.read_holding_registers = AsyncMock(return_value={1: 42})

    # Patch the client class
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_client,
    ):
        # Setup the entry
        assert await async_setup_entry(hass, mock_config_entry)

        # Verify data structures were created
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]

        # Verify coordinator has data
        assert coordinator.data is not None

        # Verify connection methods were called
        assert mock_client.connect.called
        assert mock_client.read_holding_registers.called
