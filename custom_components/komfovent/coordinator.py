"""DataUpdateCoordinator for Komfovent."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.exceptions import ModbusException

from . import registers
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ConnectedPanels,
    Controller,
)
from .helpers import get_version_from_int

_LOGGER = logging.getLogger(__name__)

FUNC_VER_EXHAUST_TEMP = 67


class KomfoventCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Komfovent data."""

    controller: Controller = Controller.NA
    func_version: int = 0

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        **kwargs: Any,
    ) -> None:
        """Initialize."""
        from .modbus import KomfoventModbusClient  # easier to mock

        kwargs.setdefault("name", DOMAIN)
        kwargs.setdefault("update_interval", timedelta(seconds=DEFAULT_SCAN_INTERVAL))

        super().__init__(hass, _LOGGER, **kwargs)
        self.client = KomfoventModbusClient(host, port)

    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        connected = await self.client.connect()

        connection_error = "Failed to connect to Komfovent device"
        if not connected:
            raise ConfigEntryNotReady(connection_error)

        ERROR_MSG = "Failed to read controller firmware version"
        try:
            # Get firmware version and extract functional version from it
            fw_data = await self.client.read(registers.REG_FIRMWARE, 2)
            fw_version = get_version_from_int(fw_data.get(registers.REG_FIRMWARE, 0))
            self.controller = fw_version[0]
            self.func_version = fw_version[4]
        except (ConnectionError, ModbusException) as error:
            _LOGGER.warning(f"{ERROR_MSG}: %s", error)
            raise ConfigEntryNotReady(ERROR_MSG) from error

        return True

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Komfovent."""
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
            data.update(await self.client.read(registers.REG_ECO_MIN_TEMP, 18))

            # Skip scheduler (300-555)

            # Read active alarms (600-610)
            data.update(await self.client.read(registers.REG_ACTIVE_ALARMS_COUNT, 11))

            # Skip alarm history (611-861)

            # Read monitoring (900-957)
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

        return data
