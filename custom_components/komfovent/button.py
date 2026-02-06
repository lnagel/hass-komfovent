"""Button platform for Komfovent integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import services
from .const import DOMAIN
from .helpers import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent button from config entry."""
    runtime_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: KomfoventCoordinator = runtime_data.coordinator

    async_add_entities(
        [
            KomfoventSetTimeButton(
                coordinator,
                ButtonEntityDescription(
                    key="set_system_time",
                    name="Set System Time",
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            KomfoventCleanFiltersButton(
                coordinator,
                ButtonEntityDescription(
                    key="clean_filters",
                    name="Clean Filters Calibration",
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
        ]
    )


class KomfoventButtonEntity(CoordinatorEntity["KomfoventCoordinator"], ButtonEntity):
    """Base class for Komfovent button entities."""

    _attr_has_entity_name = True
    coordinator: KomfoventCoordinator

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        entity_description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )
        self._attr_translation_key = entity_description.key
        self._attr_device_info = build_device_info(coordinator)


class KomfoventSetTimeButton(KomfoventButtonEntity):
    """Button to set system time on Komfovent device."""

    async def async_press(self) -> None:
        """Handle the button press."""
        await services.set_system_time(self.coordinator)


class KomfoventCleanFiltersButton(KomfoventButtonEntity):
    """Button to calibrate clean filters on Komfovent device."""

    async def async_press(self) -> None:
        """Handle the button press."""
        await services.clean_filters_calibration(self.coordinator)
