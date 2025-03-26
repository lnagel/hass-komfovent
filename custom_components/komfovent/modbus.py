"""Modbus communication handler for Komfovent."""

import asyncio
import logging

from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient

from .registers import (
    REGISTERS_16BIT_SIGNED,
    REGISTERS_16BIT_UNSIGNED,
    REGISTERS_32BIT_UNSIGNED,
)

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

    async def read(self, register: int, count: int) -> dict[int, int]:
        """Read holding registers and return dict keyed by absolute register numbers."""
        async with self._lock:
            result = await self.client.read_holding_registers(
                address=register - 1, count=count, slave=1
            )

        if result.isError():
            msg = f"Error reading registers at {register}"
            raise ModbusException(msg)

        # Create dictionary with absolute register numbers as keys
        block = dict(enumerate(result.registers, start=register))
        converted = set()
        data = {}

        for reg, value in block.items():
            if reg in REGISTERS_16BIT_UNSIGNED:
                # For 16-bit unsigned registers, use value directly
                converted.add(reg)
                data[reg] = value
            elif reg in REGISTERS_16BIT_SIGNED:
                # For 16-bit signed registers, use need to convert uint16 to int16
                converted.add(reg)
                data[reg] = value - (value >> 15 << 16)
            elif reg in REGISTERS_32BIT_UNSIGNED:
                # For 32-bit registers, combine with next register
                if reg + 1 not in block:
                    raise ValueError(f"Register {reg + 1} value not retrieved")
                converted.add(reg)
                converted.add(reg + 1)
                data[reg] = (value << 16) + block[reg + 1]

        if not_converted := set(block.keys()) - converted:
            msg = (
                f"Registers {not_converted} not found in either "
                "16-bit or 32-bit register sets"
            )
            raise NotImplementedError(msg)

        return data

    async def write_register(self, register: int, value: int) -> None:
        """Write to holding register."""
        async with self._lock:
            if register in REGISTERS_16BIT_UNSIGNED:
                # Write unsigned value as-is
                result = await self.client.write_register(register - 1, value, slave=1)
            elif register in REGISTERS_16BIT_SIGNED:
                # Convert signed value to 16-bit unsigned for Modbus
                unsigned_value = value & 0xFFFF
                result = await self.client.write_register(
                    register - 1, unsigned_value, slave=1
                )
            elif register in REGISTERS_32BIT_UNSIGNED:
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
