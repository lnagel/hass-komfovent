"""Constants for the Komfovent integration."""
from __future__ import annotations

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
REG_ECO_MODE = 2  # ECO mode active
REG_AUTO_MODE = 3  # AUTO mode active
REG_OPERATION_MODE = 4  # Current operating mode
REG_SCHEDULER_MODE = 5  # Scheduler operation mode
REG_NEXT_MODE = 6  # Next mode
REG_NEXT_MODE_TIME = 7  # Next mode start time
REG_NEXT_MODE_WEEKDAY = 8  # Next mode weekday
REG_BEFORE_MODE_MASK = 9  # Before been mode mask

# Temperature and Flow control
REG_TEMP_CONTROL = 10  # Temperature control (Supply/Extract/Balance/Room)
REG_FLOW_CONTROL = 11  # Flow control (CAV/VAV/DCV)
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
REG_TIME_START = 28  # Start of time registers block
REG_TIME = 28  # Time HH:MM
REG_YEAR = 29  # Year
REG_MONTH_DAY = 30  # Month/Day
REG_WEEK_DAY = 31  # Week day
REG_EPOCH_TIME = 32  # Time since 1970 (32-bit)

# Mode temperature setpoints
REG_NORMAL_SETPOINT = 109  # Normal mode temperature
REG_NORMAL_FAN_SUPPLY = 105  # Normal mode supply fan speed
REG_NORMAL_FAN_EXTRACT = 107  # Normal mode extract fan speed
REG_AWAY_FAN_SUPPLY = 99     # Away mode supply fan speed
REG_AWAY_FAN_EXTRACT = 101   # Away mode extract fan speed
REG_INTENSIVE_FAN_SUPPLY = 111  # Intensive mode supply fan speed
REG_INTENSIVE_FAN_EXTRACT = 113  # Intensive mode extract fan speed
REG_BOOST_FAN_SUPPLY = 117   # Boost mode supply fan speed
REG_BOOST_FAN_EXTRACT = 119  # Boost mode extract fan speed
REG_INTENSIVE_TEMP = 115  # Intensive mode temperature
REG_BOOST_TEMP = 121  # Boost mode temperature
REG_AWAY_TEMP = 103  # Away mode temperature
REG_KITCHEN_TEMP = 127  # Kitchen mode temperature

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

# Sensor registers
REG_STATUS = 899  # Unit status bitmask
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
REG_ELECTRIC_HEATER = 912  # Electric heater signal
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
REG_AQ_SENSOR1_VALUE = 951  # Air quality sensor 1 value
REG_AQ_SENSOR2_VALUE = 952  # Air quality sensor 2 value

# Firmware registers
REG_FIRMWARE = 999  # Firmware version (32-bit)
REG_PANEL1_FW = 1001  # Panel 1 firmware version (32-bit)
REG_PANEL2_FW = 1003  # Panel 2 firmware version (32-bit)

# Reset register
REG_RESET_SETTINGS = 1049  # Reset settings

# Air quality sensor type constants
AQ_SENSOR_TYPE_NOT_INSTALLED: Final = 0
AQ_SENSOR_TYPE_CO2: Final = 1
AQ_SENSOR_TYPE_VOC: Final = 2
AQ_SENSOR_TYPE_RH: Final = 3

# Air quality sensor type names
AQ_SENSOR_TYPES = {
    AQ_SENSOR_TYPE_NOT_INSTALLED: "Not installed",
    AQ_SENSOR_TYPE_CO2: "CO2",
    AQ_SENSOR_TYPE_VOC: "VOC",
    AQ_SENSOR_TYPE_RH: "RH"
}

# Time registers
REG_TIME_START = 28  # Start of time registers block (6 registers)

# Register value types
VALUE_TYPE_UINT8: Final = "uint8"
VALUE_TYPE_UINT16: Final = "uint16"
VALUE_TYPE_INT8: Final = "int8"
VALUE_TYPE_INT16: Final = "int16"
VALUE_TYPE_UINT32: Final = "uint32"

# Register read/write transforms
TRANSFORM_DEFAULT: Final = "default"
TRANSFORM_DIVIDE10: Final = "JS(divide10.js)"
TRANSFORM_MULTIPLY10: Final = "JS(multiply10.js)"
TRANSFORM_DIVIDE1000: Final = "JS(divide1000.js)"
TRANSFORM_VALIDATE_RH: Final = "JS(validateRH.js)"
TRANSFORM_VALIDATE_CO2: Final = "JS(validateCO2.js)"
TRANSFORM_VALIDATE_SPI: Final = "JS(validateSPI.js)"

# Operation modes
OPERATION_MODES = {
    0: "Standby",
    1: "Away", 
    2: "Normal",
    3: "Intensive",
    4: "Boost",
    5: "Kitchen",
    6: "Fireplace",
    7: "Override",
    8: "Holiday",
    9: "Air Quality",
    10: "Off"
}

# Scheduler modes
SCHEDULER_MODES = {
    0: "StayAtHome",
    1: "WorkingWeek", 
    2: "Office",
    3: "Custom"
}
