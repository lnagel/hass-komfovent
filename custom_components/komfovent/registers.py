"""
Modbus register definitions for Komfovent devices.

This module contains the register addresses and register sets used for communicating
with Komfovent ventilation units via Modbus TCP.
"""

from __future__ import annotations

# Modbus registers - Basic Control
REG_POWER = 1  # ON/OFF status
REG_AUTO_MODE_CONTROL = 2  # Auto mode control
REG_ECO_MODE = 3  # ECO mode
REG_AUTO_MODE = 4  # AUTO mode
REG_OPERATION_MODE = 5  # Current mode
REG_SCHEDULER_MODE = 6  # Scheduler operation mode
REG_NEXT_MODE = 7  # Next mode
REG_NEXT_MODE_TIME = 8  # Next mode start time
REG_NEXT_MODE_WEEKDAY = 9  # Next mode weekday
REG_BEFORE_MODE_MASK = 10  # Before been mode mask

# Temperature and Flow control
REG_TEMP_CONTROL = 11  # Temperature control
REG_FLOW_CONTROL = 12  # Flow control
REG_MAX_SUPPLY_FLOW = 13  # Maximum supply flow (32-bit)
REG_MAX_EXTRACT_FLOW = 15  # Maximum extract flow (32-bit)
REG_MAX_SUPPLY_PRESSURE = 17  # Max supply pressure
REG_MAX_EXTRACT_PRESSURE = 18  # Max extract pressure
REG_ROOM_SENSOR = 39  # Room sensor (Panel 1 = 0, Panel 2 = 1; undocumented for C6)

# Control sequence
REG_STAGE1 = 19  # Control stage 1
REG_STAGE2 = 20  # Control stage 2
REG_STAGE3 = 21  # Control stage 3
REG_EXTERNAL_COIL_TYPE = 22  # External coil type
REG_ICING_PROTECTION = 40  # Icing protection (Off = 0, On = 1, External coil = 2)
REG_INDOOR_HUMIDITY = 41  # Indoor humidity (Auto = -1, Manual = 10-90%RH)

# Connectivity
REG_DHCP = 35  # DHCP (Off = 0, On = 1)
REG_IP = 23  # IP address (32-bit)
REG_MASK = 25  # Network mask (32-bit)
REG_GATEWAY = 36  # Network gateway (32-bit)
REG_BACNET_ID = 38  # Bacnet ID
REG_BACNET_PORT = 44  # Bacnet port

# Settings
REG_LANGUAGE = 27  # Language
REG_FLOW_UNIT = 28  # Flow unit
REG_FIRE_ALARM_RESTART = 42  # Fire alarm restart (Off = 0, On = 1)

# Time and date
REG_TIME = 29  # Time HH:MM
REG_YEAR = 30  # Year
REG_MONTH_DAY = 31  # Month/Day
REG_WEEK_DAY = 32  # Week day
REG_EPOCH_TIME = 33  # Time since 1970 (32-bit)

# Away mode registers
REG_AWAY_FAN_SUPPLY = 100  # Supply flow (32-bit)
REG_AWAY_FAN_EXTRACT = 102  # Extract flow (32-bit)
REG_AWAY_TEMP = 104  # Setpoint
REG_AWAY_HEATER = 105  # Electric heater

# Normal mode registers
REG_NORMAL_FAN_SUPPLY = 106  # Supply flow (32-bit)
REG_NORMAL_FAN_EXTRACT = 108  # Extract flow (32-bit)
REG_NORMAL_SETPOINT = 110  # Setpoint
REG_NORMAL_HEATER = 111  # Electric heater

# Intensive mode registers
REG_INTENSIVE_FAN_SUPPLY = 112  # Supply flow (32-bit)
REG_INTENSIVE_FAN_EXTRACT = 114  # Extract flow (32-bit)
REG_INTENSIVE_TEMP = 116  # Setpoint
REG_INTENSIVE_HEATER = 117  # Electric heater

# Boost mode registers
REG_BOOST_FAN_SUPPLY = 118  # Supply flow (32-bit)
REG_BOOST_FAN_EXTRACT = 120  # Extract flow (32-bit)
REG_BOOST_TEMP = 122  # Setpoint
REG_BOOST_HEATER = 123  # Electric heater

