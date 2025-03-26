"""Binary sensor platform for Komfovent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import DOMAIN


@dataclass
class KomfoventBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing Komfovent binary sensor entities."""

    bitmask: int | None = None


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

STATUS_SENSORS: tuple[KomfoventBinarySensorEntityDescription, ...] = (
    KomfoventBinarySensorEntityDescription(
        key="starting",
        name="Starting",
        bitmask=BITMASK_STARTING,
    ),
    KomfoventBinarySensorEntityDescription(
        key="stopping",
        name="Stopping",
        bitmask=BITMASK_STOPPING,
    ),
    KomfoventBinarySensorEntityDescription(
        key="fan_running",
        name="Fan Running",
        bitmask=BITMASK_FAN,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    KomfoventBinarySensorEntityDescription(
        key="rotor_running",
        name="Rotor Running",
        bitmask=BITMASK_ROTOR,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    KomfoventBinarySensorEntityDescription(
        key="heating",
        name="Heating",
        bitmask=BITMASK_HEATING,
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    KomfoventBinarySensorEntityDescription(
        key="cooling",
        name="Cooling",
        bitmask=BITMASK_COOLING,
        device_class=BinarySensorDeviceClass.COLD,
    ),
    KomfoventBinarySensorEntityDescription(
        key="heating_denied",
        name="Heating Denied",
        bitmask=BITMASK_HEATING_DENIED,
    ),
    KomfoventBinarySensorEntityDescription(
        key="cooling_denied",
        name="Cooling Denied",
        bitmask=BITMASK_COOLING_DENIED,
    ),
    KomfoventBinarySensorEntityDescription(
        key="flow_down",
        name="Flow Down",
        bitmask=BITMASK_FLOW_DOWN,
    ),
    KomfoventBinarySensorEntityDescription(
        key="free_heating",
        name="Free Heating",
        bitmask=BITMASK_FREE_HEATING,
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    KomfoventBinarySensorEntityDescription(
        key="free_cooling",
        name="Free Cooling",
        bitmask=BITMASK_FREE_COOLING,
        device_class=BinarySensorDeviceClass.COLD,
    ),
    KomfoventBinarySensorEntityDescription(
        key="alarm_fault",
        name="Alarm Fault",
        bitmask=BITMASK_ALARM_F,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    KomfoventBinarySensorEntityDescription(
        key="alarm_warning",
        name="Alarm Warning",
        bitmask=BITMASK_ALARM_W,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent binary sensor based on a config entry."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[KomfoventBinarySensor] = []

    # Add status binary sensors
    entities.extend(
        KomfoventStatusBinarySensor(coordinator, description)
        for description in STATUS_SENSORS
    )

    async_add_entities(entities)


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
        description: KomfoventBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, registers.REG_STATUS, description)

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self.register_id)
        if value is None:
            return None
        return bool(value & self.entity_description.bitmask)
