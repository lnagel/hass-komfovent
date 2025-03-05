"""DataUpdateCoordinator for Komfovent."""
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryNotReady

from .modbus import KomfoventModbusClient
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    REG_POWER,
    REG_AUTO_MODE_CONTROL,
    REG_ECO_MODE,
    REG_AUTO_MODE,
    REG_OPERATION_MODE,
    REG_SCHEDULER_MODE,
    REG_STATUS,
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
    REG_AQ_SENSOR1_TYPE,
    REG_AQ_SENSOR2_TYPE,
    REG_AQ_SENSOR1_VALUE,
    REG_AQ_SENSOR2_VALUE,
)

_LOGGER = logging.getLogger(__name__)

class KomfoventCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Komfovent data."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = KomfoventModbusClient(host, port)

    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        return await self.client.connect()

    def _extract_32bit_value(self, registers: list[int], offset: int) -> int:
        """Extract a 32-bit value from register list at given offset."""
        return (registers[offset] << 16) + registers[offset + 1]

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Komfovent."""
        try:
            data = {}
            
            # Read basic control block (0-9)
            basic_control = await self.client.read_holding_registers(REG_POWER, 10)
            data.update({
                "power": basic_control[0],
                "auto_mode_control": basic_control[1],
                "eco_mode": basic_control[2],
                "auto_mode": basic_control[3],
                "operation_mode": basic_control[4],
                "scheduler_mode": basic_control[5],
                "next_mode": basic_control[6],
                "next_mode_time": basic_control[7],
                "next_mode_weekday": basic_control[8],
                "before_mode_mask": basic_control[9],
            })

            # Read sensor block (899-955)
            sensor_block = await self.client.read_holding_registers(REG_STATUS, 57)
            
            data.update({
                "status": sensor_block[0],
                "heating_config": sensor_block[1],
                "supply_temp": sensor_block[2],
                "extract_temp": sensor_block[3],
                "outdoor_temp": sensor_block[4],
                "water_temp": sensor_block[5],
            })
            
            # Handle 32-bit flow values
            data.update({
                "supply_flow": self._extract_32bit_value(sensor_block, 6),
                "extract_flow": self._extract_32bit_value(sensor_block, 8),
            })
            
            # Continue with remaining sensor values
            data.update({
                "supply_fan_intensity": sensor_block[10],
                "extract_fan_intensity": sensor_block[11],
                "heat_exchanger": sensor_block[12],
                "electric_heater": sensor_block[13],
                "water_heater": sensor_block[14],
                "water_cooler": sensor_block[15],
                "dx_unit": sensor_block[16],
                "filter_impurity": sensor_block[17],
                "air_dampers": sensor_block[18],
                "supply_pressure": sensor_block[19],
                "extract_pressure": sensor_block[20],
                "power_consumption": sensor_block[21],
                "heater_power": sensor_block[22],
                "heat_recovery": sensor_block[23],
                "heat_efficiency": sensor_block[24],
                "energy_saving": sensor_block[25],
                "spi": sensor_block[26],
            })

            # Handle AQ sensors at the end of the block
            data.update({
                "aq_sensor1_type": sensor_block[52],
                "aq_sensor2_type": sensor_block[53],
                "aq_sensor1_value": sensor_block[54],
                "aq_sensor2_value": sensor_block[55],
            })

            return data

        except Exception as error:
            _LOGGER.error("Error communicating with Komfovent: %s", error)
            raise ConfigEntryNotReady from error
