"""Helper functions for Komfovent integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo

from . import registers
from .const import BITMASK_FAN, DOMAIN, Controller, Panel

if TYPE_CHECKING:
    from .coordinator import KomfoventCoordinator


def build_device_info(coordinator: KomfoventCoordinator) -> DeviceInfo:
    """
    Build device info dictionary for entity registration.

    Creates a standardized device info dict that includes:
    - Device identifiers
    - Device name from config entry title
    - Manufacturer name
    - Controller model (C6, C6M, C8, or None)
    - Configuration URL for the device's web interface

    Args:
        coordinator: The Komfovent coordinator instance

    Returns:
        Dictionary containing device info for Home Assistant entity registration

    """
    host = coordinator.config_entry.data[CONF_HOST]
    model = coordinator.controller.name if coordinator.controller is not None else None

    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
        name=coordinator.config_entry.title,
        manufacturer="Komfovent",
        model=model,
        configuration_url=f"http://{host}",
    )


def flow_present(data: dict[int, Any] | None) -> bool:
    """
    Return whether air is flowing through the unit.

    The fan bit of the status register is the single source of truth. Flow is
    assumed present when the status is unknown, so incomplete data never resets
    filters or blanks sensors.

    Args:
        data: Register values as stored by the coordinator

    Returns:
        True if the fans are running or the status register is missing

    """
    status = data.get(registers.REG_STATUS) if data else None
    return status is None or bool(status & BITMASK_FAN)


def _unpack_version(value: int) -> tuple[int, int, int, int, int]:
    """
    Unpack a packed firmware version integer into its bitfields.

    The most significant nibble encodes the device type (controller or
    panel); the remaining fields are the four version numbers.

    Args:
        value: Integer containing version information packed as bitfields

    Returns:
        Tuple of (type, v1, v2, v3, v4) raw numbers

    """
    # device type 4bit <<28
    # 1st number 4bit <<24
    # 2nd number 4bit <<20
    # 3rd number 8bit <<12
    # 4th number 12bit <<0
    # Example: 18886660 => 1.2.3.4
    device_type = (value >> 28) & 0xF
    v1 = (value >> 24) & 0xF
    v2 = (value >> 20) & 0xF
    v3 = (value >> 12) & 0xFF
    v4 = value & 0xFFF
    return device_type, v1, v2, v3, v4


def get_controller_version(value: int) -> tuple[Controller, int, int, int, int]:
    """
    Convert integer version to a controller version tuple.

    Args:
        value: Integer containing version information packed as bitfields

    Returns:
        Tuple of (controller, v1, v2, v3, v4) version numbers

    """
    device_type, v1, v2, v3, v4 = _unpack_version(value)

    try:
        controller = Controller(device_type)
    except ValueError:
        controller = Controller.NA

    return controller, v1, v2, v3, v4


def get_panel_version(value: int) -> tuple[Panel, int, int, int, int]:
    """
    Convert integer version to a control panel version tuple.

    Uses the same bitfield layout as the controller version, but the
    device-type nibble is interpreted as a panel type.

    Args:
        value: Integer containing version information packed as bitfields

    Returns:
        Tuple of (panel, v1, v2, v3, v4) version numbers

    """
    device_type, v1, v2, v3, v4 = _unpack_version(value)

    try:
        panel = Panel(device_type)
    except ValueError:
        panel = Panel.NA

    return panel, v1, v2, v3, v4
