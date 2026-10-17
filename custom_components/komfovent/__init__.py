"""The Komfovent integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform

from .const import (
    DEFAULT_EMA_TIME_CONSTANT,
    DEFAULT_FIRMWARE_UPDATES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPT_EMA_TIME_CONSTANT,
    OPT_FIRMWARE_UPDATES,
    OPT_UPDATE_INTERVAL,
)
from .coordinator import KomfoventCoordinator, KomfoventRuntimeData
from .firmware.checker import FirmwareChecker
from .firmware.store import FirmwareStore
from .services import async_register_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import KomfoventConfigEntry


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]


@dataclass
class KomfoventDomainData:
    """Domain-level data shared across all Komfovent config entries."""

    firmware_store: FirmwareStore
    firmware_checker: FirmwareChecker
    # Config entries with firmware updates enabled
    firmware_entries: set[str] = field(default_factory=set)


def _get_platforms(*, firmware_enabled: bool) -> list[Platform]:
    """Return the platforms to set up for an entry."""
    if firmware_enabled:
        return PLATFORMS
    return [platform for platform in PLATFORMS if platform != Platform.UPDATE]


async def _async_get_domain_data(hass: HomeAssistant) -> KomfoventDomainData:
    """Return the shared firmware components, creating them on first use."""
    domain = hass.data.setdefault(DOMAIN, {})
    if "domain_data" not in domain:
        firmware_store = FirmwareStore(hass)
        await firmware_store.async_load()
        domain["domain_data"] = KomfoventDomainData(
            firmware_store=firmware_store,
            firmware_checker=FirmwareChecker(hass, firmware_store),
        )
        _LOGGER.debug("Created domain-level firmware components")
    return domain["domain_data"]


async def async_setup_entry(hass: HomeAssistant, entry: KomfoventConfigEntry) -> bool:
    """Set up Komfovent from a config entry."""
    update_interval = entry.options.get(OPT_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    ema_time_constant = entry.options.get(
        OPT_EMA_TIME_CONSTANT, DEFAULT_EMA_TIME_CONSTANT
    )
    firmware_enabled = entry.options.get(OPT_FIRMWARE_UPDATES, DEFAULT_FIRMWARE_UPDATES)
    coordinator = KomfoventCoordinator(
        hass=hass,
        config_entry=entry,
        update_interval=timedelta(seconds=update_interval),
        ema_time_constant=ema_time_constant,
    )

    await coordinator.connect()

    await coordinator.async_config_entry_first_refresh()

    domain_data = await _async_get_domain_data(hass) if firmware_enabled else None

    # Store per-entry runtime data on the config entry
    entry.runtime_data = KomfoventRuntimeData(
        coordinator=coordinator,
        firmware_store=domain_data.firmware_store if domain_data else None,
    )

    await async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(
        entry, _get_platforms(firmware_enabled=firmware_enabled)
    )

    # Register for firmware checks only once setup succeeded, so a failed
    # setup (which is never unloaded) cannot leave the checker running
    if domain_data is not None:
        domain_data.firmware_entries.add(entry.entry_id)
        domain_data.firmware_checker.register_controller_type(coordinator.controller)
        await domain_data.firmware_checker.async_start()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant,
    entry: KomfoventConfigEntry,
) -> None:
    """Handle options update."""
    firmware_enabled = entry.options.get(OPT_FIRMWARE_UPDATES, DEFAULT_FIRMWARE_UPDATES)
    if firmware_enabled != entry.runtime_data.firmware_enabled:
        # Adds or removes the update platform, which needs a full reload
        _LOGGER.debug("Firmware updates option changed, reloading entry")
        await hass.config_entries.async_reload(entry.entry_id)
        return

    coordinator = entry.runtime_data.coordinator
    update_interval = entry.options.get(OPT_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator.update_interval = timedelta(seconds=update_interval)
    coordinator.ema_time_constant = entry.options.get(
        OPT_EMA_TIME_CONSTANT, DEFAULT_EMA_TIME_CONSTANT
    )
    _LOGGER.debug("Update interval changed to %s seconds", update_interval)


async def async_unload_entry(hass: HomeAssistant, entry: KomfoventConfigEntry) -> bool:
    """Unload a config entry."""
    firmware_enabled = entry.runtime_data.firmware_enabled
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, _get_platforms(firmware_enabled=firmware_enabled)
    )
    if unload_ok and firmware_enabled:
        domain_data: KomfoventDomainData = hass.data[DOMAIN]["domain_data"]
        domain_data.firmware_entries.discard(entry.entry_id)
        domain_data.firmware_checker.unregister_controller_type(
            entry.runtime_data.coordinator.controller
        )

        # Stop firmware checker after the last firmware-enabled entry
        if not domain_data.firmware_entries:
            await domain_data.firmware_checker.async_stop()
            hass.data[DOMAIN].pop("domain_data")
            _LOGGER.debug("Stopped firmware checker and cleaned up domain data")

    return unload_ok
