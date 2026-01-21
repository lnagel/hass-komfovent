"""Firmware uploader for Komfovent integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# HTTP constants
HTTP_OK = 200
UPLOAD_ENDPOINT = "/g1.html"
FORM_FIELD_USERNAME = "1"
FORM_FIELD_PASSWORD = "2"  # noqa: S105
FORM_FIELD_FIRMWARE = "11111"

# Timeouts (in seconds)
CONNECT_TIMEOUT = 10
LOGIN_TIMEOUT = 30
# Upload timeout is long due to slow TCP transfer (~19 KB/s, ~57s for 1MB)
UPLOAD_TIMEOUT = 300
LOGOUT_TIMEOUT = 10

# Device restart delay (seconds)
DEVICE_RESTART_DELAY = 120


class FirmwareUploadError(Exception):
    """Exception raised when firmware upload fails."""


class FirmwareUploader:
    """
    Handles firmware upload to Komfovent devices.

    Uses HTTP form-based upload with IP-based session authentication.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        username: str = "user",
        password: str = "user",  # noqa: S107
    ) -> None:
        """
        Initialize the firmware uploader.

        Args:
            hass: Home Assistant instance
            host: Device hostname or IP address
            username: Login username (default: "user")
            password: Login password (default: "user")

        """
        self._hass = hass
        self._host = host
        self._username = username
        self._password = password
        self._base_url = f"http://{host}"

    async def async_upload_firmware(
        self,
        firmware_path: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> bool:
        """
        Upload firmware to the device.

        Args:
            firmware_path: Path to the firmware file
            progress_callback: Optional callback for progress (bytes_sent, total)

        Returns:
            True if upload was successful

        Raises:
            FirmwareUploadError: If upload fails

        """
        if not firmware_path.exists():
            msg = f"Firmware file not found: {firmware_path}"
            raise FirmwareUploadError(msg)

        if not firmware_path.name.endswith(".mbin"):
            msg = f"Invalid firmware file extension: {firmware_path.name}"
            raise FirmwareUploadError(msg)

        firmware_data = firmware_path.read_bytes()
        total_size = len(firmware_data)

        _LOGGER.info(
            "Starting firmware upload to %s (%d bytes)",
            self._host,
            total_size,
        )

        session = async_get_clientsession(self._hass)

        try:
            # Step 1: Login
            await self._async_login(session)
            _LOGGER.debug("Login successful")

            # Step 2: Upload firmware
            await self._async_upload(
                session,
                firmware_path.name,
                firmware_data,
                progress_callback,
            )
            _LOGGER.info("Firmware upload completed successfully")

            # Step 3: Logout (best effort)
            try:
                await self._async_logout(session)
                _LOGGER.debug("Logout successful")
            except (aiohttp.ClientError, TimeoutError, OSError):
                _LOGGER.debug("Logout failed (device may be restarting)")

        except aiohttp.ClientError as err:
            msg = f"Network error during upload: {err}"
            raise FirmwareUploadError(msg) from err
        except TimeoutError as err:
            msg = "Upload timed out"
            raise FirmwareUploadError(msg) from err
        else:
            return True

    async def _async_login(self, session: aiohttp.ClientSession) -> None:
        """
        Perform login to establish session.

        Args:
            session: aiohttp client session

        Raises:
            FirmwareUploadError: If login fails

        """
        url = f"{self._base_url}{UPLOAD_ENDPOINT}"
        data = aiohttp.FormData()
        data.add_field(FORM_FIELD_USERNAME, self._username)
        data.add_field(FORM_FIELD_PASSWORD, self._password)

        timeout = aiohttp.ClientTimeout(total=LOGIN_TIMEOUT)
        async with session.post(url, data=data, timeout=timeout) as response:
            if response.status != HTTP_OK:
                msg = f"Login failed with HTTP {response.status}"
                raise FirmwareUploadError(msg)

    async def _async_upload(
        self,
        session: aiohttp.ClientSession,
        filename: str,
        firmware_data: bytes,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """
        Upload firmware file.

        Args:
            session: aiohttp client session
            filename: Name of the firmware file
            firmware_data: Firmware binary content
            progress_callback: Optional progress callback

        Raises:
            FirmwareUploadError: If upload fails

        """
        url = f"{self._base_url}{UPLOAD_ENDPOINT}"

        # Create multipart form data
        data = aiohttp.FormData()
        data.add_field(FORM_FIELD_USERNAME, self._username)
        data.add_field(FORM_FIELD_PASSWORD, self._password)
        data.add_field(
            FORM_FIELD_FIRMWARE,
            firmware_data,
            filename=filename,
            content_type="application/octet-stream",
        )

        timeout = aiohttp.ClientTimeout(total=UPLOAD_TIMEOUT)

        try:
            async with session.post(url, data=data, timeout=timeout) as response:
                if response.status != HTTP_OK:
                    msg = f"Upload failed with HTTP {response.status}"
                    raise FirmwareUploadError(msg)
                # Read response to complete the request
                await response.read()
        except TimeoutError as err:
            msg = "Upload timed out - device may have slow connection or be processing"
            raise FirmwareUploadError(msg) from err

        # Call progress callback with completion
        if progress_callback:
            progress_callback(len(firmware_data), len(firmware_data))

    async def _async_logout(self, session: aiohttp.ClientSession) -> None:
        """
        Perform logout (best effort).

        Args:
            session: aiohttp client session

        """
        # The device may restart after upload, so this is best-effort
        url = f"{self._base_url}{UPLOAD_ENDPOINT}"

        # Send empty form to logout
        data = aiohttp.FormData()
        data.add_field(FORM_FIELD_USERNAME, "")
        data.add_field(FORM_FIELD_PASSWORD, "")

        timeout = aiohttp.ClientTimeout(total=LOGOUT_TIMEOUT)
        try:
            async with session.post(url, data=data, timeout=timeout):
                pass
        except (aiohttp.ClientError, TimeoutError):
            # Ignore errors - device may be restarting
            pass

    @staticmethod
    def get_restart_delay() -> int:
        """
        Get the expected device restart delay in seconds.

        Returns:
            Number of seconds to wait for device restart

        """
        return DEVICE_RESTART_DELAY
