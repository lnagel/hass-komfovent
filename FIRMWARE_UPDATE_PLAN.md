# Firmware Update Implementation Plan

## Overview

This document outlines the implementation plan for adding firmware update capabilities to the Komfovent Home Assistant integration. The feature enables single-click firmware updates from the Home Assistant UI.

**Protocol Documentation:** See [`documentation/C6-firmware-upload.md`](documentation/C6-firmware-upload.md) for detailed HTTP protocol analysis based on packet captures.

## Supported Controllers

| Controller | Firmware | Support |
|------------|----------|---------|
| C6/C6M | v1.3.15+ (.mbin) | Supported |
| C6/C6M | < v1.3.15 (.bin) | **Not supported** - requires manual update first |
| C8 | TBD | Not yet implemented |

Controllers with firmware older than v1.3.15 must be manually updated to a newer version before using this integration's update feature.

## Architecture

### New Files

```
custom_components/komfovent/
├── update.py        # KomfoventUpdateEntity (UpdateEntity)
└── firmware.py      # FirmwareManager (download/upload logic)
```

### Core Classes

**`KomfoventCoordinator`** (existing, extended)
- Triggers weekly firmware version check via FirmwareManager
- Stores firmware check results in coordinator data
- Exposes `latest_firmware` in state for entities to read

**`FirmwareManager`** - Firmware operations
- Check latest version (streaming GET, abort after headers)
- Download firmware from manufacturer to HA storage
- Login and upload firmware to device
- Version verification after restart

**`KomfoventUpdateEntity`** - Home Assistant update entity (display only)
- Reads installed version from coordinator data (Modbus)
- Reads latest version from coordinator data (firmware check results)
- Triggers install action via FirmwareManager
- Displays progress during download/upload

### Firmware Caching

Downloaded firmware is cached in Home Assistant storage to avoid re-downloading for multi-device setups or retries.

**Coordinator Permanent State:**
```python
{
    "firmware_cache": {
        "last_checked_at": "2025-01-21T10:00:00Z",  # ISO timestamp
        "filename": "C6_1_5_46_72_P1_1_1_5_48.mbin",
        "controller_version": ("C6", 1, 5, 46, 72),
        "panel_version": ("P1", 1, 1, 5, 48),
        "file_path": "/config/.storage/komfovent/C6_1_5_46_72_P1_1_1_5_48.mbin"
    }
}
```

**Version Format:** Versions are 5-tuples `(model, v1, v2, v3, v4)` matching the integration's `get_version_from_int()` format for comparison.

**Storage Location:** `.storage/komfovent/` directory in HA config.

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

### Phase 1: Version Detection

**Goal:** Coordinator periodically checks for latest firmware version.

**Note:** HEAD requests don't return `Content-Disposition` from the PHP endpoint. Must use streaming GET and abort after reading headers.

**Tasks:**
- [ ] Create `FirmwareManager` class with `async_check_latest_version()`
- [ ] Implement streaming GET request to manufacturer URL (abort after headers)
- [ ] Parse version from `Content-Disposition` header filename
- [ ] Support both modern and legacy filename patterns
- [ ] Extend coordinator to trigger weekly firmware checks
- [ ] Store version info in coordinator data (`latest_firmware` key)
- [ ] Create `KomfoventUpdateEntity` reading from coordinator state
- [ ] Show "not supported" for controllers < v1.3.15

### Phase 2: Download and Upload

**Goal:** Single-click firmware updates via FirmwareManager.

**Tasks:**
- [ ] Implement `FirmwareManager.async_download_firmware()` with progress
- [ ] Save firmware to HA storage (`.storage/komfovent/`)
- [ ] Store file metadata in coordinator permanent state
- [ ] Validate downloaded file (extension, size, signature)
- [ ] Implement `FirmwareManager.async_upload_firmware()` with login
- [ ] Handle slow TCP transfer (~57s for 1MB)
- [ ] Wait for device restart (1-2 minutes)
- [ ] Verify new version via Modbus
- [ ] Update entity calls FirmwareManager, displays progress

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
# tests/test_firmware.py
async def test_parse_version_from_modern_filename()
async def test_parse_version_from_legacy_filename()
async def test_check_latest_version()
async def test_download_firmware()
async def test_upload_firmware()
async def test_firmware_caching()

# tests/test_update.py
def test_installed_version_from_modbus()
def test_update_available_detection()
def test_unsupported_old_firmware()
```

## Files to Modify

| File | Changes |
|------|---------|
| `custom_components/komfovent/update.py` | NEW - Update entity |
| `custom_components/komfovent/firmware.py` | NEW - Firmware manager |
| `custom_components/komfovent/__init__.py` | Add Platform.UPDATE |
| `custom_components/komfovent/const.py` | Add firmware constants |
| `custom_components/komfovent/coordinator.py` | Add firmware cache to permanent state |

## Security Considerations

- Validate file extension (`.mbin` only)
- Check file size range (100KB - 10MB)
- Verify filename pattern matches expected format
- Don't expose credentials in logs
- Store firmware in HA's protected `.storage/` directory

## References

- [Protocol Documentation](documentation/C6-firmware-upload.md) - HTTP protocol analysis
- [C6 Update Instructions (PDF)](https://www.komfovent.com/en/downloads/C6_update_EN.pdf) - Manufacturer guide
- [Home Assistant Update Entity](https://developers.home-assistant.io/docs/core/entity/update/) - HA documentation
