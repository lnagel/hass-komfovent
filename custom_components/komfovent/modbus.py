"""Modbus communication handler for Komfovent."""
from typing import List
import asyncio
import logging

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

class KomfoventModbusClient:
    """Modbus client for Komfovent devices."""
    
    def __init__(self, host: str, port: int = 502) -> None:
        """Initialize the Modbus client."""
        self.client = AsyncModbusTcpClient(
            host=host,
            port=port,
            timeout=5,
            retries=3,
            reconnect_delay=5,
            reconnect_delay_max=60
        )
        self._lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        try:
            return await self.client.connect()
        except Exception as error:
            _LOGGER.error("Error connecting to Komfovent: %s", error)
            raise ConfigEntryNotReady from error

    async def close(self) -> None:
        """Close the Modbus connection."""
        self.client.close()
        
    async def read_holding_registers(self, address: int, count: int) -> List[int]:
        """Read holding registers."""
        async with self._lock:
            try:
                result = await self.client.read_holding_registers(address, count=count, slave=1)
                if result.isError():
                    raise ModbusException(f"Error reading registers at {address}")
                return result.registers
            except Exception as error:
                _LOGGER.error("Failed to read registers at %s: %s", address, error)
                raise ConfigEntryNotReady from error

    async def write_register(self, address: int, value: int) -> None:
        """Write to holding register."""
        async with self._lock:
            try:
                result = await self.client.write_register(address, value, slave=1)
                if result.isError():
                    raise ModbusException(f"Error writing register at {address}")
            except Exception as error:
                _LOGGER.error("Failed to write register at %s: %s", address, error)
                raise ConfigEntryNotReady from error
