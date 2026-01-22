"""
Mock Komfovent C6 Firmware Upload Server.

Simulates the C6 device's firmware upload endpoint for testing purposes.
Based on packet capture analysis documented in documentation/C6-firmware-upload.md

Usage:
    uv run mock_c6_server.py [--host 0.0.0.0] [--port 8060]

Then test with:
    uv run validate_firmware_update.py --host localhost:8060 --firmware test.mbin
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Server configuration (from packet capture analysis)
SERVER_NAME = "C6"
DEFAULT_PROCESSING_DELAY = 1.5  # seconds - simulate firmware flash time
VALID_EXTENSIONS = {".bin", ".mbin", ".pbin", ".rbin", ".cfg"}
FORM_FIELD_NAME = "11111"

# Default credentials (can be overridden via environment or CLI)
DEFAULT_USERNAME = os.getenv("MOCK_C6_USERNAME", "user")
DEFAULT_PASSWORD = os.getenv("MOCK_C6_PASSWORD", "user")

# Network binding
DEFAULT_HOST = "0.0.0.0"  # noqa: S104
DEFAULT_PORT = 8060

# HTML Templates
LOGIN_FORM_TEMPLATE = """<!DOCTYPE html><html><head>
<meta charset="windows-1252"><title>Komfovent</title>
<style>
body{{background-color:#f4f4f4;font-family:Verdana;margin:300px auto 0;width:300px}}
form *{{display:block;margin:5px auto}}
div{{color:red;height:40px;line-height:40px;text-align:center}}
input{{border-width:0;color:#333;font-family:Verdana;height:30px;padding-left:10px;width:180px}}
input[type=submit]{{background-color:#777;color:#eee;cursor:pointer;margin-top:15px;
padding:0;text-align:center;width:110px}}
input[type=submit]:hover{{background-color:#333}}
</style></head>
<body><form method="POST">
<div><p style="{error_style}">Incorrect password!</p></div>
<input type="text" name="1" value="user" maxlength="7">
<input type="password" name="2" value="">
<input type="submit" value="Login"></form></body></html>"""

UPLOAD_FORM_TEMPLATE = """<!DOCTYPE html><html><head>
<meta charset="windows-1252"><title>Komfovent</title></head>
<body>
<form class="l" method="post" action="/">
<label>user <input name="4" value="Logout" type="submit"></label>
</form>
<form class="f" method="post" enctype="multipart/form-data">
<table>
<tr><td><input type="file" name="{field_name}"
accept=".bin,.mbin,.pbin,.rbin,.cfg"></td></tr>
<tr><td><input type="submit" id="bs" value="Upload"></td></tr>
<tr><td id="st">{status}</td></tr>
</table>
</form>
</body></html>"""

SUCCESS_STATUS = (
    "Status: Firmware uploaded successfully, device is restarting. "
    "Panel firmware upload success: wait until finished."
)


class C6MockHandler(BaseHTTPRequestHandler):
    """HTTP request handler simulating C6 firmware upload endpoint."""

    server: C6MockServer
    server_version = "C6"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Override to use our logger."""
        logger.info("%s - %s", self.address_string(), format % args)

    def is_authenticated(self) -> bool:
        """Check if client IP is authenticated."""
        client_ip = self.client_address[0]
        return client_ip in self.server.authenticated_ips

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user and track session by IP."""
        if username == self.server.username and password == self.server.password:
            client_ip = self.client_address[0]
            self.server.authenticated_ips.add(client_ip)
            logger.info("Authenticated client: %s", client_ip)
            return True
        return False

    def logout(self) -> None:
        """Remove client from authenticated sessions."""
        client_ip = self.client_address[0]
        self.server.authenticated_ips.discard(client_ip)
        logger.info("Logged out client: %s", client_ip)

    def send_c6_headers(self, content_length: int, status: int = 200) -> None:
        """Send response headers matching C6 device."""
        self.send_response(status)
        self.send_header("Server", SERVER_NAME)
        self.send_header("Connection", "close")
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

    def _send_response(self, response: str, status: int = 200) -> None:
        """Send a response with proper headers."""
        self.send_c6_headers(len(response), status)
        self.wfile.write(response.encode())

    def do_GET(self) -> None:
        """Handle GET request - serve login or upload form."""
        if self.path == "/g1.html":
            if self.is_authenticated():
                response = self.get_upload_form()
            else:
                response = self.get_login_form()
            self._send_response(response)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        """Handle POST request - login, logout, or firmware upload."""
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if self.path == "/":
            self._handle_logout(content_length)
        elif self.path != "/g1.html":
            self.send_error(404, "Not Found")
        elif "application/x-www-form-urlencoded" in content_type:
            self._handle_login(content_length)
        elif "multipart/form-data" in content_type:
            self._handle_firmware_upload(content_type, content_length)
        else:
            logger.error("Invalid Content-Type: %s", content_type)
            self._send_response(self.get_error_response("Invalid content type"), 400)

    def _handle_logout(self, content_length: int) -> None:
        """Handle logout POST request."""
        body = self.rfile.read(content_length)
        if b"4=Logout" in body:
            self.logout()
        self._send_response(self.get_login_form())

    def _handle_login(self, content_length: int) -> None:
        """Handle login POST request."""
        body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)

        username = params.get("1", [""])[0]
        password = params.get("2", [""])[0]

        if self.authenticate(username, password):
            response = self.get_upload_form()
        else:
            logger.warning("Login failed for user: %s", username)
            response = self.get_login_form(show_error=True)

        self._send_response(response)

    def _handle_firmware_upload(self, content_type: str, content_length: int) -> None:
        """Handle firmware upload POST request."""
        if not self.is_authenticated():
            logger.warning(
                "Unauthenticated upload attempt from %s", self.client_address[0]
            )
            self._send_response(self.get_login_form())
            return

        boundary_match = re.search(r"boundary=([^\s;]+)", content_type)
        if not boundary_match:
            logger.error("No boundary in Content-Type")
            self._send_response(self.get_error_response("Missing boundary"), 400)
            return

        boundary = boundary_match.group(1).encode()
        logger.info("Receiving firmware upload: %d bytes", content_length)

        body = self.rfile.read(content_length)
        result = self.parse_multipart(body, boundary)

        if result is None:
            self._send_response(self.get_error_response("Failed to parse upload"), 400)
            return

        filename, file_data = result
        if not self._validate_and_process_firmware(filename, file_data):
            return

        self._send_response(self.get_success_response())
        logger.info("Firmware upload complete: %s", filename)

    def _validate_and_process_firmware(
        self, filename: str, file_data: bytes
    ) -> bool:
        """Validate firmware and process upload."""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in VALID_EXTENSIONS:
            logger.error("Invalid file extension: %s", ext)
            self._send_response(
                self.get_error_response(f"Invalid file type: {ext}"), 400
            )
            return False

        self.server.last_upload = {
            "filename": filename,
            "size": len(file_data),
            "timestamp": time.time(),
        }

        logger.info("Received firmware: %s (%d bytes)", filename, len(file_data))

        delay = self.server.processing_delay
        logger.info("Processing firmware (%.1fs delay)...", delay)
        time.sleep(delay)

        return True

    def parse_multipart(
        self, body: bytes, boundary: bytes
    ) -> tuple[str, bytes] | None:
        """Parse multipart form data and extract file."""
        parts = body.split(b"--" + boundary)

        for part in parts:
            if not part or part.strip() in (b"", b"--", b"--\r\n"):
                continue

            if b"\r\n\r\n" in part:
                headers_section, content = part.split(b"\r\n\r\n", 1)
            elif b"\n\n" in part:
                headers_section, content = part.split(b"\n\n", 1)
            else:
                continue

            headers_str = headers_section.decode("utf-8", errors="replace")

            if f'name="{FORM_FIELD_NAME}"' in headers_str:
                filename_match = re.search(r'filename="([^"]+)"', headers_str)
                if filename_match:
                    filename = filename_match.group(1)
                    if content.endswith(b"\r\n"):
                        content = content[:-2]
                    elif content.endswith(b"\n"):
                        content = content[:-1]
                    return filename, content

        return None

    def get_login_form(self, *, show_error: bool = False) -> str:
        """Generate the login form HTML (matches real device)."""
        error_style = "" if show_error else "display:none"
        return LOGIN_FORM_TEMPLATE.format(error_style=error_style)

    def get_upload_form(self, status_message: str = "") -> str:
        """Generate the upload form HTML (matches real device)."""
        status = status_message if status_message else "Status:"
        return UPLOAD_FORM_TEMPLATE.format(field_name=FORM_FIELD_NAME, status=status)

    def get_success_response(self) -> str:
        """Generate success response HTML."""
        return self.get_upload_form(SUCCESS_STATUS)

    def get_error_response(self, error: str) -> str:
        """Generate error response HTML."""
        return self.get_upload_form(f"Status: Firmware upload error: {error}")


class C6MockServer(HTTPServer):
    """Mock C6 server with configurable settings."""

    def __init__(
        self,
        server_address: tuple[str, int],
        processing_delay: float = DEFAULT_PROCESSING_DELAY,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
    ) -> None:
        """
        Initialize the mock C6 server.

        Args:
            server_address: Tuple of (host, port) to bind to
            processing_delay: Simulated firmware processing delay in seconds
            username: Login username
            password: Login password

        """
        super().__init__(server_address, C6MockHandler)
        self.processing_delay = processing_delay
        self.username = username
        self.password = password
        self.authenticated_ips: set[str] = set()
        self.last_upload: dict | None = None


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    delay: float = DEFAULT_PROCESSING_DELAY,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
) -> None:
    """Run the mock C6 server."""
    server_address = (host, port)
    httpd = C6MockServer(
        server_address,
        processing_delay=delay,
        username=username,
        password=password,
    )

    display_host = host if host != DEFAULT_HOST else "localhost"
    logger.info("=" * 60)
    logger.info("Mock Komfovent C6 Server")
    logger.info("=" * 60)
    logger.info("Listening on http://%s:%d", display_host, port)
    logger.info("Upload endpoint: http://%s:%d/g1.html", display_host, port)
    logger.info("Credentials: %s / %s", username, password)
    logger.info("")
    logger.info("Test with:")
    logger.info("  curl -X POST -d '1=user&2=user' http://localhost:%d/g1.html", port)
    logger.info("  curl -F '11111=@firmware.mbin' http://localhost:%d/g1.html", port)
    logger.info("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
        httpd.shutdown()


def main() -> None:
    """Run the mock C6 server with CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Mock Komfovent C6 Firmware Upload Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This server simulates the C6 device's firmware upload endpoint for testing.
Supports IP-based authentication matching real device behavior.

Examples:
  # Start server on default port 8060
  uv run mock_c6_server.py

  # Start on custom port with custom credentials
  uv run mock_c6_server.py --port 8080 --username admin --password secret
        """,
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind to (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_PROCESSING_DELAY,
        help=f"Firmware processing delay in seconds (default: {DEFAULT_PROCESSING_DELAY})",  # noqa: E501
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help=f"Login username (default: {DEFAULT_USERNAME})",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"Login password (default: {DEFAULT_PASSWORD})",
    )

    args = parser.parse_args()

    run_server(args.host, args.port, args.delay, args.username, args.password)


if __name__ == "__main__":
    main()
