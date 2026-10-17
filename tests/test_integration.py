"""Tests for Komfovent integration initialization."""

from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent import (
    PLATFORMS,
    KomfoventDomainData,
    _async_update_listener,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.komfovent.const import (
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPT_FIRMWARE_UPDATES,
    OPT_UPDATE_INTERVAL,
)
from custom_components.komfovent.coordinator import KomfoventRuntimeData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


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


@pytest.fixture
def mock_config_entry_firmware_disabled():
    """Create a mock config entry with firmware updates disabled."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
        options={OPT_FIRMWARE_UPDATES: False},
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_firmware():
    """Patch the domain-level firmware store and checker."""
    with (
        patch("custom_components.komfovent.FirmwareStore", autospec=True) as store,
        patch("custom_components.komfovent.FirmwareChecker", autospec=True) as checker,
    ):
        yield store, checker


@pytest.fixture
def mock_setup(hass: HomeAssistant):
    """Patch the coordinator, services and platform forwarding for setup."""
    mock_coordinator = MagicMock()
    mock_coordinator.connect = AsyncMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    with (
        patch(
            "custom_components.komfovent.KomfoventCoordinator",
            return_value=mock_coordinator,
        ),
        patch(
            "custom_components.komfovent.async_register_services",
            new_callable=AsyncMock,
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new_callable=AsyncMock,
        ) as mock_forward,
    ):
        yield mock_coordinator, mock_forward


def firmware_domain_data(*entry_ids: str) -> tuple[KomfoventDomainData, MagicMock]:
    """Create domain data with a mocked firmware checker."""
    checker = MagicMock()
    checker.async_start = AsyncMock()
    checker.async_stop = AsyncMock()
    domain_data = KomfoventDomainData(
        firmware_store=MagicMock(),
        firmware_checker=checker,
        firmware_entries=set(entry_ids),
    )
    return domain_data, checker


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
        mock_config_entry.runtime_data = KomfoventRuntimeData(coordinator=coordinator)
        await mock_register_services(hass)
        await hass.config_entries.async_forward_entry_setups(mock_config_entry, [])

        # Verify runtime data was stored on the entry
        assert mock_config_entry.runtime_data.coordinator is coordinator

        # Verify coordinator has data
        assert coordinator.data is not None

        # Verify connection methods were called
        assert mock_client.connect.called
        assert mock_client.read.called


@pytest.mark.usefixtures("mock_firmware")
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

        with (
            patch(
                "custom_components.komfovent.KomfoventCoordinator",
                return_value=mock_coordinator,
            ) as mock_coordinator_class,
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

        with (
            patch(
                "custom_components.komfovent.KomfoventCoordinator",
                return_value=mock_coordinator,
            ) as mock_coordinator_class,
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

    async def test_setup_entry_registers_firmware(
        self, hass: HomeAssistant, mock_config_entry, mock_firmware, mock_setup
    ):
        """Test firmware updates are enabled by default."""
        store_class, checker_class = mock_firmware
        mock_coordinator, mock_forward = mock_setup

        await async_setup_entry(hass, mock_config_entry)

        mock_forward.assert_awaited_once_with(mock_config_entry, PLATFORMS)
        assert mock_config_entry.runtime_data.firmware_store is store_class.return_value
        checker = checker_class.return_value
        checker.register_controller_type.assert_called_once_with(
            mock_coordinator.controller
        )
        checker.async_start.assert_awaited_once()
        domain_data = hass.data[DOMAIN]["domain_data"]
        assert domain_data.firmware_entries == {"test_entry_id"}

    async def test_setup_entry_reuses_domain_data(
        self, hass: HomeAssistant, mock_config_entry, mock_firmware, mock_setup
    ):
        """Test further entries share the existing firmware components."""
        store_class, _ = mock_firmware
        domain_data, _ = firmware_domain_data("other_entry_id")
        hass.data[DOMAIN] = {"domain_data": domain_data}

        await async_setup_entry(hass, mock_config_entry)

        store_class.assert_not_called()
        assert mock_config_entry.runtime_data.firmware_store is (
            domain_data.firmware_store
        )
        assert domain_data.firmware_entries == {"other_entry_id", "test_entry_id"}

    async def test_setup_entry_firmware_disabled(
        self,
        hass: HomeAssistant,
        mock_config_entry_firmware_disabled,
        mock_firmware,
        mock_setup,
    ):
        """Test disabled firmware updates skip the update platform and checker."""
        store_class, checker_class = mock_firmware
        _, mock_forward = mock_setup

        await async_setup_entry(hass, mock_config_entry_firmware_disabled)

        platforms = mock_forward.call_args.args[1]
        assert Platform.UPDATE not in platforms
        assert set(platforms) == set(PLATFORMS) - {Platform.UPDATE}
        assert mock_config_entry_firmware_disabled.runtime_data.firmware_store is None
        store_class.assert_not_called()
        checker_class.assert_not_called()
        assert "domain_data" not in hass.data.get(DOMAIN, {})

    async def test_setup_entry_platform_failure_does_not_register(
        self, hass: HomeAssistant, mock_config_entry, mock_firmware, mock_setup
    ):
        """Test a failed platform setup leaves firmware tracking untouched."""
        _, checker_class = mock_firmware
        _, mock_forward = mock_setup
        mock_forward.side_effect = RuntimeError("platform failed")

        with pytest.raises(RuntimeError):
            await async_setup_entry(hass, mock_config_entry)

        assert hass.data[DOMAIN]["domain_data"].firmware_entries == set()
        checker_class.return_value.register_controller_type.assert_not_called()
        checker_class.return_value.async_start.assert_not_called()


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
        mock_coordinator.config_data = dict(mock_config_entry_with_updated_options.data)

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
        mock_coordinator.config_data = dict(mock_config_entry.data)

        # Call the update listener (options is empty by default in mock_config_entry)
        await _async_update_listener(hass, mock_config_entry)

        # Verify the coordinator's update_interval was set to default
        assert mock_coordinator.update_interval == timedelta(
            seconds=DEFAULT_UPDATE_INTERVAL
        )

    async def test_update_listener_reloads_when_data_changed(
        self,
        hass: HomeAssistant,
        mock_coordinator,
        mock_config_entry_with_updated_options,
    ):
        """Test update listener reloads the entry after reconfigure changed data."""
        mock_config_entry_with_updated_options.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator
        )
        mock_coordinator.config_data = {CONF_HOST: "192.168.1.1", CONF_PORT: 502}
        mock_coordinator.update_interval = timedelta(seconds=30)

        with patch.object(
            hass.config_entries, "async_reload", new=AsyncMock()
        ) as mock_reload:
            await _async_update_listener(hass, mock_config_entry_with_updated_options)

        mock_reload.assert_awaited_once_with("test_entry_id")
        assert mock_coordinator.update_interval == timedelta(seconds=30)

    @pytest.mark.parametrize(
        ("firmware_store", "options"),
        [
            (MagicMock(), {OPT_FIRMWARE_UPDATES: False}),
            (None, {OPT_FIRMWARE_UPDATES: True}),
            (None, {}),
        ],
        ids=["disabled", "enabled", "default_enabled"],
    )
    async def test_update_listener_reloads_on_firmware_toggle(
        self, hass: HomeAssistant, mock_coordinator, firmware_store, options
    ):
        """Test toggling firmware updates reloads the entry."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "127.0.0.1", CONF_PORT: 502},
            options=options,
            entry_id="test_entry_id",
        )
        entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=firmware_store
        )
        mock_coordinator.update_interval = None

        with patch.object(
            hass.config_entries, "async_reload", new_callable=AsyncMock
        ) as mock_reload:
            await _async_update_listener(hass, entry)

        mock_reload.assert_awaited_once_with("test_entry_id")
        assert mock_coordinator.update_interval is None


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry function."""

    async def test_unload_entry_success(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test successful platform unload returns True."""
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator
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

    async def test_unload_entry_failure(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test failed platform unload returns False."""
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator
        )

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await async_unload_entry(hass, mock_config_entry)

        assert result is False

    @pytest.mark.parametrize(
        ("other_entries", "stopped"),
        [((), True), (("other_entry_id",), False)],
        ids=["last_entry", "other_entries_remain"],
    )
    async def test_unload_entry_releases_firmware(
        self,
        hass: HomeAssistant,
        mock_coordinator,
        mock_config_entry,
        other_entries,
        stopped,
    ):
        """Test unload unregisters firmware and stops after the last entry."""
        domain_data, checker = firmware_domain_data("test_entry_id", *other_entries)
        hass.data[DOMAIN] = {"domain_data": domain_data}
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=domain_data.firmware_store
        )

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_unload:
            result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_unload.assert_awaited_once_with(mock_config_entry, PLATFORMS)
        checker.unregister_controller_type.assert_called_once_with(
            mock_coordinator.controller
        )
        assert domain_data.firmware_entries == set(other_entries)
        assert (checker.async_stop.await_count == 1) is stopped
        assert ("domain_data" not in hass.data[DOMAIN]) is stopped

    async def test_unload_entry_firmware_disabled(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test unloading an entry without firmware skips the update platform."""
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator
        )

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_unload:
            await async_unload_entry(hass, mock_config_entry)

        assert Platform.UPDATE not in mock_unload.call_args.args[1]
        assert DOMAIN not in hass.data

    async def test_unload_entry_failure_keeps_firmware(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test a failed unload keeps the firmware registration."""
        domain_data, checker = firmware_domain_data("test_entry_id")
        hass.data[DOMAIN] = {"domain_data": domain_data}
        mock_config_entry.runtime_data = KomfoventRuntimeData(
            coordinator=mock_coordinator, firmware_store=domain_data.firmware_store
        )

        with patch.object(
            hass.config_entries,
            "async_unload_platforms",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await async_unload_entry(hass, mock_config_entry)

        assert result is False
        assert domain_data.firmware_entries == {"test_entry_id"}
        checker.async_stop.assert_not_awaited()
