#!/usr/bin/env python3
"""Modbus TCP server simulating a Komfovent ventilation unit."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from pymodbus import ModbusDeviceIdentification
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusServerContext,
    ModbusSparseDataBlock,
)
from pymodbus.server import StartAsyncTcpServer

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


async def run_server(host: str, port: int, register_data: dict[str, list[int]]) -> None:
    """
    Start the Modbus TCP server.

    Args:
        host: Network interface to bind to
        port: TCP port to listen on
        register_data: Dictionary of register numbers and values

    """
    # Convert register data to Modbus block format
    block_values = {int(k): v for k, v in register_data.items()}

    # Initialize data storage
    holding_registers = ModbusSparseDataBlock(block_values)
    store = ModbusDeviceContext(hr=holding_registers)
    context = ModbusServerContext(devices=store, single=True)

    # Server identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = "Komfovent"
    identity.ProductCode = "C6"
    identity.ModelName = "Simulator"

    # Start server
    _LOGGER.info("Starting Modbus TCP server on %s:%d", host, port)
    await StartAsyncTcpServer(
        context=context,
        identity=identity,
        address=(host, port),
    )


def main() -> None:
    """Run the Modbus TCP server simulation."""
    parser = argparse.ArgumentParser(
        description="Modbus TCP server for Komfovent simulation"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Listen address")
    parser.add_argument("--port", type=int, default=502, help="Listen port")
    parser.add_argument(
        "--input", default="registers.json", help="Input JSON file with register values"
    )

    args = parser.parse_args()

    logging.getLogger("pymodbus.logging").setLevel(logging.DEBUG)

    try:
        # Load register values
        input_path = Path(args.input)
        with input_path.open() as f:
            register_data = json.load(f)

        # Run server
        asyncio.run(run_server(args.host, args.port, register_data))

    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        _LOGGER.exception("Failed to load register data")
        sys.exit(1)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Server error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
