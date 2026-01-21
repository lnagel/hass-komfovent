"""Firmware storage management for Komfovent integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aiofiles import os as aio_os
from homeassistant.helpers.storage import Store

from custom_components.komfovent.const import (
    FIRMWARE_DIR,
    FIRMWARE_STORAGE_KEY,
    FIRMWARE_STORAGE_VERSION,
)
from custom_components.komfovent.firmware import (
    FirmwareInfo,
    StoredFirmwareData,
    format_version,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class FirmwareStore:
    """
    Manages persistent storage of firmware metadata and files.

    Firmware is stored per controller type (C6/C8), not per config entry.
    This allows multiple devices of the same type to share firmware cache.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """
        Initialize the firmware store.

        Args:
            hass: Home Assistant instance

        """
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(
            hass, FIRMWARE_STORAGE_VERSION, FIRMWARE_STORAGE_KEY
        )
        self._data: StoredFirmwareData = {"firmware": {}}
        self._storage_dir = Path(hass.config.path(".storage", FIRMWARE_DIR))

    async def async_load(self) -> None:
        """Load stored firmware data from disk."""
        stored = await self._store.async_load()
        if stored is not None:
            self._data = stored  # type: ignore[assignment]
            _LOGGER.debug(
                "Loaded firmware store with %d entries",
                len(self._data.get("firmware", {})),
            )
        else:
            self._data = {"firmware": {}}
            _LOGGER.debug("No existing firmware store found, starting fresh")

    async def async_save(self) -> None:
        """Save firmware data to disk."""
        await self._store.async_save(self._data)  # type: ignore[arg-type]
        _LOGGER.debug("Saved firmware store")

    def get_firmware_info(self, controller_type: str) -> FirmwareInfo | None:
        """
        Get firmware info for a specific controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        Returns:
            FirmwareInfo if available, None otherwise

        """
        return self._data.get("firmware", {}).get(controller_type)

    def get_latest_version(self, controller_type: str) -> str | None:
        """
        Get the latest available firmware version string for a controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        Returns:
            Version string (e.g., "1.5.46.72") if available, None otherwise

        """
        info = self.get_firmware_info(controller_type)
        if info is None:
            return None
        return format_version(info["controller_version"])

    def get_firmware_path(self, controller_type: str) -> Path | None:
        """
        Get the path to the firmware file for a controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        Returns:
            Path to firmware file if available, None otherwise

        """
        info = self.get_firmware_info(controller_type)
        if info is None:
            return None
        return Path(info["file_path"])

    async def async_set_firmware_info(
        self,
        controller_type: str,
        info: FirmwareInfo,
    ) -> None:
        """
        Store firmware info for a controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")
            info: The firmware information to store

        """
        if "firmware" not in self._data:
            self._data["firmware"] = {}
        self._data["firmware"][controller_type] = info
        await self.async_save()
        _LOGGER.info(
            "Stored firmware info for %s: version %s",
            controller_type,
            format_version(info["controller_version"]),
        )

    async def async_remove_firmware_info(self, controller_type: str) -> None:
        """
        Remove firmware info for a controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        """
        if controller_type in self._data.get("firmware", {}):
            del self._data["firmware"][controller_type]
            await self.async_save()
            _LOGGER.info("Removed firmware info for %s", controller_type)

    def get_storage_dir(self) -> Path:
        """
        Get the firmware storage directory path.

        Returns:
            Path to the firmware storage directory

        """
        return self._storage_dir

    async def async_ensure_storage_dir(self) -> Path:
        """
        Ensure the firmware storage directory exists.

        Returns:
            Path to the firmware storage directory

        """
        await aio_os.makedirs(self._storage_dir, exist_ok=True)
        return self._storage_dir

    async def async_has_firmware_file(self, controller_type: str) -> bool:
        """
        Check if firmware file exists for a controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        Returns:
            True if firmware file exists

        """
        path = self.get_firmware_path(controller_type)
        if path is None:
            return False
        return await aio_os.path.exists(path)

    async def async_cleanup_old_files(self, keep_controller_types: set[str]) -> None:
        """
        Remove firmware files that are no longer needed.

        Args:
            keep_controller_types: Set of controller types to keep

        """
        if not await aio_os.path.exists(self._storage_dir):
            return

        for filename in await aio_os.listdir(self._storage_dir):
            if not filename.endswith(".mbin"):
                continue

            # Check if file belongs to any active controller type
            is_needed = False
            for ct in keep_controller_types:
                info = self.get_firmware_info(ct)
                if info and info["filename"] == filename:
                    is_needed = True
                    break

            if not is_needed:
                try:
                    await aio_os.remove(self._storage_dir / filename)
                    _LOGGER.info("Removed old firmware file: %s", filename)
                except OSError:
                    _LOGGER.exception("Failed to remove firmware file: %s", filename)
