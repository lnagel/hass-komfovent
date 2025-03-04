"""DataUpdateCoordinator for Komfovent."""
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.components.modbus import ModbusHub
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.modbus import ModbusHub
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    REG_POWER,
    REG_ECO_MODE,
    REG_AUTO_MODE,
    REG_OPERATION_MODE,
    REG_SCHEDULER_MODE,
    REG_NORMAL_SETPOINT,
    REG_SUPPLY_TEMP,
    REG_EXTRACT_TEMP,
    REG_OUTDOOR_TEMP,
    REG_SUPPLY_FLOW,
    REG_EXTRACT_FLOW,
    REG_SUPPLY_FAN_INTENSITY,
    REG_EXTRACT_FAN_INTENSITY,
    REG_ELECTRIC_HEATER,
    REG_FILTER_IMPURITY,
    REG_POWER_CONSUMPTION,
    REG_HEATER_POWER,
    REG_HEAT_RECOVERY,
)

_LOGGER = logging.getLogger(__name__)

async def read_32bit_register(hub: ModbusHub, register: int) -> int:
    """Read a 32-bit value from two consecutive 16-bit registers."""
    regs = await hub.async_read_holding_registers(register, 2)
    return (regs[0] << 16) + regs[1]

class KomfoventCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Komfovent data."""

    def __init__(self, hass: HomeAssistant, hub: ModbusHub):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.hub = hub

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Komfovent."""
        try:
            data = {}
            
            # Basic status
            data["power"] = await self.hub.async_read_holding_registers(REG_POWER, 1)
            data["eco_mode"] = await self.hub.async_read_holding_registers(REG_ECO_MODE, 1)
            data["auto_mode"] = await self.hub.async_read_holding_registers(REG_AUTO_MODE, 1)
            data["operation_mode"] = await self.hub.async_read_holding_registers(REG_OPERATION_MODE, 1)
            data["scheduler_mode"] = await self.hub.async_read_holding_registers(REG_SCHEDULER_MODE, 1)
            
            # Temperature readings
            data["setpoint"] = await self.hub.async_read_holding_registers(REG_NORMAL_SETPOINT, 1)
            data["supply_temp"] = await self.hub.async_read_holding_registers(REG_SUPPLY_TEMP, 1)
            data["extract_temp"] = await self.hub.async_read_holding_registers(REG_EXTRACT_TEMP, 1)
            data["outdoor_temp"] = await self.hub.async_read_holding_registers(REG_OUTDOOR_TEMP, 1)
            
            # Flow and fan data
            data["supply_flow"] = await read_32bit_register(self.hub, REG_SUPPLY_FLOW)
            data["extract_flow"] = await read_32bit_register(self.hub, REG_EXTRACT_FLOW)
            data["supply_fan_intensity"] = await self.hub.async_read_holding_registers(REG_SUPPLY_FAN_INTENSITY, 1)
            data["extract_fan_intensity"] = await self.hub.async_read_holding_registers(REG_EXTRACT_FAN_INTENSITY, 1)
            
            # Power and efficiency data
            data["electric_heater"] = await self.hub.async_read_holding_registers(REG_ELECTRIC_HEATER, 1)
            data["filter_impurity"] = await self.hub.async_read_holding_registers(REG_FILTER_IMPURITY, 1)
            data["power_consumption"] = await self.hub.async_read_holding_registers(REG_POWER_CONSUMPTION, 1)
            data["heater_power"] = await self.hub.async_read_holding_registers(REG_HEATER_POWER, 1)
            data["heat_recovery"] = await self.hub.async_read_holding_registers(REG_HEAT_RECOVERY, 1)

            return data

        except Exception as error:
            _LOGGER.error("Error communicating with Komfovent: %s", error)
            raise ConfigEntryNotReady from error
