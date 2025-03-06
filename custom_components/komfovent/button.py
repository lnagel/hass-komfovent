"""Button platform for Komfovent integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import KomfoventCoordinator
from .const import DOMAIN
from .services import set_system_time


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent button from config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            KomfoventSetTimeButton(
                coordinator,
                ButtonEntityDescription(
                    key="set_system_time",
                    name="Set System Time",
                    icon="mdi:clock",
                ),
            )
        ]
    )


class KomfoventSetTimeButton(ButtonEntity):
    """Representation of a Komfovent set time button."""

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_set_system_time"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Komfovent",
            "manufacturer": "Komfovent",
            "model": "C6",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await set_system_time(self.coordinator)
