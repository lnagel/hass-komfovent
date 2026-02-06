"""DataUpdateCoordinator for Komfovent."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util.dt import utcnow
from pymodbus.exceptions import ModbusException

from . import registers
from .const import (
    DEFAULT_EMA_TIME_CONSTANT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ConnectedPanels,
    Controller,
)
from .core.ema import apply_ema
from .helpers import get_controller_version
from .modbus import KomfoventModbusClient

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FUNC_VER_AQ_HUMIDITY = 38
FUNC_VER_EXHAUST_TEMP = 67


class KomfoventCoordinator(TimestampDataUpdateCoordinator[dict[int, Any]]):
    """Class to manage fetching Komfovent data."""

    config_entry: ConfigEntry
    controller: Controller = Controller.NA
    func_version: int = 0
    client: KomfoventModbusClient
    ema_time_constant: int
    _cooldown_until: datetime | None = None

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        config_entry: ConfigEntry,
        ema_time_constant: int = DEFAULT_EMA_TIME_CONSTANT,
        **kwargs: Any,
    ) -> None:
        """Initialize."""
        kwargs.setdefault("name", DOMAIN)
        kwargs.setdefault("update_interval", timedelta(seconds=DEFAULT_UPDATE_INTERVAL))

        super().__init__(hass, _LOGGER, config_entry=config_entry, **kwargs)

        self.client = KomfoventModbusClient(
            host=config_entry.data[CONF_HOST],
            port=config_entry.data[CONF_PORT],
        )
        self.ema_time_constant = ema_time_constant

    def set_cooldown(self, seconds: float) -> None:
        """Set a cooldown period before the next update can proceed."""
        self._cooldown_until = utcnow() + timedelta(seconds=seconds)

    async def _wait_for_cooldown(self) -> None:
        """Wait for cooldown period to expire if set."""
        if self._cooldown_until is None:
            return
        wait_time = (self._cooldown_until - utcnow()).total_seconds()
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        connected = await self.client.connect()

        connection_error = "Failed to connect to Komfovent device"
        if not connected:
            raise ConfigEntryNotReady(connection_error)

        error_msg = "Failed to read controller firmware version"
        try:
            # Get firmware version and extract functional version from it
            fw_data = await self.client.read(registers.REG_FIRMWARE, 2)
            fw_version = get_controller_version(fw_data.get(registers.REG_FIRMWARE, 0))
            self.controller = fw_version[0]
            self.func_version = fw_version[4]
        except (ConnectionError, ModbusException) as error:
            _LOGGER.warning("%s: %s", error_msg, error)
            raise ConfigEntryNotReady(error_msg) from error

        return True

    async def _async_update_data(self) -> dict[int, Any]:
        """Fetch data from Komfovent."""
        await self._wait_for_cooldown()

        data = {}

        try:
            # Read primary control (1-34)
            data.update(await self.client.read(registers.REG_POWER, 34))

            # Read connectivity, extra control (35-44)
            # This has not been tested yet, it may be implemented in the future

            # Read modes (100-158)
            data.update(await self.client.read(registers.REG_AWAY_FAN_SUPPLY, 59))

            # Read humidity setpoints (159-162)
            # This has not been tested yet, it may be implemented in the future

            # Read Eco and air quality (200-217)
            if (
                self.controller in {Controller.C6, Controller.C6M}
                and self.func_version < FUNC_VER_AQ_HUMIDITY
            ):
                data.update(await self.client.read(registers.REG_ECO_MIN_TEMP, 15))
            else:
                data.update(await self.client.read(registers.REG_ECO_MIN_TEMP, 18))

            # Skip scheduler (300-555)

            # Read active alarms (600-610)
            data.update(await self.client.read(registers.REG_ACTIVE_ALARMS_COUNT, 11))

            # Skip alarm history (611-861)

            # Read monitoring (900-957)
            if (
                self.controller in {Controller.C6, Controller.C6M}
                and self.func_version < FUNC_VER_AQ_HUMIDITY
            ):
                data.update(await self.client.read(registers.REG_STATUS, 56))
            else:
                data.update(await self.client.read(registers.REG_STATUS, 58))

            # Read digital outputs (958-960)
            # This has not been tested yet, it may be implemented in the future

            # Read exhaust temperature (961)
            if (
                self.controller in {Controller.C6, Controller.C6M}
                and self.func_version >= FUNC_VER_EXHAUST_TEMP
            ):
                try:
                    data.update(await self.client.read(registers.REG_EXHAUST_TEMP, 1))
                except (ConnectionError, ModbusException) as error:
                    _LOGGER.debug("Failed to read exhaust temperature: %s", error)

            # Read controller firmware version (1000-1001)
            try:
                data.update(await self.client.read(registers.REG_FIRMWARE, 2))
            except (ConnectionError, ModbusException) as error:
                _LOGGER.warning("Failed to read controller firmware version: %s", error)

            # Read panel 1 firmware version (1002-1003)
            if data.get(registers.REG_CONNECTED_PANELS, 0) in [
                ConnectedPanels.PANEL1,
                ConnectedPanels.BOTH,
            ]:
                try:
                    data.update(await self.client.read(registers.REG_PANEL1_FW, 2))
                except (ConnectionError, ModbusException) as error:
                    _LOGGER.warning(
                        "Failed to read panel 1 firmware version: %s", error
                    )

            # Read panel 2 firmware version (1004-1005)
            if data.get(registers.REG_CONNECTED_PANELS, 0) in [
                ConnectedPanels.PANEL2,
                ConnectedPanels.BOTH,
            ]:
                try:
                    data.update(await self.client.read(registers.REG_PANEL2_FW, 2))
                except (ConnectionError, ModbusException) as error:
                    _LOGGER.warning(
                        "Failed to read panel 2 firmware version: %s", error
                    )

        except (ConnectionError, ModbusException) as error:
            _LOGGER.warning("Error communicating with Komfovent: %s", error)
            raise UpdateFailed from error

        self._apply_ema_on_update_data(data)
        return data

    def _apply_ema_on_update_data(self, data: dict[int, Any]) -> None:
        """Apply EMA filtering to selected registers."""
        if (
            self.ema_time_constant <= 0
            or self.data is None
            or not self.last_update_success_time
        ):
            return

        dt = (utcnow() - self.last_update_success_time).total_seconds()

        for reg in registers.REGISTERS_APPLY_EMA:
            if reg in data:
                data[reg] = apply_ema(
                    current=data[reg],
                    previous=self.data.get(reg),
                    tau=self.ema_time_constant,
                    dt=dt,
                )
