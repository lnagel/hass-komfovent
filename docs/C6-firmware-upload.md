# Komfovent C6 Firmware Upload Protocol Analysis

This document describes the HTTP-based firmware upload protocol used by Komfovent C6 units, based on packet capture analysis.

## Overview

| Property | Value |
|----------|-------|
| Protocol | HTTP/1.1 over TCP |
| Endpoint | `POST /g1.html` |
| Server | `C6` (embedded HTTP server) |
| Authentication | Session-based (requires prior login) |
| Encoding | `multipart/form-data` |

## Message Sequence

```
Client                                  Server (C6)
   |                                        |
   |  1. TCP SYN                            |
   |--------------------------------------->|
   |                                        |
   |  2. TCP SYN-ACK                        |
   |<---------------------------------------|
   |                                        |
   |  3. TCP ACK                            |
   |--------------------------------------->|
   |                                        |
   |  4. HTTP POST /g1.html                 |
   |     (multipart/form-data)              |
   |--------------------------------------->|
   |                                        |
   |  5. TCP ACKs (flow-controlled upload)  |
   |<---------------------------------------|
   |        ... upload continues ...        |
   |                                        |
   |  6. Final data + boundary close        |
   |--------------------------------------->|
   |                                        |
   |  [~1-2s processing delay]              |
   |                                        |
   |  7. HTTP 200 OK (with status HTML)     |
   |<---------------------------------------|
   |                                        |
   |  8. TCP FIN                            |
   |--------------------------------------->|
   |                                        |
   |  9. TCP RST (server closes abruptly)   |
   |<---------------------------------------|
```

## HTTP Request Details

### Request Headers

```http
POST /g1.html HTTP/1.1
Host: <device-ip>
Connection: keep-alive
Content-Length: <body-size>
Content-Type: multipart/form-data; boundary=<boundary>
Origin: http://<device-ip>
Referer: http://<device-ip>/g1.html
Cache-Control: max-age=0
```

### Request Body Structure

```
--<boundary>
Content-Disposition: form-data; name="11111"; filename="<firmware-filename>"
Content-Type: application/octet-stream

<binary firmware data>
--<boundary>--
```

**Key Details:**
- Form field name: `11111` (fixed value)
- Accepted file extensions: `.bin`, `.mbin`, `.pbin`, `.rbin`, `.cfg`
- Firmware filename format: `C6_<main_ver>_<panel_ver>.mbin` (e.g., `C6_1_5_44_70_P1_1_1_5_46.mbin`)

### Example Firmware File Structure

The firmware binary contains:
- Binary payload (encrypted/compressed firmware data)
- Trailing ASCII signature: `5123456781234567800AA00AA00BB00BB\r\n`

| Offset | Content |
|--------|---------|
| 0x00000000 | Binary firmware data start |
| ... | Firmware payload |
| EOF - 35 | ASCII signature `5123456781234567800AA00AA00BB00BB\r\n` |

## HTTP Response Details

### Response Headers

```http
HTTP/1.1 200 OK
Server: C6
Connection: close
Content-Type: text/html
Content-Length: 973
Cache-Control: no-cache
```

### Response Body

HTML page containing the upload form with status message:

```html
<td id="st">Status: Firmware uploaded successfully, device is restarting. Panel firmware upload success: wait until finished.</td>
```

**Possible status messages:**
- `Status: Firmware uploaded successfully, device is restarting. Panel firmware upload success: wait until finished.`
- (Other error states should be documented as discovered)

## TCP/Protocol Characteristics

### Server TCP Limitations

| Feature | Support |
|---------|---------|
| Window Scaling | **No** |
| SACK | **No** |
| Timestamps | **No** |
| MSS | 1470 bytes |
| Receive Window | 735-1470 bytes (very small) |

### Timing Characteristics

| Phase | Duration | Notes |
|-------|----------|-------|
| TCP Handshake | ~5ms | Normal |
| Upload (1.1MB) | ~57s | Throttled by small server window |
| Server Processing | ~1-2s | Device flashes firmware |
| Response Delivery | ~15ms | Split across 3 TCP segments |

**Effective Upload Speed:** ~19 KB/s (157 kbps) due to small receive window.

## Protocol Issues and Violations

### 1. Delayed Server ACK (TIMING ISSUE)

The server stops acknowledging TCP data for ~1.7 seconds while processing the firmware upload:
- Last data packet: T+56.525s
- Server ACK: T+58.225s
- Gap: 1.7 seconds

