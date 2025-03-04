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
    TEMP_CELSIUS,
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

def get_aq_sensor_attributes(sensor_type: int) -> tuple[str | None, str | None]:
    """Get the unit and device class for an air quality sensor type."""
    if sensor_type == AQ_SENSOR_TYPE_CO2:
        return "ppm", SensorDeviceClass.CO2
    elif sensor_type == AQ_SENSOR_TYPE_VOC:
        return "ppb", None
    elif sensor_type == AQ_SENSOR_TYPE_RH:
        return PERCENTAGE, SensorDeviceClass.HUMIDITY
    return None, None

SENSOR_TYPES = {
    "supply_temp": ("Supply Temperature", TEMP_CELSIUS, SensorDeviceClass.TEMPERATURE),
    "extract_temp": ("Extract Temperature", TEMP_CELSIUS, SensorDeviceClass.TEMPERATURE),
    "outdoor_temp": ("Outdoor Temperature", TEMP_CELSIUS, SensorDeviceClass.TEMPERATURE),
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
    "panel1_temp": ("Panel 1 Temperature", TEMP_CELSIUS, SensorDeviceClass.TEMPERATURE),
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
        # Skip AQ sensors - we'll handle them separately
        if sensor_type not in ["aq_sensor1_value", "aq_sensor2_value"]:
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
    if coordinator.data:
        # Sensor 1
        if coordinator.data.get("aq_sensor1_type", 0) != 0:
            sensor_type = coordinator.data["aq_sensor1_type"]
            name = f"Air Quality {AQ_SENSOR_TYPES.get(sensor_type, 'Unknown')}"
            unit, device_class = get_aq_sensor_attributes(sensor_type)
            entities.append(
                KomfoventSensor(
                    coordinator,
                    "aq_sensor1_value",
                    name,
                    unit,
                    device_class,
                )
            )
            
        # Sensor 2
        if coordinator.data.get("aq_sensor2_type", 0) != 0:
            sensor_type = coordinator.data["aq_sensor2_type"]
            name = f"Secondary Air Quality {AQ_SENSOR_TYPES.get(sensor_type, 'Unknown')}"
            unit, device_class = get_aq_sensor_attributes(sensor_type)
            entities.append(
            KomfoventSensor(
                coordinator,
                sensor_type,
                name,
                unit,
                device_class,
            )
        )

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
        # Special handling for AQ sensors to include type in unique_id
        if sensor_type in ["aq_sensor1_value", "aq_sensor2_value"]:
            aq_type_reg = "aq_sensor1_type" if sensor_type == "aq_sensor1_value" else "aq_sensor2_type"
            aq_type = coordinator.data.get(aq_type_reg, 0) if coordinator.data else 0
            aq_type_name = {1: "co2", 2: "voc", 3: "rh"}.get(aq_type, "unknown")
            self._attr_unique_id = f"{DOMAIN}_aq_{aq_type_name}"
        else:
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
            sensor_type = self.coordinator.data.get(
                "aq_sensor1_type" if self._sensor_type == "aq_sensor1_value" else "aq_sensor2_type",
                0
            )
            
            # Update name based on sensor type
            type_names = {1: "CO2", 2: "VOC", 3: "Humidity"}
            self._attr_name = type_names.get(sensor_type, "Unknown")
            
            if sensor_type == AQ_SENSOR_TYPE_NOT_INSTALLED:
                return None
            elif sensor_type == AQ_SENSOR_TYPE_CO2:
                self._attr_native_unit_of_measurement = "ppm"
                self._attr_device_class = SensorDeviceClass.CO2
                if 0 <= float(value) <= 2500:
                    return float(value)
            elif sensor_type == AQ_SENSOR_TYPE_VOC:
                self._attr_native_unit_of_measurement = "ppb"
                if 0 <= float(value) <= 2000:
                    return float(value)
            elif sensor_type == AQ_SENSOR_TYPE_RH:
                self._attr_native_unit_of_measurement = PERCENTAGE
                self._attr_device_class = SensorDeviceClass.HUMIDITY
                if 0 <= float(value) <= 100:
                    return float(value)
            return None
            
        return float(value)
