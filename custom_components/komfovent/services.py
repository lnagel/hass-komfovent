"""Services for Komfovent integration."""
import zoneinfo
from datetime import datetime
from typing import Final

from homeassistant.core import HomeAssistant, ServiceCall

from . import KomfoventCoordinator
from .const import DOMAIN
from .registers import REG_EPOCH_TIME

ATTR_CONFIG_ENTRY: Final = "config_entry"

async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Komfovent integration."""

    async def set_system_time(call: ServiceCall) -> None:
        """Service to set system time on the Komfovent unit."""
        coordinator: KomfoventCoordinator = hass.data[DOMAIN][call.data[ATTR_CONFIG_ENTRY]]

        # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
        local_tz = zoneinfo.ZoneInfo(str(hass.config.time_zone))
        local_epoch = datetime(1970, 1, 1, tzinfo=local_tz)

        # Calculate local time as seconds since local epoch
        local_time = int((datetime.now(tz=local_tz) - local_epoch).total_seconds())

        # Write local time to the Komfovent unit
        await coordinator.client.write_register(REG_EPOCH_TIME, local_time)

    hass.services.async_register(DOMAIN, "set_system_time", set_system_time)
