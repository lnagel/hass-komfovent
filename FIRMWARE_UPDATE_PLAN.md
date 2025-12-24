# Komfovent C6/C6M Firmware Update Feature - Development Plan

## Executive Summary

This document outlines the development plan for adding **fully automated** firmware update capabilities to the Komfovent Home Assistant custom component. The implementation will automatically download firmware from the manufacturer, upload it to the device, and verify the update - requiring no manual file handling from users.

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

1. **Automated Process Flow:**
   - Stop AHU (Air Handling Unit)
   - Download firmware from manufacturer server
   - Upload to device web interface at `http://[IP]/g1.html`
   - Wait 30-60 seconds for upload
   - Wait 1-2 minutes for device restart
   - Verify new firmware version

2. **Firmware File Types:**
   - `.mbin` - For firmware version X.X.X.15 or later
   - `.bin` - For firmware version X.X.X.14 or earlier

3. **Download Sources:**
   - Main firmware: `http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin`
   - Legacy firmware: `http://www.komfovent.com/Update/Controllers/firmware.php?file=bin`
   - **Note:** Accessible from residential networks where devices are installed

### Key Findings

✅ **What Works:**
- Current firmware version available via Modbus
- Version parsing implemented and tested
- Device web interface supports firmware upload
- **Firmware download accessible from residential networks**
- Devices located in settings with validated download access

❌ **Limitations:**
- Device must be stopped before updating
- No rollback mechanism available

---

## Requirements

### Functional Requirements

#### FR1: Automated Version Check
- [ ] FR1.1: Display current firmware version (already implemented)
- [ ] FR1.2: **Automatically check latest version from manufacturer**
- [ ] FR1.3: Show update availability status
- [ ] FR1.4: Display release information when available
- [ ] FR1.5: Cache version checks to minimize server requests

#### FR2: Automated Firmware Update
- [ ] FR2.1: **Automatically download firmware from manufacturer**
- [ ] FR2.2: Validate downloaded firmware file
- [ ] FR2.3: Automatically upload firmware to device
- [ ] FR2.4: Monitor update progress
- [ ] FR2.5: Verify successful update
- [ ] FR2.6: Handle update failures gracefully
- [ ] FR2.7: Clean up downloaded files after update

#### FR3: Safety Features
- [ ] FR3.1: Warn user before starting update
- [ ] FR3.2: Check device is idle/stopped before update
- [ ] FR3.3: Prevent updates during critical operations
- [ ] FR3.4: Provide clear error messages
- [ ] FR3.5: Log update attempts and results

### Non-Functional Requirements

#### NFR1: Performance
- Version check should complete within 5 seconds
- Firmware download should handle files up to 10MB
- Progress indication should update every 5-10 seconds
- Cache firmware files to avoid re-downloads

#### NFR2: Reliability
- Handle network timeouts gracefully
- Retry failed downloads (with exponential backoff)
- Maintain device state if update fails
- Automatic cleanup of temporary files

#### NFR3: Security
- Use authenticated connections to device
- Validate firmware file integrity
- Don't expose sensitive credentials in logs
- Verify firmware source authenticity

#### NFR4: Usability
- Clear status messages throughout process
- Progress indication during download and upload
- Helpful error messages with recovery steps
- Single-click update from Home Assistant UI

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
│ + in_progress: bool                         │
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
│ - download_cache: dict                      │
├─────────────────────────────────────────────┤
│ + async_check_latest_version(): str         │
│ + async_download_firmware(type): bytes      │
│ + async_login(): bool                       │
│ + async_upload_firmware(data): bool         │
│ + async_check_status(): dict                │
│ + async_verify_version(version): bool       │
│ + async_cleanup(): None                     │
└─────────────────────────────────────────────┘
```

### Data Flow

#### Automated Version Check Flow

```
Coordinator refresh → Check manufacturer URL for latest version
                           ↓
                  Extract version from filename/headers
                           ↓
                  Compare with installed version (Modbus)
                           ↓
                  Update entity state (update available/up-to-date)
```

#### Fully Automated Update Flow

```
User clicks Install → Check current firmware version (Modbus)
                           ↓
                  Determine firmware type (.bin or .mbin)
                           ↓
                  Download firmware from manufacturer
                           ↓
                  Validate downloaded file
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
                  Clean up temporary files
                           ↓
                  Update entity state
```

---

## Implementation Plan

### Phase 1: Automated Version Detection

#### Step 1.1: Implement Version Checking from Manufacturer

**File:** `custom_components/komfovent/firmware.py`

**Tasks:**
- [ ] Create `FirmwareManager` class
- [ ] Implement `async_check_latest_version()` - HEAD request to manufacturer URL
- [ ] Extract version from `Content-Disposition` header or filename
- [ ] Parse version number from filename pattern
- [ ] Cache results for 1 hour to minimize server load
- [ ] Handle network errors gracefully

**Code Structure:**
```python
class FirmwareManager:
    """Manage Komfovent firmware downloads and updates."""

    async def async_check_latest_version(
        self,
        firmware_type: str = "mbin"
    ) -> dict[str, Any]:
        """Check latest firmware version from manufacturer.

        Returns:
            {
                "version": "1.3.28.38",
                "filename": "C6_1_3_28_38_20230615.mbin",
                "date": "20230615",
                "url": "http://...",
            }
        """
        # HEAD request to get filename without downloading
        # Extract version from filename
        # Cache result
