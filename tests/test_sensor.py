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

# ====================
# Base Sensor Tests
# ====================


class TestKomfoventSensor:
    """Tests for the base KomfoventSensor class."""

    def test_initialization(self, mock_coordinator):
        """Test sensor initialization."""
        description = SensorEntityDescription(
            key="test_sensor",
            name="Test Sensor",
        )
        sensor = KomfoventSensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        assert sensor.register_id == registers.REG_POWER
        assert sensor.entity_description.key == "test_sensor"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = SensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventSensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        assert sensor.unique_id == "test_entry_id_test_sensor"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = SensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventSensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        device_info = sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"

    def test_native_value_with_data(self, mock_coordinator):
        """Test native_value returns register value when data exists."""
        description = SensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventSensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        # REG_POWER is 1 in the fixture
        assert sensor.native_value == 1

    def test_native_value_no_data(self, mock_coordinator):
        """Test native_value returns None when no data."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventSensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_native_value_missing_register(self, mock_coordinator):
        """Test native_value returns None for missing register."""
        description = SensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventSensor(
            coordinator=mock_coordinator,
            register_id=99999,  # Non-existent register
            entity_description=description,
        )

        assert sensor.native_value is None


# ====================
# Float Scaling Sensors
# ====================


class TestFloatSensor:
    """Tests for FloatSensor."""

    def test_native_value_valid(self, mock_coordinator):
        """Test float conversion of valid value."""
        mock_coordinator.data = {100: 42}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 42.0

    def test_native_value_none(self, mock_coordinator):
        """Test float returns None when no data."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_native_value_invalid_type(self, mock_coordinator):
        """Test float returns None for invalid type."""
        mock_coordinator.data = {100: "not a number"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestFloatX10Sensor:
    """Tests for FloatX10Sensor (divides by 10)."""

    def test_native_value_division(self, mock_coordinator):
        """Test value is divided by 10."""
        mock_coordinator.data = {100: 250}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX10Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 25.0

    def test_native_value_none(self, mock_coordinator):
        """Test returns None when base returns None."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX10Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestFloatX100Sensor:
    """Tests for FloatX100Sensor (divides by 100)."""

    def test_native_value_division(self, mock_coordinator):
        """Test value is divided by 100."""
        mock_coordinator.data = {100: 2500}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX100Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 25.0

    def test_native_value_none(self, mock_coordinator):
        """Test returns None when base returns None."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX100Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestFloatX1000Sensor:
    """Tests for FloatX1000Sensor (divides by 1000)."""

    def test_native_value_division(self, mock_coordinator):
        """Test value is divided by 1000."""
        mock_coordinator.data = {100: 25000}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX1000Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 25.0

    def test_native_value_none(self, mock_coordinator):
        """Test returns None when parent returns None."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX1000Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_native_value_invalid_type(self, mock_coordinator):
        """Test returns None for invalid type."""
        mock_coordinator.data = {100: "invalid"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FloatX1000Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


# ====================
# Validation Sensors
# ====================


class TestDutyCycleSensor:
    """Tests for DutyCycleSensor with range validation (0-100)."""

    def test_valid_value(self, mock_coordinator):
        """Test valid duty cycle value."""
        mock_coordinator.data = {100: 500}  # 50.0% after /10
        description = SensorEntityDescription(key="test", name="Test")
        sensor = DutyCycleSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 50.0

    def test_min_boundary(self, mock_coordinator):
        """Test minimum boundary value."""
        mock_coordinator.data = {100: 0}  # 0%
        description = SensorEntityDescription(key="test", name="Test")
        sensor = DutyCycleSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 0.0

    def test_max_boundary(self, mock_coordinator):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: 1000}  # 100%
        description = SensorEntityDescription(key="test", name="Test")
        sensor = DutyCycleSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 100.0

    def test_out_of_range_high(self, mock_coordinator):
        """Test out of range high value returns None."""
        mock_coordinator.data = {100: 1010}  # 101%
        description = SensorEntityDescription(key="test", name="Test")
        sensor = DutyCycleSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_out_of_range_low(self, mock_coordinator):
        """Test negative value returns None."""
        mock_coordinator.data = {100: -10}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = DutyCycleSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestTemperatureSensor:
    """Tests for TemperatureSensor with range validation (-50 to 120)."""

    def test_valid_value(self, mock_coordinator):
        """Test valid temperature value."""
        mock_coordinator.data = {100: 215}  # 21.5°C
        description = SensorEntityDescription(key="test", name="Test")
        sensor = TemperatureSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 21.5

    def test_min_boundary(self, mock_coordinator):
        """Test minimum boundary value."""
        mock_coordinator.data = {100: -500}  # -50°C
        description = SensorEntityDescription(key="test", name="Test")
        sensor = TemperatureSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == -50.0

    def test_max_boundary(self, mock_coordinator):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: 1200}  # 120°C
        description = SensorEntityDescription(key="test", name="Test")
        sensor = TemperatureSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 120.0

    def test_out_of_range_high(self, mock_coordinator):
        """Test out of range high value returns None."""
        mock_coordinator.data = {100: 1210}  # 121°C
        description = SensorEntityDescription(key="test", name="Test")
        sensor = TemperatureSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_out_of_range_low(self, mock_coordinator):
        """Test out of range low value returns None."""
        mock_coordinator.data = {100: -510}  # -51°C
        description = SensorEntityDescription(key="test", name="Test")
        sensor = TemperatureSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestRelativeHumiditySensor:
    """Tests for RelativeHumiditySensor with range validation (0-125)."""

    def test_valid_value(self, mock_coordinator):
        """Test valid humidity value."""
        mock_coordinator.data = {100: 65}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = RelativeHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 65

    def test_max_boundary(self, mock_coordinator):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: 125}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = RelativeHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 125

    def test_out_of_range(self, mock_coordinator):
        """Test out of range value returns None."""
        mock_coordinator.data = {100: 126}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = RelativeHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_invalid_type(self, mock_coordinator):
        """Test invalid type returns None."""
        mock_coordinator.data = {100: "invalid"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = RelativeHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestAbsoluteHumiditySensor:
    """Tests for AbsoluteHumiditySensor with range validation."""

    def test_valid_value(self, mock_coordinator):
        """Test valid absolute humidity value."""
        mock_coordinator.data = {100: 850}  # 8.50 g/m³
        description = SensorEntityDescription(key="test", name="Test")
        sensor = AbsoluteHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 8.5

    def test_min_boundary(self, mock_coordinator):
        """Test minimum boundary value."""
        mock_coordinator.data = {100: 1}  # 0.01 g/m³
        description = SensorEntityDescription(key="test", name="Test")
        sensor = AbsoluteHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 0.01

    def test_out_of_range_low(self, mock_coordinator):
        """Test below minimum returns None."""
        mock_coordinator.data = {100: 0}  # Below 0.01
        description = SensorEntityDescription(key="test", name="Test")
        sensor = AbsoluteHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_out_of_range_high(self, mock_coordinator):
        """Test above maximum returns None."""
        mock_coordinator.data = {100: 10001}  # 100.01 g/m³
        description = SensorEntityDescription(key="test", name="Test")
        sensor = AbsoluteHumiditySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestCO2Sensor:
    """Tests for CO2Sensor with range validation (0-2500)."""

    def test_valid_value(self, mock_coordinator):
        """Test valid CO2 value."""
        mock_coordinator.data = {100: 800}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = CO2Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 800

    def test_max_boundary(self, mock_coordinator):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: 2500}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = CO2Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 2500

    def test_out_of_range(self, mock_coordinator):
        """Test out of range value returns None."""
        mock_coordinator.data = {100: 2501}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = CO2Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_invalid_type(self, mock_coordinator):
        """Test invalid type returns None."""
        mock_coordinator.data = {100: "invalid"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = CO2Sensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestSPISensor:
    """Tests for SPISensor with range validation (0-5)."""

    def test_valid_value(self, mock_coordinator):
        """Test valid SPI value."""
        mock_coordinator.data = {100: 2500}  # 2.5 after /1000
        description = SensorEntityDescription(key="test", name="Test")
        sensor = SPISensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 2.5

    def test_max_boundary(self, mock_coordinator):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: 5000}  # 5.0
        description = SensorEntityDescription(key="test", name="Test")
        sensor = SPISensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 5.0

    def test_out_of_range(self, mock_coordinator):
        """Test out of range value returns None."""
        mock_coordinator.data = {100: 5001}  # > 5.0
        description = SensorEntityDescription(key="test", name="Test")
        sensor = SPISensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestVOCSensor:
    """Tests for VOCSensor with range validation (0-125)."""

    def test_valid_value(self, mock_coordinator):
        """Test valid VOC value."""
        mock_coordinator.data = {100: 50}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = VOCSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 50

    def test_max_boundary(self, mock_coordinator):
        """Test maximum boundary value."""
        mock_coordinator.data = {100: 125}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = VOCSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == 125

    def test_out_of_range(self, mock_coordinator):
        """Test out of range value returns None."""
        mock_coordinator.data = {100: 126}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = VOCSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_invalid_type(self, mock_coordinator):
        """Test invalid type returns None."""
        mock_coordinator.data = {100: "invalid"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = VOCSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


# ====================
# Enum Sensors
# ====================


class TestFirmwareVersionSensor:
    """Tests for FirmwareVersionSensor."""

    def test_valid_firmware(self, mock_coordinator):
        """Test valid firmware version parsing."""
        # C6 1.2.3.4 = 18886660 (packed bitfield format)
        mock_coordinator.data = {100: 18886660}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FirmwareVersionSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == "C6 1.2.3.4"

    def test_zero_value(self, mock_coordinator):
        """Test zero firmware returns None."""
        mock_coordinator.data = {100: 0}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FirmwareVersionSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_none_value(self, mock_coordinator):
        """Test None returns None."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FirmwareVersionSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_invalid_type(self, mock_coordinator):
        """Test invalid type returns None."""
        mock_coordinator.data = {100: "invalid"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FirmwareVersionSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestConnectedPanelsSensor:
    """Tests for ConnectedPanelsSensor."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (ConnectedPanels.NONE, "none"),
            (ConnectedPanels.PANEL1, "panel1"),
            (ConnectedPanels.PANEL2, "panel2"),
            (ConnectedPanels.BOTH, "both"),
        ],
    )
    def test_valid_values(self, mock_coordinator, value, expected):
        """Test all valid connected panels values."""
        mock_coordinator.data = {100: value}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = ConnectedPanelsSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == expected

    def test_invalid_value(self, mock_coordinator):
        """Test invalid value returns None."""
        mock_coordinator.data = {100: 99}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = ConnectedPanelsSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestHeatExchangerTypeSensor:
    """Tests for HeatExchangerTypeSensor."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (HeatExchangerType.PLATE, "plate"),
            (HeatExchangerType.ROTARY, "rotary"),
        ],
    )
    def test_valid_values(self, mock_coordinator, value, expected):
        """Test all valid heat exchanger type values."""
        mock_coordinator.data = {100: value}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = HeatExchangerTypeSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == expected

    def test_invalid_value(self, mock_coordinator):
        """Test invalid value returns None."""
        mock_coordinator.data = {100: 99}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = HeatExchangerTypeSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


