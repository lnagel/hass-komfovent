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

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN
from .coordinator import KomfoventCoordinator
from .services import async_register_services

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.DATETIME,
    Platform.NUMBER,
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
    "4": "operation_mode",
    "5": "scheduler_mode",
    "10": "temperature_control",
    "11": "flow_control",
    "212": "aq_sensor1_type",
    "213": "aq_sensor2_type",
    "901": "supply_temperature",
    "902": "extract_temperature",
    "903": "outdoor_temperature",
    "909": "supply_fan",
    "910": "extract_fan",
    "911": "heat_exchanger",
    "912": "electric_heater",
    "916": "filter_impurity",
    "918": "supply_pressure",
    "919": "extract_pressure",
    "920": "power_consumption",
    "921": "heater_power",
    "922": "heat_recovery",
    "923": "heat_exchanger_efficiency",
    "925": "specific_power_input",
    "930": "total_ahu_energy",
    "936": "total_heater_energy",
    "942": "total_recovered_energy",
    "945": "panel_1_temperature",
    "946": "panel_1_humidity",
    "948": "panel_2_temperature",
    "949": "panel_2_humidity",
    "953": "connected_panels",
    "954": "heat_exchanger_type",
    "955": "indoor_absolute_humidity",
    "999": "controller_firmware",
    "1001": "panel_1_firmware",
    "1003": "panel_2_firmware",
    "supply_fan_intensity": "supply_fan",
    "extract_fan_intensity": "extract_fan",
    "filter_impurity": "filter_clogging",
    "air_quality_co2": "extract_co2",
    "air_quality_voc": "extract_voc",
    "air_quality_rh": "extract_humidity",
    "eco_free_cooling": "eco_free_heat_cool",
    "current_mode": "operation_mode",
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
