"""Firmware checker for Komfovent integration."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import aiofiles
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from custom_components.komfovent.const import (
    FIRMWARE_CHECK_INTERVAL,
    FIRMWARE_MAX_SIZE,
    FIRMWARE_MIN_SIZE,
    FIRMWARE_URLS,
    Controller,
)
from custom_components.komfovent.firmware import (
    FirmwareInfo,
    format_version,
    get_controller_type_for_firmware,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from custom_components.komfovent.firmware.store import FirmwareStore

_LOGGER = logging.getLogger(__name__)

HTTP_OK = 200

# Firmware filename pattern matches both modern and legacy formats:
# Modern format: C6_1_5_46_72_P1_1_1_5_48.mbin
# Legacy format: C6_1_3_28_38_20180428.mbin
FIRMWARE_FILENAME_PATTERN = re.compile(
    r"^(C6|C8)_(\d+)_(\d+)_(\d+)_(\d+)(?:_P(\d+)_(\d+)_(\d+)_(\d+)_(\d+))?(?:_\d{8})?\.mbin$"
)


class FirmwareChecker:
    """
    Checks for and downloads firmware updates.

    This is a domain-level singleton that handles firmware checking for all
    Komfovent config entries. It only downloads firmware once per controller
    type, regardless of how many devices of that type exist.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        store: FirmwareStore,
    ) -> None:
        """
        Initialize the firmware checker.

        Args:
            hass: Home Assistant instance
            store: Firmware store for persistence

        """
        self._hass = hass
        self._store = store
        self._unsub_interval: Callable[[], None] | None = None
        self._active_controller_types: set[str] = set()
        self._checking = False

    def register_controller_type(self, controller: Controller) -> None:
        """
        Register a controller type as active.

        Args:
            controller: The controller type to register

        """
        ct = get_controller_type_for_firmware(controller)
        if ct != "NA":
            self._active_controller_types.add(ct)
            _LOGGER.debug("Registered controller type: %s", ct)

    def unregister_controller_type(self, controller: Controller) -> None:
        """
        Unregister a controller type.

        Args:
            controller: The controller type to unregister

        """
        ct = get_controller_type_for_firmware(controller)
        self._active_controller_types.discard(ct)
        _LOGGER.debug("Unregistered controller type: %s", ct)

    async def async_start(self) -> None:
        """Start the firmware checker with periodic updates."""
        if self._unsub_interval is not None:
            return  # Already started

        _LOGGER.info(
            "Starting firmware checker with %s interval", FIRMWARE_CHECK_INTERVAL
        )

        # Register interval callback
        self._unsub_interval = async_track_time_interval(
            self._hass,
            self._async_check_interval,
            FIRMWARE_CHECK_INTERVAL,
        )

        # Run an initial check
        await self.async_check_for_updates()

    async def async_stop(self) -> None:
        """Stop the firmware checker."""
        if self._unsub_interval is not None:
            self._unsub_interval()
            self._unsub_interval = None
            _LOGGER.info("Stopped firmware checker")

    async def _async_check_interval(self, _now: datetime) -> None:
        """Handle periodic check interval."""
        await self.async_check_for_updates()

    async def async_check_for_updates(self) -> None:
        """Check for firmware updates for all registered controller types."""
        if self._checking:
            _LOGGER.debug("Firmware check already in progress, skipping")
            return

        if not self._active_controller_types:
            _LOGGER.debug(
                "No active controller types registered, skipping firmware check"
            )
            return

        self._checking = True
        try:
            _LOGGER.debug(
                "Checking firmware for controller types: %s",
                ", ".join(self._active_controller_types),
            )

            # Check each controller type separately
            # C6 and C6M share firmware, so we only check C6
            types_to_check = set(self._active_controller_types)
            if "C6M" in types_to_check:
                types_to_check.discard("C6M")
                types_to_check.add("C6")

            for ct in types_to_check:
                await self._async_check_controller_type(ct)

        finally:
            self._checking = False

    async def _async_check_controller_type(self, controller_type: str) -> None:
        """
        Check for firmware update for a specific controller type.

        Args:
            controller_type: The controller type ("C6" or "C8")

        """
        try:
            # Get the download URL for this controller type
            if controller_type == "C6":
                url = FIRMWARE_URLS[Controller.C6]
            elif controller_type == "C8":
                url = FIRMWARE_URLS[Controller.C8]
            else:
                _LOGGER.warning("Unknown controller type: %s", controller_type)
                return

            _LOGGER.debug("Downloading firmware for %s from %s", controller_type, url)

            session = async_get_clientsession(self._hass)
            async with session.get(url, timeout=60) as response:
                if response.status != HTTP_OK:
                    _LOGGER.warning(
                        "Failed to download firmware for %s: HTTP %d",
                        controller_type,
                        response.status,
                    )
                    return

                # Get filename from Content-Disposition header and validate
                content_disposition = response.headers.get("Content-Disposition", "")
                filename = self._extract_filename(content_disposition)
                if not filename or not filename.endswith(".mbin"):
                    _LOGGER.warning(
                        "Invalid or missing firmware filename for %s: %s",
                        controller_type,
                        filename or "(none)",
                    )
                    return

                # Read firmware content
                content = await response.read()

                # Validate file size
                if not FIRMWARE_MIN_SIZE <= len(content) <= FIRMWARE_MAX_SIZE:
                    _LOGGER.warning(
                        "Invalid firmware size for %s: %d bytes (expected %d-%d)",
                        controller_type,
                        len(content),
                        FIRMWARE_MIN_SIZE,
                        FIRMWARE_MAX_SIZE,
                    )
                    return

                # Parse version from filename
                firmware_info = self._parse_firmware_filename(filename, controller_type)
                if firmware_info is None:
                    _LOGGER.warning(
                        "Failed to parse firmware filename: %s",
                        filename,
                    )
                    return

                # Check if this is a new version
                existing = self._store.get_firmware_info(controller_type)
                if existing and existing["filename"] == filename:
                    _LOGGER.debug(
                        "Firmware for %s is up to date: %s",
                        controller_type,
                        format_version(firmware_info["controller_version"]),
                    )
                    return

                # Save firmware file
                storage_dir = await self._store.async_ensure_storage_dir()
                file_path = storage_dir / filename
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)

                # Update firmware info
                firmware_info["file_path"] = str(file_path)
                firmware_info["last_checked_at"] = dt_util.utcnow().isoformat()

                await self._store.async_set_firmware_info(
                    controller_type, firmware_info
                )

                _LOGGER.info(
                    "Downloaded new firmware for %s: %s (version %s)",
                    controller_type,
                    filename,
                    format_version(firmware_info["controller_version"]),
                )

                # Clean up old firmware files
                await self._store.async_cleanup_old_files(self._active_controller_types)

        except TimeoutError:
            _LOGGER.warning(
                "Timeout downloading firmware for %s",
                controller_type,
            )
        except Exception:
            _LOGGER.exception(
                "Error checking firmware for %s",
                controller_type,
            )

    def _extract_filename(self, content_disposition: str) -> str | None:
        """
        Extract filename from Content-Disposition header.

        Handles both quoted and unquoted formats:
        - attachment; filename="C6_1_5_46_72_P1_1_1_5_48.mbin"
        - attachment; filename=C6_1_5_46_72_P1_1_1_5_48.mbin

        Args:
            content_disposition: The Content-Disposition header value

        Returns:
            Filename if found, None otherwise

        """
        if not content_disposition:
            return None

        for segment in content_disposition.split(";"):
            stripped = segment.strip()
            if stripped.lower().startswith("filename"):
                _, _, value = stripped.partition("=")
                return value.strip().strip("\"'")

        return None

    def _parse_firmware_filename(
        self,
        filename: str,
        controller_type: str,
    ) -> FirmwareInfo | None:
        """
        Parse firmware version information from filename.

        Args:
            filename: The firmware filename
            controller_type: The expected controller type

        Returns:
            FirmwareInfo if parsing successful, None otherwise

        """
        match = FIRMWARE_FILENAME_PATTERN.match(filename)
        if not match:
            return None

        file_ct = match.group(1)
        if file_ct != controller_type:
            _LOGGER.warning(
                "Firmware controller type mismatch: expected %s, got %s",
                controller_type,
                file_ct,
            )
            return None

        # Controller version
        controller_enum = Controller.C6 if file_ct == "C6" else Controller.C8
        ctrl_version = (
            controller_enum.value,
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)),
            int(match.group(5)),
        )

        # Panel version (if present in filename)
        if match.group(6):
            # Modern filename with panel version
            panel_version = (
                int(match.group(6)),  # Panel type enum value
                int(match.group(7)),
                int(match.group(8)),
                int(match.group(9)),
                int(match.group(10)),
            )
        else:
            # Legacy filename without panel version
            panel_version = (0, 0, 0, 0, 0)

        return FirmwareInfo(
            controller_type=controller_type,
            filename=filename,
            controller_version=ctrl_version,
            panel_version=panel_version,
            file_path="",  # Will be set after saving
            last_checked_at="",  # Will be set after saving
        )

    async def async_force_check(self, controller_type: str | None = None) -> None:
        """
        Force an immediate firmware check.

        Args:
            controller_type: Optional specific controller type to check.
                           If None, checks all registered types.

        """
        if controller_type:
            await self._async_check_controller_type(controller_type)
        else:
            await self.async_check_for_updates()
