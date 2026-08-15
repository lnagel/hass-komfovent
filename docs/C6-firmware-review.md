# Firmware Update Feature — Review

Branch: `claude/add-firmware-update-checks-casmC`
Reviewed: 2026-02-06

## CI Blockers

### 1. Diff coverage at 23% (required: 100%)

Zero dedicated test files exist for the new firmware code. Missing:

- `tests/test_firmware_init.py` — `format_version`, `is_newer_version`, `get_controller_type_for_firmware`
- `tests/test_firmware_store.py` — all `FirmwareStore` methods including load/save, cleanup, path handling
- `tests/test_firmware_checker.py` — register/unregister, HTTP download, filename extraction/parsing, reentrancy guard, error paths
- `tests/test_firmware_uploader.py` — login/upload/logout flow, progress callback, error handling
- `tests/test_update.py` — entity properties, `async_install` flow (reentrancy, version guard, errors, cooldown)
- `tests/test_helpers.py` — missing tests for new `get_panel_version()` function

### 2. Overall coverage dropped to 71.4% (required: 85%)

The new untested code drags coverage below the CI threshold.

---

## Architecture

### Major

#### 3. Multi-entry controller unregister bug
**File:** `firmware/checker.py:88-98`

`unregister_controller_type` uses `set.discard()`. If two config entries both have C6 controllers, unloading the first removes "C6" from `_active_controller_types`, breaking firmware checks for the second entry. Fix: use a counter/multiset instead of a plain set.

#### 4. `domain_data` key collision
**File:** `services.py`

`hass.data[DOMAIN]` now mixes entry IDs with the string `"domain_data"`. The exclusion check (`if entry_id == "domain_data": continue`) is fragile. Better: store domain data in a separate namespace (e.g., `hass.data[f"{DOMAIN}_domain"]`) or use a typed data class.

#### 5. `timeout=60` integer in checker
**File:** `firmware/checker.py:183`

`session.get(url, timeout=60)` passes an integer. Should use `aiohttp.ClientTimeout(total=60)` — the uploader already does this correctly.

### Minor

#### 6. TypedDict tuple vs JSON list mismatch
**File:** `firmware/__init__.py`

`FirmwareInfo` declares `tuple[int, int, int, int, int]` for versions, but HA's Store API serializes to JSON (lists). On reload, `async_load()` returns lists, not tuples. The type annotation is incorrect even though indexing works on both.

#### 7. C6/C6M firmware download over HTTP
**File:** `const.py:57-58`

C6/C6M URL uses `http://` (not `https://`). Likely a manufacturer limitation but should be documented as a known risk. C8 URL correctly uses `https://`.

#### 8. Path traversal defense-in-depth
**File:** `firmware/checker.py:271-295`

Filename from `Content-Disposition` header is mitigated by the anchored regex, but should also explicitly strip path components: `filename = Path(filename).name`.

---

## UX

### High

#### 9. No `release_summary`
**File:** `update.py`

Users see installed vs latest version but zero context about what changed. For an HVAC firmware update, this is concerning. Recommendation: show available controller + panel versions and download timestamp, even without a structured changelog.

#### 10. Progress is bool-only
**File:** `update.py`

`PROGRESS` feature flag is set but `in_progress` returns `True`/`False` instead of a percentage. The 3+ minute update (upload ~57s + restart 120s) shows an indeterminate spinner. The callback infrastructure already exists in `FirmwareUploader.async_upload_firmware()` — just needs to be wired into `update.py`.

### Medium

#### 11. No `release_url`
**File:** `update.py`

Returns `None` explicitly. Could link to `https://www.komfovent.com/en/support/software-updates/` or the device's web interface.

#### 12. Missing translations
**File:** `update.py`, `translations/en.json`

`_attr_name = "Firmware"` is hardcoded English. No `update` section exists in translations. Breaks the pattern used by all other entity platforms in this integration which use `_attr_translation_key`.

#### 13. No `sw_version` on DeviceInfo
**File:** `helpers.py` (`build_device_info`)

Firmware version not visible on Settings > Devices page. Should pull from the coordinator's firmware register.

#### 14. Diagnostics missing firmware state
**File:** `diagnostics.py`

Doesn't include firmware store contents (latest version, last check time), whether firmware file exists, or checker state. Hinders debugging firmware issues from diagnostics downloads.

### Low

#### 15. Error messages lack actionability
Messages like "Firmware file not available. Wait for firmware check to complete." don't say when the last check ran or when the next is scheduled. Suggest: "The integration checks every 7 days. Reload the integration to trigger an immediate check."

#### 16. Entity availability during install
Entity goes unavailable during the 120s restart window because the coordinator fails. Consider keeping the entity available while `_installing = True`.

---

## Strengths

- Clean module separation — checker/store/uploader have clear single responsibilities
- Correct HA patterns — `Store` API, `async_track_time_interval`, `CoordinatorEntity`, `HomeAssistantError`
- Domain-level singleton — multiple devices share one firmware download per controller type
- Concurrency guards — install reentrancy flag, coordinator cooldown during upload
- Minimum version guard — clear error for firmware < v1.3.15
- Coordinator unchanged — kept Modbus-only, firmware concerns properly separated

---

## Recommended Action Order

1. **Write tests** (blockers #1, #2) — 5 new test files + `get_panel_version` coverage
2. **Fix multi-entry unregister** (#3) — correctness bug
3. **Fix `aiohttp.ClientTimeout`** (#5) — API correctness
4. **Wire up progress percentage** (#10) — infrastructure already exists
5. **Add translations** (#12) — consistency
6. **Add `release_summary`** (#9) — user confidence
7. **Fix `domain_data` namespace** (#4)
8. Remaining minor/medium items
