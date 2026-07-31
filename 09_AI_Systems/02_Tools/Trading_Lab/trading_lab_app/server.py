"""Minimal allowlisted localhost HTTP server for the TRL application."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import socket
from socketserver import ThreadingMixIn
import threading
from urllib.parse import unquote, urlsplit

from . import APPLICATION_NAME
from . import service
from .mode_service import in_memory_mode_service
from .mt5_service import MarketDataService
from .news_service import OfficialNewsService
from .paper_service import DisabledPaperService


BIND_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_HTTP_REQUEST_WORKERS = 16
CLIENT_REQUEST_READ_TIMEOUT_SECONDS = 5.0
CLIENT_SHUTDOWN_BOUND_SECONDS = 6.0
CLIENT_REQUEST_HEADER_DEADLINE_SECONDS = 10.0
CLIENT_HEADER_DEADLINE_SHUTDOWN_BOUND_SECONDS = 11.0
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

MARKET_API_ROUTES = {
    "/api/market-connection": service.market_connection_document,
    "/api/market-snapshot": service.market_snapshot_document,
}

NEWS_API_ROUTES = {
    "/api/news-health": service.news_health_document,
    "/api/news-sources": service.news_sources_document,
    "/api/news-items": service.news_items_document,
    "/api/economic-events": service.economic_events_document,
}

PAPER_API_ROUTES = {
    "/api/paper-account": service.paper_account_document,
    "/api/paper-positions": service.paper_positions_document,
    "/api/paper-history": service.paper_history_document,
    "/api/market-timeline": service.market_timeline_document,
    "/api/paper-health": service.paper_health_document,
}

MODE_API_ROUTES = {
    "/api/mode-status": service.mode_status_document,
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

    def setup(self):
        super().setup()

    def _begin_header_deadline(self):
        return self.server.ensure_header_deadline(self.request)

    def _cancel_header_deadline(self):
        return self.server.cancel_header_deadline(self.request)

    def handle_one_request(self):
        """Apply inactivity and absolute bounds only through header parsing."""
        headers_complete = False
        if not self._begin_header_deadline():
            self.close_connection = True
            return
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ""
                self.request_version = ""
                self.command = ""
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            if not self._cancel_header_deadline():
                self.close_connection = True
                return
            headers_complete = True
            method_name = "do_" + self.command
            if not hasattr(self, method_name):
                self.send_error(501, "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, method_name)
            method()
            self.wfile.flush()
        except (TimeoutError, OSError):
            self.close_connection = True
            return
        finally:
            if not headers_complete:
                self._cancel_header_deadline()

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

    def _send_bytes(self, status, body, content_type, extra=None, include_body=True):
        self._write_headers(status, content_type, len(body), extra=extra)
        if include_body:
            self.wfile.write(body)

    def _send_json(self, status, value, include_body=True):
        self._send_bytes(
            status,
            deterministic_json_bytes(value),
            "application/json; charset=utf-8",
            include_body=include_body,
        )

    def _local_host_header(self):
        host = self.headers.get("Host", "")
        host_name = host.rsplit(":", 1)[0].lower()
        return host_name in {"127.0.0.1", "localhost"}

    def _handle_read(self, include_body):
        if not self._local_host_header():
            self._send_json(421, {"error": "LOCAL_HOST_REQUIRED"}, include_body)
            return
        raw_path = urlsplit(self.path).path
        decoded_path = unquote(raw_path)
        if decoded_path != raw_path or ".." in decoded_path or "\\" in decoded_path:
            self._send_json(400, {"error": "INVALID_PATH"}, include_body)
            return
        market_function = MARKET_API_ROUTES.get(decoded_path)
        if market_function is not None:
            try:
                self._send_json(
                    200,
                    market_function(self.server.market_data_service),
                    include_body,
                )
            except (OSError, ValueError, TypeError, ImportError):
                self._send_json(
                    500,
                    {"error": "LOCAL_MARKET_DATA_UNAVAILABLE"},
                    include_body,
                )
            return
        news_function = NEWS_API_ROUTES.get(decoded_path)
        if news_function is not None:
            try:
                self._send_json(
                    200,
                    news_function(self.server.official_news_service),
                    include_body,
                )
            except (OSError, ValueError, TypeError, ImportError):
                self._send_json(
                    500,
                    {"error": "LOCAL_OFFICIAL_NEWS_UNAVAILABLE"},
                    include_body,
                )
            return
        paper_function = PAPER_API_ROUTES.get(decoded_path)
        if paper_function is not None:
            try:
                self._send_json(
                    200,
                    paper_function(self.server.paper_service),
                    include_body,
                )
            except (OSError, ValueError, TypeError, RuntimeError):
                self._send_json(
                    500,
                    {"error": "LOCAL_PAPER_ENGINE_UNAVAILABLE"},
                    include_body,
                )
            return
        mode_function = MODE_API_ROUTES.get(decoded_path)
        if mode_function is not None:
            try:
                self._send_json(
                    200,
                    mode_function(self.server.mode_service),
                    include_body,
                )
            except (OSError, ValueError, TypeError, RuntimeError):
                self._send_json(
                    500,
                    {"error": "LOCAL_MODE_SERVICE_UNAVAILABLE"},
                    include_body,
                )
            return
        api_function = API_ROUTES.get(decoded_path)
        if api_function is not None:
            try:
                self._send_json(200, api_function(), include_body)
            except (OSError, ValueError, TypeError, ImportError):
                self._send_json(
                    500,
                    {"error": "LOCAL_DEMO_UNAVAILABLE"},
                    include_body,
                )
            return
        static_route = STATIC_ROUTES.get(decoded_path)
        if static_route is not None:
            filename, content_type = static_route
            body = (STATIC_DIRECTORY / filename).read_bytes()
            self._send_bytes(200, body, content_type, include_body=include_body)
            return
        self._send_json(404, {"error": "NOT_FOUND"}, include_body)

    def do_GET(self):
        self._handle_read(include_body=True)

    def do_HEAD(self):
        raw_path = urlsplit(self.path).path
        decoded_path = unquote(raw_path)
        if (
            decoded_path in MARKET_API_ROUTES
            or decoded_path in NEWS_API_ROUTES
            or decoded_path in PAPER_API_ROUTES
            or decoded_path in MODE_API_ROUTES
        ):
            self._handle_read(include_body=False)
            return
        self._method_not_allowed()

    def _method_not_allowed(self):
        body = deterministic_json_bytes({"error": "METHOD_NOT_ALLOWED"})
        decoded_path = unquote(urlsplit(self.path).path)
        allowed_methods = (
            "GET, HEAD"
            if (
                decoded_path in MARKET_API_ROUTES
                or decoded_path in NEWS_API_ROUTES
                or decoded_path in PAPER_API_ROUTES
                or decoded_path in MODE_API_ROUTES
            )
            else "GET"
        )
        self._send_bytes(
            405,
            body,
            "application/json; charset=utf-8",
            extra={"Allow": allowed_methods},
        )

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


class _DeadlineOwnership:
    """One exact timer token retained until cancellation and callback completion."""

    def __init__(self):
        self.timer = None
        self.timer_started = False
        self.expired = False
        self.callback_running = False
        self.cleanup_claimed = False
        self.cleanup_complete = False


class _HandlerOwnership:
    """One admitted request, its current deadline, and its handler join token."""

    def __init__(self, request):
        self.request = request
        self.deadline = None
        self.thread = None
        self.start_resolved = False
        self.started = False
        self.active = True
        self.socket_close_claimed = False
        self.permit_release_claimed = False
        self.join_claimed = False
        self.join_complete = False


class _HandlerOwnershipRegistry:
    """Bounded lifecycle registry for admitted handlers and their deadlines."""

    def __init__(self):
        self.condition = threading.Condition()
        self.records = {}
        self.pending_starts = 0
        self.closing = False

    def _discard_if_complete_locked(self, record):
        if record.active or not record.start_resolved:
            return
        if record.deadline is not None:
            return
        if record.started and not record.join_complete:
            return
        if self.records.get(record.request) is record:
            del self.records[record.request]

    def _complete_joins(self, records):
        try:
            for record in records:
                record.thread.join()
                with self.condition:
                    record.join_complete = True
                    self._discard_if_complete_locked(record)
                    self.condition.notify_all()
        except BaseException:
            with self.condition:
                for record in records:
                    if not record.join_complete:
                        record.join_claimed = False
                self.condition.notify_all()
            raise

    def reap_finished(self):
        """Join completed handlers before discarding their exact records."""
        current = threading.current_thread()
        with self.condition:
            records = tuple(
                record
                for record in self.records.values()
                if record.started
                and not record.join_claimed
                and not record.join_complete
                and record.thread is not current
                and not record.thread.is_alive()
            )
            for record in records:
                record.join_claimed = True
        self._complete_joins(records)

    def admit(self, request):
        with self.condition:
            if self.closing:
                return None
            record = _HandlerOwnership(request)
            self.records[request] = record
            self.pending_starts += 1
            return record

    def attach_thread(self, record, thread):
        with self.condition:
            record.thread = thread

    def resolve_start(self, record, started):
        with self.condition:
            record.started = started
            record.start_resolved = True
            self.pending_starts -= 1
            self._discard_if_complete_locked(record)
            self.condition.notify_all()

    def finish_handler(self, record):
        with self.condition:
            record.active = False
            self._discard_if_complete_locked(record)
            self.condition.notify_all()

    def lookup(self, request):
        with self.condition:
            return self.records.get(request)

    def active_count(self):
        with self.condition:
            return sum(record.active for record in self.records.values())

    def active_deadline_count(self):
        with self.condition:
            return sum(
                record.deadline is not None
                and not record.deadline.expired
                and not record.deadline.cleanup_claimed
                for record in self.records.values()
            )

    def deadline_record_count(self):
        with self.condition:
            return sum(
                record.deadline is not None for record in self.records.values()
            )

    def claim_socket_close(self, record):
        with self.condition:
            if record.socket_close_claimed:
                return False
            record.socket_close_claimed = True
            return True

    def claim_permit_release(self, record):
        with self.condition:
            if record.permit_release_claimed:
                return False
            record.permit_release_claimed = True
            return True

    def begin_close(self):
        with self.condition:
            self.closing = True
            self.condition.notify_all()

    def join(self):
        """Join each successful handler once, without joining the caller."""
        current = threading.current_thread()
        self.begin_close()
        while True:
            with self.condition:
                while self.pending_starts:
                    self.condition.wait()
                if any(
                    record.started and record.thread is current
                    for record in self.records.values()
                ):
                    return
                records = tuple(
                    record
                    for record in self.records.values()
                    if record.started
                    and not record.join_claimed
                    and not record.join_complete
                    and record.thread is not current
                )
                for record in records:
                    record.join_claimed = True
                if not records:
                    outstanding = any(
                        record.started
                        and not record.join_complete
                        and record.thread is not current
                        for record in self.records.values()
                    )
                    if not outstanding:
                        return
                    self.condition.wait()
                    continue
            self._complete_joins(records)

    def __iter__(self):
        with self.condition:
            return iter(tuple(
                record.thread
                for record in self.records.values()
                if record.started and not record.join_complete
            ))


class LocalApplicationServer(ThreadingMixIn, HTTPServer):
    """Bounded threaded IPv4 server with a fixed loopback bind boundary."""

    allow_reuse_address = False
    daemon_threads = False
    block_on_close = True
    request_queue_size = MAX_HTTP_REQUEST_WORKERS
    client_request_read_timeout_seconds = CLIENT_REQUEST_READ_TIMEOUT_SECONDS
    client_request_header_deadline_seconds = CLIENT_REQUEST_HEADER_DEADLINE_SECONDS
    handler_thread_factory = threading.Thread
    deadline_timer_factory = threading.Timer

    def __init__(self, server_address, handler_class):
        self._request_slots = threading.BoundedSemaphore(MAX_HTTP_REQUEST_WORKERS)
        self._ownership = _HandlerOwnershipRegistry()
        self._overflow_rejection_count = 0
        self._overflow_rejection_lock = threading.Lock()
        self._threads = self._ownership
        super().__init__(server_address, handler_class)

    def get_request(self):
        request, client_address = super().get_request()
        try:
            request.settimeout(self.client_request_read_timeout_seconds)
        except BaseException:
            request.close()
            raise
        return request, client_address

    def process_request(self, request, client_address):
        self._ownership.reap_finished()
        if not self._request_slots.acquire(blocking=False):
            self._reject_overflow_request(request)
            return
        record = self._ownership.admit(request)
        if record is None:
            self._request_slots.release()
            self._close_request_socket(request)
            return
        deadline = None
        try:
            deadline = self._ensure_header_deadline(record)
            thread = self.handler_thread_factory(
                target=self.process_request_thread,
                args=(record, client_address),
            )
            thread.daemon = self.daemon_threads
            self._ownership.attach_thread(record, thread)
            thread.start()
        except BaseException:
            self._cleanup_deadline(record, deadline)
            self._finalize_admitted_request(record)
            self._ownership.resolve_start(record, False)
            raise
        self._ownership.resolve_start(record, True)

    def process_request_thread(self, record, client_address):
        try:
            self.finish_request(record.request, client_address)
        except Exception:
            self.handle_error(record.request, client_address)
        finally:
            self._finalize_admitted_request(record)

    @staticmethod
    def _close_request_socket(request):
        try:
            request.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            request.close()
        except OSError:
            pass

    def _reject_overflow_request(self, request):
        with self._overflow_rejection_lock:
            self._overflow_rejection_count += 1
        self._close_request_socket(request)

    def _close_owned_request(self, record):
        if self._ownership.claim_socket_close(record):
            self._close_request_socket(record.request)

    def _release_admitted_request(self, record):
        if self._ownership.claim_permit_release(record):
            self._request_slots.release()

    def _expire_header_deadline(self, record, deadline):
        with self._ownership.condition:
            if (
                record.deadline is not deadline
                or deadline.cleanup_complete
                or deadline.cleanup_claimed
            ):
                return
            deadline.expired = True
            deadline.callback_running = True
        try:
            self._close_owned_request(record)
        finally:
            with self._ownership.condition:
                deadline.callback_running = False
                self._ownership.condition.notify_all()

    def _ensure_header_deadline(self, record):
        with self._ownership.condition:
            if record.deadline is not None:
                return record.deadline
            deadline = _DeadlineOwnership()
            timer = self.deadline_timer_factory(
                self.client_request_header_deadline_seconds,
                lambda: self._expire_header_deadline(record, deadline),
            )
            timer.name = "trl-http-header-deadline"
            timer.daemon = False
            deadline.timer = timer
            record.deadline = deadline
        try:
            timer.start()
        except BaseException:
            raise
        with self._ownership.condition:
            deadline.timer_started = True
        return deadline

    def ensure_header_deadline(self, request):
        """Keep one exact deadline token per admitted header parse."""
        record = self._ownership.lookup(request)
        if record is None:
            return False
        deadline = self._ensure_header_deadline(record)
        with self._ownership.condition:
            return not deadline.expired and not deadline.cleanup_claimed

    def _cleanup_deadline(self, record, deadline=None):
        current = threading.current_thread()
        with self._ownership.condition:
            deadline = deadline or record.deadline
            if deadline is None:
                return True
            if deadline.timer is current:
                return not deadline.expired
            while deadline.cleanup_claimed and not deadline.cleanup_complete:
                self._ownership.condition.wait()
            if deadline.cleanup_complete:
                return not deadline.expired
            deadline.cleanup_claimed = True
            timer = deadline.timer
            timer_started = deadline.timer_started
        timer.cancel()
        if timer_started:
            timer.join()
        with self._ownership.condition:
            deadline.cleanup_complete = True
            if record.deadline is deadline:
                record.deadline = None
            self._ownership._discard_if_complete_locked(record)
            self._ownership.condition.notify_all()
            return not deadline.expired

    def cancel_header_deadline(self, request):
        record = self._ownership.lookup(request)
        if record is None:
            return False
        return self._cleanup_deadline(record)

    def _finalize_admitted_request(self, record):
        self._cleanup_deadline(record)
        self._close_owned_request(record)
        self._release_admitted_request(record)
        self._ownership.finish_handler(record)

    def active_request_count(self):
        return self._ownership.active_count()

    def active_header_deadline_count(self):
        return self._ownership.active_deadline_count()

    def deadline_record_count(self):
        return self._ownership.deadline_record_count()

    def queued_accepted_connection_count(self):
        return 0

    def overflow_rejection_count(self):
        with self._overflow_rejection_lock:
            return self._overflow_rejection_count

    def server_close(self):
        self._ownership.begin_close()
        super().server_close()


def create_server(
    port=DEFAULT_PORT,
    handler_class=ApplicationHandler,
    market_data_service=None,
    official_news_service=None,
    paper_service=None,
    mode_service=None,
):
    """Create, but do not start, a server bound exclusively to loopback."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("port must be an integer from 0 through 65535")
    local_server = LocalApplicationServer((BIND_HOST, port), handler_class)
    local_server.market_data_service = market_data_service or MarketDataService()
    local_server.official_news_service = official_news_service or OfficialNewsService()
    local_server.paper_service = paper_service or DisabledPaperService()
    # Defaults to an in-memory mode service (starts at OFF, touches no
    # filesystem) when the caller does not explicitly wire one in, mirroring
    # DisabledPaperService's no-side-effect-by-default philosophy. Real
    # startup (app.py main()) always passes an explicit, durable one.
    local_server.mode_service = mode_service or in_memory_mode_service()
    return local_server
