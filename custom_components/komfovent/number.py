"""Number platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import PERCENTAGE, UnitOfTime, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent number entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            KomfoventNumber(
                coordinator=coordinator,
                register_id=registers.REG_AQ_MIN_INTENSITY,
                entity_description=NumberEntityDescription(
                    key="aq_minimum_intensity",
                    name="AQ Minimum Intensity",
                    entity_category=EntityCategory.CONFIG,
                    native_min_value=20,
                    native_max_value=100,
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
                    native_min_value=20,
                    native_max_value=100,
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
        ]
    )


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
