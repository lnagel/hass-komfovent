#!/usr/bin/env python3

import argparse
import json
import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

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


def dump_registers(host: str, port: int) -> dict:
    """Query all holding registers one by one and return values as dictionary."""
    client = ModbusTcpClient(host=host, port=port)

    if not client.connect():
        raise ConnectionError(f"Failed to connect to {host}:{port}")

    results = {}
    try:
        for address, count in RANGES:
            try:
                # Try reading single register first
                response = client.read_holding_registers(address=address, count=count)

                results[address] = response.registers
                print(f"Register {address}: {response.registers}")

                # Small delay to avoid overwhelming the device
                time.sleep(0.1)

            except ModbusException as e:
                print(f"Register {address}: Modbus error - {e}")
            except Exception as e:
                print(f"Register {address}: Unexpected error - {e}")

    finally:
        client.close()

    return results


def main():
    parser = argparse.ArgumentParser(description="Dump Modbus TCP registers to JSON")
    parser.add_argument("--host", required=True, help="Modbus TCP host")
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port")
    parser.add_argument("--output", default="registers.json", help="Output JSON file")

    args = parser.parse_args()

    try:
        print(f"Connecting to {args.host}:{args.port}...")
        print("Starting register scan (this may take a few minutes)...")
        registers = dump_registers(args.host, args.port)

        with open(args.output, "w") as f:
            json.dump(registers, f, indent=2)

        print(f"Successfully dumped {len(registers)} registers to {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
