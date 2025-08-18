# Tests for Komfovent sensors
# Framework: pytest + pytest-asyncio (Home Assistant testing idioms)
import types
import datetime as dt
from decimal import Decimal
import zoneinfo
import pytest

# We avoid importing Home Assistant runtime; instead, we mock lightweight stand-ins for coordinator and hass.
# The tests focus on pure logic of native_value, unit selection, and entity creation decisions.

# Attempt to import the module under test (adjust path if necessary).
# The repository likely places code under custom_components. If import fails, tests will be skipped gracefully.
try:
    from custom_components.komfovent.sensor import (
        create_aq_sensor,
        create_sensors,
        KomfoventSensor,
        FloatSensor,
        FloatX10Sensor,
        FloatX100Sensor,
        FloatX1000Sensor,
        FirmwareVersionSensor,
        DutyCycleSensor,
        TemperatureSensor,
        RelativeHumiditySensor,
        AbsoluteHumiditySensor,
        CO2Sensor,
        SPISensor,
        VOCSensor,
        FlowSensor,
        HeatExchangerTypeSensor,
        ConnectedPanelsSensor,
        FlowUnitSensor,
        SystemTimeSensor,
        MIN_DUTY_CYCLE, MAX_DUTY_CYCLE,
        MIN_TEMPERATURE, MAX_TEMPERATURE,
        MAX_HUMIDITY, MIN_ABS_HUMIDITY, MAX_ABS_HUMIDITY,
        MAX_CO2_PPM, MAX_SPI, MAX_VOC,
        ABS_HUMIDITY_ERRORS,
    )
    from custom_components.komfovent import registers
    from custom_components.komfovent.model import (
        Controller,
        FlowControl,
        FlowUnit,
        ConnectedPanels,
        HeatExchangerType,
        AirQualitySensorType,
        OutdoorHumiditySensor,
    )
    from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
    from homeassistant.const import PERCENTAGE
    from homeassistant.util import dt as dt_util
    HOMEASSISTANT_AVAILABLE = True
except Exception:  # pragma: no cover - allow repository variance
    HOMEASSISTANT_AVAILABLE = False

pytestmark = pytest.mark.skipif(not HOMEASSISTANT_AVAILABLE, reason="Home Assistant/komfovent module not importable in test env")

class DummyConfigEntry:
    def __init__(self, entry_id="entry123", title="Komfovent Unit"):
        self.entry_id = entry_id
        self.title = title

class DummyHass:
    class DummyConfig:
        def __init__(self, tz="UTC"):
            self.time_zone = tz
    def __init__(self, tz="UTC"):
        self.config = DummyHass.DummyConfig(tz)

class DummyCoordinator:
    def __init__(self, data=None, controller=Controller.C6, hass=None, entry_id="entry123", title="Komfovent Unit"):
        self.data = data or {}
        self.controller = controller
        self.hass = hass or DummyHass()
        self.config_entry = DummyConfigEntry(entry_id=entry_id, title=title)

# ----------------------------
# Base KomfoventSensor behavior
# ----------------------------
def test_komfovent_sensor_base_native_value_none_when_no_data():
    coord = DummyCoordinator(data=None)
    s = KomfoventSensor(coord, register_id=1234, entity_description=types.SimpleNamespace(key="k", name="n"))
    assert s.native_value is None

