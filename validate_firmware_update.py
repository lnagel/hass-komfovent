"""
Validation script for Komfovent C6/C6M firmware update process.

This script validates the firmware update workflow:
1. Upload firmware file to device
2. Monitor update progress
3. Verify successful update

WARNING: This script performs ACTUAL firmware updates on your device.
Only use for testing in a controlled environment.

Usage:
    python3 validate_firmware_update.py --host <device_ip> --firmware <path_to_firmware.mbin> [--dry-run]
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import requests


class KomfoventFirmwareUpdater:
    """Handle Komfovent C6/C6M firmware updates."""

    def __init__(self, host: str, username: str = "user", password: str = "user"):
        """Initialize the firmware updater.

        Args:
            host: IP address or hostname of the Komfovent device
            username: Web interface username (default: "user")
            password: Web interface password (default: "user")
        """
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"http://{host}"
        self.upload_url = f"{self.base_url}/g1.html"
        self.session = requests.Session()

    def login(self) -> bool:
        """Login to the device web interface.

        C6 uses IP-based sessions with form fields:
        - Field "1": username
        - Field "2": password

        Returns:
            True if login successful, False otherwise
        """
        print(f"1. Logging in to {self.upload_url}...")

        try:
            # C6 login uses form fields "1" (username) and "2" (password)
            login_data = {
                "1": self.username,
                "2": self.password,
            }

            response = self.session.post(
                self.upload_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 200:
                # Check if we got the upload form (success) or login form with error
                if "Incorrect password" in response.text:
                    print("   ✗ Login failed: Incorrect password")
                    return False
                if 'name="11111"' in response.text:
                    print("   ✓ Login successful")
                    return True
                # Assume success if we get 200 and no error
                print("   ✓ Login successful")
                return True
            else:
                print(f"   ✗ Login failed: HTTP {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ✗ Login failed: {e}")
            return False

    def validate_firmware_file(self, firmware_path: str) -> dict[str, Any]:
        """Validate firmware file before upload.

        Args:
            firmware_path: Path to firmware file

        Returns:
            Dictionary with validation results
        """
        print(f"\n2. Validating firmware file...")
        result = {
            "valid": False,
            "path": firmware_path,
            "size": 0,
            "type": None,
            "error": None,
        }

        try:
            path = Path(firmware_path)

            # Check file exists
            if not path.exists():
                result["error"] = "File does not exist"
                print(f"   ✗ {result['error']}")
                return result

            # Check file extension
            if path.suffix not in [".bin", ".mbin"]:
                result["error"] = "Invalid file type (must be .bin or .mbin)"
                print(f"   ✗ {result['error']}")
                return result

            result["type"] = path.suffix[1:]  # Remove dot
            result["size"] = path.stat().st_size

            # Check file size (typical firmware is 500KB - 5MB)
            if result["size"] < 100_000:  # Less than 100KB is suspicious
                result["error"] = f"File too small ({result['size']} bytes)"
                print(f"   ⚠ Warning: {result['error']}")
            elif result["size"] > 10_000_000:  # More than 10MB is suspicious
                result["error"] = f"File too large ({result['size']} bytes)"
                print(f"   ⚠ Warning: {result['error']}")

            result["valid"] = True
            print(f"   ✓ File is valid")
            print(f"   ✓ Type: {result['type']}")
            print(f"   ✓ Size: {result['size']:,} bytes")

        except Exception as e:
            result["error"] = str(e)
            print(f"   ✗ Validation error: {e}")

        return result

    def upload_firmware(
        self,
        firmware_path: str,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """Upload firmware file to device.

        Args:
            firmware_path: Path to firmware file
            dry_run: If True, don't actually upload

        Returns:
            Dictionary with upload results
        """
        print(f"\n3. Uploading firmware...")
        result = {
            "success": False,
            "status": None,
            "message": None,
            "error": None,
        }

        if dry_run:
            print(f"   ⚠ DRY RUN MODE - not actually uploading")
            result["success"] = True
            result["message"] = "Dry run - no upload performed"
            return result

        try:
            path = Path(firmware_path)

            # Prepare multipart upload - form field must be "11111" per C6 protocol
            with open(path, "rb") as f:
                files = {
                    "11111": (path.name, f, "application/octet-stream")
                }

                print(f"   → Uploading {path.name} to {self.upload_url}...")
                print(f"   → This may take 30-60 seconds...")

                response = self.session.post(
                    self.upload_url,
                    files=files,
                    timeout=120  # Firmware upload can take time
                )

                result["status"] = response.status_code

                if response.status_code == 200:
                    # Check response for success/error messages
                    response_text = response.text.lower()

                    if "success" in response_text or "uploaded" in response_text:
                        result["success"] = True
                        result["message"] = "Firmware uploaded successfully"
                        print(f"   ✓ Upload successful")

                        # Check for specific success messages
                        if "device is restarting" in response_text:
                            print(f"   ✓ Device is restarting")
                            result["message"] += " - device restarting"

                        if "panel firmware upload success" in response_text:
                            print(f"   ✓ Panel firmware will also be updated")
                            result["message"] += " - panel update included"

                    elif "error" in response_text:
                        result["error"] = "Upload failed (see device response)"
                        print(f"   ✗ Upload failed")
                        print(f"   ✗ Response: {response.text[:200]}")
                    else:
                        # Unclear response
                        result["success"] = True
                        result["message"] = "Upload completed (verify manually)"
                        print(f"   ⚠ Upload completed with unclear response")

                else:
                    result["error"] = f"HTTP {response.status_code}"
                    print(f"   ✗ Upload failed: {result['error']}")

        except requests.exceptions.RequestException as e:
            result["error"] = str(e)
            print(f"   ✗ Upload error: {e}")
        except Exception as e:
            result["error"] = str(e)
            print(f"   ✗ Unexpected error: {e}")

        return result

    def monitor_update_progress(self, timeout: int = 300) -> bool:
        """Monitor firmware update progress.

        Args:
            timeout: Maximum time to wait in seconds (default: 300 = 5 minutes)

        Returns:
            True if update completed successfully
        """
        print(f"\n4. Monitoring update progress...")
        print(f"   ⏱ Maximum wait time: {timeout} seconds")

        # Wait for device to restart
        print(f"   → Waiting for device to restart (60 seconds)...")
        time.sleep(60)

        # Try to reconnect
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    self.base_url,
                    timeout=5
                )

                if response.status_code == 200:
                    print(f"   ✓ Device is responding")
                    return True

            except requests.exceptions.RequestException:
                # Device still updating/restarting
                pass

            time.sleep(10)
            elapsed = int(time.time() - start_time)
            print(f"   ⏱ Still waiting... ({elapsed}s / {timeout}s)")

        print(f"   ✗ Timeout waiting for device to respond")
        return False

    def verify_update(self, expected_version: str = None) -> dict[str, Any]:
        """Verify firmware update was successful.

        Args:
            expected_version: Expected firmware version after update

        Returns:
            Dictionary with verification results
        """
        print(f"\n5. Verifying firmware update...")
        result = {
            "success": False,
            "current_version": None,
            "matches_expected": None,
        }

        try:
            # Check if device is accessible via the upload endpoint
            # (The base URL may redirect or require different handling)
            response = self.session.get(self.upload_url, timeout=10)

            if response.status_code == 200:
                print(f"   ✓ Device is accessible after update")
                result["success"] = True

                if expected_version:
                    # Try to extract version from response
                    # This is a simplified check
                    if expected_version in response.text:
                        result["matches_expected"] = True
                        print(f"   ✓ Found expected version: {expected_version}")
                    else:
                        result["matches_expected"] = False
                        print(f"   ⚠ Could not verify version {expected_version}")
                        print(f"   ⚠ Manual verification recommended")
            else:
                print(f"   ✗ Device returned status {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"   ✗ Verification failed: {e}")
            result["error"] = str(e)

        return result


def main():
    """Run firmware update validation."""
    parser = argparse.ArgumentParser(
        description="Validate Komfovent firmware update process"
    )
    parser.add_argument(
        "--host",
        required=True,
        help="IP address or hostname of Komfovent device"
    )
    parser.add_argument(
        "--firmware",
        required=True,
        help="Path to firmware file (.bin or .mbin)"
    )
    parser.add_argument(
        "--username",
        default="user",
        help="Web interface username (default: user)"
    )
    parser.add_argument(
        "--password",
        default="user",
        help="Web interface password (default: user)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without actually uploading firmware"
    )
    parser.add_argument(
        "--expected-version",
        help="Expected firmware version after update (for verification)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt (for automated testing)"
    )
    parser.add_argument(
        "--skip-wait",
        action="store_true",
        help="Skip waiting for device restart (for mock testing)"
    )

    args = parser.parse_args()

    print("="*70)
    print("KOMFOVENT FIRMWARE UPDATE - VALIDATION")
    print("="*70)
    print(f"\nTarget device: {args.host}")
    print(f"Firmware file: {args.firmware}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")

    if not args.dry_run and not args.yes:
        print("\n⚠ WARNING: This will perform an ACTUAL firmware update!")
        print("⚠ Only proceed if you are prepared to update your device.")
        response = input("\nType 'yes' to continue: ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    # Initialize updater
    updater = KomfoventFirmwareUpdater(
        host=args.host,
        username=args.username,
        password=args.password
    )

    # Step 1: Login
    if not updater.login():
        print("\n✗ VALIDATION FAILED: Could not login to device")
        sys.exit(1)

    # Step 2: Validate firmware file
    validation = updater.validate_firmware_file(args.firmware)
    if not validation["valid"]:
        print(f"\n✗ VALIDATION FAILED: {validation['error']}")
        sys.exit(1)

    # Step 3: Upload firmware
    upload_result = updater.upload_firmware(
        args.firmware,
        dry_run=args.dry_run
    )

    if not upload_result["success"]:
        print(f"\n✗ UPLOAD FAILED: {upload_result.get('error', 'Unknown error')}")
        sys.exit(1)

    if args.dry_run:
        print("\n✓ DRY RUN VALIDATION SUCCESSFUL")
        print("\nThe firmware update process would:")
        print("1. ✓ Login to device")
        print("2. ✓ Validate firmware file")
        print("3. ✓ Upload firmware to http://[IP]/g1.html")
        print("4. ⏱ Wait for device restart (1-2 minutes)")
        print("5. ✓ Verify device is accessible")
        sys.exit(0)

    # Step 4: Monitor update progress (skip for mock testing)
    if args.skip_wait:
        print("\n4. Skipping device restart wait (--skip-wait)")
    else:
        if not updater.monitor_update_progress():
            print("\n⚠ WARNING: Update monitoring timed out")
            print("⚠ Device may still be updating - check manually")
            sys.exit(1)

    # Step 5: Verify update
    verify_result = updater.verify_update(args.expected_version)

    # Summary
    print("\n" + "="*70)
    print("UPDATE VALIDATION SUMMARY")
    print("="*70)

    if verify_result["success"]:
        print("✓ Firmware update completed successfully")
        print("\nRECOMMENDATIONS:")
        print("-" * 70)
        print("1. Verify firmware version via Modbus (register 1000)")
        print("2. Check device functionality")
        print("3. Monitor for any alarms or errors")
    else:
        print("✗ Update verification failed")
        print("\nNext steps:")
        print("1. Check if device is accessible")
        print("2. Try power cycling the device")
        print("3. Check firmware version manually")
        sys.exit(1)


if __name__ == "__main__":
    main()
