"""The Komfovent integration."""
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    Platform,
)
from homeassistant.core import ServiceCall
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import KomfoventCoordinator
from .registers import REG_EPOCH_TIME

PLATFORMS = [Platform.CLIMATE, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Komfovent from a config entry."""
    coordinator = KomfoventCoordinator(
        hass, entry.data[CONF_HOST], entry.data[CONF_PORT]
    )
    await coordinator.connect()

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register services
    async def set_system_time(call: ServiceCall) -> None:
        """Service to set system time on the Komfovent unit."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        epoch_time = int(time.time())  # Local time as epoch seconds
        await coordinator.client.write_register(REG_EPOCH_TIME, epoch_time)

    hass.services.async_register(DOMAIN, "set_system_time", set_system_time)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
