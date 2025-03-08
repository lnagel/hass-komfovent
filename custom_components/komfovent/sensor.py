"""Sensor platform for Komfovent."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers
from .const import (
    DOMAIN,
    AirQualitySensorType,
    ConnectedPanels,
    HeatExchangerType,
)
from .coordinator import KomfoventCoordinator

X100_FIELDS = {
    registers.REG_INDOOR_ABS_HUMIDITY,
}

# Fields that need to be converted from Wh to kWh (divide by 1000)
WH_TO_KWH_FIELDS = {
    registers.REG_AHU_TOTAL,
    registers.REG_HEATER_TOTAL,
    registers.REG_RECOVERY_TOTAL,
}

X10_PERCENTAGE_FIELDS = {
    registers.REG_SUPPLY_FAN_INTENSITY,
    registers.REG_EXTRACT_FAN_INTENSITY,
    registers.REG_HEAT_EXCHANGER,
    registers.REG_ELECTRIC_HEATER,
    registers.REG_WATER_HEATER,
    registers.REG_WATER_COOLER,
    registers.REG_DX_UNIT,
}


def create_aq_sensor(
    coordinator: KomfoventCoordinator, register_id: int
) -> KomfoventSensor | None:
    """Create an air quality sensor if installed."""
    if not coordinator.data:
        return None

    if register_id == registers.REG_AQ_SENSOR1_VALUE:
        sensor_type_int = coordinator.data.get(
            registers.REG_AQ_SENSOR1_TYPE, AirQualitySensorType.NOT_INSTALLED
        )
    elif register_id == registers.REG_AQ_SENSOR2_VALUE:
        sensor_type_int = coordinator.data.get(
            registers.REG_AQ_SENSOR2_TYPE, AirQualitySensorType.NOT_INSTALLED
        )
    else:
        sensor_type_int = AirQualitySensorType.NOT_INSTALLED

    sensor_type = AirQualitySensorType(sensor_type_int)

    if sensor_type == AirQualitySensorType.NOT_INSTALLED:
        return None

    name = f"Air Quality {sensor_type.name.upper()}"

    if sensor_type == AirQualitySensorType.CO2:
        unit, device_class = "ppm", SensorDeviceClass.CO2
    elif sensor_type == AirQualitySensorType.VOC:
        unit, device_class = "ppb", None
    elif sensor_type == AirQualitySensorType.RH:
        unit, device_class = PERCENTAGE, SensorDeviceClass.HUMIDITY
    else:
        return None

    return KomfoventSensor(
        coordinator=coordinator,
        register_id=register_id,
        entity_description=SensorEntityDescription(
            key=f"aq_sensor_{register_id}",
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
            KomfoventSensor(
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
            KomfoventSensor(
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
            KomfoventSensor(
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
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_SUPPLY_FAN_INTENSITY,
                entity_description=SensorEntityDescription(
                    key="supply_fan_intensity",
                    name="Supply Fan Intensity",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_EXTRACT_FAN_INTENSITY,
                entity_description=SensorEntityDescription(
                    key="extract_fan_intensity",
                    name="Extract Fan Intensity",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
                ),
            ),
            KomfoventSensor(
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
            KomfoventSensor(
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
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_FILTER_IMPURITY,
                entity_description=SensorEntityDescription(
                    key="filter_impurity",
                    name="Filter Impurity",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=0,
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
                register_id=registers.REG_SPI,
                entity_description=SensorEntityDescription(
                    key="specific_power_input",
                    name="Specific Power Input",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=2,
                ),
            ),
            KomfoventSensor(
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
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_CONNECTED_PANELS,
                entity_description=SensorEntityDescription(
                    key="connected_panels",
                    name="Connected Panels",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_HEAT_EXCHANGER_TYPE,
                entity_description=SensorEntityDescription(
                    key="heat_exchanger_type",
                    name="Heat Exchanger Type",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            KomfoventSensor(
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
            KomfoventSensor(
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
            KomfoventSensor(
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
            KomfoventSensor(
                coordinator=coordinator,
                register_id=registers.REG_FIRMWARE,
                entity_description=SensorEntityDescription(
                    key="controller_firmware",
                    name="Controller firmware",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
        ]
    )

    # Add panel 1 sensors if panel is present
    if coordinator.data and coordinator.data.get(registers.REG_CONNECTED_PANELS, 0) in [
        ConnectedPanels.PANEL1,
        ConnectedPanels.BOTH,
    ]:
        entities.extend(
            [
                KomfoventSensor(
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
                KomfoventSensor(
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
                KomfoventSensor(
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
    if coordinator.data and coordinator.data.get(registers.REG_CONNECTED_PANELS, 0) in [
        ConnectedPanels.PANEL2,
        ConnectedPanels.BOTH,
    ]:
        entities.extend(
            [
                KomfoventSensor(
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
                KomfoventSensor(
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
                KomfoventSensor(
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
    if aq_sensor := create_aq_sensor(coordinator, registers.REG_AQ_SENSOR1_VALUE):
        entities.append(aq_sensor)
    if aq_sensor := create_aq_sensor(coordinator, registers.REG_AQ_SENSOR2_VALUE):
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
    """Representation of a Komfovent sensor."""

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
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{register_id}"
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

        value = self.coordinator.data.get(self.register_id)
        if value is None:
            return None

        try:
            # Apply transforms based on sensor type and register format
            if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
                # All temperatures are x10 in Modbus registers
                if isinstance(value, (int, float)):
                    return float(value) / 10
                return None
            if self.register_id in X10_PERCENTAGE_FIELDS:
                # These percentage fields are stored as actual value * 10
                if isinstance(value, (int, float)):
                    value = float(value) / 10
                    if 0 <= value <= 100:
                        return value
                return None
            if self.register_id in X100_FIELDS:
                if isinstance(value, (int, float)):
                    return float(value) / 100
                return None
            if self.register_id in WH_TO_KWH_FIELDS:
                if isinstance(value, (int, float)):
                    return float(value) / 1000  # Convert Wh to kWh
                return None
            if self.register_id in {
                registers.REG_FIRMWARE,
                registers.REG_PANEL1_FW,
                registers.REG_PANEL2_FW,
            }:
                if isinstance(value, int):
                    # Extract version numbers using bit shifts
                    v1 = (value >> 24) & 0xFF  # First number (8 bits)
                    v2 = (value >> 20) & 0xF  # Second number (4 bits)
                    v3 = (value >> 12) & 0xFF  # Third number (8 bits)
                    v4 = value & 0xFFF  # Fourth number (12 bits)
                    if any([v1, v2, v3, v4]):
                        return f"{v1}.{v2}.{v3}.{v4}"
                return None
            if self.entity_description.device_class == SensorDeviceClass.HUMIDITY:
                # Validate RH values (0-125%)
                if 0 <= float(value) <= 125:
                    return float(value)
                return None
            if self.entity_description.device_class == SensorDeviceClass.CO2:
                # Validate CO2 values (0-2500 ppm)
                if 0 <= float(value) <= 2500:
                    return float(value)
                return None
            if self.register_id == registers.REG_SPI:
                # Validate SPI values (0-5)
                value = float(value) / 1000
                if 0 <= value <= 5:
                    return value
                return None
            if self.entity_description.native_unit_of_measurement == "ppb":  # VOC
                if not isinstance(value, (int, float)):
                    return None
                value = float(value)
                if 0 <= value <= 2000:
                    return value
                return None
            if self.register_id == registers.REG_HEAT_EXCHANGER_TYPE:
                try:
                    return HeatExchangerType(value).name
                except ValueError:
                    return None
            if self.register_id == registers.REG_CONNECTED_PANELS:
                try:
                    return ConnectedPanels(value).name
                except ValueError:
                    return None

            return float(value)
        except (ValueError, TypeError):
            return None
