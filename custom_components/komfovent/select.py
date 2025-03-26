"""Select platform for Komfovent."""  # noqa: A005

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from enum import IntEnum

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import registers
from .const import (
    DOMAIN,
    AirQualitySensorType,
    FlowControl,
    HeatRecoveryControl,
    MicroVentilation,
    OperationMode,
    OutdoorHumiditySensor,
    OverrideActivation,
    SchedulerMode,
    TemperatureControl,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent select entities."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            KomfoventOperationModeSelect(
                coordinator=coordinator,
                register_id=registers.REG_OPERATION_MODE,
                enum_class=OperationMode,
                entity_description=SelectEntityDescription(
                    key="operation_mode",
                    name="Current mode",
                    options=[mode.name.lower() for mode in OperationMode],
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_SCHEDULER_MODE,
                enum_class=SchedulerMode,
                entity_description=SelectEntityDescription(
                    key="scheduler_mode",
                    name="Scheduler mode",
                    options=[mode.name.lower() for mode in SchedulerMode],
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_TEMP_CONTROL,
                enum_class=TemperatureControl,
                entity_description=SelectEntityDescription(
                    key="temperature_control",
                    name="Temperature control",
                    entity_category=EntityCategory.CONFIG,
                    options=[mode.name.lower() for mode in TemperatureControl],
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_FLOW_CONTROL,
                enum_class=FlowControl,
                entity_description=SelectEntityDescription(
                    key="flow_control",
                    name="Flow control",
                    entity_category=EntityCategory.CONFIG,
                    options=[mode.name.lower() for mode in FlowControl],
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_AQ_SENSOR1_TYPE,
                enum_class=AirQualitySensorType,
                entity_description=SelectEntityDescription(
                    key="aq_sensor1_type",
                    name="AQ Sensor 1 Type",
                    entity_category=EntityCategory.CONFIG,
                    options=[mode.name.lower() for mode in AirQualitySensorType],
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_AQ_SENSOR2_TYPE,
                enum_class=AirQualitySensorType,
                entity_description=SelectEntityDescription(
                    key="aq_sensor2_type",
                    name="AQ Sensor 2 Type",
                    entity_category=EntityCategory.CONFIG,
                    options=[mode.name.lower() for mode in AirQualitySensorType],
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_AQ_OUTDOOR_HUMIDITY,
                enum_class=OutdoorHumiditySensor,
                entity_description=SelectEntityDescription(
                    key="aq_outdoor_humidity_sensor",
                    name="AQ Outdoor Humidity Sensor",
                    entity_category=EntityCategory.CONFIG,
                    icon="mdi:water-percent",
                    options=[mode.name.lower() for mode in OutdoorHumiditySensor],
                    entity_registry_enabled_default=False,
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_ECO_HEAT_RECOVERY,
                enum_class=HeatRecoveryControl,
                entity_description=SelectEntityDescription(
                    key="eco_heat_recovery",
                    name="ECO Heat Recovery",
                    icon="mdi:heat-wave",
                    options=[mode.name.lower() for mode in HeatRecoveryControl],
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_OVERRIDE_ACTIVATION,
                enum_class=OverrideActivation,
                entity_description=SelectEntityDescription(
                    key="override_activation",
                    name="Override Activation",
                    options=[mode.name.lower() for mode in OverrideActivation],
                    entity_registry_enabled_default=True,
                    entity_registry_visible_default=False,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
            KomfoventSelect(
                coordinator=coordinator,
                register_id=registers.REG_HOLIDAYS_MICRO_VENT,
                enum_class=MicroVentilation,
                entity_description=SelectEntityDescription(
                    key="holidays_micro_ventilation",
                    name="Holidays Micro-ventilation",
                    options=[mode.name.lower() for mode in MicroVentilation],
                    entity_registry_enabled_default=True,
                    entity_registry_visible_default=False,
                    entity_category=EntityCategory.CONFIG,
                ),
            ),
        ]
    )


class KomfoventSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Komfovent select entity."""

    _attr_has_entity_name: ClassVar[bool] = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        enum_class: type[IntEnum],
        entity_description: SelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.register_id = register_id
        self.enum_class = enum_class
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": "Komfovent",
            "model": None,
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.coordinator.data:
            return None

        mode = self.coordinator.data.get(self.register_id)
        try:
            return self.enum_class(mode).name.lower()
        except ValueError:
            return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            mode = self.enum_class[option.upper()]
        except ValueError:
            _LOGGER.warning("Invalid operation mode: %s", option)
            return

        await self.coordinator.client.write(self.register_id, mode.value)

        await self.coordinator.async_request_refresh()


class KomfoventOperationModeSelect(KomfoventSelect):
    """Special select entity for operation mode that handles power and auto mode."""

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            mode = self.enum_class[option.upper()]
        except ValueError:
            _LOGGER.warning("Invalid operation mode: %s", option)
            return

        if mode == OperationMode.OFF:
            await self.coordinator.client.write(registers.REG_POWER, 0)
        elif mode == OperationMode.AIR_QUALITY:
            await self.coordinator.client.write(registers.REG_AUTO_MODE, 1)
        elif mode in {
            OperationMode.AWAY,
            OperationMode.NORMAL,
            OperationMode.INTENSIVE,
            OperationMode.BOOST,
        }:
            await self.coordinator.client.write(
                registers.REG_OPERATION_MODE, mode.value
            )
        else:
            _LOGGER.warning("Unsupported operation mode: %s", option)
            return

        await self.coordinator.async_request_refresh()
