"""Update platform for Komfovent."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers
from .const import DOMAIN, FIRMWARE_MIN_SUPPORTED_VERSION
from .firmware import format_version, get_controller_type_for_firmware
from .firmware.uploader import FirmwareUploader, FirmwareUploadError
from .helpers import build_device_info, get_controller_version

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator
    from .firmware.store import FirmwareStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent update entity."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime_data.coordinator
    store = runtime_data.firmware_store

    async_add_entities([KomfoventUpdateEntity(coordinator, store)])


class KomfoventUpdateEntity(CoordinatorEntity["KomfoventCoordinator"], UpdateEntity):
    """Representation of a Komfovent firmware update entity."""

    _attr_has_entity_name: ClassVar[bool] = True
    _attr_name: ClassVar[str] = "Firmware"
    _attr_device_class: ClassVar[UpdateDeviceClass] = UpdateDeviceClass.FIRMWARE
    _attr_supported_features: ClassVar[int] = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
    )
    coordinator: KomfoventCoordinator

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
        self._installing = False

    @property
    def installed_version(self) -> str | None:
        """Return the installed firmware version."""
        if not self.coordinator.data:
            return None

        raw_value = self.coordinator.data.get(registers.REG_FIRMWARE)
        if raw_value is None or raw_value == 0:
            return None

        try:
            version = get_controller_version(int(raw_value))
            return format_version(version)
        except (ValueError, TypeError):
            return None

    @property
    def latest_version(self) -> str | None:
        """Return the latest available firmware version."""
        controller_type = get_controller_type_for_firmware(self.coordinator.controller)
        if controller_type == "NA":
            return None

        return self._store.get_latest_version(controller_type)

    @property
    def release_url(self) -> str | None:
        """Return the URL for firmware release notes."""
        # Komfovent doesn't provide release notes URLs
        return None

    @property
    def in_progress(self) -> bool | int:
        """Return if an update is in progress."""
        return self._installing

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

        Returns True if the installed firmware version is >= v1.3.15.
        """
        if not self.coordinator.data:
            return False

        raw_value = self.coordinator.data.get(registers.REG_FIRMWARE)
        if raw_value is None or raw_value == 0:
            return False

        try:
            version = get_controller_version(int(raw_value))
        except (ValueError, TypeError):
            return False
        else:
            # Compare v1, v2, v3 with minimum supported version
            installed = (version[1], version[2], version[3])
            return installed >= FIRMWARE_MIN_SUPPORTED_VERSION

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
        if self._installing:
            msg = "Firmware update already in progress"
            raise HomeAssistantError(msg)

        # Check if firmware update is supported
        if not self._is_firmware_supported:
            min_ver = ".".join(map(str, FIRMWARE_MIN_SUPPORTED_VERSION))
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

        # Get device host
        host = self.coordinator.config_entry.data[CONF_HOST]

        self._installing = True
        self.async_write_ha_state()

        try:
            # Create uploader
            uploader = FirmwareUploader(self.hass, host)

            _LOGGER.info(
                "Starting firmware upload to %s (%s)",
                self.coordinator.config_entry.title,
                host,
            )

            # Upload firmware
            await uploader.async_upload_firmware(firmware_path)

            _LOGGER.info(
                "Firmware upload complete, waiting %d seconds for device restart",
                FirmwareUploader.get_restart_delay(),
            )

            # Set cooldown on coordinator to prevent Modbus errors during restart
            self.coordinator.set_cooldown(FirmwareUploader.get_restart_delay())

            # Wait for device to restart
            await asyncio.sleep(FirmwareUploader.get_restart_delay())

            # Request a refresh to get the new version
            await self.coordinator.async_request_refresh()

            _LOGGER.info(
                "Firmware update completed for %s",
                self.coordinator.config_entry.title,
            )

        except FirmwareUploadError as err:
            _LOGGER.exception("Firmware upload failed")
            msg = f"Firmware upload failed: {err}"
            raise HomeAssistantError(msg) from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during firmware update")
            msg = f"Firmware update failed: {err}"
            raise HomeAssistantError(msg) from err
        finally:
            self._installing = False
            self.async_write_ha_state()
