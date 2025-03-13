"""Configure pytest for Home Assistant test suite."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant


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
            for i, value in enumerate(values):
                transformed_data[block_start_int + i + 1] = value

    # Set up read_holding_registers to return data from our fixture
    async def mock_read_registers(address: int, count: int) -> dict[int, int]:
        result = {}
        for reg in range(address, address + count):
            result[reg] = transformed_data.get(reg, 0)
        return result

    mock_client.read_holding_registers = AsyncMock(side_effect=mock_read_registers)
    mock_client.write_register = AsyncMock()

    return mock_client
