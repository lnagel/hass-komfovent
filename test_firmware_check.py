#!/usr/bin/env python3
"""Test script to validate firmware version check process for Komfovent C6/C6M controllers."""

import re
import sys
from urllib.parse import unquote

import requests


# Firmware download URLs from manufacturer
FIRMWARE_URLS = {
    "mbin": "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin",
    "bin": "http://www.komfovent.com/Update/Controllers/firmware.php?file=bin",
}


def extract_version_from_filename(filename: str) -> tuple[str, str] | None:
    """
    Extract version information from firmware filename.

    Expected patterns:
    - C6_1_3_17_20_20180428.bin
    - C6_1_3_28_38_20180428.mbin

    Args:
        filename: Firmware filename

    Returns:
        Tuple of (version_string, date_string) or None if not found
    """
    # Pattern: C6_v1_v2_v3_v4_date.ext
    pattern = r"C6[M]?_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)\.(m?bin)"

    match = re.search(pattern, filename, re.IGNORECASE)
    if match:
        v1, v2, v3, v4, date, ext = match.groups()
        version = f"{v1}.{v2}.{v3}.{v4}"
        return version, date

    return None


def check_firmware_version(firmware_type: str = "mbin") -> dict:
    """
    Check firmware version using HEAD request.

    Args:
        firmware_type: Type of firmware file ("mbin" or "bin")

    Returns:
        Dictionary with version check results
    """
    url = FIRMWARE_URLS.get(firmware_type)
    if not url:
        return {"error": f"Unknown firmware type: {firmware_type}"}

    print(f"\n{'='*70}")
    print(f"Testing firmware version check for {firmware_type.upper()} files")
    print(f"{'='*70}")
    print(f"URL: {url}")

    result = {
        "url": url,
        "firmware_type": firmware_type,
        "success": False,
    }

    try:
        # Try HEAD request first (recommended for version checks)
        print("\n1. Sending HEAD request...")
        head_response = requests.head(url, allow_redirects=True, timeout=10)

        print(f"   Status Code: {head_response.status_code}")
        print(f"   Headers:")
        for key, value in head_response.headers.items():
            print(f"     {key}: {value}")

        # Check Content-Disposition header for filename
        content_disposition = head_response.headers.get("Content-Disposition", "")
        filename = None

        if content_disposition:
            # Extract filename from Content-Disposition header
            # Example: attachment; filename="C6_1_3_17_20_20180428.bin"
            match = re.search(r'filename=[\'\"]?([^\'\"]+)[\'\"]?', content_disposition)
            if match:
                filename = unquote(match.group(1))
                print(f"\n2. Filename from Content-Disposition: {filename}")

        # If no filename in headers, check Content-Location or final URL
        if not filename:
            content_location = head_response.headers.get("Content-Location", "")
            if content_location:
                filename = content_location.split("/")[-1]
                print(f"\n2. Filename from Content-Location: {filename}")

        if not filename and head_response.url != url:
            # Get filename from final redirected URL
            filename = head_response.url.split("/")[-1]
            print(f"\n2. Filename from final URL: {filename}")

        result["filename"] = filename
        result["headers"] = dict(head_response.headers)
        result["status_code"] = head_response.status_code

        if filename:
            # Extract version from filename
            version_info = extract_version_from_filename(filename)
            if version_info:
                version, date = version_info
                result["version"] = version
                result["build_date"] = date
                result["success"] = True

                print(f"\n3. Version Information:")
                print(f"   Version: {version}")
                print(f"   Build Date: {date}")
            else:
                print(f"\n3. WARNING: Could not extract version from filename")
                result["error"] = "Version extraction failed"
        else:
            print(f"\n3. WARNING: No filename found in response headers")

            # Try GET request with Range header to get minimal data
            print("\n4. Trying GET request with Range header...")
            get_response = requests.get(
                url,
                headers={"Range": "bytes=0-1023"},
                timeout=10,
                stream=True
            )

            print(f"   Status Code: {get_response.status_code}")
            content_disposition = get_response.headers.get("Content-Disposition", "")

            if content_disposition:
                match = re.search(r'filename=[\'\"]?([^\'\"]+)[\'\"]?', content_disposition)
                if match:
                    filename = unquote(match.group(1))
                    print(f"   Filename from GET request: {filename}")

                    result["filename"] = filename
                    version_info = extract_version_from_filename(filename)
                    if version_info:
                        version, date = version_info
                        result["version"] = version
                        result["build_date"] = date
                        result["success"] = True

                        print(f"\n5. Version Information:")
                        print(f"   Version: {version}")
                        print(f"   Build Date: {date}")

    except requests.exceptions.RequestException as e:
        print(f"\nERROR: Request failed - {e}")
        result["error"] = str(e)

    except Exception as e:
        print(f"\nERROR: Unexpected error - {e}")
        result["error"] = str(e)

    return result


def compare_versions(current: str, latest: str) -> str:
    """
    Compare two version strings.

    Args:
        current: Current version (e.g., "1.3.17.20")
        latest: Latest version (e.g., "1.3.28.38")

    Returns:
        "older", "same", or "newer"
    """
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]

        if current_parts < latest_parts:
            return "older"
        elif current_parts > latest_parts:
            return "newer"
        else:
            return "same"
    except (ValueError, AttributeError):
        return "unknown"


def main():
    """Run firmware version check tests."""
    print("\n" + "="*70)
    print("KOMFOVENT C6/C6M FIRMWARE VERSION CHECK - VALIDATION SCRIPT")
    print("="*70)

    # Test both firmware types
    results = {}
    for firmware_type in ["mbin", "bin"]:
        result = check_firmware_version(firmware_type)
        results[firmware_type] = result

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    for firmware_type, result in results.items():
        print(f"\n{firmware_type.upper()} Firmware:")
        if result.get("success"):
            print(f"  ✓ Version check successful")
            print(f"  ✓ Version: {result.get('version')}")
            print(f"  ✓ Build Date: {result.get('build_date')}")
            print(f"  ✓ Filename: {result.get('filename')}")
        else:
            print(f"  ✗ Version check failed")
            if "error" in result:
                print(f"  ✗ Error: {result['error']}")

    # Test version comparison
    print(f"\n{'='*70}")
    print("VERSION COMPARISON TEST")
    print(f"{'='*70}")

    test_cases = [
        ("1.3.17.20", "1.3.28.38", "older"),
        ("1.3.28.38", "1.3.17.20", "newer"),
        ("1.3.28.38", "1.3.28.38", "same"),
    ]

    for current, latest, expected in test_cases:
        result = compare_versions(current, latest)
        status = "✓" if result == expected else "✗"
        print(f"{status} Current: {current}, Latest: {latest} => {result} (expected: {expected})")

    # Exit with appropriate code
    all_success = all(r.get("success", False) for r in results.values())
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
