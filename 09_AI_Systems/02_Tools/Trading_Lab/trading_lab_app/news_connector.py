"""Exact-endpoint HTTPS transport boundary for official publisher metadata."""

from dataclasses import dataclass
import http.client
import json
import multiprocessing
from multiprocessing.connection import wait
import socket
import struct
import threading
import time

from . import news_data, news_parser, news_sources


CONNECT_TIMEOUT_SECONDS = 5
READ_TIMEOUT_SECONDS = 10
ABSOLUTE_REQUEST_DEADLINE_SECONDS = 20
SOURCE_TERMINATE_JOIN_SECONDS = 0.5
SOURCE_KILL_JOIN_SECONDS = 0.5
SOURCE_CHILD_SHUTDOWN_BOUND_SECONDS = (
    SOURCE_TERMINATE_JOIN_SECONDS + SOURCE_KILL_JOIN_SECONDS
)
MAX_RESPONSE_BYTES = news_parser.MAX_RESPONSE_BYTES
MAX_IPC_METADATA_BYTES = 64 * 1024
MAX_IPC_MESSAGE_BYTES = MAX_RESPONSE_BYTES + MAX_IPC_METADATA_BYTES + 16
USER_AGENT = "ALSAKKAF-TRL/2.0-r2.004 local-official-news-metadata"
XML_CONTENT_TYPES = frozenset((
    "application/rss+xml", "application/atom+xml", "application/xml", "text/xml",
))
JSON_CONTENT_TYPES = frozenset(("application/json", "text/json"))
_IPC_SUCCESS = b"S"
_IPC_FAILURE = b"E"
_IPC_VERSION = 1
_CHILD_FAILURE_CODES = frozenset((
    "NEWS_PROVIDER_CHANGED", "NEWS_SOURCE_TIMEOUT", "NEWS_SOURCE_HTTP_ERROR",
    "NEWS_SOURCE_INTERNAL_ERROR", "NEWS_SOURCE_TOO_LARGE",
))


class RetrievalError(OSError):
    def __init__(self, reason_code):
        super().__init__(reason_code)
        self.reason_code = reason_code


class _HttpsCleanupFailure(Exception):
    """Private sentinel for ordinary child-local HTTPS cleanup failure."""


@dataclass(frozen=True)
class TransportResponse:
    status: int
    headers: dict
    body: bytes
    endpoint: str


def _close_https_resources(response, connection):
    """Attempt both closes and convert only ordinary failures to a sentinel."""
    response_close_failed = False
    connection_close_failed = False
    try:
        if response is not None:
            try:
                response.close()
            except Exception:
                response_close_failed = True
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                connection_close_failed = True
    if response_close_failed or connection_close_failed:
        raise _HttpsCleanupFailure()


