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
)
from . import registers

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

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Komfovent."""
        try:
            data = {}
            
            # Read basic control block (0-11)
            basic_control = await self.client.read_holding_registers(registers.REG_POWER, 12)
            data.update({
                "power": basic_control[registers.REG_POWER],
                "auto_mode_control": basic_control[registers.REG_AUTO_MODE_CONTROL],
                "eco_mode": basic_control[registers.REG_ECO_MODE],
                "auto_mode": basic_control[registers.REG_AUTO_MODE],
                "operation_mode": basic_control[registers.REG_OPERATION_MODE],
                "scheduler_mode": basic_control[registers.REG_SCHEDULER_MODE],
                "next_mode": basic_control[registers.REG_NEXT_MODE],
                "next_mode_time": basic_control[registers.REG_NEXT_MODE_TIME],
                "next_mode_weekday": basic_control[registers.REG_NEXT_MODE_WEEKDAY],
                "before_mode_mask": basic_control[registers.REG_BEFORE_MODE_MASK],
                "temp_control": basic_control[registers.REG_TEMP_CONTROL],
                "flow_control": basic_control[registers.REG_FLOW_CONTROL],
            })

            # Read Eco and air quality blocks (199-213)
            eco_auto_block = await self.client.read_holding_registers(registers.REG_ECO_MIN_TEMP, 15)
            data.update({
                "aq_sensor1_type": eco_auto_block[registers.REG_AQ_SENSOR1_TYPE],
                "aq_sensor2_type": eco_auto_block[registers.REG_AQ_SENSOR2_TYPE],
            })

            # Read sensor block (899-955)
            sensor_block = await self.client.read_holding_registers(registers.REG_STATUS, 57)
            data.update({
                "status": sensor_block[registers.REG_STATUS],
                "heating_config": sensor_block[registers.REG_HEATING_CONFIG],
                "supply_temp": sensor_block[registers.REG_SUPPLY_TEMP],
                "extract_temp": sensor_block[registers.REG_EXTRACT_TEMP],
                "outdoor_temp": sensor_block[registers.REG_OUTDOOR_TEMP],
                "water_temp": sensor_block[registers.REG_WATER_TEMP],
                "supply_flow": (sensor_block[registers.REG_SUPPLY_FLOW] << 16) + sensor_block[registers.REG_SUPPLY_FLOW + 1],
                "extract_flow": (sensor_block[registers.REG_EXTRACT_FLOW] << 16) + sensor_block[registers.REG_EXTRACT_FLOW + 1],
                "supply_fan_intensity": sensor_block[registers.REG_SUPPLY_FAN_INTENSITY],
                "extract_fan_intensity": sensor_block[registers.REG_EXTRACT_FAN_INTENSITY],
                "heat_exchanger": sensor_block[registers.REG_HEAT_EXCHANGER],
                "electric_heater": sensor_block[registers.REG_ELECTRIC_HEATER],
                "water_heater": sensor_block[registers.REG_WATER_HEATER],
                "water_cooler": sensor_block[registers.REG_WATER_COOLER],
                "dx_unit": sensor_block[registers.REG_DX_UNIT],
                "filter_impurity": sensor_block[registers.REG_FILTER_IMPURITY],
                "air_dampers": sensor_block[registers.REG_AIR_DAMPERS],
                "supply_pressure": sensor_block[registers.REG_SUPPLY_PRESSURE],
                "extract_pressure": sensor_block[registers.REG_EXTRACT_PRESSURE],
                "power_consumption": sensor_block[registers.REG_POWER_CONSUMPTION],
                "heater_power": sensor_block[registers.REG_HEATER_POWER],
                "heat_recovery": sensor_block[registers.REG_HEAT_RECOVERY],
                "heat_efficiency": sensor_block[registers.REG_HEAT_EFFICIENCY],
                "energy_saving": sensor_block[registers.REG_ENERGY_SAVING],
                "spi": sensor_block[registers.REG_SPI],
            })

            # Read panel values
            panel_block = await self.client.read_holding_registers(registers.REG_PANEL1_TEMP, 11)
            data.update({
                "panel1_temp": panel_block[registers.REG_PANEL1_TEMP],
                "panel1_rh": panel_block[registers.REG_PANEL1_RH],
                "panel2_temp": panel_block[registers.REG_PANEL2_TEMP],
                "panel2_rh": panel_block[registers.REG_PANEL2_RH],
                "aq_sensor1_value": panel_block[registers.REG_AQ_SENSOR1_VALUE],
                "aq_sensor2_value": panel_block[registers.REG_AQ_SENSOR2_VALUE],
                "indoor_abs_humidity": panel_block[registers.REG_INDOOR_ABS_HUMIDITY],
            })

            return data

        except Exception as error:
            _LOGGER.error("Error communicating with Komfovent: %s", error)
            raise ConfigEntryNotReady from error
