"""Tests for the Komfovent coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.coordinator import KomfoventCoordinator
from custom_components.komfovent.registers import REG_SUPPLY_TEMP


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

    # Patch the client class where it's used
    with patch(
        "custom_components.komfovent.coordinator.KomfoventModbusClient",
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

    # Patch the client class where it's used
    with patch(
        "custom_components.komfovent.coordinator.KomfoventModbusClient",
        return_value=mock_client,
    ):
        # Create coordinator
        coordinator = KomfoventCoordinator(hass, config_entry=mock_config_entry)

        # Test connection - should raise
        with pytest.raises(ConnectionError):
            await coordinator.connect()


async def test_cooldown_delays_update(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that cooldown delays the next update."""
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()
    mock_client.read = AsyncMock(return_value={1: 42})

    with (
        patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.komfovent.coordinator.asyncio.sleep", new=AsyncMock()
        ) as mock_sleep,
    ):
        coordinator = KomfoventCoordinator(hass, config_entry=mock_config_entry)
        await coordinator.connect()

        # Set a 1 second cooldown
        coordinator.set_cooldown(1.0)

        # Trigger an update - should wait for cooldown
        await coordinator.async_refresh()

        # Verify sleep was called with approximately 1 second
        mock_sleep.assert_called_once()
        wait_time = mock_sleep.call_args[0][0]
        assert 0.9 < wait_time <= 1.0


class TestEmaFiltering:
    """Tests for EMA filtering in coordinator."""

    def test_ema_not_applied_when_disabled(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test EMA is not applied when time constant is 0."""
        with patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=AsyncMock(),
        ):
            coordinator = KomfoventCoordinator(
                hass, config_entry=mock_config_entry, ema_time_constant=0
            )
            coordinator.data = {REG_SUPPLY_TEMP: 200}
            coordinator.last_update_success_time = utcnow() - timedelta(seconds=30)

            data = {REG_SUPPLY_TEMP: 250}
            coordinator._apply_ema_on_update_data(data)

            # Value should remain unchanged (no filtering)
            assert data[REG_SUPPLY_TEMP] == 250

    def test_ema_not_applied_when_no_previous_data(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test EMA is not applied on first update."""
        with patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=AsyncMock(),
        ):
            coordinator = KomfoventCoordinator(
                hass, config_entry=mock_config_entry, ema_time_constant=300
            )
            coordinator.data = None  # type: ignore[assignment]
            coordinator.last_update_success_time = utcnow() - timedelta(seconds=30)

            data = {REG_SUPPLY_TEMP: 250}
            coordinator._apply_ema_on_update_data(data)

            # Value should remain unchanged
            assert data[REG_SUPPLY_TEMP] == 250

    def test_ema_not_applied_when_no_last_update_time(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test EMA is not applied when last_update_success_time is None."""
        with patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=AsyncMock(),
        ):
            coordinator = KomfoventCoordinator(
                hass, config_entry=mock_config_entry, ema_time_constant=300
            )
            coordinator.data = {REG_SUPPLY_TEMP: 200}
            coordinator.last_update_success_time = None

            data = {REG_SUPPLY_TEMP: 250}
            coordinator._apply_ema_on_update_data(data)

            # Value should remain unchanged
            assert data[REG_SUPPLY_TEMP] == 250

    def test_ema_applied_when_enabled(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test EMA filtering is applied when conditions are met."""
        with patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=AsyncMock(),
        ):
            coordinator = KomfoventCoordinator(
                hass, config_entry=mock_config_entry, ema_time_constant=300
            )
            coordinator.data = {REG_SUPPLY_TEMP: 200}
            coordinator.last_update_success_time = utcnow() - timedelta(seconds=30)

            data = {REG_SUPPLY_TEMP: 250}
            coordinator._apply_ema_on_update_data(data)

            # Value should be filtered (between previous and current)
            # With tau=300, dt=30: alpha = 30/(300+30) = 0.0909
            # filtered = 0.0909 * 250 + 0.9091 * 200 = 204.5
            assert data[REG_SUPPLY_TEMP] == pytest.approx(204.5, rel=0.01)

    def test_ema_skips_registers_not_in_data(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test EMA only processes registers present in data."""
        with patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=AsyncMock(),
        ):
            coordinator = KomfoventCoordinator(
                hass, config_entry=mock_config_entry, ema_time_constant=300
            )
            coordinator.data = {REG_SUPPLY_TEMP: 200}
            coordinator.last_update_success_time = utcnow() - timedelta(seconds=30)

            # Data without any EMA registers
            data = {999: 100}
            coordinator._apply_ema_on_update_data(data)

            # Non-EMA register should remain unchanged
            assert data[999] == 100
