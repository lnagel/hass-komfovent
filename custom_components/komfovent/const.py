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


# Alarm reset command value
ALARM_RESET_COMMAND: Final = 0x99C6

# Alarm code messages mapping raw alarm byte to human-readable message.
# Faults have MSb=0, Warnings have MSb=1. Lower 7 bits are the alarm number.
ALARM_CODE_MESSAGES: Final[dict[int, str]] = {
    # Faults — from MODBUS_C6_2025.pdf pp30-31
    0x01: "Supply Flow Not Reached",
    0x02: "Exhaust Flow Not Reached",
    0x03: "Water Temp B5 Too Low",
    0x04: "Low Supply Air Temperature",
    0x05: "High Supply Air Temperature",
    0x06: "Electric Heater Overheat",
    0x07: "Heat Exchanger Failure",
    0x08: "Heat Exchanger Icing",
    0x09: "Internal Fire",
    0x0A: "External Fire",
    0x0B: "Supply Air Temp B1 Short",
    0x0C: "Supply Air Temp B1 Not Connected",
    0x0D: "Extract Air Temp B2 Short",
    0x0E: "Extract Air Temp B2 Not Connected",
    0x0F: "Outdoor Air Temp B3 Short",
    0x10: "Outdoor Air Temp B3 Not Connected",
    0x11: "Exhaust Air Temp B4 Short",
    0x12: "Exhaust Air Temp B4 Not Connected",
    0x13: "Water Temp B5 Short",
    0x14: "Water Temp B5 Not Connected",
    0x15: "Supply Temp After Hx B10 Short",
    0x16: "Supply Temp After Hx B10 Not Connected",
    0x17: "Flash Fail",
    0x18: "Too Low 24V Supply Voltage",
    0x19: "Too High 24V Supply Voltage",
    0x1A: "24V Supply Voltage Overloaded",
    0x1C: "Room Temperature Sensor Fail",
    0x1D: "Room Humidity Sensor Fail",
    0x1E: "Humidity Sensor Failure",
    0x1F: "Impurity Sensor Failure",
    0x20: "Heat Exchanger Failure",
    0x21: "Heat Exchanger Failure",
    0x22: "Heat Exchanger Failure",
    0x23: "Heat Exchanger Failure",
    0x24: "Heat Exchanger Failure",
    0x25: "Heat Exchanger Failure",
    0x26: "Air Flow Sensor Failure",
    0x27: "Air Flow Sensor Failure",
    0x28: "Communication Error",
    0x29: "Fire Dampers Failure",
    0x2A: "Fire Damper Failure",
    0x2B: "Fire Damper Failure",
    0x2C: "Fire Damper Failure",
    0x2D: "Fire Damper Failure",
    0x2E: "External Fire Alarm",
    0x2F: "External Fire Alarm",
    0x30: "External Fire Alarm",
    0x31: "External Fire Alarm",
    0x32: "External Fire Alarm",
    0x33: "Electric Heater Failure",
    0x34: "Electric Preheater Failure",
    # Warnings
    0x81: "Change Air Filter",
    0x82: "Service Mode",
    0x83: "Water Temp B5 Too Low",
    0x84: "Humidity Sensor Failure",
    0x85: "Impurity Sensor Failure",
    0x86: "Low Heat Exchanger Efficiency",
}


def format_alarm_code(code: int) -> str:
    """Format raw alarm byte to manual notation: F9, W1, etc."""
    number = code & 0x7F
    prefix = "W" if code & 0x80 else "F"
    return f"{prefix}{number}"
