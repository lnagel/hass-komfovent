"""Diagnostics support for Komfovent."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_HOST, CONF_PORT
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .coordinator import KomfoventCoordinator

logger = logging.getLogger(__name__)


INTEGRATION_RANGES = [
    (0, 34),  # primary control block 0-33
    (99, 57),  # modes 99-155
    (199, 15),  # eco and air quality 199-213
    (299, 100),  # scheduler 299-554
    (399, 100),  # scheduler 299-554
    (499, 56),  # scheduler 299-554
    (599, 11),  # active alarms 599-609
    (610, 89),  # alarm history 610-868
    (699, 100),  # alarm history 610-868
    (799, 62),  # alarm history 610-860
    (899, 57),  # detailed information 899-955
    (999, 2),  # controller firmware 999-1000
    (1001, 2),  # panel 1 firmware 1001-1002
    (1003, 2),  # panel 2 firmware 1003-1004
    # reset settings 1049
]
MOBILE_APP_RANGES = [
    (10802, 1),
    (4999, 47),
    (5199, 49),
    (5099, 65),
    (5599, 8),
    (6100, 21),
    (5999, 6),
    (5579, 11),
    (7001, 2),
    (5699, 65),
    (5764, 64),
    (5828, 64),
    (5892, 64),
    (5299, 125),
    (5424, 125),
]
RANGES = INTEGRATION_RANGES + MOBILE_APP_RANGES


async def dump_registers(host: str, port: int) -> dict[int, list[int]]:
    """
    Query all holding registers one by one and return values as dictionary.

    Args:
        host: Modbus TCP host address
        port: Modbus TCP port number

    Returns:
        Dictionary mapping register addresses to list of register values

    Raises:
        ConnectionError: If connection to device fails
        ModbusException: If there is an error reading registers

    """
    client = AsyncModbusTcpClient(host=host, port=port)

    error_msg = f"Failed to connect to {host}:{port}"
    if not await client.connect():
        raise ConnectionError(error_msg)

    results: dict[int, list[int]] = {}
    try:
        for address, count in RANGES:
            try:
                response = await client.read_holding_registers(
                    address=address, count=count
                )
                results[address] = response.registers
                logger.info("Register %d: %s", address, response.registers)
            except ModbusException:
                logger.error("Register %d: Modbus error", address)  # noqa: TRY400

            await asyncio.sleep(0.1)

    finally:
        client.close()

    return results


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    try:
        registers = await dump_registers(host, port)
    except (ConnectionError, ModbusException):
        logger.exception("Failed to dump registers")
        registers = {}

    return {
        "config_entry": entry.as_dict(),
        "registers": registers,
        "coordinator_data": coordinator.data,
    }
