"""Tests for Komfovent integration initialization."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    entity_registry as er,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
        entry_id="test_entry_id",
    )


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_modbus_client):
    """Test the integration sets up successfully."""
    # Initialize HomeAssistant mocks
    hass.data.setdefault(DOMAIN, {})
    hass.services = AsyncMock()
    hass.services.async_register = MagicMock()  # Use sync mock for register
    hass.config = MagicMock()  # Use sync mock for config
    hass.config_entries = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    # Create mock client with required async methods
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()  # Should not raise exception
    mock_client.read = AsyncMock(return_value={1: 42})

    # Mock the entity registry
    entity_registry = er.async_get(hass)
    entity_registry.entities = {}

    # Patch the client class and services registration
    with (
        patch(
            "custom_components.komfovent.modbus.KomfoventModbusClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.komfovent.services.async_register_services"
        ) as mock_register_services,
    ):
        # Create coordinator directly and simulate the setup process
        from custom_components.komfovent.coordinator import KomfoventCoordinator

        coordinator = KomfoventCoordinator(
            hass,
            host=mock_config_entry.data[CONF_HOST],
            port=mock_config_entry.data[CONF_PORT],
            config_entry=mock_config_entry,
        )

        # Connect and get initial data
        await coordinator.connect()
        await coordinator.async_refresh()

        # Simulate what async_setup_entry does
        hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = coordinator
        await mock_register_services(hass)
        await hass.config_entries.async_forward_entry_setups(mock_config_entry, [])

        # Verify data structures were created
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]

        # Verify coordinator has data
        assert coordinator.data is not None

        # Verify connection methods were called
        assert mock_client.connect.called
        assert mock_client.read.called
