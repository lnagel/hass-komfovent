"""Constants for the Komfovent integration."""
from __future__ import annotations

from enum import IntEnum
from homeassistant.const import (
    TEMP_CELSIUS,
    PERCENTAGE,
    POWER_WATT,
    ENERGY_KILO_WATT_HOUR,
    VOLUME_FLOW_RATE_CUBIC_METERS_PER_HOUR,
    REVOLUTIONS_PER_MINUTE,
)
from typing import Final

DOMAIN = "komfovent"


DEFAULT_NAME = "Komfovent"
DEFAULT_HOST: Final = "10.20.2.60"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID: Final = 254
DEFAULT_SCAN_INTERVAL = 30

# Modbus registers - Basic Control
REG_POWER = 0  # ON/OFF status
REG_AUTO_MODE_CONTROL = 1  # Auto mode control
REG_ECO_MODE = 2  # ECO mode
REG_AUTO_MODE = 3  # AUTO mode
REG_OPERATION_MODE = 4  # Current mode
REG_SCHEDULER_MODE = 5  # Scheduler operation mode
REG_NEXT_MODE = 6  # Next mode
REG_NEXT_MODE_TIME = 7  # Next mode start time
REG_NEXT_MODE_WEEKDAY = 8  # Next mode weekday
REG_BEFORE_MODE_MASK = 9  # Before been mode mask

# Temperature and Flow control
REG_TEMP_CONTROL = 10  # Temperature control
REG_FLOW_CONTROL = 11  # Flow control
REG_MAX_SUPPLY_FLOW = 12  # Maximum supply flow (32-bit)
REG_MAX_EXTRACT_FLOW = 14  # Maximum extract flow (32-bit)
REG_MAX_SUPPLY_PRESSURE = 16  # Max supply pressure
REG_MAX_EXTRACT_PRESSURE = 17  # Max extract pressure

# Control sequence
REG_STAGE1 = 18  # Stage 1 control
REG_STAGE2 = 19  # Stage 2 control
REG_STAGE3 = 20  # Stage 3 control
REG_COIL_TYPE = 21  # Coil type

# Connectivity
REG_IP = 22  # IP address (32-bit)
REG_MASK = 24  # Network mask (32-bit)

# Settings
REG_LANGUAGE = 26  # Language
REG_FLOW_UNITS = 27  # Flow units

# Time and date
REG_TIME = 28  # Time HH:MM
REG_YEAR = 29  # Year
REG_MONTH_DAY = 30  # Month/Day
REG_WEEK_DAY = 31  # Week day
REG_EPOCH_TIME = 32  # Time since 1970 (32-bit)

# Mode: Away
REG_AWAY_FAN_SUPPLY = 99     # Supply flow (32-bit)
REG_AWAY_FAN_EXTRACT = 101   # Extract flow (32-bit)
REG_AWAY_TEMP = 103          # Setpoint
REG_AWAY_HEATING = 104       # Heating

# Mode: Normal
REG_NORMAL_FAN_SUPPLY = 105  # Supply flow (32-bit)
REG_NORMAL_FAN_EXTRACT = 107 # Extract flow (32-bit)
REG_NORMAL_SETPOINT = 109    # Setpoint
REG_NORMAL_HEATING = 110     # Heating

# Mode: Intensive
REG_INTENSIVE_FAN_SUPPLY = 111  # Supply flow (32-bit)
REG_INTENSIVE_FAN_EXTRACT = 113 # Extract flow (32-bit)
REG_INTENSIVE_TEMP = 115     # Setpoint
REG_INTENSIVE_HEATING = 116  # Heating

# Mode: Boost
REG_BOOST_FAN_SUPPLY = 117   # Supply flow (32-bit)
REG_BOOST_FAN_EXTRACT = 119  # Extract flow (32-bit)
REG_BOOST_TEMP = 121        # Setpoint
REG_BOOST_HEATING = 122     # Heating

