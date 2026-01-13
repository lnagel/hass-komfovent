"""Tests for Komfovent sensor platform."""

from datetime import datetime

import pytest
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfVolumeFlowRate

from custom_components.komfovent import registers
from custom_components.komfovent.const import (
    DOMAIN,
    AirQualitySensorType,
    ConnectedPanels,
    Controller,
    FlowControl,
    FlowUnit,
    HeatExchangerType,
    OutdoorHumiditySensor,
)
from custom_components.komfovent.sensor import (
    AbsoluteHumiditySensor,
    CO2Sensor,
    ConnectedPanelsSensor,
    DutyCycleSensor,
    FirmwareVersionSensor,
    FloatSensor,
    FloatX10Sensor,
    FloatX100Sensor,
    FloatX1000Sensor,
    FlowSensor,
    FlowUnitSensor,
    HeatExchangerTypeSensor,
    KomfoventSensor,
    RelativeHumiditySensor,
    SPISensor,
    SystemTimeSensor,
    TemperatureSensor,
    VOCSensor,
    create_aq_sensor,
    create_sensors,
)

DESC = SensorEntityDescription(key="test", name="Test")

# ==================== Data Tables ====================

# (sensor_class, raw, expected, min, max, out_of_range, low_out_of_range)
VALIDATION_SENSORS = [
    (DutyCycleSensor, 500, 50.0, 0, 1000, 1010, -10),
    (TemperatureSensor, 215, 21.5, -500, 1200, 1210, -510),
    (RelativeHumiditySensor, 65, 65, 0, 125, 126, None),
    (AbsoluteHumiditySensor, 850, 8.5, 1, 10000, 10001, 0),
    (CO2Sensor, 800, 800, 0, 2500, 2501, None),
    (VOCSensor, 50, 50, 0, 125, 126, None),
    (SPISensor, 2500, 2.5, 0, 5000, 5001, None),
]

SCALING_SENSORS = [
    (FloatSensor, 42, 42.0),
    (FloatX10Sensor, 250, 25.0),
    (FloatX100Sensor, 2500, 25.0),
    (FloatX1000Sensor, 25000, 25.0),
]

ENUM_SENSORS = [
    (ConnectedPanelsSensor, ConnectedPanels.NONE, "none"),
    (ConnectedPanelsSensor, ConnectedPanels.PANEL1, "panel1"),
    (HeatExchangerTypeSensor, HeatExchangerType.PLATE, "plate"),
    (HeatExchangerTypeSensor, HeatExchangerType.ROTARY, "rotary"),
    (FlowUnitSensor, FlowUnit.M3H, "m3h"),
    (FlowUnitSensor, FlowUnit.LS, "ls"),
]

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

AQ_SENSORS = [
    (AirQualitySensorType.CO2, None, CO2Sensor, "extract_co2"),
    (AirQualitySensorType.VOC, None, VOCSensor, "extract_voc"),
    (
        AirQualitySensorType.HUMIDITY,
        OutdoorHumiditySensor.NONE,
        RelativeHumiditySensor,
        "extract_humidity",
    ),
    (
        AirQualitySensorType.HUMIDITY,
        OutdoorHumiditySensor.SENSOR1,
        RelativeHumiditySensor,
        "outdoor_humidity",
    ),
    (AirQualitySensorType.NOT_INSTALLED, None, None, None),
]


# ==================== Base Sensor Tests ====================


class TestKomfoventSensor:
    """Tests for the base KomfoventSensor class."""

    def test_initialization(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = KomfoventSensor(mock_coordinator, registers.REG_POWER, DESC)
        assert sensor.register_id == registers.REG_POWER

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        sensor = KomfoventSensor(mock_coordinator, registers.REG_POWER, DESC)
        assert sensor.unique_id == "test_entry_id_test"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        sensor = KomfoventSensor(mock_coordinator, registers.REG_POWER, DESC)
        assert sensor.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}

    @pytest.mark.parametrize(
        ("data", "expected"),
        [({registers.REG_POWER: 1}, 1), (None, None), ({}, None)],
    )
    def test_native_value(self, mock_coordinator, data, expected):
        """Test native_value with various data states."""
        mock_coordinator.data = data
        sensor = KomfoventSensor(mock_coordinator, registers.REG_POWER, DESC)
        assert sensor.native_value == expected


# ==================== Scaling Sensor Tests ====================


