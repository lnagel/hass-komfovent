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
    REG_AQ_SENSOR2_VALUE, REG_NEXT_MODE, REG_NEXT_MODE_TIME, REG_NEXT_MODE_WEEKDAY, REG_BEFORE_MODE_MASK,
    REG_TEMP_CONTROL, REG_FLOW_CONTROL, REG_HEATING_CONFIG, REG_WATER_TEMP, REG_HEAT_EXCHANGER, REG_WATER_HEATER,
    REG_WATER_COOLER, REG_DX_UNIT, REG_AIR_DAMPERS, REG_SUPPLY_PRESSURE, REG_EXTRACT_PRESSURE, REG_HEAT_EFFICIENCY,
    REG_ENERGY_SAVING, REG_SPI, REG_INDOOR_ABS_HUMIDITY, REG_PANEL1_TEMP, REG_PANEL1_RH, REG_PANEL2_TEMP, REG_PANEL2_RH,
    REG_ECO_MIN_TEMP,
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

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Komfovent."""
        try:
            data = {}
            
            # Read basic control block (0-11)
            basic_control = await self.client.read_holding_registers(REG_POWER, 12)
            data.update({
                "power": basic_control[REG_POWER],
                "auto_mode_control": basic_control[REG_AUTO_MODE_CONTROL],
                "eco_mode": basic_control[REG_ECO_MODE],
                "auto_mode": basic_control[REG_AUTO_MODE],
                "operation_mode": basic_control[REG_OPERATION_MODE],
                "scheduler_mode": basic_control[REG_SCHEDULER_MODE],
                "next_mode": basic_control[REG_NEXT_MODE],
                "next_mode_time": basic_control[REG_NEXT_MODE_TIME],
                "next_mode_weekday": basic_control[REG_NEXT_MODE_WEEKDAY],
                "before_mode_mask": basic_control[REG_BEFORE_MODE_MASK],
                "temp_control": basic_control[REG_TEMP_CONTROL],
                "flow_control": basic_control[REG_FLOW_CONTROL],
            })

            # Read Eco and air quality blocks (199-213)
            eco_auto_block = await self.client.read_holding_registers(REG_ECO_MIN_TEMP, 15)
            data.update({
                "aq_sensor1_type": eco_auto_block[REG_AQ_SENSOR1_TYPE],
                "aq_sensor2_type": eco_auto_block[REG_AQ_SENSOR2_TYPE],
            })

            # Read sensor block (899-955)
            sensor_block = await self.client.read_holding_registers(REG_STATUS, 57)
            data.update({
                "status": sensor_block[REG_STATUS],
                "heating_config": sensor_block[REG_HEATING_CONFIG],
                "supply_temp": sensor_block[REG_SUPPLY_TEMP],
                "extract_temp": sensor_block[REG_EXTRACT_TEMP],
                "outdoor_temp": sensor_block[REG_OUTDOOR_TEMP],
                "water_temp": sensor_block[REG_WATER_TEMP],
                "supply_flow": (sensor_block[REG_SUPPLY_FLOW] << 16) + sensor_block[REG_SUPPLY_FLOW + 1],
                "extract_flow": (sensor_block[REG_EXTRACT_FLOW] << 16) + sensor_block[REG_EXTRACT_FLOW + 1],
                "supply_fan_intensity": sensor_block[REG_SUPPLY_FAN_INTENSITY],
                "extract_fan_intensity": sensor_block[REG_EXTRACT_FAN_INTENSITY],
                "heat_exchanger": sensor_block[REG_HEAT_EXCHANGER],
                "electric_heater": sensor_block[REG_ELECTRIC_HEATER],
                "water_heater": sensor_block[REG_WATER_HEATER],
                "water_cooler": sensor_block[REG_WATER_COOLER],
                "dx_unit": sensor_block[REG_DX_UNIT],
                "filter_impurity": sensor_block[REG_FILTER_IMPURITY],
                "air_dampers": sensor_block[REG_AIR_DAMPERS],
                "supply_pressure": sensor_block[REG_SUPPLY_PRESSURE],
                "extract_pressure": sensor_block[REG_EXTRACT_PRESSURE],
                "power_consumption": sensor_block[REG_POWER_CONSUMPTION],
                "heater_power": sensor_block[REG_HEATER_POWER],
                "heat_recovery": sensor_block[REG_HEAT_RECOVERY],
                "heat_efficiency": sensor_block[REG_HEAT_EFFICIENCY],
                "energy_saving": sensor_block[REG_ENERGY_SAVING],
                "spi": sensor_block[REG_SPI],
            })

            # Read panel values
            panel_block = await self.client.read_holding_registers(REG_PANEL1_TEMP, 11)
            data.update({
                "panel1_temp": panel_block[REG_PANEL1_TEMP],
                "panel1_rh": panel_block[REG_PANEL1_RH],
                "panel2_temp": panel_block[REG_PANEL2_TEMP],
                "panel2_rh": panel_block[REG_PANEL2_RH],
                "aq_sensor1_value": panel_block[REG_AQ_SENSOR1_VALUE],
                "aq_sensor2_value": panel_block[REG_AQ_SENSOR2_VALUE],
                "indoor_abs_humidity": panel_block[REG_INDOOR_ABS_HUMIDITY],
            })

            return data

        except Exception as error:
            _LOGGER.error("Error communicating with Komfovent: %s", error)
            raise ConfigEntryNotReady from error
