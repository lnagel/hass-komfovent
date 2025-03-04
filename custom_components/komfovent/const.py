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

# Modbus registers
REG_POWER = 0  # Unit active status
REG_ECO_MODE = 2  # ECO mode active
REG_AUTO_MODE = 3  # AUTO mode active
REG_OPERATION_MODE = 4  # Current operating mode
REG_SCHEDULER_MODE = 5
REG_TEMP_CONTROL = 10
REG_FLOW_CONTROL = 11

# Mode temperature setpoints
REG_NORMAL_SETPOINT = 109  # Normal mode temperature
# Fan speed setpoints
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
REG_ECO_MIN_TEMP = 199
REG_ECO_MAX_TEMP = 200

# Air quality setpoints
REG_HUMIDITY_SETPOINT = 207  # Humidity setpoint
REG_CO2_SETPOINT = 206  # CO2 setpoint

# Sensor registers
REG_STATUS = 899  # Unit status bitmask
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
REG_FILTER_IMPURITY = 916  # Filter clogging
REG_POWER_CONSUMPTION = 920  # Power consumption
REG_HEATER_POWER = 921  # Heater power
REG_HEAT_RECOVERY = 922  # Heat recovery
REG_HEAT_EFFICIENCY = 923  # Heat exchanger efficiency
REG_SPI = 925  # Specific power input

# Panel sensor registers
REG_PANEL1_TEMP = 945  # Panel 1 temperature
REG_PANEL1_RH = 946  # Panel 1 relative humidity
REG_EXTRACT_CO2 = 951  # Extract air CO2
REG_EXTRACT_RH = 952  # Extract air relative humidity

# Air quality sensor configuration
REG_AQ_SENSOR1_TYPE = 212  # Air quality sensor 1 type
REG_AQ_SENSOR2_TYPE = 213  # Air quality sensor 2 type
REG_AQ_SENSOR1_VALUE = 951  # Air quality sensor 1 value
REG_AQ_SENSOR2_VALUE = 952  # Air quality sensor 2 value

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
