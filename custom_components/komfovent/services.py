"""Services for Komfovent integration."""

import asyncio
import logging
import zoneinfo
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from . import KomfoventCoordinator, registers
from .const import DOMAIN, OperationMode

_LOGGER = logging.getLogger(__name__)

DEFAULT_MODE_TIMER = 60


def get_coordinator_for_device(
    hass: HomeAssistant, device_id: str
) -> KomfoventCoordinator | None:
    """Get the coordinator for a device ID."""
    device_registry = dr.async_get(hass)
    if (device_entry := device_registry.async_get(device_id)) is None:
        return None

    for entry_id in device_entry.config_entries:
        if coordinator := hass.data[DOMAIN].get(entry_id):
            return coordinator
    return None


async def clean_filters_calibration(coordinator: KomfoventCoordinator) -> None:
    """Reset filters counter."""
    await coordinator.client.write(registers.REG_CLEAN_FILTERS, 1)


async def set_operation_mode(
    coordinator: KomfoventCoordinator, mode: str, minutes: int | None = None
) -> None:
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
            minutes
            or coordinator.data.get(registers.REG_KITCHEN_TIMER)
            or DEFAULT_MODE_TIMER,
        )
    elif operation_mode == OperationMode.FIREPLACE:
        await coordinator.client.write(
            registers.REG_FIREPLACE_TIMER,
            minutes
            or coordinator.data.get(registers.REG_FIREPLACE_TIMER)
            or DEFAULT_MODE_TIMER,
        )
    elif operation_mode == OperationMode.OVERRIDE:
        await coordinator.client.write(
            registers.REG_OVERRIDE_TIMER,
            minutes
            or coordinator.data.get(registers.REG_OVERRIDE_TIMER)
            or DEFAULT_MODE_TIMER,
        )
    else:
        _LOGGER.warning("Unsupported operation mode: %s", mode)
        return

    # Wait a second for the command to be processed by the controller
    await asyncio.sleep(1.0)

    # Refresh the coordinator data to reflect the changes
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
        for device_id in call.data["device_id"]:
            if not (coordinator := get_coordinator_for_device(hass, device_id)):
                _LOGGER.error("Device %s not found", device_id)
                continue
            await clean_filters_calibration(coordinator)

    async def handle_set_operation_mode(call: ServiceCall) -> None:
        """Handle the set operation mode service call."""
        for device_id in call.data["device_id"]:
            if not (coordinator := get_coordinator_for_device(hass, device_id)):
                _LOGGER.error("Device %s not found", device_id)
                continue
            await set_operation_mode(
                coordinator, call.data["mode"], call.data.get("minutes")
            )

    async def handle_set_system_time(call: ServiceCall) -> None:
        """Handle the set system time service call."""
        for device_id in call.data["device_id"]:
            if not (coordinator := get_coordinator_for_device(hass, device_id)):
                _LOGGER.error("Device %s not found", device_id)
                continue
            await set_system_time(coordinator)

    hass.services.async_register(
        DOMAIN, "clean_filters_calibration", handle_clean_filters_calibration
    )
    hass.services.async_register(
        DOMAIN, "set_operation_mode", handle_set_operation_mode
    )
    hass.services.async_register(DOMAIN, "set_system_time", handle_set_system_time)
