"""Select platform for Komfovent."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Final

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers
from .const import DOMAIN, OperationMode

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent select entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KomfoventModeSelect(coordinator)])


class KomfoventModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Komfovent mode select entity."""

    _attr_has_entity_name: ClassVar[bool] = True
    _attr_name: ClassVar[str] = "Current mode"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = [mode.name.lower() for mode in OperationMode]

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_mode_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": "Komfovent",
            "model": None,
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.coordinator.data:
            return None

        mode = self.coordinator.data.get(registers.REG_OPERATION_MODE, 0)
        try:
            return OperationMode(mode).name.lower()
        except ValueError:
            return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            mode = OperationMode[option.upper()]
        except ValueError:
            _LOGGER.warning("Invalid operation mode: %s", option)
            return

        if mode == OperationMode.OFF:
            await self.coordinator.client.write_register(registers.REG_POWER, 0)
        elif mode == OperationMode.AIR_QUALITY:
            await self.coordinator.client.write_register(registers.REG_AUTO_MODE, 1)
        elif mode in {
            OperationMode.AWAY,
            OperationMode.NORMAL,
            OperationMode.INTENSIVE,
            OperationMode.BOOST,
        }:
            await self.coordinator.client.write_register(
                registers.REG_OPERATION_MODE, mode.value
            )
        else:
            _LOGGER.warning("Unsupported operation mode: %s", option)
            return

        await self.coordinator.async_request_refresh()
