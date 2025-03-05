"""Sensor platform for Komfovent."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    AirQualitySensorType,
)
from .coordinator import KomfoventCoordinator


X100_FIELDS = {
    registers.REG_INDOOR_ABS_HUMIDITY,
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

def create_aq_sensor(coordinator: KomfoventCoordinator, sensor_num: int) -> KomfoventSensor | None:
    """Create an air quality sensor if installed."""
    sensor_type_key = f"aq_sensor{sensor_num}_type"
    sensor_value_key = f"aq_sensor{sensor_num}_value"
    
    if not coordinator.data:
        return None
        
    sensor_type_reg = registers.REG_AQ_SENSOR1_TYPE if sensor_num == 1 else registers.REG_AQ_SENSOR2_TYPE
    sensor_type_int = coordinator.data.get(sensor_type_reg, AirQualitySensorType.NOT_INSTALLED)
    try:
        sensor_type = AirQualitySensorType(sensor_type_int)
    except ValueError:
        return None
        
    if sensor_type == AirQualitySensorType.NOT_INSTALLED:
        return None
        
    name = f"Air Quality {sensor_type.name.title()}"
    
    if sensor_type == AirQualitySensorType.CO2:
        unit, device_class = "ppm", SensorDeviceClass.CO2
    elif sensor_type == AirQualitySensorType.VOC:
        unit, device_class = "ppb", None
    elif sensor_type == AirQualitySensorType.RH:
        unit, device_class = PERCENTAGE, SensorDeviceClass.HUMIDITY
    else:
        return None
        
    return KomfoventSensor(
        coordinator,
        sensor_value_key,
        name,
        unit,
        device_class,
    )

SENSOR_TYPES = {
    registers.REG_SUPPLY_TEMP: ("Supply Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    registers.REG_EXTRACT_TEMP: ("Extract Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    registers.REG_OUTDOOR_TEMP: ("Outdoor Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    registers.REG_SUPPLY_FLOW: ("Supply Flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, None),
    registers.REG_EXTRACT_FLOW: ("Extract Flow", UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, None),
    registers.REG_SUPPLY_FAN_INTENSITY: ("Supply Fan Intensity", PERCENTAGE, None),
    registers.REG_EXTRACT_FAN_INTENSITY: ("Extract Fan Intensity", PERCENTAGE, None),
    registers.REG_HEAT_EXCHANGER: ("Heat Exchanger", PERCENTAGE, None),
    registers.REG_ELECTRIC_HEATER: ("Electric Heater", PERCENTAGE, None),
    registers.REG_FILTER_IMPURITY: ("Filter Impurity", PERCENTAGE, None),
    registers.REG_POWER_CONSUMPTION: ("Power Consumption", UnitOfPower.WATT, SensorDeviceClass.POWER),
    registers.REG_HEATER_POWER: ("Heater Power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    registers.REG_HEAT_RECOVERY: ("Heat Recovery", UnitOfPower.WATT, SensorDeviceClass.POWER),
    registers.REG_HEAT_EFFICIENCY: ("Heat Exchanger Efficiency", PERCENTAGE, None),
    registers.REG_SPI: ("Specific Power Input", None, None),
    registers.REG_PANEL1_TEMP: ("Panel 1 Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    registers.REG_PANEL1_RH: ("Panel 1 Humidity", PERCENTAGE, SensorDeviceClass.HUMIDITY),
    registers.REG_INDOOR_ABS_HUMIDITY: ("Indoor Absolute Humidity", "g/m³", None),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Komfovent sensors."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Create standard sensors
    for sensor_type, (name, unit, device_class) in SENSOR_TYPES.items():
        entities.append(
                KomfoventSensor(
                    coordinator,
                    sensor_type,
                    name,
                    unit,
                    device_class,
                )
            )

    # Add AQ sensors if installed
    if aq_sensor := create_aq_sensor(coordinator, 1):
        entities.append(aq_sensor)
    if aq_sensor := create_aq_sensor(coordinator, 2):
        entities.append(aq_sensor)

    async_add_entities(entities)

class KomfoventSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Komfovent sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        sensor_type: str,
        name: str,
        unit: str | None,
        device_class: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Komfovent Ventilation",
            "manufacturer": "Komfovent",
            "model": "Modbus",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        try:
            if not self.coordinator.data:
                return None
                
            value = self.coordinator.data.get(self._sensor_type)
            if value is None:
                return None

            # Apply transforms based on sensor type and register format
            if self._attr_device_class == SensorDeviceClass.TEMPERATURE:
                # All temperatures are x10 in Modbus registers
                if isinstance(value, (int, float)):
                    return float(value) / 10
                return None
            elif self._sensor_type in X10_PERCENTAGE_FIELDS:
                # These percentage fields are stored as actual value * 10
                if isinstance(value, (int, float)):
                    value = float(value) / 10
                    if 0 <= value <= 100:
                        return value
                return None
            elif self._sensor_type in X100_FIELDS:
                if isinstance(value, (int, float)):
                    return float(value) / 100
                return None
            elif self._attr_device_class == SensorDeviceClass.HUMIDITY:
                # Validate RH values (0-125%)
                if 0 <= float(value) <= 125:
                    return float(value)
                return None
            elif self._attr_device_class == SensorDeviceClass.CO2:
                # Validate CO2 values (0-2500 ppm)
                if 0 <= float(value) <= 2500:
                    return float(value)
                return None
            elif self._sensor_type == "spi":
                # Validate SPI values (0-5)
                value = float(value) / 1000
                if 0 <= value <= 5:
                    return value
                return None
            elif self._sensor_type in ["aq_sensor1_value", "aq_sensor2_value"]:
                if not isinstance(value, (int, float)):
                    return None
                value = float(value)
                
                # Only validate VOC values, CO2 and humidity are handled above
                if self._attr_native_unit_of_measurement == "ppb":  # VOC
                    if 0 <= value <= 2000:
                        return value
                    return None
                return value
                
            return float(value)
        except (ValueError, TypeError):
            return None
