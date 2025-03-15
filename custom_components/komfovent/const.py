"""Constants for the Komfovent integration."""

from __future__ import annotations

from enum import IntEnum
from typing import Final

DOMAIN = "komfovent"

DEFAULT_NAME = "Komfovent"
DEFAULT_HOST: Final = None
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID: Final = 254
DEFAULT_SCAN_INTERVAL = 30


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

    CAV = 0
    VAV = 1
    DCV = 2
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
    RH = 3


class OverrideMode(IntEnum):
    """Override mode types."""

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


class FlowUnit(IntEnum):
    """Flow measurement units."""

    M3H = 0  # m³/h
    LS = 1  # l/s


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
