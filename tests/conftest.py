"""Configure pytest for Home Assistant test suite."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant


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
    pass


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
    return hass_obj


@pytest.fixture(
    params=list(Path(__file__).parent.glob("fixtures/*_registers_*.json")),
)
def mock_registers(request):
    json_path = request.param
    with open(json_path) as f:
        return json_path.name, json.load(f)


@pytest.fixture
def mock_modbus_client() -> MagicMock:
    """Create a mock KomfoventModbusClient."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    json_file = Path(__file__).parent / Path("fixtures/C6_registers_0.json")

    with json_file.open() as f:
        register_data = json.load(f)
        transformed_data = {}
        for block_start, values in register_data.items():
            block_start_int = int(block_start)
            for reg, value in enumerate(values, start=block_start_int):
                transformed_data[reg] = value

    # Set up read to return data from our fixture
    async def mock_read(register: int, count: int) -> dict[int, int]:
        result = {}
        for reg in range(register, register + count):
            result[reg] = transformed_data.get(reg, 0)
        return result

    mock_client.read = AsyncMock(side_effect=mock_read)
    mock_client.write = AsyncMock()

    return mock_client
