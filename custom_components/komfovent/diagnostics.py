"""Diagnostics support for Komfovent."""

from __future__ import annotations

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
    (1, 34),  # primary control block 1-34
    (100, 57),  # modes 100-156
    (200, 17),  # eco and air quality 200-216
    (217, 1),  # heat recovery control 217
    (300, 100),  # scheduler 300-555
    (400, 100),  # scheduler 400-555
    (500, 56),  # scheduler 500-555
    (600, 11),  # active alarms 600-610
    (611, 89),  # alarm history 611-699
    (700, 100),  # alarm history 700-799
    (800, 62),  # alarm history 800-861
    (900, 57),  # detailed information 900-956
    (958, 3),  # digital outputs 958-960
    (961, 1),  # exhaust temperature 961
    (1000, 2),  # controller firmware 1000-1001
    (1002, 2),  # panel 1 firmware 1002-1003
    (1004, 2),  # panel 2 firmware 1004-1005
    # reset settings 1050
    # clean filters calibration 1051
]
MOBILE_APP_RANGES = [
    (10803, 1),
    (5000, 47),
    (5200, 49),
    (5100, 65),
    (5600, 8),
    (6101, 21),
    (6000, 6),
    (5580, 11),
    (7002, 2),
    (5700, 65),
    (5765, 64),
    (5829, 64),
    (5893, 64),
    (5300, 125),
    (5425, 125),
]
UNKNOWN_RANGES = [
    (35, 10),  # unknown 35-44
    (157, 6),  # unknown 157-162
    (957, 1),  # unknown 957
]
RANGES = INTEGRATION_RANGES + MOBILE_APP_RANGES + UNKNOWN_RANGES


async def dump_registers(host: str, port: int) -> dict[int, list[int]]:
    """
    Query all holding registers one by one and return values as dictionary.

    Args:
        host: Modbus TCP host address
        port: Modbus TCP port number

    Returns:
        Dictionary mapping register numbers to list of register values

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
        for start, count in RANGES:
            try:
                response = await client.read_holding_registers(
                    address=start - 1, count=count
                )
                results[start] = response.registers
                logger.info("Register %d: %s", start, response.registers)
            except ModbusException:
                logger.error("Register %d: Modbus error", start)  # noqa: TRY400

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
