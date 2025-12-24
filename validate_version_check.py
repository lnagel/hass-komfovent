#!/usr/bin/env python3
"""
Validation script for Komfovent C6/C6M firmware version check process.

This script validates that we can:
1. Check the current firmware version via Modbus
2. Query the latest available firmware version from the device's web interface
3. Compare versions to determine if an update is available

Usage:
    python3 validate_version_check.py --host <device_ip> [--username user] [--password user]
"""

import argparse
import re
import sys
from typing import Any

import requests
from bs4 import BeautifulSoup


class KomfoventVersionChecker:
    """Check Komfovent C6/C6M firmware versions."""

    def __init__(self, host: str, username: str = "user", password: str = "user"):
        """Initialize the version checker.

        Args:
            host: IP address or hostname of the Komfovent device
            username: Web interface username (default: "user")
            password: Web interface password (default: "user")
        """
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"http://{host}"
        self.session = requests.Session()

    def login(self) -> bool:
        """Login to the device web interface.

        Returns:
            True if login successful, False otherwise
        """
        login_url = self.base_url
        print(f"1. Attempting to login to {login_url}...")

        try:
            # First, get the login page
            response = self.session.get(login_url, timeout=10)
            if response.status_code != 200:
                print(f"   ✗ Failed to access login page: {response.status_code}")
                return False

            # Attempt login (POST to root with credentials)
            login_data = {
                "username": self.username,
                "password": self.password,
            }

            response = self.session.post(
                login_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )

            if response.status_code == 200:
                print(f"   ✓ Login successful")
                return True
            else:
                print(f"   ✗ Login failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ✗ Login failed: {e}")
            return False

    def get_current_firmware_version(self) -> dict[str, Any]:
        """Get current firmware version from device web interface.

        Returns:
            Dictionary with version information:
            {
                "main_module": "CF-400-V_v1945",
                "main_module_version": "1945",
                "controller": "C6 1.3.18.21",
                "controller_version": "1.3.18.21",
                "panel1": "C6 1.1.3.14",
                "panel1_version": "1.1.3.14",
                "panel2": None,
                "panel2_version": None,
            }
        """
        print("\n2. Fetching current firmware versions...")
        result = {
            "main_module": None,
            "main_module_version": None,
            "controller": None,
            "controller_version": None,
            "panel1": None,
            "panel1_version": None,
            "panel2": None,
            "panel2_version": None,
        }

        try:
            # The INFORMATION section is typically on the main settings page
            # According to PDF, we need to navigate to SETTINGS
            response = self.session.get(self.base_url, timeout=10)

            if response.status_code != 200:
                print(f"   ✗ Failed to fetch page: {response.status_code}")
                return result

            # Parse the HTML to extract firmware versions
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for firmware version patterns in the HTML
            # Pattern 1: "Main module firmware: C6 1.3.18.21"
            # Pattern 2: "Control panel firmware (1): C6 1.1.3.14"

            # Try to find version info in the page
            text_content = soup.get_text()

            # Extract main module firmware
            main_pattern = r"(CF-\d+-[A-Z]_v\d+)"
            match = re.search(main_pattern, text_content)
            if match:
                result["main_module"] = match.group(1)
                # Extract version number
                version_match = re.search(r"v(\d+)", match.group(1))
                if version_match:
                    result["main_module_version"] = version_match.group(1)
                print(f"   ✓ Main module firmware: {result['main_module']}")

            # Extract controller firmware
            controller_pattern = r"C6[M]?\s+(\d+\.\d+\.\d+\.\d+)"
            matches = re.finditer(controller_pattern, text_content)

            versions_found = []
            for match in matches:
                version = match.group(1)
                if version not in versions_found:
                    versions_found.append(version)

            if len(versions_found) > 0:
                result["controller"] = f"C6 {versions_found[0]}"
                result["controller_version"] = versions_found[0]
                print(f"   ✓ Controller firmware: {result['controller']}")

            if len(versions_found) > 1:
                result["panel1"] = f"C6 {versions_found[1]}"
                result["panel1_version"] = versions_found[1]
                print(f"   ✓ Panel 1 firmware: {result['panel1']}")

            if len(versions_found) > 2:
                result["panel2"] = f"C6 {versions_found[2]}"
                result["panel2_version"] = versions_found[2]
                print(f"   ✓ Panel 2 firmware: {result['panel2']}")

            if not result["controller_version"]:
                print(f"   ⚠ Could not extract firmware versions from web interface")
                print(f"   ⚠ This is expected - we'll use Modbus instead")

        except requests.exceptions.RequestException as e:
            print(f"   ✗ Failed to fetch versions: {e}")
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")

        return result

    def check_latest_firmware_available(self) -> dict[str, Any]:
        """Check if latest firmware is available for download.

        According to the manufacturer documentation, firmware downloads are
        available at specific URLs, but these are blocked from external access.

        For local network access, the device may provide version information
        through its web interface or a dedicated API endpoint.

        Returns:
            Dictionary with latest version information
        """
        print("\n3. Checking for latest firmware...")
        result = {
            "available": False,
            "version": None,
            "url": None,
            "method": None,
        }

        # Option 1: Check if device has a built-in update check endpoint
        # This is speculative - would need to be verified with actual device
        update_endpoints = [
            "/update_check",
            "/api/firmware/latest",
            "/firmware/check",
        ]

        for endpoint in update_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✓ Found update endpoint: {endpoint}")
                    result["available"] = True
                    result["url"] = url
                    result["method"] = "device_api"
                    # Try to parse response for version info
                    try:
                        data = response.json()
                        result["version"] = data.get("version", data.get("latest_version"))
                    except:
                        pass
                    break
            except:
                continue

        if not result["available"]:
            print("   ⚠ No update check endpoint found on device")
            print("   ⚠ Latest firmware must be obtained from manufacturer's website")
            print("   ⚠ Users must download firmware manually and upload via web interface")

        return result

    def compare_versions(self, current: str, latest: str) -> str:
        """Compare two version strings.

        Args:
            current: Current version (e.g., "1.3.17.20")
            latest: Latest version (e.g., "1.3.28.38")

        Returns:
            "update_available", "up_to_date", or "unknown"
        """
        try:
            current_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]

            if current_parts < latest_parts:
                return "update_available"
            elif current_parts == latest_parts:
                return "up_to_date"
            else:
                return "unknown"  # Current is newer than latest?
        except (ValueError, AttributeError):
            return "unknown"


