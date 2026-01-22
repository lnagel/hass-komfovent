#!/usr/bin/env python3
"""
Download Komfovent C6/C6M firmware files.

This script downloads .mbin firmware from the manufacturer's server.
Only firmware v1.3.15+ (.mbin) is supported. Older .bin firmware is not supported.

Usage:
    python3 download_firmware.py [--output firmware.mbin]
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Firmware download URL (only .mbin supported, v1.3.15+)
FIRMWARE_URL = "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin"

# Reference documentation
DOWNLOADS_PDF = "https://www.komfovent.com/en/downloads/C6_update_EN.pdf"

# HTTP status codes
HTTP_OK = 200
HTTP_FORBIDDEN = 403

# File size thresholds (bytes)
MIN_FIRMWARE_SIZE = 100_000  # 100KB - files smaller than this are suspicious
MAX_FIRMWARE_SIZE = 10_000_000  # 10MB - files larger than this are suspicious

# Download settings
CHUNK_SIZE = 8192
REQUEST_TIMEOUT = 30


def extract_filename_from_headers(response: requests.Response) -> str | None:
    """
    Extract filename from response headers.

    Checks Content-Disposition, Content-Location, and final URL for filename.

    Args:
        response: HTTP response object

    Returns:
        Filename if found, None otherwise

    """
    content_disposition = response.headers.get("Content-Disposition", "")
    if content_disposition:
        match = re.search(r"filename=[\'\"]?([^\'\"]+)[\'\"]?", content_disposition)
        if match:
            return unquote(match.group(1))

    content_location = response.headers.get("Content-Location", "")
    if content_location:
        return content_location.split("/")[-1]

    if response.url and response.url != FIRMWARE_URL:
        url_filename = response.url.split("/")[-1]
        if url_filename.endswith(".mbin"):
            return url_filename

    return None


def format_version(version: tuple) -> str:
    """Format version tuple as string for display."""
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
        Dictionary with version info or None if pattern not matched

    """
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


def _log_header(title: str) -> None:
    """Log a section header."""
    logger.info("=" * 70)
    logger.info(title)
    logger.info("=" * 70)


def _handle_forbidden_response(response: requests.Response) -> None:
    """Handle 403 Forbidden response."""
    logger.error("Access denied (403 Forbidden)")
    deny_reason = response.headers.get("x-deny-reason")
    if deny_reason:
        logger.error("Reason: %s", deny_reason)
    _log_header("ACCESS DENIED FROM THIS LOCATION")
    logger.warning("Download access is restricted to residential networks")
    logger.warning("where Komfovent devices are installed.")
    logger.info("This script must be run from the same network as your device.")
    logger.info("The Home Assistant integration will have proper access.")


def _log_version_info(version_info: dict) -> None:
    """Log firmware version information."""
    cv = version_info["controller_version"]
    logger.info("Version: %s", format_version(cv))
    logger.info("Model: %s", version_info["model"])
    if version_info.get("date"):
        logger.info("Date: %s", version_info["date"])


def _log_detailed_version_info(version_info: dict) -> None:
    """Log detailed firmware version information."""
    logger.info("Firmware Information:")
    logger.info("  Model: %s", version_info["model"])
    cv = version_info["controller_version"]
    logger.info("  Controller Version: %s", format_version(cv))
    pv = version_info.get("panel_version")
    if pv:
        logger.info("  Panel Version: %s", format_version(pv))
    if "date" in version_info:
        logger.info("  Build Date: %s", version_info["date"])
    logger.info("  Type: %s", version_info["extension"])
    logger.info("  Pattern: %s", version_info["pattern"])


def _verify_file_size(file_size: int) -> None:
    """Log file size verification results."""
    if file_size < MIN_FIRMWARE_SIZE:
        logger.warning("File seems small (< 100KB)")
        logger.warning("This might not be a valid firmware file")
    elif file_size > MAX_FIRMWARE_SIZE:
        logger.warning("File seems large (> 10MB)")
        logger.warning("This might not be a valid firmware file")
    else:
        logger.info("File size looks reasonable")


def _download_with_progress(
    response: requests.Response, output_file: Path, total_size: int
) -> None:
    """Download file with progress logging."""
    downloaded = 0
    with output_file.open("wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    logger.info(
                        "Progress: %.1f%% (%d / %d bytes)",
                        percent,
                        downloaded,
                        total_size,
                    )
    logger.info("Download complete!")


