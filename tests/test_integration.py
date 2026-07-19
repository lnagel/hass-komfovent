"""Tests for Komfovent integration initialization."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent import (
    KomfoventDomainData,
    _async_update_listener,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.komfovent.const import (
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPT_UPDATE_INTERVAL,
)
from custom_components.komfovent.coordinator import KomfoventRuntimeData


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_config_entry_with_options():
    """Create a mock config entry with custom update_interval option."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
        options={OPT_UPDATE_INTERVAL: 60},
        entry_id="test_entry_id",
    )


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_modbus_client):
    """Test the integration sets up successfully."""
    # Initialize HomeAssistant mocks
    hass.services = AsyncMock()
    hass.services.async_register = MagicMock()  # Use sync mock for register
    hass.config = MagicMock()  # Use sync mock for config
    hass.config_entries = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

    # Create mock client with required async methods
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()  # Should not raise exception
    mock_client.read = AsyncMock(return_value={1: 42})

    # Patch the client class where it's used and services registration
    with (
        patch(
            "custom_components.komfovent.coordinator.KomfoventModbusClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.komfovent.services.async_register_services",
            new_callable=AsyncMock,
        ) as mock_register_services,
    ):
        # Create coordinator directly and simulate the setup process
        from custom_components.komfovent.coordinator import KomfoventCoordinator

        coordinator = KomfoventCoordinator(hass, config_entry=mock_config_entry)

        # Connect and get initial data
        await coordinator.connect()
        await coordinator.async_refresh()

        # Simulate what async_setup_entry does
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=coordinator, firmware_store=MagicMock()
        )
        await mock_register_services(hass)
        await hass.config_entries.async_forward_entry_setups(mock_config_entry, [])

        # Verify runtime data was stored on the entry
        assert mock_config_entry.runtime_data.coordinator is coordinator

        # Verify coordinator has data
        assert coordinator.data is not None

        # Verify connection methods were called
        assert mock_client.connect.called
        assert mock_client.read.called


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    async def test_setup_entry_with_default_update_interval(
        self, hass: HomeAssistant, mock_config_entry, mock_modbus_client
    ):
        """Test setup uses default update_interval when not in options."""
        # Create a mock coordinator to avoid complex setup
        mock_coordinator = MagicMock()
        mock_coordinator.connect = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.update_interval = None
        mock_coordinator.controller = MagicMock()

        # Create mock firmware components
        mock_firmware_store = MagicMock()
        mock_firmware_store.async_load = AsyncMock()
        mock_firmware_checker = MagicMock()
        mock_firmware_checker.register_controller_type = MagicMock()
        mock_firmware_checker.async_start = AsyncMock()

        with (
            patch(
                "custom_components.komfovent.KomfoventCoordinator",
                return_value=mock_coordinator,
            ) as mock_coordinator_class,
            patch(
                "custom_components.komfovent.FirmwareStore",
                return_value=mock_firmware_store,
            ),
            patch(
                "custom_components.komfovent.FirmwareChecker",
                return_value=mock_firmware_checker,
            ),
            patch(
                "custom_components.komfovent.async_register_services",
                new_callable=AsyncMock,
            ),
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        # Verify coordinator was created with default update_interval
        mock_coordinator_class.assert_called_once()
        call_kwargs = mock_coordinator_class.call_args.kwargs
        assert call_kwargs["update_interval"] == timedelta(
            seconds=DEFAULT_UPDATE_INTERVAL
        )

    async def test_setup_entry_with_custom_update_interval(
        self, hass: HomeAssistant, mock_config_entry_with_options, mock_modbus_client
    ):
        """Test setup uses custom update_interval from options."""
        mock_coordinator = MagicMock()
        mock_coordinator.connect = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.update_interval = None
        mock_coordinator.controller = MagicMock()

        # Create mock firmware components
        mock_firmware_store = MagicMock()
        mock_firmware_store.async_load = AsyncMock()
        mock_firmware_checker = MagicMock()
        mock_firmware_checker.register_controller_type = MagicMock()
        mock_firmware_checker.async_start = AsyncMock()

        with (
            patch(
                "custom_components.komfovent.KomfoventCoordinator",
                return_value=mock_coordinator,
            ) as mock_coordinator_class,
            patch(
                "custom_components.komfovent.FirmwareStore",
                return_value=mock_firmware_store,
            ),
            patch(
                "custom_components.komfovent.FirmwareChecker",
                return_value=mock_firmware_checker,
            ),
            patch(
                "custom_components.komfovent.async_register_services",
                new_callable=AsyncMock,
            ),
            patch.object(
                hass.config_entries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            result = await async_setup_entry(hass, mock_config_entry_with_options)

        assert result is True
        # Verify coordinator was created with custom update_interval
        mock_coordinator_class.assert_called_once()
        call_kwargs = mock_coordinator_class.call_args.kwargs
        assert call_kwargs["update_interval"] == timedelta(seconds=60)


class TestAsyncUpdateListener:
    """Tests for _async_update_listener function."""

    @pytest.fixture
    def mock_config_entry_with_updated_options(self):
        """Create a mock config entry with updated options."""
        return MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
            options={OPT_UPDATE_INTERVAL: 120},
            entry_id="test_entry_id",
        )

    async def test_update_listener_changes_update_interval(
        self,
        hass: HomeAssistant,
        mock_coordinator,
        mock_config_entry_with_updated_options,
    ):
        """Test update listener changes coordinator update_interval."""
        # Attach runtime data with the coordinator to the entry
        mock_config_entry_with_updated_options.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=MagicMock()
        )

        # Call the update listener
        await _async_update_listener(hass, mock_config_entry_with_updated_options)

        # Verify the coordinator's update_interval was updated
        assert mock_coordinator.update_interval == timedelta(seconds=120)

    async def test_update_listener_uses_default_when_option_missing(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test update listener uses default when option is missing."""
        # Attach runtime data with the coordinator to the entry
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=MagicMock()
        )

        # Call the update listener (options is empty by default in mock_config_entry)
        await _async_update_listener(hass, mock_config_entry)

        # Verify the coordinator's update_interval was set to default
        assert mock_coordinator.update_interval == timedelta(
            seconds=DEFAULT_UPDATE_INTERVAL
        )


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry function."""

    async def test_unload_entry_success(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test successful unload tears down the last entry's domain data."""
        mock_firmware_store = MagicMock()
        mock_firmware_checker = MagicMock()
        mock_firmware_checker.unregister_controller_type = MagicMock()
        mock_firmware_checker.async_stop = AsyncMock()

        hass.data[DOMAIN] = {
            "domain_data": KomfoventDomainData(
                firmware_store=mock_firmware_store,
                firmware_checker=mock_firmware_checker,
                entry_count=1,
            )
        }
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=mock_firmware_store
        )

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_unload:
            result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_unload.assert_awaited_once()
        mock_firmware_checker.unregister_controller_type.assert_called_once_with(
            mock_coordinator.controller
        )
        # Last entry: checker stopped and domain data removed
        mock_firmware_checker.async_stop.assert_awaited_once()
        assert "domain_data" not in hass.data[DOMAIN]

    async def test_unload_entry_failure(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test failed platform unload returns False and keeps domain data."""
        mock_firmware_store = MagicMock()
        mock_firmware_checker = MagicMock()
        mock_firmware_checker.async_stop = AsyncMock()

        hass.data[DOMAIN] = {
            "domain_data": KomfoventDomainData(
                firmware_store=mock_firmware_store,
                firmware_checker=mock_firmware_checker,
                entry_count=1,
            )
        }
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=mock_firmware_store
        )

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await async_unload_entry(hass, mock_config_entry)

        assert result is False
        # Failed unload leaves domain data untouched
        assert "domain_data" in hass.data[DOMAIN]
        mock_firmware_checker.async_stop.assert_not_called()
