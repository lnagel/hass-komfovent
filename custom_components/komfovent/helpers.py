"""Helper functions for Komfovent integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, Controller

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


def get_version_from_int(value: int) -> tuple[Controller, int, int, int, int]:
    """
    Convert integer version to component numbers.

    Args:
        value: Integer containing version information packed as bitfields

    Returns:
        Tuple of (controller, v1, v2, v3, v4) version numbers

    """
    # controller 4bit <<28
    # 1st number 4bit <<24
    # 2nd number 4bit <<20
    # 3rd number 8bit <<12
    # 4th number 12bit <<0
    # Example: 18886660 => 1.2.3.4

    ct = (value >> 28) & 0xF
    v1 = (value >> 24) & 0xF
    v2 = (value >> 20) & 0xF
    v3 = (value >> 12) & 0xFF
    v4 = value & 0xFFF

    try:
        controller = Controller(ct)
    except ValueError:
        controller = Controller.NA

    return controller, v1, v2, v3, v4
