"""Binary sensor platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory
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
    """Set up Komfovent binary sensor based on a config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Binary sensors will be added here
    entities: list[KomfoventBinarySensor] = []

    async_add_entities(entities)


class KomfoventBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for Komfovent binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
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
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        return bool(self.coordinator.data.get(self.register_id))
