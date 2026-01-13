"""Tests for Komfovent button platform."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.button import ButtonEntityDescription

from custom_components.komfovent.button import (
    KomfoventButtonEntity,
    KomfoventCleanFiltersButton,
    KomfoventSetTimeButton,
)
from custom_components.komfovent.const import DOMAIN

# ==================== Data Tables ====================

BUTTON_TYPES = [
    (
        KomfoventSetTimeButton,
        "set_system_time",
        "custom_components.komfovent.button.services.set_system_time",
    ),
    (
        KomfoventCleanFiltersButton,
        "clean_filters",
        "custom_components.komfovent.button.services.clean_filters_calibration",
    ),
]


# ==================== Base Button Tests ====================


class TestKomfoventButtonEntity:
    """Tests for base KomfoventButtonEntity."""

    def test_initialization(self, mock_coordinator):
        """Test button entity initialization."""
        description = ButtonEntityDescription(key="test_button", name="Test Button")
        button = KomfoventButtonEntity(mock_coordinator, description)

        assert button.entity_description.key == "test_button"
        assert button._attr_has_entity_name is True

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = ButtonEntityDescription(key="test_button", name="Test")
        button = KomfoventButtonEntity(mock_coordinator, description)

        assert button.unique_id == "test_entry_id_test_button"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = ButtonEntityDescription(key="test_button", name="Test")
        button = KomfoventButtonEntity(mock_coordinator, description)

        device_info = button.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


# ==================== Button Specific Tests ====================


@pytest.mark.parametrize(("button_class", "key", "service_path"), BUTTON_TYPES)
class TestButtonPress:
    """Tests for button async_press methods."""

    def test_initialization(self, mock_coordinator, button_class, key, service_path):
        """Test button initialization."""
        description = ButtonEntityDescription(key=key, name="Test")
        button = button_class(mock_coordinator, description)

        assert button.entity_description.key == key

    async def test_async_press(self, mock_coordinator, button_class, key, service_path):
        """Test async_press calls the correct service."""
        description = ButtonEntityDescription(key=key, name="Test")
        button = button_class(mock_coordinator, description)

        with patch(service_path, new_callable=AsyncMock) as mock_service:
            await button.async_press()

            mock_service.assert_called_once_with(mock_coordinator)
