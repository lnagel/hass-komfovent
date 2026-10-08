"""Binary sensor platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventConfigEntry, KomfoventCoordinator

from . import registers
from .const import (
    BITMASK_ALARM_F,
    BITMASK_ALARM_W,
    BITMASK_COOLING,
    BITMASK_COOLING_DENIED,
    BITMASK_FAN,
    BITMASK_FLOW_DOWN,
    BITMASK_FREE_COOLING,
    BITMASK_FREE_HEATING,
    BITMASK_HEATING,
    BITMASK_HEATING_DENIED,
    BITMASK_ROTOR,
    BITMASK_STARTING,
    BITMASK_STOPPING,
)
from .helpers import build_device_info


async def create_binary_sensors(
    coordinator: KomfoventCoordinator,
) -> list[KomfoventBinarySensor]:
    """Get list of binary sensor entities."""
    return [
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_STARTING,
            entity_description=BinarySensorEntityDescription(
                key="status_starting",
                name="Status Starting",
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_STOPPING,
            entity_description=BinarySensorEntityDescription(
                key="status_stopping",
                name="Status Stopping",
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FAN,
            entity_description=BinarySensorEntityDescription(
                key="status_fan",
                name="Status Fan",
                device_class=BinarySensorDeviceClass.RUNNING,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_ROTOR,
            entity_description=BinarySensorEntityDescription(
                key="status_rotor",
                name="Status Rotor",
                device_class=BinarySensorDeviceClass.RUNNING,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_HEATING,
            entity_description=BinarySensorEntityDescription(
                key="status_heating",
                name="Status Heating",
                device_class=BinarySensorDeviceClass.RUNNING,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_COOLING,
            entity_description=BinarySensorEntityDescription(
                key="status_cooling",
                name="Status Cooling",
                device_class=BinarySensorDeviceClass.RUNNING,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_HEATING_DENIED,
            entity_description=BinarySensorEntityDescription(
                key="status_heating_denied",
                name="Status Heating Denied",
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_COOLING_DENIED,
            entity_description=BinarySensorEntityDescription(
                key="status_cooling_denied",
                name="Status Cooling Denied",
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FLOW_DOWN,
            entity_description=BinarySensorEntityDescription(
                key="status_flow_down",
                name="Status Flow Down",
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FREE_HEATING,
            entity_description=BinarySensorEntityDescription(
                key="status_free_heating",
                name="Status Free Heating",
                device_class=BinarySensorDeviceClass.RUNNING,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FREE_COOLING,
            entity_description=BinarySensorEntityDescription(
                key="status_free_cooling",
                name="Status Free Cooling",
                device_class=BinarySensorDeviceClass.RUNNING,
                entity_registry_enabled_default=False,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_ALARM_F,
            entity_description=BinarySensorEntityDescription(
                key="status_alarm_fault",
                name="Status Alarm Fault",
                device_class=BinarySensorDeviceClass.PROBLEM,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_ALARM_W,
            entity_description=BinarySensorEntityDescription(
                key="status_alarm_warning",
                name="Status Alarm Warning",
                device_class=BinarySensorDeviceClass.PROBLEM,
            ),
        ),
    ]


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: KomfoventConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent binary sensor based on a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(await create_binary_sensors(coordinator))


class KomfoventBinarySensor(
    CoordinatorEntity["KomfoventCoordinator"], BinarySensorEntity
):
    """Base class for Komfovent binary sensors."""

    _attr_has_entity_name = True
    coordinator: KomfoventCoordinator

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.register_id = register_id
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )
        self._attr_translation_key = entity_description.key
        self._attr_device_info = build_device_info(coordinator)

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self.register_id)
        if value is None:
            return None
        return bool(value)


class KomfoventStatusBinarySensor(KomfoventBinarySensor):
    """Binary sensor for status register bitmask values."""

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        bitmask: int,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, register_id, entity_description)
        self.bitmask = bitmask

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self.register_id)
        if value is None:
            return None
        return bool(value & self.bitmask)
