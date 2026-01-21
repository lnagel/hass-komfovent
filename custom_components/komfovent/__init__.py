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
    entry_count: int = 0


async def async_setup_entry(hass: HomeAssistant, entry: KomfoventConfigEntry) -> bool:
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

    # Store per-entry runtime data on the config entry
    entry.runtime_data = KomfoventRuntimeData(
        coordinator=coordinator,
        firmware_store=domain_data.firmware_store,
    )

    await async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start firmware checker if this is the first entry
    if domain_data.entry_count == 1:
        await domain_data.firmware_checker.async_start()
        _LOGGER.debug("Started firmware checker")

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant,  # noqa: ARG001
    entry: KomfoventConfigEntry,
) -> None:
    """Handle options update."""
    coordinator = entry.runtime_data.coordinator
    update_interval = entry.options.get(OPT_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    coordinator.update_interval = timedelta(seconds=update_interval)
    coordinator.ema_time_constant = entry.options.get(
        OPT_EMA_TIME_CONSTANT, DEFAULT_EMA_TIME_CONSTANT
    )
    _LOGGER.debug("Update interval changed to %s seconds", update_interval)


async def async_unload_entry(hass: HomeAssistant, entry: KomfoventConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data: KomfoventDomainData = hass.data[DOMAIN]["domain_data"]

        # Unregister this entry's controller type
        domain_data.firmware_checker.unregister_controller_type(
            entry.runtime_data.coordinator.controller
        )

        domain_data.entry_count -= 1

        # Stop firmware checker if this was the last entry
        if domain_data.entry_count == 0:
            await domain_data.firmware_checker.async_stop()
            hass.data[DOMAIN].pop("domain_data")
            _LOGGER.debug("Stopped firmware checker and cleaned up domain data")

    return unload_ok