def _direct_https_get(source):
    """Perform one governed HTTPS operation inside the owned source child."""
    try:
        hostname, path = news_sources.validated_endpoint_parts(source)
    except news_sources.SourceRegistryError as error:
        raise RetrievalError("NEWS_PROVIDER_CHANGED") from error
    endpoint = source["exact_endpoint"]
    if not news_sources.endpoint_is_allowlisted(source, endpoint):
        raise RetrievalError("NEWS_PROVIDER_CHANGED")
    connection = http.client.HTTPSConnection(
        hostname, timeout=CONNECT_TIMEOUT_SECONDS,
    )
    response = None
    try:
        connection.request(
            "GET", path,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, application/json",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        if connection.sock is not None:
            connection.sock.settimeout(READ_TIMEOUT_SECONDS)
        response = connection.getresponse()
        if connection.sock is not None:
            connection.sock.settimeout(READ_TIMEOUT_SECONDS)
        chunks = []
        total = 0
        while True:
            chunk = response.read(min(65536, MAX_RESPONSE_BYTES + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                raise RetrievalError("NEWS_SOURCE_TOO_LARGE")
            chunks.append(chunk)
        headers = {
            name.lower(): value.strip() for name, value in response.getheaders()
        }
        result = TransportResponse(
            response.status, headers, b"".join(chunks), endpoint,
        )
    except (TimeoutError, socket.timeout) as error:
        try:
            _close_https_resources(response, connection)
        except _HttpsCleanupFailure:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from None
        raise RetrievalError("NEWS_SOURCE_TIMEOUT") from error
    except RetrievalError:
        try:
            _close_https_resources(response, connection)
        except _HttpsCleanupFailure:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from None
        raise
    except (OSError, http.client.HTTPException) as error:
        try:
            _close_https_resources(response, connection)
        except _HttpsCleanupFailure:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from None
        raise RetrievalError("NEWS_SOURCE_HTTP_ERROR") from error
    except Exception:
        try:
            _close_https_resources(response, connection)
        except _HttpsCleanupFailure:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from None
        raise
    except BaseException:
        try:
            _close_https_resources(response, connection)
        except _HttpsCleanupFailure:
            pass
        raise
    try:
        _close_https_resources(response, connection)
    except _HttpsCleanupFailure:
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from None
    return result


def _encode_child_success(response):
    if (
        type(response) is not TransportResponse
        or type(response.status) is not int
        or not 100 <= response.status <= 599
        or type(response.body) is not bytes
        or len(response.body) > MAX_RESPONSE_BYTES
    ):
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    metadata = json.dumps(
        {
            "endpoint": response.endpoint,
            "headers": response.headers,
            "status": response.status,
            "version": _IPC_VERSION,
        },
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(metadata) > MAX_IPC_METADATA_BYTES:
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    return _IPC_SUCCESS + struct.pack("!I", len(metadata)) + metadata + response.body


def _encode_child_failure(reason_code):
    selected = (
        reason_code
        if reason_code in _CHILD_FAILURE_CODES
        else "NEWS_SOURCE_INTERNAL_ERROR"
    )
    return _IPC_FAILURE + selected.encode("ascii")


def source_child_main(source, send_connection):
    """Windows-spawn-compatible child target for exactly one governed source."""
    try:
        try:
            payload = _encode_child_success(_direct_https_get(source))
        except RetrievalError as error:
            payload = _encode_child_failure(error.reason_code)
        except Exception:
            payload = _encode_child_failure("NEWS_SOURCE_INTERNAL_ERROR")
        try:
            send_connection.send_bytes(payload)
        except (OSError, TypeError, ValueError, OverflowError):
            pass
    finally:
        try:
            send_connection.close()
        except Exception:
            pass


def _decode_child_payload(payload, source):
    if type(payload) is not bytes or not payload:
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    if payload[:1] == _IPC_FAILURE:
        try:
            reason_code = payload[1:].decode("ascii", errors="strict")
        except UnicodeError as error:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
        if reason_code not in _CHILD_FAILURE_CODES:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
        raise RetrievalError(reason_code)
    if payload[:1] != _IPC_SUCCESS or len(payload) < 5:
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    metadata_length = struct.unpack("!I", payload[1:5])[0]
    if metadata_length > MAX_IPC_METADATA_BYTES or 5 + metadata_length > len(payload):
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    metadata_bytes = payload[5:5 + metadata_length]
    body = payload[5 + metadata_length:]
    if len(body) > MAX_RESPONSE_BYTES:
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    try:
        metadata = json.loads(metadata_bytes.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
    if (
        type(metadata) is not dict
        or set(metadata) != {"endpoint", "headers", "status", "version"}
        or metadata["version"] != _IPC_VERSION
        or type(metadata["endpoint"]) is not str
        or metadata["endpoint"] != source["exact_endpoint"]
        or type(metadata["status"]) is not int
        or not 100 <= metadata["status"] <= 599
        or type(metadata["headers"]) is not dict
        or any(type(key) is not str or type(value) is not str for key, value in metadata["headers"].items())
    ):
        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
    return TransportResponse(
        metadata["status"], dict(metadata["headers"]), body, metadata["endpoint"],
    )


class _OwnedSourceChild:
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FINALIZING = "FINALIZING"
    FINALIZED = "FINALIZED"

    def __init__(self, process, receive_connection, send_connection):
        self.process = process
        self.receive_connection = receive_connection
        self.send_connection = send_connection
        self.lock = threading.Lock()
        self.start_complete = threading.Event()
        self.finalized = threading.Event()
        self.state = self.STARTING
        self.started = False
        self.cancelled = False
        self.join_called = False
        self.process_close_called = False
        self.receive_close_called = False
        self.send_close_called = False
        self.exitcode = None
        self.cleanup_failed = False
        self.finalizer_count = 0


def _process_is_alive(process):
    try:
        return process.is_alive()
    except Exception:
        return False


class DirectHttpsTransport:
    """Own one terminable spawn child for each complete source operation."""

    def __init__(
        self, process_context=None, child_target=source_child_main,
        monotonic=None, wait_function=None,
    ):
        self._context = process_context or multiprocessing.get_context("spawn")
        self._child_target = child_target
        self._monotonic = monotonic or time.monotonic
        self._wait = wait_function or wait
        self._children = set()
        self._children_lock = threading.Lock()
        self._closed = False

    def _discard_child(self, record):
        with self._children_lock:
            self._children.discard(record)

    @staticmethod
    def _cancel_child(record):
        with record.lock:
            if record.state != record.FINALIZED:
                record.cancelled = True

    @staticmethod
    def _child_is_cancelled(record):
        with record.lock:
            return record.cancelled

    def _wait_for_child_exit(self, record, timeout, cancel_aware=False):
        """Wait on the process sentinel without consuming the one allowed join."""
        process = record.process
        if not _process_is_alive(process):
            return True
        # Cleanup cannot depend on the injectable retrieval-deadline clock:
        # that collaborator may itself be the post-start failure being cleaned.
        deadline = None if timeout is None else time.monotonic() + timeout
        while _process_is_alive(process):
            if cancel_aware and self._child_is_cancelled(record):
                return False
            if deadline is None:
                interval = SOURCE_KILL_JOIN_SECONDS
            else:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return not _process_is_alive(process)
                interval = min(0.05, remaining)
            try:
                ready = self._wait((process.sentinel,), timeout=interval)
            except Exception:
                return False
            if process.sentinel in ready:
                return True
        return True

    def _retrieval_now(self):
        """Read the injectable retrieval clock with an explicit internal code."""
        try:
            return self._monotonic()
        except Exception as error:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error

    def _stop_child(self, record):
        """Stop a started child without joining; the finalizer joins once later."""
        process = record.process
        if not _process_is_alive(process):
            return
        try:
            process.terminate()
        except Exception:
            record.cleanup_failed = True
        if self._wait_for_child_exit(record, SOURCE_TERMINATE_JOIN_SECONDS):
            return
        try:
            process.kill()
        except Exception:
            record.cleanup_failed = True
        if self._wait_for_child_exit(record, SOURCE_KILL_JOIN_SECONDS):
            return
        while _process_is_alive(process):
            try:
                process.kill()
            except Exception:
                record.cleanup_failed = True
            self._wait_for_child_exit(record, SOURCE_KILL_JOIN_SECONDS)

    def _finalize_child(self, record, graceful_timeout=None):
        """Join and close one exact record once; repeated calls are harmless."""
        with record.lock:
            if record.state == record.FINALIZED:
                return record.exitcode, record.cleanup_failed
            if record.state == record.FINALIZING:
                finalized = record.finalized
                owns_finalization = False
            else:
                record.state = record.FINALIZING
                record.finalizer_count += 1
                finalized = record.finalized
                owns_finalization = True
        if not owns_finalization:
            finalized.wait()
            return record.exitcode, record.cleanup_failed

        process = record.process
        try:
            if record.started:
                graceful = not self._child_is_cancelled(record)
                if graceful:
                    graceful = self._wait_for_child_exit(
                        record, graceful_timeout, cancel_aware=True,
                    )
                if not graceful or _process_is_alive(process):
                    self._stop_child(record)
                try:
                    record.join_called = True
                    process.join()
                except Exception:
                    record.cleanup_failed = True
                try:
                    record.exitcode = process.exitcode
                except Exception:
                    record.cleanup_failed = True
        finally:
            if not record.receive_close_called:
                record.receive_close_called = True
                try:
                    record.receive_connection.close()
                except Exception:
                    record.cleanup_failed = True
            if not record.send_close_called:
                record.send_close_called = True
                try:
                    record.send_connection.close()
                except Exception:
                    record.cleanup_failed = True
            if not record.process_close_called:
                record.process_close_called = True
                try:
                    process.close()
                except Exception:
                    record.cleanup_failed = True
            with record.lock:
                record.state = record.FINALIZED
                record.finalized.set()
            self._discard_child(record)
        return record.exitcode, record.cleanup_failed

    def active_child_count(self):
        with self._children_lock:
            return sum(
                record.state != record.FINALIZED
                and record.started
                and _process_is_alive(record.process)
                for record in self._children
            )

    def active_process_handle_count(self):
        with self._children_lock:
            return sum(
                not record.process_close_called for record in self._children
            )

    def active_ipc_handle_count(self):
        with self._children_lock:
            return sum(
                int(not record.receive_close_called)
                + int(not record.send_close_called)
                for record in self._children
            )

    def child_record_count(self):
        with self._children_lock:
            return len(self._children)

    def close(self):
        with self._children_lock:
            self._closed = True
            records = list(self._children)
        for record in records:
            self._cancel_child(record)
        for record in records:
            record.finalized.wait()

    def get(self, source):
        try:
            news_sources.validated_endpoint_parts(source)
        except news_sources.SourceRegistryError as error:
            raise RetrievalError("NEWS_PROVIDER_CHANGED") from error
        if not news_sources.endpoint_is_allowlisted(source, source["exact_endpoint"]):
            raise RetrievalError("NEWS_PROVIDER_CHANGED")
        receive_connection = None
        send_connection = None
        process = None
        with self._children_lock:
            if self._closed:
                raise RetrievalError("NEWS_SOURCE_TIMEOUT")
            try:
                receive_connection, send_connection = self._context.Pipe(duplex=False)
                process = self._context.Process(
                    target=self._child_target,
                    args=(source, send_connection),
                    name="trl-news-source-{}".format(source["source_id"]),
                    daemon=False,
                )
                record = _OwnedSourceChild(
                    process, receive_connection, send_connection,
                )
                self._children.add(record)
            except Exception as error:
                for connection in (receive_connection, send_connection):
                    if connection is not None:
                        try:
                            connection.close()
                        except Exception:
                            pass
                if process is not None:
                    try:
                        process.close()
                    except Exception:
                        pass
                raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error

        try:
            try:
                process.start()
            except BaseException as error:
                record.start_complete.set()
                self._finalize_child(record)
                if isinstance(error, Exception):
                    raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
                raise
            with record.lock:
                record.started = True
                record.state = record.RUNNING
                cancelled = record.cancelled
                record.start_complete.set()
            if cancelled:
                raise RetrievalError("NEWS_SOURCE_TIMEOUT")
            deadline = self._retrieval_now() + ABSOLUTE_REQUEST_DEADLINE_SECONDS
            payload = None
            while payload is None:
                if self._child_is_cancelled(record):
                    raise RetrievalError("NEWS_SOURCE_TIMEOUT")
                remaining = deadline - self._retrieval_now()
                if remaining <= 0:
                    raise RetrievalError("NEWS_SOURCE_TIMEOUT")
                try:
                    ready = self._wait(
                        (receive_connection, process.sentinel),
                        timeout=min(0.05, remaining),
                    )
                except Exception as error:
                    raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
                if not ready:
                    continue
                if receive_connection in ready:
                    try:
                        payload = receive_connection.recv_bytes(MAX_IPC_MESSAGE_BYTES)
                    except EOFError as error:
                        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
                    except OSError as error:
                        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
                    except Exception as error:
                        raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR") from error
                elif process.sentinel in ready:
                    try:
                        if receive_connection.poll(0):
                            payload = receive_connection.recv_bytes(MAX_IPC_MESSAGE_BYTES)
                            continue
                    except Exception:
                        pass
                    raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
            remaining = max(0.0, deadline - self._retrieval_now())
            exitcode, cleanup_failed = self._finalize_child(
                record, graceful_timeout=remaining,
            )
            if self._child_is_cancelled(record):
                raise RetrievalError("NEWS_SOURCE_TIMEOUT")
            if cleanup_failed or exitcode != 0:
                raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
            return _decode_child_payload(payload, source)
        except BaseException:
            self._cancel_child(record)
            raise
        finally:
            if not record.start_complete.is_set():
                record.start_complete.set()
            self._finalize_child(record)


class OfficialNewsConnector:
    def __init__(self, transport=None):
        self._transport = transport or DirectHttpsTransport()
        self._hostname_locks = {}
        self._hostname_waiters = {}
        self._hostname_locks_guard = threading.Lock()
        self._closed = False

    def _hostname_lock(self, hostname):
        """Return bounded connector-owned admission after source validation."""
        with self._hostname_locks_guard:
            if self._closed:
                raise RetrievalError("NEWS_SOURCE_TIMEOUT")
            lock = self._hostname_locks.get(hostname)
            if lock is None:
                lock = threading.Lock()
                self._hostname_locks[hostname] = lock
                self._hostname_waiters[hostname] = 0
            return lock

    def _acquire_hostname(self, hostname):
        lock = self._hostname_lock(hostname)
        if lock.acquire(blocking=False):
            return lock
        with self._hostname_locks_guard:
            self._hostname_waiters[hostname] += 1
        try:
            lock.acquire()
        finally:
            with self._hostname_locks_guard:
                self._hostname_waiters[hostname] -= 1
        return lock

    def hostname_state_count(self):
        with self._hostname_locks_guard:
            return len(self._hostname_locks)

    def hostname_waiter_count(self):
        with self._hostname_locks_guard:
            return sum(self._hostname_waiters.values())

    def held_hostname_lock_count(self):
        with self._hostname_locks_guard:
            locks = tuple(self._hostname_locks.values())
        return sum(lock.locked() for lock in locks)

    def close(self):
        with self._hostname_locks_guard:
            if self._closed:
                return
            self._closed = True
        closer = getattr(self._transport, "close", None)
        if closer is not None:
            closer()

    def retrieve(self, source, retrieved_timestamp_utc):
        try:
            hostname, _path = news_sources.validated_endpoint_parts(source)
        except news_sources.SourceRegistryError as error:
            raise RetrievalError("NEWS_PROVIDER_CHANGED") from error
        if not news_sources.endpoint_is_allowlisted(source, source["exact_endpoint"]):
            raise RetrievalError("NEWS_PROVIDER_CHANGED")
        hostname_lock = self._acquire_hostname(hostname)
        try:
            with self._hostname_locks_guard:
                if self._closed:
                    raise RetrievalError("NEWS_SOURCE_TIMEOUT")
            response = self._transport.get(source)
        finally:
            hostname_lock.release()
        if type(response) is not TransportResponse:
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
        if (
            type(response.endpoint) is not str
            or type(response.status) is not int
            or not 100 <= response.status <= 599
            or type(response.headers) is not dict
            or any(
                type(key) is not str or type(value) is not str
                for key, value in response.headers.items()
            )
            or type(response.body) is not bytes
        ):
            raise RetrievalError("NEWS_SOURCE_INTERNAL_ERROR")
        if response.endpoint != source["exact_endpoint"]:
            raise RetrievalError("NEWS_SOURCE_REDIRECT_BLOCKED")
        if not 200 <= response.status <= 299:
            if 300 <= response.status <= 399:
                raise RetrievalError("NEWS_SOURCE_REDIRECT_BLOCKED")
            raise RetrievalError("NEWS_SOURCE_HTTP_ERROR")
        body = response.body
        if len(body) > MAX_RESPONSE_BYTES:
            raise RetrievalError("NEWS_SOURCE_TOO_LARGE")
        headers = {str(key).lower(): str(value).strip() for key, value in response.headers.items()}
        if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
            raise RetrievalError("NEWS_SOURCE_CONTENT_TYPE_INVALID")
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        accepted = JSON_CONTENT_TYPES if source["format"] == "JSON" else XML_CONTENT_TYPES
        if content_type not in accepted:
            raise RetrievalError("NEWS_SOURCE_CONTENT_TYPE_INVALID")
        try:
            if source["format"] == "JSON":
                events = news_parser.parse_bea_release_dates(
                    body, source, retrieved_timestamp_utc,
                )
                return [], events
            items = news_parser.parse_xml_news(body, source, retrieved_timestamp_utc)
            return items, []
        except news_data.NewsValidationError as error:
            raise RetrievalError(error.reason_code) from error
