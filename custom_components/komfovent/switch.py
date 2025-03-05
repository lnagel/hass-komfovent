"""Switch platform for Komfovent."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers
from .const import DOMAIN
from .coordinator import KomfoventCoordinator


async def create_switches(coordinator):
    return [
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_POWER,
            entity_description=SwitchEntityDescription(
                key="power",
                name="Power",
                icon="mdi:power",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_ECO_MODE,
            entity_description=SwitchEntityDescription(
                key="eco_mode",
                name="ECO Mode",
                icon="mdi:leaf",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AUTO_MODE,
            entity_description=SwitchEntityDescription(
                key="auto_mode",
                name="AUTO Mode",
                icon="mdi:auto-fix",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent switches."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(await create_switches(coordinator))


class KomfoventSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Komfovent switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
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
        """Return True if entity is on."""
        if not self.coordinator.data:
            return None
        return bool(self.coordinator.data.get(self.register_id, 0))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self.coordinator.client.write_register(self.register_id, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self.coordinator.client.write_register(self.register_id, 0)
        await self.coordinator.async_request_refresh()
