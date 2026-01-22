"""
Validation script for Komfovent C6/C6M firmware update process.

This script validates the firmware update workflow:
1. Upload firmware file to device
2. Monitor update progress
3. Verify successful update

WARNING: This script performs ACTUAL firmware updates on your device.
Only use for testing in a controlled environment.

Usage:
    python3 validate_firmware_update.py --host <ip> --firmware <path> [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_OK = 200

# File size thresholds (bytes)
MIN_FIRMWARE_SIZE = 100_000  # 100KB
MAX_FIRMWARE_SIZE = 10_000_000  # 10MB

# Timeout constants (in seconds)
LOGIN_TIMEOUT = 10
UPLOAD_TIMEOUT = 120
VERIFY_TIMEOUT = 10
PING_TIMEOUT = 5
PING_INTERVAL = 10
RESTART_WAIT = 60
DEFAULT_UPDATE_TIMEOUT = 300  # 5 minutes

# Default credentials
DEFAULT_USERNAME = os.getenv("KOMFOVENT_USERNAME", "user")
DEFAULT_PASSWORD = os.getenv("KOMFOVENT_PASSWORD", "user")


class KomfoventFirmwareUpdater:
    """Handle Komfovent C6/C6M firmware updates."""

    def __init__(
        self,
        host: str,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
    ) -> None:
        """
        Initialize the firmware updater.

        Args:
            host: IP address or hostname of the Komfovent device
            username: Web interface username
            password: Web interface password

        """
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"http://{host}"
        self.upload_url = f"{self.base_url}/g1.html"
        self.session = requests.Session()

    def login(self) -> bool:
        """
        Login to the device web interface.

        C6 uses IP-based sessions with form fields:
        - Field "1": username
        - Field "2": password

        Returns:
            True if login successful, False otherwise

        """
        logger.info("1. Logging in to %s...", self.upload_url)

        try:
            login_data = {"1": self.username, "2": self.password}
            response = self.session.post(
                self.upload_url,
                data=login_data,
                timeout=LOGIN_TIMEOUT,
                allow_redirects=True,
            )
        except requests.exceptions.RequestException:
            logger.exception("Login failed")
            return False

        if response.status_code == HTTP_OK:
            if "Incorrect password" in response.text:
                logger.error("Login failed: Incorrect password")
                return False
            if 'name="11111"' in response.text:
                logger.info("Login successful")
                return True
            logger.info("Login successful")
            return True

        logger.error("Login failed: HTTP %d", response.status_code)
        return False

    def validate_firmware_file(self, firmware_path: str) -> dict[str, Any]:
        """
        Validate firmware file before upload.

        Args:
            firmware_path: Path to firmware file

        Returns:
            Dictionary with validation results

        """
        logger.info("2. Validating firmware file...")
        result: dict[str, Any] = {
            "valid": False,
            "path": firmware_path,
            "size": 0,
            "type": None,
            "error": None,
        }

        path = Path(firmware_path)

        if not path.exists():
            result["error"] = "File does not exist"
            logger.error("%s", result["error"])
            return result

        if path.suffix not in [".bin", ".mbin"]:
            result["error"] = "Invalid file type (must be .bin or .mbin)"
            logger.error("%s", result["error"])
            return result

        result["type"] = path.suffix[1:]
        result["size"] = path.stat().st_size

        if result["size"] < MIN_FIRMWARE_SIZE:
            logger.warning("File too small (%d bytes)", result["size"])
        elif result["size"] > MAX_FIRMWARE_SIZE:
            logger.warning("File too large (%d bytes)", result["size"])

        result["valid"] = True
        logger.info("File is valid")
        logger.info("Type: %s", result["type"])
        logger.info("Size: %d bytes", result["size"])

        return result

    def upload_firmware(
        self, firmware_path: str, *, dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Upload firmware file to device.

        Args:
            firmware_path: Path to firmware file
            dry_run: If True, don't actually upload

        Returns:
            Dictionary with upload results

        """
        logger.info("3. Uploading firmware...")
        result: dict[str, Any] = {
            "success": False,
            "status": None,
            "message": None,
            "error": None,
        }

        if dry_run:
            logger.warning("DRY RUN MODE - not actually uploading")
            result["success"] = True
            result["message"] = "Dry run - no upload performed"
            return result

        path = Path(firmware_path)

        try:
            with path.open("rb") as f:
                files = {"11111": (path.name, f, "application/octet-stream")}

                logger.info("Uploading %s to %s...", path.name, self.upload_url)
                logger.info("This may take 30-60 seconds...")

                response = self.session.post(
                    self.upload_url,
                    files=files,
                    timeout=UPLOAD_TIMEOUT,
                )

                result["status"] = response.status_code
                self._parse_upload_response(response, result)

        except requests.exceptions.RequestException:
            logger.exception("Upload error")
            result["error"] = "Request failed"

        return result

    def _parse_upload_response(
        self, response: requests.Response, result: dict[str, Any]
    ) -> None:
        """Parse the upload response and update result dict."""
        if response.status_code != HTTP_OK:
            result["error"] = f"HTTP {response.status_code}"
            logger.error("Upload failed: %s", result["error"])
            return

        response_text = response.text.lower()

        if "success" in response_text or "uploaded" in response_text:
            result["success"] = True
            result["message"] = "Firmware uploaded successfully"
            logger.info("Upload successful")

            if "device is restarting" in response_text:
                logger.info("Device is restarting")
                result["message"] += " - device restarting"

            if "panel firmware upload success" in response_text:
                logger.info("Panel firmware will also be updated")
                result["message"] += " - panel update included"

        elif "error" in response_text:
            result["error"] = "Upload failed (see device response)"
            logger.error("Upload failed")
            logger.error("Response: %s", response.text[:200])
        else:
            result["success"] = True
            result["message"] = "Upload completed (verify manually)"
            logger.warning("Upload completed with unclear response")

    def monitor_update_progress(self, timeout: int = DEFAULT_UPDATE_TIMEOUT) -> bool:
        """
        Monitor firmware update progress.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if update completed successfully

        """
        logger.info("4. Monitoring update progress...")
        logger.info("Maximum wait time: %d seconds", timeout)

        logger.info("Waiting for device to restart (%d seconds)...", RESTART_WAIT)
        time.sleep(RESTART_WAIT)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(self.base_url, timeout=PING_TIMEOUT)

                if response.status_code == HTTP_OK:
                    logger.info("Device is responding")
                    return True

            except requests.exceptions.RequestException:
                pass

            time.sleep(PING_INTERVAL)
            elapsed = int(time.time() - start_time)
            logger.info("Still waiting... (%ds / %ds)", elapsed, timeout)

        logger.error("Timeout waiting for device to respond")
        return False

    def verify_update(self, expected_version: str | None = None) -> dict[str, Any]:
        """
        Verify firmware update was successful.

        Args:
            expected_version: Expected firmware version after update

        Returns:
            Dictionary with verification results

        """
        logger.info("5. Verifying firmware update...")
        result: dict[str, Any] = {
            "success": False,
            "current_version": None,
            "matches_expected": None,
        }

        try:
            response = self.session.get(self.upload_url, timeout=VERIFY_TIMEOUT)

            if response.status_code == HTTP_OK:
                logger.info("Device is accessible after update")
                result["success"] = True

                if expected_version:
                    if expected_version in response.text:
                        result["matches_expected"] = True
                        logger.info("Found expected version: %s", expected_version)
                    else:
                        result["matches_expected"] = False
                        logger.warning("Could not verify version %s", expected_version)
                        logger.warning("Manual verification recommended")
            else:
                logger.error("Device returned status %d", response.status_code)

        except requests.exceptions.RequestException:
            logger.exception("Verification failed")
            result["error"] = "Request failed"

        return result