# Kitchen mode registers
REG_KITCHEN_SUPPLY = 124  # Supply flow (32-bit)
REG_KITCHEN_EXTRACT = 126  # Extract flow (32-bit)
REG_KITCHEN_TEMP = 128  # Setpoint
REG_KITCHEN_HEATER = 129  # Electric heater
REG_KITCHEN_TIMER = 130  # Timer time

# Fireplace mode registers
REG_FIREPLACE_SUPPLY = 131  # Supply flow (32-bit)
REG_FIREPLACE_EXTRACT = 133  # Extract flow (32-bit)
REG_FIREPLACE_TEMP = 135  # Setpoint
REG_FIREPLACE_HEATER = 136  # Electric heater
REG_FIREPLACE_TIMER = 137  # Timer time

# Override mode registers
REG_OVERRIDE_SUPPLY = 138  # Supply flow (32-bit)
REG_OVERRIDE_EXTRACT = 140  # Extract flow (32-bit)
REG_OVERRIDE_TEMP = 142  # Setpoint
REG_OVERRIDE_HEATER = 143  # Electric heater
REG_OVERRIDE_ACTIVATION = 144  # Activation mode
REG_OVERRIDE_TIMER = 145  # Timer time
REG_OVERRIDE_DELAY_START = 157  # Delayed start time (0-10 minutes)
REG_OVERRIDE_DELAY_STOP = 158  # Delayed stop time (0-30 minutes)

# Holiday mode registers
REG_HOLIDAYS_MICRO_VENT = 146  # Micro-ventilation
REG_HOLIDAYS_TEMP = 147  # Setpoint
REG_HOLIDAYS_HEATER = 148  # Electric heater
REG_HOLIDAYS_FROM = 149  # From Day/Month
REG_HOLIDAYS_UNTIL = 151  # Until Day/Month
REG_HOLIDAYS_YEAR_FROM = 153  # Year, from
REG_HOLIDAYS_DATE_FROM = 154  # Month/Day, from
REG_HOLIDAYS_YEAR_TILL = 155  # Year, until
REG_HOLIDAYS_DATE_TILL = 156  # Month/Day, until

# ECO settings
REG_ECO_MIN_TEMP = 200  # Minimum supply air temperature
REG_ECO_MAX_TEMP = 201  # Maximum supply air temperature
REG_ECO_FREE_HEAT_COOL = 202  # Free heating/cooling
REG_ECO_HEATER_BLOCKING = 203  # Heating denied
REG_ECO_COOLER_BLOCKING = 204  # Cooling denied
REG_ECO_HEAT_RECOVERY = 217  # Heat recovery control mode

# Air quality settings
REG_AQ_IMPURITY_CONTROL = 205  # Impurity control
REG_AQ_TEMP_SETPOINT = 206  # Temperature setpoint
REG_AQ_IMPURITY_SETPOINT = 207  # CO2/VOC setpoint
REG_AQ_HUMIDITY_SETPOINT = 208  # Humidity setpoint
REG_AQ_MIN_INTENSITY = 209  # Air quality minimum intensity
REG_AQ_MAX_INTENSITY = 210  # Air quality maximum intensity
REG_AQ_ELECTRIC_HEATER = 211  # Air quality electric heater
REG_AQ_CHECK_PERIOD = 212  # Air quality check period
REG_AQ_SENSOR1_TYPE = 213  # Air quality sensor 1 type
REG_AQ_SENSOR2_TYPE = 214  # Air quality sensor 2 type
REG_AQ_HUMIDITY_CONTROL = 215  # Humidity control (undocumented for C6)
REG_AQ_OUTDOOR_HUMIDITY = 216  # Outdoor humidity sensor (undocumented for C6)

