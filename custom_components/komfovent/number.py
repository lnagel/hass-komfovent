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
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import DOMAIN, AirQualitySensorType
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
