"""Tests for Komfovent datetime platform."""

import zoneinfo
from datetime import datetime

import pytest
from homeassistant.components.datetime import DateTimeEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.datetime import KomfoventDateTime

DESC = DateTimeEntityDescription(key="test_datetime", name="Test")

# ==================== Data Tables ====================

NATIVE_VALUE_CASES = [
    (1000000, "UTC", 1970, 1, 12),
    (0, "Europe/Amsterdam", 1970, 1, 1),
]

EDGE_CASES = [(None, None), ({}, None), ({100: "invalid"}, None)]

SET_VALUE_CASES = [
    (
        "UTC",
        datetime(1970, 1, 12, 13, 46, 40, tzinfo=zoneinfo.ZoneInfo("UTC")),
        1000000,
    ),
]

# ==================== Entity Tests ====================


def test_entity_properties(mock_coordinator):
    """Test datetime entity initialization and properties."""
    dt = KomfoventDateTime(mock_coordinator, 100, DESC)
    assert dt.register_id == 100
    assert dt.unique_id == "test_entry_id_test_datetime"
    assert dt.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}


# ==================== Native Value Tests ====================


@pytest.mark.parametrize(
    ("seconds", "timezone", "year", "month", "day"), NATIVE_VALUE_CASES
)
def test_native_value(mock_coordinator, seconds, timezone, year, month, day):
    """Test native_value returns correct datetime."""
    mock_coordinator.data = {100: seconds}
    mock_coordinator.hass.config.time_zone = timezone
    result = KomfoventDateTime(mock_coordinator, 100, DESC).native_value
    assert result.year == year
    assert result.month == month
    assert result.day == day


@pytest.mark.parametrize(("data", "expected"), EDGE_CASES)
def test_native_value_edge_cases(mock_coordinator, data, expected):
    """Test native_value edge cases."""
    mock_coordinator.data = data
    mock_coordinator.hass.config.time_zone = "UTC"
    assert KomfoventDateTime(mock_coordinator, 100, DESC).native_value is expected


# ==================== Async Set Value Tests ====================


@pytest.mark.parametrize(("timezone", "dt_value", "expected_seconds"), SET_VALUE_CASES)
async def test_set_value(mock_coordinator, timezone, dt_value, expected_seconds):
    """Test async_set_value with timezone-aware datetime."""
    mock_coordinator.hass.config.time_zone = timezone
    await KomfoventDateTime(mock_coordinator, 100, DESC).async_set_value(dt_value)
    mock_coordinator.client.write.assert_called_once_with(100, expected_seconds)
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_set_value_naive_datetime(mock_coordinator):
    """Test async_set_value with timezone-naive datetime."""
    mock_coordinator.hass.config.time_zone = "UTC"
    value = datetime(1970, 1, 12, 13, 46, 40)  # noqa: DTZ001
    await KomfoventDateTime(mock_coordinator, 100, DESC).async_set_value(value)
    mock_coordinator.client.write.assert_called_once_with(100, 1000000)


async def test_set_value_holidays_register(mock_coordinator):
    """Test async_set_value for holidays_from register."""
    mock_coordinator.hass.config.time_zone = "UTC"
    desc = DateTimeEntityDescription(key="holidays_from", name="Holidays From")
    dt = KomfoventDateTime(mock_coordinator, registers.REG_HOLIDAYS_FROM, desc)
    value = datetime(2024, 1, 15, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    await dt.async_set_value(value)
    expected = int(
        (value - datetime(1970, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))).total_seconds()
    )
    mock_coordinator.client.write.assert_called_once_with(
        registers.REG_HOLIDAYS_FROM, expected
    )
