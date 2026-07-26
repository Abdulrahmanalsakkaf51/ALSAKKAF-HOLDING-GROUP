"""Minimal allowlisted localhost HTTP server for the TRL application."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import APPLICATION_NAME
from . import service


BIND_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"

STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}

API_ROUTES = {
    "/api/health": service.health_document,
    "/api/version": service.version_document,
    "/api/capabilities": service.capabilities_document,
    "/api/strategy-registry": service.strategy_registry_document,
    "/api/demo/market-data": service.market_data_document,
    "/api/demo/result": service.demo_result,
    "/api/demo/report": service.report_document,
}

SECURITY_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'none'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
        "form-action 'none'"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def deterministic_json_bytes(value):
    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")


class ApplicationHandler(BaseHTTPRequestHandler):
    """Serve only known static assets and fixed read-only API documents."""

    server_version = "ALSAKKAF-TRL-Local/2.0"
    sys_version = ""

    def _write_headers(self, status, content_type, content_length, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        if extra:
            for name, value in extra.items():
                self.send_header(name, value)
        self.end_headers()

    def _send_bytes(self, status, body, content_type, extra=None):
        self._write_headers(status, content_type, len(body), extra=extra)
        self.wfile.write(body)

    def _send_json(self, status, value):
        self._send_bytes(
            status,
            deterministic_json_bytes(value),
            "application/json; charset=utf-8",
        )

    def _local_host_header(self):
        host = self.headers.get("Host", "")
        host_name = host.rsplit(":", 1)[0].lower()
        return host_name in {"127.0.0.1", "localhost"}

    def do_GET(self):
        if not self._local_host_header():
            self._send_json(421, {"error": "LOCAL_HOST_REQUIRED"})
            return
        raw_path = urlsplit(self.path).path
        decoded_path = unquote(raw_path)
        if decoded_path != raw_path or ".." in decoded_path or "\\" in decoded_path:
            self._send_json(400, {"error": "INVALID_PATH"})
            return
        api_function = API_ROUTES.get(decoded_path)
        if api_function is not None:
            try:
                self._send_json(200, api_function())
            except (OSError, ValueError, TypeError, ImportError) as error:
                self._send_json(500, {
                    "error": "LOCAL_DEMO_UNAVAILABLE",
                    "detail": str(error),
                })
            return
        static_route = STATIC_ROUTES.get(decoded_path)
        if static_route is not None:
            filename, content_type = static_route
            body = (STATIC_DIRECTORY / filename).read_bytes()
            self._send_bytes(200, body, content_type)
            return
        self._send_json(404, {"error": "NOT_FOUND"})

    def _method_not_allowed(self):
        body = deterministic_json_bytes({"error": "METHOD_NOT_ALLOWED"})
        self._send_bytes(
            405,
            body,
            "application/json; charset=utf-8",
            extra={"Allow": "GET"},
        )

    do_HEAD = _method_not_allowed
    do_POST = _method_not_allowed
    do_PUT = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_DELETE = _method_not_allowed
    do_OPTIONS = _method_not_allowed
    do_CONNECT = _method_not_allowed
    do_TRACE = _method_not_allowed

    def log_message(self, format_string, *args):
        """Keep local requests quiet; startup and shutdown remain explicit."""
        return


class LocalApplicationServer(HTTPServer):
    """IPv4 server with a fixed loopback bind boundary."""

    allow_reuse_address = False


def create_server(port=DEFAULT_PORT, handler_class=ApplicationHandler):
    """Create, but do not start, a server bound exclusively to loopback."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("port must be an integer from 0 through 65535")
    return LocalApplicationServer((BIND_HOST, port), handler_class)
