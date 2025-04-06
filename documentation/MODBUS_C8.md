The key differences between C6 and C8 controllers include:

* Flow Control: The C8 controller doesn't have flow control mode and flow units registers that are present in C6/C6M.
* Humidity Control: C8 has enhanced humidity control with dedicated registers for humidity setpoints for each operation mode and absolute humidity measurements.
* Control Sequence: C6/C6M supports three stages in control sequence, while C8 only has two.
* Energy vs. Time Monitoring: C6/C6M focuses on energy consumption metrics, while C8 emphasizes operation time counters for various components.
* Air Quality Sensors: C6/C6M supports two air quality sensors (B8 and B9), while C8 only supports one (B8).
* Register Interpretation: Flow values in C6/C6M can be in m³/h, l/s, Pa, or % depending on the flow control mode, while in C8 they are exclusively in percentage.
* Additional Features: C8 adds dehumidification with DX unit capability.
* Alarm Differences: C8 has fewer alarm codes defined in the documentation.