```

#### Step 1.2: Create Update Entity with Auto Version Check

**File:** `custom_components/komfovent/update.py`

**Tasks:**
- [ ] Create `KomfoventUpdateEntity` class extending `UpdateEntity`
- [ ] Implement `installed_version` property (read from Modbus)
- [ ] Implement `latest_version` property (from FirmwareManager)
- [ ] Implement automatic version checking on refresh
- [ ] Add release notes support
- [ ] Set supported_features for install

**Code:**
```python
class KomfoventUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Komfovent firmware update entity."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL
        | UpdateEntityFeature.PROGRESS
        | UpdateEntityFeature.RELEASE_NOTES
    )
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    @property
    def installed_version(self) -> str | None:
        """Return installed firmware version from Modbus."""
        # Get from coordinator.data[REG_FIRMWARE]

    @property
    def latest_version(self) -> str | None:
        """Return latest firmware version from manufacturer."""
        # Automatically checked by FirmwareManager

    @property
    def in_progress(self) -> bool:
        """Return True if update is in progress."""
        # Track update state
```

#### Step 1.3: Testing Phase 1

**Tasks:**
- [ ] Verify version check works from residential network
- [ ] Test version comparison logic
- [ ] Verify update entity shows correct state
- [ ] Test cache expiration

**Expected Result:**
- Update entity automatically detects new firmware
- Shows "Update available" when new version exists
- No manual version configuration needed

---

### Phase 2: Automated Firmware Download and Upload

#### Step 2.1: Implement Firmware Download

**File:** `custom_components/komfovent/firmware.py`

**Tasks:**
- [ ] Implement `async_download_firmware()` method
- [ ] Determine firmware type based on current version
- [ ] Download with progress tracking
- [ ] Validate downloaded file (size, extension, checksum)
- [ ] Store temporarily in Home Assistant temp directory
- [ ] Implement retry logic with exponential backoff

**Code:**
```python
async def async_download_firmware(
    self,
    firmware_type: str,
    progress_callback=None
) -> bytes:
    """Download firmware from manufacturer.

    Args:
        firmware_type: "mbin" or "bin"
        progress_callback: Optional callback for progress updates

    Returns:
        Firmware file data as bytes
    """
    # Download with aiohttp
    # Track progress
    # Validate file
    # Return data
```

#### Step 2.2: Implement Automated Upload

**File:** `custom_components/komfovent/firmware.py`

**Tasks:**
- [ ] Implement device login
- [ ] Implement firmware upload to /g1.html
- [ ] Monitor upload progress
- [ ] Wait for device restart
- [ ] Verify version after restart
- [ ] Clean up temporary files

**Code:**
```python
async def async_upload_firmware(
    self,
    firmware_data: bytes,
    filename: str,
    progress_callback=None
) -> bool:
    """Upload firmware to device.

    Args:
        firmware_data: Firmware file bytes
        filename: Original filename
        progress_callback: Optional progress callback

    Returns:
        True if successful
    """
    # Login to device
    # Upload to /g1.html
    # Monitor progress
    # Return success/failure
```

#### Step 2.3: Implement Full Update Flow in Update Entity

**File:** `custom_components/komfovent/update.py`

**Tasks:**
- [ ] Implement `async_install()` method
- [ ] Integrate download and upload
- [ ] Show progress during update
- [ ] Handle errors and timeouts
- [ ] Update entity state throughout process

**Code:**
```python
async def async_install(
    self,
    version: str | None,
    backup: bool,
    **kwargs: Any,
) -> None:
    """Automatically download and install firmware update."""

    # 1. Determine firmware type (.bin or .mbin)
    # 2. Download from manufacturer
    # 3. Validate file
    # 4. Check device status
    # 5. Upload to device
    # 6. Monitor progress
    # 7. Wait for restart
    # 8. Verify version
    # 9. Clean up
