"""Tests for Komfovent datetime platform."""

import zoneinfo
from datetime import datetime

from homeassistant.components.datetime import DateTimeEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.datetime import KomfoventDateTime


class TestKomfoventDateTime:
    """Tests for KomfoventDateTime entity."""

    def test_initialization(self, mock_coordinator):
        """Test datetime entity initialization."""
        description = DateTimeEntityDescription(
            key="test_datetime",
            name="Test DateTime",
        )
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert dt_entity.register_id == 100
        assert dt_entity.entity_description.key == "test_datetime"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = DateTimeEntityDescription(key="test_datetime", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert dt_entity.unique_id == "test_entry_id_test_datetime"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = DateTimeEntityDescription(key="test_datetime", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        device_info = dt_entity.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


class TestNativeValue:
    """Tests for native_value property."""

    def test_native_value_valid(self, mock_coordinator):
        """Test native_value returns correct datetime for valid value."""
        # 1000000 seconds since local epoch
        mock_coordinator.data = {100: 1000000}
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        result = dt_entity.native_value
        assert result is not None
        # 1000000 seconds = ~11.57 days from epoch
        expected = datetime(1970, 1, 12, 13, 46, 40, tzinfo=zoneinfo.ZoneInfo("UTC"))
        assert result == expected

    def test_native_value_with_timezone(self, mock_coordinator):
        """Test native_value with non-UTC timezone."""
        # 0 seconds = epoch in local timezone
        mock_coordinator.data = {100: 0}
        mock_coordinator.hass.config.time_zone = "Europe/Amsterdam"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        result = dt_entity.native_value
        assert result is not None
        expected = datetime(
            1970, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Amsterdam")
        )
        assert result == expected

    def test_native_value_no_data(self, mock_coordinator):
        """Test native_value returns None when no data."""
        mock_coordinator.data = None
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert dt_entity.native_value is None

    def test_native_value_missing_register(self, mock_coordinator):
        """Test native_value returns None for missing register."""
        mock_coordinator.data = {}
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert dt_entity.native_value is None

    def test_native_value_invalid_value(self, mock_coordinator):
        """Test native_value returns None for invalid value."""
        mock_coordinator.data = {100: "invalid"}
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert dt_entity.native_value is None


class TestAsyncSetValue:
    """Tests for async_set_value method."""

    async def test_set_value_with_timezone(self, mock_coordinator):
        """Test async_set_value with timezone-aware datetime."""
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        # Set to a specific datetime (1000000 seconds from epoch)
        value = datetime(1970, 1, 12, 13, 46, 40, tzinfo=zoneinfo.ZoneInfo("UTC"))
        await dt_entity.async_set_value(value)

        mock_coordinator.client.write.assert_called_once_with(100, 1000000)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_value_without_timezone(self, mock_coordinator):
        """Test async_set_value with timezone-naive datetime."""
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        # Set to a naive datetime (should assume local timezone)
        value = datetime(1970, 1, 12, 13, 46, 40)  # noqa: DTZ001
        await dt_entity.async_set_value(value)

        mock_coordinator.client.write.assert_called_once_with(100, 1000000)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_value_holidays_from(self, mock_coordinator):
        """Test async_set_value for holidays_from register."""
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(
            key="holidays_from", name="Holidays From"
        )
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=registers.REG_HOLIDAYS_FROM,
            entity_description=description,
        )

        # Set to Jan 15, 2024 at midnight UTC
        value = datetime(2024, 1, 15, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        await dt_entity.async_set_value(value)

        # Calculate expected seconds since epoch
        expected_seconds = int(
            (
                value - datetime(1970, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
            ).total_seconds()
        )
        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_HOLIDAYS_FROM, expected_seconds
        )

    async def test_set_value_with_different_timezone(self, mock_coordinator):
        """Test async_set_value with a different timezone than local."""
        mock_coordinator.hass.config.time_zone = "Europe/Amsterdam"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        # Set using UTC datetime, but local epoch is Amsterdam
        value = datetime(1970, 1, 1, 1, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        await dt_entity.async_set_value(value)

        # UTC 01:00 is same moment as Amsterdam 02:00 (CET = UTC+1 in winter 1970)
        # Local epoch in Amsterdam is 1970-01-01 00:00:00+01:00
        # So UTC 01:00 is 2 hours after local epoch in Amsterdam
        mock_coordinator.client.write.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()
