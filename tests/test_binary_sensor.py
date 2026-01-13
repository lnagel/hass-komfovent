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

# ==================== Data Tables ====================

BITMASK_TEST_CASES = [
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

EXPECTED_STATUS_KEYS = {
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


# ==================== Base Binary Sensor Tests ====================


class TestKomfoventBinarySensor:
    """Tests for base KomfoventBinarySensor entity."""

    def test_initialization(self, mock_coordinator):
        """Test binary sensor initialization."""
        description = BinarySensorEntityDescription(
            key="test_sensor", name="Test Sensor"
        )
        sensor = KomfoventBinarySensor(mock_coordinator, 100, description)

        assert sensor.register_id == 100
        assert sensor.entity_description.key == "test_sensor"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = BinarySensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventBinarySensor(mock_coordinator, 100, description)

        assert sensor.unique_id == "test_entry_id_test_sensor"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = BinarySensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventBinarySensor(mock_coordinator, 100, description)

        device_info = sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            ({100: 1}, True),
            ({100: 0}, False),
            (None, None),
            ({}, None),
        ],
    )
    def test_is_on(self, mock_coordinator, data, expected):
        """Test is_on for various data states."""
        mock_coordinator.data = data
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventBinarySensor(mock_coordinator, 100, description)

        assert sensor.is_on is expected


# ==================== Status Binary Sensor Tests ====================


class TestKomfoventStatusBinarySensor:
    """Tests for KomfoventStatusBinarySensor with bitmask operations."""

    def test_initialization_with_bitmask(self, mock_coordinator):
        """Test status binary sensor initialization with bitmask."""
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_FAN, description
        )

        assert sensor.bitmask == BITMASK_FAN

    @pytest.mark.parametrize(
        ("bitmask", "status_value", "expected"), BITMASK_TEST_CASES
    )
    def test_is_on_bitmask(self, mock_coordinator, bitmask, status_value, expected):
        """Test is_on with various bitmask values."""
        mock_coordinator.data = {registers.REG_STATUS: status_value}
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, bitmask, description
        )

        assert sensor.is_on is expected

    def test_multiple_bits_set(self, mock_coordinator):
        """Test is_on when multiple bits are set."""
        mock_coordinator.data = {registers.REG_STATUS: 21}  # bits 0, 2, 4
        description = BinarySensorEntityDescription(key="test", name="Test")

        # FAN (bit 2) should be on
        sensor = KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_FAN, description
        )
        assert sensor.is_on is True

        # STOPPING (bit 1) should be off
        sensor2 = KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_STOPPING, description
        )
        assert sensor2.is_on is False

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, None),
            ({}, None),
        ],
    )
    def test_edge_cases(self, mock_coordinator, data, expected):
        """Test is_on edge cases."""
        mock_coordinator.data = data
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            mock_coordinator, registers.REG_STATUS, BITMASK_FAN, description
        )

        assert sensor.is_on is expected


# ==================== Factory Function Tests ====================


class TestCreateBinarySensors:
    """Tests for create_binary_sensors factory function."""

    async def test_creates_all_status_sensors(self, mock_coordinator):
        """Test that all 13 status binary sensors are created."""
        sensors = await create_binary_sensors(mock_coordinator)

        assert len(sensors) == 13
        sensor_keys = {s.entity_description.key for s in sensors}
        assert sensor_keys == EXPECTED_STATUS_KEYS
