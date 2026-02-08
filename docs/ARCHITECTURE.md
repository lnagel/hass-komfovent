# Architecture Guide

Quick reference for developers and AI agents working on this Home Assistant Komfovent integration.

## Data Flow

```
Komfovent Device (Modbus TCP)
         │
         ▼
┌─────────────────────────┐
│  KomfoventModbusClient  │  modbus.py - Raw register I/O, type conversion
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  KomfoventCoordinator   │  coordinator.py - Polling, EMA filtering, state
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Entity Platforms       │  sensor.py, climate.py, switch.py, etc.
└────────────┬────────────┘
             ▼
      Home Assistant
```

## Core Components

| File | Purpose |
|------|---------|
| `modbus.py` | Async Modbus client with auto-reconnect, handles 16/32-bit signed/unsigned |
| `coordinator.py` | DataUpdateCoordinator - polls registers, applies EMA smoothing |
| `registers.py` | All register definitions: addresses, types, EMA eligibility |
| `const.py` | Enums (Controller, OperationMode), constants, configuration keys |
| `helpers.py` | Device info builder, version parsing utilities |
| `services.py` | HA service handlers (set_operation_mode, clean_filters_calibration) |

## Register System

Registers are the central abstraction. Defined in `registers.py`:

```python
REGISTERS_16BIT_UNSIGNED = {REG_POWER_ON, REG_OPERATION_MODE, ...}
REGISTERS_16BIT_SIGNED = {REG_SUPPLY_TEMP, REG_EXTRACT_TEMP, ...}
REGISTERS_32BIT_UNSIGNED = {REG_SUPPLY_FLOW, REG_EXTRACT_FLOW, ...}
REGISTERS_APPLY_EMA = {REG_SUPPLY_TEMP, REG_HUMIDITY, ...}  # Smoothed readings
```

The coordinator fetches registers in optimized blocks (1-34, 100-158, 200-217, 900-957, 1000-1005).

## Entity Pattern

All entities follow the CoordinatorEntity pattern:

```python
class KomfoventSensor(CoordinatorEntity["KomfoventCoordinator"], SensorEntity):
    def __init__(self, coordinator, register_id, description):
        super().__init__(coordinator)
        self.register_id = register_id
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.register_id)
```

**Key points:**
- Entities subscribe to coordinator updates automatically
- `native_value` reads from `coordinator.data[register_id]`
- Write operations use `coordinator.client.write_register()`

## Controller Types

Three controller types with different feature sets:

| Controller | Features |
|------------|----------|
| C6 | Full feature set: flow units, SPI sensors, energy counters |
| C6M | Same as C6 |
| C8 | Subset of features, different register availability |

Detection happens in `coordinator.py` by parsing the firmware version register.

## Platform Overview

| Platform | Entities | Notes |
|----------|----------|-------|
| `sensor.py` | ~50+ sensors | Temperatures, flows, pressures, status values |
| `binary_sensor.py` | ~10 sensors | Status bitmask extraction (heating, cooling, alarms) |
| `climate.py` | 1 entity | HVAC control with preset modes |
| `switch.py` | ~13 switches | Power, ECO mode, air quality controls |
| `select.py` | ~8 selects | Operation mode, scheduler, control type |
| `number.py` | ~40+ numbers | Setpoints, timers, thresholds |
| `button.py` | 2 buttons | Set time, filter calibration |
| `datetime.py` | 2 entities | Holiday period dates |

## Value Transformations

Common patterns in sensor subclasses:

| Class | Transform | Example |
|-------|-----------|---------|
| `FloatX10Sensor` | `value / 10` | Temperatures (250 → 25.0°C) |
| `FloatX100Sensor` | `value / 100` | Pressure (1234 → 12.34 Pa) |
| `DutyCycleSensor` | `value` | 0-100% direct |
| `VersionSensor` | Bit parsing | Firmware version extraction |

## Adding New Functionality

### New Sensor
1. Add register constant to `registers.py`
2. Add to appropriate type set (`REGISTERS_16BIT_UNSIGNED`, etc.)
3. Create `SensorEntityDescription` in `sensor.py`
4. Add to entity creation in `async_setup_entry()`

### New Switch/Select/Number
Same pattern: register → description → entity creation.

### Controller-Specific Logic
```python
if coordinator.controller in {Controller.C6, Controller.C6M}:
    # C6/C6M specific code
```

## Key Files by Size

| File | Lines | Complexity |
|------|-------|------------|
| `sensor.py` | ~1000 | High - many sensor types |
| `number.py` | ~700 | Medium - many adjustable params |
| `registers.py` | ~400 | Low - just definitions |
| `switch.py` | ~270 | Low |
| `select.py` | ~280 | Low |
| `binary_sensor.py` | ~250 | Low |
| `climate.py` | ~230 | Medium - multi-register reads |
| `coordinator.py` | ~220 | Medium - core logic |