# Alarm registers
REG_ACTIVE_ALARMS_COUNT = (
    600  # Active alarms count (write 0x99C6 to reset and restore previous mode)
)
REG_ACTIVE_ALARM1 = 601  # Active alarm 1 code
REG_ACTIVE_ALARM2 = 602  # Active alarm 2 code
REG_ACTIVE_ALARM3 = 603  # Active alarm 3 code
REG_ACTIVE_ALARM4 = 604  # Active alarm 4 code
REG_ACTIVE_ALARM5 = 605  # Active alarm 5 code
REG_ACTIVE_ALARM6 = 606  # Active alarm 6 code
REG_ACTIVE_ALARM7 = 607  # Active alarm 7 code
REG_ACTIVE_ALARM8 = 608  # Active alarm 8 code
REG_ACTIVE_ALARM9 = 609  # Active alarm 9 code
REG_ACTIVE_ALARM10 = 610  # Active alarm 10 code

# Sensor registers
# Unit status bitmask values:
# Starting=0, Stopping=1, Fan=2, Rotor=3, Heating=4, Cooling=5,
# HeatingDenied=6, CoolingDenied=7, FlowDown=8, FreeHeating=9,
# FreeCooling=10, AlarmF=11, AlarmW=12
REG_STATUS = 900  # Unit status bitmask
REG_HEATING_CONFIG = 901  # Heating/cooling config
REG_SUPPLY_TEMP = 902  # Supply air temperature (x10 °C)
REG_EXTRACT_TEMP = 903  # Extract air temperature (x10 °C)
REG_OUTDOOR_TEMP = 904  # Outdoor air temperature (x10 °C)
REG_WATER_TEMP = 905  # Water temperature (x10 °C)
REG_SUPPLY_FLOW = 906  # Supply air flow (32-bit)
REG_EXTRACT_FLOW = 908  # Extract air flow (32-bit)
REG_SUPPLY_FAN = 910  # Supply fan speed
REG_EXTRACT_FAN = 911  # Extract fan speed
REG_HEAT_EXCHANGER = 912  # Heat exchanger signal
REG_ELECTRIC_HEATER = 913  # Electric heater signal (x10 %)
REG_WATER_HEATER = 914  # Water heater signal
REG_WATER_COOLER = 915  # Water cooler signal
REG_DX_UNIT = 916  # DX unit signal
REG_FILTER_CLOGGING = 917  # Filter clogging
REG_AIR_DAMPERS = 918  # Air dampers
REG_SUPPLY_PRESSURE = 919  # Supply pressure
REG_EXTRACT_PRESSURE = 920  # Extract pressure
REG_EXTRACT_AQ_1 = 952  # Air quality sensor 1 value
REG_EXTRACT_AQ_2 = 953  # Air quality sensor 2 value
REG_HEAT_EXCHANGER_TYPE = 955  # Heat exchanger type
REG_INDOOR_ABS_HUMIDITY = 956  # Indoor absolute humidity (undocumented for C6)
REG_OUTDOOR_ABS_HUMIDITY = 957  # Outdoor absolute humidity (undocumented for C6)
REG_EXHAUST_TEMP = 961  # Exhaust temperature

# Efficiency status
REG_POWER_CONSUMPTION = 921  # Power consumption
REG_HEATER_POWER = 922  # Heater power
REG_HEAT_RECOVERY = 923  # Heat recovery
REG_HEAT_EFFICIENCY = 924  # Heat exchanger efficiency
REG_ENERGY_SAVING = 925  # Energy saving
REG_SPI = 926  # Specific power input

# Consumption registers
REG_AHU_DAY = 927  # AHU consumption Day (32-bit)
REG_AHU_MONTH = 929  # AHU consumption Month (32-bit)
REG_AHU_TOTAL = 931  # AHU consumption Total (32-bit)
REG_HEATER_DAY = 933  # Additional heater Day (32-bit)
REG_HEATER_MONTH = 935  # Additional heater Month (32-bit)
REG_HEATER_TOTAL = 937  # Additional heater Total (32-bit)
REG_RECOVERY_DAY = 939  # Recovered energy Day (32-bit)
REG_RECOVERY_MONTH = 941  # Recovered energy Month (32-bit)
REG_RECOVERY_TOTAL = 943  # Recovered energy Total (32-bit)
REG_SPI_DAY = 945  # SPI per day

# Panel sensor registers
REG_PANEL1_TEMP = 946  # Panel 1 temperature
REG_PANEL1_RH = 947  # Panel 1 relative humidity
REG_PANEL1_AQ = 948  # Panel 1 air quality
REG_PANEL2_TEMP = 949  # Panel 2 temperature
REG_PANEL2_RH = 950  # Panel 2 relative humidity
REG_PANEL2_AQ = 951  # Panel 2 air quality
REG_CONNECTED_PANELS = 954  # Connected panels

