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
    POWER_WATT,
    ENERGY_KILO_WATT_HOUR,
    VOLUME_FLOW_RATE_CUBIC_METERS_PER_HOUR,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    AQ_SENSOR_TYPES,
    AQ_SENSOR_TYPE_NOT_INSTALLED,
    AQ_SENSOR_TYPE_CO2,
    AQ_SENSOR_TYPE_VOC,
    AQ_SENSOR_TYPE_RH,
)
from .coordinator import KomfoventCoordinator

def create_aq_sensor(coordinator: KomfoventCoordinator, sensor_num: int) -> KomfoventSensor | None:
    """Create an air quality sensor if installed."""
    sensor_type_key = f"aq_sensor{sensor_num}_type"
    sensor_value_key = f"aq_sensor{sensor_num}_value"
    
    if not coordinator.data:
        return None
        
    sensor_type = coordinator.data.get(sensor_type_key, AQ_SENSOR_TYPE_NOT_INSTALLED)
    if sensor_type == AQ_SENSOR_TYPE_NOT_INSTALLED:
        return None
        
    name = f"Air Quality {AQ_SENSOR_TYPES.get(sensor_type, 'Unknown')}"
    
    if sensor_type == AQ_SENSOR_TYPE_CO2:
        unit, device_class = "ppm", SensorDeviceClass.CO2
    elif sensor_type == AQ_SENSOR_TYPE_VOC:
        unit, device_class = "ppb", None
    elif sensor_type == AQ_SENSOR_TYPE_RH:
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
    "supply_temp": ("Supply Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "extract_temp": ("Extract Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "outdoor_temp": ("Outdoor Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "supply_flow": ("Supply Flow", VOLUME_FLOW_RATE_CUBIC_METERS_PER_HOUR, None),
    "extract_flow": ("Extract Flow", VOLUME_FLOW_RATE_CUBIC_METERS_PER_HOUR, None),
    "supply_fan_intensity": ("Supply Fan Intensity", PERCENTAGE, None),
    "extract_fan_intensity": ("Extract Fan Intensity", PERCENTAGE, None),
    "heat_exchanger": ("Heat Exchanger", PERCENTAGE, None),
    "electric_heater": ("Electric Heater", PERCENTAGE, None),
    "filter_impurity": ("Filter Impurity", PERCENTAGE, None),
    "power_consumption": ("Power Consumption", POWER_WATT, SensorDeviceClass.POWER),
    "heater_power": ("Heater Power", POWER_WATT, SensorDeviceClass.POWER),
    "heat_recovery": ("Heat Recovery", POWER_WATT, SensorDeviceClass.POWER),
    "heat_efficiency": ("Heat Exchanger Efficiency", PERCENTAGE, None),
    "spi": ("Specific Power Input", None, None),
    "panel1_temp": ("Panel 1 Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "panel1_rh": ("Panel 1 Humidity", PERCENTAGE, SensorDeviceClass.HUMIDITY),
    "extract_co2": ("Extract Air CO2", "ppm", SensorDeviceClass.CO2),
    "extract_rh": ("Extract Air Humidity", PERCENTAGE, SensorDeviceClass.HUMIDITY),
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
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{DOMAIN}_device")},
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
