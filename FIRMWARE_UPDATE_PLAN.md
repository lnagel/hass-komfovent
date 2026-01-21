# Firmware Update Implementation Plan

## Overview

This document outlines the implementation plan for adding firmware update capabilities to the Komfovent Home Assistant integration. The feature enables single-click firmware updates from the Home Assistant UI.

**Protocol Documentation:** See [`documentation/C6-firmware-upload.md`](documentation/C6-firmware-upload.md) for detailed HTTP protocol analysis based on packet captures.

## Architecture

### New Files

```
custom_components/komfovent/
├── update.py        # KomfoventUpdateEntity (UpdateEntity)
└── firmware.py      # FirmwareManager (download/upload logic)
```

### Core Classes

**`KomfoventUpdateEntity`** - Home Assistant update entity
- Reports installed version from Modbus registers
- Checks manufacturer URL for latest version
- Provides install action for single-click updates
- Tracks progress during download/upload

**`FirmwareManager`** - Firmware operations
- HEAD request to detect latest version
- Download firmware from manufacturer
- Login and upload to device
- Version verification after restart

## Firmware Details

### Filename Patterns

Two firmware filename patterns are used:

| Pattern | Example | Description |
|---------|---------|-------------|
| Modern | `C6_1_5_46_72_P1_1_1_5_48.mbin` | Controller + panel versions |
| Legacy | `C6_1_3_28_38_20180428.mbin` | Controller + build date |

### Download URLs

| Type | URL |
|------|-----|
| MBIN (v1.3.15+) | `http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin` |
| BIN (< v1.3.15) | `http://www.komfovent.com/Update/Controllers/firmware.php?file=bin` |

### Upload Protocol

- **Endpoint:** `POST /g1.html`
- **Authentication:** IP-based session with form fields `1` (username) and `2` (password)
- **Upload field:** `11111` (multipart/form-data)
- **Performance:** ~19 KB/s due to 735-byte TCP window (~57s for 1MB file)
- **Processing delay:** 1-2 seconds after upload completes

See protocol documentation for full details.

## Implementation Phases

### Phase 1: Version Detection

**Goal:** Automatically detect latest firmware version from manufacturer.

**Note:** HEAD requests don't return `Content-Disposition` from the PHP endpoint. Must use GET with streaming and abort after reading headers.

**Tasks:**
- [ ] Create `FirmwareManager` class
- [ ] Implement streaming GET request to manufacturer URL (abort after headers)
- [ ] Parse version from `Content-Disposition` header filename
- [ ] Support both modern and legacy filename patterns
- [ ] Cache version checks (1 hour) to minimize server load
- [ ] Create `KomfoventUpdateEntity` with `installed_version` property
- [ ] Add `latest_version` property from FirmwareManager

### Phase 2: Download and Upload

**Goal:** Single-click firmware updates.

**Tasks:**
- [ ] Implement firmware download with progress tracking
- [ ] Validate downloaded file (extension, size, signature)
- [ ] Implement device login (fields `1` and `2`)
- [ ] Implement firmware upload (field `11111`)
- [ ] Handle slow TCP transfer (~57s for 1MB)
- [ ] Wait for device restart (1-2 minutes)
- [ ] Verify new version via Modbus
- [ ] Clean up temporary files

### Phase 3: Polish

**Goal:** Robust error handling and user experience.

**Tasks:**
- [ ] Detailed progress states (downloading, uploading, restarting)
- [ ] Retry logic with exponential backoff
- [ ] Clear error messages with recovery suggestions
- [ ] Firmware caching for multi-device scenarios
- [ ] Automatic cleanup on failure

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
# Test download (HEAD request for version check)
uv run python scripts/download_firmware.py --type mbin --head-only

# Test download (full file)
uv run python scripts/download_firmware.py --type mbin --output firmware.mbin

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

# tests/test_update.py
def test_installed_version_from_modbus()
def test_update_available_detection()
def test_firmware_type_selection()
```

## Files to Modify

| File | Changes |
|------|---------|
| `custom_components/komfovent/update.py` | NEW - Update entity |
| `custom_components/komfovent/firmware.py` | NEW - Firmware manager |
| `custom_components/komfovent/__init__.py` | Add Platform.UPDATE |
| `custom_components/komfovent/const.py` | Add firmware constants |
| `custom_components/komfovent/manifest.json` | Update if dependencies needed |

## Security Considerations

- Validate file extension (`.bin`, `.mbin`, `.pbin`, `.rbin`, `.cfg`)
- Check file size range (100KB - 10MB)
- Verify filename pattern matches expected format
- Don't expose credentials in logs
- Secure temporary file storage
- Automatic cleanup of downloaded files

## References

- [Protocol Documentation](documentation/C6-firmware-upload.md) - HTTP protocol analysis
- [C6 Update Instructions (PDF)](https://www.komfovent.com/en/downloads/C6_update_EN.pdf) - Manufacturer guide
- [Home Assistant Update Entity](https://developers.home-assistant.io/docs/core/entity/update/) - HA documentation
