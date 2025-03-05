#!/usr/bin/env python3

import argparse
import asyncio
import json
import logging

from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartAsyncTcpServer

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


async def run_server(host: str, port: int, registers: dict[str, int]):
    """Start the Modbus TCP server."""
    # Initialize data storage
    block = ModbusSparseDataBlock(registers)
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves=store, single=True)

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


def main():
    parser = argparse.ArgumentParser(
        description="Modbus TCP server for Komfovent simulation"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Listen address")
    parser.add_argument("--port", type=int, default=502, help="Listen port")
    parser.add_argument(
        "--input", default="registers.json", help="Input JSON file with register values"
    )

    args = parser.parse_args()

    logging.getLogger("pymodbus.logging").setLevel(logging.DEBUG)

    try:
        # Load register values
        with open(args.input) as f:
            register_data = json.load(f)
            registers = {int(k) + 1: v for k, v in register_data.items()}

        _LOGGER.info("Loaded %d registers from %s", len(registers), args.input)

        # Run server
        asyncio.run(run_server(args.host, args.port, registers))

    except Exception as e:
        _LOGGER.error("Error: %s", e)
        exit(1)


if __name__ == "__main__":
    main()