def _log_header(title: str) -> None:
    """Log a section header."""
    logger.info("=" * 70)
    logger.info(title)
    logger.info("=" * 70)


def _create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Validate Komfovent firmware update process"
    )
    parser.add_argument(
        "--host", required=True, help="IP address or hostname of Komfovent device"
    )
    parser.add_argument(
        "--firmware", required=True, help="Path to firmware file (.bin or .mbin)"
    )
    parser.add_argument(
        "--username", default=DEFAULT_USERNAME, help="Web interface username"
    )
    parser.add_argument(
        "--password", default=DEFAULT_PASSWORD, help="Web interface password"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without actually uploading firmware",
    )
    parser.add_argument(
        "--expected-version",
        help="Expected firmware version after update (for verification)",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt (for automated testing)",
    )
    parser.add_argument(
        "--skip-wait", action="store_true",
        help="Skip waiting for device restart (for mock testing)",
    )
    return parser


def _log_dry_run_success() -> None:
    """Log dry run success message."""
    logger.info("DRY RUN VALIDATION SUCCESSFUL")
    logger.info("The firmware update process would:")
    logger.info("1. Login to device")
    logger.info("2. Validate firmware file")
    logger.info("3. Upload firmware to http://[IP]/g1.html")
    logger.info("4. Wait for device restart (1-2 minutes)")
    logger.info("5. Verify device is accessible")


