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
from .helpers import build_device_info


async def create_switches(coordinator: KomfoventCoordinator) -> list[KomfoventSwitch]:
    """Create switch entities for Komfovent device."""
    return [
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
            register_id=registers.REG_ECO_FREE_HEAT_COOL,
            entity_description=SwitchEntityDescription(
                key="eco_free_heat_cool",
                name="ECO Free Heating/Cooling",
                icon="mdi:snowflake",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_ECO_HEATER_BLOCKING,
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
            register_id=registers.REG_ECO_COOLER_BLOCKING,
            entity_description=SwitchEntityDescription(
                key="eco_cooler_blocking",
                name="ECO Cooler Blocking",
                icon="mdi:snowflake-off",
                entity_registry_enabled_default=True,
                entity_category=None,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_AWAY_HEATER,
            entity_description=SwitchEntityDescription(
                key="away_electric_heater",
                name="Away Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_NORMAL_HEATER,
            entity_description=SwitchEntityDescription(
                key="normal_electric_heater",
                name="Normal Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_INTENSIVE_HEATER,
            entity_description=SwitchEntityDescription(
                key="intensive_electric_heater",
                name="Intensive Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_BOOST_HEATER,
            entity_description=SwitchEntityDescription(
                key="boost_electric_heater",
                name="Boost Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_KITCHEN_HEATER,
            entity_description=SwitchEntityDescription(
                key="kitchen_electric_heater",
                name="Kitchen Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_FIREPLACE_HEATER,
            entity_description=SwitchEntityDescription(
                key="fireplace_electric_heater",
                name="Fireplace Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_OVERRIDE_HEATER,
            entity_description=SwitchEntityDescription(
                key="override_electric_heater",
                name="Override Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
            ),
        ),
        KomfoventSwitch(
            coordinator=coordinator,
            register_id=registers.REG_HOLIDAYS_HEATER,
            entity_description=SwitchEntityDescription(
                key="holidays_electric_heater",
                name="Holidays Electric Heater",
                icon="mdi:radiator",
                entity_registry_enabled_default=True,
                entity_registry_visible_default=False,
                entity_category=EntityCategory.CONFIG,
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


class KomfoventSwitch(CoordinatorEntity["KomfoventCoordinator"], SwitchEntity):
    """Representation of a Komfovent switch."""

    _attr_has_entity_name = True
    coordinator: KomfoventCoordinator

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
        self._attr_device_info = build_device_info(coordinator)

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self.register_id)
        if value is None:
            return None
        return bool(value)

    async def async_turn_on(self, **_kwargs: dict) -> None:
        """Turn the entity on."""
        await self.coordinator.client.write(self.register_id, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: dict) -> None:
        """Turn the entity off."""
        await self.coordinator.client.write(self.register_id, 0)
        await self.coordinator.async_request_refresh()
