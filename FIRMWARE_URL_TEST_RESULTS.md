# Firmware Download URL Testing Results

## Test Date: 2025-12-24

## Hypothesis
The manufacturer firmware URLs might return version information via HTTP headers (Content-Disposition) that could be used for automatic version checking.

## Test URLs
- MBIN firmware: `http://www.komfovent.com/Update/Controllers/firmware.php?file=mbin`
- BIN firmware: `http://www.komfovent.com/Update/Controllers/firmware.php?file=bin`

## Test Method: HEAD Request

```python
import requests
response = requests.head(url, allow_redirects=True, timeout=10)
```

## Actual Results

### Response Headers (MBIN)
```
Status Code: 403 Forbidden
x-deny-reason: host_not_allowed
content-length: 16
content-type: text/plain
date: Wed, 24 Dec 2025 06:05:55 GMT
server: envoy
```

### Response Headers (BIN)
```
Status Code: 403 Forbidden
x-deny-reason: host_not_allowed
content-length: 16
content-type: text/plain
date: Wed, 24 Dec 2025 06:05:55 GMT
server: envoy
```

## Key Findings

### ❌ Hypothesis REJECTED

1. **Access Blocked**: HTTP 403 Forbidden
2. **Host-Based Filtering**: Header `x-deny-reason: host_not_allowed` indicates IP-based access control
3. **No Version Information**: No `Content-Disposition` or other metadata headers present
4. **Envoy Proxy**: Server uses Envoy proxy for request filtering

### Additional Tests

Tested with different User-Agent strings:
- `Mozilla/5.0 (compatible; KomfoventC6/1.3)` → 403
- `Komfovent-Controller/1.0` → 403
- `wget/1.21` → 403
- `curl/7.88.1` → 403

**Result**: User-Agent has no effect. Filtering is based on originating host/IP address.

## Implications

### Cannot Use for Automatic Version Checking

❌ **External access is blocked** - Cannot query from Home Assistant
❌ **No metadata in headers** - Even if accessible, no version info available
❌ **User-Agent spoofing doesn't work** - Host-based filtering is active

### Alternative Approaches

✅ **Device Local Access**: The device itself may be whitelisted to download
✅ **Manual Download**: Users download from web interface (https://www.komfovent.com/en/page/software)
✅ **Local Upload**: Upload firmware via device web interface at `http://[IP]/g1.html`
✅ **Version from Modbus**: Current version already available via register 1000

## Conclusion

**The original hypothesis about using HEAD requests to check firmware versions is NOT viable.**

The manufacturer has implemented host-based access control that blocks external requests. The only viable approach is:

1. Users manually download firmware from the manufacturer website
2. Users configure latest version in Home Assistant (optional)
3. Home Assistant uploads firmware to device's local web interface
4. Version verification via Modbus after update

This validates the approach outlined in `FIRMWARE_UPDATE_PLAN.md` which assumes manual firmware download and local device upload.

## Technical Details

**Server Configuration:**
- Reverse proxy: Envoy
- Access control: Host-based allowlist
- Blocked response: 16-byte plaintext "Access denied" (assumed)
- No CORS headers present
- No authentication challenge (401) - direct 403 rejection

**Possible Whitelisted Hosts:**
- Komfovent internal networks
- Device IP ranges (controllers may download directly)
- Specific partner networks

## Recommendations

1. ✅ Proceed with manual download + local upload approach
2. ✅ Use Modbus for current version detection
3. ✅ Allow user configuration of latest available version
4. ❌ Do not attempt automatic version checking from external URLs
5. 💡 Consider community-maintained version database as future enhancement

## References

- Test script: `test_firmware_check.py`
- Development plan: `FIRMWARE_UPDATE_PLAN.md`
- Manufacturer downloads: https://www.komfovent.com/en/page/software