class TestFlowUnitSensor:
    """Tests for FlowUnitSensor."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (FlowUnit.M3H, "m3h"),
            (FlowUnit.LS, "ls"),
        ],
    )
    def test_valid_values(self, mock_coordinator, value, expected):
        """Test all valid flow unit values."""
        mock_coordinator.data = {100: value}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowUnitSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value == expected

    def test_invalid_value(self, mock_coordinator):
        """Test invalid value returns None."""
        mock_coordinator.data = {100: 99}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowUnitSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


# ====================
# Dynamic Unit Sensors
# ====================


class TestFlowSensor:
    """Tests for FlowSensor with dynamic units."""

    def test_c6_flow_control_off(self, mock_coordinator):
        """Test C6 with flow control off returns percentage."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.OFF,
            100: 50,
        }
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_c6_flow_unit_m3h(self, mock_coordinator):
        """Test C6 with m3/h flow unit."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.CONSTANT,
            registers.REG_FLOW_UNIT: FlowUnit.M3H,
            100: 350,
        }
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert (
            sensor.native_unit_of_measurement
            == UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        )

    def test_c6_flow_unit_ls(self, mock_coordinator):
        """Test C6 with l/s flow unit."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.VARIABLE,
            registers.REG_FLOW_UNIT: FlowUnit.LS,
            100: 100,
        }
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert (
            sensor.native_unit_of_measurement == UnitOfVolumeFlowRate.LITERS_PER_SECOND
        )

    def test_c6m_flow_unit(self, mock_coordinator):
        """Test C6M flow unit handling."""
        mock_coordinator.controller = Controller.C6M
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.DIRECT,
            registers.REG_FLOW_UNIT: FlowUnit.M3H,
            100: 200,
        }
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert (
            sensor.native_unit_of_measurement
            == UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        )

    def test_c8_returns_percentage(self, mock_coordinator):
        """Test C8 always returns percentage."""
        mock_coordinator.controller = Controller.C8
        mock_coordinator.data = {100: 75}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_unit_of_measurement == PERCENTAGE

    def test_no_data(self, mock_coordinator):
        """Test returns None when no data."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = FlowSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_unit_of_measurement is None


# ====================
# System Time Sensor
# ====================


class TestSystemTimeSensor:
    """Tests for SystemTimeSensor."""

    def test_valid_timestamp(self, mock_coordinator):
        """Test valid Unix timestamp conversion."""
        # 1704067200 = 2024-01-01 00:00:00 UTC
        mock_coordinator.data = {100: 1704067200}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = SystemTimeSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        result = sensor.native_value
        assert result is not None
        assert isinstance(result, datetime)

    def test_none_value(self, mock_coordinator):
        """Test None returns None."""
        mock_coordinator.data = None
        description = SensorEntityDescription(key="test", name="Test")
        sensor = SystemTimeSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None

    def test_invalid_type(self, mock_coordinator):
        """Test invalid type returns None."""
        mock_coordinator.data = {100: "invalid"}
        description = SensorEntityDescription(key="test", name="Test")
        sensor = SystemTimeSensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.native_value is None


# ====================
# Factory Functions
# ====================


class TestCreateSensors:
    """Tests for create_sensors factory function."""

    async def test_creates_core_sensors(self, mock_coordinator):
        """Test that core sensors are created."""
        sensors = await create_sensors(mock_coordinator)

        # Should have many sensors
        assert len(sensors) > 20

        # Check some expected sensor keys
        sensor_keys = {s.entity_description.key for s in sensors}
        assert "supply_temperature" in sensor_keys
        assert "extract_temperature" in sensor_keys
        assert "outdoor_temperature" in sensor_keys
        assert "supply_fan" in sensor_keys
        assert "extract_fan" in sensor_keys
        assert "controller_firmware" in sensor_keys

    async def test_c6_specific_sensors(self, mock_coordinator):
        """Test C6 controller-specific sensors are created."""
        mock_coordinator.controller = Controller.C6
        sensors = await create_sensors(mock_coordinator)

        sensor_keys = {s.entity_description.key for s in sensors}
        assert "flow_unit" in sensor_keys
        assert "specific_power_input" in sensor_keys
        assert "total_ahu_energy" in sensor_keys

    async def test_c8_no_c6_specific_sensors(self, mock_coordinator):
        """Test C8 controller doesn't get C6-specific sensors."""
        mock_coordinator.controller = Controller.C8
        sensors = await create_sensors(mock_coordinator)

        sensor_keys = {s.entity_description.key for s in sensors}
        assert "flow_unit" not in sensor_keys
        assert "specific_power_input" not in sensor_keys

    async def test_panel_sensors_created_when_panel_connected(self, mock_coordinator):
        """Test panel sensors are created when panel is connected."""
        mock_coordinator.data[registers.REG_CONNECTED_PANELS] = ConnectedPanels.PANEL1
        sensors = await create_sensors(mock_coordinator)

        sensor_keys = {s.entity_description.key for s in sensors}
        assert "panel_1_temperature" in sensor_keys
        assert "panel_1_humidity" in sensor_keys

    async def test_no_panel_sensors_when_none_connected(self, mock_coordinator):
        """Test no panel sensors when no panel connected."""
        mock_coordinator.data[registers.REG_CONNECTED_PANELS] = ConnectedPanels.NONE
        sensors = await create_sensors(mock_coordinator)

        sensor_keys = {s.entity_description.key for s in sensors}
        assert "panel_1_temperature" not in sensor_keys
        assert "panel_2_temperature" not in sensor_keys


