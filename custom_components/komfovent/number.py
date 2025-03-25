"""Number platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import (
    DOMAIN,
    AirQualitySensorType,
    FAN_SPEED_MIN,
    FAN_SPEED_MAX,
    FlowControl,
    FlowUnit,
    HolidayMicroventilation,
)
from .registers import REG_ECO_MAX_TEMP, REG_ECO_MIN_TEMP

AQ_INTENSITY_MIN = 20
AQ_INTENSITY_MAX = 100
TEMP_SETPOINT_MIN = 5
TEMP_SETPOINT_MAX = 40

CO2_MIN = 0
CO2_MAX = 2000
VOC_MIN = 0
VOC_MAX = 100


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent number entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # Normal mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_NORMAL_FAN_SUPPLY,
            entity_description=NumberEntityDescription(
                key="normal_supply_flow",
                name="Normal Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_NORMAL_FAN_EXTRACT,
            entity_description=NumberEntityDescription(
                key="normal_extract_flow",
                name="Normal Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_NORMAL_SETPOINT,
            entity_description=NumberEntityDescription(
                key="normal_temperature",
                name="Normal Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        # Intensive mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_INTENSIVE_FAN_SUPPLY,
            entity_description=NumberEntityDescription(
                key="intensive_supply_flow",
                name="Intensive Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_INTENSIVE_FAN_EXTRACT,
            entity_description=NumberEntityDescription(
                key="intensive_extract_flow",
                name="Intensive Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_INTENSIVE_TEMP,
            entity_description=NumberEntityDescription(
                key="intensive_temperature",
                name="Intensive Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        # Boost mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_BOOST_FAN_SUPPLY,
            entity_description=NumberEntityDescription(
                key="boost_supply_flow",
                name="Boost Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_BOOST_FAN_EXTRACT,
            entity_description=NumberEntityDescription(
                key="boost_extract_flow",
                name="Boost Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_BOOST_TEMP,
            entity_description=NumberEntityDescription(
                key="boost_temperature",
                name="Boost Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        # Away mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_AWAY_FAN_SUPPLY,
            entity_description=NumberEntityDescription(
                key="away_supply_flow",
                name="Away Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_AWAY_FAN_EXTRACT,
            entity_description=NumberEntityDescription(
                key="away_extract_flow",
                name="Away Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_AWAY_TEMP,
            entity_description=NumberEntityDescription(
                key="away_temperature",
                name="Away Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        # Kitchen mode controls
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_SUPPLY,
            entity_description=NumberEntityDescription(
                key="kitchen_supply_fan",
                name="Kitchen Supply Fan",
                native_unit_of_measurement=PERCENTAGE,
                native_min_value=FAN_SPEED_MIN,
                native_max_value=FAN_SPEED_MAX,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_EXTRACT,
            entity_description=NumberEntityDescription(
                key="kitchen_extract_fan",
                name="Kitchen Extract Fan",
                native_unit_of_measurement=PERCENTAGE,
                native_min_value=FAN_SPEED_MIN,
                native_max_value=FAN_SPEED_MAX,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_TEMP,
            entity_description=NumberEntityDescription(
                key="kitchen_temperature",
                name="Kitchen Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_TIMER,
            entity_description=NumberEntityDescription(
                key="kitchen_timer",
                name="Kitchen Timer",
                native_unit_of_measurement=UnitOfTime.MINUTES,
                native_min_value=0,
                native_max_value=300,
                native_step=1,
                device_class=NumberDeviceClass.DURATION,
                entity_category=EntityCategory.CONFIG,
                entity_registry_enabled_default=False,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=REG_ECO_MIN_TEMP,
            entity_description=NumberEntityDescription(
                key="eco_min_supply_temperature",
                name="ECO Min Supply Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=REG_ECO_MAX_TEMP,
            entity_description=NumberEntityDescription(
                key="eco_max_supply_temperature",
                name="ECO Max Supply Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_AQ_MIN_INTENSITY,
            entity_description=NumberEntityDescription(
                key="aq_minimum_intensity",
                name="AQ Minimum Intensity",
                entity_category=EntityCategory.CONFIG,
                native_min_value=AQ_INTENSITY_MIN,
                native_max_value=AQ_INTENSITY_MAX,
                native_step=1,
                native_unit_of_measurement=PERCENTAGE,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_AQ_MAX_INTENSITY,
            entity_description=NumberEntityDescription(
                key="aq_maximum_intensity",
                name="AQ Maximum Intensity",
                entity_category=EntityCategory.CONFIG,
                native_min_value=AQ_INTENSITY_MIN,
                native_max_value=AQ_INTENSITY_MAX,
                native_step=1,
                native_unit_of_measurement=PERCENTAGE,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_AQ_CHECK_PERIOD,
            entity_description=NumberEntityDescription(
                key="aq_check_period",
                name="AQ Check Period",
                entity_category=EntityCategory.CONFIG,
                native_min_value=1,
                native_max_value=24,
                native_step=1,
                native_unit_of_measurement=UnitOfTime.HOURS,
                device_class=NumberDeviceClass.DURATION,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_AQ_TEMP_SETPOINT,
            entity_description=NumberEntityDescription(
                key="aq_temperature_setpoint",
                name="AQ Temperature Setpoint",
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
            ),
        ),
        # Kitchen mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_SUPPLY,
            entity_description=NumberEntityDescription(
                key="kitchen_supply_flow",
                name="Kitchen Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_EXTRACT,
            entity_description=NumberEntityDescription(
                key="kitchen_extract_flow",
                name="Kitchen Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_TEMP,
            entity_description=NumberEntityDescription(
                key="kitchen_temperature",
                name="Kitchen Temperature",
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_TIMER,
            entity_description=NumberEntityDescription(
                key="kitchen_timer",
                name="Kitchen Timer",
                native_unit_of_measurement=UnitOfTime.MINUTES,
                native_min_value=0,
                native_max_value=300,
                native_step=1,
                device_class=NumberDeviceClass.DURATION,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        # Fireplace mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_FIREPLACE_SUPPLY,
            entity_description=NumberEntityDescription(
                key="fireplace_supply_flow",
                name="Fireplace Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_FIREPLACE_EXTRACT,
            entity_description=NumberEntityDescription(
                key="fireplace_extract_flow",
                name="Fireplace Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_FIREPLACE_TEMP,
            entity_description=NumberEntityDescription(
                key="fireplace_temperature",
                name="Fireplace Temperature",
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_FIREPLACE_TIMER,
            entity_description=NumberEntityDescription(
                key="fireplace_timer",
                name="Fireplace Timer",
                native_unit_of_measurement=UnitOfTime.MINUTES,
                native_min_value=0,
                native_max_value=300,
                native_step=1,
                device_class=NumberDeviceClass.DURATION,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        # Override mode controls
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_OVERRIDE_SUPPLY,
            entity_description=NumberEntityDescription(
                key="override_supply_flow",
                name="Override Supply Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        FlowNumber(
            coordinator=coordinator,
            register_id=registers.REG_OVERRIDE_EXTRACT,
            entity_description=NumberEntityDescription(
                key="override_extract_flow",
                name="Override Extract Flow",
                native_min_value=0,
                native_max_value=200000,
                native_step=1,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_OVERRIDE_TEMP,
            entity_description=NumberEntityDescription(
                key="override_temperature",
                name="Override Temperature",
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventNumber(
            coordinator=coordinator,
            register_id=registers.REG_OVERRIDE_TIMER,
            entity_description=NumberEntityDescription(
                key="override_timer",
                name="Override Timer",
                native_unit_of_measurement=UnitOfTime.MINUTES,
                native_min_value=0,
                native_max_value=300,
                native_step=1,
                device_class=NumberDeviceClass.DURATION,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        # Holiday mode controls
        TemperatureNumber(
            coordinator=coordinator,
            register_id=registers.REG_HOLIDAYS_TEMP,
            entity_description=NumberEntityDescription(
                key="holidays_temperature",
                name="Holidays Temperature",
                native_min_value=TEMP_SETPOINT_MIN,
                native_max_value=TEMP_SETPOINT_MAX,
                native_step=0.1,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
    ]

    # Check AQ sensor types to determine if we should add the impurity setpoint
    sensor1_type = coordinator.data.get(registers.REG_AQ_SENSOR1_TYPE)
    sensor2_type = coordinator.data.get(registers.REG_AQ_SENSOR2_TYPE)

    # Check if either sensor is a CO2 sensor
    if AirQualitySensorType.CO2 in {sensor1_type, sensor2_type}:
        entities.append(
            KomfoventNumber(
                coordinator=coordinator,
                register_id=registers.REG_AQ_IMPURITY_SETPOINT,
                entity_description=NumberEntityDescription(
                    key="aq_co2_setpoint",
                    name="AQ CO2 Setpoint",
                    native_step=1,
                    native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
                    native_min_value=CO2_MIN,
                    native_max_value=CO2_MAX,
                    device_class=NumberDeviceClass.CO2,
                ),
            ),
        )
    # Check if either sensor is a VOC sensor (and CO2 sensor is not already added)
    elif AirQualitySensorType.VOC in {sensor1_type, sensor2_type}:
        entities.append(
            KomfoventNumber(
                coordinator=coordinator,
                register_id=registers.REG_AQ_IMPURITY_SETPOINT,
                entity_description=NumberEntityDescription(
                    key="aq_voc_setpoint",
                    name="AQ VOC Setpoint",
                    native_step=1,
                    native_unit_of_measurement=PERCENTAGE,
                ),
            ),
        )

    # Check if either sensor is a humidity sensor (independent of CO2/VOC)
    if AirQualitySensorType.HUMIDITY in {sensor1_type, sensor2_type}:
        entities.append(
            KomfoventNumber(
                coordinator=coordinator,
                register_id=registers.REG_AQ_HUMIDITY_SETPOINT,
                entity_description=NumberEntityDescription(
                    key="aq_humidity_setpoint",
                    name="AQ Humidity Setpoint",
                    native_step=1,
                    native_unit_of_measurement=PERCENTAGE,
                    native_min_value=0,
                    native_max_value=100,
                    device_class=NumberDeviceClass.HUMIDITY,
                ),
            ),
        )

    async_add_entities(entities)


class KomfoventNumber(CoordinatorEntity, NumberEntity):
    """Base representation of a Komfovent number entity."""

    _attr_has_entity_name: ClassVar[bool] = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: NumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
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
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self.register_id, 0)

        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.client.write_register(self.register_id, int(value))
        await self.coordinator.async_request_refresh()


class FlowNumber(KomfoventNumber):
    """Flow number with dynamic units based on flow unit setting."""

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if not self.coordinator.data:
            return None

        flow_control = self.coordinator.data.get(registers.REG_FLOW_CONTROL)
        if flow_control == FlowControl.OFF:
            return PERCENTAGE

        flow_unit = self.coordinator.data.get(registers.REG_FLOW_UNIT)
        if flow_unit == FlowUnit.M3H:
            return UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        if flow_unit == FlowUnit.LS:
            return UnitOfVolumeFlowRate.LITERS_PER_SECOND

        return None


class TemperatureNumber(KomfoventNumber):
    """Temperature number with x10 scaling."""

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        value = super().native_value

        if value is None:
            return None

        return value / 10

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await super().async_set_native_value(value * 10)
