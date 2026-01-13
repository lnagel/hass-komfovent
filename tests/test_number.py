"""Tests for Komfovent number platform."""

from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfVolumeFlowRate

from custom_components.komfovent import registers
from custom_components.komfovent.const import (
    DOMAIN,
    Controller,
    FlowControl,
    FlowUnit,
)
from custom_components.komfovent.number import (
    FlowNumber,
    KomfoventNumber,
    TemperatureNumber,
)


class TestKomfoventNumber:
    """Tests for base KomfoventNumber entity."""

    def test_initialization(self, mock_coordinator):
        """Test number entity initialization."""
        description = NumberEntityDescription(
            key="test_number",
            name="Test Number",
        )
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.register_id == 100
        assert number.entity_description.key == "test_number"

    def test_unique_id(self, mock_coordinator):
        """Test unique_id generation."""
        description = NumberEntityDescription(key="test_number", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.unique_id == "test_entry_id_test_number"

    def test_device_info(self, mock_coordinator):
        """Test device_info property."""
        description = NumberEntityDescription(key="test_number", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        device_info = number.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_id")}
        assert device_info["name"] == "Komfovent"
        assert device_info["manufacturer"] == "Komfovent"

    def test_native_value_with_data(self, mock_coordinator):
        """Test native_value returns register value as float."""
        mock_coordinator.data = {100: 42}
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_value == 42.0

    def test_native_value_no_data(self, mock_coordinator):
        """Test native_value returns None when no data."""
        mock_coordinator.data = None
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_value is None

    def test_native_value_missing_register(self, mock_coordinator):
        """Test native_value returns None for missing register."""
        mock_coordinator.data = {}
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_value is None

    def test_native_value_invalid_type(self, mock_coordinator):
        """Test native_value returns None for invalid type."""
        mock_coordinator.data = {100: "not a number"}
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_value is None

    async def test_async_set_native_value(self, mock_coordinator):
        """Test async_set_native_value writes to register."""
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        await number.async_set_native_value(50.0)

        mock_coordinator.client.write.assert_called_once_with(100, 50)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_set_native_value_converts_to_int(self, mock_coordinator):
        """Test async_set_native_value converts float to int."""
        description = NumberEntityDescription(key="test", name="Test")
        number = KomfoventNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        await number.async_set_native_value(42.7)

        mock_coordinator.client.write.assert_called_once_with(100, 42)


class TestTemperatureNumber:
    """Tests for TemperatureNumber with x10 scaling."""

    def test_native_value_divides_by_10(self, mock_coordinator):
        """Test native_value divides register value by 10."""
        mock_coordinator.data = {100: 215}  # 21.5°C
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_value == 21.5

    def test_native_value_none(self, mock_coordinator):
        """Test native_value returns None when parent returns None."""
        mock_coordinator.data = None
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_value is None

    async def test_async_set_native_value_multiplies_by_10(self, mock_coordinator):
        """Test async_set_native_value multiplies value by 10."""
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        await number.async_set_native_value(21.5)

        mock_coordinator.client.write.assert_called_once_with(100, 215)
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_set_native_value_at_boundaries(self, mock_coordinator):
        """Test async_set_native_value at temperature boundaries."""
        description = NumberEntityDescription(key="test", name="Test")
        number = TemperatureNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        # Test minimum (5°C)
        await number.async_set_native_value(5.0)
        mock_coordinator.client.write.assert_called_with(100, 50)

        mock_coordinator.client.write.reset_mock()

        # Test maximum (40°C)
        await number.async_set_native_value(40.0)
        mock_coordinator.client.write.assert_called_with(100, 400)


class TestFlowNumber:
    """Tests for FlowNumber with dynamic units."""

    def test_c6_flow_control_off(self, mock_coordinator):
        """Test C6 with flow control off returns percentage."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.OFF,
        }
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_unit_of_measurement == PERCENTAGE

    def test_c6_flow_unit_m3h(self, mock_coordinator):
        """Test C6 with m³/h flow unit."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.CONSTANT,
            registers.REG_FLOW_UNIT: FlowUnit.M3H,
        }
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert (
            number.native_unit_of_measurement
            == UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        )

    def test_c6_flow_unit_ls(self, mock_coordinator):
        """Test C6 with l/s flow unit."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.VARIABLE,
            registers.REG_FLOW_UNIT: FlowUnit.LS,
        }
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert (
            number.native_unit_of_measurement == UnitOfVolumeFlowRate.LITERS_PER_SECOND
        )

    def test_c6m_flow_unit(self, mock_coordinator):
        """Test C6M with flow unit."""
        mock_coordinator.controller = Controller.C6M
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.DIRECT,
            registers.REG_FLOW_UNIT: FlowUnit.M3H,
        }
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert (
            number.native_unit_of_measurement
            == UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        )

    def test_c8_returns_percentage(self, mock_coordinator):
        """Test C8 always returns percentage."""
        mock_coordinator.controller = Controller.C8
        mock_coordinator.data = {100: 50}  # Need some data to pass falsy check
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_unit_of_measurement == PERCENTAGE

    def test_no_data(self, mock_coordinator):
        """Test returns None when no data."""
        mock_coordinator.data = None
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_unit_of_measurement is None

    def test_unknown_flow_unit(self, mock_coordinator):
        """Test returns None for unknown flow unit."""
        mock_coordinator.controller = Controller.C6
        mock_coordinator.data = {
            registers.REG_FLOW_CONTROL: FlowControl.CONSTANT,
            registers.REG_FLOW_UNIT: 99,  # Invalid
        }
        description = NumberEntityDescription(key="test", name="Test")
        number = FlowNumber(
            coordinator=mock_coordinator,
            register_id=100,
            entity_description=description,
        )

        assert number.native_unit_of_measurement is None
