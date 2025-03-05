"""Switch platform for Komfovent."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers
from .const import DOMAIN
from .coordinator import KomfoventCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent switches."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        KomfoventSwitch(
            coordinator,
            "Power",
            "power",
            registers.REG_POWER,
            "Turn ventilation unit on/off",
            "mdi:power",
        ),
        KomfoventSwitch(
            coordinator,
            "ECO Mode",
            "eco_mode",
            registers.REG_ECO_MODE,
            "Enables energy saving mode",
            "mdi:leaf",
        ),
        KomfoventSwitch(
            coordinator,
            "AUTO Mode",
            "auto_mode",
            registers.REG_AUTO_MODE,
            "Enables automatic mode control",
            "mdi:auto-fix",
        ),
    ])

class KomfoventSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Komfovent switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        name: str,
        key: str,
        register_id: int,
        description: str,
        icon: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._register_id = register_id
        self._attr_device_class = None
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Komfovent Ventilation",
            "manufacturer": "Komfovent",
            "model": "Modbus",
        }
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if not self.coordinator.data:
            return None
        return bool(self.coordinator.data.get(self._register_id, 0))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self.coordinator.client.write_register(self._register_id, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self.coordinator.client.write_register(self._register_id, 0)
        await self.coordinator.async_request_refresh()
