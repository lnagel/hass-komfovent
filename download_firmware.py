#!/usr/bin/env python3
"""
Download Komfovent C6/C6M firmware files.

This script attempts to download firmware from the manufacturer's server.
Note: External access is typically blocked (403 Forbidden). This script may
work if run from a whitelisted network or device.

Usage:
    python3 download_firmware.py [--type mbin|bin] [--output firmware.mbin]
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import requests


# Firmware download URLs
FIRMWARE_URLS = {
    "mbin": "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin",
    "bin": "http://www.komfovent.com/Update/Controllers/firmware.php?file=bin",
}

# Alternative download page
DOWNLOADS_PAGE = "https://www.komfovent.com/en/page/software"
DOWNLOADS_PDF = "https://www.komfovent.com/en/downloads/C6_update_EN.pdf"


def extract_filename_from_headers(response: requests.Response) -> str | None:
    """Extract filename from response headers.

    Args:
        response: HTTP response object

    Returns:
        Filename if found, None otherwise
    """
    # Check Content-Disposition header
    content_disposition = response.headers.get("Content-Disposition", "")
    if content_disposition:
        # Example: attachment; filename="C6_1_3_28_38_20180428.mbin"
        match = re.search(r'filename=[\'\"]?([^\'\"]+)[\'\"]?', content_disposition)
        if match:
            return unquote(match.group(1))

    # Check Content-Location header
    content_location = response.headers.get("Content-Location", "")
    if content_location:
        return content_location.split("/")[-1]

    # Try to extract from final URL after redirects
    if response.url and response.url != FIRMWARE_URLS.get("mbin") and response.url != FIRMWARE_URLS.get("bin"):
        url_filename = response.url.split("/")[-1]
        # Check if it looks like a firmware file
        if url_filename.endswith((".mbin", ".bin")):
            return url_filename

    return None


def extract_version_from_filename(filename: str) -> dict | None:
    """Extract version information from firmware filename.

    Expected patterns:
    - C6_1_3_28_38_20180428.mbin
    - C6M_1_4_44_69_20230615.mbin

    Args:
        filename: Firmware filename

    Returns:
        Dictionary with version info or None
    """
    # Pattern: C6[M]?_v1_v2_v3_v4_date.ext
    pattern = r"C6(M)?_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)\.(m?bin)"

    match = re.search(pattern, filename, re.IGNORECASE)
    if match:
        model_suffix, v1, v2, v3, v4, date, ext = match.groups()

        model = f"C6{model_suffix}" if model_suffix else "C6"
        version = f"{v1}.{v2}.{v3}.{v4}"

        return {
            "model": model,
            "version": version,
            "v1": int(v1),
            "v2": int(v2),
            "v3": int(v3),
            "v4": int(v4),
            "date": date,
            "extension": ext,
        }

    return None


def download_firmware(firmware_type: str = "mbin", output_path: str = None) -> bool:
    """Download firmware file from manufacturer.

    Args:
        firmware_type: Type of firmware ("mbin" or "bin")
        output_path: Output file path (optional)

    Returns:
        True if successful, False otherwise
    """
    url = FIRMWARE_URLS.get(firmware_type)
    if not url:
        print(f"❌ Error: Unknown firmware type '{firmware_type}'")
        print(f"   Valid types: mbin, bin")
        return False

    print(f"{'='*70}")
    print(f"Downloading {firmware_type.upper()} firmware")
    print(f"{'='*70}")
    print(f"URL: {url}\n")

    try:
        # First, try a HEAD request to check access and get filename
        print("1. Checking access with HEAD request...")
        head_response = requests.head(url, allow_redirects=True, timeout=10)

        print(f"   Status: {head_response.status_code}")

        if head_response.status_code == 403:
            print(f"   ❌ Access denied (403 Forbidden)")

            # Check for deny reason
            deny_reason = head_response.headers.get("x-deny-reason")
            if deny_reason:
                print(f"   Reason: {deny_reason}")

            print(f"\n{'='*70}")
            print(f"ACCESS DENIED FROM THIS LOCATION")
            print(f"{'='*70}\n")
            print("⚠️  Download access is restricted to residential networks")
            print("    where Komfovent devices are installed.\n")
            print("This script must be run from the same network as your device.")
            print("The Home Assistant integration will have proper access.\n")

            return False

        elif head_response.status_code != 200:
            print(f"   ❌ Unexpected status code: {head_response.status_code}")
            return False

        print(f"   ✅ Access granted!")

        # Try to get filename from headers
        filename = extract_filename_from_headers(head_response)
        if filename:
            print(f"   Filename: {filename}")

            # Extract version info
            version_info = extract_version_from_filename(filename)
            if version_info:
                print(f"   Version: {version_info['version']}")
                print(f"   Model: {version_info['model']}")
                print(f"   Date: {version_info['date']}")

        # Determine output filename
        if output_path:
            output_file = Path(output_path)
        elif filename:
            output_file = Path(filename)
        else:
            output_file = Path(f"komfovent_firmware.{firmware_type}")

        print(f"\n2. Downloading to: {output_file}")

        # Download the file
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Get total size if available
        total_size = int(response.headers.get('content-length', 0))

        # Download with progress
        downloaded = 0
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"   Progress: {percent:.1f}% ({downloaded:,} / {total_size:,} bytes)", end='\r')

        print(f"\n   ✅ Download complete!")

        # Verify file
        file_size = output_file.stat().st_size
        print(f"\n3. Verifying downloaded file...")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

        if file_size < 100_000:
            print(f"   ⚠️  Warning: File seems small (< 100KB)")
            print(f"   This might not be a valid firmware file")
        elif file_size > 10_000_000:
            print(f"   ⚠️  Warning: File seems large (> 10MB)")
            print(f"   This might not be a valid firmware file")
        else:
            print(f"   ✅ File size looks reasonable")

        # Extract version from filename
        if filename:
            version_info = extract_version_from_filename(str(output_file))
            if version_info:
                print(f"\n4. Firmware Information:")
                print(f"   Model: {version_info['model']}")
                print(f"   Version: {version_info['version']}")
                print(f"   Build Date: {version_info['date']}")
                print(f"   Type: {version_info['extension']}")

        print(f"\n{'='*70}")
        print(f"✅ SUCCESS - Firmware downloaded successfully!")
        print(f"{'='*70}")
        print(f"\nNext steps:")
        print(f"1. Verify firmware version matches your needs")
        print(f"2. Use validate_firmware_update.py to test upload (dry-run)")
        print(f"3. Upload to device at http://[device_ip]/g1.html")

        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Download failed: {e}")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def validate_firmware_file(filepath: str) -> bool:
    """Validate a firmware file.

    Args:
        filepath: Path to firmware file

    Returns:
        True if valid, False otherwise
    """
    print(f"{'='*70}")
    print(f"Validating firmware file")
    print(f"{'='*70}\n")

    path = Path(filepath)

    # Check file exists
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False

    print(f"File: {path}")

    # Check extension
    if path.suffix not in [".bin", ".mbin"]:
        print(f"❌ Invalid extension: {path.suffix}")
        print(f"   Expected: .bin or .mbin")
        return False

    print(f"✅ Extension: {path.suffix}")

    # Check file size
    size = path.stat().st_size
    print(f"✅ Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")

    if size < 100_000:
        print(f"⚠️  Warning: File is very small (< 100KB)")
    elif size > 10_000_000:
        print(f"⚠️  Warning: File is very large (> 10MB)")

    # Extract version from filename
    version_info = extract_version_from_filename(path.name)
    if version_info:
        print(f"\nFirmware Information:")
        print(f"  Model: {version_info['model']}")
        print(f"  Version: {version_info['version']}")
        print(f"  Build Date: {version_info['date']}")
        print(f"  Type: {version_info['extension']}")
    else:
        print(f"\n⚠️  Could not extract version from filename")
        print(f"   Expected format: C6_1_3_XX_XX_YYYYMMDD.{path.suffix[1:]}")

    print(f"\n{'='*70}")
    print(f"✅ File validation passed")
    print(f"{'='*70}")
    print(f"\nThis file can be uploaded to your Komfovent device.")
    print(f"Use: python3 validate_firmware_update.py --host [IP] --firmware {filepath}")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download Komfovent C6/C6M firmware files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download latest MBIN firmware
  python3 download_firmware.py --type mbin

  # Download to specific file
  python3 download_firmware.py --type mbin --output firmware_latest.mbin

  # Download BIN firmware (for older controllers)
  python3 download_firmware.py --type bin

  # Validate an existing firmware file
  python3 download_firmware.py --validate firmware.mbin

Note: This script must be run from the same network as your Komfovent device.
The manufacturer restricts downloads to residential networks where devices are installed.
        """
    )

    parser.add_argument(
        "--type",
        choices=["mbin", "bin"],
        default="mbin",
        help="Firmware type to download (default: mbin)"
    )

    parser.add_argument(
        "--output",
        help="Output file path (default: auto-detect from response)"
    )

    parser.add_argument(
        "--validate",
        metavar="FILE",
        help="Validate an existing firmware file instead of downloading"
    )

    args = parser.parse_args()

    # Validate mode
    if args.validate:
        success = validate_firmware_file(args.validate)
        sys.exit(0 if success else 1)

    # Download mode
    success = download_firmware(
        firmware_type=args.type,
        output_path=args.output
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
