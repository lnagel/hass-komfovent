"""Services for Komfovent integration."""

import zoneinfo
from datetime import datetime
from typing import Final

from homeassistant.core import HomeAssistant, ServiceCall

from . import KomfoventCoordinator
from .const import DOMAIN
from .registers import REG_CLEAN_FILTERS, REG_EPOCH_TIME

ATTR_CONFIG_ENTRY: Final = "config_entry"


async def clean_filters_calibration(coordinator: KomfoventCoordinator) -> None:
    """Reset filters counter."""
    await coordinator.client.write_register(REG_CLEAN_FILTERS, 1)


async def set_system_time(coordinator: KomfoventCoordinator) -> None:
    """Set system time on the Komfovent unit."""
    # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
    local_tz = zoneinfo.ZoneInfo(str(coordinator.hass.config.time_zone))
    local_epoch = datetime(1970, 1, 1, tzinfo=local_tz)

    # Calculate local time as seconds since local epoch
    local_time = int((datetime.now(tz=local_tz) - local_epoch).total_seconds())

    # Write local time to the Komfovent unit
    await coordinator.client.write_register(REG_EPOCH_TIME, local_time)


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Komfovent integration."""

    async def handle_set_system_time(call: ServiceCall) -> None:
        """Handle the set system time service call."""
        coordinator: KomfoventCoordinator = hass.data[DOMAIN][
            call.data[ATTR_CONFIG_ENTRY]
        ]
        await set_system_time(coordinator)

    async def handle_clean_filters_calibration(call: ServiceCall) -> None:
        """Handle the clean filters calibration service call."""
        coordinator: KomfoventCoordinator = hass.data[DOMAIN][
            call.data[ATTR_CONFIG_ENTRY]
        ]
        await clean_filters_calibration(coordinator)

    hass.services.async_register(DOMAIN, "set_system_time", handle_set_system_time)
    hass.services.async_register(
        DOMAIN, "clean_filters_calibration", handle_clean_filters_calibration
    )
