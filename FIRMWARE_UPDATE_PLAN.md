# Firmware Update Implementation Plan

## Overview

This document outlines the implementation plan for adding firmware update capabilities to the Komfovent Home Assistant integration. The feature enables single-click firmware updates from the Home Assistant UI.

**Protocol Documentation:** See [`documentation/C6-firmware-upload.md`](documentation/C6-firmware-upload.md) for detailed HTTP protocol analysis based on packet captures.

## Supported Controllers

| Controller | Firmware | Support |
|------------|----------|---------|
| C6/C6M | v1.3.15+ (.mbin) | Supported |
| C6/C6M | < v1.3.15 (.bin) | **Not supported** - requires manual update first |
| C8 | All versions (.mbin) | Supported |

Controllers with firmware older than v1.3.15 must be manually updated to a newer version before using this integration's update feature.

**Documentation:**
- [C6 Update Instructions (PDF)](documentation/C6_update_EN.pdf)
- [C8 Update Instructions (PDF)](documentation/C8_update_EN.pdf)

## Architecture

### New Files

```
custom_components/komfovent/
├── firmware/
│   ├── __init__.py       # Package exports
│   ├── store.py          # FirmwareStore (HA Store API)
│   ├── checker.py        # FirmwareChecker (scheduled HTTP)
│   └── uploader.py       # FirmwareUploader (device HTTP)
├── update.py             # KomfoventUpdateEntity
```

### Core Classes

**KomfoventCoordinator** (existing, unchanged)
- Polls Modbus registers every 30 seconds
- Provides installed firmware version via `self.data[REG_FIRMWARE]`
- NOT responsible for firmware checks or caching

**FirmwareStore** - Persistent storage
- Uses `homeassistant.helpers.storage.Store` API
- Persists to `.storage/komfovent_firmware.json`
- Stores: `last_checked_at`, `latest_version`, `filename`, `file_path`

**FirmwareChecker** - Scheduled firmware checks
- Uses `async_track_time_interval` for weekly checks
- Downloads firmware from manufacturer
- Updates FirmwareStore with metadata
- Saves binary to `.storage/komfovent/`

**FirmwareUploader** - Device firmware upload
- Stateless HTTP client
- Login, upload, logout operations
- Used by UpdateEntity during install

**KomfoventUpdateEntity** - Home Assistant update entity
- `installed_version`: reads from `coordinator.data` (Modbus)
- `latest_version`: reads from FirmwareStore
- `async_install`: uses FirmwareUploader

### Data Flow

**Installed Version (Modbus -> Entity)**
```
Device registers 1000-1005
  -> coordinator._async_update_data() (every 30s)
  -> coordinator.data[REG_FIRMWARE]
  -> UpdateEntity.installed_version
```

**Latest Version (HTTP -> Store -> Entity)**
```
Komfovent server (firmware.php)
  -> FirmwareChecker.async_check_for_update() (weekly)
  -> FirmwareStore.async_save()
  -> .storage/komfovent_firmware.json
  -> UpdateEntity.latest_version
```

### Lifecycle Management

**Setup** (`__init__.py async_setup_entry`):
1. Create coordinator (existing)
2. Create FirmwareStore, call `async_load()`
3. Create FirmwareChecker, call `async_start()`
4. Store all in `hass.data[DOMAIN][entry.entry_id]`
5. Register cleanup: `entry.async_on_unload(checker.async_stop)`

**Unload** (`__init__.py async_unload_entry`):
1. `FirmwareChecker.async_stop()` called via `async_on_unload`
2. Remove entry from `hass.data`

### Persistent Storage

Firmware metadata is stored using Home Assistant's Store API:

**Location:** `.storage/komfovent_firmware.json`

**Structure:**
```json
{
    "last_checked_at": "2025-01-21T10:00:00Z",
    "filename": "C6_1_5_46_72_P1_1_1_5_48.mbin",
    "controller_version": [0, 1, 5, 46, 72],
    "panel_version": [0, 1, 1, 5, 48],
    "file_path": "/config/.storage/komfovent/C6_1_5_46_72_P1_1_1_5_48.mbin"
}
```

**Version Format:** Versions are 5-tuples `(enum_value, v1, v2, v3, v4)` matching the helper return types. Enum integers are stored directly (Controller.C6 = 0, Panel.P1 = 0) and loaded via `Controller(value)` / `Panel(value)`.

**Binary Location:** `.storage/komfovent/<filename>.mbin`

**Update Detection:** An update is suggested when either the controller OR panel functional version (v4, last element of the tuple) in the cached firmware is higher than the installed version. Komfovent uses an internal versioning scheme (not semver) where only the functional version determines update eligibility. This ensures panel-only updates are not missed.

### Version Helpers

Rename and split the existing `get_version_from_int()` helper:

**New in `const.py`:**
```python
class Panel(IntEnum):
    """Panel types for firmware versioning."""
    P1 = 0
    NA = 15
```

**Renamed in `helpers.py`:**
```python
def get_controller_version(value: int) -> tuple[Controller, int, int, int, int]:
    """Convert integer to controller version tuple."""
    # Renamed from get_version_from_int()

def get_panel_version(value: int) -> tuple[Panel, int, int, int, int]:
    """Convert integer to panel version tuple."""
    # Same bitfield logic, but returns Panel enum
```

All existing usages of `get_version_from_int()` should be migrated to `get_controller_version()`.

## Firmware Details

### Filename Patterns

