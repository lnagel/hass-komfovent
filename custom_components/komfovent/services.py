"""Services for Komfovent integration."""
from datetime import datetime
import zoneinfo

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE
from homeassistant.helpers.service import async_get_all_descriptions, get_config_entry
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import ATTR_CONFIG_ENTRY

from .const import DOMAIN
from .registers import REG_EPOCH_TIME


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Komfovent integration."""

    async def set_system_time(call: ServiceCall) -> None:
        """Service to set system time on the Komfovent unit."""
        entry = get_config_entry(hass, call.data[ATTR_CONFIG_ENTRY])
        coordinator = hass.data[DOMAIN][entry.entry_id]
        
        # Get local timezone
        local_tz = zoneinfo.ZoneInfo(str(hass.config.time_zone))
        # Get current time in local timezone
        local_time = datetime.now(local_tz)
        # Get local epoch (seconds since 1970-01-01 00:00:00 in local timezone)
        local_epoch = int((local_time - datetime(1970, 1, 1, tzinfo=local_tz)).total_seconds())
        await coordinator.client.write_register(REG_EPOCH_TIME, local_epoch)

    hass.services.async_register(DOMAIN, "set_system_time", set_system_time)
