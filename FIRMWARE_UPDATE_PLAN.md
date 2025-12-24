# Komfovent C6/C6M Firmware Update Feature - Development Plan

## Executive Summary

This document outlines the development plan for adding firmware update capabilities to the Komfovent Home Assistant custom component. The implementation will follow Home Assistant best practices and leverage the existing Modbus integration while adding support for firmware version checking and updates through the device's local web interface.

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Requirements](#requirements)
3. [Architecture Overview](#architecture-overview)
4. [Implementation Plan](#implementation-plan)
5. [Testing Strategy](#testing-strategy)
6. [Security Considerations](#security-considerations)
7. [User Experience](#user-experience)
8. [Future Enhancements](#future-enhancements)

---

## Current State Analysis

### Existing Implementation

The Komfovent integration currently includes:

- **Firmware Version Sensor** (`custom_components/komfovent/sensor.py:802`)
  - Reads firmware version from Modbus register 1000 (REG_FIRMWARE)
  - Displays version as "C6 1.3.18.21" format
  - Supports controller, panel 1, and panel 2 firmware versions
  - Uses `get_version_from_int()` helper to parse version from 32-bit integer

- **Version Parsing** (`custom_components/komfovent/helpers.py:8`)
  - Extracts controller type and version numbers from packed integer
  - Format: controller (4bit) + v1 (4bit) + v2 (4bit) + v3 (8bit) + v4 (12bit)
  - Example: 18886660 => C6 1.2.3.4

### Manufacturer Update Process

According to the [C6 firmware update documentation](https://www.komfovent.com/en/downloads/C6_update_EN.pdf):

1. **Manual Process Required:**
   - Stop AHU (Air Handling Unit)
   - Navigate to device web interface at `http://[IP]/g1.html`
   - Upload firmware file (.bin or .mbin depending on current version)
   - Wait 30-60 seconds for upload
   - Wait 1-2 minutes for device restart
   - Verify new firmware version

2. **Firmware File Types:**
   - `.mbin` - For firmware version X.X.X.15 or later
   - `.bin` - For firmware version X.X.X.14 or earlier

3. **Download Sources:**
   - Main firmware: `http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin`
   - Legacy firmware: `http://www.komfovent.com/Update/Controllers/firmware.php?file=bin`
   - **Note:** These URLs are blocked from external access (403 Forbidden)

### Key Findings

✅ **What Works:**
- Current firmware version is already available via Modbus
- Version parsing is implemented and tested
- Device web interface supports firmware upload

❌ **Limitations:**
- Manufacturer firmware URLs are blocked from external access
- No automatic version check mechanism available
- Update requires manual file download and upload
- Device must be stopped before updating

---

## Requirements

### Functional Requirements

#### FR1: Version Check Feature
- [ ] FR1.1: Display current firmware version (already implemented)
- [ ] FR1.2: Show update availability status
- [ ] FR1.3: Provide link to manufacturer download page
- [ ] FR1.4: Display release information when available
- [ ] FR1.5: Support manual version override for latest version

#### FR2: Firmware Update Feature
- [ ] FR2.1: Support firmware file upload through Home Assistant UI
- [ ] FR2.2: Validate firmware file before upload (.bin or .mbin)
- [ ] FR2.3: Upload firmware to device web interface
- [ ] FR2.4: Monitor update progress
- [ ] FR2.5: Verify successful update
- [ ] FR2.6: Handle update failures gracefully
- [ ] FR2.7: Support backup/rollback (if device supports it)

#### FR3: Safety Features
- [ ] FR3.1: Warn user before starting update
- [ ] FR3.2: Check device is idle/stopped before update
- [ ] FR3.3: Prevent updates during critical operations
- [ ] FR3.4: Provide clear error messages
- [ ] FR3.5: Log update attempts and results

### Non-Functional Requirements

#### NFR1: Performance
- Update check should complete within 5 seconds
- Firmware upload should handle files up to 10MB
- Progress indication should update every 5-10 seconds

#### NFR2: Reliability
- Handle network timeouts gracefully
- Retry failed operations (with limits)
- Maintain device state if update fails

#### NFR3: Security
- Use authenticated connections to device
- Validate firmware file integrity
- Don't expose sensitive credentials in logs

#### NFR4: Usability
- Clear status messages throughout process
- Progress indication during upload
- Helpful error messages with recovery steps

---

## Architecture Overview

### Component Structure

```
custom_components/komfovent/
├── __init__.py                 # Add Platform.UPDATE
├── const.py                    # Add update-related constants
├── coordinator.py              # (no changes needed)
├── update.py                   # NEW - Update entity implementation
├── firmware.py                 # NEW - Firmware management module
└── manifest.json               # Update requirements if needed
```

### Class Diagram

```
┌─────────────────────────────────────────────┐
│         KomfoventUpdateEntity               │
│         (UpdateEntity)                      │
├─────────────────────────────────────────────┤
│ - coordinator: KomfoventCoordinator         │
│ - firmware_manager: FirmwareManager         │
├─────────────────────────────────────────────┤
│ + installed_version: str                    │
│ + latest_version: str | None                │
│ + release_url: str                          │
│ + release_summary: str                      │
│ + supported_features: UpdateEntityFeature   │
│                                             │
│ + async_install(version, backup): None     │
│ + async_release_notes(): str               │
└─────────────────────────────────────────────┘
                    │
                    │ uses
                    ▼
┌─────────────────────────────────────────────┐
│          FirmwareManager                    │
├─────────────────────────────────────────────┤
│ - host: str                                 │
│ - username: str                             │
│ - password: str                             │
│ - session: aiohttp.ClientSession            │
├─────────────────────────────────────────────┤
│ + async_login(): bool                       │
│ + async_upload_firmware(file): bool         │
│ + async_check_status(): dict                │
│ + async_verify_version(version): bool       │
└─────────────────────────────────────────────┘
```

### Data Flow

#### Version Check Flow

```
User opens HA → UpdateEntity.installed_version (from Modbus)
                         ↓
                  Check latest version
                  (from user config or external source)
                         ↓
                  Compare versions
                         ↓
                  Display update available/up-to-date
```

#### Firmware Update Flow

```
User clicks Install → Validate firmware file
                           ↓
                    Confirm with user
                           ↓
                    Login to device web interface
                           ↓
                    Upload firmware to /g1.html
                           ↓
                    Monitor upload progress (30-60s)
                           ↓
                    Wait for device restart (1-2min)
                           ↓
                    Verify new firmware version
                           ↓
                    Update entity state
```

---

## Implementation Plan

### Phase 1: Foundation (Version Check Only)

#### Step 1.1: Create Update Entity Structure

**File:** `custom_components/komfovent/update.py`

**Tasks:**
- [ ] Create `KomfoventUpdateEntity` class extending `UpdateEntity`
- [ ] Implement `installed_version` property (read from coordinator)
- [ ] Implement `latest_version` property (initially returns None)
- [ ] Add `release_url` pointing to manufacturer downloads page
- [ ] Set `supported_features` to `UpdateEntityFeature.RELEASE_NOTES`
- [ ] Implement `async_release_notes()` with manufacturer instructions

**Code Structure:**
```python
from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)

class KomfoventUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Komfovent firmware update entity."""

    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    @property
    def installed_version(self) -> str | None:
        """Return the installed firmware version."""
        # Get from coordinator.data[REG_FIRMWARE]
        # Parse using get_version_from_int()

    @property
    def latest_version(self) -> str | None:
        """Return the latest firmware version available."""
        # Phase 1: Return None (manual check)
        # Phase 2: Check configured latest version
        # Phase 3: Auto-check if API available

    @property
    def release_url(self) -> str | None:
        """Return the URL for release notes/download."""
        return "https://www.komfovent.com/en/page/software"

    async def async_release_notes(self) -> str | None:
        """Return the release notes."""
        return (
            "To update firmware:\n"
            "1. Download firmware from Komfovent website\n"
            "2. Upload via device web interface\n"
            f"3. Navigate to http://{self.coordinator.host}/g1.html\n"
        )
```

#### Step 1.2: Update Platform Registration

**File:** `custom_components/komfovent/__init__.py`

**Tasks:**
- [ ] Add `Platform.UPDATE` to `PLATFORMS` list
- [ ] Update `async_setup_entry` if needed

**Code Change:**
```python
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,  # NEW
]
```

#### Step 1.3: Add Update Entity Constants

**File:** `custom_components/komfovent/const.py`

**Tasks:**
- [ ] Add manufacturer firmware URLs (for reference)
- [ ] Add update-related timeouts and limits

**Code:**
```python
# Firmware update
FIRMWARE_UPLOAD_URL = "/g1.html"
FIRMWARE_UPLOAD_TIMEOUT = 120  # seconds
FIRMWARE_RESTART_TIMEOUT = 180  # seconds

# Manufacturer URLs (for reference - blocked from external access)
MANUFACTURER_FIRMWARE_URL_MBIN = "http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin"
MANUFACTURER_FIRMWARE_URL_BIN = "http://www.komfovent.com/Update/Controllers/firmware.php?file=bin"
MANUFACTURER_DOWNLOADS_PAGE = "https://www.komfovent.com/en/page/software"
MANUFACTURER_C6_UPDATE_PDF = "https://www.komfovent.com/en/downloads/C6_update_EN.pdf"
```

#### Step 1.4: Testing Phase 1

**Tasks:**
- [ ] Test update entity appears in Home Assistant
- [ ] Verify installed_version matches firmware sensor
- [ ] Check release notes display correctly
- [ ] Verify release_url link works

**Expected Result:**
- Update entity shows "No update available" (latest_version is None)
- Users can view release notes with manual update instructions
- Clicking release URL opens manufacturer downloads page

---

### Phase 2: Firmware Upload Capability

#### Step 2.1: Create Firmware Manager Module

**File:** `custom_components/komfovent/firmware.py`

**Tasks:**
- [ ] Create `FirmwareManager` class
- [ ] Implement async login to device web interface
- [ ] Implement async firmware upload
- [ ] Implement progress monitoring
- [ ] Implement version verification

**Code Structure:**
```python
import aiohttp
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

class FirmwareManager:
    """Manage Komfovent firmware updates."""

    def __init__(self, host: str, username: str, password: str):
        """Initialize firmware manager."""
        self.host = host
        self.username = username
        self.password = password
        self._session: aiohttp.ClientSession | None = None

    async def async_login(self) -> bool:
        """Login to device web interface."""

    async def async_upload_firmware(
        self,
        firmware_data: bytes,
        filename: str,
        progress_callback=None
    ) -> dict[str, Any]:
        """Upload firmware file to device."""

    async def async_check_device_status(self) -> dict[str, Any]:
        """Check if device is ready for update."""

    async def async_wait_for_restart(self, timeout: int = 180) -> bool:
        """Wait for device to restart after update."""

    async def async_close(self) -> None:
        """Close the session."""
```

#### Step 2.2: Implement Firmware Upload in Update Entity

**File:** `custom_components/komfovent/update.py`

**Tasks:**
- [ ] Add `UpdateEntityFeature.INSTALL` to supported features
- [ ] Implement `async_install()` method
- [ ] Add firmware file validation
- [ ] Implement progress tracking
- [ ] Handle errors and timeouts

**Code Structure:**
```python
class KomfoventUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Komfovent firmware update entity."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL
        | UpdateEntityFeature.RELEASE_NOTES
    )

    async def async_install(
        self,
        version: str | None,
        backup: bool,
        **kwargs: Any,
    ) -> None:
        """Install firmware update."""

        # 1. Validate firmware file
        # 2. Check device status
        # 3. Upload firmware
        # 4. Monitor progress
        # 5. Wait for restart
        # 6. Verify new version
```

#### Step 2.3: Add Configuration for Firmware File

**Options:**

**Option A: File Upload via Service Call**
- Add custom service `komfovent.upload_firmware`
- Accept file path or file data
- Most flexible but requires more user setup

**Option B: Configuration Entry**
- Add config option for firmware file path
- User places file in accessible location
- Simpler UX but less flexible

**Option C: Hybrid Approach (Recommended)**
- Update entity shows "Update available" when user sets latest version in config
- User downloads firmware manually
- User triggers install - HA prompts for firmware file path
- HA uploads file to device

#### Step 2.4: Testing Phase 2

**Tasks:**
- [ ] Test firmware file validation
- [ ] Test upload to device (dry run)
- [ ] Test progress monitoring
- [ ] Test error handling (network errors, invalid files, etc.)
- [ ] Test actual firmware update on test device
- [ ] Verify version after update

**Test Cases:**
1. Valid .mbin file for firmware >=1.3.15
2. Valid .bin file for firmware <1.3.15
3. Invalid file extension
4. Network timeout during upload
5. Device restart timeout
6. Version verification after update

---

### Phase 3: Enhanced Version Management

#### Step 3.1: Add Latest Version Configuration

**File:** `custom_components/komfovent/config_flow.py`

**Tasks:**
- [ ] Add options flow for update settings
- [ ] Add field for latest firmware version (optional)
- [ ] Add field for firmware file path (optional)
- [ ] Validate version format

**UI Flow:**
```
Settings → Integrations → Komfovent → Configure
  ├─ Latest firmware version: [____] (optional)
  ├─ Firmware file path: [____] (optional)
  └─ [Save]
```

#### Step 3.2: Implement Version Comparison

**File:** `custom_components/komfovent/update.py`

**Tasks:**
- [ ] Add version comparison logic
- [ ] Return configured latest version
- [ ] Compare with installed version
- [ ] Update state accordingly

**Code:**
```python
@property
def latest_version(self) -> str | None:
    """Return the latest firmware version available."""
    # Get from config entry options
    return self.coordinator.config_entry.options.get("latest_firmware_version")

@property
def update_available(self) -> bool:
    """Return True if an update is available."""
    if not self.latest_version:
        return False

    return self._compare_versions(
        self.installed_version,
        self.latest_version
    ) < 0
```

#### Step 3.3: Testing Phase 3

**Tasks:**
- [ ] Test version comparison logic
- [ ] Test update available detection
- [ ] Test UI configuration flow
- [ ] Test version format validation

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_update.py`

**Test Cases:**
```python
def test_installed_version_parsing()
def test_version_comparison()
def test_update_available_detection()
def test_firmware_file_validation()
def test_release_notes_generation()
```

**File:** `tests/test_firmware.py`

**Test Cases:**
```python
def test_firmware_manager_login()
def test_firmware_upload()
def test_progress_monitoring()
def test_error_handling()
```

### Integration Tests

**File:** `tests/test_integration.py`

**Test Cases:**
```python
async def test_update_entity_setup()
async def test_firmware_update_flow()
async def test_update_failure_recovery()
```

### Manual Testing Checklist

- [ ] Update entity appears in Home Assistant UI
- [ ] Installed version displays correctly
- [ ] Latest version displays when configured
- [ ] Update available state is correct
- [ ] Release notes are accessible
- [ ] Firmware upload works with valid file
- [ ] Progress is shown during update
- [ ] Version is verified after update
- [ ] Error messages are clear and helpful
- [ ] Device continues working after failed update

### Validation Scripts

Two validation scripts are provided:

1. **`validate_version_check.py`**
   - Tests firmware version retrieval
   - Tests version comparison logic
   - Validates web interface access
   - **Requirements:** `requests`, `beautifulsoup4`

2. **`validate_firmware_update.py`**
   - Tests firmware file validation
   - Tests upload process
   - Tests progress monitoring
   - Tests version verification
   - **Requirements:** `requests`
   - **Usage:** Run with `--dry-run` for safe testing

**Installation:**
```bash
pip install requests beautifulsoup4
```

**Example Usage:**
```bash
# Version check validation
python3 validate_version_check.py --host 192.168.1.100 --test-version 1.3.28.38

# Firmware update validation (dry run)
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware /path/to/C6_1_3_28_38.mbin \
    --dry-run

# Actual firmware update (use with caution!)
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware /path/to/C6_1_3_28_38.mbin \
    --expected-version 1.3.28.38
```

---

## Security Considerations

### Authentication

- [ ] Store device credentials securely in config entry
- [ ] Don't log credentials in debug logs
- [ ] Use HTTPS if device supports it (unlikely for C6)
- [ ] Implement session timeout

### Firmware Validation

- [ ] Validate file extension (.bin or .mbin)
- [ ] Check file size (100KB - 10MB typical range)
- [ ] Verify file is readable before upload
- [ ] Optionally: Checksum validation if manufacturer provides

### Network Security

- [ ] Use authenticated connections
- [ ] Implement request timeouts
- [ ] Handle SSL/TLS errors gracefully
- [ ] Rate limit upload attempts

### Error Handling

- [ ] Don't expose internal errors to users
- [ ] Log detailed errors for debugging
- [ ] Provide recovery instructions
- [ ] Prevent bricking device with invalid firmware

---

## User Experience

### UI Flow

#### Version Check

```
Home Assistant Dashboard
  └─ Devices → Komfovent
       └─ Update: Komfovent Firmware
            ├─ Installed version: 1.3.17.20
            ├─ Latest version: Not configured
            ├─ Status: Unknown
            └─ [Release Notes]
```

#### Update Available

```
Home Assistant Dashboard
  └─ Devices → Komfovent
       └─ Update: Komfovent Firmware
            ├─ Installed version: 1.3.17.20
            ├─ Latest version: 1.3.28.38
            ├─ Status: Update available
            ├─ [Release Notes]
            └─ [Install]
```

#### Update Process

```
1. User clicks [Install]
2. Dialog: "Select firmware file"
   ├─ File picker
   ├─ [ ] Create backup (if supported)
   └─ [Upload] [Cancel]

3. Upload in progress
   ├─ Progress bar: 45%
   └─ "Uploading firmware..."

4. Restart in progress
   ├─ Progress spinner
   └─ "Device is restarting..."

5. Verification
   ├─ ✓ Check mark
   └─ "Update successful"

6. Or Error
   ├─ ✗ Error icon
   ├─ "Update failed: Connection timeout"
   └─ [Retry] [Cancel]
```

### Error Messages

| Error | User Message | Recovery Steps |
|-------|--------------|----------------|
| Invalid file | "Invalid firmware file. Please select a .bin or .mbin file." | Select correct file |
| Network error | "Could not connect to device. Check network connection." | Verify device is on network |
| Upload timeout | "Firmware upload timed out. The device may still be updating." | Wait 5 minutes, check device |
| Version mismatch | "Firmware version mismatch. Update may have failed." | Manual verification needed |
| Device busy | "Device is currently running. Stop the device before updating." | Stop AHU first |

### Documentation

**User-facing documentation should include:**

1. **Prerequisites**
   - Stop AHU before updating
   - Ensure stable network connection
   - Download firmware from manufacturer

2. **Version Check Setup**
   - How to configure latest version
   - Where to find latest firmware version

3. **Update Process**
   - Step-by-step instructions
   - Expected duration
   - What to do if update fails

4. **Troubleshooting**
   - Common errors and solutions
   - Recovery procedures
   - Contact information

---

## Future Enhancements

### Phase 4: Automatic Version Detection

**Goal:** Automatically detect latest firmware version

**Options:**
1. **Web Scraping** (fragile, not recommended)
   - Scrape manufacturer downloads page
   - Extract latest version
   - Requires maintenance when page changes

2. **RSS/Feed Monitoring** (if available)
   - Subscribe to manufacturer update feed
   - Parse version information
   - More reliable than scraping

3. **Community API** (recommended long-term)
   - Create community-maintained version database
   - Crowdsource latest versions
   - Provide API for integrations

### Phase 5: Update Scheduling

**Goal:** Schedule updates during maintenance windows

**Features:**
- Configure preferred update time
- Automatic download of firmware
- Automatic update installation
- Rollback on failure

### Phase 6: Multi-Device Updates

**Goal:** Update multiple Komfovent devices

**Features:**
- Detect all Komfovent devices
- Batch update capability
- Staggered update scheduling
- Progress dashboard

### Phase 7: Backup and Rollback

**Goal:** Protect against failed updates

**Features:**
- Backup current firmware (if device supports)
- Automatic rollback on failure
- Manual rollback option
- Backup verification

---

## Dependencies

### Python Packages

**Required:**
- `homeassistant` (core)
- `aiohttp` (already used in HA)
- `pymodbus` (already in integration)

**Optional for validation scripts:**
- `requests` (sync HTTP)
- `beautifulsoup4` (HTML parsing)

**Update `manifest.json`:**
```json
{
  "requirements": [
    "pymodbus==3.6.2"
  ]
}
```

No additional requirements needed - use built-in HA libraries.

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1 | Version check entity | 8-12 hours |
| Phase 2 | Firmware upload | 16-24 hours |
| Phase 3 | Version management | 8-12 hours |
| Testing | Unit + integration tests | 12-16 hours |
| Documentation | User + developer docs | 4-8 hours |
| **Total** | | **48-72 hours** |

**Milestones:**
- Week 1: Phase 1 complete + basic testing
- Week 2: Phase 2 complete + integration testing
- Week 3: Phase 3 complete + documentation
- Week 4: Final testing + release

---

## Success Criteria

### Phase 1 (MVP)
- ✓ Update entity displays installed version
- ✓ Release notes provide manual update instructions
- ✓ Users can access manufacturer downloads

### Phase 2 (Core Functionality)
- ✓ Users can upload firmware via Home Assistant
- ✓ Upload progress is visible
- ✓ Version is verified after update
- ✓ Error handling is robust

### Phase 3 (Enhanced UX)
- ✓ Update available detection works
- ✓ Configuration is user-friendly
- ✓ Documentation is clear and complete

### Overall Success
- ✓ Reduces manual update steps by 50%
- ✓ No bricked devices during testing
- ✓ Positive user feedback
- ✓ Minimal support requests

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Device becomes unresponsive after update | Medium | High | Thorough testing, clear recovery docs |
| Network timeout during upload | High | Medium | Retry logic, timeout handling |
| Manufacturer changes web interface | Low | High | Version detection, graceful degradation |
| Invalid firmware file bricks device | Low | Critical | File validation, user warnings |
| Concurrent updates cause conflicts | Low | Medium | Update locking, status checks |

---

## Conclusion

This development plan provides a phased approach to implementing firmware update capabilities for the Komfovent Home Assistant integration. By starting with basic version checking and gradually adding upload functionality, we can:

1. **Deliver value incrementally** - Users get version tracking immediately
2. **Minimize risk** - Each phase is tested before proceeding
3. **Maintain quality** - Following HA best practices throughout
4. **Enable future enhancement** - Architecture supports advanced features

The provided validation scripts allow testing the core functionality before full implementation, reducing development risk and ensuring the approach is sound.

### Next Steps

1. **Review and approve this plan** with stakeholders
2. **Run validation scripts** on test device to confirm approach
3. **Begin Phase 1 implementation** - version check entity
4. **Iterate based on feedback** from testing and users
5. **Document learnings** for future enhancements

---

## References

- [Home Assistant Update Entity Documentation](https://developers.home-assistant.io/docs/core/entity/update/)
- [Komfovent C6 Firmware Update Instructions (PDF)](https://www.komfovent.com/en/downloads/C6_update_EN.pdf)
- [Komfovent Software Downloads](https://www.komfovent.com/en/page/software)
- [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index/)
- Existing integration code in `custom_components/komfovent/`

---

**Document Version:** 1.0
**Date:** 2025-12-24
**Author:** Development Planning for hass-komfovent
**Status:** Ready for Review
