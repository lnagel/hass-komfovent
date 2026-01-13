"""Tests for Komfovent button platform."""

from unittest.mock import AsyncMock, patch

from homeassistant.components.button import ButtonEntityDescription

from custom_components.komfovent.button import (
    KomfoventButtonEntity,
    KomfoventCleanFiltersButton,
    KomfoventSetTimeButton,
)
from custom_components.komfovent.const import DOMAIN


class TestKomfoventButtonEntity:
    """Tests for base KomfoventButtonEntity."""

    def test_initialization(self, mock_coordinator):
        """Test button entity initialization."""
        description = ButtonEntityDescription(
            key="test_button",
            name="Test Button",
        )
        button = KomfoventButtonEntity(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        assert button.entity_description.key == "test_button"
        assert button._attr_has_entity_name is True

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = ButtonEntityDescription(key="test_button", name="Test")
        button = KomfoventButtonEntity(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        assert button.unique_id == "test_entry_id_test_button"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = ButtonEntityDescription(key="test_button", name="Test")
        button = KomfoventButtonEntity(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        device_info = button.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


class TestKomfoventSetTimeButton:
    """Tests for KomfoventSetTimeButton."""

    def test_initialization(self, mock_coordinator):
        """Test set time button initialization."""
        description = ButtonEntityDescription(
            key="set_system_time",
            name="Set System Time",
        )
        button = KomfoventSetTimeButton(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        assert button.entity_description.key == "set_system_time"

    async def test_async_press(self, mock_coordinator):
        """Test async_press calls services.set_system_time."""
        description = ButtonEntityDescription(
            key="set_system_time",
            name="Set System Time",
        )
        button = KomfoventSetTimeButton(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        with patch(
            "custom_components.komfovent.button.services.set_system_time",
            new_callable=AsyncMock,
        ) as mock_set_time:
            await button.async_press()

            mock_set_time.assert_called_once_with(mock_coordinator)


class TestKomfoventCleanFiltersButton:
    """Tests for KomfoventCleanFiltersButton."""

    def test_initialization(self, mock_coordinator):
        """Test clean filters button initialization."""
        description = ButtonEntityDescription(
            key="clean_filters",
            name="Clean Filters Calibration",
        )
        button = KomfoventCleanFiltersButton(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        assert button.entity_description.key == "clean_filters"

    async def test_async_press(self, mock_coordinator):
        """Test async_press calls services.clean_filters_calibration."""
        description = ButtonEntityDescription(
            key="clean_filters",
            name="Clean Filters Calibration",
        )
        button = KomfoventCleanFiltersButton(
            coordinator=mock_coordinator,
            entity_description=description,
        )

        with patch(
            "custom_components.komfovent.button.services.clean_filters_calibration",
            new_callable=AsyncMock,
        ) as mock_clean_filters:
            await button.async_press()

            mock_clean_filters.assert_called_once_with(mock_coordinator)
