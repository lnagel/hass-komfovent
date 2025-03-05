#!/usr/bin/env python3
"""Tool to dump Modbus TCP registers from Komfovent devices to JSON."""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
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
    (999, 6),  # firmware 999-1004
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


def dump_registers(host: str, port: int) -> dict[int, list[int]]:
    """Query all holding registers one by one and return values as dictionary.
    
    Args:
        host: Modbus TCP host address
        port: Modbus TCP port number
        
    Returns:
        Dictionary mapping register addresses to list of register values
        
    Raises:
        ConnectionError: If connection to device fails
        ModbusException: If there is an error reading registers
    """
    client = ModbusTcpClient(host=host, port=port)

    error_msg = f"Failed to connect to {host}:{port}"
    if not client.connect():
        raise ConnectionError(error_msg)

    results: dict[int, list[int]] = {}
    try:
        for address, count in RANGES:
            try:
                # Try reading single register first
                response = client.read_holding_registers(address=address, count=count)

                results[address] = response.registers
                logger.info("Register %d: %s", address, response.registers)

                # Small delay to avoid overwhelming the device
                time.sleep(0.1)

            except ModbusException as e:
                logger.error("Register %d: Modbus error - %s", address, e)

    finally:
        client.close()

    return results


def main() -> None:
    """Run the Modbus register dump tool."""
    parser = argparse.ArgumentParser(description="Dump Modbus TCP registers to JSON")
    parser.add_argument("--host", required=True, help="Modbus TCP host")
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port")
    parser.add_argument("--output", default="registers.json", help="Output JSON file")

    args = parser.parse_args()

    try:
        logger.info("Connecting to %s:%d...", args.host, args.port)
        logger.info("Starting register scan (this may take a few minutes)...")
        registers = dump_registers(args.host, args.port)

        output_path = Path(args.output)
        with output_path.open("w") as f:
            json.dump(registers, f, indent=2)

        logger.info("Successfully dumped %d registers to %s", len(registers), args.output)

    except (ConnectionError, ModbusException) as e:
        logger.error("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
