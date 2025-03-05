#!/usr/bin/env python3

import argparse
import json
import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse


def dump_registers(host: str, port: int) -> dict:
    """Query all holding registers one by one and return values as dictionary."""
    client = ModbusTcpClient(host=host, port=port)

    if not client.connect():
        raise ConnectionError(f"Failed to connect to {host}:{port}")

    results = {}
    try:
        for register_id in range(0, 1024):
            try:
                # Try reading single register first
                response = client.read_holding_registers(address=register_id, count=1)

                if isinstance(response, ExceptionResponse):
                    # If failed, try reading two registers starting from previous address
                    if register_id > 0:
                        response = client.read_holding_registers(
                            address=register_id - 1, count=2
                        )
                        if isinstance(response, ExceptionResponse):
                            print(
                                f"Register {register_id}: Exception on both single and double read"
                            )
                            continue
                        if (
                            hasattr(response, "registers")
                            and len(response.registers) == 2
                        ):
                            # Take second value from the double read
                            value = response.registers[1]
                            results[register_id] = value
                            print(f"Register {register_id}: {value} (from double read)")
                            continue
                    print(f"Register {register_id}: Exception {response}")
                    continue

                if not hasattr(response, "registers") or not response.registers:
                    print(f"Register {register_id}: Invalid response")
                    continue

                # Normal single register read succeeded
                value = response.registers[0]
                results[register_id] = value
                print(f"Register {register_id}: {value} (direct read)")

                # Small delay to avoid overwhelming the device
                time.sleep(0.1)

            except ModbusException as e:
                print(f"Register {register_id}: Modbus error - {e}")
            except Exception as e:
                print(f"Register {register_id}: Unexpected error - {e}")

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
