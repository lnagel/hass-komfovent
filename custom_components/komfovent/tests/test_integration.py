"""Integration tests for Komfovent integration."""
import json
import os
from unittest.mock import patch, AsyncMock
import asyncio
from typing import Generator

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.modbus import DOMAIN as MODBUS_DOMAIN
from homeassistant.components.climate import (
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    ATTR_TEMPERATURE,
    PERCENTAGE,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.const import (
    UnitOfPower,
    UnitOfVolumeFlowRate,
)
from homeassistant.setup import async_setup_component
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartAsyncTcpServer

from custom_components.komfovent.const import (
    DOMAIN,
    DEFAULT_NAME,
    REG_POWER,
    REG_OPERATION_MODE,
    REG_ECO_MODE,
    REG_AUTO_MODE,
    OperationMode,
    AirQualitySensorType,
)

@pytest.fixture
def register_data() -> dict:
    """Load register data from file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    register_file = os.path.join(current_dir, "..", "documentation", "C6_holding_registers.json")
    
    with open(register_file) as f:
        return json.load(f)

@pytest.fixture
def mock_modbus_server(hass: HomeAssistant, register_data) -> Generator:
    """Create a mock Modbus server with real register data."""
    register_array = [0] * 1025
    for reg, value in register_data.items():
        register_array[int(reg)] = value

    block = ModbusSequentialDataBlock(0, register_array)
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves=store, single=True)

    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(StartAsyncTcpServer(
        context=context,
        address=("127.0.0.1", 0)
    ))
    
    yield {
        "host": "127.0.0.1",
        "port": server.server.sockets[0].getsockname()[1]
    }
    
    server.server.close()
    loop.run_until_complete(server.server.wait_closed())

@pytest.fixture
async def integration(hass: HomeAssistant, mock_modbus_server):
    """Set up the Komfovent integration."""
    # Set up Modbus first
    modbus_config = {
        CONF_NAME: DEFAULT_NAME,
        CONF_HOST: mock_modbus_server["host"],
        CONF_PORT: mock_modbus_server["port"],
        "type": "tcp",
        "delay": 0,
    }
    
    assert await async_setup_component(
        hass, 
        MODBUS_DOMAIN, 
        {MODBUS_DOMAIN: [modbus_config]}
    )
    await hass.async_block_till_done()

    # Set up Komfovent
    with patch("custom_components.komfovent.dashboard.async_get_dashboard", return_value={}), \
         patch("homeassistant.components.lovelace.dashboard.async_get_dashboards", return_value=[]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data={
                CONF_NAME: DEFAULT_NAME,
                CONF_HOST: mock_modbus_server["host"],
                CONF_PORT: mock_modbus_server["port"],
            },
        )
        
        assert result["type"] == "create_entry"
        await hass.async_block_till_done()
        return result

async def test_climate_entity(hass: HomeAssistant, integration, register_data):
    """Test climate entity setup and attributes."""
    entity_id = "climate.komfovent"
    state = hass.states.get(entity_id)
    assert state is not None

    # Check basic attributes
    assert state.attributes["temperature_unit"] == UnitOfTemperature.CELSIUS
    assert state.attributes["supported_features"] == (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )
    assert state.attributes["fan_modes"] == ["away", "normal", "intensive", "boost"]
    assert state.attributes["preset_modes"] == [mode.name.lower() for mode in OperationMode]

    # Check state based on power and operation mode
    power = int(register_data[str(REG_POWER)])
    if not power:
        assert state.state == HVACMode.OFF
    else:
        assert state.state == HVACMode.HEAT_COOL

    # Check current operation mode
    mode = int(register_data[str(REG_OPERATION_MODE)])
    assert state.attributes["preset_mode"] == OperationMode(mode).name.lower()

    # Check eco and auto modes
    eco_mode = bool(int(register_data[str(REG_ECO_MODE)]))
    auto_mode = bool(int(register_data[str(REG_AUTO_MODE)]))
    assert state.attributes.get("eco_mode") == eco_mode
    assert state.attributes.get("auto_mode") == auto_mode

async def test_temperature_sensors(hass: HomeAssistant, integration, register_data):
    """Test temperature sensor entities."""
    sensors = [
        ("sensor.komfovent_supply_temperature", "supply_temp", UnitOfTemperature.CELSIUS),
        ("sensor.komfovent_extract_temperature", "extract_temp", UnitOfTemperature.CELSIUS),
        ("sensor.komfovent_outdoor_temperature", "outdoor_temp", UnitOfTemperature.CELSIUS),
    ]

    for entity_id, reg_key, unit in sensors:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes["unit_of_measurement"] == unit
        # Temperature values are stored as actual value * 10 in Modbus
        expected_value = float(register_data[reg_key]) / 10
        assert float(state.state) == expected_value

async def test_flow_sensors(hass: HomeAssistant, integration, register_data):
    """Test flow sensor entities."""
    sensors = [
        ("sensor.komfovent_supply_flow", "supply_flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR),
        ("sensor.komfovent_extract_flow", "extract_flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR),
    ]

    for entity_id, reg_key, unit in sensors:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes["unit_of_measurement"] == unit
        assert float(state.state) == float(register_data[reg_key])

async def test_percentage_sensors(hass: HomeAssistant, integration, register_data):
    """Test percentage-based sensor entities."""
    sensors = [
        ("sensor.komfovent_supply_fan_intensity", "supply_fan_intensity"),
        ("sensor.komfovent_extract_fan_intensity", "extract_fan_intensity"),
        ("sensor.komfovent_heat_exchanger", "heat_exchanger"),
        ("sensor.komfovent_electric_heater", "electric_heater"),
        ("sensor.komfovent_filter_impurity", "filter_impurity"),
        ("sensor.komfovent_heat_exchanger_efficiency", "heat_efficiency"),
    ]

    for entity_id, reg_key in sensors:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes["unit_of_measurement"] == PERCENTAGE
        assert float(state.state) == float(register_data[reg_key])

async def test_power_sensors(hass: HomeAssistant, integration, register_data):
    """Test power-related sensor entities."""
    sensors = [
        ("sensor.komfovent_power_consumption", "power_consumption", UnitOfPower.WATT),
        ("sensor.komfovent_heater_power", "heater_power", UnitOfPower.WATT),
        ("sensor.komfovent_heat_recovery", "heat_recovery", UnitOfPower.WATT),
    ]

    for entity_id, reg_key, unit in sensors:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfPower.WATT
        assert float(state.state) == float(register_data[reg_key])

async def test_air_quality_sensors(hass: HomeAssistant, integration, register_data):
    """Test air quality sensor entities."""
    # Check AQ sensor 1
    sensor_type = int(register_data["aq_sensor1_type"])
    if sensor_type != AirQualitySensorType.NOT_INSTALLED:
        sensor_name = AirQualitySensorType(sensor_type).name
        entity_id = f"sensor.komfovent_air_quality_{sensor_name.lower()}"
        state = hass.states.get(entity_id)
        assert state is not None
        assert float(state.state) == float(register_data["aq_sensor1_value"])

    # Check AQ sensor 2
    sensor_type = int(register_data["aq_sensor2_type"])
    if sensor_type != AirQualitySensorType.NOT_INSTALLED:
        sensor_name = AirQualitySensorType(sensor_type).name
        entity_id = f"sensor.komfovent_air_quality_{sensor_name.lower()}"
        state = hass.states.get(entity_id)
        assert state is not None
        assert float(state.state) == float(register_data["aq_sensor2_value"])

async def test_climate_controls(hass: HomeAssistant, integration):
    """Test climate entity controls."""
    entity_id = "climate.komfovent"

    # Test setting temperature
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {
            "entity_id": entity_id,
            ATTR_TEMPERATURE: 22
        },
        blocking=True,
    )

    # Test setting HVAC mode
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {
            "entity_id": entity_id,
            "hvac_mode": HVACMode.OFF
        },
        blocking=True,
    )

    # Test setting preset mode
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": "normal"
        },
        blocking=True,
    )

    # Test setting fan mode
    await hass.services.async_call(
        "climate",
        "set_fan_mode",
        {
            "entity_id": entity_id,
            "fan_mode": "normal"
        },
        blocking=True,
    )
