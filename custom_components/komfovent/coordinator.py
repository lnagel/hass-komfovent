"""DataUpdateCoordinator for Komfovent."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.exceptions import ModbusException

from . import registers
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ConnectedPanels,
)


def process_register_block(block: dict[int, int]) -> dict[int, int]:
    """
    Process a block of register values handling 16/32 bit registers.

    Args:
        block: Dictionary of register values from read_registers

    Returns:
        Dictionary of processed register values

    """
    data = {}

    for reg, value in block.items():
        if reg in registers.REGISTERS_32BIT:
            # For 32-bit registers, combine with next register
            if reg + 1 in block:
                data[reg] = (value << 16) + block[reg + 1]
        elif reg in registers.REGISTERS_16BIT:
            # For 16-bit registers, use value directly
            data[reg] = value

    return data


_LOGGER = logging.getLogger(__name__)


class KomfoventCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Komfovent data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        **kwargs: Any,
    ) -> None:
        """Initialize."""
        from .modbus import KomfoventModbusClient  # easier to mock

        kwargs.setdefault("name", DOMAIN)
        kwargs.setdefault("update_interval", timedelta(seconds=DEFAULT_SCAN_INTERVAL))

        super().__init__(hass, _LOGGER, **kwargs)
        self.client = KomfoventModbusClient(host, port)

    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        connected = await self.client.connect()

        if not connected:
            _LOGGER.error("Failed to connect")
            return False

        return True

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Komfovent."""
        data = {}

        try:
            # Read basic control block (1-34)
            basic_control = await self.client.read_registers(registers.REG_POWER, 34)
            data.update(process_register_block(basic_control))

            # Read modes (100-156)
            modes_block = await self.client.read_registers(
                registers.REG_AWAY_FAN_SUPPLY, 57
            )
            data.update(process_register_block(modes_block))

            # Read Eco and air quality blocks (200-214)
            eco_auto_block = await self.client.read_registers(
                registers.REG_ECO_MIN_TEMP, 15
            )
            data.update(process_register_block(eco_auto_block))

            # Read active alarms block (600-610)
            alarms_block = await self.client.read_registers(
                registers.REG_ACTIVE_ALARMS_COUNT, 11
            )
            data.update(process_register_block(alarms_block))

            # Read sensor block (900-956)
            sensor_block = await self.client.read_registers(registers.REG_STATUS, 57)
            data.update(process_register_block(sensor_block))

            # Read digital outputs block (958-960)

            # Read exhaust temperature block (961)

            # Read controller firmware version (1000-1001)
            try:
                firmware_block = await self.client.read_registers(
                    registers.REG_FIRMWARE, 2
                )
                data.update(process_register_block(firmware_block))
            except (ConnectionError, ModbusException) as error:
                _LOGGER.warning("Failed to read controller firmware version: %s", error)

            # Read panel 1 firmware version (1002-1003)
            if data.get(registers.REG_CONNECTED_PANELS, 0) in [
                ConnectedPanels.PANEL1,
                ConnectedPanels.BOTH,
            ]:
                try:
                    panel1_block = await self.client.read_registers(
                        registers.REG_PANEL1_FW, 2
                    )
                    data.update(process_register_block(panel1_block))
                except (ConnectionError, ModbusException) as error:
                    _LOGGER.warning(
                        "Failed to read panel 1 firmware version: %s", error
                    )

            # Read panel 2 firmware version (1004-1005)
            if data.get(registers.REG_CONNECTED_PANELS, 0) in [
                ConnectedPanels.PANEL2,
                ConnectedPanels.BOTH,
            ]:
                try:
                    panel2_block = await self.client.read_registers(
                        registers.REG_PANEL2_FW, 2
                    )
                    data.update(process_register_block(panel2_block))
                except (ConnectionError, ModbusException) as error:
                    _LOGGER.warning(
                        "Failed to read panel 2 firmware version: %s", error
                    )

        except (ConnectionError, ModbusException) as error:
            _LOGGER.warning("Error communicating with Komfovent: %s", error)
            raise UpdateFailed from error

        return data
