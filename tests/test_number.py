"""Tests for Komfovent number platform."""

import pytest
from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfVolumeFlowRate

from custom_components.komfovent import registers
from custom_components.komfovent.const import (
    DOMAIN,
    Controller,
    FlowControl,
    FlowUnit,
)
from custom_components.komfovent.number import (
    FlowNumber,
    KomfoventNumber,
    TemperatureNumber,
)

DESC = NumberEntityDescription(key="test_number", name="Test")

# ==================== Data Tables ====================

NATIVE_VALUE_CASES = [
    ({100: 42}, 42.0),
    (None, None),
    ({}, None),
    ({100: "not a number"}, None),
]

SET_VALUE_CASES = [(50.0, 50), (42.7, 42)]

TEMP_READ_CASES = [(215, 21.5), (50, 5.0), (400, 40.0)]
TEMP_WRITE_CASES = [(21.5, 215), (5.0, 50), (40.0, 400)]

FLOW_UNITS = [
    (Controller.C6, FlowControl.OFF, None, PERCENTAGE),
    (
        Controller.C6,
        FlowControl.CONSTANT,
        FlowUnit.M3H,
        UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    (
        Controller.C6,
        FlowControl.VARIABLE,
        FlowUnit.LS,
        UnitOfVolumeFlowRate.LITERS_PER_SECOND,
    ),
    (
        Controller.C6M,
        FlowControl.DIRECT,
        FlowUnit.M3H,
        UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    ),
    (Controller.C8, None, None, PERCENTAGE),
]

FLOW_EDGE_CASES = [
    (None, None, None),
    (
        {registers.REG_FLOW_CONTROL: FlowControl.CONSTANT, registers.REG_FLOW_UNIT: 99},
        99,
        None,
    ),
]

# ==================== Base Number Tests ====================


def test_entity_properties(mock_coordinator):
    """Test number entity initialization and properties."""
    n = KomfoventNumber(mock_coordinator, 100, DESC)
    assert n.register_id == 100
    assert n.unique_id == "test_entry_id_test_number"
    assert n.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}


@pytest.mark.parametrize(("data", "expected"), NATIVE_VALUE_CASES)
def test_native_value(mock_coordinator, data, expected):
    """Test native_value with various data states."""
    mock_coordinator.data = data
    assert KomfoventNumber(mock_coordinator, 100, DESC).native_value == expected


@pytest.mark.parametrize(("value", "expected_int"), SET_VALUE_CASES)
async def test_set_native_value(mock_coordinator, value, expected_int):
    """Test async_set_native_value writes to register."""
    await KomfoventNumber(mock_coordinator, 100, DESC).async_set_native_value(value)
    mock_coordinator.client.write.assert_called_once_with(100, expected_int)
    mock_coordinator.async_request_refresh.assert_called_once()


# ==================== Temperature Number Tests ====================


@pytest.mark.parametrize(("raw", "expected"), TEMP_READ_CASES)
def test_temperature_native_value(mock_coordinator, raw, expected):
    """Test TemperatureNumber divides by 10."""
    mock_coordinator.data = {100: raw}
    assert TemperatureNumber(mock_coordinator, 100, DESC).native_value == expected


def test_temperature_native_value_none(mock_coordinator):
    """Test TemperatureNumber returns None when no data."""
    mock_coordinator.data = None
    assert TemperatureNumber(mock_coordinator, 100, DESC).native_value is None


@pytest.mark.parametrize(("value", "expected_raw"), TEMP_WRITE_CASES)
async def test_temperature_set_value(mock_coordinator, value, expected_raw):
    """Test TemperatureNumber multiplies by 10."""
    await TemperatureNumber(mock_coordinator, 100, DESC).async_set_native_value(value)
    mock_coordinator.client.write.assert_called_once_with(100, expected_raw)


# ==================== Flow Number Tests ====================


@pytest.mark.parametrize(
    ("controller", "flow_control", "flow_unit", "expected_unit"), FLOW_UNITS
)
def test_flow_number_units(
    mock_coordinator, controller, flow_control, flow_unit, expected_unit
):
    """Test FlowNumber dynamic unit selection."""
    mock_coordinator.controller = controller
    data = {100: 50}
    if flow_control is not None:
        data[registers.REG_FLOW_CONTROL] = flow_control
    if flow_unit is not None:
        data[registers.REG_FLOW_UNIT] = flow_unit
    mock_coordinator.data = data
    assert (
        FlowNumber(mock_coordinator, 100, DESC).native_unit_of_measurement
        == expected_unit
    )


@pytest.mark.parametrize(("data", "flow_unit", "expected"), FLOW_EDGE_CASES)
def test_flow_number_edge_cases(mock_coordinator, data, flow_unit, expected):
    """Test FlowNumber edge cases."""
    mock_coordinator.controller = Controller.C6
    mock_coordinator.data = data
    assert (
        FlowNumber(mock_coordinator, 100, DESC).native_unit_of_measurement == expected
    )
