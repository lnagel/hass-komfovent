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


class TestKomfoventSelect:
    """Tests for KomfoventSelect entity."""

    def test_initialization(self, mock_coordinator):
        """Test select entity initialization."""
        description = SelectEntityDescription(
            key="test_select",
            name="Test Select",
            options=[mode.name.lower() for mode in SchedulerMode],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        assert select.register_id == 100
        assert select.enum_class == SchedulerMode

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = SelectEntityDescription(
            key="test_select",
            name="Test",
            options=["a", "b"],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        assert select.unique_id == "test_entry_id_test_select"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = SelectEntityDescription(
            key="test_select",
            name="Test",
            options=["a", "b"],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        device_info = select.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


class TestCurrentOption:
    """Tests for current_option property."""

    @pytest.mark.parametrize(
        ("enum_class", "value", "expected"),
        [
            (SchedulerMode, SchedulerMode.STAY_AT_HOME, "stay_at_home"),
            (SchedulerMode, SchedulerMode.WORKING_WEEK, "working_week"),
            (SchedulerMode, SchedulerMode.OFFICE, "office"),
            (SchedulerMode, SchedulerMode.CUSTOM, "custom"),
            (TemperatureControl, TemperatureControl.SUPPLY, "supply"),
            (TemperatureControl, TemperatureControl.EXTRACT, "extract"),
            (TemperatureControl, TemperatureControl.ROOM, "room"),
            (OperationMode, OperationMode.NORMAL, "normal"),
            (OperationMode, OperationMode.AWAY, "away"),
        ],
    )
    def test_current_option_valid_values(
        self, mock_coordinator, enum_class, value, expected
    ):
        """Test current_option returns correct option for valid values."""
        mock_coordinator.data = {100: value}
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in enum_class],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=enum_class,
            entity_description=description,
        )

        assert select.current_option == expected

    def test_current_option_no_data(self, mock_coordinator):
        """Test current_option returns None when no data."""
        mock_coordinator.data = None
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=["a", "b"],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        assert select.current_option is None

    def test_current_option_invalid_value(self, mock_coordinator):
        """Test current_option returns None for invalid enum value."""
        mock_coordinator.data = {100: 99}  # Invalid value
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=["a", "b"],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        assert select.current_option is None


class TestAsyncSelectOption:
    """Tests for async_select_option method."""

    async def test_select_option_writes_to_register(self, mock_coordinator):
        """Test async_select_option writes enum value to register."""
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in SchedulerMode],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        await select.async_select_option("working_week")

        mock_coordinator.client.write.assert_called_once_with(
            100, SchedulerMode.WORKING_WEEK.value
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_select_option_case_insensitive(self, mock_coordinator):
        """Test async_select_option handles case insensitivity."""
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in SchedulerMode],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        await select.async_select_option("OFFICE")

        mock_coordinator.client.write.assert_called_once_with(
            100, SchedulerMode.OFFICE.value
        )

    async def test_select_option_invalid_option(self, mock_coordinator):
        """
        Test async_select_option raises KeyError for invalid option.

        Note: The code has a bug - it catches ValueError but should catch KeyError.
        This test documents the actual behavior.
        """
        description = SelectEntityDescription(
            key="test",
            name="Test",
            options=[m.name.lower() for m in SchedulerMode],
        )
        select = KomfoventSelect(
            coordinator=mock_coordinator,
            register_id=100,
            enum_class=SchedulerMode,
            entity_description=description,
        )

        # Invalid option raises KeyError (enum lookup failure)
        with pytest.raises(KeyError):
            await select.async_select_option("invalid_option")


class TestKomfoventOperationModeSelect:
    """Tests for KomfoventOperationModeSelect entity."""

    async def test_select_option_delegates_to_services(self, mock_coordinator):
        """Test async_select_option delegates to services.set_operation_mode."""
        description = SelectEntityDescription(
            key="operation_mode",
            name="Operation mode",
            options=[m.name.lower() for m in OperationMode],
        )
        select = KomfoventOperationModeSelect(
            coordinator=mock_coordinator,
            register_id=registers.REG_OPERATION_MODE,
            enum_class=OperationMode,
            entity_description=description,
        )

        with patch(
            "custom_components.komfovent.select.services.set_operation_mode",
            new_callable=AsyncMock,
        ) as mock_set_mode:
            await select.async_select_option("away")

            mock_set_mode.assert_called_once_with(mock_coordinator, "away")

    async def test_select_option_various_modes(self, mock_coordinator):
        """Test async_select_option with various operation modes."""
        description = SelectEntityDescription(
            key="operation_mode",
            name="Operation mode",
            options=[m.name.lower() for m in OperationMode],
        )
        select = KomfoventOperationModeSelect(
            coordinator=mock_coordinator,
            register_id=registers.REG_OPERATION_MODE,
            enum_class=OperationMode,
            entity_description=description,
        )

        for mode in ["normal", "intensive", "boost", "kitchen", "fireplace", "off"]:
            with patch(
                "custom_components.komfovent.select.services.set_operation_mode",
                new_callable=AsyncMock,
            ) as mock_set_mode:
                await select.async_select_option(mode)
                mock_set_mode.assert_called_once_with(mock_coordinator, mode)
