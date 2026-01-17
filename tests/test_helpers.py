"""Test cases for Komfovent helper functions."""

from custom_components.komfovent.const import DOMAIN, Controller
from custom_components.komfovent.helpers import build_device_info, get_version_from_int


def uint32(high, low):
    return (high << 16) + low


def test_get_version_from_int():
    """Test version number extraction from packed integer."""
    # Test the example case from the docstring
    assert get_version_from_int(18886660) == (Controller.C6, 1, 2, 3, 4)

    # Test C6 controller firmware version
    assert get_version_from_int(uint32(305, 4116)) == (Controller.C6, 1, 3, 17, 20)
    assert get_version_from_int(20037670) == (Controller.C6, 1, 3, 28, 38)
    assert get_version_from_int(uint32(305, 49190)) == (Controller.C6, 1, 3, 28, 38)
    assert get_version_from_int(20099140) == (Controller.C6, 1, 3, 43, 68)
    assert get_version_from_int(20103237) == (Controller.C6, 1, 3, 44, 69)

    # Test C6M controller firmware version
    assert get_version_from_int(289542195) == (Controller.C6M, 1, 4, 33, 51)
    assert get_version_from_int(289579075) == (Controller.C6M, 1, 4, 42, 67)
    assert get_version_from_int(uint32(4418, 41027)) == (Controller.C6M, 1, 4, 42, 67)
    assert get_version_from_int(uint32(4418, 49221)) == (Controller.C6M, 1, 4, 44, 69)

    # Test C8 controller firmware version
    assert get_version_from_int(uint32(8464, 12301)) == (Controller.C8, 1, 1, 3, 13)

    # Test additional cases for C6 panel firmware version
    assert get_version_from_int(17838105) == (Controller.C6, 1, 1, 3, 25)
    assert get_version_from_int(18886683) == (Controller.C6, 1, 2, 3, 27)
    assert get_version_from_int(17838114) == (Controller.C6, 1, 1, 3, 34)
    assert get_version_from_int(17846317) == (Controller.C6, 1, 1, 5, 45)
    assert get_version_from_int(34607113) == (Controller.C6, 2, 1, 1, 9)

    # Test boundary values
    assert get_version_from_int(0) == (Controller.C6, 0, 0, 0, 0)
    assert get_version_from_int(0xFFFFFFFF) == (Controller.NA, 15, 15, 255, 4095)


def test_build_device_info(mock_coordinator):
    """Test build_device_info returns correct device info dictionary."""
    device_info = build_device_info(mock_coordinator)

    assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
    assert device_info["name"] == "Komfovent"
    assert device_info["manufacturer"] == "Komfovent"
    assert device_info["model"] == "C6"
    assert device_info["configuration_url"] == "http://192.168.1.100"


def test_build_device_info_with_different_controllers(
    mock_coordinator_by_controller,
):
    """Test build_device_info returns correct model for each controller type."""
    device_info = build_device_info(mock_coordinator_by_controller)

    controller = mock_coordinator_by_controller.controller
    assert device_info["model"] == controller.name
    assert device_info["configuration_url"] == "http://192.168.1.100"
