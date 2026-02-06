"""DateTime platform for Komfovent."""

from __future__ import annotations

import zoneinfo
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.datetime import DateTimeEntity, DateTimeEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import DOMAIN
from .helpers import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent datetime entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            KomfoventDateTime(
                coordinator=coordinator,
                register_id=registers.REG_HOLIDAYS_FROM,
                entity_description=DateTimeEntityDescription(
                    key="holidays_from",
                    name="Holidays From",
                    entity_registry_enabled_default=True,
                    entity_registry_visible_default=False,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            KomfoventDateTime(
                coordinator=coordinator,
                register_id=registers.REG_HOLIDAYS_UNTIL,
                entity_description=DateTimeEntityDescription(
                    key="holidays_until",
                    name="Holidays Until",
                    entity_registry_enabled_default=True,
                    entity_registry_visible_default=False,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
        ]
    )


class KomfoventDateTime(CoordinatorEntity["KomfoventCoordinator"], DateTimeEntity):
    """Representation of a Komfovent datetime entity."""

    _attr_has_entity_name = True
    coordinator: KomfoventCoordinator

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: DateTimeEntityDescription,
    ) -> None:
        """Initialize the datetime entity."""
        super().__init__(coordinator)
        self.register_id = register_id
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )
        self._attr_translation_key = entity_description.key
        self._attr_device_info = build_device_info(coordinator)

    @property
    def native_value(self) -> datetime | None:
        """Return the datetime value."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self.register_id)
        if value is None:
            return None

        try:
            # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
            local_tz = zoneinfo.ZoneInfo(str(self.coordinator.hass.config.time_zone))
            local_epoch = datetime(1970, 1, 1, tzinfo=local_tz)

            # Convert seconds since local epoch to datetime
            return local_epoch + timedelta(seconds=value)
        except (ValueError, TypeError, OSError):
            return None

    async def async_set_value(self, value: datetime) -> None:
        """Update the datetime value."""
        # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
        local_tz = zoneinfo.ZoneInfo(str(self.coordinator.hass.config.time_zone))
        local_epoch = datetime(1970, 1, 1, tzinfo=local_tz)

        if not value.tzinfo:
            # If datetime has no timezone, assume local timezone
            value = value.replace(tzinfo=local_tz)

        # Calculate seconds since local epoch
        seconds = int((value - local_epoch).total_seconds())

        # Write value to register
        await self.coordinator.client.write(self.register_id, seconds)
        await self.coordinator.async_request_refresh()
