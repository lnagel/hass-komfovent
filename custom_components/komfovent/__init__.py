"""The Komfovent integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    entity_registry as er,
)

from . import registers
from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN
from .coordinator import KomfoventCoordinator
from .services import async_register_services

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

ENTITY_ID_MIGRATIONS = {
    str(registers.REG_SUPPLY_TEMP): "supply_temperature",
    str(registers.REG_EXTRACT_TEMP): "extract_temperature",
    str(registers.REG_OUTDOOR_TEMP): "outdoor_temperature",
    str(registers.REG_SUPPLY_FAN_INTENSITY): "supply_fan_intensity",
    str(registers.REG_EXTRACT_FAN_INTENSITY): "extract_fan_intensity",
    str(registers.REG_HEAT_EXCHANGER): "heat_exchanger",
    str(registers.REG_ELECTRIC_HEATER): "electric_heater",
    str(registers.REG_FILTER_IMPURITY): "filter_impurity",
    str(registers.REG_SUPPLY_PRESSURE): "supply_pressure",
    str(registers.REG_EXTRACT_PRESSURE): "extract_pressure",
    str(registers.REG_POWER_CONSUMPTION): "power_consumption",
    str(registers.REG_HEATER_POWER): "heater_power",
    str(registers.REG_HEAT_RECOVERY): "heat_recovery",
    str(registers.REG_HEAT_EFFICIENCY): "heat_exchanger_efficiency",
    str(registers.REG_SPI): "specific_power_input",
    str(registers.REG_INDOOR_ABS_HUMIDITY): "indoor_absolute_humidity",
    str(registers.REG_CONNECTED_PANELS): "connected_panels",
    str(registers.REG_HEAT_EXCHANGER_TYPE): "heat_exchanger_type",
    str(registers.REG_AHU_TOTAL): "total_ahu_energy",
    str(registers.REG_HEATER_TOTAL): "total_heater_energy",
    str(registers.REG_RECOVERY_TOTAL): "total_recovered_energy",
    str(registers.REG_FIRMWARE): "controller_firmware",
    str(registers.REG_PANEL1_TEMP): "panel_1_temperature",
    str(registers.REG_PANEL1_RH): "panel_1_humidity",
    str(registers.REG_PANEL1_FW): "panel_1_firmware",
    str(registers.REG_PANEL2_TEMP): "panel_2_temperature",
    str(registers.REG_PANEL2_RH): "panel_2_humidity",
    str(registers.REG_PANEL2_FW): "panel_2_firmware",
    str(registers.REG_OPERATION_MODE): "operation_mode",
    str(registers.REG_SCHEDULER_MODE): "scheduler_mode",
    str(registers.REG_TEMP_CONTROL): "temperature_control",
    str(registers.REG_FLOW_CONTROL): "flow_control",
    str(registers.REG_AQ_SENSOR1_TYPE): "aq_sensor1_type",
    str(registers.REG_AQ_SENSOR2_TYPE): "aq_sensor2_type",
}


async def _async_migrate_unique_ids(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    _coordinator: KomfoventCoordinator,
) -> None:
    entity_registry = er.async_get(hass)
    for entity_id, registry_entry in entity_registry.entities.items():
        if registry_entry.config_entry_id != config_entry.entry_id:
            continue

        entity_unique_id = registry_entry.unique_id
        short_id = entity_unique_id.removeprefix(f"{config_entry.entry_id}_")

        if short_id in ENTITY_ID_MIGRATIONS:
            new_unique_id = f"{config_entry.entry_id}_{ENTITY_ID_MIGRATIONS[short_id]}"
            _LOGGER.debug(
                "Migrating unique_id from [%s] to [%s]",
                entity_unique_id,
                new_unique_id,
            )
            entity_registry.async_update_entity(entity_id, new_unique_id=new_unique_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Komfovent from a config entry."""
    coordinator = KomfoventCoordinator(
        hass, entry.data[CONF_HOST], entry.data[CONF_PORT]
    )

    connected = await coordinator.connect()
    connection_error = "Failed to connect to Komfovent device"
    if not connected:
        raise ConfigEntryNotReady(connection_error)

    await coordinator.async_config_entry_first_refresh()
    await _async_migrate_unique_ids(hass, entry, coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
