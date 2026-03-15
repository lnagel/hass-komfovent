# Unimplemented Registers

| Block                        | Register number | Register name                      | Access | DataType       | DataRange                        | Values and Units                                                                                                                                                                                                                                                                                                     |
|------------------------------|-----------------|------------------------------------|--------|----------------|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Detailed information         | 901             | Heating/cooling config             | RO     | unsigned char  | 0 - 7                            | Electric heater => 0 bit, Water cooler/heater => 1 bit, DX unit => 2 bit                                                                                                                                                                                                                                             |
| Digital Outputs              | 958             | Alarm                              | RO     | unsigned char  | 0 - 1                            | Off = 0, On = 1                                                                                                                                                                                                                                                                                                      |
| Digital Outputs              | 959             | Heating                            | RO     | unsigned char  | 0 - 1                            | Off = 0, On = 1                                                                                                                                                                                                                                                                                                      |
| Digital Outputs              | 960             | Cooling                            | RO     | unsigned char  | 0 - 1                            | Off = 0, On = 1                                                                                                                                                                                                                                                                                                      |

## Notes

### Heating/cooling config (901)
Read-only bitmask reflecting which heating/cooling components are currently
enabled in the control sequence configuration (registers 19-21 Stage 1/2/3).
The data is already being read by the coordinator but no entity exposes it.
Potentially redundant since the same information is available through the
Stage 1/2/3 select entities.

### Digital Outputs (958-960)
Alarm, Heating, and Cooling digital output states. These are redundant with
the status bitmask (register 900) which already provides Heating (bit 4),
Cooling (bit 5), AlarmF (bit 11), and AlarmW (bit 12) as binary sensors.
