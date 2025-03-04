#!/usr/bin/env python3

import argparse
import json
from pymodbus.client import ModbusTcpClient

def dump_registers(host: str, port: int) -> dict:
    """Query all holding registers and return values as dictionary."""
    client = ModbusTcpClient(host=host, port=port)
    
    if not client.connect():
        raise ConnectionError(f"Failed to connect to {host}:{port}")
    
    results = {}
    try:
        # Query registers in chunks of 100 to avoid timeout issues
        for start in range(0, 1024, 100):
            count = min(100, 1024 - start)
            response = client.read_holding_registers(address=start, count=count)
            
            if response.isError():
                print(f"Error reading registers {start}-{start+count}")
                continue
                
            for i, value in enumerate(response.registers):
                register_id = start + i
                results[register_id] = value
                
    finally:
        client.close()
        
    return results

def main():
    parser = argparse.ArgumentParser(description='Dump Modbus TCP registers to JSON')
    parser.add_argument('--host', default='10.20.2.60', help='Modbus TCP host')
    parser.add_argument('--port', type=int, default=502, help='Modbus TCP port')
    parser.add_argument('--output', default='registers.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    try:
        registers = dump_registers(args.host, args.port)
        
        with open(args.output, 'w') as f:
            json.dump(registers, f, indent=2)
            
        print(f"Successfully dumped {len(registers)} registers to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
