"""Tests for Komfovent datetime platform."""

import zoneinfo
from datetime import datetime

import pytest
from homeassistant.components.datetime import DateTimeEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.datetime import KomfoventDateTime

# ==================== Entity Tests ====================


class TestKomfoventDateTime:
    """Tests for KomfoventDateTime entity."""

    def test_initialization(self, mock_coordinator):
        """Test datetime entity initialization."""
        description = DateTimeEntityDescription(
            key="test_datetime", name="Test DateTime"
        )
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        assert dt_entity.register_id == 100
        assert dt_entity.entity_description.key == "test_datetime"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = DateTimeEntityDescription(key="test_datetime", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        assert dt_entity.unique_id == "test_entry_id_test_datetime"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = DateTimeEntityDescription(key="test_datetime", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        device_info = dt_entity.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


# ==================== Native Value Tests ====================


class TestNativeValue:
    """Tests for native_value property."""

    @pytest.mark.parametrize(
        ("seconds", "timezone", "expected_year", "expected_month", "expected_day"),
        [
            (1000000, "UTC", 1970, 1, 12),
            (0, "Europe/Amsterdam", 1970, 1, 1),
        ],
    )
    def test_valid_values(
        self,
        mock_coordinator,
        seconds,
        timezone,
        expected_year,
        expected_month,
        expected_day,
    ):
        """Test native_value returns correct datetime for valid value."""
        mock_coordinator.data = {100: seconds}
        mock_coordinator.hass.config.time_zone = timezone
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        result = dt_entity.native_value
        assert result is not None
        assert result.year == expected_year
        assert result.month == expected_month
        assert result.day == expected_day

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, None),
            ({}, None),
            ({100: "invalid"}, None),
        ],
    )
    def test_edge_cases(self, mock_coordinator, data, expected):
        """Test native_value edge cases."""
        mock_coordinator.data = data
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        assert dt_entity.native_value is expected


# ==================== Async Set Value Tests ====================


class TestAsyncSetValue:
    """Tests for async_set_value method."""

    @pytest.mark.parametrize(
        ("timezone", "dt_value", "expected_seconds"),
        [
            (
                "UTC",
                datetime(1970, 1, 12, 13, 46, 40, tzinfo=zoneinfo.ZoneInfo("UTC")),
                1000000,
            ),
        ],
    )
    async def test_set_value_with_timezone(
        self, mock_coordinator, timezone, dt_value, expected_seconds
    ):
        """Test async_set_value with timezone-aware datetime."""
        mock_coordinator.hass.config.time_zone = timezone
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        await dt_entity.async_set_value(dt_value)

        mock_coordinator.client.write.assert_called_once_with(100, expected_seconds)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_set_value_without_timezone(self, mock_coordinator):
        """Test async_set_value with timezone-naive datetime."""
        mock_coordinator.hass.config.time_zone = "UTC"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

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
            mock_coordinator, registers.REG_HOLIDAYS_FROM, description
        )

        value = datetime(2024, 1, 15, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        await dt_entity.async_set_value(value)

        expected_seconds = int(
            (
                value - datetime(1970, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
            ).total_seconds()
        )
        mock_coordinator.client.write.assert_called_once_with(
            registers.REG_HOLIDAYS_FROM, expected_seconds
        )

    async def test_set_value_different_timezone(self, mock_coordinator):
        """Test async_set_value with a different timezone than local."""
        mock_coordinator.hass.config.time_zone = "Europe/Amsterdam"
        description = DateTimeEntityDescription(key="test", name="Test")
        dt_entity = KomfoventDateTime(mock_coordinator, 100, description)

        value = datetime(1970, 1, 1, 1, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        await dt_entity.async_set_value(value)

        mock_coordinator.client.write.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()
