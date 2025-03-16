from __future__ import annotations

"""Helper functions for Komfovent integration."""


def get_version_from_int(value: int) -> tuple[int, int, int, int]:
    """
    Convert integer version to component numbers.

    Args:
        value: Integer containing version information packed as bitfields

    Returns:
        Tuple of (major, minor, patch, build) version numbers

    """
    # 1st number 8bit <<24
    # 2nd number 4bit <<20
    # 3rd number 8bit <<12
    # 4th number 12bit <<0
    # Example: 18886660 => 1.2.3.4

    v1 = (value >> 24) & 0xFF
    v2 = (value >> 20) & 0xF
    v3 = (value >> 12) & 0xFF
    v4 = value & 0xFFF

    return v1, v2, v3, v4
