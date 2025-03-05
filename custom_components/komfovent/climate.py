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
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OperationMode,
    MODE_TEMP_MAPPING,
    TEMP_CONTROL_MAPPING,
    TemperatureControl,
)
from . import registers
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
        | ClimateEntityFeature.TURN_ECO_ON
        | ClimateEntityFeature.TURN_AUTO_ON
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

    async def async_turn_eco_on(self) -> None:
        """Turn on eco mode."""
        await self.coordinator.client.write_register(registers.REG_ECO_MODE, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_eco_off(self) -> None:
        """Turn off eco mode."""
        await self.coordinator.client.write_register(registers.REG_ECO_MODE, 0)
        await self.coordinator.async_request_refresh()

    async def async_turn_auto_on(self) -> None:
        """Turn on auto mode."""
        await self.coordinator.client.write_register(registers.REG_AUTO_MODE, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_auto_off(self) -> None:
        """Turn off auto mode."""
        await self.coordinator.client.write_register(registers.REG_AUTO_MODE, 0)
        await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None
            
        try:
            temp_control = TemperatureControl(self.coordinator.data.get(registers.REG_TEMP_CONTROL, TemperatureControl.SUPPLY))
            temp_key = TEMP_CONTROL_MAPPING[temp_control]
            
            if (temp := self.coordinator.data.get(temp_key)) is not None:
                return float(temp) / 10
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid temperature control mode")
            
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data:
            return None
            
        try:
            mode = OperationMode(self.coordinator.data.get(registers.REG_OPERATION_MODE, 0))
            temp_reg = MODE_TEMP_MAPPING[mode]
            if (temp := self.coordinator.data.get(temp_reg)) is not None:
                return float(temp) / 10
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid operation mode or temperature value")
            
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation mode."""
        if not self.coordinator.data:
            return HVACMode.OFF
            
        power = self.coordinator.data.get(registers.REG_POWER, 0)
        operation_mode = self.coordinator.data.get(registers.REG_OPERATION_MODE, OperationMode.OFF)
        
        if not power or operation_mode == OperationMode.OFF:
            return HVACMode.OFF
        return HVACMode.HEAT_COOL

    @property
    def is_eco_mode(self) -> bool:
        """Return if ECO mode is active."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get(registers.REG_ECO_MODE, 0))

    @property
    def is_auto_mode(self) -> bool:
        """Return if AUTO mode is active."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get(registers.REG_AUTO_MODE, 0))

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if self.coordinator.data:
            mode = self.coordinator.data.get(registers.REG_OPERATION_MODE, 0)
            try:
                return OperationMode(mode).name.lower()
            except ValueError:
                return "unknown"

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        try:
            mode = OperationMode(self.coordinator.data.get(registers.REG_OPERATION_MODE, 0))
            reg = MODE_TEMP_MAPPING[mode]
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid operation mode, using normal setpoint")
            reg = registers.REG_NORMAL_SETPOINT

        # Temperature values are stored as actual value * 10 in Modbus
        value = int(temp * 10)
        await self.coordinator.client.write_register(reg, value)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.write_register(registers.REG_POWER, 0)
        else:
            await self.coordinator.client.write_register(registers.REG_POWER, 1)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        try:
            mode = OperationMode[preset_mode.upper()]
            await self.coordinator.client.write_register(
                registers.REG_OPERATION_MODE, mode.value
            )
            await self.coordinator.async_request_refresh()
        except ValueError:
            _LOGGER.warning("Invalid preset mode: %s", preset_mode)

