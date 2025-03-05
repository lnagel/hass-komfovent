"""The Komfovent integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, CONF_NAME, CONF_TYPE, CONF_DELAY, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.components.modbus import get_hub, ModbusHub

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import KomfoventCoordinator

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Komfovent from a config entry."""
    conf_hub = {CONF_HOST: entry.data[CONF_HOST], CONF_PORT: entry.data[CONF_PORT],CONF_NAME: "Komfovent",CONF_TYPE: 'tcp',CONF_DELAY:0, CONF_TIMEOUT: 500}
    hub = ModbusHub(hass, conf_hub)
    coordinator = KomfoventCoordinator(hass, hub)
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