def main():
    """Run validation tests."""
    parser = argparse.ArgumentParser(
        description="Validate Komfovent firmware version check process"
    )
    parser.add_argument(
        "--host",
        required=True,
        help="IP address or hostname of Komfovent device"
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
        "--test-version",
        help="Test version for comparison (e.g., 1.3.28.38)"
    )

    args = parser.parse_args()

    print("="*70)
    print("KOMFOVENT FIRMWARE VERSION CHECK - VALIDATION")
    print("="*70)
    print(f"\nTarget device: {args.host}")

    # Initialize checker
    checker = KomfoventVersionChecker(
        host=args.host,
        username=args.username,
        password=args.password
    )

    # Step 1: Login
    if not checker.login():
        print("\n✗ VALIDATION FAILED: Could not login to device")
        sys.exit(1)

    # Step 2: Get current firmware version
    current_versions = checker.get_current_firmware_version()

    # Step 3: Check for latest firmware
    latest_info = checker.check_latest_firmware_available()

    # Step 4: Version comparison test
    print("\n4. Version comparison test...")
    if args.test_version and current_versions.get("controller_version"):
        current = current_versions["controller_version"]
        latest = args.test_version

        comparison = checker.compare_versions(current, latest)
        print(f"   Current: {current}")
        print(f"   Latest:  {latest}")
        print(f"   Result:  {comparison}")

        if comparison == "update_available":
            print(f"   ✓ Update is available!")
        elif comparison == "up_to_date":
            print(f"   ✓ Firmware is up to date")
    else:
        print("   ⚠ Skipping version comparison (no test version provided)")

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    success = True

    if current_versions.get("controller_version"):
        print("✓ Successfully retrieved current firmware version")
    else:
        print("✗ Could not retrieve current firmware version")
        success = False

    print("\nRECOMMENDATIONS:")
    print("-" * 70)
    print("1. Use Modbus to read firmware version (register 1000)")
    print("   This is already implemented in the integration")
    print("")
    print("2. Firmware updates require manual download from manufacturer")
    print("   Users must:")
    print("   - Download firmware from Komfovent website")
    print("   - Upload via device web interface (http://[IP]/g1.html)")
    print("")
    print("3. UpdateEntity should:")
    print("   - Show current installed version (from Modbus)")
    print("   - Provide link to manufacturer download page")
    print("   - Provide instructions for manual update")
    print("   - Optionally: Support uploading downloaded firmware file")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
