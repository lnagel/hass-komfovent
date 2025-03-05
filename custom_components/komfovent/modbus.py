"""Modbus client for Komfovent."""
import logging
from typing import List

from homeassistant.components.modbus import ModbusHub
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

class KomfoventModbusClient:
    """Modbus client for Komfovent devices."""

    def __init__(self, host: str, port: int):
        """Initialize the Modbus client."""
        self.host = host
        self.port = port
        self.hub = None

    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        try:
            from homeassistant.components.modbus import get_hub
            conf = {
                "host": self.host,
                "port": self.port,
                "name": "Komfovent",
                "type": "tcp",
                "delay": 0,
                "timeout": 500
            }
            self.hub = ModbusHub(conf)
            return True
        except Exception as error:
            _LOGGER.error("Error connecting to Komfovent: %s", error)
            raise ConfigEntryNotReady from error

    async def read_holding_registers(self, address: int, count: int) -> List[int]:
        """Read holding registers."""
        if not self.hub:
            raise ConfigEntryNotReady("Modbus hub not initialized")
        result = await self.hub.async_read_holding_registers(address, count)
        if result is None:
            raise ConfigEntryNotReady("Failed to read registers")
        return result.registers
