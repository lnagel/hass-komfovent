"""Climate platform for Komfovent."""
from __future__ import annotations
from typing import Any
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OperationMode,
    REG_OPERATION_MODE,
    REG_POWER,
    REG_NORMAL_SETPOINT,
    REG_AWAY_TEMP,
    REG_INTENSIVE_TEMP,
    REG_BOOST_TEMP,
    REG_KITCHEN_TEMP,
    REG_FIREPLACE_TEMP,
    REG_OVERRIDE_TEMP,
    REG_HOLIDAYS_TEMP,
    REG_AQ_TEMP_SETPOINT,
    REG_ECO_MODE,
    REG_AUTO_MODE,
)
from .coordinator import KomfoventCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Komfovent climate device."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KomfoventClimate(coordinator)])

class KomfoventClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Komfovent climate device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY, HVACMode.HEAT_COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [mode.name.lower() for mode in OperationMode]

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Komfovent Ventilation",
            "manufacturer": "Komfovent",
            "model": "Modbus",
        }
        self._eco_mode = False
        self._auto_mode = False

    async def async_set_eco_mode(self, eco_mode: bool) -> None:
        """Set ECO mode."""
        await self.coordinator.client.write_register(REG_ECO_MODE, 1 if eco_mode else 0)
        self._eco_mode = eco_mode
        await self.coordinator.async_request_refresh()

    async def async_set_auto_mode(self, auto_mode: bool) -> None:
        """Set AUTO mode."""
        await self.coordinator.client.write_register(REG_AUTO_MODE, 1 if auto_mode else 0)
        self._auto_mode = auto_mode
        await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.coordinator.data:
            return float(self.coordinator.data.get("extract_temp", 0)) / 10

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data:
            return None
            
        try:
            mode = OperationMode(self.coordinator.data.get("operation_mode", 0))
            temp_key = MODE_TEMP_MAPPING[mode][0]
            if (temp := self.coordinator.data.get(temp_key)) is not None:
                return float(temp) / 10
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid operation mode or temperature value")
            
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation mode."""
        if self.coordinator.data:
            if not self.coordinator.data.get("power", 0):
                return HVACMode.OFF
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if self.coordinator.data:
            mode = self.coordinator.data.get("operation_mode", 0)
            try:
                return OperationMode(mode).name.lower()
            except ValueError:
                return "unknown"

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        try:
            mode = OperationMode(self.coordinator.data.get("operation_mode", 0))
            reg = MODE_TEMP_MAPPING[mode][1]
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid operation mode, using normal setpoint")
            reg = REG_NORMAL_SETPOINT

        # Temperature values are stored as actual value * 10 in Modbus
        value = int(temp * 10)
        await self.coordinator.client.write_register(reg, value)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.write_register(REG_POWER, 0)
        else:
            await self.coordinator.client.write_register(REG_POWER, 1)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        try:
            mode = OperationMode[preset_mode.upper()]
            await self.coordinator.client.write_register(
                REG_OPERATION_MODE, mode.value
            )
            await self.coordinator.async_request_refresh()
        except ValueError:
            _LOGGER.warning("Invalid preset mode: %s", preset_mode)

