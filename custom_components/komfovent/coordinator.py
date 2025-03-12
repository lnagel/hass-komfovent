"""DataUpdateCoordinator for Komfovent."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.exceptions import ModbusException

from . import registers
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ConnectedPanels,
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

STATIC_DATA_ADDRESSES = {
    registers.REG_CONNECTED_PANELS,
    registers.REG_FIRMWARE,
    registers.REG_PANEL1_FW,
    registers.REG_PANEL2_FW,
}


class KomfoventCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Komfovent data."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
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
        await self.client.connect()

        data = {}

        # Read connected panels
        try:
            connected_panels_block = await self.client.read_holding_registers(
                registers.REG_CONNECTED_PANELS, 1
            )
            data.update(process_register_block(connected_panels_block))
        except (ConnectionError, ModbusException) as error:
            _LOGGER.warning("Failed to read connected panels: %s", error)
            raise ConfigEntryNotReady from error

        # Read controller firmware version
        try:
            firmware_block = await self.client.read_holding_registers(
                registers.REG_FIRMWARE, 2
            )
            data.update(process_register_block(firmware_block))
        except (ConnectionError, ModbusException) as error:
            _LOGGER.warning("Failed to read controller firmware version: %s", error)
            # raise ConfigEntryNotReady from error

        # Read panel 1 firmware version
        if data.get(registers.REG_CONNECTED_PANELS, 0) in [
            ConnectedPanels.PANEL1,
            ConnectedPanels.BOTH,
        ]:
            try:
                panel1_block = await self.client.read_holding_registers(
                    registers.REG_PANEL1_FW, 2
                )
                data.update(process_register_block(panel1_block))
            except (ConnectionError, ModbusException) as error:
                _LOGGER.warning("Failed to read panel 1 firmware version: %s", error)
                # raise ConfigEntryNotReady from error

        # Read panel 2 firmware version
        if data.get(registers.REG_CONNECTED_PANELS, 0) in [
            ConnectedPanels.PANEL2,
            ConnectedPanels.BOTH,
        ]:
            try:
                panel2_block = await self.client.read_holding_registers(
                    registers.REG_PANEL2_FW, 2
                )
                data.update(process_register_block(panel2_block))
            except (ConnectionError, ModbusException) as error:
                _LOGGER.warning("Failed to read panel 2 firmware version: %s", error)
                # raise ConfigEntryNotReady from error

        self.data = data

        return True

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Komfovent."""
        data = {}

        for address in STATIC_DATA_ADDRESSES:
            if self.data and address in self.data:
                data[address] = self.data[address]

        try:
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

        except Exception as error:
            _LOGGER.warning("Error communicating with Komfovent: %s", error)
            raise UpdateFailed from error

        return data