# Digital Outputs
REG_DO_ALARM = 958  # Digital Output: Alarm
REG_DO_HEATING = 959  # Digital Output: Heating
REG_DO_COOLING = 960  # Digital Output: Cooling

# Firmware registers
REG_FIRMWARE = 1000  # Firmware version (32-bit)
REG_PANEL1_FW = 1002  # Panel 1 firmware version (32-bit)
REG_PANEL2_FW = 1004  # Panel 2 firmware version (32-bit)

# Reset register
REG_RESET_SETTINGS = 1050  # Reset settings
REG_CLEAN_FILTERS = 1051  # Clean filters calibration

# Sets of 16-bit and 32-bit registers
REGISTERS_16BIT_UNSIGNED = {
    REG_POWER,
    REG_AUTO_MODE_CONTROL,
    REG_ECO_MODE,
    REG_AUTO_MODE,
    REG_OPERATION_MODE,
    REG_SCHEDULER_MODE,
    REG_NEXT_MODE,
    REG_NEXT_MODE_TIME,
    REG_NEXT_MODE_WEEKDAY,
    REG_BEFORE_MODE_MASK,
    REG_TEMP_CONTROL,
    REG_FLOW_CONTROL,
    REG_MAX_SUPPLY_PRESSURE,
    REG_MAX_EXTRACT_PRESSURE,
    REG_ROOM_SENSOR,
    REG_STAGE1,
    REG_STAGE2,
    REG_STAGE3,
    REG_EXTERNAL_COIL_TYPE,
    REG_ICING_PROTECTION,
    REG_INDOOR_HUMIDITY,
    REG_DHCP,
    REG_BACNET_ID,
    REG_BACNET_PORT,
    REG_LANGUAGE,
    REG_FLOW_UNIT,
    REG_FIRE_ALARM_RESTART,
    REG_TIME,
    REG_YEAR,
    REG_MONTH_DAY,
    REG_WEEK_DAY,
    REG_AWAY_HEATER,
    REG_NORMAL_HEATER,
    REG_INTENSIVE_HEATER,
    REG_BOOST_HEATER,
    REG_KITCHEN_HEATER,
    REG_KITCHEN_TIMER,
    REG_FIREPLACE_HEATER,
    REG_FIREPLACE_TIMER,
    REG_OVERRIDE_HEATER,
    REG_OVERRIDE_ACTIVATION,
    REG_OVERRIDE_ACTIVATION,
    REG_OVERRIDE_TIMER,
    REG_OVERRIDE_DELAY_START,
    REG_OVERRIDE_DELAY_STOP,
    REG_HOLIDAYS_MICRO_VENT,
    REG_HOLIDAYS_HEATER,
    REG_HOLIDAYS_YEAR_FROM,
    REG_HOLIDAYS_DATE_FROM,
    REG_HOLIDAYS_YEAR_TILL,
    REG_HOLIDAYS_DATE_TILL,
    REG_ECO_MIN_TEMP,
    REG_ECO_MAX_TEMP,
    REG_ECO_FREE_HEAT_COOL,
    REG_ECO_HEATER_BLOCKING,
    REG_ECO_COOLER_BLOCKING,
    REG_AQ_IMPURITY_CONTROL,
    REG_AQ_IMPURITY_SETPOINT,
    REG_AQ_HUMIDITY_SETPOINT,
    REG_AQ_MIN_INTENSITY,
    REG_AQ_MAX_INTENSITY,
    REG_AQ_ELECTRIC_HEATER,
    REG_AQ_CHECK_PERIOD,
    REG_AQ_SENSOR1_TYPE,
    REG_AQ_SENSOR2_TYPE,
    REG_AQ_HUMIDITY_CONTROL,
    REG_AQ_OUTDOOR_HUMIDITY,
    REG_ECO_HEAT_RECOVERY,
    REG_ACTIVE_ALARMS_COUNT,
    REG_ACTIVE_ALARM1,
    REG_ACTIVE_ALARM2,
    REG_ACTIVE_ALARM3,
    REG_ACTIVE_ALARM4,
    REG_ACTIVE_ALARM5,
    REG_ACTIVE_ALARM6,
    REG_ACTIVE_ALARM7,
    REG_ACTIVE_ALARM8,
    REG_ACTIVE_ALARM9,
    REG_ACTIVE_ALARM10,
    REG_STATUS,
    REG_HEATING_CONFIG,
    REG_SUPPLY_FAN,
    REG_EXTRACT_FAN,
    REG_HEAT_EXCHANGER,
    REG_ELECTRIC_HEATER,
    REG_WATER_HEATER,
    REG_WATER_COOLER,
    REG_FILTER_CLOGGING,
    REG_AIR_DAMPERS,
    REG_SUPPLY_PRESSURE,
    REG_EXTRACT_PRESSURE,
    REG_POWER_CONSUMPTION,
    REG_HEATER_POWER,
    REG_HEAT_RECOVERY,
    REG_HEAT_EFFICIENCY,
    REG_ENERGY_SAVING,
    REG_SPI,
    REG_SPI_DAY,
    REG_PANEL1_AQ,
    REG_PANEL2_AQ,
    REG_EXTRACT_AQ_1,
    REG_EXTRACT_AQ_2,
    REG_CONNECTED_PANELS,
    REG_HEAT_EXCHANGER_TYPE,
    REG_INDOOR_ABS_HUMIDITY,
    REG_OUTDOOR_ABS_HUMIDITY,
    REG_DO_ALARM,
    REG_DO_HEATING,
    REG_DO_COOLING,
    REG_RESET_SETTINGS,
    REG_CLEAN_FILTERS,
}
REGISTERS_16BIT_SIGNED = {
    REG_AWAY_TEMP,
    REG_NORMAL_SETPOINT,
    REG_INTENSIVE_TEMP,
    REG_BOOST_TEMP,
    REG_KITCHEN_TEMP,
    REG_FIREPLACE_TEMP,
    REG_OVERRIDE_TEMP,
    REG_HOLIDAYS_TEMP,
    REG_AQ_TEMP_SETPOINT,
    REG_SUPPLY_TEMP,
    REG_EXTRACT_TEMP,
    REG_OUTDOOR_TEMP,
    REG_WATER_TEMP,
    REG_DX_UNIT,
    REG_PANEL1_TEMP,
    REG_PANEL1_RH,
    REG_PANEL2_TEMP,
    REG_PANEL2_RH,
    REG_EXHAUST_TEMP,
}
REGISTERS_32BIT_UNSIGNED = {
    REG_MAX_SUPPLY_FLOW,
    REG_MAX_EXTRACT_FLOW,
    REG_IP,
    REG_MASK,
    REG_GATEWAY,
    REG_EPOCH_TIME,
    REG_AWAY_FAN_SUPPLY,
    REG_AWAY_FAN_EXTRACT,
    REG_NORMAL_FAN_SUPPLY,
    REG_NORMAL_FAN_EXTRACT,
    REG_INTENSIVE_FAN_SUPPLY,
    REG_INTENSIVE_FAN_EXTRACT,
    REG_BOOST_FAN_SUPPLY,
    REG_BOOST_FAN_EXTRACT,
    REG_KITCHEN_SUPPLY,
    REG_KITCHEN_EXTRACT,
    REG_FIREPLACE_SUPPLY,
    REG_FIREPLACE_EXTRACT,
    REG_OVERRIDE_SUPPLY,
    REG_OVERRIDE_EXTRACT,
    REG_HOLIDAYS_FROM,
    REG_HOLIDAYS_UNTIL,
    REG_SUPPLY_FLOW,
    REG_EXTRACT_FLOW,
    REG_AHU_DAY,
    REG_AHU_MONTH,
    REG_AHU_TOTAL,
    REG_HEATER_DAY,
    REG_HEATER_MONTH,
    REG_HEATER_TOTAL,
    REG_RECOVERY_DAY,
    REG_RECOVERY_MONTH,
    REG_RECOVERY_TOTAL,
    REG_FIRMWARE,
    REG_PANEL1_FW,
    REG_PANEL2_FW,
}
