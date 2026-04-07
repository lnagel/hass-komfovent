"""Firmware update components for Komfovent integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from custom_components.komfovent.const import Controller as ControllerType


class FirmwareInfo(TypedDict):
    """Firmware information for a specific controller type."""

    controller_type: (
        str  # "C6", "C6M", or "C8" - stored as string for JSON serialization
    )
    filename: str
    controller_version: tuple[int, int, int, int, int]  # (enum, v1, v2, v3, v4)
    panel_version: tuple[int, int, int, int, int]  # (enum, v1, v2, v3, v4)
    file_path: str
    last_checked_at: str  # ISO-8601 datetime string


class StoredFirmwareData(TypedDict):
    """Stored firmware data structure (persisted to disk)."""

    firmware: dict[str, FirmwareInfo]  # Keyed by controller type ("C6", "C8")


def format_version(version: tuple[int, int, int, int, int]) -> str:
    """Format a version tuple as a string (e.g., '1.5.46.72')."""
    return f"{version[1]}.{version[2]}.{version[3]}.{version[4]}"


def is_newer_version(
    installed: tuple[int, int, int, int, int],
    available: tuple[int, int, int, int, int],
) -> bool:
    """
    Check if available version is newer than installed.

    Komfovent uses functional version (v4, the last element) to determine
    update eligibility. This ensures panel-only updates are not missed.

    Args:
        installed: Installed version tuple (enum, v1, v2, v3, v4)
        available: Available version tuple (enum, v1, v2, v3, v4)

    Returns:
        True if available version is newer than installed

    """
    # Compare functional versions (v4)
    return available[4] > installed[4]


def get_controller_type_for_firmware(controller: ControllerType) -> str:
    """
    Get the firmware controller type string for a given controller.

    C6 and C6M share the same firmware, so both map to "C6".

    Args:
        controller: The controller enum value

    Returns:
        Controller type string ("C6" or "C8")

    """
    # Import here to avoid circular imports
    from custom_components.komfovent.const import Controller  # noqa: PLC0415

    # C6 and C6M share firmware
    if controller in {Controller.C6, Controller.C6M}:
        return "C6"
    if controller == Controller.C8:
        return "C8"
    return "NA"


__all__ = [
    "FirmwareInfo",
    "StoredFirmwareData",
    "format_version",
    "get_controller_type_for_firmware",
    "is_newer_version",
]
