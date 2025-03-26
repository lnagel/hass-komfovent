"""Binary sensor platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import DOMAIN

# Status bitmask values
BITMASK_STARTING: Final = 1 << 0  # 1
BITMASK_STOPPING: Final = 1 << 1  # 2
BITMASK_FAN: Final = 1 << 2  # 4
BITMASK_ROTOR: Final = 1 << 3  # 8
BITMASK_HEATING: Final = 1 << 4  # 16
BITMASK_COOLING: Final = 1 << 5  # 32
BITMASK_HEATING_DENIED: Final = 1 << 6  # 64
BITMASK_COOLING_DENIED: Final = 1 << 7  # 128
BITMASK_FLOW_DOWN: Final = 1 << 8  # 256
BITMASK_FREE_HEATING: Final = 1 << 9  # 512
BITMASK_FREE_COOLING: Final = 1 << 10  # 1024
BITMASK_ALARM_F: Final = 1 << 11  # 2048
BITMASK_ALARM_W: Final = 1 << 12  # 4096


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
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_STOPPING,
            entity_description=BinarySensorEntityDescription(
                key="status_stopping",
                name="Status Stopping",
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FAN,
            entity_description=BinarySensorEntityDescription(
                key="status_fan_running",
                name="Status Fan Running",
                device_class=BinarySensorDeviceClass.RUNNING,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_ROTOR,
            entity_description=BinarySensorEntityDescription(
                key="status_rotor_running",
                name="Status Rotor Running",
                device_class=BinarySensorDeviceClass.RUNNING,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_HEATING,
            entity_description=BinarySensorEntityDescription(
                key="status_heating",
                name="Status Heating",
                device_class=BinarySensorDeviceClass.HEAT,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_COOLING,
            entity_description=BinarySensorEntityDescription(
                key="status_cooling",
                name="Status Cooling",
                device_class=BinarySensorDeviceClass.COLD,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_HEATING_DENIED,
            entity_description=BinarySensorEntityDescription(
                key="status_heating_denied",
                name="Status Heating Denied",
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_COOLING_DENIED,
            entity_description=BinarySensorEntityDescription(
                key="status_cooling_denied",
                name="Status Cooling Denied",
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
                device_class=BinarySensorDeviceClass.HEAT,
            ),
        ),
        KomfoventStatusBinarySensor(
            coordinator=coordinator,
            register_id=registers.REG_STATUS,
            bitmask=BITMASK_FREE_COOLING,
            entity_description=BinarySensorEntityDescription(
                key="status_free_cooling",
                name="Status Free Cooling",
                device_class=BinarySensorDeviceClass.COLD,
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
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent binary sensor based on a config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(await create_binary_sensors(coordinator))


class KomfoventBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for Komfovent binary sensors."""

    _attr_has_entity_name = True

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
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": "Komfovent",
            "model": None,
        }

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
