"""Firmware update components for Komfovent integration."""

from __future__ import annotations

from typing import TypedDict

from custom_components.komfovent.const import Controller


class FirmwareInfo(TypedDict):
    """Firmware information for a specific controller type."""

    controller_type: str  # "C6" or "C8", stored as string for JSON serialization
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


def get_controller_type_for_firmware(controller: Controller) -> str:
    """
    Get the firmware controller type string for a given controller.

    C6 and C6M share the same firmware, so both map to "C6".

    Args:
        controller: The controller enum value

    Returns:
        Controller type string ("C6", "C8" or "NA")

    """
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
]
