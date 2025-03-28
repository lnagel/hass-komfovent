"""Services for Komfovent integration."""

import logging
import zoneinfo
from datetime import datetime
from typing import Final

from homeassistant.core import HomeAssistant, ServiceCall

from . import KomfoventCoordinator, registers
from .const import DOMAIN, OperationMode

_LOGGER = logging.getLogger(__name__)

DEFAULT_MODE_TIMER = 60

ATTR_CONFIG_ENTRY: Final = "config_entry"


async def clean_filters_calibration(coordinator: KomfoventCoordinator) -> None:
    """Reset filters counter."""
    await coordinator.client.write(registers.REG_CLEAN_FILTERS, 1)


async def set_mode(coordinator: KomfoventCoordinator, mode: str) -> None:
    """Set operation mode on the Komfovent unit."""
    try:
        operation_mode = OperationMode[mode.upper()]
    except ValueError:
        _LOGGER.warning("Invalid operation mode: %s", mode)
        return

    if operation_mode == OperationMode.OFF:
        await coordinator.client.write(registers.REG_POWER, 0)
    elif operation_mode == OperationMode.AIR_QUALITY:
        await coordinator.client.write(registers.REG_AUTO_MODE, 1)
    elif operation_mode in {
        OperationMode.AWAY,
        OperationMode.NORMAL,
        OperationMode.INTENSIVE,
        OperationMode.BOOST,
    }:
        await coordinator.client.write(
            registers.REG_OPERATION_MODE, operation_mode.value
        )
    elif operation_mode == OperationMode.KITCHEN:
        await coordinator.client.write(
            registers.REG_KITCHEN_TIMER,
            coordinator.data.get(registers.REG_KITCHEN_TIMER) or DEFAULT_MODE_TIMER,
        )
    elif operation_mode == OperationMode.FIREPLACE:
        await coordinator.client.write(
            registers.REG_FIREPLACE_TIMER,
            coordinator.data.get(registers.REG_FIREPLACE_TIMER) or DEFAULT_MODE_TIMER,
        )
    elif operation_mode == OperationMode.OVERRIDE:
        await coordinator.client.write(
            registers.REG_OVERRIDE_TIMER,
            coordinator.data.get(registers.REG_OVERRIDE_TIMER) or DEFAULT_MODE_TIMER,
        )
    else:
        _LOGGER.warning("Unsupported operation mode: %s", mode)
        return

    await coordinator.async_request_refresh()


async def set_system_time(coordinator: KomfoventCoordinator) -> None:
    """Set system time on the Komfovent unit."""
    # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
    local_tz = zoneinfo.ZoneInfo(str(coordinator.hass.config.time_zone))
    local_epoch = datetime(1970, 1, 1, tzinfo=local_tz)

    # Calculate local time as seconds since local epoch
    local_time = int((datetime.now(tz=local_tz) - local_epoch).total_seconds())

    # Write local time to the Komfovent unit
    await coordinator.client.write(registers.REG_EPOCH_TIME, local_time)


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Komfovent integration."""

    async def handle_clean_filters_calibration(call: ServiceCall) -> None:
        """Handle the clean filters calibration service call."""
        coordinator: KomfoventCoordinator = hass.data[DOMAIN][
            call.data[ATTR_CONFIG_ENTRY]
        ]
        await clean_filters_calibration(coordinator)

    async def handle_set_mode(call: ServiceCall) -> None:
        """Handle the set mode service call."""
        coordinator: KomfoventCoordinator = hass.data[DOMAIN][
            call.data[ATTR_CONFIG_ENTRY]
        ]
        await set_mode(coordinator, call.data["mode"])

    async def handle_set_system_time(call: ServiceCall) -> None:
        """Handle the set system time service call."""
        coordinator: KomfoventCoordinator = hass.data[DOMAIN][
            call.data[ATTR_CONFIG_ENTRY]
        ]
        await set_system_time(coordinator)

    hass.services.async_register(
        DOMAIN, "clean_filters_calibration", handle_clean_filters_calibration
    )
    hass.services.async_register(DOMAIN, "set_mode", handle_set_mode)
    hass.services.async_register(DOMAIN, "set_system_time", handle_set_system_time)
