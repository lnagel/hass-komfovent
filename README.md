# Komfovent integration for Home Assistant

A Home Assistant integration that connects to Komfovent devices through Modbus TCP.

## Installation

1. Add this repository to HACS or copy the `custom_components/komfovent` folder to your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Add the integration through the Home Assistant UI.
4. Configure the integration with the IP address of your Komfovent device.

## Device support

Currently only the Komfovent C6/C6M devices are supported, however due to the large variety of configurations,
not every combination has been tested yet. Support for Komfovent C8 devices could easily be added, but I don't
have access to one for testing. Since the C8 register layout is extremely similar to the C6, it might work out
of the box.

If you have issues seeing the data correctly, then please open a new ticket with:

- the model of your device, controller type and firmware version
- a data dump taken with the `modbus_dump.py` tool
- screenshots of the data in the Komfovent app or web interface

## Configuration

The integration can be configured through the Home Assistant UI. The following options are available:

- **name**: The name of your Komfovent device
- **Host**: The IP address of your Komfovent device
- **Port**: The Modbus TCP port (default: 502)

## Services

The integration provides several services that can be called from Home Assistant actions:

### Clean Filters Calibration
Calibrates the clean filters on the Komfovent unit after filter replacement:

```yaml
# Example service call
action: komfovent.clean_filters_calibration
target:
  device_id: YOUR_DEVICE_ID
```

### Set Operation Mode 
Sets the operation mode of the Komfovent unit:

```yaml
# Example service call
action: komfovent.set_operation_mode
target:
  device_id: YOUR_DEVICE_ID
data:
  mode: kitchen
  minutes: 60
```

Available modes:
- `off`: Turn off the unit
- `air_quality`: Enable automatic air quality control
- `away`: Low-intensity ventilation for when you're away
- `normal`: Standard ventilation mode
- `intensive`: Increased ventilation
- `boost`: Maximum ventilation
- `kitchen`: Temporary increased ventilation for cooking
- `fireplace`: Special mode for fireplace operation
- `override`: Override current schedule

The `minutes` parameter (1-300) is only used for `kitchen`, `fireplace`, and `override` modes.

```yaml
# Example action in a button card
show_name: true
show_icon: true
type: button
entity: select.komfovent_current_mode
name: Kitchen
icon: mdi:stove
show_state: false
tap_action:
  action: perform-action
  perform_action: komfovent.set_operation_mode
  target:
    device_id: YOUR_DEVICE_ID
  data:
    mode: kitchen
    minutes: 5
```

### Set System Time
Sets the system time on the Komfovent unit to match the local time:

```yaml
# Example service call
action: komfovent.set_system_time
target:
  device_id: YOUR_DEVICE_ID
```

## ModBus tools

The `modbus_dump.py` tool can be used to dump the ModBus data from the Komfovent device. Usage:

```bash
python3 modbus_dump.py --host <device_ip> [--port 502] [--output registers.json]
```

This will scan all known register ranges and save the results to a JSON file. The tool supports these arguments:
- `--host`: Required. IP address of your Komfovent device
- `--port`: Optional. ModBus TCP port (default: 502)
- `--output`: Optional. Output JSON file path (default: registers.json)

The `modbus_server.py` tool can be used to simulate a Komfovent ModBus server for testing purposes. Usage:

```bash
python3 modbus_server.py [--host 0.0.0.0] [--port 502] [--input registers.json]
```

This will start a ModBus TCP server that simulates a Komfovent device using register values from a JSON file. The tool supports these arguments:
- `--host`: Optional. Network interface to listen on (default: 0.0.0.0)
- `--port`: Optional. ModBus TCP port to listen on (default: 502)
- `--input`: Optional. Input JSON file with register values (default: registers.json)

You can use this tool for development and testing without needing a physical device. First dump the registers from a real device, then use that JSON file to run the simulator.

## Repository Overview

This repository contains multiple files, here is an overview:

| File                            | Purpose                                                                                                                | Documentation                                                                                                                  |
|---------------------------------|------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `.devcontainer.json`            | Used for development/testing with Visual Studio Code.                                                                  | [Documentation](https://code.visualstudio.com/docs/remote/containers)                                                          |
| `.github/ISSUE_TEMPLATE/*.yml`  | Templates for the issue tracker                                                                                        | [Documentation](https://help.github.com/en/github/building-a-strong-community/configuring-issue-templates-for-your-repository) |
| `custom_components/komfovent/*` | Integration files, this is where everything happens.                                                                   | [Documentation](https://developers.home-assistant.io/docs/creating_component_index)                                            |
| `CONTRIBUTING.md`               | Guidelines on how to contribute.                                                                                       | [Documentation](https://help.github.com/en/github/building-a-strong-community/setting-guidelines-for-repository-contributors)  |
| `LICENSE`                       | The license file for the project.                                                                                      | [Documentation](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/licensing-a-repository)          |
| `README.md`                     | The file you are reading now, should contain info about the integration, installation, and configuration instructions. | [Documentation](https://help.github.com/en/github/writing-on-github/basic-writing-and-formatting-syntax)                       |
| `requirements.txt`              | Python packages used for development/lint/testing this integration.                                                    | [Documentation](https://pip.pypa.io/en/stable/user_guide/#requirements-files)                                                  |

## Next steps

These are some next steps you may want to look into:
- Add tests to your integration, [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) can help you get started.
- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).
