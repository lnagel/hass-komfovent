"""Sensor platform for Komfovent."""

from __future__ import annotations

import zoneinfo
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import get_version_from_int

if TYPE_CHECKING:
    from decimal import Decimal

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import (
    DOMAIN,
    AirQualitySensorType,
    ConnectedPanels,
    Controller,
    FlowControl,
    FlowUnit,
    HeatExchangerType,
    OutdoorHumiditySensor,
)

# Constants for value validation
MIN_DUTY_CYCLE = 0
MAX_DUTY_CYCLE = 100
MIN_TEMPERATURE = -50
MAX_TEMPERATURE = 120
MAX_PERCENTAGE = 100
MAX_HUMIDITY = 125
MIN_ABS_HUMIDITY = 0.01
MAX_ABS_HUMIDITY = 100
MAX_CO2_PPM = 2500
MAX_SPI = 5
MAX_VOC = 125

ABS_HUMIDITY_ERRORS = {65534, 65535}


def create_aq_sensor(
    coordinator: KomfoventCoordinator, register_id: int
) -> KomfoventSensor | None:
    """Create an air quality sensor if installed."""
    if not coordinator.data:
        return None

    if register_id == registers.REG_EXTRACT_AQ_1:
        sensor_type_int = coordinator.data.get(registers.REG_AQ_SENSOR1_TYPE)
    elif register_id == registers.REG_EXTRACT_AQ_2:
        sensor_type_int = coordinator.data.get(registers.REG_AQ_SENSOR2_TYPE)
    else:
        sensor_type_int = AirQualitySensorType.NOT_INSTALLED

    sensor_type = AirQualitySensorType(sensor_type_int)

    if sensor_type == AirQualitySensorType.NOT_INSTALLED:
        return None

    if sensor_type == AirQualitySensorType.CO2:
        key = "extract_co2"
        name = "Extract CO2"
        sensor_class = CO2Sensor
        unit = CONCENTRATION_PARTS_PER_MILLION
        device_class = SensorDeviceClass.CO2
    elif sensor_type == AirQualitySensorType.VOC:
        key = "extract_voc"
        name = "Extract VOC"
        sensor_class = VOCSensor
        unit = PERCENTAGE
        device_class = None
    elif sensor_type == AirQualitySensorType.HUMIDITY:
        outdoor_humidity_sensor = coordinator.data.get(
            registers.REG_AQ_OUTDOOR_HUMIDITY
        )
        is_outdoor = (
            register_id == registers.REG_EXTRACT_AQ_1
            and outdoor_humidity_sensor == OutdoorHumiditySensor.SENSOR1
        ) or (
            register_id == registers.REG_EXTRACT_AQ_2
            and outdoor_humidity_sensor == OutdoorHumiditySensor.SENSOR2
        )

        if is_outdoor:
            key = "outdoor_humidity"
            name = "Outdoor Humidity"
        else:
            key = "extract_humidity"
            name = "Extract Humidity"

        sensor_class = RelativeHumiditySensor
        unit = PERCENTAGE
        device_class = SensorDeviceClass.HUMIDITY
    else:
        return None

    return sensor_class(
        coordinator=coordinator,
        register_id=register_id,
        entity_description=SensorEntityDescription(
            key=key,
            name=name,
            native_unit_of_measurement=unit,
            device_class=device_class,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=0,
        ),
    )


