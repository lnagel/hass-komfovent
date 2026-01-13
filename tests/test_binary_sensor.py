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


class TestKomfoventBinarySensor:
    """Tests for base KomfoventBinarySensor entity."""

    def test_initialization(self, mock_coordinator):
        """Test binary sensor initialization."""
        description = BinarySensorEntityDescription(
            key="test_sensor",
            name="Test Sensor",
        )
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.register_id == 100
        assert sensor.entity_description.key == "test_sensor"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = BinarySensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.unique_id == "test_entry_id_test_sensor"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = BinarySensorEntityDescription(key="test_sensor", name="Test")
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        device_info = sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"

    def test_is_on_true(self, mock_coordinator):
        """Test is_on returns True for non-zero value."""
        mock_coordinator.data = {100: 1}
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.is_on is True

    def test_is_on_false(self, mock_coordinator):
        """Test is_on returns False for zero value."""
        mock_coordinator.data = {100: 0}
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.is_on is False

    def test_is_on_no_data(self, mock_coordinator):
        """Test is_on returns None when no data."""
        mock_coordinator.data = None
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.is_on is None

    def test_is_on_missing_register(self, mock_coordinator):
        """Test is_on returns None for missing register."""
        mock_coordinator.data = {}
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventBinarySensor(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert sensor.is_on is None


class TestKomfoventStatusBinarySensor:
    """Tests for KomfoventStatusBinarySensor with bitmask operations."""

    def test_initialization_with_bitmask(self, mock_coordinator):
        """Test status binary sensor initialization with bitmask."""
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FAN,
            entity_description=description,
        )

        assert sensor.bitmask == BITMASK_FAN

    @pytest.mark.parametrize(
        ("bitmask", "status_value", "expected"),
        [
            (BITMASK_STARTING, 1, True),  # Bit 0 set
            (BITMASK_STARTING, 0, False),  # Bit 0 not set
            (BITMASK_STOPPING, 2, True),  # Bit 1 set
            (BITMASK_STOPPING, 1, False),  # Bit 1 not set
            (BITMASK_FAN, 4, True),  # Bit 2 set
            (BITMASK_FAN, 3, False),  # Bit 2 not set
            (BITMASK_HEATING, 16, True),  # Bit 4 set
            (BITMASK_COOLING, 32, True),  # Bit 5 set
            (BITMASK_ALARM_F, 2048, True),  # Bit 11 set
            (BITMASK_ALARM_W, 4096, True),  # Bit 12 set
        ],
    )
    def test_is_on_bitmask(self, mock_coordinator, bitmask, status_value, expected):
        """Test is_on with various bitmask values."""
        mock_coordinator.data = {registers.REG_STATUS: status_value}
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_STATUS,
            bitmask=bitmask,
            entity_description=description,
        )

        assert sensor.is_on is expected

    def test_is_on_multiple_bits_set(self, mock_coordinator):
        """Test is_on when multiple bits are set."""
        # Set bits 0, 2, and 4 (1 + 4 + 16 = 21)
        mock_coordinator.data = {registers.REG_STATUS: 21}
        description = BinarySensorEntityDescription(key="test", name="Test")

        # Test that FAN (bit 2) is on
        sensor = KomfoventStatusBinarySensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FAN,
            entity_description=description,
        )
        assert sensor.is_on is True

        # Test that STOPPING (bit 1) is off
        sensor2 = KomfoventStatusBinarySensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_STOPPING,
            entity_description=description,
        )
        assert sensor2.is_on is False

    def test_is_on_no_data(self, mock_coordinator):
        """Test is_on returns None when no data."""
        mock_coordinator.data = None
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FAN,
            entity_description=description,
        )

        assert sensor.is_on is None

    def test_is_on_missing_register(self, mock_coordinator):
        """Test is_on returns None for missing register."""
        mock_coordinator.data = {}
        description = BinarySensorEntityDescription(key="test", name="Test")
        sensor = KomfoventStatusBinarySensor(
            coordinator=mock_coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FAN,
            entity_description=description,
        )

        assert sensor.is_on is None


class TestCreateBinarySensors:
    """Tests for create_binary_sensors factory function."""

    async def test_creates_all_status_sensors(self, mock_coordinator):
        """Test that all 13 status binary sensors are created."""
        sensors = await create_binary_sensors(mock_coordinator)

        assert len(sensors) == 13

        expected_keys = {
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

        sensor_keys = {s.entity_description.key for s in sensors}
        assert sensor_keys == expected_keys
