"""Tests for Komfovent binary sensor platform."""

import pytest
from homeassistant.components.binary_sensor import BinarySensorEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.binary_sensor import (
    BITMASK_ALARM_F,
    BITMASK_ALARM_W,
    BITMASK_COOLING,
    BITMASK_FAN,
    BITMASK_HEATING,
    BITMASK_STARTING,
    BITMASK_STOPPING,
    KomfoventBinarySensor,
    KomfoventStatusBinarySensor,
    create_binary_sensors,
)
from custom_components.komfovent.const import DOMAIN

DESC = BinarySensorEntityDescription(key="test", name="Test")

# ==================== Data Tables ====================

IS_ON_CASES = [({100: 1}, True), ({100: 0}, False), (None, None), ({}, None)]

BITMASK_CASES = [
    (BITMASK_STARTING, 1, True),
    (BITMASK_STARTING, 0, False),
    (BITMASK_STOPPING, 2, True),
    (BITMASK_STOPPING, 1, False),
    (BITMASK_FAN, 4, True),
    (BITMASK_FAN, 3, False),
    (BITMASK_HEATING, 16, True),
    (BITMASK_COOLING, 32, True),
    (BITMASK_ALARM_F, 2048, True),
    (BITMASK_ALARM_W, 4096, True),
]

EXPECTED_KEYS = {
    "status_starting",
    "status_stopping",
    "status_fan",
    "status_rotor",
    "status_heating",
    "status_cooling",
    "status_heating_denied",
    "status_cooling_denied",
    "status_flow_down",
    "status_free_heating",
    "status_free_cooling",
    "status_alarm_fault",
    "status_alarm_warning",
}

# ==================== Entity Tests ====================


def test_entity_properties(mock_coordinator):
    """Test binary sensor entity initialization and properties."""
    s = KomfoventBinarySensor(mock_coordinator, 100, DESC)
    assert s.register_id == 100
    assert s.unique_id == "test_entry_id_test"
    assert s.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}


@pytest.mark.parametrize(("data", "expected"), IS_ON_CASES)
def test_is_on(mock_coordinator, data, expected):
    """Test is_on for various data states."""
    mock_coordinator.data = data
    assert KomfoventBinarySensor(mock_coordinator, 100, DESC).is_on is expected


# ==================== Status Binary Sensor Tests ====================


def test_status_sensor_bitmask(mock_coordinator):
    """Test status binary sensor has bitmask attribute."""
    s = KomfoventStatusBinarySensor(
        mock_coordinator, registers.REG_STATUS, BITMASK_FAN, DESC
    )
    assert s.bitmask == BITMASK_FAN


@pytest.mark.parametrize(("bitmask", "status_value", "expected"), BITMASK_CASES)
def test_status_is_on_bitmask(mock_coordinator, bitmask, status_value, expected):
    """Test is_on with various bitmask values."""
    mock_coordinator.data = {registers.REG_STATUS: status_value}
    s = KomfoventStatusBinarySensor(
        mock_coordinator, registers.REG_STATUS, bitmask, DESC
    )
    assert s.is_on is expected


def test_multiple_bits_set(mock_coordinator):
    """Test is_on when multiple bits are set."""
    mock_coordinator.data = {registers.REG_STATUS: 21}  # bits 0, 2, 4
    assert (
        KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_FAN, DESC
        ).is_on
        is True
    )
    assert (
        KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_STOPPING, DESC
        ).is_on
        is False
    )


@pytest.mark.parametrize(("data", "expected"), [(None, None), ({}, None)])
def test_status_edge_cases(mock_coordinator, data, expected):
    """Test is_on edge cases."""
    mock_coordinator.data = data
    assert (
        KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_FAN, DESC
        ).is_on
        is expected
    )


# ==================== Factory Tests ====================


async def test_create_binary_sensors(mock_coordinator):
    """Test all 13 status binary sensors are created."""
    sensors = await create_binary_sensors(mock_coordinator)
    assert len(sensors) == 13
    assert {s.entity_description.key for s in sensors} == EXPECTED_KEYS
