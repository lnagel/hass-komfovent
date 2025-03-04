"""Climate platform for Komfovent."""
from __future__ import annotations
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OPERATION_MODES,
    REG_OPERATION_MODE,
    REG_POWER,
    REG_NORMAL_SETPOINT,
    REG_AWAY_TEMP,
    REG_INTENSIVE_TEMP,
    REG_BOOST_TEMP,
    REG_KITCHEN_TEMP,
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
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY, HVACMode.HEAT_COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )
    _attr_fan_modes = ["away", "normal", "intensive", "boost"]
    _attr_preset_modes = list(OPERATION_MODES.values())

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": "Komfovent Ventilation",
            "manufacturer": "Komfovent",
            "model": "Modbus",
        }
        self._eco_mode = False
        self._auto_mode = False

    async def async_set_eco_mode(self, eco_mode: bool) -> None:
        """Set ECO mode."""
        await self.coordinator.hub.async_write_register(REG_ECO_MODE, 1 if eco_mode else 0)
        self._eco_mode = eco_mode
        await self.coordinator.async_request_refresh()

    async def async_set_auto_mode(self, auto_mode: bool) -> None:
        """Set AUTO mode."""
        await self.coordinator.hub.async_write_register(REG_AUTO_MODE, 1 if auto_mode else 0)
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
        if self.coordinator.data:
            mode = self.coordinator.data.get("operation_mode", 0)
            if mode == 1:  # Away
                return float(self.coordinator.data.get("away_temp", 0)) / 10
            elif mode == 2:  # Normal
                return float(self.coordinator.data.get("normal_temp", 0)) / 10
            elif mode == 3:  # Intensive
                return float(self.coordinator.data.get("intensive_temp", 0)) / 10
            elif mode == 4:  # Boost
                return float(self.coordinator.data.get("boost_temp", 0)) / 10
            elif mode == 5:  # Kitchen
                return float(self.coordinator.data.get("kitchen_temp", 0)) / 10
            return float(self.coordinator.data.get("normal_temp", 0)) / 10

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
            return OPERATION_MODES.get(mode, "Unknown")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        mode = self.coordinator.data.get("operation_mode", 0)
        reg = REG_NORMAL_SETPOINT  # Default to normal mode
        
        if mode == 1:  # Away
            reg = REG_AWAY_TEMP
        elif mode == 2:  # Normal
            reg = REG_NORMAL_SETPOINT
        elif mode == 3:  # Intensive
            reg = REG_INTENSIVE_TEMP
        elif mode == 4:  # Boost
            reg = REG_BOOST_TEMP
        elif mode == 5:  # Kitchen
            reg = REG_KITCHEN_TEMP

        # Temperature values are stored as actual value * 10 in Modbus
        value = int(temp * 10)
        await self.coordinator.hub.async_write_register(reg, value)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.hub.async_write_register(REG_POWER, 0)
        else:
            await self.coordinator.hub.async_write_register(REG_POWER, 1)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        for mode_num, mode_name in OPERATION_MODES.items():
            if mode_name == preset_mode:
                await self.coordinator.hub.async_write_register(
                    REG_OPERATION_MODE, mode_num
                )
                break
        await self.coordinator.async_request_refresh()

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        if self.coordinator.data:
            mode = self.coordinator.data.get("operation_mode", 0)
            if mode == 1:
                return "away"
            elif mode == 2:
                return "normal"
            elif mode == 3:
                return "intensive"
            elif mode == 4:
                return "boost"
        return "normal"

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        mode_map = {
            "away": 1,
            "normal": 2,
            "intensive": 3,
            "boost": 4
        }
        if fan_mode in mode_map:
            await self.coordinator.hub.async_write_register(
                REG_OPERATION_MODE, mode_map[fan_mode]
            )
            await self.coordinator.async_request_refresh()