# Mode: Kitchen
REG_KITCHEN_SUPPLY = 123    # Supply flow (32-bit)
REG_KITCHEN_EXTRACT = 125   # Extract flow (32-bit)
REG_KITCHEN_TEMP = 127      # Setpoint
REG_KITCHEN_HEATING = 128   # Heating
REG_KITCHEN_TIMER = 129     # Timer time

# Mode: Fireplace
REG_FIREPLACE_SUPPLY = 130  # Supply flow (32-bit)
REG_FIREPLACE_EXTRACT = 132 # Extract flow (32-bit)
REG_FIREPLACE_TEMP = 134    # Setpoint
REG_FIREPLACE_HEATING = 135 # Heating
REG_FIREPLACE_TIMER = 136   # Timer time

# Mode: Override
REG_OVERRIDE_SUPPLY = 137   # Supply flow (32-bit)
REG_OVERRIDE_EXTRACT = 139  # Extract flow (32-bit)
REG_OVERRIDE_TEMP = 141     # Setpoint
REG_OVERRIDE_HEATING = 142  # Heating
REG_OVERRIDE_MODE = 143     # Mode
REG_OVERRIDE_TIMER = 144    # Timer time

# Mode: Holidays
REG_HOLIDAYS_MICROVENT = 145 # Microventilation
REG_HOLIDAYS_TEMP = 146      # Setpoint
REG_HOLIDAYS_HEATING = 147   # Heating
REG_HOLIDAYS_FROM = 148      # From Day/Month
REG_HOLIDAYS_TILL = 150      # Till Day/Month
REG_HOLIDAYS_YEAR_FROM = 152 # Year, from
REG_HOLIDAYS_DATE_FROM = 153 # Month/Day, from
REG_HOLIDAYS_YEAR_TILL = 154 # Year, till
REG_HOLIDAYS_DATE_TILL = 155 # Month/Day, till

# ECO settings
REG_ECO_MIN_TEMP = 199  # Minimum supply air temperature
REG_ECO_MAX_TEMP = 200  # Maximum supply air temperature
REG_FREE_HEATING = 201  # Free heating/cooling
REG_HEATING_DENIED = 202  # Heating enable denied
REG_COOLING_DENIED = 203  # Cooling enable denied

# Air quality settings
REG_AQ_ENABLE = 204  # Air quality Enable
REG_AQ_TEMP_SETPOINT = 205  # Temperature setpoint
REG_CO2_SETPOINT = 206  # CO2 setpoint
REG_HUMIDITY_SETPOINT = 207  # Humidity setpoint
REG_AQ_MIN_INTENSITY = 208  # Air quality minimum intensity
REG_AQ_MAX_INTENSITY = 209  # Air quality maximum intensity
REG_AQ_HEATING = 210  # Air quality heating
REG_AQ_CHECK_PERIOD = 211  # Air quality check period
REG_AQ_SENSOR1_TYPE = 212  # Air quality sensor 1 type
REG_AQ_SENSOR2_TYPE = 213  # Air quality sensor 2 type

# Alarm registers
REG_ACTIVE_ALARMS_COUNT = 599  # Active alarms count (write 0x99C6 to reset and restore previous mode)
REG_ACTIVE_ALARM1 = 600  # Active alarm 1 code
REG_ACTIVE_ALARM2 = 601  # Active alarm 2 code
REG_ACTIVE_ALARM3 = 602  # Active alarm 3 code
REG_ACTIVE_ALARM4 = 603  # Active alarm 4 code
REG_ACTIVE_ALARM5 = 604  # Active alarm 5 code
REG_ACTIVE_ALARM6 = 605  # Active alarm 6 code
REG_ACTIVE_ALARM7 = 606  # Active alarm 7 code
REG_ACTIVE_ALARM8 = 607  # Active alarm 8 code
REG_ACTIVE_ALARM9 = 608  # Active alarm 9 code
REG_ACTIVE_ALARM10 = 609  # Active alarm 10 code

