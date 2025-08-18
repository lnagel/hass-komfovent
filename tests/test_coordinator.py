"""Tests for the Komfovent coordinator."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.coordinator import KomfoventCoordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
        entry_id="test_entry_id",
    )


async def test_coordinator_updates_data(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that the coordinator can update and process data."""
    # Create mock client with required async methods
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()  # Should not raise exception
    mock_client.read = AsyncMock(return_value={1: 42})

    # Patch the client class
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_client,
    ):
        # Create and initialize coordinator
        coordinator = KomfoventCoordinator(hass, config_entry=mock_config_entry)

        # Test connection - should not raise
        await coordinator.connect()

        # Force a data update
        await coordinator.async_refresh()

        # Verify coordinator has data
        assert coordinator.data is not None

        # Verify the client was called correctly
        assert mock_client.connect.called
        assert mock_client.read.called


async def test_coordinator_handles_connection_failure(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Test that the coordinator handles connection failures gracefully."""
    # Create mock client that fails to connect
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock(side_effect=ConnectionError)
    mock_client.read = AsyncMock(return_value={1: 42})

    # Patch the client class
    with patch(
        "custom_components.komfovent.modbus.KomfoventModbusClient",
        return_value=mock_client,
    ):
        # Create coordinator
        coordinator = KomfoventCoordinator(hass, config_entry=mock_config_entry)

        # Test connection - should raise
        with pytest.raises(ConnectionError):
            await coordinator.connect()
