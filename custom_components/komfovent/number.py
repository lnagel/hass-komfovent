"""Number platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import (
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

AQ_INTENSITY_MIN = 20
AQ_INTENSITY_MAX = 100
AQ_TEMP_SETPOINT_MIN = 5
AQ_TEMP_SETPOINT_MAX = 40

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
                entity_category=EntityCategory.CONFIG,
                native_min_value=AQ_TEMP_SETPOINT_MIN,  # Min temp per MODBUS spec
                native_max_value=AQ_TEMP_SETPOINT_MAX,  # Max temp per MODBUS spec
                native_step=0.1,  # 0.1°C steps since value is x10
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=NumberDeviceClass.TEMPERATURE,
            ),
        ),
    ]

    # Check AQ sensor types to determine if we should add the impurity setpoint
    sensor1_type = coordinator.data.get(registers.REG_AQ_SENSOR1_TYPE)
    sensor2_type = coordinator.data.get(registers.REG_AQ_SENSOR2_TYPE)

    # Use first CO2/VOC sensor type found
    aq_type = None
    if sensor1_type in (AirQualitySensorType.CO2, AirQualitySensorType.VOC):
        aq_type = sensor1_type
    elif sensor2_type in (AirQualitySensorType.CO2, AirQualitySensorType.VOC):
        aq_type = sensor2_type

    if aq_type is not None:
        # Configure entity based on sensor type
        if aq_type == AirQualitySensorType.CO2:
            native_unit = "ppm"
            min_val = CO2_MIN
            max_val = CO2_MAX
        else:  # VOC
            native_unit = PERCENTAGE
            min_val = VOC_MIN
            max_val = VOC_MAX

        entities.append(
            AirQualityNumber(
                coordinator=coordinator,
                register_id=registers.REG_AQ_IMPURITY_SETPOINT,
                entity_description=NumberEntityDescription(
                    key="aq_impurity_setpoint",
                    name="AQ Impurity Setpoint",
                    entity_category=EntityCategory.CONFIG,
                    native_step=1,
                    native_unit_of_measurement=native_unit,
                    native_min_value=min_val,
                    native_max_value=max_val,
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


class AirQualityNumber(TemperatureNumber):
    """Air quality number with x10 scaling."""
