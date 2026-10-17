"""Firmware storage management for Komfovent integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aiofiles import os as aio_os
from homeassistant.exceptions import HomeAssistantError
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

# Keys every stored FirmwareInfo must have
_FIRMWARE_INFO_KEYS = frozenset(FirmwareInfo.__annotations__)
VERSION_TUPLE_LENGTH = 5


class FirmwareDataStore(Store[StoredFirmwareData]):
    """Store for firmware metadata with migration support."""

    async def _async_migrate_func(
        self,
        old_major_version: int,  # noqa: ARG002
        old_minor_version: int,  # noqa: ARG002
        old_data: dict[str, Any],
    ) -> StoredFirmwareData:
        """
        Migrate stored firmware data to the current version.

        Version 1 is the first format, so there is nothing to migrate yet.
        When bumping FIRMWARE_STORAGE_VERSION, add a step per old version:
        ``if old_major_version == 1: old_data = self._migrate_v1_to_v2(old_data)``
        """
        return {"firmware": old_data.get("firmware", {})}


def _is_valid_firmware_info(info: Any) -> bool:
    """Check that a stored entry has the FirmwareInfo shape."""
    return (
        isinstance(info, dict)
        and info.keys() >= _FIRMWARE_INFO_KEYS
        and isinstance(info["controller_version"], list | tuple)
        and len(info["controller_version"]) == VERSION_TUPLE_LENGTH
    )


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
        self._store = FirmwareDataStore(
            hass, FIRMWARE_STORAGE_VERSION, FIRMWARE_STORAGE_KEY
        )
        self._data: StoredFirmwareData = {"firmware": {}}
        self._storage_dir = Path(hass.config.path(".storage", FIRMWARE_DIR))

    async def async_load(self) -> None:
        """
        Load stored firmware data from disk.

        The data is only a cache of downloaded firmware, so unreadable data
        (e.g. written by a newer version before a downgrade) or malformed
        entries are dropped and re-downloaded instead of failing setup.
        """
        try:
            stored = await self._store.async_load()
        except HomeAssistantError:
            _LOGGER.warning("Discarding unreadable firmware store", exc_info=True)
            stored = None

        firmware = (stored or {}).get("firmware", {})
        valid = {
            ct: info for ct, info in firmware.items() if _is_valid_firmware_info(info)
        }
        if len(valid) != len(firmware):
            _LOGGER.warning(
                "Discarding %d malformed firmware store entries",
                len(firmware) - len(valid),
            )
        self._data = {"firmware": valid}
        _LOGGER.debug("Loaded firmware store with %d entries", len(valid))

    def get_firmware_info(self, controller_type: str) -> FirmwareInfo | None:
        """
        Get firmware info for a specific controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        Returns:
            FirmwareInfo if available, None otherwise

        """
        return self._data["firmware"].get(controller_type)

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
        self._data["firmware"][controller_type] = info
        await self._store.async_save(self._data)
        _LOGGER.info(
            "Stored firmware info for %s: version %s",
            controller_type,
            format_version(info["controller_version"]),
        )

    async def async_ensure_storage_dir(self) -> Path:
        """
        Ensure the firmware storage directory exists.

        Returns:
            Path to the firmware storage directory

        """
        await aio_os.makedirs(self._storage_dir, exist_ok=True)
        return self._storage_dir

    async def async_cleanup_old_files(self, keep_controller_types: set[str]) -> None:
        """
        Remove firmware files that are no longer needed.

        Args:
            keep_controller_types: Set of controller types to keep

        """
        if not await aio_os.path.exists(self._storage_dir):
            return

        keep = {
            info["filename"]
            for ct in keep_controller_types
            if (info := self.get_firmware_info(ct)) is not None
        }
        for filename in await aio_os.listdir(self._storage_dir):
            if not filename.endswith(".mbin") or filename in keep:
                continue
            try:
                await aio_os.remove(self._storage_dir / filename)
                _LOGGER.info("Removed old firmware file: %s", filename)
            except OSError:
                _LOGGER.exception("Failed to remove firmware file: %s", filename)
