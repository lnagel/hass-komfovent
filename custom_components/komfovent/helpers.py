"""Helper functions for Komfovent integration."""

from __future__ import annotations

from .const import Controller


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
