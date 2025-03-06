"""Services for Komfovent integration."""
from datetime import datetime
import zoneinfo

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .registers import REG_EPOCH_TIME


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Komfovent integration."""

    async def set_system_time(call: ServiceCall) -> None:
        """Service to set system time on the Komfovent unit."""
        # Get the coordinator from the first config entry
        entry_id = list(hass.data[DOMAIN].keys())[0]
        coordinator = hass.data[DOMAIN][entry_id]
        
        # Get local timezone
        local_tz = zoneinfo.ZoneInfo(str(hass.config.time_zone))
        # Get current time in local timezone
        local_time = datetime.now(local_tz)
        # Get local epoch (seconds since 1970-01-01 00:00:00 in local timezone)
        local_epoch = int((local_time - datetime(1970, 1, 1, tzinfo=local_tz)).total_seconds())
        await coordinator.client.write_register(REG_EPOCH_TIME, local_epoch)

    hass.services.async_register(DOMAIN, "set_system_time", set_system_time)
