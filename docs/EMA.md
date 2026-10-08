# EMA (Exponential Moving Average) Filtering

## Overview

The integration supports optional EMA low-pass filtering for sensor readings to reduce noise and smooth out rapid fluctuations.

## Configuration

In the integration options, set **Measurement averaging time constant** (seconds):
- `0` = Disabled (default shows raw values)
- `30-1800` = Time constant (τ) for the EMA filter

Higher values produce smoother readings but slower response to actual changes.

## How It Works

The EMA filter uses the formula:

```
filtered = α × current + (1 - α) × previous
where α = dt / (τ + dt)
```

- `dt` = time since last update
- `τ` = configured time constant

## Filtered Registers

The following sensor registers have EMA filtering applied:

| Category       | Registers                                                  |
|----------------|------------------------------------------------------------|
| Temperatures   | Supply, Extract, Outdoor, Water, Exhaust, Panel 1, Panel 2 |
| Humidity       | Panel 1 RH, Panel 2 RH, Indoor Absolute, Outdoor Absolute  |
| Air Quality    | Extract AQ 1, Extract AQ 2                                 |
| Heat Exchanger | Signal, Recovery, Efficiency                               |
| Efficiency     | SPI, Energy Saving                                         |
| Pressure       | Supply Pressure, Extract Pressure                          |

## Reset on Flow Change

Flow-dependent measurements step when the fans start or stop. Filtering that
step would show as a slow ramp in history, so on the update where the flow state
changes the filter is skipped for these registers and restarts from the raw
value. Flow presence is taken from the fan bit of the status register (900).

All filtered registers are reset except the panel sensors (Panel 1/2 temperature
and RH), which measure room air and are filtered continuously.

## Implementation

- `core/ema.py` - The `apply_ema()` function
- `coordinator.py` - `_apply_ema_on_update_data()` applies filtering before returning data
- `registers.py` - `REGISTERS_APPLY_EMA` defines which registers to filter and `REGISTERS_EMA_RESET_ON_FLOW_CHANGE` which of them reset
- `helpers.py` - `flow_present()` determines flow presence from the status register
- `config_flow.py` - Options flow for `ema_time_constant` setting