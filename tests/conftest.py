"""Configure pytest for Home Assistant test suite."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.komfovent.const import DOMAIN, Controller
from custom_components.komfovent.modbus import convert_register_block
from custom_components.komfovent.registers import (
    REGISTERS_16BIT_SIGNED,
    REGISTERS_16BIT_UNSIGNED,
    REGISTERS_32BIT_UNSIGNED,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_CLASSIFIED_REGISTERS = (
    REGISTERS_16BIT_UNSIGNED
    | REGISTERS_16BIT_SIGNED
    | REGISTERS_32BIT_UNSIGNED
    # high-word slots needed by convert_register_block for 32-bit combine
    | {reg + 1 for reg in REGISTERS_32BIT_UNSIGNED}
)


def load_register_fixture(fixture_name: str) -> dict[int, int]:
    """
    Load a JSON fixture file and transform to register dict format.

    Fixture files store raw uint16 wire data as exported by the
    diagnostics dump. Production stores the post-conversion view
    (signed temps, combined 32-bit values), so we apply the same
    conversion here to match.

    Args:
        fixture_name: Name of the fixture file (e.g., "C6_registers_0.json")

    Returns:
        Dictionary mapping register addresses to their values.

    """
    json_path = FIXTURES_DIR / fixture_name
    with json_path.open() as f:
        register_data = json.load(f)

    raw = {
        reg: value
        for block_start, values in register_data.items()
        for reg, value in enumerate(values, start=int(block_start))
        if reg in _CLASSIFIED_REGISTERS
    }
    return convert_register_block(raw)


def get_controller_from_fixture_name(fixture_name: str) -> Controller:
    """Determine controller type from fixture filename."""
    if fixture_name.startswith("C6M"):
        return Controller.C6M
    if fixture_name.startswith("C8"):
        return Controller.C8
    return Controller.C6


@pytest.fixture
def socket_enabled(request):
    """Enable socket for tests marked with enable_socket marker."""
    if request.node.get_closest_marker("enable_socket"):
        import pytest_socket

        pytest_socket.enable_socket()
        yield
        pytest_socket.disable_socket(allow_unix_socket=True)
    else:
        yield


@pytest.fixture(autouse=True)
def auto_enable_socket(socket_enabled):
    """Automatically apply socket_enabled fixture to all tests."""


@pytest.fixture
def hass() -> HomeAssistant:
    """Create a Home Assistant instance for testing."""
    hass_obj = MagicMock(spec=HomeAssistant)
    hass_obj.data = {}
    hass_obj.states = MagicMock()
    hass_obj.config_entries = MagicMock()
    hass_obj.bus = MagicMock()
    hass_obj.bus.async_fire = AsyncMock()
    hass_obj.async_block_till_done = AsyncMock()
    hass_obj.config = MagicMock()
    hass_obj.config.time_zone = "UTC"
    hass_obj.services = MagicMock()
    hass_obj.services.async_register = MagicMock()
    return hass_obj


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Komfovent",
        data={"host": "192.168.1.100", "port": 502},
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_coordinator(hass, mock_config_entry):
    """Create a mock KomfoventCoordinator with C6 register data."""
    from custom_components.komfovent.coordinator import KomfoventCoordinator

    coordinator = MagicMock(spec=KomfoventCoordinator)
    coordinator.hass = hass
    coordinator.config_entry = mock_config_entry
    coordinator.data = load_register_fixture("C6_registers_0.json")
    coordinator.controller = Controller.C6
    coordinator.func_version = 67

    # Mock the client
    coordinator.client = MagicMock()
    coordinator.client.write = AsyncMock()
    coordinator.client.read = AsyncMock()

    # Mock async_request_refresh
    coordinator.async_request_refresh = AsyncMock()

    return coordinator


@pytest.fixture(
    params=[
        ("C6_registers_0.json", Controller.C6),
        ("C6M_registers_0.json", Controller.C6M),
        ("C8_registers_0K01AJ.json", Controller.C8),
    ],
    ids=["C6", "C6M", "C8"],
)
def mock_coordinator_by_controller(request, hass, mock_config_entry):
    """Create a mock coordinator parametrized by controller type."""
    from custom_components.komfovent.coordinator import KomfoventCoordinator

    fixture_name, controller = request.param

    coordinator = MagicMock(spec=KomfoventCoordinator)
    coordinator.hass = hass
    coordinator.config_entry = mock_config_entry
    coordinator.data = load_register_fixture(fixture_name)
    coordinator.controller = controller
    coordinator.func_version = 67

    # Mock the client
    coordinator.client = MagicMock()
    coordinator.client.write = AsyncMock()
    coordinator.client.read = AsyncMock()

    # Mock async_request_refresh
    coordinator.async_request_refresh = AsyncMock()

    return coordinator


@pytest.fixture(
    params=list(Path(__file__).parent.glob("fixtures/*_registers_*.json")),
)
def mock_registers(request):
    json_path = request.param
    with json_path.open() as f:
        return json_path.name, json.load(f)


@pytest.fixture
def mock_modbus_client() -> MagicMock:
    """Create a mock KomfoventModbusClient."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    transformed_data = load_register_fixture("C6_registers_0.json")

    # Set up read to return data from our fixture, mirroring
    # KomfoventModbusClient.read which only returns converted registers
    # within the requested window.
    async def mock_read(register: int, count: int) -> dict[int, int]:
        return {
            reg: value
            for reg, value in transformed_data.items()
            if register <= reg < register + count
        }

    mock_client.read = AsyncMock(side_effect=mock_read)
    mock_client.write = AsyncMock()

    return mock_client
