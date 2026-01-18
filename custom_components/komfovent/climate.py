"""Climate platform for Komfovent."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Final

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers, services
from .binary_sensor import (
    BITMASK_COOLING,
    BITMASK_FAN,
    BITMASK_HEATING,
)
from .const import (
    DOMAIN,
    OperationMode,
    TemperatureControl,
)
from .helpers import build_device_info

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)

SETPOINT_MIN_TEMP: Final = 5  # Minimum temperature supported by device (raw value 50)
SETPOINT_MAX_TEMP: Final = 40  # Maximum temperature supported by device (raw value 400)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Komfovent climate device."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KomfoventClimate(coordinator)])


class KomfoventClimate(CoordinatorEntity["KomfoventCoordinator"], ClimateEntity):
    """Representation of a Komfovent climate device."""

    _attr_has_entity_name: ClassVar[bool] = True
    _attr_name: ClassVar[None] = None
    _attr_temperature_unit: ClassVar[str] = UnitOfTemperature.CELSIUS
    _attr_hvac_modes: ClassVar[list[str]] = [HVACMode.OFF, HVACMode.HEAT_COOL]
    _attr_supported_features: ClassVar[int] = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes: ClassVar[list[str]] = [
        mode.name.lower() for mode in OperationMode
    ]
    _attr_translation_key = "komfovent_climate"
    coordinator: KomfoventCoordinator

    def __init__(self, coordinator: KomfoventCoordinator) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate"
        self._attr_device_info = build_device_info(coordinator)
        self._eco_mode = False
        self._auto_mode = False

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None

        try:
            temp_control = TemperatureControl(
                self.coordinator.data.get(registers.REG_TEMP_CONTROL)
            )
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
            mode = OperationMode(
                self.coordinator.data.get(registers.REG_OPERATION_MODE)
            )
            temp_reg = MODE_TEMP_MAPPING[mode]
            if (temp := self.coordinator.data.get(temp_reg)) is not None:
                return float(temp) / 10
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid operation mode or temperature value")

        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation mode."""
        if not self.coordinator.data:
            return None

        power = self.coordinator.data.get(registers.REG_POWER)

        if power is None:
            return None

        if power:
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:  # noqa: PLR0911
        """Return the current HVAC action."""
        if not self.coordinator.data:
            return None

        power = self.coordinator.data.get(registers.REG_POWER)
        status = self.coordinator.data.get(registers.REG_STATUS)

        # Return None if either power or status is missing, or if device is off
        if power is None or status is None:
            return None
        if power == 0:
            return HVACAction.OFF

        # Check status bits for active operations (priority: heating > cooling > fan)
        if status & BITMASK_HEATING:
            return HVACAction.HEATING
        if status & BITMASK_COOLING:
            return HVACAction.COOLING
        if status & BITMASK_FAN:
            return HVACAction.FAN

        # Device is on but not actively doing anything
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if not self.coordinator.data:
            return None

        mode = self.coordinator.data.get(registers.REG_OPERATION_MODE)
        try:
            return OperationMode(mode).name.lower()
        except ValueError:
            return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # Get current mode and its temperature register
        try:
            mode = OperationMode(
                self.coordinator.data.get(registers.REG_OPERATION_MODE)
            )
            reg = MODE_TEMP_MAPPING[mode]
        except (ValueError, KeyError):
            _LOGGER.warning("Invalid operation mode, using normal setpoint")
            reg = registers.REG_NORMAL_SETPOINT

        # Convert temperature to device format (x10)
        # Ensure the value is within reasonable bounds
        if SETPOINT_MIN_TEMP <= temp <= SETPOINT_MAX_TEMP:
            value = int(temp * 10)
            try:
                await self.coordinator.client.write(reg, value)
                await self.coordinator.async_request_refresh()
            except (ConnectionError, TimeoutError):
                _LOGGER.exception("Failed to set temperature")
        else:
            _LOGGER.warning(
                "Temperature %.1f°C out of bounds (%d-%d°C, raw values %d-%d)",
                temp,
                SETPOINT_MIN_TEMP,
                SETPOINT_MAX_TEMP,
                SETPOINT_MIN_TEMP * 10,
                SETPOINT_MAX_TEMP * 10,
            )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.write(registers.REG_POWER, 0)
        else:
            await self.coordinator.client.write(registers.REG_POWER, 1)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await services.set_operation_mode(self.coordinator, preset_mode)


MODE_TEMP_MAPPING = {
    OperationMode.STANDBY: registers.REG_NORMAL_SETPOINT,  # Use normal temp for standby
    OperationMode.AWAY: registers.REG_AWAY_TEMP,
    OperationMode.NORMAL: registers.REG_NORMAL_SETPOINT,
    OperationMode.INTENSIVE: registers.REG_INTENSIVE_TEMP,
    OperationMode.BOOST: registers.REG_BOOST_TEMP,
    OperationMode.KITCHEN: registers.REG_KITCHEN_TEMP,
    OperationMode.FIREPLACE: registers.REG_FIREPLACE_TEMP,
    OperationMode.OVERRIDE: registers.REG_OVERRIDE_TEMP,
    OperationMode.HOLIDAY: registers.REG_HOLIDAYS_TEMP,
    OperationMode.AIR_QUALITY: registers.REG_AQ_TEMP_SETPOINT,
    OperationMode.OFF: registers.REG_NORMAL_SETPOINT,  # Use normal temp when off
}
TEMP_CONTROL_MAPPING = {
    TemperatureControl.SUPPLY: registers.REG_SUPPLY_TEMP,
    TemperatureControl.EXTRACT: registers.REG_EXTRACT_TEMP,
    # Using panel1 temp for room temperature
    TemperatureControl.ROOM: registers.REG_PANEL1_TEMP,
    # Using extract temp for balance mode
    TemperatureControl.BALANCE: registers.REG_EXTRACT_TEMP,
}
