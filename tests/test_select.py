"""Tests for Komfovent select platform."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.select import SelectEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import (
    DOMAIN,
    OperationMode,
    SchedulerMode,
    TemperatureControl,
)
from custom_components.komfovent.select import (
    KomfoventOperationModeSelect,
    KomfoventSelect,
)

DESC = SelectEntityDescription(key="test", name="Test", options=["a"])

# ==================== Data Tables ====================

CURRENT_OPTION_CASES = [
    (SchedulerMode, SchedulerMode.STAY_AT_HOME, "stay_at_home"),
    (SchedulerMode, SchedulerMode.WORKING_WEEK, "working_week"),
    (SchedulerMode, SchedulerMode.OFFICE, "office"),
    (TemperatureControl, TemperatureControl.SUPPLY, "supply"),
    (OperationMode, OperationMode.NORMAL, "normal"),
    (OperationMode, OperationMode.AWAY, "away"),
]

SELECT_OPTION_CASES = [
    ("working_week", SchedulerMode.WORKING_WEEK.value),
    ("OFFICE", SchedulerMode.OFFICE.value),
]

EDGE_CASES = [(None, None), ({100: 99}, None)]

# ==================== Entity Tests ====================


def test_entity_properties(mock_coordinator):
    """Test select entity initialization and properties."""
    s = KomfoventSelect(mock_coordinator, 100, SchedulerMode, DESC)
    assert s.register_id == 100
    assert s.enum_class == SchedulerMode
    assert s.unique_id == "test_entry_id_test"
    assert s.device_info["identifiers"] == {(DOMAIN, "test_entry_id")}


# ==================== Current Option Tests ====================


@pytest.mark.parametrize(("enum_class", "value", "expected"), CURRENT_OPTION_CASES)
def test_current_option(mock_coordinator, enum_class, value, expected):
    """Test current_option returns correct option."""
    mock_coordinator.data = {100: value}
    desc = SelectEntityDescription(
        key="t", name="T", options=[m.name.lower() for m in enum_class]
    )
    assert (
        KomfoventSelect(mock_coordinator, 100, enum_class, desc).current_option
        == expected
    )


@pytest.mark.parametrize(("data", "expected"), EDGE_CASES)
def test_current_option_edge_cases(mock_coordinator, data, expected):
    """Test current_option edge cases."""
    mock_coordinator.data = data
    assert (
        KomfoventSelect(mock_coordinator, 100, SchedulerMode, DESC).current_option
        is expected
    )


# ==================== Select Option Tests ====================


@pytest.mark.parametrize(("option", "expected_value"), SELECT_OPTION_CASES)
async def test_select_option(mock_coordinator, option, expected_value):
    """Test async_select_option writes enum value."""
    desc = SelectEntityDescription(
        key="t", name="T", options=[m.name.lower() for m in SchedulerMode]
    )
    await KomfoventSelect(
        mock_coordinator, 100, SchedulerMode, desc
    ).async_select_option(option)
    mock_coordinator.client.write.assert_called_once_with(100, expected_value)
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_select_invalid_option(mock_coordinator):
    """Test async_select_option raises KeyError for invalid option."""
    desc = SelectEntityDescription(
        key="t", name="T", options=[m.name.lower() for m in SchedulerMode]
    )
    with pytest.raises(KeyError):
        await KomfoventSelect(
            mock_coordinator, 100, SchedulerMode, desc
        ).async_select_option("invalid")


# ==================== Operation Mode Select Tests ====================


@pytest.mark.parametrize(
    "mode", ["away", "normal", "intensive", "boost", "kitchen", "fireplace", "off"]
)
async def test_operation_mode_delegates_to_services(mock_coordinator, mode):
    """Test operation mode select delegates to services."""
    desc = SelectEntityDescription(
        key="op", name="Op", options=[m.name.lower() for m in OperationMode]
    )
    select = KomfoventOperationModeSelect(
        mock_coordinator, registers.REG_OPERATION_MODE, OperationMode, desc
    )
    with patch(
        "custom_components.komfovent.select.services.set_operation_mode",
        new_callable=AsyncMock,
    ) as mock:
        await select.async_select_option(mode)
        mock.assert_called_once_with(mock_coordinator, mode)
