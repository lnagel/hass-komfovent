#!/usr/bin/env python3
"""Tool to dump Modbus TCP registers from Komfovent devices to JSON."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from pymodbus.exceptions import ModbusException

from custom_components.komfovent.diagnostics import dump_registers

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


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
        registers = asyncio.run(dump_registers(args.host, args.port))

        output_path = Path(args.output)
        with output_path.open("w") as f:
            json.dump(registers, f, indent=2)

        logger.info(
            "Successfully dumped %d registers to %s", len(registers), args.output
        )

    except (ConnectionError, ModbusException):
        logger.exception("Error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
