"""DateTime platform for Komfovent."""

from __future__ import annotations

from datetime import datetime
import zoneinfo
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
                    key="holiday_from",
                    name="Holiday From",
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            KomfoventDateTime(
                coordinator=coordinator,
                register_id=registers.REG_HOLIDAYS_TILL,
                entity_description=DateTimeEntityDescription(
                    key="holiday_till",
                    name="Holiday Till",
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
        ]
    )


class KomfoventDateTime(CoordinatorEntity, DateTimeEntity):
    """Representation of a Komfovent datetime entity."""

    _attr_has_entity_name = True

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
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": "Komfovent",
            "model": None,
        }

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
        if not value.tzinfo:
            # If datetime has no timezone, assume local timezone
            local_tz = zoneinfo.ZoneInfo(str(self.coordinator.hass.config.time_zone))
            value = value.replace(tzinfo=local_tz)

        # Initialize local epoch (1970-01-01 00:00:00 in local timezone)
        local_epoch = datetime(1970, 1, 1, tzinfo=value.tzinfo)

        # Calculate seconds since local epoch
        seconds = int((value - local_epoch).total_seconds())

        # Write value to register
        await self.coordinator.client.write_register(self.register_id, seconds)
        await self.coordinator.async_request_refresh()