def download_firmware(output_path: str | None = None) -> bool:
    """
    Download firmware file from manufacturer.

    Only .mbin firmware (v1.3.15+) is supported.

    Args:
        output_path: Output file path (optional)

    Returns:
        True if successful, False otherwise

    """
    _log_header("Downloading MBIN firmware")
    logger.info("URL: %s", FIRMWARE_URL)

    try:
        logger.info("1. Connecting to server...")
        response = requests.get(FIRMWARE_URL, stream=True, timeout=REQUEST_TIMEOUT)
        logger.info("Status: %d", response.status_code)

        if response.status_code == HTTP_FORBIDDEN:
            _handle_forbidden_response(response)
            return False

        if response.status_code != HTTP_OK:
            logger.error("Unexpected status code: %d", response.status_code)
            return False

        logger.info("Access granted!")

        filename = extract_filename_from_headers(response)
        if filename:
            logger.info("Filename: %s", filename)
            version_info = extract_version_from_filename(filename)
            if version_info:
                _log_version_info(version_info)

        output_file = _determine_output_file(output_path, filename)
        logger.info("2. Downloading to: %s", output_file)

        total_size = int(response.headers.get("content-length", 0))
        _download_with_progress(response, output_file, total_size)

        _verify_downloaded_file(output_file, filename)
        _log_success()

    except requests.exceptions.RequestException:
        logger.exception("Download failed")
        return False

    else:
        return True


def _determine_output_file(output_path: str | None, filename: str | None) -> Path:
    """Determine the output file path."""
    if output_path:
        return Path(output_path)
    if filename:
        return Path(filename)
    return Path("komfovent_firmware.mbin")


def _verify_downloaded_file(output_file: Path, filename: str | None) -> None:
    """Verify the downloaded file."""
    file_size = output_file.stat().st_size
    logger.info("3. Verifying downloaded file...")
    logger.info("File: %s", output_file)
    logger.info("Size: %d bytes (%.2f MB)", file_size, file_size / 1024 / 1024)
    _verify_file_size(file_size)

    if filename:
        version_info = extract_version_from_filename(str(output_file))
        if version_info:
            logger.info("4. Firmware Information:")
            _log_detailed_version_info(version_info)


def _log_success() -> None:
    """Log success message."""
    _log_header("SUCCESS - Firmware downloaded successfully!")
    logger.info("Next steps:")
    logger.info("1. Verify firmware version matches your needs")
    logger.info("2. Use validate_firmware_update.py to test upload (dry-run)")
    logger.info("3. Upload to device at http://[device_ip]/g1.html")


def validate_firmware_file(filepath: str) -> bool:
    """
    Validate a firmware file.

    Args:
        filepath: Path to firmware file

    Returns:
        True if valid, False otherwise

    """
    _log_header("Validating firmware file")

    path = Path(filepath)

    if not path.exists():
        logger.error("File not found: %s", filepath)
        return False

    logger.info("File: %s", path)

    if path.suffix != ".mbin":
        logger.error("Invalid extension: %s", path.suffix)
        logger.error("Expected: .mbin (only v1.3.15+ firmware supported)")
        return False

    logger.info("Extension: %s", path.suffix)

    size = path.stat().st_size
    logger.info("Size: %d bytes (%.2f MB)", size, size / 1024 / 1024)
    _verify_file_size(size)

    version_info = extract_version_from_filename(path.name)
    if version_info:
        _log_detailed_version_info(version_info)
    else:
        logger.warning("Could not extract version from filename")
        logger.info("Expected formats:")
        logger.info("  Modern: C6_1_5_XX_XX_P1_1_1_X_XX.mbin")
        logger.info("  Legacy: C6_1_3_XX_XX_YYYYMMDD.mbin")

    _log_header("File validation passed")
    logger.info("This file can be uploaded to your Komfovent device.")
    logger.info(
        "Use: python3 validate_firmware_update.py --host [IP] --firmware %s", filepath
    )

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

    if args.validate:
        success = validate_firmware_file(args.validate)
        sys.exit(0 if success else 1)

    success = download_firmware(output_path=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
