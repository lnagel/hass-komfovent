#!/usr/bin/env python3
"""
Download Komfovent C6/C6M firmware files.

This script downloads .mbin firmware from the manufacturer's server.
Only firmware v1.3.15+ (.mbin) is supported. Older .bin firmware is not supported.

Usage:
    python3 download_firmware.py [--output firmware.mbin]
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import requests

# Firmware download URL (only .mbin supported, v1.3.15+)
FIRMWARE_URL = "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin"

# Reference documentation
DOWNLOADS_PDF = "https://www.komfovent.com/en/downloads/C6_update_EN.pdf"


def extract_filename_from_headers(response: requests.Response) -> str | None:
    """
    Extract filename from response headers.

    Args:
        response: HTTP response object

    Returns:
        Filename if found, None otherwise

    """
    # Check Content-Disposition header
    content_disposition = response.headers.get("Content-Disposition", "")
    if content_disposition:
        # Example: attachment; filename="C6_1_3_28_38_20180428.mbin"
        match = re.search(r"filename=[\'\"]?([^\'\"]+)[\'\"]?", content_disposition)
        if match:
            return unquote(match.group(1))

    # Check Content-Location header
    content_location = response.headers.get("Content-Location", "")
    if content_location:
        return content_location.split("/")[-1]

    # Try to extract from final URL after redirects
    if response.url and response.url != FIRMWARE_URL:
        url_filename = response.url.split("/")[-1]
        # Check if it looks like a firmware file
        if url_filename.endswith(".mbin"):
            return url_filename

    return None


def format_version(version: tuple) -> str:
    """Format version tuple as string for display."""
    # ("C6", 1, 5, 46, 72) -> "1.5.46.72"
    return f"{version[1]}.{version[2]}.{version[3]}.{version[4]}"


def extract_version_from_filename(filename: str) -> dict | None:
    """
    Extract version information from firmware filename.

    Expected patterns:
    - Modern: C6_1_5_46_72_P1_1_1_5_48.mbin (controller + panel versions)
    - Legacy: C6_1_3_28_38_20180428.mbin (controller + date)

    Args:
        filename: Firmware filename

    Returns:
        Dictionary with version info:
        - controller_version: ("C6", 1, 5, 46, 72) - 5-tuple for comparison
        - panel_version: ("P1", 1, 1, 5, 48) or None - 5-tuple for comparison

    """
    # Modern pattern: C6[M]?_v1_v2_v3_v4_P1_p1_p2_p3_p4.mbin
    modern_pattern = (
        r"C6(M)?_(\d+)_(\d+)_(\d+)_(\d+)_P1_(\d+)_(\d+)_(\d+)_(\d+)\.(mbin)"
    )

    match = re.search(modern_pattern, filename, re.IGNORECASE)
    if match:
        model_suffix, v1, v2, v3, v4, p1, p2, p3, p4, ext = match.groups()

        model = f"C6{model_suffix}" if model_suffix else "C6"

        return {
            "model": model,
            "controller_version": (model, int(v1), int(v2), int(v3), int(v4)),
            "panel_version": ("P1", int(p1), int(p2), int(p3), int(p4)),
            "extension": ext,
            "pattern": "modern",
        }

    # Legacy pattern: C6[M]?_v1_v2_v3_v4_date.mbin
    legacy_pattern = r"C6(M)?_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)\.(mbin)"

    match = re.search(legacy_pattern, filename, re.IGNORECASE)
    if match:
        model_suffix, v1, v2, v3, v4, date, ext = match.groups()

        model = f"C6{model_suffix}" if model_suffix else "C6"

        return {
            "model": model,
            "controller_version": (model, int(v1), int(v2), int(v3), int(v4)),
            "panel_version": None,
            "date": date,
            "extension": ext,
            "pattern": "legacy",
        }

    return None


def download_firmware(output_path: str | None = None) -> bool:
    """
    Download firmware file from manufacturer.

    Only .mbin firmware (v1.3.15+) is supported.

    Args:
        output_path: Output file path (optional)

    Returns:
        True if successful, False otherwise

    """
    print(f"{'=' * 70}")
    print("Downloading MBIN firmware")
    print(f"{'=' * 70}")
    print(f"URL: {FIRMWARE_URL}\n")

    try:
        # Use streaming GET to check access and download in one request
        # (HEAD requests don't return Content-Disposition from this PHP endpoint)
        print("1. Connecting to server...")
        response = requests.get(FIRMWARE_URL, stream=True, timeout=30)

        print(f"   Status: {response.status_code}")

        if response.status_code == 403:
            print("   ❌ Access denied (403 Forbidden)")

            # Check for deny reason
            deny_reason = response.headers.get("x-deny-reason")
            if deny_reason:
                print(f"   Reason: {deny_reason}")

            print(f"\n{'=' * 70}")
            print("ACCESS DENIED FROM THIS LOCATION")
            print(f"{'=' * 70}\n")
            print("⚠️  Download access is restricted to residential networks")
            print("    where Komfovent devices are installed.\n")
            print("This script must be run from the same network as your device.")
            print("The Home Assistant integration will have proper access.\n")

            return False

        if response.status_code != 200:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False

        print("   ✅ Access granted!")

        # Get filename from headers (available in streaming GET response)
        filename = extract_filename_from_headers(response)
        if filename:
            print(f"   Filename: {filename}")

            # Extract version info
            version_info = extract_version_from_filename(filename)
            if version_info:
                cv = version_info["controller_version"]
                print(f"   Version: {format_version(cv)}")
                print(f"   Model: {version_info['model']}")
                if version_info.get("date"):
                    print(f"   Date: {version_info['date']}")

        # Determine output filename
        if output_path:
            output_file = Path(output_path)
        elif filename:
            output_file = Path(filename)
        else:
            output_file = Path("komfovent_firmware.mbin")

        print(f"\n2. Downloading to: {output_file}")

        # Get total size if available
        total_size = int(response.headers.get("content-length", 0))

        # Download with progress (continuing from same response)
        downloaded = 0
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(
                            f"   Progress: {percent:.1f}% ({downloaded:,} / {total_size:,} bytes)",
                            end="\r",
                        )

        print("\n   ✅ Download complete!")

        # Verify file
        file_size = output_file.stat().st_size
        print("\n3. Verifying downloaded file...")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

        if file_size < 100_000:
            print("   ⚠️  Warning: File seems small (< 100KB)")
            print("   This might not be a valid firmware file")
        elif file_size > 10_000_000:
            print("   ⚠️  Warning: File seems large (> 10MB)")
            print("   This might not be a valid firmware file")
        else:
            print("   ✅ File size looks reasonable")

        # Extract version from filename
        if filename:
            version_info = extract_version_from_filename(str(output_file))
            if version_info:
                print("\n4. Firmware Information:")
                print(f"   Model: {version_info['model']}")
                cv = version_info["controller_version"]
                print(f"   Controller Version: {format_version(cv)}")
                pv = version_info.get("panel_version")
                if pv:
                    print(f"   Panel Version: {format_version(pv)}")
                if "date" in version_info:
                    print(f"   Build Date: {version_info['date']}")
                print(f"   Type: {version_info['extension']}")
                print(f"   Pattern: {version_info['pattern']}")

        print(f"\n{'=' * 70}")
        print("✅ SUCCESS - Firmware downloaded successfully!")
        print(f"{'=' * 70}")
        print("\nNext steps:")
        print("1. Verify firmware version matches your needs")
        print("2. Use validate_firmware_update.py to test upload (dry-run)")
        print("3. Upload to device at http://[device_ip]/g1.html")

        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Download failed: {e}")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def validate_firmware_file(filepath: str) -> bool:
    """
    Validate a firmware file.

    Args:
        filepath: Path to firmware file

    Returns:
        True if valid, False otherwise

    """
    print(f"{'=' * 70}")
    print("Validating firmware file")
    print(f"{'=' * 70}\n")

    path = Path(filepath)

    # Check file exists
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False

    print(f"File: {path}")

    # Check extension (only .mbin supported)
    if path.suffix != ".mbin":
        print(f"❌ Invalid extension: {path.suffix}")
        print("   Expected: .mbin (only v1.3.15+ firmware supported)")
        return False

    print(f"✅ Extension: {path.suffix}")

    # Check file size
    size = path.stat().st_size
    print(f"✅ Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")

    if size < 100_000:
        print("⚠️  Warning: File is very small (< 100KB)")
    elif size > 10_000_000:
        print("⚠️  Warning: File is very large (> 10MB)")

    # Extract version from filename
    version_info = extract_version_from_filename(path.name)
    if version_info:
        print("\nFirmware Information:")
        print(f"  Model: {version_info['model']}")
        cv = version_info["controller_version"]
        print(f"  Controller Version: {format_version(cv)}")
        pv = version_info.get("panel_version")
        if pv:
            print(f"  Panel Version: {format_version(pv)}")
        if "date" in version_info:
            print(f"  Build Date: {version_info['date']}")
        print(f"  Type: {version_info['extension']}")
        print(f"  Pattern: {version_info['pattern']}")
    else:
        print("\n⚠️  Could not extract version from filename")
        print("   Expected formats:")
        print("     Modern: C6_1_5_XX_XX_P1_1_1_X_XX.mbin")
        print("     Legacy: C6_1_3_XX_XX_YYYYMMDD.mbin")

    print(f"\n{'=' * 70}")
    print("✅ File validation passed")
    print(f"{'=' * 70}")
    print("\nThis file can be uploaded to your Komfovent device.")
    print(f"Use: python3 validate_firmware_update.py --host [IP] --firmware {filepath}")

    return True


def main() -> None:
    """Download or validate Komfovent firmware."""
    parser = argparse.ArgumentParser(
        description="Download Komfovent C6/C6M firmware files (.mbin only, v1.3.15+)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download latest firmware
  python3 download_firmware.py

  # Download to specific file
  python3 download_firmware.py --output firmware_latest.mbin

  # Validate an existing firmware file
  python3 download_firmware.py --validate firmware.mbin

Note: Only .mbin firmware (v1.3.15+) is supported. Older .bin firmware requires
manual update first.

This script must be run from the same network as your Komfovent device.
        """,
    )

    parser.add_argument(
        "--output", help="Output file path (default: auto-detect from response)"
    )

    parser.add_argument(
        "--validate",
        metavar="FILE",
        help="Validate an existing firmware file instead of downloading",
    )

    args = parser.parse_args()

    # Validate mode
    if args.validate:
        success = validate_firmware_file(args.validate)
        sys.exit(0 if success else 1)

    # Download mode
    success = download_firmware(output_path=args.output)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
