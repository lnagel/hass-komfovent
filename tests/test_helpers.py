"""Test cases for Komfovent helper functions."""

import pytest

from custom_components.komfovent.const import Controller
from custom_components.komfovent.helpers import get_version_from_int


def uint32(high, low):
    return (high << 16) + low


def test_get_version_from_int():
    """Test version number extraction from packed integer."""
    # Test the example case from the docstring
    assert get_version_from_int(18886660) == (Controller.C6, 1, 2, 3, 4)

    # Test additional cases for C6 controller firmware version
    assert get_version_from_int(20037670) == (Controller.C6, 1, 3, 28, 38)
    assert get_version_from_int(uint32(305, 49190)) == (Controller.C6, 1, 3, 28, 38)
    assert get_version_from_int(20099140) == (Controller.C6, 1, 3, 43, 68)
    assert get_version_from_int(20103237) == (Controller.C6, 1, 3, 44, 69)

    # Test additional cases for C6M controller firmware version
    assert get_version_from_int(289542195) == (Controller.C6M, 1, 4, 33, 51)
    assert get_version_from_int(289579075) == (Controller.C6M, 1, 4, 42, 67)
    assert get_version_from_int(uint32(4418, 41027)) == (Controller.C6M, 1, 4, 42, 67)
    assert get_version_from_int(uint32(4418, 49221)) == (Controller.C6M, 1, 4, 44, 69)

    # Test additional cases for C6 panel firmware version
    assert get_version_from_int(17838105) == (Controller.C6, 1, 1, 3, 25)
    assert get_version_from_int(18886683) == (Controller.C6, 1, 2, 3, 27)
    assert get_version_from_int(17838114) == (Controller.C6, 1, 1, 3, 34)
    assert get_version_from_int(17846317) == (Controller.C6, 1, 1, 5, 45)
    assert get_version_from_int(34607113) == (Controller.C6, 2, 1, 1, 9)

    # Test boundary values
    assert get_version_from_int(0) == (Controller.C6, 0, 0, 0, 0)
    assert get_version_from_int(0xFFFFFFFF) == (Controller.NA, 15, 15, 255, 4095)
