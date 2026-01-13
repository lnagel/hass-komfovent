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

# ==================== Data Tables ====================

FLOW_NUMBER_UNITS = [
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


# ==================== Base Number Tests ====================


class TestKomfoventNumber:
    """Tests for base KomfoventNumber entity."""

    def test_initialization(self, mock_coordinator):
        """Test number entity initialization."""
        description = NumberEntityDescription(key="test_number", name="Test Number")
        number = KomfoventNumber(mock_coordinator, 100, description)

        assert number.register_id == 100
        assert number.entity_description.key == "test_number"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = NumberEntityDescription(key="test_number", name="Test")
        number = KomfoventNumber(mock_coordinator, 100, description)

        assert number.unique_id == "test_entry_id_test_number"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = NumberEntityDescription(key="test_number", name="Test")
        number = KomfoventNumber(mock_coordinator, 100, description)

        device_info = number.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({100: 42}, 42.0),
            (None, None),
            ({}, None),
            ({100: "not a number"}, None),
        ],
    )
    def test_native_value(self, mock_coordinator, data, expected):
        """Test native_value with various data states."""
        mock_coordinator.data = data
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(mock_coordinator, 100, description)

        assert number.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_int"),
        [
            (50.0, 50),
            (42.7, 42),
        ],
    )
    async def test_async_set_native_value(self, mock_coordinator, value, expected_int):
        """Test async_set_native_value writes to register."""
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(mock_coordinator, 100, description)

        await number.async_set_native_value(value)

        mock_coordinator.client.write.assert_called_once_with(100, expected_int)
        mock_coordinator.async_request_refresh.assert_called_once()


# ==================== Temperature Number Tests ====================


class TestTemperatureNumber:
    """Tests for TemperatureNumber with x10 scaling."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (215, 21.5),
            (50, 5.0),
            (400, 40.0),
        ],
    )
    def test_native_value(self, mock_coordinator, raw, expected):
        """Test native_value divides register value by 10."""
        mock_coordinator.data = {100: raw}
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(mock_coordinator, 100, description)

        assert number.native_value == expected

    def test_native_value_none(self, mock_coordinator):
        """Test native_value returns None when parent returns None."""
        mock_coordinator.data = None
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(mock_coordinator, 100, description)

        assert number.native_value is None

    @pytest.mark.parametrize(
        ("value", "expected_raw"),
        [
            (21.5, 215),
            (5.0, 50),
            (40.0, 400),
        ],
    )
    async def test_async_set_native_value(self, mock_coordinator, value, expected_raw):
        """Test async_set_native_value multiplies value by 10."""
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(mock_coordinator, 100, description)

        await number.async_set_native_value(value)

        mock_coordinator.client.write.assert_called_once_with(100, expected_raw)
        mock_coordinator.async_request_refresh.assert_called_once()


# ==================== Flow Number Tests ====================


@pytest.mark.parametrize(
    ("controller", "flow_control", "flow_unit", "expected_unit"), FLOW_NUMBER_UNITS
)
def test_flow_number_units(
    mock_coordinator, controller, flow_control, flow_unit, expected_unit
):
    """Test FlowNumber dynamic unit selection."""
    mock_coordinator.controller = controller
    data = {100: 50}  # Need some data for falsy check
    if flow_control is not None:
        data[registers.REG_FLOW_CONTROL] = flow_control
    if flow_unit is not None:
        data[registers.REG_FLOW_UNIT] = flow_unit
    mock_coordinator.data = data

    description = NumberEntityDescription(key="test", name="Test")
    number = FlowNumber(mock_coordinator, 100, description)

    assert number.native_unit_of_measurement == expected_unit


@pytest.mark.parametrize(
    ("data", "flow_unit", "expected"),
    [
        (None, None, None),
        (
            {
                registers.REG_FLOW_CONTROL: FlowControl.CONSTANT,
                registers.REG_FLOW_UNIT: 99,
            },
            99,
            None,
        ),
    ],
)
def test_flow_number_edge_cases(mock_coordinator, data, flow_unit, expected):
    """Test FlowNumber edge cases."""
    mock_coordinator.controller = Controller.C6
    mock_coordinator.data = data
    description = NumberEntityDescription(key="test", name="Test")
    number = FlowNumber(mock_coordinator, 100, description)

    assert number.native_unit_of_measurement == expected