| Pattern | Example | Description |
|---------|---------|-------------|
| Modern | `C6_1_5_46_72_P1_1_1_5_48.mbin` | Controller + panel versions |
| Legacy | `C6_1_3_28_38_20180428.mbin` | Controller + build date |

Both patterns use `.mbin` extension for supported firmware.

### Download URL

```
http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin
```

### Upload Protocol

- **Endpoint:** `POST /g1.html`
- **Authentication:** IP-based session with form fields `1` (username) and `2` (password)
- **Upload field:** `11111` (multipart/form-data)
- **Performance:** ~19 KB/s due to 735-byte TCP window (~57s for 1MB file)
- **Processing delay:** 1-2 seconds after upload completes

See protocol documentation for full details.

## Implementation Phases

### Phase 1: Version Detection & Download

**Goal:** FirmwareChecker periodically downloads latest firmware and caches it via FirmwareStore.

**Note:** HEAD requests don't return `Content-Disposition` from the PHP endpoint, so we download the full file and extract version from the response headers.

**Tasks:**
- [ ] Add `Panel` IntEnum to `const.py` (P1, NA)
- [ ] Rename `get_version_from_int()` to `get_controller_version()`, add `get_panel_version()`
- [ ] Migrate all existing usages to `get_controller_version()`
- [ ] Create `firmware/store.py` with FirmwareStore class (HA Store API)
- [ ] Create `firmware/checker.py` with FirmwareChecker class
- [ ] Download firmware, extract version from `Content-Disposition` header
- [ ] Parse version from filename (modern and legacy patterns)
- [ ] Save firmware to HA storage (`.storage/komfovent/`)
- [ ] Store metadata via FirmwareStore
- [ ] Use `async_track_time_interval` for weekly checks
- [ ] Create `KomfoventUpdateEntity` reading from FirmwareStore
- [ ] Show "not supported" for controllers < v1.3.15

### Phase 2: Upload

**Goal:** Single-click firmware upload via FirmwareUploader.

**Tasks:**
- [ ] Create `firmware/uploader.py` with FirmwareUploader class
- [ ] Implement login, upload, logout operations
- [ ] Handle slow TCP transfer (~57s for 1MB)
- [ ] Wait for device restart (1-2 minutes)
- [ ] Verify new version via Modbus
- [ ] UpdateEntity calls FirmwareUploader, displays progress

### Phase 3: Polish

**Goal:** Robust error handling and user experience.

**Tasks:**
- [ ] Detailed progress states (downloading, uploading, restarting)
- [ ] Retry logic with exponential backoff
- [ ] Clear error messages with recovery suggestions
- [ ] Reuse cached firmware if version matches
- [ ] Automatic cleanup of old firmware files

## Testing

### Mock Server

Use `scripts/mock_c6_server.py` to test upload flow without a real device:

```bash
uv run python scripts/mock_c6_server.py
```

The mock server simulates:
- IP-based authentication
- Form field validation (`1`, `2`, `11111`)
- Slow TCP transfer behavior
- Processing delay before response

### Validation Scripts

| Script | Purpose |
|--------|---------|
| `scripts/download_firmware.py` | Test firmware download from manufacturer |
| `scripts/validate_firmware_update.py` | Test complete upload flow |

```bash
# Test download
uv run python scripts/download_firmware.py --output firmware.mbin

# Test upload to mock server
uv run python scripts/validate_firmware_update.py --host localhost:8080 --dry-run
```

### Unit Tests

```python
# tests/test_firmware_store.py
async def test_store_save_and_load()
async def test_store_handles_missing_file()

# tests/test_firmware_checker.py
async def test_parse_version_from_modern_filename()
async def test_parse_version_from_legacy_filename()
async def test_check_for_update()
async def test_weekly_schedule()

# tests/test_firmware_uploader.py
async def test_login()
async def test_upload_firmware()
async def test_logout()

# tests/test_update.py
def test_installed_version_from_modbus()
def test_latest_version_from_store()
def test_update_available_detection()
def test_unsupported_old_firmware()
```

## Files to Modify

| File | Changes |
|------|---------|
| `firmware/store.py` | NEW - FirmwareStore class |
| `firmware/checker.py` | NEW - FirmwareChecker class |
| `firmware/uploader.py` | NEW - FirmwareUploader class |
| `update.py` | NEW - KomfoventUpdateEntity |
| `__init__.py` | Add Platform.UPDATE, setup firmware components |
| `const.py` | Add `Panel` IntEnum, firmware constants |
| `helpers.py` | Rename to `get_controller_version()`, add `get_panel_version()` |
| `coordinator.py` | **No changes** - remains Modbus-only |

## Security Considerations

- Validate file extension (`.mbin` only)
- Check file size range (100KB - 10MB)
- Verify filename pattern matches expected format
- Don't expose credentials in logs
- Store firmware in HA's protected `.storage/` directory

## References

- [Protocol Documentation](documentation/C6-firmware-upload.md) - HTTP protocol analysis
- [C6 Update Instructions (PDF)](documentation/C6_update_EN.pdf) - Manufacturer guide
- [C8 Update Instructions (PDF)](documentation/C8_update_EN.pdf) - Manufacturer guide
- [Home Assistant Update Entity](https://developers.home-assistant.io/docs/core/entity/update/) - HA documentation
- [Home Assistant Store API](https://developers.home-assistant.io/docs/api_lib_storage) - Persistent storage