def _log_summary(verify_result: dict[str, Any]) -> None:
    """Log final summary and exit if failed."""
    _log_header("UPDATE VALIDATION SUMMARY")

    if verify_result["success"]:
        logger.info("Firmware update completed successfully")
        logger.info("RECOMMENDATIONS:")
        logger.info("-" * 70)
        logger.info("1. Verify firmware version via Modbus (register 1000)")
        logger.info("2. Check device functionality")
        logger.info("3. Monitor for any alarms or errors")
    else:
        logger.error("Update verification failed")
        logger.info("Next steps:")
        logger.info("1. Check if device is accessible")
        logger.info("2. Try power cycling the device")
        logger.info("3. Check firmware version manually")
        sys.exit(1)


def main() -> None:
    """Run firmware update validation."""
    args = _create_parser().parse_args()

    _log_header("KOMFOVENT FIRMWARE UPDATE - VALIDATION")
    logger.info("Target device: %s", args.host)
    logger.info("Firmware file: %s", args.firmware)
    logger.info("Mode: %s", "DRY RUN" if args.dry_run else "LIVE UPDATE")

    if not args.dry_run and not args.yes:
        logger.warning("This will perform an ACTUAL firmware update!")
        logger.warning("Only proceed if you are prepared to update your device.")
        response = input("\nType 'yes' to continue: ")
        if response.lower() != "yes":
            logger.info("Aborted.")
            sys.exit(0)

    updater = KomfoventFirmwareUpdater(
        host=args.host, username=args.username, password=args.password
    )

    if not updater.login():
        logger.error("VALIDATION FAILED: Could not login to device")
        sys.exit(1)

    validation = updater.validate_firmware_file(args.firmware)
    if not validation["valid"]:
        logger.error("VALIDATION FAILED: %s", validation["error"])
        sys.exit(1)

    upload_result = updater.upload_firmware(args.firmware, dry_run=args.dry_run)
    if not upload_result["success"]:
        logger.error("UPLOAD FAILED: %s", upload_result.get("error", "Unknown error"))
        sys.exit(1)

    if args.dry_run:
        _log_dry_run_success()
        sys.exit(0)

    if args.skip_wait:
        logger.info("4. Skipping device restart wait (--skip-wait)")
    elif not updater.monitor_update_progress():
        logger.warning("Update monitoring timed out")
        logger.warning("Device may still be updating - check manually")
        sys.exit(1)

    _log_summary(updater.verify_update(args.expected_version))


if __name__ == "__main__":
    main()
