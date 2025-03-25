"""Switch platform for Komfovent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KomfoventCoordinator

from . import registers
from .const import DOMAIN


async def create_switches(coordinator: KomfoventCoordinator) -> list[KomfoventSwitch]:
    """Create switch entities for Komfovent device."""
    return [
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_NORMAL_HEATING,
            entity_description=SwitchEntityDescription(
                key="normal_heating",
                name="Normal Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_INTENSIVE_HEATING,
            entity_description=SwitchEntityDescription(
                key="intensive_heating",
                name="Intensive Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_BOOST_HEATING,
            entity_description=SwitchEntityDescription(
                key="boost_heating",
                name="Boost Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_HEATING,
            entity_description=SwitchEntityDescription(
                key="kitchen_heating",
                name="Kitchen Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_FIREPLACE_HEATING,
            entity_description=SwitchEntityDescription(
                key="fireplace_heating",
                name="Fireplace Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_OVERRIDE_HEATING,
            entity_description=SwitchEntityDescription(
                key="override_heating",
                name="Override Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_HOLIDAYS_HEATING,
            entity_description=SwitchEntityDescription(
                key="holiday_heating",
                name="Holiday Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AWAY_HEATING,
            entity_description=SwitchEntityDescription(
                key="away_heating",
                name="Away Heating",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_POWER,
            entity_description=SwitchEntityDescription(
                key="power",
                name="Power",
                icon="mdi:power",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_ECO_MODE,
            entity_description=SwitchEntityDescription(
                key="eco_mode",
                name="ECO Mode",
                icon="mdi:leaf",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AUTO_MODE,
            entity_description=SwitchEntityDescription(
                key="auto_mode",
                name="AUTO Mode",
                icon="mdi:auto-fix",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AQ_IMPURITY_CONTROL,
            entity_description=SwitchEntityDescription(
                key="aq_impurity_control",
                name="AQ Impurity Control",
                icon="mdi:air-filter",
                entity_registry_enabled_default=True,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AQ_HUMIDITY_CONTROL,
            entity_description=SwitchEntityDescription(
                key="aq_humidity_control",
                name="AQ Humidity Control",
                icon="mdi:water-percent",
                entity_registry_enabled_default=True,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AQ_ELECTRIC_HEATER,
            entity_description=SwitchEntityDescription(
                key="aq_electric_heater",
                name="AQ Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_FREE_HEATING,
            entity_description=SwitchEntityDescription(
                key="eco_free_cooling",
                name="ECO Free Cooling",
                icon="mdi:snowflake",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_HEATING_DENIED,
            entity_description=SwitchEntityDescription(
                key="eco_heater_blocking",
                name="ECO Heater Blocking",
                icon="mdi:radiator-off",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_COOLING_DENIED,
            entity_description=SwitchEntityDescription(
                key="eco_cooler_blocking",
                name="ECO Cooler Blocking",
                icon="mdi:snowflake-off",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Komfovent switches."""
    coordinator: KomfoventCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(await create_switches(coordinator))


class KomfoventSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Komfovent switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KomfoventCoordinator,
        register_id: int,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
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
        """Return True if entity is on."""
        if not self.coordinator.data:
            return None
        return bool(self.coordinator.data.get(self.register_id, 0))

    async def async_turn_on(self, **_kwargs: dict) -> None:
        """Turn the entity on."""
        await self.coordinator.client.write_register(self.register_id, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: dict) -> None:
        """Turn the entity off."""
        await self.coordinator.client.write_register(self.register_id, 0)
        await self.coordinator.async_request_refresh()
