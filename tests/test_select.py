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

# ==================== Data Tables ====================

CURRENT_OPTION_CASES = [
    (SchedulerMode, SchedulerMode.STAY_AT_HOME, "stay_at_home"),
    (SchedulerMode, SchedulerMode.WORKING_WEEK, "working_week"),
    (SchedulerMode, SchedulerMode.OFFICE, "office"),
    (SchedulerMode, SchedulerMode.CUSTOM, "custom"),
    (TemperatureControl, TemperatureControl.SUPPLY, "supply"),
    (TemperatureControl, TemperatureControl.EXTRACT, "extract"),
    (TemperatureControl, TemperatureControl.ROOM, "room"),
    (OperationMode, OperationMode.NORMAL, "normal"),
    (OperationMode, OperationMode.AWAY, "away"),
]


# ==================== Base Select Tests ====================


class TestKomfoventSelect:
    """Tests for KomfoventSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test select entity initialization."""
        description = SelectEntityDescription(
            key="test_select",
            name="Test Select",
            options=[mode.name.lower() for mode in SchedulerMode],
        )
        select = KomfoventSelect(mock_coordinator, 100, SchedulerMode, description)

        assert select.register_id == 100
        assert select.enum_class == SchedulerMode

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = SelectEntityDescription(
            key="test_select", name="Test", options=["a"]
        )
        select = KomfoventSelect(mock_coordinator, 100, SchedulerMode, description)

        assert select.unique_id == "test_entry_id_test_select"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = SelectEntityDescription(
            key="test_select", name="Test", options=["a"]
        )
        select = KomfoventSelect(mock_coordinator, 100, SchedulerMode, description)

        device_info = select.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


# ==================== Current Option Tests ====================


class TestCurrentOption:
    """Tests for current_option property."""

    @pytest.mark.parametrize(("enum_class", "value", "expected"), CURRENT_OPTION_CASES)
    def test_valid_values(self, mock_coordinator, enum_class, value, expected):
        """Test current_option returns correct option for valid values."""
        mock_coordinator.data = {100: value}
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in enum_class],
        )
        select = KomfoventSelect(mock_coordinator, 100, enum_class, description)

        assert select.current_option == expected

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (None, None),
            ({100: 99}, None),
        ],
    )
    def test_edge_cases(self, mock_coordinator, data, expected):
        """Test current_option edge cases."""
        mock_coordinator.data = data
        description = SelectEntityDescription(key="test", name="Test", options=["a"])
        select = KomfoventSelect(mock_coordinator, 100, SchedulerMode, description)

        assert select.current_option is expected


# ==================== Async Select Option Tests ====================


class TestAsyncSelectOption:
    """Tests for async_select_option method."""

    @pytest.mark.parametrize(
        ("option", "expected_value"),
        [
            ("working_week", SchedulerMode.WORKING_WEEK.value),
            ("OFFICE", SchedulerMode.OFFICE.value),
        ],
    )
    async def test_select_option(self, mock_coordinator, option, expected_value):
        """Test async_select_option writes enum value to register."""
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in SchedulerMode],
        )
        select = KomfoventSelect(mock_coordinator, 100, SchedulerMode, description)

        await select.async_select_option(option)

        mock_coordinator.client.write.assert_called_once_with(100, expected_value)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_invalid_option(self, mock_coordinator):
        """Test async_select_option raises KeyError for invalid option."""
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in SchedulerMode],
        )
        select = KomfoventSelect(mock_coordinator, 100, SchedulerMode, description)

        with pytest.raises(KeyError):
            await select.async_select_option("invalid_option")


# ==================== Operation Mode Select Tests ====================


class TestKomfoventOperationModeSelect:
    """Tests for KomfoventOperationModeSelect entity."""

    @pytest.mark.parametrize(
        "mode", ["away", "normal", "intensive", "boost", "kitchen", "fireplace", "off"]
    )
    async def test_select_option_delegates_to_services(self, mock_coordinator, mode):
        """Test async_select_option delegates to services.set_operation_mode."""
        description = SelectEntityDescription(
            key="operation_mode",
            name="Operation mode",
            options=[m.name.lower() for m in OperationMode],
        )
        select = KomfoventOperationModeSelect(
            mock_coordinator, registers.REG_OPERATION_MODE, OperationMode, description
        )

        with patch(
            "custom_components.komfovent.select.services.set_operation_mode",
            new_callable=AsyncMock,
        ) as mock_set_mode:
            await select.async_select_option(mode)
            mock_set_mode.assert_called_once_with(mock_coordinator, mode)
