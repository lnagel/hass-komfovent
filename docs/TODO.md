# Unimplemented Registers

Registers that are read by the coordinator but not yet exposed as Home Assistant entities.

| Block                        | Register number | Register name                      | Access | DataType       | DataRange                        | Values and Units                                                                                                                                                                                                                                                                                                     |
|------------------------------|-----------------|------------------------------------|--------|----------------|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Settings                     | 27              | Language                           | R/W    | unsigned char  | 0-255                            | English = 0, Lithuanian = 1, Russian = 2, ...                                                                                                                                                                                                                                                                        |
| Detailed information         | 901             | Heating/cooling config             | RO     | unsigned char  | 0 - 7                            | Electric heater => 0 bit, Water cooler/heater => 1 bit, DX unit => 2 bit                                                                                                                                                                                                                                             |
| Detailed information         | 905             | Water temperature                  | RO     | signed short   | \-500 - 1200                     | x10 C                                                                                                                                                                                                                                                                                                                |
| Consumption                  | 927-928         | AHU consumption, Day               | RO     | unsigned int   | 0 - 4294967296                   | Wh                                                                                                                                                                                                                                                                                                                   |
| Consumption                  | 929-930         | AHU consumption, Month             | RO     | unsigned int   | 0 - 4294967296                   | Wh                                                                                                                                                                                                                                                                                                                   |
| Consumption                  | 933-934         | Add. air heater consumption, Day   | RO     | unsigned int   | 0 - 4294967296                   | Wh                                                                                                                                                                                                                                                                                                                   |
| Consumption                  | 935-936         | Add. air heater consumption, Month | RO     | unsigned int   | 0 - 4294967296                   | Wh                                                                                                                                                                                                                                                                                                                   |
| Consumption                  | 939-940         | Recovered energy, Day              | RO     | unsigned int   | 0 - 4294967296                   | Wh                                                                                                                                                                                                                                                                                                                   |
| Consumption                  | 941-942         | Recovered energy, Month            | RO     | unsigned int   | 0 - 4294967296                   | Wh                                                                                                                                                                                                                                                                                                                   |
| Panel                        | 948             | Panel 1 air quality                | RO     | unsigned short | 0 - 65535                        | ppm, ppb                                                                                                                                                                                                                                                                                                             |
| Panel                        | 951             | Panel 2 air quality                | RO     | unsigned short | 0 - 65535                        | ppm, ppb                                                                                                                                                                                                                                                                                                             |
| Digital Outputs              | 958             | Alarm                              | RO     | unsigned char  | 0 - 1                            | Off = 0, On = 1                                                                                                                                                                                                                                                                                                      |
| Digital Outputs              | 959             | Heating                            | RO     | unsigned char  | 0 - 1                            | Off = 0, On = 1                                                                                                                                                                                                                                                                                                      |
| Digital Outputs              | 960             | Cooling                            | RO     | unsigned char  | 0 - 1                            | Off = 0, On = 1                                                                                                                                                                                                                                                                                                      |

## Notes

### Language (27)
Panel display language. Could be exposed as a select entity to allow
changing the panel language from Home Assistant.

### Heating/cooling config (901)
Read-only bitmask reflecting which heating/cooling components are currently
enabled in the control sequence configuration (registers 19-21 Stage 1/2/3).
The data is already being read by the coordinator but no entity exposes it.
Potentially redundant since the same information is available through the
Stage 1/2/3 select entities.

### Water temperature (905)
Water heater return water temperature.

### Daily / monthly energy counters (927-928, 929-930, 933-934, 935-936, 939-940, 941-942)
AHU, additional heater, and recovered energy consumption for the current
day and month. Only the lifetime totals (931, 937, 943) are currently
exposed. The daily/monthly counters reset on the device.

### Panel air quality (948, 951)
Panel-mounted air quality sensor readings. C6 (documented in
`docs/MODBUS_C6.md`). Gate behind `REG_CONNECTED_PANELS` like the existing
panel temperature/humidity sensors.

### Digital Outputs (958-960)
Alarm, Heating, and Cooling digital output states. These are redundant with
the status bitmask (register 900) which already provides Heating (bit 4),
Cooling (bit 5), AlarmF (bit 11), and AlarmW (bit 12) as binary sensors.
Note: not currently read by the coordinator (the 900-block read stops at
957 and resumes at 961).