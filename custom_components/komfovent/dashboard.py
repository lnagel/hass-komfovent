"""Dashboard for Komfovent integration."""

from homeassistant.components.lovelace.types import LovelaceConfig


async def async_get_dashboard() -> LovelaceConfig:
    """Get the Komfovent dashboard configuration."""
    return {
        "title": "Komfovent",
        "views": [
            {
                "title": "Main",
                "path": "main",
                "badges": [],
                "cards": [
                    {
                        "type": "vertical-stack",
                        "cards": [
                            {
                                "type": "horizontal-stack",
                                "cards": [
                                    {
                                        "type": "custom:button-card",
                                        "entity": "sensor.komfovent_operation_mode",
                                        "color": "grey",
                                        "tap_action": {
                                            "action": "call-service",
                                            "service": "modbus.write_register",
                                            "service_data": {
                                                "address": 4,
                                                "hub": "Komfovent",
                                                "unit": 1,
                                                "value": 1,
                                            },
                                        },
                                        "name": "Away",
                                        "icon": "mdi:home-export-outline",
                                        "state": {
                                            "value": "Away",
                                            "color": "CornflowerBlue",
                                        },
                                    },
                                    {
                                        "type": "custom:button-card",
                                        "entity": "sensor.komfovent_operation_mode",
                                        "color": "grey",
                                        "tap_action": {
                                            "action": "call-service",
                                            "service": "modbus.write_register",
                                            "service_data": {
                                                "address": 4,
                                                "hub": "Komfovent",
                                                "unit": 1,
                                                "value": 2,
                                            },
                                        },
                                        "name": "Normal",
                                        "icon": "mdi:home-account",
                                        "state": {
                                            "value": "Normal",
                                            "color": "CornflowerBlue",
                                        },
                                    },
                                    {
                                        "type": "custom:button-card",
                                        "entity": "sensor.komfovent_operation_mode",
                                        "color": "grey",
                                        "tap_action": {
                                            "action": "call-service",
                                            "service": "modbus.write_register",
                                            "service_data": {
                                                "address": 4,
                                                "hub": "Komfovent",
                                                "unit": 1,
                                                "value": 3,
                                            },
                                        },
                                        "name": "Intensive",
                                        "icon": "mdi:weather-windy",
                                        "state": {
                                            "value": "Intensive",
                                            "color": "CornflowerBlue",
                                        },
                                    },
                                    {
                                        "type": "custom:button-card",
                                        "entity": "sensor.komfovent_operation_mode",
                                        "color": "grey",
                                        "tap_action": {
                                            "action": "call-service",
                                            "service": "modbus.write_register",
                                            "service_data": {
                                                "address": 4,
                                                "hub": "Komfovent",
                                                "unit": 1,
                                                "value": 4,
                                            },
                                        },
                                        "name": "Boost",
                                        "icon": "mdi:fan",
                                        "state": {
                                            "value": "Boost",
                                            "color": "CornflowerBlue",
                                        },
                                    },
                                ],
                            },
                            {
                                "type": "horizontal-stack",
                                "cards": [
                                    {
                                        "type": "sensor",
                                        "entity": "sensor.komfovent_supply_temperature_c",  # noqa: E501
                                        "name": "Supply",
                                        "icon": "mdi:home-import-outline",
                                    },
                                    {
                                        "type": "sensor",
                                        "entity": "sensor.komfovent_extract_temperature_c",  # noqa: E501
                                        "name": "Extract",
                                        "icon": "mdi:home-export-outline",
                                    },
                                    {
                                        "type": "sensor",
                                        "entity": "sensor.komfovent_outdoor_temperature_c",  # noqa: E501
                                        "name": "Outside",
                                        "icon": "mdi:thermometer",
                                    },
                                ],
                            },
                            {
                                "type": "horizontal-stack",
                                "cards": [
                                    {
                                        "type": "custom:numberbox-card",
                                        "name": "Setpoint",
                                        "entity": "input_number.komfovent_set_temp",
                                    },
                                    {
                                        "type": "custom:numberbox-card",
                                        "name": "Fan Speed",
                                        "entity": "input_number.komfovent_set_fan",
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Status",
                        "entities": [
                            "binary_sensor.komfovent_status_starting",
                            "binary_sensor.komfovent_status_stopping",
                            "binary_sensor.komfovent_status_fan",
                            "binary_sensor.komfovent_status_rotor",
                            "binary_sensor.komfovent_status_heating",
                            "binary_sensor.komfovent_status_cooling",
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Energy",
                        "entities": [
                            "sensor.komfovent_power_consumption_w",
                            "sensor.komfovent_heat_recovery_w",
                            "sensor.komfovent_heater_power_w",
                        ],
                    },
                ],
            }
        ],
    }
