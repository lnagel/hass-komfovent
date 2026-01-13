"""Tests for Komfovent switch platform."""

from homeassistant.components.switch import SwitchEntityDescription

from custom_components.komfovent import registers
from custom_components.komfovent.const import DOMAIN
from custom_components.komfovent.switch import KomfoventSwitch, create_switches


class TestKomfoventSwitch:
    """Tests for KomfoventSwitch entity."""

    def test_initialization(self, mock_coordinator):
        """Test switch entity initialization."""
        description = SwitchEntityDescription(
            key="test_switch",
            name="Test Switch",
        )
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert switch.register_id == 100
        assert switch.entity_description.key == "test_switch"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = SwitchEntityDescription(key="test_switch", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert switch.unique_id == "test_entry_id_test_switch"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = SwitchEntityDescription(key="test_switch", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        device_info = switch.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"


class TestIsOn:
    """Tests for is_on property."""

    def test_is_on_true(self, mock_coordinator):
        """Test is_on returns True for non-zero value."""
        mock_coordinator.data = {100: 1}
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert switch.is_on is True

    def test_is_on_false(self, mock_coordinator):
        """Test is_on returns False for zero value."""
        mock_coordinator.data = {100: 0}
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert switch.is_on is False

    def test_is_on_no_data(self, mock_coordinator):
        """Test is_on returns None when no data."""
        mock_coordinator.data = None
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert switch.is_on is None

    def test_is_on_missing_register(self, mock_coordinator):
        """Test is_on returns None for missing register."""
        mock_coordinator.data = {}
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert switch.is_on is None


class TestAsyncTurnOn:
    """Tests for async_turn_on method."""

    async def test_turn_on(self, mock_coordinator):
        """Test async_turn_on writes 1 to register."""
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        await switch.async_turn_on()

        mock_coordinator.client.write.assert_called_once_with(100, 1)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_on_power_switch(self, mock_coordinator):
        """Test async_turn_on for power switch."""
        description = SwitchEntityDescription(key="power", name="Power")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        await switch.async_turn_on()

        mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 1)


class TestAsyncTurnOff:
    """Tests for async_turn_off method."""

    async def test_turn_off(self, mock_coordinator):
        """Test async_turn_off writes 0 to register."""
        description = SwitchEntityDescription(key="test", name="Test")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        await switch.async_turn_off()

        mock_coordinator.client.write.assert_called_once_with(100, 0)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_off_power_switch(self, mock_coordinator):
        """Test async_turn_off for power switch."""
        description = SwitchEntityDescription(key="power", name="Power")
        switch = KomfoventSwitch(
            coordinator=mock_coordinator,
            register_id=registers.REG_POWER,
            entity_description=description,
        )

        await switch.async_turn_off()

        mock_coordinator.client.write.assert_called_once_with(registers.REG_POWER, 0)


class TestCreateSwitches:
    """Tests for create_switches factory function."""

    async def test_creates_all_switches(self, mock_coordinator):
        """Test that all switch entities are created."""
        switches = await create_switches(mock_coordinator)

        assert len(switches) == 17

        expected_keys = {
            "power",
            "eco_mode",
            "auto_mode",
            "aq_impurity_control",
            "aq_humidity_control",
            "aq_electric_heater",
            "eco_free_heat_cool",
            "eco_heater_blocking",
            "eco_cooler_blocking",
            "away_electric_heater",
            "normal_electric_heater",
            "intensive_electric_heater",
            "boost_electric_heater",
            "kitchen_electric_heater",
            "fireplace_electric_heater",
            "override_electric_heater",
            "holidays_electric_heater",
        }

        switch_keys = {s.entity_description.key for s in switches}
        assert switch_keys == expected_keys