```

#### Step 2.4: Testing Phase 2

**Tasks:**
- [ ] Test automatic download from residential network
- [ ] Test upload to device
- [ ] Test progress reporting
- [ ] Test error handling
- [ ] Test cleanup of temp files
- [ ] Perform actual update on test device

**Test Cases:**
1. Full automated update (download → upload → verify)
2. Network timeout during download
3. Network timeout during upload
4. Device restart timeout
5. Version verification after update
6. Cleanup after successful update
7. Cleanup after failed update

---

### Phase 3: Polish and Optimization

#### Step 3.1: Progress Tracking

**Tasks:**
- [ ] Implement detailed progress states
- [ ] Show download progress percentage
- [ ] Show upload progress percentage
- [ ] Show waiting states (device restart)
- [ ] Update entity attributes with current state

#### Step 3.2: Error Handling and Recovery

**Tasks:**
- [ ] Implement retry logic for transient failures
- [ ] Provide clear error messages
- [ ] Log detailed error information
- [ ] Implement automatic cleanup on failure
- [ ] Add recovery instructions to entity attributes

#### Step 3.3: Optimization

**Tasks:**
- [ ] Cache firmware files (same version, multiple devices)
- [ ] Implement version check caching
- [ ] Optimize download chunk size
- [ ] Minimize server load with appropriate intervals

#### Step 3.4: Testing Phase 3

**Tasks:**
- [ ] Test with multiple devices
- [ ] Test concurrent updates
- [ ] Test cache behavior
- [ ] Load testing
- [ ] Long-running stability test

---

## Testing Strategy

### Validation Scripts

Three validation scripts provided:

1. **`download_firmware.py`**
   - Tests automatic firmware download
   - Validates firmware files
   - Extracts version information
   - **Run from same network as device**

2. **`validate_version_check.py`**
   - Tests web interface access
   - Validates version detection
   - Tests version comparison

3. **`validate_firmware_update.py`**
   - Tests complete update workflow
   - Supports dry-run mode
   - Validates end-to-end process

### Unit Tests

**File:** `tests/test_update.py`

```python
def test_installed_version_parsing()
def test_version_comparison()
def test_update_available_detection()
def test_firmware_type_selection()
def test_progress_tracking()
```

**File:** `tests/test_firmware.py`

```python
async def test_check_latest_version()
async def test_download_firmware()
async def test_upload_firmware()
async def test_version_verification()
async def test_cleanup()
```

### Integration Tests

**File:** `tests/test_update_integration.py`

```python
async def test_full_automated_update()
async def test_update_progress_reporting()
async def test_error_recovery()
async def test_concurrent_updates()
```

---

## Security Considerations

### Firmware Validation

- [ ] Validate file extension (.bin or .mbin)
- [ ] Check file size (100KB - 10MB typical)
- [ ] Verify filename pattern matches expected format
- [ ] Validate version number format
- [ ] Optional: Checksum validation if provided by manufacturer

### Network Security

- [ ] Use authenticated connections to device
- [ ] Implement request timeouts
- [ ] Rate limit download attempts
- [ ] Verify firmware source (manufacturer URL)
- [ ] Secure temporary file storage

### Error Handling

- [ ] Don't expose credentials in logs
- [ ] Sanitize error messages
- [ ] Provide recovery instructions
- [ ] Prevent bricking with validation
- [ ] Automatic cleanup of failed downloads

---

## User Experience

### UI Flow - Fully Automated

#### Update Available

```
Home Assistant Dashboard
  └─ Devices → Komfovent
       └─ Update: Komfovent Firmware
            ├─ Installed version: 1.3.17.20
            ├─ Latest version: 1.3.28.38 (automatically detected)
            ├─ Status: Update available
            ├─ [Release Notes]
            └─ [Install] ← Single click!
```

#### Automated Update Process

```
1. User clicks [Install]

2. Confirmation dialog:
   "Update firmware from 1.3.17.20 to 1.3.28.38?"
   [Update] [Cancel]

3. Download phase:
   ├─ Progress bar: "Downloading... 45%"
   └─ Status: "Downloading firmware from manufacturer"

4. Upload phase:
   ├─ Progress bar: "Uploading... 67%"
   └─ Status: "Uploading to device"

5. Restart phase:
   ├─ Progress spinner
   └─ Status: "Device is restarting..."

6. Verification:
   ├─ ✓ Check mark
   └─ "Update successful to version 1.3.28.38"

7. Or Error:
   ├─ ✗ Error icon
   ├─ "Download failed: Connection timeout"
   └─ [Retry] [Cancel]
```

**No manual file handling required!**

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1 | Auto version detection | 12-16 hours |
| Phase 2 | Auto download & upload | 20-28 hours |
| Phase 3 | Polish & optimization | 8-12 hours |
| Testing | Comprehensive testing | 12-16 hours |
| Documentation | User & dev docs | 4-8 hours |
| **Total** | | **56-80 hours** |

---

## Success Criteria

### Phase 1 (Auto Version Check)
- ✓ Automatically detects latest firmware version
- ✓ Shows update available/up-to-date status
- ✓ No manual configuration needed

### Phase 2 (Full Automation)
- ✓ Downloads firmware automatically
- ✓ Uploads to device automatically
- ✓ Verifies update completion
- ✓ Requires zero manual file handling

### Phase 3 (Polish)
- ✓ Clear progress indication
- ✓ Robust error handling
- ✓ Efficient caching and optimization

### Overall Success
- ✓ Single-click firmware updates
- ✓ No manual file downloads or uploads
- ✓ Works reliably from residential networks
- ✓ No bricked devices
- ✓ Positive user feedback

---

## Conclusion

This development plan provides a fully automated firmware update solution for Komfovent devices. By leveraging validated download access from residential networks, users can update firmware with a single click from Home Assistant - no manual file handling required.

**Key Benefits:**
- 🚀 Fully automated download and upload
- 🎯 Single-click updates from HA UI
- 📊 Real-time progress tracking
- 🔒 Safe with validation and error handling
- ♻️ Automatic cleanup of temporary files

---

**Document Version:** 2.0
**Date:** 2025-12-24
**Status:** Ready for Implementation
