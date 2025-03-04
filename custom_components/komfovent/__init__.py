"""The Komfovent integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.modbus import get_hub
from homeassistant.components.lovelace import async_register_dashboard

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import KomfoventCoordinator
from .dashboard import async_get_dashboard

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Komfovent from a config entry."""
    hub = get_hub(hass, DEFAULT_NAME)
    coordinator = KomfoventCoordinator(hass, hub)
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    # Register the dashboard
    await async_register_dashboard(
        hass,
        "komfovent",
        "Komfovent",
        require_admin=False,
        icon="mdi:hvac",
        show_in_sidebar=True,
        config=await async_get_dashboard()
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