**Impact:** Causes client TCP retransmissions (observed 2 retransmits of final packet).

**Mock Implementation Note:** Should delay final ACK by 1-2 seconds to simulate firmware processing.

### 2. RST Instead of FIN (PROTOCOL VIOLATION)

The server closes the connection with RST instead of proper FIN-ACK:
- Client sends: FIN-ACK
- Server responds: RST-ACK

**Impact:** Minor - connection is already complete. Some clients may log warnings.

**Mock Implementation Note:** Can safely use proper FIN-ACK closure.

### 3. Very Small Receive Window (PERFORMANCE LIMITATION)

Server advertises only 735 bytes receive window consistently throughout upload.

**Impact:** Severely throttles upload speed to ~19 KB/s.

**Mock Implementation Note:** Use small socket receive buffer (1-2KB) to replicate behavior.

### 4. No TCP Window Scaling

Server does not support RFC 1323 window scaling.

**Impact:** Combined with small window, limits throughput.

## Mock Endpoint Implementation Guide

### Server Requirements

```python
# Key server characteristics to replicate:
RECEIVE_BUFFER_SIZE = 1470  # bytes
PROCESSING_DELAY = 1.5      # seconds (simulate firmware flash)
SERVER_HEADER = "C6"
```

### Request Validation

1. Verify `POST /g1.html`
2. Parse `multipart/form-data` with boundary
3. Extract file from field `name="11111"`
4. Validate filename matches pattern: `*.bin`, `*.mbin`, `*.pbin`, `*.rbin`, `*.cfg`
5. Optionally validate firmware signature at EOF

### Response Generation

```python
def success_response():
    return """HTTP/1.1 200 OK
Server: C6
Connection: close
Content-Type: text/html
Content-Length: 973
Cache-Control: no-cache

<!DOCTYPE html><html><head><meta charset="windows-1252"><title>Komfovent</title></head>
<body>
<form class="f" method="post" enctype="multipart/form-data">
<table>
<tr><td><input type="file" name="11111" accept=".bin,.mbin,.pbin,.rbin,.cfg"></td></tr>
<tr><td><input type="submit" id="bs" value="Upload"></td></tr>
<tr><td id="st">Status: Firmware uploaded successfully, device is restarting. Panel firmware upload success: wait until finished.</td></tr>
</table>
</form>
</body></html>"""
```

## Mock Client Implementation Guide

### Upload Process

```python
import requests

def upload_firmware(host: str, firmware_path: str) -> bool:
    url = f"http://{host}/g1.html"

    with open(firmware_path, 'rb') as f:
        files = {
            '11111': (
                os.path.basename(firmware_path),
                f,
                'application/octet-stream'
            )
        }
        headers = {
            'Origin': f'http://{host}',
            'Referer': f'http://{host}/g1.html',
        }

        # Use longer timeout due to slow upload + processing
        response = requests.post(
            url,
            files=files,
            headers=headers,
            timeout=120  # 2 minutes for large files
        )

    return 'uploaded successfully' in response.text
```

### Expected Timing

| File Size | Upload Time | Total Time |
|-----------|-------------|------------|
| 500 KB | ~26s | ~28s |
| 1 MB | ~52s | ~54s |
| 1.5 MB | ~78s | ~80s |

### Error Handling

- **Connection timeout:** Server may be busy or unreachable
- **Read timeout:** Server processing delay can exceed 2s for large files
- **RST on close:** Normal behavior, ignore socket errors after response received

## Observed Packet Capture Summary

| Metric | Value |
|--------|-------|
| Total packets | 3076 |
| Request packets (with payload) | 1537 |
| Response packets (with payload) | 3 |
| Retransmissions | 2 (final boundary close) |
| Total request size | 1,124,696 bytes |
| Firmware file size | 1,123,678 bytes |
| Total duration | 58.243 seconds |

## Appendix: Raw Header Dumps

### Captured Request Headers

```
POST /g1.html HTTP/1.1
Host: 192.168.0.60
Connection: keep-alive
Content-Length: 1123896
Cache-Control: max-age=0
Origin: http://192.168.0.60
DNT: 1
Upgrade-Insecure-Requests: 1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary5RkmKlDPbZNgDa48
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8
Referer: http://192.168.0.60/g1.html
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9,et;q=0.8
```

### Captured Response Headers

```
HTTP/1.1 200 OK
Server: C6
Connection: close
Content-Type: text/html
Content-Length: 973
Cache-Control: no-cache
```