async def create_sensors(coordinator: KomfoventCoordinator) -> list[KomfoventSensor]:
    """Get list of sensor entities."""
    entities = []

    # Add core sensors
    entities.extend(
        [
            TemperatureSensor(
                coordinator=coordinator,
                register_id=registers.REG_SUPPLY_TEMP,
                entity_description=SensorEntityDescription(
                    key="supply_temperature",
                    name="Supply Temperature",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=1,
                ),
            ),
            TemperatureSensor(
                coordinator=coordinator,
                register_id=registers.REG_EXTRACT_TEMP,
                entity_description=SensorEntityDescription(
                    key="extract_temperature",
                    name="Extract Temperature",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=1,
                ),
            ),
            TemperatureSensor(
                coordinator=coordinator,
                register_id=registers.REG_OUTDOOR_TEMP,
                entity_description=SensorEntityDescription(
                    key="outdoor_temperature",
                    name="Outdoor Temperature",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=1,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_SUPPLY_FAN,
                entity_description=SensorEntityDescription(
                    key="supply_fan",
                    name="Supply Fan",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_EXTRACT_FAN,
                entity_description=SensorEntityDescription(
                    key="extract_fan",
                    name="Extract Fan",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_HEAT_EXCHANGER,
                entity_description=SensorEntityDescription(
                    key="heat_exchanger",
                    name="Heat Exchanger",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_ELECTRIC_HEATER,
                entity_description=SensorEntityDescription(
                    key="electric_heater",
                    name="Electric Heater",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_WATER_HEATER,
                entity_description=SensorEntityDescription(
                    key="water_heater",
                    name="Water Heater",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_registry_enabled_default=False,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_WATER_COOLER,
                entity_description=SensorEntityDescription(
                    key="water_cooler",
                    name="Water Cooler",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_registry_enabled_default=False,
                ),
            ),
            DutyCycleSensor(
                coordinator=coordinator,
                register_id=registers.REG_DX_UNIT,
                entity_description=SensorEntityDescription(
                    key="dx_unit",
                    name="DX Unit",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_FILTER_CLOGGING,
                entity_description=SensorEntityDescription(
                    key="filter_clogging",
                    name="Filter Clogging",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_AIR_DAMPERS,
                entity_description=SensorEntityDescription(
                    key="air_dampers",
                    name="Air Dampers",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_POWER_CONSUMPTION,
                entity_description=SensorEntityDescription(
                    key="power_consumption",
                    name="Power Consumption",
                    native_unit_of_measurement=UnitOfPower.WATT,
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_HEATER_POWER,
                entity_description=SensorEntityDescription(
                    key="heater_power",
                    name="Heater Power",
                    native_unit_of_measurement=UnitOfPower.WATT,
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_HEAT_RECOVERY,
                entity_description=SensorEntityDescription(
                    key="heat_recovery",
                    name="Heat Recovery",
                    native_unit_of_measurement=UnitOfPower.WATT,
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_HEAT_EFFICIENCY,
                entity_description=SensorEntityDescription(
                    key="heat_exchanger_efficiency",
                    name="Heat Exchanger Efficiency",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_ENERGY_SAVING,
                entity_description=SensorEntityDescription(
                    key="energy_saving",
                    name="Energy Saving",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_registry_enabled_default=False,
                ),
            ),
            ConnectedPanelsSensor(
                coordinator=coordinator,
                register_id=registers.REG_CONNECTED_PANELS,
                entity_description=SensorEntityDescription(
                    key="connected_panels",
                    name="Connected Panels",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_registry_enabled_default=False,
                ),
            ),
            HeatExchangerTypeSensor(
                coordinator=coordinator,
                register_id=registers.REG_HEAT_EXCHANGER_TYPE,
                entity_description=SensorEntityDescription(
                    key="heat_exchanger_type",
                    name="Heat Exchanger Type",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_registry_enabled_default=False,
                ),
            ),
            FlowSensor(
                coordinator=coordinator,
                register_id=registers.REG_MAX_SUPPLY_FLOW,
                entity_description=SensorEntityDescription(
                    key="max_supply_flow",
                    name="Maximum Supply Flow",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_registry_enabled_default=False,
                ),
            ),
            FlowSensor(
                coordinator=coordinator,
                register_id=registers.REG_MAX_EXTRACT_FLOW,
                entity_description=SensorEntityDescription(
                    key="max_extract_flow",
                    name="Maximum Extract Flow",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_registry_enabled_default=False,
                ),
            ),
            FlowSensor(
                coordinator=coordinator,
                register_id=registers.REG_SUPPLY_FLOW,
                entity_description=SensorEntityDescription(
                    key="supply_flow",
                    name="Supply Flow",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            FlowSensor(
                coordinator=coordinator,
                register_id=registers.REG_EXTRACT_FLOW,
                entity_description=SensorEntityDescription(
                    key="extract_flow",
                    name="Extract Flow",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            FirmwareVersionSensor(
                coordinator=coordinator,
                register_id=registers.REG_FIRMWARE,
                entity_description=SensorEntityDescription(
                    key="controller_firmware",
                    name="Controller firmware",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            SystemTimeSensor(
                coordinator=coordinator,
                register_id=registers.REG_EPOCH_TIME,
                entity_description=SensorEntityDescription(
                    key="system_time",
                    name="System Time",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    device_class=SensorDeviceClass.TIMESTAMP,
                    entity_registry_enabled_default=False,
                ),
            ),
        ]
    )

    # Flow, SPI and total energy counters only available on C6 and C6M controllers
    if coordinator.controller in {Controller.C6, Controller.C6M}:
        entities.extend(
            [
                FlowUnitSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_FLOW_UNIT,
                    entity_description=SensorEntityDescription(
                        key="flow_unit",
                        name="Flow Unit",
                        entity_category=EntityCategory.DIAGNOSTIC,
                        entity_registry_enabled_default=False,
                    ),
                ),
                SPISensor(
                    coordinator=coordinator,
                    register_id=registers.REG_SPI,
                    entity_description=SensorEntityDescription(
                        key="specific_power_input",
                        name="Specific Power Input",
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=2,
                    ),
                ),
                FloatX1000Sensor(
                    coordinator=coordinator,
                    register_id=registers.REG_AHU_TOTAL,
                    entity_description=SensorEntityDescription(
                        key="total_ahu_energy",
                        name="Total AHU Energy",
                        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                        device_class=SensorDeviceClass.ENERGY,
                        state_class=SensorStateClass.TOTAL_INCREASING,
                        suggested_display_precision=3,
                    ),
                ),
                FloatX1000Sensor(
                    coordinator=coordinator,
                    register_id=registers.REG_HEATER_TOTAL,
                    entity_description=SensorEntityDescription(
                        key="total_heater_energy",
                        name="Total Heater Energy",
                        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                        device_class=SensorDeviceClass.ENERGY,
                        state_class=SensorStateClass.TOTAL_INCREASING,
                        suggested_display_precision=3,
                    ),
                ),
                FloatX1000Sensor(
                    coordinator=coordinator,
                    register_id=registers.REG_RECOVERY_TOTAL,
                    entity_description=SensorEntityDescription(
                        key="total_recovered_energy",
                        name="Total Recovered Energy",
                        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                        device_class=SensorDeviceClass.ENERGY,
                        state_class=SensorStateClass.TOTAL_INCREASING,
                        suggested_display_precision=3,
                    ),
                ),
            ]
        )

    # Add pressure sensors if using a flow control mode is variable air volume
    if coordinator.data and coordinator.data.get(registers.REG_FLOW_CONTROL) in [
        FlowControl.VARIABLE
    ]:
        entities.extend(
            [
                KomfoventSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_MAX_SUPPLY_PRESSURE,
                    entity_description=SensorEntityDescription(
                        key="max_supply_pressure",
                        name="Maximum Supply Pressure",
                        native_unit_of_measurement=UnitOfPressure.PA,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=0,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ),
                KomfoventSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_MAX_EXTRACT_PRESSURE,
                    entity_description=SensorEntityDescription(
                        key="max_extract_pressure",
                        name="Maximum Extract Pressure",
                        native_unit_of_measurement=UnitOfPressure.PA,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=0,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ),
                KomfoventSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_SUPPLY_PRESSURE,
                    entity_description=SensorEntityDescription(
                        key="supply_pressure",
                        name="Supply Pressure",
                        native_unit_of_measurement=UnitOfPressure.PA,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=0,
                    ),
                ),
                KomfoventSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_EXTRACT_PRESSURE,
                    entity_description=SensorEntityDescription(
                        key="extract_pressure",
                        name="Extract Pressure",
                        native_unit_of_measurement=UnitOfPressure.PA,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=0,
                    ),
                ),
            ]
        )

    # Add indoor absolute humidity if value indicates sensor is present
    indoor_humidity = coordinator.data.get(registers.REG_INDOOR_ABS_HUMIDITY)
    if indoor_humidity is not None and indoor_humidity not in ABS_HUMIDITY_ERRORS:
        entities.extend(
            [
                AbsoluteHumiditySensor(
                    coordinator=coordinator,
                    register_id=registers.REG_INDOOR_ABS_HUMIDITY,
                    entity_description=SensorEntityDescription(
                        key="indoor_absolute_humidity",
                        name="Indoor Absolute Humidity",
                        native_unit_of_measurement="g/m³",
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=2,
                    ),
                ),
            ]
        )

    # Add outdoor absolute humidity if value indicates sensor is present
    outdoor_humidity = coordinator.data.get(registers.REG_OUTDOOR_ABS_HUMIDITY)
    if outdoor_humidity is not None and outdoor_humidity not in ABS_HUMIDITY_ERRORS:
        entities.extend(
            [
                AbsoluteHumiditySensor(
                    coordinator=coordinator,
                    register_id=registers.REG_OUTDOOR_ABS_HUMIDITY,
                    entity_description=SensorEntityDescription(
                        key="outdoor_absolute_humidity",
                        name="Outdoor Absolute Humidity",
                        native_unit_of_measurement="g/m³",
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=2,
                    ),
                ),
            ]
        )

    # Add exhaust temperature if value is present
    if coordinator.data and registers.REG_EXHAUST_TEMP in coordinator.data:
        entities.extend(
            [
                TemperatureSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_EXHAUST_TEMP,
                    entity_description=SensorEntityDescription(
                        key="exhaust_temperature",
                        name="Exhaust Temperature",
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        device_class=SensorDeviceClass.TEMPERATURE,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=1,
                    ),
                ),
            ]
        )

    # Add panel 1 sensors if panel is present
    if coordinator.data and coordinator.data.get(registers.REG_CONNECTED_PANELS) in [
        ConnectedPanels.PANEL1,
        ConnectedPanels.BOTH,
    ]:
        entities.extend(
            [
                TemperatureSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_PANEL1_TEMP,
                    entity_description=SensorEntityDescription(
                        key="panel_1_temperature",
                        name="Panel 1 Temperature",
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        device_class=SensorDeviceClass.TEMPERATURE,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=1,
                    ),
                ),
                RelativeHumiditySensor(
                    coordinator=coordinator,
                    register_id=registers.REG_PANEL1_RH,
                    entity_description=SensorEntityDescription(
                        key="panel_1_humidity",
                        name="Panel 1 Humidity",
                        native_unit_of_measurement=PERCENTAGE,
                        device_class=SensorDeviceClass.HUMIDITY,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=0,
                    ),
                ),
                FirmwareVersionSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_PANEL1_FW,
                    entity_description=SensorEntityDescription(
                        key="panel_1_firmware",
                        name="Panel 1 firmware",
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ),
            ]
        )

    # Add panel 2 sensors if panel is present
    if coordinator.data and coordinator.data.get(registers.REG_CONNECTED_PANELS) in [
        ConnectedPanels.PANEL2,
        ConnectedPanels.BOTH,
    ]:
        entities.extend(
            [
                TemperatureSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_PANEL2_TEMP,
                    entity_description=SensorEntityDescription(
                        key="panel_2_temperature",
                        name="Panel 2 Temperature",
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        device_class=SensorDeviceClass.TEMPERATURE,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=1,
                    ),
                ),
                RelativeHumiditySensor(
                    coordinator=coordinator,
                    register_id=registers.REG_PANEL2_RH,
                    entity_description=SensorEntityDescription(
                        key="panel_2_humidity",
                        name="Panel 2 Humidity",
                        native_unit_of_measurement=PERCENTAGE,
                        device_class=SensorDeviceClass.HUMIDITY,
                        state_class=SensorStateClass.MEASUREMENT,
                        suggested_display_precision=0,
                    ),
                ),
                FirmwareVersionSensor(
                    coordinator=coordinator,
                    register_id=registers.REG_PANEL2_FW,
                    entity_description=SensorEntityDescription(
                        key="panel_2_firmware",
                        name="Panel 2 firmware",
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                ),
            ]
        )

    # Add AQ sensors if installed
    if aq_sensor := create_aq_sensor(coordinator, registers.REG_EXTRACT_AQ_1):
        entities.append(aq_sensor)
    if aq_sensor := create_aq_sensor(coordinator, registers.REG_EXTRACT_AQ_2):
        entities.append(aq_sensor)

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Komfovent sensors."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(await create_sensors(coordinator))


class KomfoventSensor(CoordinatorEntity, SensorEntity):
    """Base representation of a Komfovent sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.register_id = register_id
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": "Komfovent",
            "model": None,
        }

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        return self.coordinator.data.get(self.register_id)


class FloatSensor(KomfoventSensor):
    """Temperature sensor with x10 scaling."""

    @property
    def native_value(self) -> StateType:
        """Return the float value of the sensor."""
        value = super().native_value
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class FloatX10Sensor(FloatSensor):
    """Sensor that divides its value by 10."""

    @property
    def native_value(self) -> StateType:
        """Return the sensor value divided by 10."""
        value = super().native_value
        if value is None:
            return None

        return value / 10


class FloatX100Sensor(FloatSensor):
    """Sensor that divides its value by 100."""

    @property
    def native_value(self) -> StateType:
        """Return the value divided by 100."""
        value = super().native_value
        if value is None:
            return None

        return value / 100


class FloatX1000Sensor(KomfoventSensor):
    """Sensor that divides its value by 1000."""

    @property
    def native_value(self) -> StateType:
        """Return the energy value in kWh."""
        value = super().native_value
        if value is None:
            return None

        return value / 1000


class FirmwareVersionSensor(KomfoventSensor):
    """Firmware version sensor."""

    @property
    def native_value(self) -> StateType:
        """Return the firmware version string."""
        value = super().native_value
        if value is None:
            return None

        if value == 0:
            return None

        controller, v1, v2, v3, v4 = get_version_from_int(value)
        return f"{controller.name} {v1}.{v2}.{v3}.{v4}"


class DutyCycleSensor(FloatX10Sensor):
    """Temperature sensor with range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the temperature value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if MIN_DUTY_CYCLE <= value <= MAX_DUTY_CYCLE:
            return value
        return None


class TemperatureSensor(FloatX10Sensor):
    """Temperature sensor with range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the temperature value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if MIN_TEMPERATURE <= value <= MAX_TEMPERATURE:
            return value
        return None


class RelativeHumiditySensor(KomfoventSensor):
    """Humidity sensor with range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the humidity value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if 0 <= value <= MAX_HUMIDITY:
            return value
        return None


class AbsoluteHumiditySensor(FloatX100Sensor):
    """Humidity sensor with range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the humidity value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if MIN_ABS_HUMIDITY <= value <= MAX_ABS_HUMIDITY:
            return value
        return None


class CO2Sensor(KomfoventSensor):
    """CO2 sensor with range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the CO2 value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if 0 <= value <= MAX_CO2_PPM:
            return value
        return None


class SPISensor(FloatX1000Sensor):
    """SPI sensor with scaling and range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the SPI value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if 0 <= value <= MAX_SPI:
            return value
        return None


class VOCSensor(KomfoventSensor):
    """VOC sensor with range validation."""

    @property
    def native_value(self) -> StateType:
        """Return the VOC value if within valid range."""
        value = super().native_value
        if value is None:
            return None

        if 0 <= value <= MAX_VOC:
            return value
        return None


class FlowSensor(FloatSensor):
    """Flow sensor with dynamic units based on flow unit setting."""

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if not self.coordinator.data:
            return None

        if self.coordinator.controller in {Controller.C6, Controller.C6M}:
            flow_control = self.coordinator.data.get(registers.REG_FLOW_CONTROL)
            if flow_control == FlowControl.OFF:
                return PERCENTAGE

            flow_unit = self.coordinator.data.get(registers.REG_FLOW_UNIT)
            if flow_unit == FlowUnit.M3H:
                return UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
            if flow_unit == FlowUnit.LS:
                return UnitOfVolumeFlowRate.LITERS_PER_SECOND
        elif self.coordinator.controller in {Controller.C8}:
            # no flow control or flow unit support
            return PERCENTAGE

        return None


class HeatExchangerTypeSensor(KomfoventSensor):
    """Heat exchanger type sensor."""

    @property
    def native_value(self) -> StateType:
        """Return the heat exchanger type name."""
        value = super().native_value
        if value is None:
            return None

        try:
            return HeatExchangerType(value).name.lower()
        except ValueError:
            return None


class ConnectedPanelsSensor(KomfoventSensor):
    """Connected panels sensor."""

    @property
    def native_value(self) -> StateType:
        """Return the connected panels state name."""
        value = super().native_value
        if value is None:
            return None

        try:
            return ConnectedPanels(value).name.lower()
        except ValueError:
            return None


class FlowUnitSensor(KomfoventSensor):
    """Flow unit sensor."""

    @property
    def native_value(self) -> StateType:
        """Return the flow units state name."""
        value = super().native_value
        if value is None:
            return None

        try:
            return FlowUnit(value).name.lower()
        except ValueError:
            return None


class SystemTimeSensor(KomfoventSensor):
    """System time sensor."""

    @property
    def native_value(self) -> StateType:
        """Return the system time as datetime from Unix timestamp."""
        value = super().native_value
        if value is None:
            return None

        try:
            # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
            local_tz = zoneinfo.ZoneInfo(str(self.coordinator.hass.config.time_zone))
            local_epoch = datetime(1970, 1, 1, tzinfo=local_tz)

            # Convert seconds since local epoch to datetime
            return local_epoch + timedelta(seconds=value)
        except (ValueError, TypeError, OSError):
            return None
