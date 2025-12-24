# Firmware Update Scripts - Usage Guide

This repository includes several scripts to help validate and test the firmware update process for Komfovent C6/C6M controllers.

## 📋 Available Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `download_firmware.py` | Download/validate firmware files | ✅ Ready |
| `validate_version_check.py` | Test version checking via web interface | ✅ Ready |
| `validate_firmware_update.py` | Test firmware upload process | ✅ Ready |
| `test_firmware_check.py` | Test manufacturer URL accessibility | ✅ Ready |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install requests beautifulsoup4
```

### 2. Download Firmware

**Option A: Automatic (if you have whitelisted access):**
```bash
python3 download_firmware.py --type mbin
```

**Option B: Manual Download (typical):**
1. Visit https://www.komfovent.com/en/page/software
2. Download the firmware file (e.g., `C6_1_3_28_38_20230615.mbin`)
3. Validate it:
```bash
python3 download_firmware.py --validate C6_1_3_28_38_20230615.mbin
```

### 3. Test Version Check (Optional)

```bash
python3 validate_version_check.py \
    --host 192.168.1.100 \
    --username user \
    --password user \
    --test-version 1.3.28.38
```

### 4. Test Firmware Update (Dry Run)

```bash
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware C6_1_3_28_38_20230615.mbin \
    --dry-run
```

### 5. Perform Actual Update (Caution!)

⚠️ **WARNING**: This performs a real firmware update!

```bash
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware C6_1_3_28_38_20230615.mbin \
    --expected-version 1.3.28.38
```

## 📖 Detailed Usage

### download_firmware.py

Download or validate Komfovent firmware files.

**Download MBIN firmware:**
```bash
python3 download_firmware.py --type mbin
```

**Download BIN firmware (for older controllers):**
```bash
python3 download_firmware.py --type bin
```

**Download to specific file:**
```bash
python3 download_firmware.py --type mbin --output latest_firmware.mbin
```

**Validate existing firmware file:**
```bash
python3 download_firmware.py --validate firmware.mbin
```

**Expected Output (when blocked):**
```
======================================================================
Downloading MBIN firmware
======================================================================
URL: http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin

1. Checking access with HEAD request...
   Status: 403
   ❌ Access denied (403 Forbidden)
   Reason: host_not_allowed

📥 MANUAL DOWNLOAD REQUIRED

Please download the firmware manually:
1. Visit: https://www.komfovent.com/en/page/software
2. Download the latest MBIN firmware file
```

**What it validates:**
- ✅ File extension (.bin or .mbin)
- ✅ File size (warns if < 100KB or > 10MB)
- ✅ Filename pattern (C6_v1_v2_v3_v4_date.mbin)
- ✅ Version extraction (1.3.28.38 format)

---

### validate_version_check.py

Test firmware version detection and comparison.

**Basic usage:**
```bash
python3 validate_version_check.py --host 192.168.1.100
```

**With version comparison test:**
```bash
python3 validate_version_check.py \
    --host 192.168.1.100 \
    --test-version 1.3.28.38
```

**With custom credentials:**
```bash
python3 validate_version_check.py \
    --host 192.168.1.100 \
    --username admin \
    --password mypassword
```

**What it tests:**
- ✅ Login to device web interface
- ✅ Extract current firmware versions
- ✅ Check for update endpoints
- ✅ Version comparison logic

**Expected Output:**
```
======================================================================
KOMFOVENT FIRMWARE VERSION CHECK - VALIDATION
======================================================================

Target device: 192.168.1.100

1. Attempting to login...
   ✓ Login successful

2. Fetching current firmware versions...
   ✓ Controller firmware: C6 1.3.18.21
   ✓ Panel 1 firmware: C6 1.1.3.14

3. Checking for latest firmware...
   ⚠ No update check endpoint found on device

4. Version comparison test...
   Current: 1.3.18.21
   Latest:  1.3.28.38
   Result:  update_available
   ✓ Update is available!
```

---

### validate_firmware_update.py

Test the complete firmware update workflow.

**Dry run (safe testing - doesn't upload):**
```bash
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware C6_1_3_28_38_20230615.mbin \
    --dry-run
```

**Actual update (real device update!):**
```bash
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware C6_1_3_28_38_20230615.mbin \
    --expected-version 1.3.28.38
```

**With custom credentials:**
```bash
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --username admin \
    --password mypassword \
    --firmware firmware.mbin \
    --dry-run
```

**What it tests:**
- ✅ Login to device
- ✅ Firmware file validation
- ✅ Upload to http://[IP]/g1.html
- ✅ Progress monitoring
- ✅ Device restart detection
- ✅ Version verification

**Expected Output (dry run):**
```
======================================================================
KOMFOVENT FIRMWARE UPDATE - VALIDATION
======================================================================

