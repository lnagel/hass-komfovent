"""Tests for the Komfovent base coordinator entity."""

from unittest.mock import patch

from homeassistant.components.switch import SwitchEntityDescription

from custom_components.komfovent.switch import KomfoventSwitch

DESC = SwitchEntityDescription(key="test_switch", name="Test")


async def test_added_to_hass_refreshes_state(mock_coordinator):
    """Test state is refreshed from coordinator data when added to hass."""
    mock_coordinator.data = {100: 0}
    s = KomfoventSwitch(mock_coordinator, 100, DESC)
    assert s.is_on is False

    mock_coordinator.data = {100: 1}
    await s.async_added_to_hass()

    assert s.is_on is True
    mock_coordinator.async_add_listener.assert_called_once()


def test_coordinator_update_refreshes_state(mock_coordinator):
    """Test state is refreshed before it is written on coordinator update."""
    mock_coordinator.data = {100: 0}
    s = KomfoventSwitch(mock_coordinator, 100, DESC)
    assert s.is_on is False

    mock_coordinator.data = {100: 1}
    written = []
    with patch.object(
        s, "async_write_ha_state", side_effect=lambda: written.append(s.is_on)
    ):
        s._handle_coordinator_update()

    assert written == [True]
