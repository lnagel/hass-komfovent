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

def process_register_block(block: Dict[int, int]) -> Dict[int, int]:
    """Process a block of register values handling 16/32 bit registers.
    
    Args:
        block: Dictionary of register values from read_holding_registers
        start_address: Starting address of the block
        
    Returns:
        Dictionary of processed register values
    """
    data = {}
    
    for reg_address, value in block.items():
        if reg_address in registers.REGISTERS_32BIT:
            # For 32-bit registers, combine with next register
            if reg_address + 1 in block:
                data[reg_address] = (value << 16) + block[reg_address + 1]
        elif reg_address in registers.REGISTERS_16BIT:
            # For 16-bit registers, use value directly
            data[reg_address] = value
            
    return data

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
            data.update(process_register_block(basic_control))

            # Read Eco and air quality blocks (199-213)
            eco_auto_block = await self.client.read_holding_registers(registers.REG_ECO_MIN_TEMP, 15)
            data.update(process_register_block(eco_auto_block))

            # Read sensor block (899-955)
            sensor_block = await self.client.read_holding_registers(registers.REG_STATUS, 57)
            data.update(process_register_block(sensor_block))

            # Read panel values
            panel_block = await self.client.read_holding_registers(registers.REG_PANEL1_TEMP, 11)
            data.update(process_register_block(panel_block))

            return data

        except Exception as error:
            _LOGGER.error("Error communicating with Komfovent: %s", error)
            raise ConfigEntryNotReady from error