@pytest.mark.parametrize(("sensor_class", "raw", "expected"), SCALING_SENSORS)
def test_scaling_sensors(mock_coordinator, sensor_class, raw, expected):
    """Test sensors with scaling (division)."""
    mock_coordinator.data = {100: raw}
    assert sensor_class(mock_coordinator, 100, DESC).native_value == expected


@pytest.mark.parametrize(
    "sensor_class", [FloatSensor, FloatX10Sensor, FloatX100Sensor, FloatX1000Sensor]
)
def test_scaling_sensors_none(mock_coordinator, sensor_class):
    """Test scaling sensors return None when no data."""
    mock_coordinator.data = None
    assert sensor_class(mock_coordinator, 100, DESC).native_value is None


def test_float_x1000_invalid_type(mock_coordinator):
    """Test FloatX1000Sensor returns None for invalid type."""
    mock_coordinator.data = {100: "invalid"}
    assert FloatX1000Sensor(mock_coordinator, 100, DESC).native_value is None


# ==================== Validation Sensor Tests ====================


@pytest.mark.parametrize(
    (
        "sensor_class",
        "raw",
        "expected",
        "min_raw",
        "max_raw",
        "out_of_range",
        "low_out",
    ),
    VALIDATION_SENSORS,
)
class TestValidationSensors:
    """Tests for sensors with range validation."""

    def test_valid_value(
        self,
        mock_coordinator,
        sensor_class,
        raw,
        expected,
        min_raw,
        max_raw,
        out_of_range,
        low_out,
    ):
        """Test valid value within range."""
        mock_coordinator.data = {100: raw}
        assert sensor_class(mock_coordinator, 100, DESC).native_value == expected

    def test_min_boundary(
        self,
        mock_coordinator,
        sensor_class,
        raw,
        expected,
        min_raw,
        max_raw,
        out_of_range,
        low_out,
    ):
        """Test minimum boundary value."""
        mock_coordinator.data = {100: min_raw}
        assert sensor_class(mock_coordinator, 100, DESC).native_value is not None

    def test_max_boundary(
        self,
        mock_coordinator,
        sensor_class,
        raw,
        expected,
        min_raw,
        max_raw,
        out_of_range,
        low_out,
    ):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: max_raw}
        assert sensor_class(mock_coordinator, 100, DESC).native_value is not None

    def test_out_of_range_high(
        self,
        mock_coordinator,
        sensor_class,
        raw,
        expected,
        min_raw,
        max_raw,
        out_of_range,
        low_out,
    ):
        """Test out of range value returns None."""
        mock_coordinator.data = {100: out_of_range}
        assert sensor_class(mock_coordinator, 100, DESC).native_value is None

    def test_out_of_range_low(
        self,
        mock_coordinator,
        sensor_class,
        raw,
        expected,
        min_raw,
        max_raw,
        out_of_range,
        low_out,
    ):
        """Test below minimum returns None."""
        if low_out is None:
            pytest.skip("No low out-of-range value for this sensor")
        mock_coordinator.data = {100: low_out}
        assert sensor_class(mock_coordinator, 100, DESC).native_value is None


@pytest.mark.parametrize("sensor_class", [RelativeHumiditySensor, CO2Sensor, VOCSensor])
def test_validation_sensor_invalid_type(mock_coordinator, sensor_class):
    """Test validation sensors return None for invalid type."""
    mock_coordinator.data = {100: "invalid"}
    assert sensor_class(mock_coordinator, 100, DESC).native_value is None


# ==================== Enum Sensor Tests ====================


@pytest.mark.parametrize(("sensor_class", "value", "expected"), ENUM_SENSORS)
def test_enum_sensors(mock_coordinator, sensor_class, value, expected):
    """Test enum-based sensors."""
    mock_coordinator.data = {100: value}
    assert sensor_class(mock_coordinator, 100, DESC).native_value == expected


@pytest.mark.parametrize(
    "sensor_class", [ConnectedPanelsSensor, HeatExchangerTypeSensor, FlowUnitSensor]
)
def test_enum_sensors_invalid(mock_coordinator, sensor_class):
    """Test invalid enum value returns None."""
    mock_coordinator.data = {100: 99}
    assert sensor_class(mock_coordinator, 100, DESC).native_value is None