# Sensor registers
REG_STATUS = 899  # Unit status bitmask (Starting=0, Stopping=1, Fan=2, Rotor=3, Heating=4, Cooling=5, HeatingDenied=6, CoolingDenied=7, FlowDown=8, FreeHeating=9, FreeCooling=10, AlarmF=11, AlarmW=12)
REG_HEATING_CONFIG = 900  # Heating/cooling config
REG_SUPPLY_TEMP = 901  # Supply air temperature (x10 °C)
REG_EXTRACT_TEMP = 902  # Extract air temperature (x10 °C)
REG_OUTDOOR_TEMP = 903  # Outdoor air temperature (x10 °C)
REG_WATER_TEMP = 904   # Water temperature (x10 °C)
REG_SUPPLY_FLOW = 905  # Supply air flow (32-bit)
REG_EXTRACT_FLOW = 907  # Extract air flow (32-bit)
REG_SUPPLY_FAN_INTENSITY = 909  # Supply fan speed
REG_EXTRACT_FAN_INTENSITY = 910  # Extract fan speed
REG_HEAT_EXCHANGER = 911  # Heat exchanger signal
REG_ELECTRIC_HEATER = 912  # Electric heater signal (x10 %)
REG_WATER_HEATER = 913  # Water heater signal
REG_WATER_COOLER = 914  # Water cooler signal
REG_DX_UNIT = 915  # DX unit signal
REG_FILTER_IMPURITY = 916  # Filter clogging
REG_AIR_DAMPERS = 917  # Air dampers
REG_SUPPLY_PRESSURE = 918  # Supply pressure
REG_EXTRACT_PRESSURE = 919  # Extract pressure

# Efficiency status
REG_POWER_CONSUMPTION = 920  # Power consumption
REG_HEATER_POWER = 921  # Heater power
REG_HEAT_RECOVERY = 922  # Heat recovery
REG_HEAT_EFFICIENCY = 923  # Heat exchanger efficiency
REG_ENERGY_SAVING = 924  # Energy saving
REG_SPI = 925  # Specific power input

# Consumption registers
REG_AHU_DAY = 926  # AHU consumption Day (32-bit)
REG_AHU_MONTH = 928  # AHU consumption Month (32-bit)
REG_AHU_TOTAL = 930  # AHU consumption Total (32-bit)
REG_HEATER_DAY = 932  # Additional heater Day (32-bit)
REG_HEATER_MONTH = 934  # Additional heater Month (32-bit)
REG_HEATER_TOTAL = 936  # Additional heater Total (32-bit)
REG_RECOVERY_DAY = 938  # Recovered energy Day (32-bit)
REG_RECOVERY_MONTH = 940  # Recovered energy Month (32-bit)
REG_RECOVERY_TOTAL = 942  # Recovered energy Total (32-bit)
REG_SPI_DAY = 944  # SPI per day

# Panel sensor registers
REG_PANEL1_TEMP = 945  # Panel 1 temperature
REG_PANEL1_RH = 946  # Panel 1 relative humidity
REG_PANEL1_AQ = 947  # Panel 1 air quality
REG_PANEL2_TEMP = 948  # Panel 2 temperature
REG_PANEL2_RH = 949  # Panel 2 relative humidity
REG_PANEL2_AQ = 950  # Panel 2 air quality

# Air quality sensor registers
REG_AQ_SENSOR1_VALUE = 951  # Air quality sensor 1 value
REG_AQ_SENSOR2_VALUE = 952  # Air quality sensor 2 value

# Firmware registers
REG_FIRMWARE = 999  # Firmware version (32-bit)
REG_PANEL1_FW = 1001  # Panel 1 firmware version (32-bit)
REG_PANEL2_FW = 1003  # Panel 2 firmware version (32-bit)

# Reset register
REG_RESET_SETTINGS = 1049  # Reset settings

# Register value types
VALUE_TYPE_UINT8: Final = "uint8"
VALUE_TYPE_UINT16: Final = "uint16"
VALUE_TYPE_INT8: Final = "int8"
VALUE_TYPE_INT16: Final = "int16"
VALUE_TYPE_UINT32: Final = "uint32"

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
    BALANCE = 2
    ROOM = 3

class FlowControl(IntEnum):
    """Flow control types."""
    CAV = 0
    VAV = 1
    DCV = 2

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
