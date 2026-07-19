"""Tests for the per-platform async_setup_entry functions."""

from unittest.mock import MagicMock

import pytest

from custom_components.komfovent import (
    binary_sensor,
    button,
    climate,
    number,
    select,
    sensor,
    switch,
)
from custom_components.komfovent import (
    datetime as komfovent_datetime,
)
from custom_components.komfovent.coordinator import KomfoventRuntimeData

PLATFORM_MODULES = [
    binary_sensor,
    button,
    climate,
    komfovent_datetime,
    number,
    select,
    sensor,
    switch,
]


@pytest.mark.parametrize(
    "platform",
    PLATFORM_MODULES,
    ids=[module.__name__.rsplit(".", 1)[-1] for module in PLATFORM_MODULES],
)
async def test_platform_setup_reads_runtime_data(
    hass, mock_config_entry, mock_coordinator, platform
):
    """Each platform reads the coordinator from entry.runtime_data and adds entities."""
    mock_config_entry.runtime_data = KomfoventRuntimeData(coordinator=mock_coordinator)
    async_add_entities = MagicMock()

    await platform.async_setup_entry(hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