Target device: 192.168.1.100
Firmware file: C6_1_3_28_38_20230615.mbin
Mode: DRY RUN

1. Logging in to http://192.168.1.100...
   ✓ Login successful

2. Validating firmware file...
   ✓ File is valid
   ✓ Type: mbin
   ✓ Size: 1,234,567 bytes

3. Uploading firmware...
   ⚠ DRY RUN MODE - not actually uploading

✓ DRY RUN VALIDATION SUCCESSFUL
```

---

### test_firmware_check.py

Test manufacturer firmware URL accessibility.

**Basic usage:**
```bash
python3 test_firmware_check.py
```

**What it tests:**
- ✅ HEAD request to manufacturer URLs
- ✅ Response headers analysis
- ✅ Version extraction logic
- ✅ Version comparison logic

**Expected Output:**
```
======================================================================
Testing firmware version check for MBIN files
======================================================================
URL: http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin

1. Sending HEAD request...
   Status Code: 403
   Headers:
     x-deny-reason: host_not_allowed
     content-type: text/plain
     server: envoy

3. WARNING: No filename found in response headers
```

---

## 🔧 Troubleshooting

### "403 Forbidden" when downloading

**Expected behavior** - The manufacturer blocks external downloads.

**Solutions:**
1. Download manually from https://www.komfovent.com/en/page/software
2. Try running from device's local network
3. Use the `--validate` flag to check manually downloaded files

### "Could not login to device"

**Possible causes:**
- Device is not accessible on network
- Wrong IP address
- Wrong username/password
- Device firewall blocking connection

**Solutions:**
1. Verify device IP: `ping 192.168.1.100`
2. Check web interface manually: `http://192.168.1.100`
3. Verify credentials (default: user/user)

### "File too small" warning

**Possible causes:**
- Incomplete download
- Wrong file downloaded
- Corrupted file

**Solutions:**
1. Re-download the firmware file
2. Verify file size (typical: 500KB - 5MB)
3. Check file content is not an HTML error page

### Update timeout

**Possible causes:**
- Network issues
- Device is still updating
- Device requires manual power cycle

**Solutions:**
1. Wait 5 minutes and check device manually
2. Try power cycling the device
3. Access device web interface to check status

---

## 📊 Workflow Examples

### Complete Manual Update Workflow

```bash
# 1. Download firmware manually from manufacturer
# Visit: https://www.komfovent.com/en/page/software
# Download: C6_1_3_28_38_20230615.mbin

# 2. Validate the downloaded file
python3 download_firmware.py --validate C6_1_3_28_38_20230615.mbin

# 3. Check current version on device
python3 validate_version_check.py --host 192.168.1.100

# 4. Test update process (dry run)
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware C6_1_3_28_38_20230615.mbin \
    --dry-run

# 5. Perform actual update (when ready)
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware C6_1_3_28_38_20230615.mbin \
    --expected-version 1.3.28.38
```

### Testing Before Implementation

```bash
# 1. Test manufacturer URL access
python3 test_firmware_check.py

# 2. Test device web interface access
python3 validate_version_check.py --host 192.168.1.100

# 3. Test update workflow (dry run only!)
python3 validate_firmware_update.py \
    --host 192.168.1.100 \
    --firmware test_firmware.mbin \
    --dry-run
```

---

## 🎯 Script Return Codes

All scripts use standard exit codes:

- **0** = Success
- **1** = Error/Failure

Use in automation:
```bash
if python3 download_firmware.py --validate firmware.mbin; then
    echo "Firmware is valid"
    python3 validate_firmware_update.py --host 192.168.1.100 --firmware firmware.mbin
else
    echo "Invalid firmware file"
    exit 1
fi
```

---

## 📚 Additional Resources

- **Development Plan**: See `FIRMWARE_UPDATE_PLAN.md`
- **Test Results**: See `FIRMWARE_URL_TEST_RESULTS.md`
- **Summary**: See `README_FIRMWARE_UPDATE.md`
- **Manufacturer Docs**: https://www.komfovent.com/en/downloads/C6_update_EN.pdf

---

## ⚠️ Important Notes

1. **Backup First**: No backup mechanism is available - update at your own risk
2. **Stop Device**: Always stop the AHU before updating
3. **Stable Network**: Ensure stable network connection during update
4. **Test First**: Always use `--dry-run` before actual update
5. **Manual Verification**: Verify firmware version after update

---

## 🐛 Reporting Issues

If you encounter issues with the scripts:

1. Run with `--dry-run` to avoid device changes
2. Check error messages carefully
3. Verify device is accessible
4. Test manually via web interface
5. Report issues with full error output

---

**Last Updated**: 2025-12-24
**Scripts Version**: 1.0
**Tested With**: Komfovent C6 firmware 1.3.x
