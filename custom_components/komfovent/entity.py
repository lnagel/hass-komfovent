"""Base entity for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from .coordinator import KomfoventCoordinator


class KomfoventCoordinatorEntity(CoordinatorEntity["KomfoventCoordinator"]):
    """Base class that derives entity state from coordinator data."""

    coordinator: KomfoventCoordinator

    async def async_added_to_hass(self) -> None:
        """Populate state attributes before the first state write."""
        await super().async_added_to_hass()
        self._update_attrs()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh state attributes from coordinator data and write state."""
        self._update_attrs()
        super()._handle_coordinator_update()

    def _update_attrs(self) -> None:
        """Set the _attr_* state attributes from coordinator data."""
