"""Modbus communication handler for Komfovent."""

import asyncio
import logging

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
        return await self.client.connect()

    async def close(self) -> None:
        """Close the Modbus connection."""
        self.client.close()

    async def read_holding_registers(self, register: int, count: int) -> dict[int, int]:
        """Read holding registers and return dict keyed by absolute register numbers."""
        async with self._lock:
            result = await self.client.read_holding_registers(
                address=register - 1, count=count, slave=1
            )

        if result.isError():
            msg = f"Error reading registers at {register}"
            raise ModbusException(msg)

        # Create dictionary with absolute register numbers as keys
        return dict(enumerate(result.registers, start=register))

    async def write_register(self, register: int, value: int) -> None:
        """Write to holding register."""
        async with self._lock:
            if register in REGISTERS_16BIT:
                result = await self.client.write_register(register, value, slave=1)
            elif register in REGISTERS_32BIT:
                # Split 32-bit value into two 16-bit values
                high_word = (value >> 16) & 0xFFFF
                low_word = value & 0xFFFF

                # Write both words in a single transaction
                result = await self.client.write_registers(
                    address=register - 1, values=[high_word, low_word], slave=1
                )
            else:
                msg = (
                    f"Register {register} not found in either "
                    "16-bit or 32-bit register sets"
                )
                raise NotImplementedError(msg)

        if result.isError():
            msg = f"Error writing register at {register}"
            raise ModbusException(msg)
