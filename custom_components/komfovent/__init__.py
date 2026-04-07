"""The Komfovent integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform

from .const import (
    DEFAULT_EMA_TIME_CONSTANT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OPT_EMA_TIME_CONSTANT,
    OPT_UPDATE_INTERVAL,
)
from .coordinator import KomfoventCoordinator
from .firmware.checker import FirmwareChecker
from .firmware.store import FirmwareStore
from .services import async_register_services

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


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
class KomfoventRuntimeData:
    """Runtime data for a Komfovent config entry."""

    coordinator: KomfoventCoordinator
    firmware_store: FirmwareStore


@dataclass
class KomfoventDomainData:
    """Domain-level data for Komfovent integration."""

    firmware_store: FirmwareStore
    firmware_checker: FirmwareChecker
    entry_count: int = 0


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Komfovent from a config entry."""
    update_interval = entry.options.get(OPT_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    ema_time_constant = entry.options.get(
        OPT_EMA_TIME_CONSTANT, DEFAULT_EMA_TIME_CONSTANT
    )
    coordinator = KomfoventCoordinator(
        hass=hass,
        config_entry=entry,
        update_interval=timedelta(seconds=update_interval),
        ema_time_constant=ema_time_constant,
    )

    await coordinator.connect()

    await coordinator.async_config_entry_first_refresh()

    # Set up domain-level data if this is the first entry
    hass.data.setdefault(DOMAIN, {})

    if "domain_data" not in hass.data[DOMAIN]:
        # First entry - create domain-level components
        firmware_store = FirmwareStore(hass)
        await firmware_store.async_load()

        firmware_checker = FirmwareChecker(hass, firmware_store)

        hass.data[DOMAIN]["domain_data"] = KomfoventDomainData(
            firmware_store=firmware_store,
            firmware_checker=firmware_checker,
        )
        _LOGGER.debug("Created domain-level firmware components")

    domain_data: KomfoventDomainData = hass.data[DOMAIN]["domain_data"]
    domain_data.entry_count += 1

    # Register this entry's controller type with the checker
    domain_data.firmware_checker.register_controller_type(coordinator.controller)

    # Create per-entry runtime data
    runtime_data = KomfoventRuntimeData(
        coordinator=coordinator,
        firmware_store=domain_data.firmware_store,
    )
    hass.data[DOMAIN][entry.entry_id] = runtime_data

    await async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start firmware checker if this is the first entry
    if domain_data.entry_count == 1:
        await domain_data.firmware_checker.async_start()
        _LOGGER.debug("Started firmware checker")

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    runtime_data: KomfoventRuntimeData = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime_data.coordinator
    update_interval = entry.options.get(OPT_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator.update_interval = timedelta(seconds=update_interval)
    coordinator.ema_time_constant = entry.options.get(
        OPT_EMA_TIME_CONSTANT, DEFAULT_EMA_TIME_CONSTANT
    )
    _LOGGER.debug("Update interval changed to %s seconds", update_interval)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        runtime_data: KomfoventRuntimeData = hass.data[DOMAIN].pop(entry.entry_id)
        domain_data: KomfoventDomainData = hass.data[DOMAIN]["domain_data"]

        # Unregister this entry's controller type
        domain_data.firmware_checker.unregister_controller_type(
            runtime_data.coordinator.controller
        )

        domain_data.entry_count -= 1

        # Stop firmware checker if this was the last entry
        if domain_data.entry_count == 0:
            await domain_data.firmware_checker.async_stop()
            hass.data[DOMAIN].pop("domain_data")
            _LOGGER.debug("Stopped firmware checker and cleaned up domain data")

    return unload_ok
