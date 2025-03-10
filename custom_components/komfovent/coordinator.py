"""DataUpdateCoordinator for Komfovent."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import registers
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .modbus import KomfoventModbusClient


def process_register_block(block: dict[int, int]) -> dict[int, int]:
    """
    Process a block of register values handling 16/32 bit registers.

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Komfovent."""
        try:
            data = {}

            # Read basic control block (0-33)
            basic_control = await self.client.read_holding_registers(
                registers.REG_POWER, 34
            )
            data.update(process_register_block(basic_control))

            # Read modes (99-155)
            modes_block = await self.client.read_holding_registers(
                registers.REG_AWAY_FAN_SUPPLY, 57
            )
            data.update(process_register_block(modes_block))

            # Read Eco and air quality blocks (199-213)
            eco_auto_block = await self.client.read_holding_registers(
                registers.REG_ECO_MIN_TEMP, 15
            )
            data.update(process_register_block(eco_auto_block))

            # Read active alarms block (599-609)
            alarms_block = await self.client.read_holding_registers(
                registers.REG_ACTIVE_ALARMS_COUNT, 11
            )
            data.update(process_register_block(alarms_block))

            # Read sensor block (899-955)
            sensor_block = await self.client.read_holding_registers(
                registers.REG_STATUS, 57
            )
            data.update(process_register_block(sensor_block))

            # Read firmware version
            firmware_block = await self.client.read_holding_registers(
                registers.REG_FIRMWARE, 6
            )
            data.update(process_register_block(firmware_block))

            return data

        except Exception as error:
            _LOGGER.error("Error communicating with Komfovent: %s", error)
            raise ConfigEntryNotReady from error