class TestFirmwareVersionSensor:
    """Tests for FirmwareVersionSensor."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(18886660, "C6 1.2.3.4"), (0, None), ("invalid", None), (None, None)],
    )
    def test_firmware_values(self, mock_coordinator, value, expected):
        """Test firmware version parsing."""
        mock_coordinator.data = None if value is None else {100: value}
        assert (
            FirmwareVersionSensor(mock_coordinator, 100, DESC).native_value == expected
        )


# ==================== Dynamic Unit Sensors ====================


@pytest.mark.parametrize(
    ("controller", "flow_control", "flow_unit", "expected"), FLOW_UNITS
)
def test_flow_sensor_units(
    mock_coordinator, controller, flow_control, flow_unit, expected
):
    """Test FlowSensor dynamic unit selection."""
    mock_coordinator.controller = controller
    data = {100: 50}
    if flow_control is not None:
        data[registers.REG_FLOW_CONTROL] = flow_control
    if flow_unit is not None:
        data[registers.REG_FLOW_UNIT] = flow_unit
    mock_coordinator.data = data
    assert (
        FlowSensor(mock_coordinator, 100, DESC).native_unit_of_measurement == expected
    )


def test_flow_sensor_no_data(mock_coordinator):
    """Test FlowSensor returns None when no data."""
    mock_coordinator.data = None
    assert FlowSensor(mock_coordinator, 100, DESC).native_unit_of_measurement is None


# ==================== System Time Sensor ====================


@pytest.mark.parametrize(
    ("data", "is_datetime"),
    [({100: 1704067200}, True), (None, False), ({100: "invalid"}, False)],
)
def test_system_time_sensor(mock_coordinator, data, is_datetime):
    """Test SystemTimeSensor native_value."""
    mock_coordinator.data = data
    result = SystemTimeSensor(mock_coordinator, 100, DESC).native_value
    assert isinstance(result, datetime) if is_datetime else result is None


# ==================== Factory Functions ====================


@pytest.mark.parametrize(
    ("controller", "expected", "unexpected"),
    [
        (Controller.C6, {"supply_temperature", "flow_unit"}, set()),
        (Controller.C8, {"supply_temperature"}, {"flow_unit", "specific_power_input"}),
    ],
)
async def test_create_sensors_controller(
    mock_coordinator, controller, expected, unexpected
):
    """Test controller-specific sensor creation."""
    mock_coordinator.controller = controller
    sensors = await create_sensors(mock_coordinator)
    keys = {s.entity_description.key for s in sensors}
    assert expected <= keys
    assert not (unexpected & keys)


async def test_create_sensors_count(mock_coordinator):
    """Test that minimum number of sensors are created."""
    assert len(await create_sensors(mock_coordinator)) > 20


@pytest.mark.parametrize(
    ("panels", "expected_in", "expected_out"),
    [
        (ConnectedPanels.PANEL1, {"panel_1_temperature"}, {"panel_2_temperature"}),
        (ConnectedPanels.NONE, set(), {"panel_1_temperature", "panel_2_temperature"}),
    ],
)
async def test_create_sensors_panels(
    mock_coordinator, panels, expected_in, expected_out
):
    """Test panel sensor creation based on connected panels."""
    mock_coordinator.data[registers.REG_CONNECTED_PANELS] = panels
    keys = {s.entity_description.key for s in await create_sensors(mock_coordinator)}
    assert expected_in <= keys
    assert not (expected_out & keys)


@pytest.mark.parametrize(
    ("sensor_type", "outdoor", "expected_class", "expected_key"), AQ_SENSORS
)
def test_create_aq_sensor(
    mock_coordinator, sensor_type, outdoor, expected_class, expected_key
):
    """Test AQ sensor creation based on type."""
    mock_coordinator.data[registers.REG_AQ_SENSOR1_TYPE] = sensor_type
    if outdoor is not None:
        mock_coordinator.data[registers.REG_AQ_OUTDOOR_HUMIDITY] = outdoor
    result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)
    if expected_class is None:
        assert result is None
    else:
        assert isinstance(result, expected_class)
        assert result.entity_description.key == expected_key


def test_create_aq_sensor_no_data(mock_coordinator):
    """Test returns None when no coordinator data."""
    mock_coordinator.data = None
    assert create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1) is None


def test_create_aq_sensor_unknown_register(mock_coordinator):
    """Test unknown register returns None."""
    assert create_aq_sensor(mock_coordinator, 99999) is None