class TestCreateAqSensor:
    """Tests for create_aq_sensor factory function."""

    def test_no_coordinator_data(self, mock_coordinator):
        """Test returns None when no coordinator data."""
        mock_coordinator.data = None
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)
        assert result is None

    def test_not_installed(self, mock_coordinator):
        """Test returns None when sensor not installed."""
        mock_coordinator.data[registers.REG_AQ_SENSOR1_TYPE] = (
            AirQualitySensorType.NOT_INSTALLED
        )
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)
        assert result is None

    def test_co2_sensor(self, mock_coordinator):
        """Test CO2 sensor creation."""
        mock_coordinator.data[registers.REG_AQ_SENSOR1_TYPE] = AirQualitySensorType.CO2
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)

        assert result is not None
        assert isinstance(result, CO2Sensor)
        assert result.entity_description.key == "extract_co2"

    def test_voc_sensor(self, mock_coordinator):
        """Test VOC sensor creation."""
        mock_coordinator.data[registers.REG_AQ_SENSOR1_TYPE] = AirQualitySensorType.VOC
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)

        assert result is not None
        assert isinstance(result, VOCSensor)
        assert result.entity_description.key == "extract_voc"

    def test_humidity_sensor_indoor(self, mock_coordinator):
        """Test humidity sensor creation (indoor)."""
        mock_coordinator.data[registers.REG_AQ_SENSOR1_TYPE] = (
            AirQualitySensorType.HUMIDITY
        )
        mock_coordinator.data[registers.REG_AQ_OUTDOOR_HUMIDITY] = (
            OutdoorHumiditySensor.NONE
        )
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)

        assert result is not None
        assert isinstance(result, RelativeHumiditySensor)
        assert result.entity_description.key == "extract_humidity"

    def test_humidity_sensor_outdoor(self, mock_coordinator):
        """Test humidity sensor creation (outdoor)."""
        mock_coordinator.data[registers.REG_AQ_SENSOR1_TYPE] = (
            AirQualitySensorType.HUMIDITY
        )
        mock_coordinator.data[registers.REG_AQ_OUTDOOR_HUMIDITY] = (
            OutdoorHumiditySensor.SENSOR1
        )
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_1)

        assert result is not None
        assert isinstance(result, RelativeHumiditySensor)
        assert result.entity_description.key == "outdoor_humidity"

    def test_sensor2_co2(self, mock_coordinator):
        """Test sensor 2 CO2 creation."""
        mock_coordinator.data[registers.REG_AQ_SENSOR2_TYPE] = AirQualitySensorType.CO2
        result = create_aq_sensor(mock_coordinator, registers.REG_EXTRACT_AQ_2)

        assert result is not None
        assert isinstance(result, CO2Sensor)

    def test_unknown_register(self, mock_coordinator):
        """Test unknown register returns None."""
        result = create_aq_sensor(mock_coordinator, 99999)
        assert result is None
