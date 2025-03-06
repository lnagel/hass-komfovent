"""Modbus communication handler for Komfovent."""

import asyncio
import logging

from homeassistant.exceptions import ConfigEntryNotReady
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .registers import REGISTERS_16BIT, REGISTERS_32BIT

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
            reconnect_delay_max=60,
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

    async def read_holding_registers(self, address: int, count: int) -> dict[int, int]:
        """Read holding registers and return dict keyed by absolute register addresses."""
        async with self._lock:
            try:
                result = await self.client.read_holding_registers(
                    address, count=count, slave=1
                )
                if result.isError():
                    raise ModbusException(f"Error reading registers at {address}")

                # Create dictionary with absolute register addresses as keys
                return {address + i: value for i, value in enumerate(result.registers)}

            except Exception as error:
                _LOGGER.error("Failed to read registers at %s: %s", address, error)
                raise ConfigEntryNotReady from error

    async def write_register(self, address: int, value: int) -> None:
        """Write to holding register."""
        async with self._lock:
            try:
                if address in REGISTERS_32BIT:
                    # Split 32-bit value into two 16-bit values
                    high_word = (value >> 16) & 0xFFFF
                    low_word = value & 0xFFFF
                    
                    # Write high word first, then low word
                    result = await self.client.write_register(address, high_word, slave=1)
                    if result.isError():
                        raise ModbusException(f"Error writing high word at {address}")
                    
                    result = await self.client.write_register(address + 1, low_word, slave=1)
                    if result.isError():
                        raise ModbusException(f"Error writing low word at {address + 1}")
                
                elif address in REGISTERS_16BIT:
                    result = await self.client.write_register(address, value, slave=1)
                    if result.isError():
                        raise ModbusException(f"Error writing register at {address}")
                
                else:
                    raise ValueError(f"Register {address} not found in either 16-bit or 32-bit register sets")
                    
            except Exception as error:
                _LOGGER.error("Failed to write register at %s: %s", address, error)
                raise ConfigEntryNotReady from error
