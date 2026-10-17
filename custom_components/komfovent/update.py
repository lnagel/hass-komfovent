"""Update platform for Komfovent."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.exceptions import HomeAssistantError

from . import registers
from .const import FIRMWARE_MIN_SUPPORTED_VERSION_C6
from .entity import KomfoventCoordinatorEntity
from .firmware import FirmwareInfo, get_controller_type_for_firmware
from .firmware.uploader import FirmwareUploader, FirmwareUploadError
from .helpers import build_device_info, get_controller_version

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventConfigEntry, KomfoventCoordinator
    from .firmware.store import FirmwareStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: KomfoventConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent update entity."""
    coordinator = entry.runtime_data.coordinator
    store = entry.runtime_data.firmware_store

    async_add_entities([KomfoventUpdateEntity(coordinator, store)])


class KomfoventUpdateEntity(KomfoventCoordinatorEntity, UpdateEntity):
    """Representation of a Komfovent firmware update entity."""

    _attr_has_entity_name = True
    _attr_name = "Firmware"
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        store: FirmwareStore,
    ) -> None:
        """
        Initialize the update entity.

        Args:
            coordinator: The Komfovent data coordinator
            store: The firmware store

        """
        super().__init__(coordinator)
        self._store = store
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_firmware_update"
        self._attr_device_info = build_device_info(coordinator)

        self._update_attrs()

    def _update_attrs(self) -> None:
        """Set version attributes from coordinator data and the firmware store."""
        self._attr_installed_version = self._compute_installed_version()

        info = self._get_firmware_info()
        if info is None:
            self._attr_latest_version = None
            self._attr_release_summary = None
        else:
            self._attr_latest_version = str(info["controller_version"][4])
            self._attr_release_summary = info["filename"]

    def _compute_installed_version(self) -> str | None:
        """Return the installed firmware functional version (v4)."""
        if not self.coordinator.data:
            return None

        raw_value = self.coordinator.data.get(registers.REG_FIRMWARE)
        if raw_value is None or raw_value == 0:
            return None

        try:
            version = get_controller_version(int(raw_value))
            return str(version[4])
        except ValueError, TypeError:
            return None

    def _get_firmware_info(self) -> FirmwareInfo | None:
        """Return the stored firmware info for this controller type."""
        controller_type = get_controller_type_for_firmware(self.coordinator.controller)
        if controller_type == "NA":
            return None
        return self._store.get_firmware_info(controller_type)

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        # Entity is available if we have coordinator data
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def _is_firmware_supported(self) -> bool:
        """
        Check if firmware update is supported for this device.

        C6/C6M controllers need v1.3.15 or newer for .mbin uploads. C8
        controllers supported .mbin uploads from launch.
        """
        if get_controller_type_for_firmware(self.coordinator.controller) != "C6":
            return True

        if not self.coordinator.data:
            return False

        raw_value = self.coordinator.data.get(registers.REG_FIRMWARE)
        if raw_value is None or raw_value == 0:
            return False

        try:
            version = get_controller_version(int(raw_value))
        except ValueError, TypeError:
            return False
        else:
            # Compare v1, v2, v3 with minimum supported version
            installed = (version[1], version[2], version[3])
            return installed >= FIRMWARE_MIN_SUPPORTED_VERSION_C6

    @property
    def entity_picture(self) -> str | None:
        """Return entity picture URL."""
        # No entity picture for now
        return None

    async def async_install(
        self,
        version: str | None,  # noqa: ARG002
        backup: bool,  # noqa: ARG002, FBT001
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """
        Install a firmware update.

        Args:
            version: Version to install (unused, always installs latest)
            backup: Whether to backup before installing (unused)
            **kwargs: Additional arguments (unused)

        Raises:
            HomeAssistantError: If installation fails

        """
        if self._attr_in_progress:
            msg = "Firmware update already in progress"
            raise HomeAssistantError(msg)

        # Check if firmware update is supported
        if not self._is_firmware_supported:
            min_ver = ".".join(map(str, FIRMWARE_MIN_SUPPORTED_VERSION_C6))
            msg = (
                f"Firmware update not supported. Device firmware must be "
                f"v{min_ver} or newer. Please update manually first."
            )
            raise HomeAssistantError(msg)

        # Get controller type
        controller_type = get_controller_type_for_firmware(self.coordinator.controller)
        if controller_type == "NA":
            msg = "Unknown controller type"
            raise HomeAssistantError(msg)

        # Get firmware file path
        firmware_path = self._store.get_firmware_path(controller_type)
        if firmware_path is None or not firmware_path.exists():
            msg = "Firmware file not available. Wait for firmware check to complete."
            raise HomeAssistantError(msg)

        # The functional version the device should report after flashing
        expected_version = self.latest_version

        # Get device connection details
        host = self.coordinator.config_entry.data[CONF_HOST]
        password = self.coordinator.config_entry.data.get(CONF_PASSWORD)

        self._attr_in_progress = True
        self.async_write_ha_state()

        # Stop Modbus polling while the device is flashing and restarting
        self.coordinator.pause_updates()
        try:
            uploader = FirmwareUploader(self.hass, host, password=password)

            _LOGGER.info(
                "Starting firmware upload to %s (%s)",
                self.coordinator.config_entry.title,
                host,
            )
            await uploader.async_upload_firmware(firmware_path)

            _LOGGER.info(
                "Firmware upload complete, waiting %d seconds for device restart",
                FirmwareUploader.get_restart_delay(),
            )
            await asyncio.sleep(FirmwareUploader.get_restart_delay())

        except FirmwareUploadError as err:
            _LOGGER.exception("Firmware upload failed")
            msg = f"Firmware upload failed: {err}"
            raise HomeAssistantError(msg) from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during firmware update")
            msg = f"Firmware update failed: {err}"
            raise HomeAssistantError(msg) from err
        finally:
            self.coordinator.resume_updates()
            self._attr_in_progress = False
            self.async_write_ha_state()

        # Read the version the device reports after restarting
        await self.coordinator.async_refresh()
        self._verify_installed_version(expected_version)

        _LOGGER.info(
            "Firmware update completed for %s",
            self.coordinator.config_entry.title,
        )

    def _verify_installed_version(self, expected_version: str | None) -> None:
        """
        Verify the device reports the flashed firmware after restarting.

        Raises:
            HomeAssistantError: If the device is unreachable or reports
                another version

        """
        if not self.coordinator.last_update_success:
            msg = (
                "Firmware was uploaded, but the device did not respond after "
                "restarting. Check the device."
            )
            raise HomeAssistantError(msg)

        installed_version = self._compute_installed_version()
        if installed_version != expected_version:
            msg = (
                f"Firmware was uploaded, but the device reports version "
                f"{installed_version} instead of {expected_version}"
            )
            raise HomeAssistantError(msg)
