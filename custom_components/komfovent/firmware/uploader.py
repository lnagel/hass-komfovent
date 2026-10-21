"""Firmware uploader for Komfovent integration."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
from aiofiles import os as aio_os
from aiohttp import hdrs
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.komfovent.const import USER_AGENT

if TYPE_CHECKING:
    from pathlib import Path

    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# The device reports the upload result in <td id="st">Status: ...</td>
_STATUS_PATTERN = re.compile(r'<td\s+id="st">\s*(.*?)\s*</td>', re.IGNORECASE)

# HTTP constants
HTTP_OK = 200
UPLOAD_ENDPOINT = "/g1.html"
HEADERS = {hdrs.USER_AGENT: USER_AGENT}
FORM_FIELD_USERNAME = "1"
FORM_FIELD_PASSWORD = "2"  # noqa: S105
FORM_FIELD_FIRMWARE = "11111"

# Factory credentials; the device restores this password after every upgrade
DEFAULT_USERNAME = "user"
DEFAULT_PASSWORD = "user"  # noqa: S105

# Timeouts (in seconds)
LOGIN_TIMEOUT = 30
# Upload timeout is long due to slow TCP transfer (~19 KB/s, ~57s for 1MB)
UPLOAD_TIMEOUT = 300
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
        password: str | None = None,
    ) -> None:
        """
        Initialize the firmware uploader.

        Args:
            hass: Home Assistant instance
            host: Device hostname or IP address
            password: Login password; blank uses the default password

        """
        self._hass = hass
        self._host = host
        # Passwords to try in order, without duplicates
        self._passwords = list(
            dict.fromkeys(p for p in (password, DEFAULT_PASSWORD) if p)
        )
        self._base_url = f"http://{host}"

    async def async_upload_firmware(
        self,
        firmware_path: Path,
    ) -> None:
        """
        Upload firmware to the device.

        Args:
            firmware_path: Path to the firmware file

        Raises:
            FirmwareUploadError: If upload fails

        """
        if not await aio_os.path.exists(firmware_path):
            msg = f"Firmware file not found: {firmware_path}"
            raise FirmwareUploadError(msg)

        if not firmware_path.name.endswith(".mbin"):
            msg = f"Invalid firmware file extension: {firmware_path.name}"
            raise FirmwareUploadError(msg)

        async with aiofiles.open(firmware_path, "rb") as f:
            firmware_data = await f.read()
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
            await self._async_upload(session, firmware_path.name, firmware_data)
            _LOGGER.info("Firmware upload completed successfully")

        except aiohttp.ClientError as err:
            msg = f"Network error during upload: {err}"
            raise FirmwareUploadError(msg) from err
        except TimeoutError as err:
            msg = "Upload timed out"
            raise FirmwareUploadError(msg) from err

    async def _async_login(self, session: aiohttp.ClientSession) -> None:
        """
        Perform login to establish session.

        Tries the configured password first and falls back to the default
        password, which the device restores after every firmware upgrade.

        Args:
            session: aiohttp client session

        Raises:
            FirmwareUploadError: If login fails

        """
        for password in self._passwords:
            if await self._async_try_login(session, password):
                if password != self._passwords[0]:
                    _LOGGER.warning(
                        "Configured password was rejected by %s, logged in with "
                        "the default password instead",
                        self._host,
                    )
                return

        msg = "Login failed: invalid credentials"
        raise FirmwareUploadError(msg)

    async def _async_try_login(
        self, session: aiohttp.ClientSession, password: str
    ) -> bool:
        """
        Attempt a single login with the given password.

        Args:
            session: aiohttp client session
            password: Password to log in with

        Returns:
            True if the device accepted the credentials

        Raises:
            FirmwareUploadError: If the device answers with an HTTP error

        """
        url = f"{self._base_url}{UPLOAD_ENDPOINT}"
        form_data = {
            FORM_FIELD_USERNAME: DEFAULT_USERNAME,
            FORM_FIELD_PASSWORD: password,
        }

        timeout = aiohttp.ClientTimeout(total=LOGIN_TIMEOUT)
        async with session.post(
            url, data=form_data, headers=HEADERS, timeout=timeout
        ) as response:
            if response.status != HTTP_OK:
                msg = f"Login failed with HTTP {response.status}"
                raise FirmwareUploadError(msg)
            body = await response.text(encoding="windows-1252")
            return 'value="Logout"' in body

    async def _async_upload(
        self,
        session: aiohttp.ClientSession,
        filename: str,
        firmware_data: bytes,
    ) -> None:
        """
        Upload firmware file.

        Args:
            session: aiohttp client session
            filename: Name of the firmware file
            firmware_data: Firmware binary content

        Raises:
            FirmwareUploadError: If upload fails

        """
        url = f"{self._base_url}{UPLOAD_ENDPOINT}"

        # File field only: the session is IP-based and extra fields confuse the device
        data = aiohttp.FormData()
        data.add_field(
            FORM_FIELD_FIRMWARE,
            firmware_data,
            filename=filename,
            content_type="application/octet-stream",
        )

        timeout = aiohttp.ClientTimeout(total=UPLOAD_TIMEOUT)

        try:
            async with session.post(
                url, data=data, headers=HEADERS, timeout=timeout
            ) as response:
                if response.status != HTTP_OK:
                    msg = f"Upload failed with HTTP {response.status}"
                    raise FirmwareUploadError(msg)
                # Parse response body for device status message
                body = await response.text(encoding="windows-1252")
                self._check_response_for_errors(body)
        except TimeoutError as err:
            msg = "Upload timed out - device may have slow connection or be processing"
            raise FirmwareUploadError(msg) from err

    @staticmethod
    def _check_response_for_errors(body: str) -> None:
        """
        Check the device response body for error messages.

        The device returns HTTP 200 even on errors, with the status
        in a <td id="st"> element.

        Args:
            body: The HTML response body

        Raises:
            FirmwareUploadError: If the response has no or an error status

        """
        match = _STATUS_PATTERN.search(body)
        if not match:
            # The device answers HTTP 200 even on errors, so the outcome is unknown
            msg = "Device did not report an upload status"
            raise FirmwareUploadError(msg)

        status = match.group(1)
        _LOGGER.debug("Device upload status: %s", status)

        status_lower = status.lower()
        if "error" in status_lower:
            raise FirmwareUploadError(status)
        if "success" not in status_lower:
            msg = f"Unexpected device response after upload: {status}"
            raise FirmwareUploadError(msg)
