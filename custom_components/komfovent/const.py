"""Constants for the Komfovent integration."""

from __future__ import annotations

from datetime import timedelta
from enum import IntEnum
from typing import Final

DOMAIN = "komfovent"

# Firmware update constants
FIRMWARE_CHECK_INTERVAL: Final = timedelta(days=7)
FIRMWARE_STORAGE_KEY: Final = "komfovent_firmware"
FIRMWARE_STORAGE_VERSION: Final = 1
FIRMWARE_DIR: Final = "komfovent"
FIRMWARE_MIN_SIZE: Final = 100 * 1024  # 100 KB
FIRMWARE_MAX_SIZE: Final = 10 * 1024 * 1024  # 10 MB
FIRMWARE_MIN_SUPPORTED_VERSION: Final = (1, 3, 15)  # v1.3.15 minimum for .mbin support

# Config
DEFAULT_NAME = "Komfovent"
DEFAULT_HOST: Final = None
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID: Final = 254

# Options
OPT_UPDATE_INTERVAL: Final = "update_interval"
OPT_EMA_TIME_CONSTANT: Final = "ema_time_constant"
OPT_STEP_FLOW: Final = "step_flow"
OPT_STEP_TEMPERATURE: Final = "step_temperature"
OPT_STEP_HUMIDITY: Final = "step_humidity"
OPT_STEP_CO2: Final = "step_co2"
OPT_STEP_VOC: Final = "step_voc"
OPT_STEP_TIMER: Final = "step_timer"

# Defaults
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_EMA_TIME_CONSTANT = 300
DEFAULT_STEP_FLOW: Final = 5.0
DEFAULT_STEP_TEMPERATURE: Final = 0.5
DEFAULT_STEP_HUMIDITY: Final = 5.0
DEFAULT_STEP_CO2: Final = 25.0
DEFAULT_STEP_VOC: Final = 5.0
DEFAULT_STEP_TIMER: Final = 5.0


class Controller(IntEnum):
    """Controllers."""

    C6 = 0
    C6M = 1
    C8 = 2
    NA = 15


class Panel(IntEnum):
    """Panel types for firmware versioning."""

    P1 = 0
    NA = 15


# Firmware download URLs per controller type
# C6 and C6M share the same firmware
FIRMWARE_URLS: Final[dict[Controller, str]] = {
    Controller.C6: "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin",
    Controller.C6M: "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin",
    Controller.C8: "https://komfovent.com/Update/Controllers/C8/firmware.php?file=mbin",
}


class OperationMode(IntEnum):
    """Operation modes."""

    STANDBY = 0
    AWAY = 1
    NORMAL = 2
    INTENSIVE = 3
    BOOST = 4
    KITCHEN = 5
    FIREPLACE = 6
    OVERRIDE = 7
    HOLIDAY = 8
    AIR_QUALITY = 9
    OFF = 10


class SchedulerMode(IntEnum):
    """Scheduler operation modes."""

    STAY_AT_HOME = 0
    WORKING_WEEK = 1
    OFFICE = 2
    CUSTOM = 3


class AutoModeControl(IntEnum):
    """Auto mode control types."""

    SCHEDULING = 0
    AIR_QUALITY = 1


class TemperatureControl(IntEnum):
    """Temperature control types."""

    SUPPLY = 0
    EXTRACT = 1
    ROOM = 2
    BALANCE = 3


class FlowControl(IntEnum):
    """Flow control types."""

    CONSTANT = 0
    VARIABLE = 1
    DIRECT = 2
    OFF = 3


class CoilType(IntEnum):
    """Coil types."""

    HOT_WATER = 0
    COLD_WATER = 1
    COMBI = 2


class AirQualitySensorType(IntEnum):
    """Air quality sensor types."""

    NOT_INSTALLED = 0
    CO2 = 1
    VOC = 2
    HUMIDITY = 3


class OutdoorHumiditySensor(IntEnum):
    """Outdoor humidity sensor options."""

    NONE = 0
    SENSOR1 = 1
    SENSOR2 = 2


class OverrideActivation(IntEnum):
    """
    Override mode types.

    Determines when override mode can be activated:
    - ALL_TIME: Override can be activated at any time
    - IF_ON: Override only when unit is running
    - IF_OFF: Override only when unit is stopped
    """

    ALL_TIME = 0
    IF_ON = 1
    IF_OFF = 2


class HolidayMicroventilation(IntEnum):
    """Holiday microventilation modes."""

    ONCE_PER_DAY = 1
    TWICE_PER_DAY = 2
    THRICE_PER_DAY = 3
    FOUR_TIMES_PER_DAY = 4


class ConnectedPanels(IntEnum):
    """Connected control panels."""

    NONE = 0
    PANEL1 = 1
    PANEL2 = 2
    BOTH = 3


class HeatExchangerType(IntEnum):
    """Heat exchanger types."""

    PLATE = 0
    ROTARY = 1


class MicroVentilation(IntEnum):
    """Holiday mode micro-ventilation frequency."""

    ONCE = 1
    TWICE = 2
    THRICE = 3
    FOUR = 4


class FlowUnit(IntEnum):
    """Flow measurement units."""

    M3H = 0  # m³/h
    LS = 1  # l/s


class HeatRecoveryControl(IntEnum):
    """Heat recovery control modes."""

    AUTO = 0
    CONSTANT = 1
    NON_STOP = 2


class ControlStage(IntEnum):
    """Control stage options."""

    NONE = 0
    EXTERNAL_COIL = 1
    ELECTRIC_HEATER = 2
    EXTERNAL_DX_UNIT = 3


class ResetSettings(IntEnum):
    """Reset settings options."""

    AWAY = 1
    NORMAL = 2
    INTENSIVE = 3
    BOOST = 4
    HOLIDAYS = 5
    OVERRIDE = 6
    KITCHEN = 7
    FIREPLACE = 8
    AIR_QUALITY = 9
    ECO = 10
    ADVANCED = 11