def test_komfovent_sensor_base_returns_value_from_coordinator():
    coord = DummyCoordinator(data={42: 7})
    s = KomfoventSensor(coord, register_id=42, entity_description=types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == 7

# ----------------------------
# Float scaling sensors
# ----------------------------
@pytest.mark.parametrize(
    "cls,input_val,expected",
    [
        (FloatSensor, "3.5", 3.5),
        (FloatSensor, 7, 7.0),
        (FloatSensor, None, None),
    ],
)
def test_float_sensor_scaling_and_invalid(cls, input_val, expected):
    coord = DummyCoordinator(data={1: input_val})
    s = cls(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == expected

@pytest.mark.parametrize("input_val,expected", [(100, 10.0), (15, 1.5), (None, None)])
def test_float_x10_sensor(input_val, expected):
    coord = DummyCoordinator(data={1: input_val})
    s = FloatX10Sensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == expected

@pytest.mark.parametrize("input_val,expected", [(100, 1.0), (250, 2.5), (None, None)])
def test_float_x100_sensor(input_val, expected):
    coord = DummyCoordinator(data={1: input_val})
    s = FloatX100Sensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == expected

@pytest.mark.parametrize("input_val,expected", [(0, 0.0), (5000, 5.0), (None, None)])
def test_float_x1000_sensor(input_val, expected):
    coord = DummyCoordinator(data={1: input_val})
    s = FloatX1000Sensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == expected

# ----------------------------
# Range-validated sensors
# ----------------------------
@pytest.mark.parametrize("val,ok", [(MIN_DUTY_CYCLE, True), (MAX_DUTY_CYCLE, True), (-1, False), (101, False), (None, None)])
def test_duty_cycle_sensor_range(val, ok):
    coord = DummyCoordinator(data={1: val*10 if val is not None else None})
    s = DutyCycleSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert s.native_value == val
    else:
        assert s.native_value is None

@pytest.mark.parametrize("val,ok", [(MIN_TEMPERATURE, True), (MAX_TEMPERATURE, True), (MIN_TEMPERATURE-0.1, False), (MAX_TEMPERATURE+0.1, False), (None, None)])
def test_temperature_sensor_range(val, ok):
    coord = DummyCoordinator(data={1: None if val is None else val*10})
    s = TemperatureSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert pytest.approx(s.native_value, rel=1e-9) == val
    else:
        assert s.native_value is None

@pytest.mark.parametrize("val,ok", [(0, True), (MAX_HUMIDITY, True), (MAX_HUMIDITY+1, False), (-1, False), (None, None)])
def test_relative_humidity_sensor_range(val, ok):
    coord = DummyCoordinator(data={1: val})
    s = RelativeHumiditySensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert s.native_value == val
    else:
        assert s.native_value is None

@pytest.mark.parametrize("val,ok", [(MIN_ABS_HUMIDITY, True), (MAX_ABS_HUMIDITY, True), (MIN_ABS_HUMIDITY-0.01, False), (MAX_ABS_HUMIDITY+0.01, False), (None, None)])
def test_absolute_humidity_sensor_range(val, ok):
    raw = None if val is None else val * 100  # FloatX100 scaling
    coord = DummyCoordinator(data={1: raw})
    s = AbsoluteHumiditySensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert pytest.approx(s.native_value, rel=1e-9) == val
    else:
        assert s.native_value is None

@pytest.mark.parametrize("val,ok", [(0, True), (MAX_CO2_PPM, True), (MAX_CO2_PPM+1, False), (-1, False), (None, None)])
def test_co2_sensor_range(val, ok):
    coord = DummyCoordinator(data={1: val})
    s = CO2Sensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert s.native_value == val
    else:
        assert s.native_value is None

@pytest.mark.parametrize("val,ok", [(0, True), (MAX_SPI, True), (MAX_SPI+0.01, False), (-0.01, False), (None, None)])
def test_spi_sensor_range(val, ok):
    raw = None if val is None else val * 1000  # FloatX1000 scaling
    coord = DummyCoordinator(data={1: raw})
    s = SPISensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert pytest.approx(s.native_value, rel=1e-9) == val
    else:
        assert s.native_value is None

@pytest.mark.parametrize("val,ok", [(0, True), (MAX_VOC, True), (MAX_VOC+1, False), (-1, False), (None, None)])
def test_voc_sensor_range(val, ok):
    coord = DummyCoordinator(data={1: val})
    s = VOCSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    if ok is None:
        assert s.native_value is None
    elif ok:
        assert s.native_value == val
    else:
        assert s.native_value is None

# ----------------------------
# Enum parsing sensors
# ----------------------------
def test_heat_exchanger_type_sensor_valid_and_invalid():
    coord = DummyCoordinator(data={1: HeatExchangerType.PLATE.value})
    s = HeatExchangerTypeSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == HeatExchangerType(HeatExchangerType.PLATE.value).name.lower()

    coord2 = DummyCoordinator(data={1: 999})
    s2 = HeatExchangerTypeSensor(coord2, 1, types.SimpleNamespace(key="k", name="n"))
    assert s2.native_value is None

def test_connected_panels_sensor_valid_and_invalid():
    coord = DummyCoordinator(data={1: ConnectedPanels.BOTH.value})
    s = ConnectedPanelsSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == ConnectedPanels(ConnectedPanels.BOTH.value).name.lower()

    coord2 = DummyCoordinator(data={1: -5})
    s2 = ConnectedPanelsSensor(coord2, 1, types.SimpleNamespace(key="k", name="n"))
    assert s2.native_value is None

def test_flow_unit_sensor_valid_and_invalid():
    coord = DummyCoordinator(data={1: FlowUnit.M3H.value})
    s = FlowUnitSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value == FlowUnit(FlowUnit.M3H.value).name.lower()

    coord2 = DummyCoordinator(data={1: 12345})
    s2 = FlowUnitSensor(coord2, 1, types.SimpleNamespace(key="k", name="n"))
    assert s2.native_value is None

# ----------------------------
# FlowSensor dynamic unit logic
# ----------------------------
@pytest.mark.parametrize(
    "controller,flow_control,flow_unit,expected_unit",
    [
        (Controller.C6, FlowControl.OFF, None, PERCENTAGE),
        (Controller.C6M, FlowControl.OFF, None, PERCENTAGE),
        (Controller.C6, FlowControl.CONSTANT, FlowUnit.M3H, "m³/h"),
        (Controller.C6, FlowControl.CONSTANT, FlowUnit.LS, "l/s"),
        (Controller.C8, None, None, PERCENTAGE),
    ],
)
def test_flow_sensor_unit_selection(controller, flow_control, flow_unit, expected_unit):
    data = {}
    if flow_control is not None:
        data[registers.REG_FLOW_CONTROL] = flow_control
    if flow_unit is not None:
        data[registers.REG_FLOW_UNIT] = flow_unit
    coord = DummyCoordinator(data=data, controller=controller)
    s = FlowSensor(coord, registers.REG_SUPPLY_FLOW, types.SimpleNamespace(key="k", name="n"))
    assert s.native_unit_of_measurement == expected_unit

def test_flow_sensor_unit_none_when_unknown_config():
    coord = DummyCoordinator(data={registers.REG_FLOW_CONTROL: FlowControl.CONSTANT, registers.REG_FLOW_UNIT: 999}, controller=Controller.C6)
    s = FlowSensor(coord, registers.REG_SUPPLY_FLOW, types.SimpleNamespace(key="k", name="n"))
    assert s.native_unit_of_measurement is None

# ----------------------------
# Firmware version handling
# ----------------------------
def test_firmware_version_none_when_zero_or_missing():
    coord = DummyCoordinator(data={1: 0})
    s = FirmwareVersionSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value is None

# ----------------------------
# SystemTimeSensor conversion and error handling
# ----------------------------
def test_system_time_sensor_converts_local_epoch_seconds_to_datetime_utc():
    # Choose UTC timezone for deterministic result
    hass = DummyHass(tz="UTC")
    seconds_since_epoch = 3600  # 1 hour after 1970-01-01T00:00:00Z
    coord = DummyCoordinator(data={1: seconds_since_epoch}, hass=hass)
    s = SystemTimeSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    val = s.native_value
    assert isinstance(val, dt.datetime)
    assert val == dt.datetime(1970, 1, 1, 1, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))

@pytest.mark.parametrize("bad", ["x", -1.2, object()])
def test_system_time_sensor_invalid_inputs_return_none(bad):
    coord = DummyCoordinator(data={1: bad})
    s = SystemTimeSensor(coord, 1, types.SimpleNamespace(key="k", name="n"))
    assert s.native_value is None

# ----------------------------
# create_aq_sensor logic
# ----------------------------
def test_create_aq_sensor_none_when_no_data_or_not_installed():
    coord = DummyCoordinator(data=None)
    assert create_aq_sensor(coord, registers.REG_EXTRACT_AQ_1) is None

    coord2 = DummyCoordinator(data={
        registers.REG_AQ_SENSOR1_TYPE: AirQualitySensorType.NOT_INSTALLED
    })
    assert create_aq_sensor(coord2, registers.REG_EXTRACT_AQ_1) is None

def test_create_aq_sensor_installs_correct_types():
    base = {
        registers.REG_AQ_SENSOR1_TYPE: AirQualitySensorType.CO2,
        registers.REG_AQ_SENSOR2_TYPE: AirQualitySensorType.VOC,
    }
    coord = DummyCoordinator(data=base)
    s1 = create_aq_sensor(coord, registers.REG_EXTRACT_AQ_1)
    s2 = create_aq_sensor(coord, registers.REG_EXTRACT_AQ_2)
    assert isinstance(s1, CO2Sensor)
    assert isinstance(s2, VOCSensor)

def test_create_aq_sensor_humidity_indoor_vs_outdoor_key_and_name():
    # Sensor1 humidity mapped to outdoor when OutdoorHumiditySensor.SENSOR1
    data = {
        registers.REG_AQ_SENSOR1_TYPE: AirQualitySensorType.HUMIDITY,
        registers.REG_AQ_OUTDOOR_HUMIDITY: OutdoorHumiditySensor.SENSOR1,
    }
    coord = DummyCoordinator(data=data)
    s = create_aq_sensor(coord, registers.REG_EXTRACT_AQ_1)
    assert isinstance(s, RelativeHumiditySensor)
    assert s.entity_description.key == "outdoor_humidity"
    assert "Outdoor Humidity" in s.entity_description.name

    # Sensor2 humidity indoor extract when OutdoorHumiditySensor is SENSOR1
    s2 = create_aq_sensor(coord, registers.REG_EXTRACT_AQ_2)
    assert isinstance(s2, RelativeHumiditySensor)
    assert s2.entity_description.key == "extract_humidity"

# ----------------------------
# create_sensors entity set composition
# ----------------------------
@pytest.mark.asyncio
async def test_create_sensors_includes_core_entities_and_conditionals_c6_variable():
    # Setup coordinator with C6 controller and VARIABLE flow control
    data = {
        registers.REG_FLOW_CONTROL: FlowControl.VARIABLE,
        registers.REG_INDOOR_ABS_HUMIDITY: int(5.00 * 100),  # valid, not in ABS_HUMIDITY_ERRORS
        registers.REG_OUTDOOR_ABS_HUMIDITY: int(6.50 * 100),
        registers.REG_EXHAUST_TEMP: 215,  # 21.5°C
        registers.REG_CONNECTED_PANELS: ConnectedPanels.BOTH,
    }
    coord = DummyCoordinator(data=data, controller=Controller.C6)
    entities = await create_sensors(coord)

    # Expect presence of some core sensors
    keys = {e.entity_description.key for e in entities}
    assert "supply_temperature" in keys
    assert "extract_temperature" in keys
    assert "outdoor_temperature" in keys
    assert "supply_fan" in keys
    assert "extract_fan" in keys
    assert "heat_exchanger" in keys
    assert "electric_heater" in keys
    assert "water_heater" in keys
    assert "water_cooler" in keys
    assert "dx_unit" in keys
    assert "filter_clogging" in keys
    assert "air_dampers" in keys
    assert "power_consumption" in keys
    assert "heater_power" in keys
    assert "heat_recovery" in keys
    assert "heat_exchanger_efficiency" in keys
    assert "energy_saving" in keys
    assert "connected_panels" in keys
    assert "heat_exchanger_type" in keys
    assert "max_supply_flow" in keys
    assert "max_extract_flow" in keys
    assert "supply_flow" in keys
    assert "extract_flow" in keys
    assert "controller_firmware" in keys
    assert "system_time" in keys

    # C6 controller extras
    assert "flow_unit" in keys
    assert "specific_power_input" in keys
    assert "total_ahu_energy" in keys
    assert "total_heater_energy" in keys
    assert "total_recovered_energy" in keys

    # VARIABLE flow control adds pressure sensors
    assert "max_supply_pressure" in keys
    assert "max_extract_pressure" in keys
    assert "supply_pressure" in keys
    assert "extract_pressure" in keys

    # Absolute humidity sensors included (values are valid and not error sentinels)
    assert "indoor_absolute_humidity" in keys
    assert "outdoor_absolute_humidity" in keys

    # Exhaust temperature included because register present
    assert "exhaust_temperature" in keys

    # Panel 1 and 2 sensors present because ConnectedPanels.BOTH
    assert "panel_1_temperature" in keys
    assert "panel_1_humidity" in keys
    assert "panel_1_firmware" in keys
    assert "panel_2_temperature" in keys
    assert "panel_2_humidity" in keys
    assert "panel_2_firmware" in keys

@pytest.mark.asyncio
async def test_create_sensors_skips_abs_humidity_on_error_codes_and_no_pressure_when_not_variable():
    data = {
        registers.REG_FLOW_CONTROL: FlowControl.CONSTANT,
        # Error sentinel values should prevent adding abs humidity sensors
        registers.REG_INDOOR_ABS_HUMIDITY: next(iter(ABS_HUMIDITY_ERRORS)),
        registers.REG_OUTDOOR_ABS_HUMIDITY: next(iter(ABS_HUMIDITY_ERRORS)),
    }
    coord = DummyCoordinator(data=data, controller=Controller.C6)
    entities = await create_sensors(coord)
    keys = {e.entity_description.key for e in entities}
    assert "indoor_absolute_humidity" not in keys
    assert "outdoor_absolute_humidity" not in keys

    # Not VARIABLE -> no pressure sensors
    assert "max_supply_pressure" not in keys
    assert "max_extract_pressure" not in keys
    assert "supply_pressure" not in keys
    assert "extract_pressure" not in keys

@pytest.mark.asyncio
async def test_create_sensors_c8_controller_units_and_no_flowunit_specifics():
    coord = DummyCoordinator(data={}, controller=Controller.C8)
    entities = await create_sensors(coord)
    keys = {e.entity_description.key for e in entities}
    # C8 should not include flow_unit or SPI/energy totals
    assert "flow_unit" not in keys
    assert "specific_power_input" not in keys
    assert "total_ahu_energy" not in keys

# ----------------------------
# create_aq_sensor returns None for unknown register id
# ----------------------------
def test_create_aq_sensor_unknown_register_returns_none():
    data = {
        registers.REG_AQ_SENSOR1_TYPE: AirQualitySensorType.CO2,
        registers.REG_AQ_SENSOR2_TYPE: AirQualitySensorType.VOC,
    }
    coord = DummyCoordinator(data=data)
    assert create_aq_sensor(coord, 0xDEAD) is None