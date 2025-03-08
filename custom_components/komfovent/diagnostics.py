"""Diagnostics support for Komfovent."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

from modbus_dump import dump_registers

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import KomfoventCoordinator

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    registers = await dump_registers(host, port)

    return {
        "config_entry": entry.as_dict(),
        "registers": registers,
    }
