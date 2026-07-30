# -*- coding: utf-8 -*-
"""Offline acceptance tests for TRL-R2-004 official news and events."""

import copy
from datetime import datetime, timedelta, timezone
import http.client
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock


BASE = Path(__file__).resolve().parent
APP_DIRECTORY = BASE / "trading_lab_app"
STATIC_DIRECTORY = APP_DIRECTORY / "static"
FIXED_NOW = datetime(2026, 7, 27, 12, 0, 0, tzinfo=timezone.utc)
sys.path.insert(0, str(BASE))

from trading_lab_app import app, capabilities, server  # noqa: E402
from trading_lab_app import news_cache, news_data, news_parser, news_sources  # noqa: E402
from trading_lab_app.news_connector import (  # noqa: E402
    ABSOLUTE_REQUEST_DEADLINE_SECONDS, MAX_IPC_MESSAGE_BYTES,
    READ_TIMEOUT_SECONDS,
    DirectHttpsTransport, OfficialNewsConnector, RetrievalError,
    TransportResponse, _direct_https_get, _encode_child_success,
    source_child_main,
)
from trading_lab_app.news_service import (  # noqa: E402
    NEWS_REFRESH_WORKERS, STABLE_HEALTH_CODES, OfficialNewsConfiguration,
    OfficialNewsService,
)


RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
<title>Official &amp; governed release</title>
<link>https://www.federalreserve.gov/newsevents/pressreleases/example.htm</link>
<pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate>
<description><![CDATA[<script>bad()</script><img src="track">Body not retained]]></description>
</item></channel></rss>"""

ATOM_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<title><![CDATA[Atom <b>official</b> update]]></title>
<link href="https://www.ecb.europa.eu/press/example/html/index.en.html"/>
<updated>2026-07-27T10:30:00Z</updated><content>Not retained</content>
</entry></feed>"""

BEA_BODY = json.dumps({
    "release_dates": [{
        "ReleaseDate": "2026-07-30",
        "ReleaseName": "Gross Domestic Product",
        "ReleaseURL": "https://www.bea.gov/news/example",
    }]
}, separators=(",", ":")).encode("utf-8")


class FakeClock:
    def __init__(self, value=FIXED_NOW):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


class FakeTransport:
    def __init__(self, responses=None, default=None):
        self.responses = dict(responses or {})
        self.default = default
        self.calls = []

    def get(self, source):
        endpoint = source["exact_endpoint"]
        self.calls.append(endpoint)
        value = self.responses.get(endpoint, self.default)
        if isinstance(value, Exception):
            raise value
        if callable(value):
            value = value(source)
        if value is None:
            raise RetrievalError("NEWS_SOURCE_HTTP_ERROR")
        return copy.deepcopy(value)


class InvalidJsonCacheStorage:
    def __init__(self, raw):
        self.raw = raw
        self.load_count = 0
        self.write_count = 0
        self.value = None

    def load(self):
        self.load_count += 1
        return news_cache.decode_cache_bytes(self.raw)

    def write(self, value):
        self.write_count += 1
        self.value = copy.deepcopy(value)


class InspectingCacheStorage(news_cache.InMemoryCacheStorage):
    def __init__(self, forbidden_text):
        super().__init__()
        self.forbidden_text = forbidden_text
        self.invalid_candidate_writes = 0

    def write(self, value):
        if self.forbidden_text in json.dumps(value, ensure_ascii=False):
            self.invalid_candidate_writes += 1
        super().write(value)


class GateCacheStorage(news_cache.InMemoryCacheStorage):
    def __init__(self, fail_write=False):
        super().__init__()
        self.write_started = threading.Event()
        self.release_write = threading.Event()
        self.fail_after_release = fail_write

    def write(self, value):
        self.write_started.set()
        if not self.release_write.wait(5):
            raise news_cache.CacheError("NEWS_CACHE_WRITE_FAILED")
        if self.fail_after_release:
            raise news_cache.CacheError("NEWS_CACHE_WRITE_FAILED")
        super().write(value)


class CountingFileCacheStorage(news_cache.FileCacheStorage):
    """Production-like atomic storage with observable test-only counters."""

    def __init__(self, path, fail_write=False):
        super().__init__(path)
        self.fail_write = fail_write
        self.write_attempt_count = 0
        self.write_count = 0

    def write(self, value):
        self.write_attempt_count += 1
        if self.fail_write:
            raise news_cache.CacheError("NEWS_CACHE_WRITE_FAILED")
        super().write(value)
        self.write_count += 1


class ConcurrentGateTransport(FakeTransport):
    def __init__(self, responses):
        super().__init__(responses)
        self.release = threading.Event()
        self.more_than_one_active = threading.Event()
        self.all_workers_active = threading.Event()
        self._activity_lock = threading.Lock()
        self.active = 0
        self.maximum_active = 0

    def get(self, source):
        with self._activity_lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
            if self.active > 1:
                self.more_than_one_active.set()
            if self.active == NEWS_REFRESH_WORKERS:
                self.all_workers_active.set()
        try:
            if not self.release.wait(timeout=10):
                raise RetrievalError("NEWS_SOURCE_TIMEOUT")
            return super().get(source)
        finally:
            with self._activity_lock:
                self.active -= 1


class CompletionOrderTransport(FakeTransport):
    def __init__(self, responses, source_order):
        super().__init__(responses)
        self._source_order = list(source_order)
        self._next = 0
        self._condition = threading.Condition()

    def get(self, source):
        deadline = time.monotonic() + 10
        with self._condition:
            while self._source_order[self._next] != source["source_id"]:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RetrievalError("NEWS_SOURCE_TIMEOUT")
                self._condition.wait(remaining)
            self._next += 1
            self._condition.notify_all()
        return super().get(source)


class AwaitingOfficialNewsService(OfficialNewsService):
    """Keep legacy acceptance assertions synchronous; focused tests use production."""

    def _refresh_if_permitted(self):
        super()._refresh_if_permitted()
        self.wait_for_refresh(10)


def blocked_source_child(_source, send_connection):
    """Spawn-safe deterministic stand-in for blocked DNS/connect/TLS or I/O."""
    try:
        threading.Event().wait(60)
    finally:
        send_connection.close()


def dns_blocked_source_child(source, send_connection):
    blocked_source_child(source, send_connection)


def connection_without_socket_source_child(source, send_connection):
    blocked_source_child(source, send_connection)


def tls_status_header_trickle_source_child(source, send_connection):
    blocked_source_child(source, send_connection)


def body_trickle_source_child(source, send_connection):
    blocked_source_child(source, send_connection)


BLOCKING_CHILD_TARGETS = frozenset((
    blocked_source_child,
    dns_blocked_source_child,
    connection_without_socket_source_child,
    tls_status_header_trickle_source_child,
    body_trickle_source_child,
))


def successful_source_child(source, send_connection):
    """Spawn-safe deterministic successful IPC child."""
    try:
        selected_type = (
            "application/json" if source["format"] == "JSON"
            else "application/rss+xml"
        )
        payload = _encode_child_success(TransportResponse(
            200,
            {"content-type": selected_type},
            b"",
            source["exact_endpoint"],
        ))
        send_connection.send_bytes(payload)
    finally:
        send_connection.close()


def crashing_source_child(_source, _send_connection):
    os._exit(17)


def malformed_source_child(_source, send_connection):
    try:
        send_connection.send_bytes(b"malformed")
    finally:
        send_connection.close()


def oversized_source_child(_source, send_connection):
    try:
        send_connection.send_bytes(b"x" * (MAX_IPC_MESSAGE_BYTES + 1))
    finally:
        send_connection.close()


class _FakePipeChannel:
    def __init__(self):
        self.condition = threading.Condition()
        self.payload = None
        self.writer_count = 1
        self.writer_closed = False


class _FakeSendConnection:
    def __init__(self, channel):
        self.channel = channel
        self.closed = False

    def clone(self):
        with self.channel.condition:
            self.channel.writer_count += 1
        return _FakeSendConnection(self.channel)

    def send_bytes(self, payload):
        if self.closed:
            raise OSError("fake pipe is closed")
        with self.channel.condition:
            self.channel.payload = bytes(payload)
            self.channel.condition.notify_all()

    def close(self):
        if self.closed:
            return
        self.closed = True
        with self.channel.condition:
            self.channel.writer_count -= 1
            if self.channel.writer_count == 0:
                self.channel.writer_closed = True
            self.channel.condition.notify_all()


class _FakeReceiveConnection:
    def __init__(self, channel):
        self.channel = channel
        self.closed = False

    def is_ready(self):
        with self.channel.condition:
            return (
                self.channel.payload is not None
                or self.channel.writer_closed
                or self.closed
            )

    def poll(self, _timeout=0):
        return self.is_ready()

    def recv_bytes(self, maxlength):
        with self.channel.condition:
            if self.channel.payload is None:
                raise EOFError("fake pipe reached EOF")
            payload = self.channel.payload
            self.channel.payload = None
        if len(payload) > maxlength:
            raise OSError("fake IPC payload exceeds maxlength")
        return payload

    def close(self):
        self.closed = True
        with self.channel.condition:
            self.channel.condition.notify_all()


class _FakeProcess:
    def __init__(self, context, target, args, name, daemon):
        self.context = context
        self.target = target
        self.args = (args[0], args[1].clone())
        self.name = name
        self.daemon = daemon
        self.sentinel = threading.Event()
        self.stop = threading.Event()
        self.thread = None
        self.exitcode = None
        self.closed = False

    def _run(self):
        try:
            if self.target in BLOCKING_CHILD_TARGETS:
                self.stop.wait(60)
                self.exitcode = -15
            elif self.target is crashing_source_child:
                if self.context.exit_gate is not None:
                    self.context.exit_gate.wait(60)
                self.exitcode = 17
            else:
                self.target(*self.args)
                if self.context.exit_gate is not None:
                    self.context.exit_gate.wait(60)
                self.exitcode = 0
        except BaseException:
            self.exitcode = 1
        finally:
            self.args[1].close()
            self.sentinel.set()

    def start(self):
        self.context.start_count += 1
        self.context.start_entered.set()
        if self.context.start_hook is not None:
            self.context.start_hook()
        if self.context.start_gate is not None:
            self.context.start_gate.wait(60)
        if self.context.start_error is not None:
            raise self.context.start_error
        self.thread = threading.Thread(
            target=self._run, name="fake-" + self.name, daemon=False,
        )
        self.thread.start()

    def is_alive(self):
        return self.thread is not None and self.thread.is_alive()

    def terminate(self):
        self.context.terminate_count += 1
        self.stop.set()

    def kill(self):
        self.context.kill_count += 1
        self.stop.set()

    def join(self, timeout=None):
        self.context.join_count += 1
        if self.thread is not None:
            self.thread.join(timeout)

    def close(self):
        if self.is_alive():
            raise ValueError("cannot close a live fake process")
        if not self.closed:
            self.closed = True
            self.context.process_close_count += 1


class FakeProcessContext:
    def __init__(
        self, start_error=None, start_gate=None, start_hook=None,
        exit_gate=None,
    ):
        self.processes = []
        self.start_error = start_error
        self.start_gate = start_gate
        self.start_hook = start_hook
        self.exit_gate = exit_gate
        self.start_entered = threading.Event()
        self.start_count = 0
        self.join_count = 0
        self.terminate_count = 0
        self.kill_count = 0
        self.process_close_count = 0

    def Pipe(self, duplex=False):
        if duplex is not False:
            raise AssertionError("source IPC must remain unidirectional")
        channel = _FakePipeChannel()
        return _FakeReceiveConnection(channel), _FakeSendConnection(channel)

    def Process(self, target, args, name, daemon):
        process = _FakeProcess(self, target, args, name, daemon)
        self.processes.append(process)
        return process

    def active_count(self):
        return sum(process.is_alive() for process in self.processes)

    def open_process_handle_count(self):
        return sum(not process.closed for process in self.processes)


def fake_process_wait(objects, timeout):
    deadline = time.monotonic() + timeout
    while True:
        ready = []
        for item in objects:
            if hasattr(item, "is_ready") and item.is_ready():
                ready.append(item)
            elif hasattr(item, "is_set") and item.is_set():
                ready.append(item)
        if ready or time.monotonic() >= deadline:
            return ready
        threading.Event().wait(min(0.005, deadline - time.monotonic()))


def response(source, body=None, content_type=None, status=200, endpoint=None, headers=None):
    selected_body = body
    if selected_body is None:
        selected_body = BEA_BODY if source["format"] == "JSON" else RSS_BODY
    selected_type = content_type
    if selected_type is None:
        selected_type = "application/json" if source["format"] == "JSON" else "application/rss+xml"
    values = {"content-type": selected_type}
    values.update(headers or {})
    return TransportResponse(status, values, selected_body, endpoint or source["exact_endpoint"])


def valid_transport(registry=None):
    registry = registry or news_sources.load_source_registry()
    return FakeTransport({
        source["exact_endpoint"]: response(source) for source in registry["sources"]
    })


def enabled_service(
    transport=None, clock=None, cache=None, refresh=900, asynchronous=False,
):
    service_class = OfficialNewsService if asynchronous else AwaitingOfficialNewsService
    return service_class(
        OfficialNewsConfiguration(True, refresh),
        transport=transport or valid_transport(),
        clock=clock or FakeClock(),
        cache_storage=cache or news_cache.InMemoryCacheStorage(),
    )


def operating_system_temporary_file(prefix):
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".json")
    os.close(descriptor)
    return Path(name)


def cached_wrapper(record, kind, seen="2026-07-27T12:00:00Z"):
    id_field = "news_id" if kind == "news" else "event_id"
    return {
        "kind": kind,
        "identity": record[id_field],
        "fingerprint": news_data.observation_fingerprint(record),
        "first_seen_timestamp_utc": seen,
        "last_seen_timestamp_utc": seen,
        "record": copy.deepcopy(record),
    }


def cached_document(*wrappers, saved="2026-07-27T12:00:00Z"):
    document = news_cache.empty_document(saved)
    document["records"] = [copy.deepcopy(wrapper) for wrapper in wrappers]
    return document


def governed_cache_fixtures():
    registry = news_sources.load_source_registry()
    fed = next(
        source for source in registry["sources"]
        if source["source_id"] == "FED_MONETARY_POLICY_RSS"
    )
    bea = next(
        source for source in registry["sources"]
        if source["source_id"] == "BEA_RELEASE_DATES_JSON"
    )
    news = news_data.news_item(
        fed, "Governed cached news",
        "https://www.federalreserve.gov/newsevents/pressreleases/cache.htm",
        "2026-07-27T10:00:00Z", "2026-07-27T12:00:00Z",
    )
    event = news_data.economic_event(
        bea, "Governed cached event", "2026-07-30", None,
        "2026-07-27T12:00:00Z", None,
    )
    return registry, news, event


def adversarial_cache_documents():
    registry, valid_news, valid_event = governed_cache_fixtures()

    def changed(record, kind, mutation):
        candidate = copy.deepcopy(record)
        mutation(candidate)
        return cached_document(cached_wrapper(candidate, kind))

    def governed_external(record, url):
        record["source_url"] = url
        record["source_url_availability_status"] = "GOVERNED_ITEM_LINK_AVAILABLE"
        record["source_url_reason_code"] = "SOURCE_ITEM_LINK_HOST_GOVERNED"
        record["identity_basis"] = "GOVERNED_ITEM_URL"
        record["identity_ambiguity_reason"] = None
        record["news_id"] = news_data.stable_identifier(
            "NEWS", (record["source_id"], url)
        )
        record["limitations"] = record["limitations"][:3]

    cases = [
        ("missing_source_id", changed(valid_news, "news", lambda item: item.pop("source_id"))),
        ("unknown_extra_field", changed(valid_news, "news", lambda item: item.update({"unexpected": "value"}))),
        ("wrong_exact_type", changed(valid_news, "news", lambda item: item.update({"currency_tags": ("USD",)}))),
        ("boolean_revision", changed(valid_news, "news", lambda item: item.update({"revision_number": True}))),
        ("unknown_source_id", changed(valid_news, "news", lambda item: item.update({
            "source_id": "UNKNOWN_SOURCE",
            "news_id": news_data.stable_identifier("NEWS", ("UNKNOWN_SOURCE", item["source_url"])),
        }))),
        ("publisher_mismatch", changed(valid_news, "news", lambda item: item.update({"publisher": "Impostor"}))),
        ("region_mismatch", changed(valid_news, "news", lambda item: item.update({"country_or_region": "ZZ"}))),
        ("currency_mismatch", changed(valid_news, "news", lambda item: item.update({"currency_tags": ["EUR"]}))),
        ("category_mismatch", changed(valid_news, "news", lambda item: item.update({"source_category": "UNAUTHORIZED"}))),
        ("arbitrary_external_governed", changed(valid_news, "news", lambda item: governed_external(item, "https://example.invalid/article"))),
        ("ungoverned_self_consistent", changed(valid_news, "news", lambda item: governed_external(item, "https://attacker.invalid/self-consistent"))),
        ("overbound_query_self_consistent", changed(
            valid_news,
            "news",
            lambda item: governed_external(
                item,
                "https://www.federalreserve.gov/release?q="
                + "x" * (news_data.MAX_QUERY_LENGTH + 1),
            ),
        )),
        ("encoded_control_self_consistent", changed(
            valid_news,
            "news",
            lambda item: governed_external(
                item,
                "https://www.federalreserve.gov/release%0Ahidden",
            ),
        )),
        ("fallback_url_mismatch", changed(
            news_data.news_item(
                next(source for source in registry["sources"] if source["source_id"] == "BEA_NEWS_RELEASE_RSS"),
                "Fallback", None, None, "2026-07-27T12:00:00Z",
            ),
            "news", lambda item: item.update({"source_url": "https://apps.bea.gov/not-the-endpoint"}),
        )),
        ("fallback_reason_mismatch", changed(
            news_data.news_item(
                next(source for source in registry["sources"] if source["source_id"] == "BEA_NEWS_RELEASE_RSS"),
                "Fallback", None, None, "2026-07-27T12:00:00Z",
            ),
            "news", lambda item: item.update({"source_url_reason_code": "SOURCE_ITEM_LINK_HOST_GOVERNED"}),
        )),
        ("stable_id_mismatch", changed(valid_news, "news", lambda item: item.update({"news_id": "NEWS-000000000000000000000000"}))),
        ("identity_basis_mismatch", changed(valid_news, "news", lambda item: item.update({"identity_basis": "SOURCE_FALLBACK_TITLE_ONLY"}))),
        ("invalid_timestamp", changed(valid_news, "news", lambda item: item.update({"published_timestamp_utc": "not-a-timestamp"}))),
        ("invalid_schedule_precision", changed(valid_event, "event", lambda item: item.update({"scheduled_time_precision": "MONTH_ONLY"}))),
        ("incompatible_event_schema", changed(valid_event, "event", lambda item: item.update({"schema_version": "TRL-OFFICIAL-ECONOMIC-EVENT-1.2"}))),
        ("event_series_id_mismatch", changed(valid_event, "event", lambda item: item.update({"event_series_id": "EVENT-SERIES-000000000000000000000000"}))),
        ("event_occurrence_id_mismatch", changed(valid_event, "event", lambda item: item.update({"event_id": "EVENT-000000000000000000000000"}))),
        ("missing_reason_mismatch", changed(valid_event, "event", lambda item: item["missing_value_reasons"].update({"actual": None}))),
        ("boolean_optional_number", changed(valid_event, "event", lambda item: (item.update({"actual": True}), item["missing_value_reasons"].update({"actual": None})))),
        ("cached_operational_freshness", changed(valid_news, "news", lambda item: item.update({"operational_freshness_status": "NEWS_RECORD_CURRENT"}))),
    ]
    for label, value in (
        ("nan", float("nan")),
        ("positive_infinity", float("inf")),
        ("negative_infinity", float("-inf")),
    ):
        record = copy.deepcopy(valid_event)
        record["actual"] = value
        record["missing_value_reasons"]["actual"] = None
        wrapper = cached_wrapper(valid_event, "event")
        wrapper["record"] = record
        cases.append((label, cached_document(wrapper)))
    return registry, valid_news, valid_event, cases


class RegistryAndNetworkBoundaryTests(unittest.TestCase):
    def test_exact_immutable_source_allowlist(self):
        registry = news_sources.load_source_registry()
        self.assertTrue(registry["immutable"])
        self.assertEqual(
            {item["source_id"]: item["exact_endpoint"] for item in registry["sources"]},
            news_sources.EXPECTED_SOURCE_ENDPOINTS,
        )
        self.assertEqual(registry["registry_version"], "TRL-OFFICIAL-NEWS-SOURCES-1.1")
        for item in registry["sources"]:
            self.assertTrue(item["exact_endpoint"].startswith("https://"))
            self.assertEqual(item["authentication_requirement"], "NO_API_KEY_REQUIRED")
            self.assertEqual(item["terms_review_date"], "2026-07-27")
            self.assertEqual(
                tuple(item["permitted_item_link_hostnames"]),
                news_sources.EXPECTED_ITEM_LINK_HOSTNAMES[item["source_id"]],
            )

    def test_retrieval_endpoint_and_item_link_hosts_are_independent(self):
        registry = news_sources.load_source_registry()
        source = next(item for item in registry["sources"] if item["source_id"] == "BEA_NEWS_RELEASE_RSS")
        self.assertEqual(source["exact_hostname"], "apps.bea.gov")
        self.assertTrue(news_sources.endpoint_is_allowlisted(source, source["exact_endpoint"]))
        self.assertTrue(news_sources.item_link_host_is_allowlisted(source, "www.bea.gov"))
        self.assertFalse(news_sources.item_link_host_is_allowlisted(source, "apps.bea.gov"))
        altered_endpoint = copy.deepcopy(source)
        altered_endpoint["exact_endpoint"] = "https://www.bea.gov/rss/rss.xml"
        self.assertFalse(news_sources.endpoint_is_allowlisted(altered_endpoint, altered_endpoint["exact_endpoint"]))
        altered_links = copy.deepcopy(source)
        altered_links["permitted_item_link_hostnames"] = ["apps.bea.gov"]
        self.assertFalse(news_sources.item_link_host_is_allowlisted(altered_links, "apps.bea.gov"))

    def test_ungoverned_and_unsafe_item_links_use_explicit_safe_fallback(self):
        source = next(
            item for item in news_sources.load_source_registry()["sources"]
            if item["source_id"] == "BEA_NEWS_RELEASE_RSS"
        )
        cases = (
            ("https://example.invalid/item", "SOURCE_ITEM_LINK_HOST_NOT_GOVERNED"),
            ("http://www.bea.gov/item", "SOURCE_ITEM_LINK_HTTPS_REQUIRED"),
            ("https://user:secret@www.bea.gov/item", "SOURCE_ITEM_LINK_CREDENTIALS_REJECTED"),
            ("https://www.bea.gov:444/item", "SOURCE_ITEM_LINK_UNSAFE_PORT"),
            ("https://www.bea.gov/item#fragment", "SOURCE_ITEM_LINK_FRAGMENT_REJECTED"),
            ("https://www.bea.gov/item with space", "SOURCE_ITEM_LINK_MALFORMED"),
        )
        for value, reason in cases:
            with self.subTest(reason=reason):
                url, status, actual_reason = news_data.governed_official_url(value, source)
                self.assertEqual(url, source["exact_endpoint"])
                self.assertEqual(status, "SOURCE_ENDPOINT_FALLBACK")
                self.assertEqual(actual_reason, reason)
        body = b"<rss><channel><item><title>Untrusted link</title><link>https://example.invalid/item</link></item></channel></rss>"
        item = news_parser.parse_xml_news(body, source, "2026-07-27T12:00:00Z")[0]
        self.assertEqual(item["source_url"], source["exact_endpoint"])
        self.assertEqual(item["source_url_availability_status"], "SOURCE_ENDPOINT_FALLBACK")
        self.assertEqual(item["source_url_reason_code"], "SOURCE_ITEM_LINK_HOST_NOT_GOVERNED")

    def test_governed_query_urls_are_preserved_bounded_and_identity_bearing(self):
        registry = news_sources.load_source_registry()
        source = registry["sources"][0]
        first_url = "https://www.federalreserve.gov/release?id=1"
        second_url = "https://www.federalreserve.gov/release?id=2"
        first = news_data.news_item(
            source, "Query release", first_url,
            "2026-07-27T10:00:00Z", "2026-07-27T12:00:00Z",
        )
        second = news_data.news_item(
            source, "Query release", second_url,
            "2026-07-27T10:00:00Z", "2026-07-27T12:00:00Z",
        )
        repeated = news_data.news_item(
            source, "Query release", first_url,
            "2026-07-27T10:00:00Z", "2026-07-28T12:00:00Z",
        )
        ordered_url = "https://www.federalreserve.gov/release?z=2&a=1"
        ordered = news_data.news_item(
            source, "Ordered query", ordered_url,
            "2026-07-27T10:00:00Z", "2026-07-27T12:00:00Z",
        )
        self.assertEqual(first["source_url"], first_url)
        self.assertEqual(second["source_url"], second_url)
        self.assertNotEqual(first["news_id"], second["news_id"])
        self.assertEqual(first["news_id"], repeated["news_id"])
        self.assertEqual(ordered["source_url"], ordered_url)

        invalid = (
            ("https://www.federalreserve.gov/release?id=%ZZ", "SOURCE_ITEM_LINK_QUERY_MALFORMED"),
            ("https://www.federalreserve.gov/release?id=%FF", "SOURCE_ITEM_LINK_QUERY_MALFORMED"),
            ("https://www.federalreserve.gov/release?id=one\\two", "SOURCE_ITEM_LINK_MALFORMED"),
            ("https://www.federalreserve.gov/release?id=one\x01two", "SOURCE_ITEM_LINK_MALFORMED"),
            (
                "https://www.federalreserve.gov/release?q="
                + "x" * news_data.MAX_QUERY_LENGTH,
                "SOURCE_ITEM_LINK_QUERY_TOO_LARGE",
            ),
            (
                "https://www.federalreserve.gov/release?"
                + "&".join(
                    "p{}=x".format(index)
                    for index in range(news_data.MAX_QUERY_PARAMETERS + 1)
                ),
                "SOURCE_ITEM_LINK_QUERY_TOO_MANY_PARAMETERS",
            ),
            ("https://www.federalreserve.gov/release?id=1#fragment", "SOURCE_ITEM_LINK_FRAGMENT_REJECTED"),
        )
        for url, reason in invalid:
            with self.subTest(reason=reason):
                fallback, status, actual_reason = news_data.governed_official_url(
                    url, source
                )
                self.assertEqual(fallback, source["exact_endpoint"])
                self.assertEqual(status, "SOURCE_ENDPOINT_FALLBACK")
                self.assertEqual(actual_reason, reason)

        document = cached_document(
            cached_wrapper(first, "news"), cached_wrapper(second, "news")
        )
        round_trip = news_cache.validate_document(document, FIXED_NOW, registry)
        self.assertEqual(
            [wrapper["record"]["source_url"] for wrapper in round_trip["records"]],
            [first_url, second_url],
        )
        javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        reference = javascript[
            javascript.index("function officialItemReference"):
            javascript.index("function operationalFreshnessLabel")
        ]
        self.assertIn("externalSourceLink(record.source_url, label)", reference)

    def test_percent_decoded_path_and_query_controls_fail_closed(self):
        registry, valid_news, _, _ = adversarial_cache_documents()
        source = registry["sources"][0]
        unsafe_escapes = (
            "%5C", "%5c", "%0A", "%0a", "%0D", "%00", "%7F",
            "%C2%85", "%E2%80%AE", "%FF",
        )
        for escaped in unsafe_escapes:
            for component, url, reason in (
                (
                    "path",
                    "https://www.federalreserve.gov/release" + escaped + "item",
                    "SOURCE_ITEM_LINK_MALFORMED",
                ),
                (
                    "query",
                    "https://www.federalreserve.gov/release?id=x" + escaped + "y",
                    "SOURCE_ITEM_LINK_QUERY_MALFORMED",
                ),
            ):
                with self.subTest(component=component, escaped=escaped):
                    fallback, status, actual_reason = news_data.governed_official_url(
                        url, source
                    )
                    self.assertEqual(fallback, source["exact_endpoint"])
                    self.assertEqual(status, "SOURCE_ENDPOINT_FALLBACK")
                    self.assertEqual(actual_reason, reason)

        valid_path = "https://www.federalreserve.gov/release/%E2%82%AC"
        valid_query = "https://www.federalreserve.gov/release?name=%D8%B3%D9%84%D8%A7%D9%85"
        for url in (valid_path, valid_query):
            with self.subTest(valid=url):
                canonical, status, reason = news_data.governed_official_url(
                    url, source
                )
                self.assertEqual(canonical, url)
                self.assertEqual(status, "GOVERNED_ITEM_LINK_AVAILABLE")
                self.assertEqual(reason, "SOURCE_ITEM_LINK_HOST_GOVERNED")

        malicious = copy.deepcopy(valid_news)
        encoded_control = "https://www.federalreserve.gov/release%0Ahidden"
        malicious.update({
            "source_url": encoded_control,
            "source_url_availability_status": "GOVERNED_ITEM_LINK_AVAILABLE",
            "source_url_reason_code": "SOURCE_ITEM_LINK_HOST_GOVERNED",
            "identity_basis": "GOVERNED_ITEM_URL",
            "identity_ambiguity_reason": None,
            "news_id": news_data.stable_identifier(
                "NEWS", (malicious["source_id"], encoded_control)
            ),
            "limitations": malicious["limitations"][:3],
        })
        document = cached_document(cached_wrapper(malicious, "news"))
        with self.assertRaisesRegex(news_cache.CacheError, "NEWS_CACHE_INVALID"):
            news_cache.validate_document(document, FIXED_NOW, registry)

    def test_registry_copy_and_source_inputs_are_not_mutated(self):
        registry = news_sources.load_source_registry()
        original = copy.deepcopy(registry)
        source = registry["sources"][0]
        OfficialNewsConnector(FakeTransport({source["exact_endpoint"]: response(source)})).retrieve(
            source, "2026-07-27T12:00:00Z"
        )
        self.assertEqual(registry, original)

    def test_disabled_means_zero_transport_calls_and_no_initialization(self):
        transport = FakeTransport()
        cache = news_cache.InMemoryCacheStorage(fail_load=True, fail_write=True)
        service = OfficialNewsService(transport=transport, cache_storage=cache)
        silent_default = OfficialNewsService()
        with mock.patch("trading_lab_app.news_sources.load_source_registry") as loader, mock.patch(
            "socket.getaddrinfo"
        ) as dns_lookup, mock.patch(
            "trading_lab_app.news_connector.multiprocessing.get_context"
        ) as process_context:
            self.assertEqual(service.health_document()["status"], "NEWS_DISABLED")
            self.assertEqual(service.sources_document()["sources"], [])
            self.assertEqual(service.news_items_document()["items"], [])
            self.assertEqual(service.economic_events_document()["events"], [])
            self.assertEqual(silent_default.health_document()["status"], "NEWS_DISABLED")
        loader.assert_not_called()
        dns_lookup.assert_not_called()
        process_context.assert_not_called()
        self.assertEqual(transport.calls, [])
        self.assertEqual(cache.write_count, 0)
        self.assertEqual(service.health_document()["network_request_count"], 0)

    def test_disabled_nonfinite_cache_recovery_does_not_load_or_network(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                cache = InvalidJsonCacheStorage(('{' + '"value":' + constant + '}').encode("ascii"))
                transport = FakeTransport()
                service = OfficialNewsService(transport=transport, cache_storage=cache)
                health = service.health_document()
                self.assertEqual(health["status"], "NEWS_DISABLED")
                self.assertEqual(health["network_request_count"], 0)
                self.assertEqual(cache.load_count, 0)
                self.assertEqual(cache.write_count, 0)
                self.assertEqual(transport.calls, [])

    def test_no_arbitrary_url_or_non_https_endpoint_is_accepted(self):
        source = news_sources.load_source_registry()["sources"][0]
        altered = copy.deepcopy(source)
        altered["exact_endpoint"] = "https://example.invalid/feed"
        with self.assertRaisesRegex(RetrievalError, "NEWS_PROVIDER_CHANGED"):
            OfficialNewsConnector(FakeTransport()).retrieve(altered, "2026-07-27T12:00:00Z")

    def test_complete_source_identity_binds_transport_to_endpoint(self):
        source = news_sources.load_source_registry()["sources"][0]
        hostname, path = news_sources.validated_endpoint_parts(source)
        self.assertEqual(hostname, "www.federalreserve.gov")
        self.assertEqual(path, "/feeds/press_monetary.xml")
        for field, value in (
            ("exact_hostname", "example.invalid"),
            ("exact_path", "/other.xml"),
            ("exact_endpoint", "https://user@www.federalreserve.gov/feeds/press_monetary.xml"),
            ("exact_endpoint", "https://www.federalreserve.gov:444/feeds/press_monetary.xml"),
            ("exact_endpoint", "https://www.federalreserve.gov/feeds/press_monetary.xml?x=1"),
            ("exact_endpoint", "https://www.federalreserve.gov/feeds/press_monetary.xml#x"),
        ):
            with self.subTest(field=field, value=value):
                altered = copy.deepcopy(source)
                altered[field] = value
                transport = mock.Mock()
                with mock.patch("socket.getaddrinfo") as dns_lookup, self.assertRaisesRegex(
                    RetrievalError, "NEWS_PROVIDER_CHANGED"
                ):
                    OfficialNewsConnector(transport).retrieve(
                        altered, "2026-07-27T12:00:00Z"
                    )
                transport.get.assert_not_called()
                dns_lookup.assert_not_called()
        transport = FakeTransport({source["exact_endpoint"]: response(source)})
        OfficialNewsConnector(transport).retrieve(dict(source), "2026-07-27T12:00:00Z")
        self.assertEqual(transport.calls, [source["exact_endpoint"]])
        direct = {"source_id": source["source_id"], "exact_endpoint": source["exact_endpoint"]}
        rejected_transport = mock.Mock()
        with self.assertRaisesRegex(RetrievalError, "NEWS_PROVIDER_CHANGED"):
            OfficialNewsConnector(rejected_transport).retrieve(
                direct, "2026-07-27T12:00:00Z"
            )
        rejected_transport.get.assert_not_called()
        altered["exact_endpoint"] = "http://www.federalreserve.gov/feeds/press_monetary.xml"
        with self.assertRaisesRegex(RetrievalError, "NEWS_PROVIDER_CHANGED"):
            OfficialNewsConnector(FakeTransport()).retrieve(altered, "2026-07-27T12:00:00Z")

    def test_redirect_timeout_and_http_errors_have_stable_codes(self):
        source = news_sources.load_source_registry()["sources"][0]
        cases = (
            (response(source, status=302), "NEWS_SOURCE_REDIRECT_BLOCKED"),
            (response(source, endpoint="https://www.federalreserve.gov/other"), "NEWS_SOURCE_REDIRECT_BLOCKED"),
            (RetrievalError("NEWS_SOURCE_TIMEOUT"), "NEWS_SOURCE_TIMEOUT"),
            (response(source, status=503), "NEWS_SOURCE_HTTP_ERROR"),
        )
        for value, code in cases:
            with self.subTest(code=code):
                connector = OfficialNewsConnector(FakeTransport({source["exact_endpoint"]: value}))
                with self.assertRaisesRegex(RetrievalError, code):
                    connector.retrieve(source, "2026-07-27T12:00:00Z")

    def test_content_type_encoding_and_response_size_are_bounded(self):
        source = news_sources.load_source_registry()["sources"][0]
        cases = (
            (response(source, content_type="text/html"), "NEWS_SOURCE_CONTENT_TYPE_INVALID"),
            (response(source, headers={"content-encoding": "gzip"}), "NEWS_SOURCE_CONTENT_TYPE_INVALID"),
            (response(source, body=b"x" * (news_parser.MAX_RESPONSE_BYTES + 1)), "NEWS_SOURCE_TOO_LARGE"),
        )
        for value, code in cases:
            with self.subTest(code=code):
                connector = OfficialNewsConnector(FakeTransport({source["exact_endpoint"]: value}))
                with self.assertRaisesRegex(RetrievalError, code):
                    connector.retrieve(source, "2026-07-27T12:00:00Z")

    def test_child_internal_connection_status_header_and_body_timeouts_are_stable(self):
        source = news_sources.load_source_registry()["sources"][0]

        class ControlledSocket:
            def settimeout(self, value):
                self.read_timeout = value

        class TimedResponse:
            status = 200

            def read(self, _size):
                raise socket.timeout("controlled body inactivity")

            def getheaders(self):
                return [("Content-Type", "application/rss+xml")]

            def close(self):
                return None

        class InactivityConnection:
            mode = "body"
            instances = []

            def __init__(self, _hostname, timeout):
                self.timeout = timeout
                self.sock = ControlledSocket()
                self.response = TimedResponse()
                self.__class__.instances.append(self)

            def request(self, _method, _path, headers):
                self.headers = dict(headers)
                if self.mode == "connection":
                    raise socket.timeout("controlled connection inactivity")

            def getresponse(self):
                if self.mode in {"status", "headers"}:
                    raise socket.timeout("controlled response inactivity")
                return self.response

            def close(self):
                return None

        for mode in ("connection", "status", "headers", "body"):
            with self.subTest(mode=mode), mock.patch(
                "trading_lab_app.news_connector.http.client.HTTPSConnection",
                InactivityConnection,
            ):
                InactivityConnection.mode = mode
                with self.assertRaisesRegex(
                    RetrievalError, "NEWS_SOURCE_TIMEOUT"
                ):
                    _direct_https_get(source)
                self.assertEqual(
                    InactivityConnection.instances[-1].timeout, 5,
                )
                if mode != "connection":
                    self.assertEqual(
                        InactivityConnection.instances[-1].sock.read_timeout,
                        READ_TIMEOUT_SECONDS,
                    )

    def test_spawn_child_deadline_crash_ipc_bounds_and_handle_cleanup(self):
        source = news_sources.load_source_registry()["sources"][0]
        self.assertEqual(
            source_child_main.__qualname__, "source_child_main",
        )
        self.assertEqual(
            source_child_main.__module__, "trading_lab_app.news_connector",
        )
        cases = (
            ("dns_before_socket", dns_blocked_source_child, "NEWS_SOURCE_TIMEOUT"),
            (
                "connection_before_socket",
                connection_without_socket_source_child,
                "NEWS_SOURCE_TIMEOUT",
            ),
            (
                "tls_status_header_trickle",
                tls_status_header_trickle_source_child,
                "NEWS_SOURCE_TIMEOUT",
            ),
            ("body_trickle", body_trickle_source_child, "NEWS_SOURCE_TIMEOUT"),
            ("child_crash", crashing_source_child, "NEWS_SOURCE_HTTP_ERROR"),
            ("malformed_ipc", malformed_source_child, "NEWS_SOURCE_HTTP_ERROR"),
            ("oversized_ipc", oversized_source_child, "NEWS_SOURCE_TOO_LARGE"),
        )
        for label, target, expected in cases:
            with self.subTest(phase=label), mock.patch(
                "trading_lab_app.news_connector.ABSOLUTE_REQUEST_DEADLINE_SECONDS",
                0.08,
            ):
                context = FakeProcessContext()
                transport = DirectHttpsTransport(
                    process_context=context,
                    child_target=target,
                    wait_function=fake_process_wait,
                )
                started = time.monotonic()
                with self.assertRaisesRegex(RetrievalError, expected):
                    transport.get(source)
                self.assertLess(time.monotonic() - started, 0.5)
                self.assertEqual(transport.active_child_count(), 0)
                self.assertEqual(transport.active_process_handle_count(), 0)
                self.assertEqual(transport.active_ipc_handle_count(), 0)
                self.assertEqual(context.active_count(), 0)
                self.assertEqual(context.open_process_handle_count(), 0)
                transport.close()

        serialization_context = FakeProcessContext(
            start_error=TypeError("controlled spawn serialization failure")
        )
        serialization_transport = DirectHttpsTransport(
            process_context=serialization_context,
            child_target=successful_source_child,
            wait_function=fake_process_wait,
        )
        with self.assertRaisesRegex(RetrievalError, "NEWS_SOURCE_HTTP_ERROR"):
            serialization_transport.get(source)
        self.assertEqual(serialization_context.active_count(), 0)
        self.assertEqual(serialization_context.open_process_handle_count(), 0)
        self.assertEqual(serialization_transport.active_process_handle_count(), 0)
        self.assertEqual(serialization_transport.active_ipc_handle_count(), 0)
        serialization_transport.close()

        context = FakeProcessContext()
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=successful_source_child,
            wait_function=fake_process_wait,
        )
        first = transport.get(source)
        second = transport.get(source)
        self.assertEqual(first, second)
        self.assertEqual(transport.active_child_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        self.assertEqual(context.start_count, 2)
        self.assertEqual(context.open_process_handle_count(), 0)
        transport.close()

        registry = news_sources.load_source_registry()
        context = FakeProcessContext()
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            wait_function=fake_process_wait,
        )
        outcomes = []

        def retrieve(selected_source):
            try:
                transport.get(selected_source)
            except RetrievalError as error:
                outcomes.append(error.reason_code)

        with mock.patch(
            "trading_lab_app.news_connector.ABSOLUTE_REQUEST_DEADLINE_SECONDS",
            0.08,
        ):
            workers = [
                threading.Thread(target=retrieve, args=(selected_source,))
                for selected_source in registry["sources"]
            ]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(1)
        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(outcomes, ["NEWS_SOURCE_TIMEOUT"] * NEWS_REFRESH_WORKERS)
        self.assertEqual(context.start_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(transport.active_child_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        transport.close()
        self.assertFalse(any(
            thread.name == "trl-news-source-deadline" and thread.is_alive()
            for thread in threading.enumerate()
        ))

    def test_starting_record_is_cancellable_without_global_registry_lock(self):
        source = news_sources.load_source_registry()["sources"][0]
        start_gate = threading.Event()
        context = FakeProcessContext(start_gate=start_gate)
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            wait_function=fake_process_wait,
        )
        global_lock_free = []

        def probe_registry_lock():
            acquired = transport._children_lock.acquire(blocking=False)
            global_lock_free.append(acquired)
            if acquired:
                transport._children_lock.release()

        context.start_hook = probe_registry_lock
        outcome = []

        def retrieve():
            try:
                transport.get(source)
            except RetrievalError as error:
                outcome.append(error.reason_code)

        worker = threading.Thread(target=retrieve, name="test-delayed-start")
        worker.start()
        self.assertTrue(context.start_entered.wait(2))
        with transport._children_lock:
            record = next(iter(transport._children))
        self.assertEqual(record.state, record.STARTING)
        shutdown = threading.Thread(target=transport.close, name="test-start-shutdown")
        shutdown.start()
        deadline = time.monotonic() + 2
        while not record.cancelled and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertTrue(record.cancelled)
        self.assertTrue(shutdown.is_alive())
        start_gate.set()
        worker.join(3)
        shutdown.join(3)
        self.assertFalse(worker.is_alive())
        self.assertFalse(shutdown.is_alive())
        self.assertEqual(global_lock_free, [True])
        self.assertEqual(outcome, ["NEWS_SOURCE_TIMEOUT"])
        self.assertTrue(record.started)
        self.assertEqual(record.state, record.FINALIZED)
        self.assertEqual(record.finalizer_count, 1)
        self.assertTrue(record.join_called)
        self.assertTrue(record.process_close_called)
        self.assertEqual(context.terminate_count, 1)
        self.assertEqual(context.join_count, 1)
        self.assertEqual(context.process_close_count, 1)
        self.assertTrue(record.start_complete.is_set())
        self.assertTrue(record.receive_close_called)
        self.assertTrue(record.send_close_called)
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(transport.child_record_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)

    def test_process_start_is_outside_post_spawn_retrieval_deadline(self):
        source = news_sources.load_source_registry()["sources"][0]
        start_gate = threading.Event()
        context = FakeProcessContext(start_gate=start_gate)
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=successful_source_child,
            wait_function=fake_process_wait,
        )
        release = threading.Timer(0.12, start_gate.set)
        release.start()
        started = time.monotonic()
        try:
            with mock.patch(
                "trading_lab_app.news_connector.ABSOLUTE_REQUEST_DEADLINE_SECONDS",
                0.05,
            ):
                result = transport.get(source)
        finally:
            release.join()
            transport.close()
        self.assertEqual(result.status, 200)
        self.assertGreaterEqual(time.monotonic() - started, 0.10)
        self.assertEqual(context.join_count, 1)
        self.assertEqual(context.process_close_count, 1)
        self.assertEqual(transport.child_record_count(), 0)
        documentation = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                BASE / "TRL_APP_QUICK_START.md",
                BASE / "TRL_NEWS_SOURCE_GOVERNANCE.md",
                BASE / "TRL_OFFICIAL_NEWS_SETUP_GUIDE.md",
                BASE / "TRL_R2_004_NEWS_EVENTS_CONTRACT.md",
            )
        )
        self.assertIn(
            "outside the post-spawn 20-second publisher-retrieval deadline",
            documentation,
        )
        self.assertIn(
            "cannot safely preempt a blocked",
            documentation,
        )

    def test_post_start_clock_failure_keeps_exact_child_owned_and_finalized(self):
        source = news_sources.load_source_registry()["sources"][0]
        context = FakeProcessContext()
        observations = []
        records = []
        transport_box = {}

        def failing_monotonic():
            transport = transport_box["transport"]
            with transport._children_lock:
                record = next(iter(transport._children))
            with record.lock:
                observations.append((
                    record.started,
                    record.state,
                    record.start_complete.is_set(),
                ))
            raise RuntimeError("controlled post-start clock failure")

        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            monotonic=failing_monotonic,
            wait_function=fake_process_wait,
        )
        transport_box["transport"] = transport
        original_discard = transport._discard_child

        def capture(record):
            records.append(record)
            original_discard(record)

        transport._discard_child = capture
        with self.assertRaisesRegex(
            RetrievalError, "NEWS_SOURCE_INTERNAL_ERROR"
        ) as raised:
            transport.get(source)
        self.assertEqual(
            raised.exception.reason_code, "NEWS_SOURCE_INTERNAL_ERROR"
        )
        self.assertNotIn(
            raised.exception.reason_code,
            {
                "NEWS_SOURCE_HTTP_ERROR",
                "NEWS_SOURCE_TIMEOUT",
                "NEWS_PROVIDER_CHANGED",
            },
        )
        transport.close()
        transport.close()

        self.assertEqual(observations, [(True, "RUNNING", True)])
        self.assertEqual(context.start_count, 1)
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.join_count, 1)
        self.assertEqual(context.process_close_count, 1)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(transport.child_record_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.finalizer_count, 1)
        self.assertEqual(record.state, record.FINALIZED)
        self.assertTrue(record.join_called)
        self.assertTrue(record.process_close_called)
        self.assertTrue(record.receive_close_called)
        self.assertTrue(record.send_close_called)

    def test_internal_clock_failure_is_sanitized_in_health_and_capabilities(self):
        context = FakeProcessContext()

        def failing_monotonic():
            raise RuntimeError("controlled secret path C:\\private\\clock")

        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            monotonic=failing_monotonic,
            wait_function=fake_process_wait,
        )
        service = OfficialNewsService(
            OfficialNewsConfiguration(True, 900),
            transport=transport,
            clock=FakeClock(),
            cache_storage=news_cache.InMemoryCacheStorage(),
        )
        service.health_document()
        self.assertTrue(service.wait_for_refresh(5))
        health = service.health_document()
        self.assertEqual(health["schema_version"], "TRL-OFFICIAL-NEWS-HEALTH-1.2")
        self.assertEqual(health["status"], "NEWS_ALL_SOURCES_FAILED")
        self.assertTrue(all(
            item["reason_code"] == "NEWS_SOURCE_INTERNAL_ERROR"
            for item in health["source_health"]
        ))
        self.assertIn(
            "NEWS_SOURCE_INTERNAL_ERROR", health["stable_health_codes"]
        )
        serialized = json.dumps(health, sort_keys=True)
        self.assertNotIn("controlled secret", serialized)
        self.assertNotIn("private", serialized)
        self.assertNotIn("RuntimeError", serialized)
        self.assertEqual(
            capabilities.capability_manifest()[
                "official_news_stable_health_reason_codes"
            ],
            list(STABLE_HEALTH_CODES),
        )
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.join_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.process_close_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        self.assertEqual(transport.child_record_count(), 0)
        self.assertTrue(service.shutdown())

    def test_shutdown_races_with_six_post_start_clock_failures(self):
        class GateFailingMonotonic:
            def __init__(self, expected):
                self.expected = expected
                self.count = 0
                self.lock = threading.Lock()
                self.all_entered = threading.Event()
                self.release = threading.Event()

            def __call__(self):
                with self.lock:
                    self.count += 1
                    if self.count == self.expected:
                        self.all_entered.set()
                if not self.release.wait(5):
                    raise RuntimeError("controlled clock release timeout")
                raise RuntimeError("controlled post-start clock failure")

        context = FakeProcessContext()
        clock = GateFailingMonotonic(NEWS_REFRESH_WORKERS)
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            monotonic=clock,
            wait_function=fake_process_wait,
        )
        records = []
        records_lock = threading.Lock()
        original_discard = transport._discard_child

        def capture(record):
            with records_lock:
                records.append(record)
            original_discard(record)

        transport._discard_child = capture
        service = OfficialNewsService(
            OfficialNewsConfiguration(True, 900),
            transport=transport,
            clock=FakeClock(),
            cache_storage=news_cache.InMemoryCacheStorage(),
        )
        first = service.health_document()
        self.assertEqual(first["status"], "NEWS_REFRESHING")
        self.assertTrue(clock.all_entered.wait(3))
        self.assertEqual(context.start_count, NEWS_REFRESH_WORKERS)

        shutdown_results = []
        shutdown = threading.Thread(
            target=lambda: shutdown_results.append(service.shutdown()),
            name="test-post-start-clock-shutdown",
        )
        shutdown.start()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with transport._children_lock:
                if transport._children and all(
                    record.cancelled for record in transport._children
                ):
                    break
            time.sleep(0.005)
        with transport._children_lock:
            self.assertEqual(len(transport._children), NEWS_REFRESH_WORKERS)
            self.assertTrue(all(
                record.cancelled for record in transport._children
            ))
        self.assertTrue(shutdown.is_alive())
        clock.release.set()
        shutdown.join(5)

        self.assertFalse(shutdown.is_alive())
        self.assertEqual(shutdown_results, [True])
        self.assertTrue(service.shutdown())
        self.assertTrue(service.shutdown())
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.join_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.process_close_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(transport.child_record_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        self.assertEqual(len(records), NEWS_REFRESH_WORKERS)
        self.assertTrue(all(
            record.finalizer_count == 1
            and record.state == record.FINALIZED
            and record.join_called
            and record.process_close_called
            and record.receive_close_called
            and record.send_close_called
            for record in records
        ))
        self.assertFalse(service._refreshing)
        self.assertIsNone(service._refresh_owner)
        self.assertIsNone(service._refresh_thread)
        self.assertFalse(any(
            thread.is_alive() and (
                thread.name.startswith("trl-news-refresh")
                or thread.name.startswith("trl-news-coordinator")
                or thread.name.startswith("fake-trl-news-source")
            )
            for thread in threading.enumerate()
        ))

    def test_normal_success_establishes_ownership_before_deadline_clock(self):
        source = news_sources.load_source_registry()["sources"][0]
        context = FakeProcessContext()
        observations = []
        records = []
        transport_box = {}

        def observed_monotonic():
            transport = transport_box["transport"]
            with transport._children_lock:
                record = next(iter(transport._children))
            with record.lock:
                observations.append((
                    record.started,
                    record.state,
                    record.start_complete.is_set(),
                ))
            return time.monotonic()

        transport = DirectHttpsTransport(
            process_context=context,
            child_target=successful_source_child,
            monotonic=observed_monotonic,
            wait_function=fake_process_wait,
        )
        transport_box["transport"] = transport
        original_discard = transport._discard_child

        def capture(record):
            records.append(record)
            original_discard(record)

        transport._discard_child = capture
        result = transport.get(source)
        callback_count = len(observations)
        transport.close()
        transport.close()

        self.assertEqual(result.status, 200)
        self.assertGreaterEqual(callback_count, 2)
        self.assertTrue(all(
            observation == (True, "RUNNING", True)
            for observation in observations
        ))
        self.assertEqual(len(observations), callback_count)
        self.assertEqual(context.start_count, 1)
        self.assertEqual(context.join_count, 1)
        self.assertEqual(context.process_close_count, 1)
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(transport.child_record_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].finalizer_count, 1)
        self.assertEqual(records[0].state, records[0].FINALIZED)

    def test_exactly_once_finalizer_for_success_start_failure_and_races(self):
        source = news_sources.load_source_registry()["sources"][0]

        success_context = FakeProcessContext()
        success_transport = DirectHttpsTransport(
            process_context=success_context,
            child_target=successful_source_child,
            wait_function=fake_process_wait,
        )
        finalized = []
        original_discard = success_transport._discard_child

        def capture_success(record):
            finalized.append(record)
            original_discard(record)

        success_transport._discard_child = capture_success
        self.assertEqual(success_transport.get(source).status, 200)
        success_transport.close()
        self.assertEqual(success_context.join_count, 1)
        self.assertEqual(success_context.process_close_count, 1)
        self.assertEqual(finalized[0].finalizer_count, 1)

        failed_context = FakeProcessContext(
            start_error=TypeError("controlled serialization failure"),
        )
        failed_transport = DirectHttpsTransport(
            process_context=failed_context,
            child_target=successful_source_child,
            wait_function=fake_process_wait,
        )
        with self.assertRaisesRegex(RetrievalError, "NEWS_SOURCE_HTTP_ERROR"):
            failed_transport.get(source)
        failed_transport.close()
        self.assertEqual(failed_context.join_count, 0)
        self.assertEqual(failed_context.process_close_count, 1)
        self.assertEqual(failed_transport.child_record_count(), 0)

        for label, target, delay in (
            ("normal_shutdown", successful_source_child, 0.0),
            ("timeout_shutdown", blocked_source_child, 0.06),
            ("crash_shutdown", crashing_source_child, 0.0),
        ):
            with self.subTest(label=label):
                exit_gate = (
                    threading.Event()
                    if target is not blocked_source_child else None
                )
                context = FakeProcessContext(exit_gate=exit_gate)
                transport = DirectHttpsTransport(
                    process_context=context,
                    child_target=target,
                    wait_function=fake_process_wait,
                )
                records = []
                discard = transport._discard_child

                def capture(record, discard=discard):
                    records.append(record)
                    discard(record)

                transport._discard_child = capture
                errors = []

                def retrieve_for_race():
                    try:
                        with mock.patch(
                            "trading_lab_app.news_connector.ABSOLUTE_REQUEST_DEADLINE_SECONDS",
                            0.10,
                        ):
                            transport.get(source)
                    except RetrievalError as error:
                        errors.append(error.reason_code)

                worker = threading.Thread(
                    target=retrieve_for_race,
                    name="test-{}-worker".format(label),
                )
                worker.start()
                self.assertTrue(context.start_entered.wait(2))
                if delay:
                    time.sleep(delay)
                shutdown = threading.Thread(
                    target=transport.close,
                    name="test-{}-shutdown".format(label),
                )
                shutdown.start()
                if exit_gate is not None:
                    exit_gate.set()
                worker.join(3)
                shutdown.join(3)
                self.assertFalse(worker.is_alive())
                self.assertFalse(shutdown.is_alive())
                self.assertEqual(context.join_count, 1)
                self.assertEqual(context.process_close_count, 1)
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0].finalizer_count, 1)
                self.assertEqual(records[0].state, records[0].FINALIZED)
                self.assertEqual(transport.child_record_count(), 0)


class ParserSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = news_sources.load_source_registry()
        cls.rss_source = registry["sources"][0]
        cls.bea_source = next(item for item in registry["sources"] if item["source_id"] == "BEA_RELEASE_DATES_JSON")
        cls.bea_rss_source = next(
            item for item in registry["sources"]
            if item["source_id"] == "BEA_NEWS_RELEASE_RSS"
        )
        cls.bls_source = next(
            item for item in registry["sources"]
            if item["source_id"] == "BLS_LATEST_RELEASES_RSS"
        )
        cls.atom_source = next(
            item for item in registry["sources"]
            if item["source_id"] == "ECB_PRESS_RELEASE_RSS"
        )

    def parse_xml(self, body):
        return news_parser.parse_xml_news(body, self.rss_source, "2026-07-27T12:00:00Z")

    def parse_atom(self, children, title="Atom governed item"):
        body = (
            '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>'
            + title + "</title>" + children + "</entry></feed>"
        ).encode("utf-8")
        return news_parser.parse_xml_news(
            body, self.atom_source, "2026-07-27T12:00:00Z"
        )[0]

    def test_invalid_utf8_dtd_entity_and_malformed_xml_are_rejected(self):
        cases = (
            (b"\xff", "NEWS_SOURCE_UTF8_INVALID"),
            (b'<!DOCTYPE rss SYSTEM "file:///x"><rss/>', "NEWS_SOURCE_XML_UNSAFE"),
            (b'<!ENTITY x "bad"><rss/>', "NEWS_SOURCE_XML_UNSAFE"),
            (b"<rss><item></rss>", "NEWS_SOURCE_PARSE_ERROR"),
        )
        for body, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(news_data.NewsValidationError, code):
                self.parse_xml(body)

    def test_oversized_deep_and_too_many_xml_entries_are_rejected(self):
        deep = ("<x>" * 25 + "</x>" * 25).encode("utf-8")
        many = ("<rss><channel>" + "<item><title>x</title></item>" * 201 + "</channel></rss>").encode("utf-8")
        for body, code in (
            (b"x" * (news_parser.MAX_RESPONSE_BYTES + 1), "NEWS_SOURCE_TOO_LARGE"),
            (deep, "NEWS_SOURCE_SCHEMA_INVALID"),
            (many, "NEWS_SOURCE_SCHEMA_INVALID"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(news_data.NewsValidationError, code):
                self.parse_xml(body)

    def test_rss_atom_missing_optional_fields_and_strict_timestamps(self):
        rss = self.parse_xml(RSS_BODY)[0]
        self.assertEqual(rss["title"], "Official & governed release")
        atom_source = next(
            item for item in news_sources.load_source_registry()["sources"]
            if item["source_id"] == "ECB_PRESS_RELEASE_RSS"
        )
        atom = news_parser.parse_xml_news(ATOM_BODY, atom_source, "2026-07-27T12:00:00Z")[0]
        self.assertEqual(atom["title"], "Atom official update")
        missing = self.parse_xml(b"<rss><channel><item><title>Undated</title></item></channel></rss>")[0]
        self.assertIsNone(missing["published_timestamp_utc"])
        with self.assertRaisesRegex(news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"):
            self.parse_xml(b"<rss><channel><item><title>x</title><pubDate>not-a-date</pubDate></item></channel></rss>")

    def test_bls_long_description_is_bounded_discarded_metadata(self):
        description_marker = "SYNTHETIC-NONRETAINED-DESCRIPTION-"
        description = description_marker + "x" * (4589 - len(description_marker))
        body = (
            '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<channel><item><title>Major indicators synthetic metadata</title>"
            "<link>https://www.bls.gov/bls/</link>"
            "<pubDate>Wed, 29 Jul 2026 10:01:38 -0400</pubDate>"
            "<dc:creator>U.S. Bureau of Labor Statistics</dc:creator>"
            "<description>" + description + "</description>"
            "</item></channel></rss>"
        ).encode("utf-8")
        records = news_parser.parse_xml_news(
            body, self.bls_source, "2026-07-30T08:00:00Z"
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source_id"], "BLS_LATEST_RELEASES_RSS")
        self.assertEqual(records[0]["source_url"], "https://www.bls.gov/bls/")
        self.assertEqual(
            records[0]["published_timestamp_utc"], "2026-07-29T14:01:38Z"
        )
        self.assertNotIn(description_marker, json.dumps(records))
        oversized = body.replace(
            description.encode("utf-8"),
            b"x" * (news_parser.MAX_NONRETAINED_DESCRIPTION_LENGTH + 1),
        )
        with self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
        ):
            news_parser.parse_xml_news(
                oversized, self.bls_source, "2026-07-30T08:00:00Z"
            )

    def test_bea_rss_named_eastern_dates_and_direct_metadata_fields(self):
        rows = []
        for index in range(46):
            rows.append(
                "<item><dbid>{0}</dbid><title>Synthetic BEA release {0}</title>"
                "<link>https://www.bea.gov/news/synthetic-{0}</link>"
                "<guid>synthetic-{0}</guid><description>Not retained {0}</description>"
                "<data>Not retained</data><nextreleasedate>Not retained</nextreleasedate>"
                "<unitsofmeasure>Not retained</unitsofmeasure>"
                "<changeunit>Not retained</changeunit>"
                "<linkhistoric>Not retained</linkhistoric>"
                "<linkarchive>Not retained</linkarchive><pdf>Not retained</pdf>"
                "<pubDate>Wed, 29 Jul 2026 10:01:38 EDT</pubDate></item>".format(index)
            )
        body = ("<rss><channel>" + "".join(rows) + "</channel></rss>").encode(
            "utf-8"
        )
        records = news_parser.parse_xml_news(
            body, self.bea_rss_source, "2026-07-30T08:00:00Z"
        )
        self.assertEqual(len(records), 46)
        self.assertEqual(records[0]["published_timestamp_utc"], "2026-07-29T14:01:38Z")
        self.assertEqual(
            news_data.parse_source_timestamp(
                "Wed, 29 Jul 2026 10:01:38 EST"
            ),
            "2026-07-29T15:01:38Z",
        )
        encoded = json.dumps(records)
        for discarded in (
            "Not retained", "nextreleasedate", "unitsofmeasure", "linkarchive"
        ):
            self.assertNotIn(discarded, encoded)
        with self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
        ):
            news_data.parse_source_timestamp(
                "Wed, 29 Jul 2026 10:01:38 PDT"
            )

    def test_atom_publication_time_precedes_update_independent_of_child_order(self):
        published = "2026-07-27T09:00:00Z"
        updated = "2026-07-27T10:00:00Z"
        updated_first = (
            "<updated>" + updated + "</updated>"
            "<published>" + published + "</published>"
        )
        published_first = (
            "<published>" + published + "</published>"
            "<updated>" + updated + "</updated>"
        )
        first = self.parse_atom(updated_first)
        second = self.parse_atom(published_first)
        self.assertEqual(first["published_timestamp_utc"], published)
        self.assertEqual(second["published_timestamp_utc"], published)
        self.assertEqual(
            self.parse_atom("<published>" + published + "</published>")[
                "published_timestamp_utc"
            ],
            published,
        )
        self.assertEqual(
            self.parse_atom("<updated>" + updated + "</updated>")[
                "published_timestamp_utc"
            ],
            updated,
        )
        self.assertIsNone(self.parse_atom("")["published_timestamp_utc"])

        with self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
        ):
            self.parse_atom(
                "<updated>" + updated + "</updated>"
                "<published>not-a-time</published>"
            )

        changed_update = self.parse_atom(
            "<published>" + published + "</published>"
            "<updated>2026-07-27T11:00:00Z</updated>"
        )
        self.assertEqual(first["news_id"], changed_update["news_id"])
        self.assertEqual(
            first["published_timestamp_utc"],
            changed_update["published_timestamp_utc"],
        )

        rss = self.parse_xml(
            b"<rss><channel><item><title>RSS</title>"
            b"<date>2026-07-26T08:00:00Z</date>"
            b"<pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate>"
            b"</item></channel></rss>"
        )[0]
        self.assertEqual(rss["published_timestamp_utc"], "2026-07-27T10:00:00Z")

        source_before = copy.deepcopy(self.atom_source)
        body = (
            '<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
            '<title>Deterministic</title><published>' + published
            + "</published></entry></feed>"
        ).encode("utf-8")
        body_before = bytes(body)
        parsed_once = news_parser.parse_xml_news(
            body, self.atom_source, "2026-07-27T12:00:00Z"
        )
        parsed_twice = news_parser.parse_xml_news(
            body, self.atom_source, "2026-07-27T12:00:00Z"
        )
        self.assertEqual(parsed_once, parsed_twice)
        self.assertEqual(body, body_before)
        self.assertEqual(self.atom_source, source_before)

    def test_atom_selects_only_deterministically_ranked_alternate_links(self):
        alternate = "https://www.ecb.europa.eu/press/alternate.html"
        self_link = "https://www.ecb.europa.eu/rss/press.html"
        enclosure = "https://www.ecb.europa.eu/press/file.pdf"
        published = "<published>2026-07-27T09:00:00Z</published>"
        arrangements = (
            '<link rel="self" href="' + self_link + '"/>'
            '<link rel="alternate" href="' + alternate + '"/>',
            '<link rel="enclosure" href="' + enclosure + '"/>'
            '<link rel="alternate" href="' + alternate + '"/>',
            '<link rel="alternate" href="' + alternate + '"/>'
            '<link rel="self" href="' + self_link + '"/>',
            '<link href="' + alternate + '"/>',
        )
        selected = []
        for links in arrangements:
            item = self.parse_atom(links + published)
            selected.append(item)
            self.assertEqual(item["source_url"], alternate)
            self.assertEqual(
                item["source_url_availability_status"],
                "GOVERNED_ITEM_LINK_AVAILABLE",
            )
        self.assertEqual(len({item["news_id"] for item in selected}), 1)

        preferred_html = self.parse_atom(
            '<link rel="alternate" type="application/pdf" '
            'href="https://www.ecb.europa.eu/press/document.pdf"/>'
            '<link rel="alternate" type="text/html; charset=UTF-8" href="' + alternate
            + '"/>' + published
        )
        self.assertEqual(preferred_html["source_url"], alternate)

        no_alternate = self.parse_atom(
            '<link rel="self" href="' + self_link + '"/>'
            '<link rel="enclosure" href="' + enclosure + '"/>' + published
        )
        self.assertEqual(
            no_alternate["source_url_availability_status"],
            "SOURCE_ENDPOINT_FALLBACK",
        )
        self.assertEqual(
            no_alternate["source_url_reason_code"],
            "SOURCE_ITEM_LINK_NOT_PROVIDED",
        )

        ungoverned = self.parse_atom(
            '<link rel="alternate" href="https://example.invalid/item"/>'
            + published
        )
        self.assertEqual(
            ungoverned["source_url_availability_status"],
            "SOURCE_ENDPOINT_FALLBACK",
        )
        self.assertEqual(
            ungoverned["source_url_reason_code"],
            "SOURCE_ITEM_LINK_HOST_NOT_GOVERNED",
        )

        expected = news_data.news_item(
            self.atom_source, "Atom governed item", alternate,
            "2026-07-27T09:00:00Z", "2026-07-27T12:00:00Z",
        )
        self.assertEqual(selected[0]["news_id"], expected["news_id"])
        javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        self.assertIn(
            "externalSourceLink(record.source_url, label)", javascript
        )

    def test_malformed_duplicate_deep_and_nonfinite_json_are_rejected(self):
        deep = b'{"release_dates":' + b"[" * 17 + b"]" * 17 + b"}"
        cases = (
            (b"{", "NEWS_SOURCE_PARSE_ERROR"),
            (b'{"release_dates":[],"release_dates":[]}', "NEWS_SOURCE_SCHEMA_INVALID"),
            (deep, "NEWS_SOURCE_SCHEMA_INVALID"),
            (b'{"release_dates":[{"ReleaseDate":"2026-07-30","ReleaseName":"x","actual":NaN}]}', "NEWS_SOURCE_SCHEMA_INVALID"),
            (b'{"release_dates":[{"ReleaseDate":"2026-07-30","ReleaseName":"x","actual":true}]}', "NEWS_SOURCE_SCHEMA_INVALID"),
            (b"\xff", "NEWS_SOURCE_UTF8_INVALID"),
        )
        for body, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(news_data.NewsValidationError, code):
                news_parser.parse_bea_release_dates(body, self.bea_source, "2026-07-27T12:00:00Z")

    def test_json_decoder_recursion_is_a_governed_parse_error(self):
        depth = 2000
        body = (
            b'{"release_dates":' + b"[" * depth + b"0"
            + b"]" * depth + b"}"
        )
        self.assertLess(len(body), news_parser.MAX_RESPONSE_BYTES)
        with self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
        ):
            news_parser.parse_bea_release_dates(
                body, self.bea_source, "2026-07-27T12:00:00Z"
            )
        with mock.patch(
            "trading_lab_app.news_parser.json.loads",
            side_effect=RecursionError("must not escape"),
        ), self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_PARSE_ERROR"
        ):
            news_parser.parse_bea_release_dates(
                b'{"release_dates":[]}',
                self.bea_source,
                "2026-07-27T12:00:00Z",
            )

    def test_bea_schedule_preserves_nulls_and_date_precision(self):
        event = news_parser.parse_bea_release_dates(
            BEA_BODY, self.bea_source, "2026-07-27T12:00:00Z"
        )[0]
        self.assertEqual(event["scheduled_timestamp_utc"], "2026-07-30T00:00:00Z")
        self.assertEqual(event["scheduled_time_precision"], "DATE_ONLY")
        for field in ("actual", "forecast", "previous", "importance"):
            self.assertIsNone(event[field])
            self.assertEqual(event["missing_value_reasons"][field], "SOURCE_NOT_PROVIDED")

    def test_bea_product_release_mapping_expands_strict_rfc3339_occurrences(self):
        body = json.dumps({
            "Gross Domestic Product": {
                "release_dates": [
                    "2026-07-30T08:30:00-04:00",
                    "2026-08-27T08:30:00-04:00",
                ],
            },
            "Personal Income and Outlays": {
                "release_dates": ["2026-07-31T08:30:00-04:00"],
            },
            "file_last_updated": "2026-07-29T16:45:00Z",
        }, separators=(",", ":")).encode("utf-8")
        events = news_parser.parse_bea_release_dates(
            body, self.bea_source, "2026-07-30T08:00:00Z"
        )
        self.assertEqual(
            [event["event_name"] for event in events],
            [
                "Gross Domestic Product",
                "Personal Income and Outlays",
                "Gross Domestic Product",
            ],
        )
        self.assertEqual(
            [event["scheduled_timestamp_utc"] for event in events],
            [
                "2026-07-30T12:30:00Z",
                "2026-07-31T12:30:00Z",
                "2026-08-27T12:30:00Z",
            ],
        )
        for event in events:
            self.assertEqual(event["scheduled_time_precision"], "TIMESTAMP")
            self.assertEqual(event["data_quality_status"], "SOURCE_TIMESTAMP_VALID")
            self.assertEqual(
                event["source_url_availability_status"],
                "SOURCE_ENDPOINT_FALLBACK",
            )
        self.assertNotIn("file_last_updated", json.dumps(events))

    def test_bea_product_mapping_deduplicates_equivalent_dates_per_product(self):
        equivalent_dates = [
            "2026-08-01T12:00:00Z",
            "2026-08-01T16:00:00+04:00",
            "2026-08-01T12:00:00Z",
        ]

        def parse(dates, retrieved="2026-07-30T08:00:00Z"):
            return news_parser.parse_bea_release_dates(
                json.dumps({
                    "Gross Domestic Product": {"release_dates": dates},
                    "file_last_updated": "2026-07-29T16:45:00Z",
                }, separators=(",", ":")).encode("utf-8"),
                self.bea_source,
                retrieved,
            )

        first = parse(equivalent_dates)
        reordered = parse(
            list(reversed(equivalent_dates)), "2026-07-30T09:00:00Z"
        )
        self.assertEqual(len(first), 1)
        self.assertEqual(len(reordered), 1)
        self.assertEqual(first[0]["scheduled_timestamp_utc"], "2026-08-01T12:00:00Z")
        self.assertEqual(first[0]["event_series_id"], reordered[0]["event_series_id"])
        self.assertEqual(first[0]["event_id"], reordered[0]["event_id"])
        self.assertEqual(
            news_data.observation_fingerprint(first[0]),
            news_data.observation_fingerprint(reordered[0]),
        )
        self.assertEqual(first[0]["revision_number"], reordered[0]["revision_number"])

        different_products = news_parser.parse_bea_release_dates(
            json.dumps({
                "Gross Domestic Product": {
                    "release_dates": [equivalent_dates[0]],
                },
                "Personal Income and Outlays": {
                    "release_dates": [equivalent_dates[1]],
                },
                "file_last_updated": "2026-07-29T16:45:00Z",
            }, separators=(",", ":")).encode("utf-8"),
            self.bea_source,
            "2026-07-30T08:00:00Z",
        )
        self.assertEqual(len(different_products), 2)
        self.assertEqual(len({event["event_id"] for event in different_products}), 2)
        self.assertEqual(
            len({event["event_series_id"] for event in different_products}), 2
        )

        different_dates = parse([
            "2026-08-02T12:00:00Z",
            "2026-08-01T12:00:00Z",
        ])
        self.assertEqual(
            [event["scheduled_timestamp_utc"] for event in different_dates],
            ["2026-08-01T12:00:00Z", "2026-08-02T12:00:00Z"],
        )
        self.assertEqual(len({event["event_id"] for event in different_dates}), 2)
        self.assertEqual(
            len({event["event_series_id"] for event in different_dates}), 1
        )

    def test_bea_product_mapping_has_canonical_global_output_order(self):
        retrieved = "2026-07-30T08:00:00Z"
        metadata = "2026-07-29T16:45:00Z"
        first_document = {
            "Alpha Product": {"release_dates": [
                "2026-08-03T12:00:00Z",
                "2026-08-01T12:00:00Z",
                "2026-08-01T16:00:00+04:00",
            ]},
            "Beta Product": {"release_dates": [
                "2026-08-02T12:00:00Z",
                "2026-08-01T12:00:00Z",
            ]},
            "file_last_updated": metadata,
        }
        reversed_document = {
            "Beta Product": {
                "release_dates": list(reversed(
                    first_document["Beta Product"]["release_dates"]
                )),
            },
            "Alpha Product": {
                "release_dates": list(reversed(
                    first_document["Alpha Product"]["release_dates"]
                )),
            },
            "file_last_updated": metadata,
        }
        original_first = copy.deepcopy(first_document)
        original_reversed = copy.deepcopy(reversed_document)

        def parse(document):
            return news_parser.parse_bea_release_dates(
                json.dumps(
                    document, separators=(",", ":"),
                ).encode("utf-8"),
                self.bea_source,
                retrieved,
            )

        first = parse(first_document)
        reversed_result = parse(reversed_document)
        repeated = parse(copy.deepcopy(first_document))
        decoded_result = news_parser._product_release_events(
            first_document, self.bea_source, retrieved,
        )

        self.assertEqual(first, reversed_result)
        self.assertEqual(
            news_cache.deterministic_bytes(first),
            news_cache.deterministic_bytes(reversed_result),
        )
        self.assertEqual(first, repeated)
        self.assertEqual(first, decoded_result)
        self.assertEqual(first_document, original_first)
        self.assertEqual(reversed_document, original_reversed)
        self.assertEqual(len(first), 4)
        self.assertEqual(
            [
                (
                    news_data.chronological_timestamp_key(
                        event["scheduled_timestamp_utc"]
                    ),
                    event["event_series_id"],
                    event["event_id"],
                )
                for event in first
            ],
            sorted(
                (
                    news_data.chronological_timestamp_key(
                        event["scheduled_timestamp_utc"]
                    ),
                    event["event_series_id"],
                    event["event_id"],
                )
                for event in first
            ),
        )
        self.assertLess(
            next(index for index, event in enumerate(first) if (
                event["event_name"] == "Beta Product"
                and event["scheduled_timestamp_utc"] == "2026-08-02T12:00:00Z"
            )),
            next(index for index, event in enumerate(first) if (
                event["event_name"] == "Alpha Product"
                and event["scheduled_timestamp_utc"] == "2026-08-03T12:00:00Z"
            )),
        )
        same_time = [
            event for event in first
            if event["scheduled_timestamp_utc"] == "2026-08-01T12:00:00Z"
        ]
        self.assertEqual(
            [(event["event_series_id"], event["event_id"]) for event in same_time],
            sorted(
                (event["event_series_id"], event["event_id"])
                for event in same_time
            ),
        )
        self.assertEqual(
            len([
                event for event in first
                if event["event_name"] == "Alpha Product"
                and event["scheduled_timestamp_utc"] == "2026-08-01T12:00:00Z"
            ]),
            1,
        )

        expected = sorted([
            news_data.economic_event(
                self.bea_source, "Alpha Product", "2026-08-01T12:00:00Z",
                None, retrieved, None,
            ),
            news_data.economic_event(
                self.bea_source, "Alpha Product", "2026-08-03T12:00:00Z",
                None, retrieved, None,
            ),
            news_data.economic_event(
                self.bea_source, "Beta Product", "2026-08-01T12:00:00Z",
                None, retrieved, None,
            ),
            news_data.economic_event(
                self.bea_source, "Beta Product", "2026-08-02T12:00:00Z",
                None, retrieved, None,
            ),
        ], key=lambda event: (
            news_data.chronological_timestamp_key(
                event["scheduled_timestamp_utc"]
            ),
            event["event_series_id"],
            event["event_id"],
        ))
        self.assertEqual(first, expected)
        self.assertEqual(
            [(event["event_id"], event["event_series_id"],
              news_data.observation_fingerprint(event), event["revision_number"])
             for event in first],
            [(event["event_id"], event["event_series_id"],
              news_data.observation_fingerprint(event), event["revision_number"])
             for event in expected],
        )

    def test_bea_fractional_instants_have_true_chronological_global_order(self):
        retrieved = "2026-07-30T08:00:00Z"
        document = {
            "Alpha Product": {"release_dates": [
                "2026-08-01T12:00:00.1Z",
                "2026-08-01T16:00:00.100000+04:00",
                "2026-08-01T12:00:00Z",
                "2026-08-01T16:00:00+04:00",
                "2026-08-01T12:00:00.001Z",
                "2026-08-01T07:00:00.001-05:00",
                "2026-08-01T12:00:00.01Z",
                "2026-08-01T16:00:00.010+04:00",
                "2026-08-01T11:59:59.999999Z",
                "2026-08-01T12:00:01Z",
                "2026-08-01T12:00:01.000001Z",
            ]},
            "Beta Product": {"release_dates": [
                "2026-08-01T12:00:00.000001Z",
                "2026-08-01T12:00:00Z",
            ]},
            "file_last_updated": "2026-07-29T16:45:00Z",
        }
        reversed_document = {
            "Beta Product": {"release_dates": list(reversed(
                document["Beta Product"]["release_dates"]
            ))},
            "Alpha Product": {"release_dates": list(reversed(
                document["Alpha Product"]["release_dates"]
            ))},
            "file_last_updated": document["file_last_updated"],
        }
        original = copy.deepcopy(document)
        original_reversed = copy.deepcopy(reversed_document)

        def parse(value):
            return news_parser.parse_bea_release_dates(
                json.dumps(value, separators=(",", ":")).encode("utf-8"),
                self.bea_source,
                retrieved,
            )

        first = parse(document)
        reversed_result = parse(reversed_document)
        repeated = parse(copy.deepcopy(document))
        expected_timestamps = [
            "2026-08-01T11:59:59.999999Z",
            "2026-08-01T12:00:00Z",
            "2026-08-01T12:00:00Z",
            "2026-08-01T12:00:00.000001Z",
            "2026-08-01T12:00:00.001Z",
            "2026-08-01T12:00:00.01Z",
            "2026-08-01T12:00:00.1Z",
            "2026-08-01T12:00:01Z",
            "2026-08-01T12:00:01.000001Z",
        ]

        self.assertEqual(
            [event["scheduled_timestamp_utc"] for event in first],
            expected_timestamps,
        )
        self.assertEqual(first, reversed_result)
        self.assertEqual(first, repeated)
        self.assertEqual(
            news_cache.deterministic_bytes(first),
            news_cache.deterministic_bytes(reversed_result),
        )
        self.assertEqual(document, original)
        self.assertEqual(reversed_document, original_reversed)
        same_time = [
            event for event in first
            if event["scheduled_timestamp_utc"] == "2026-08-01T12:00:00Z"
        ]
        self.assertEqual(
            [(event["event_series_id"], event["event_id"]) for event in same_time],
            sorted(
                (event["event_series_id"], event["event_id"])
                for event in same_time
            ),
        )
        self.assertTrue(all(
            event["schema_version"] == news_data.ECONOMIC_EVENT_SCHEMA
            and event["revision_number"] == 1
            and event["actual"] is None
            and event["forecast"] is None
            and event["previous"] is None
            and event["importance"] is None
            for event in first
        ))
        self.assertEqual(
            [
                (
                    event["event_id"], event["event_series_id"],
                    news_data.observation_fingerprint(event),
                    event["revision_number"],
                )
                for event in first
            ],
            [
                (
                    event["event_id"], event["event_series_id"],
                    news_data.observation_fingerprint(event),
                    event["revision_number"],
                )
                for event in reversed_result
            ],
        )

    def test_bea_product_mapping_uses_event_id_as_final_tiebreaker(self):
        document = {
            "Product B": {"release_dates": ["2026-08-01T12:00:00Z"]},
            "Product A": {"release_dates": ["2026-08-01T12:00:00Z"]},
            "file_last_updated": "2026-07-29T16:45:00Z",
        }
        original = copy.deepcopy(document)

        def constructed_event(_source, name, *_values):
            return {
                "scheduled_timestamp_utc": "2026-08-01T12:00:00Z",
                "event_series_id": "EVENT-SERIES-SAME",
                "event_id": "EVENT-A" if name == "Product A" else "EVENT-B",
            }

        with mock.patch.object(
            news_data, "economic_event", side_effect=constructed_event,
        ):
            events = news_parser._product_release_events(
                document, self.bea_source, "2026-07-30T08:00:00Z",
            )
        self.assertEqual(
            [event["event_id"] for event in events], ["EVENT-A", "EVENT-B"]
        )
        self.assertEqual(document, original)

    def test_bea_product_names_must_already_be_exactly_canonical(self):
        valid_timestamp = "2026-08-01T12:00:00Z"
        invalid_names = (
            "GDP\nRelease",
            "GDP\tRelease",
            "GDP\rRelease",
            "GDP<script>secret</script>Release",
            "GDP<style>secret</style>Release",
            "GDP<iframe>secret</iframe>Release",
            "GDP<object>secret</object>Release",
            "GDP<embed>secret</embed>Release",
            "GDP<svg>secret</svg>Release",
            "GDP<math>secret</math>Release",
            "GDP<img src=x>Release",
            "GDP<template>secret</template>Release",
            "GDP<noscript>secret</noscript>Release",
            "GDP<form>secret</form>Release",
            "GDP<area>Release",
            "GDP<base>Release",
            "GDP<br>Release",
            "GDP<col>Release",
            "GDP<hr>Release",
            "GDP<input>Release",
            "GDP<link>Release",
            "GDP<meta>Release",
            "GDP<param>Release",
            "GDP<source>Release",
            "GDP<track>Release",
            "GDP<wbr>Release",
            "GDP&lt;script&gt;secret&lt;/script&gt;Release",
            "GDP&amp;lt;script&amp;gt;secret&amp;lt;/script&amp;gt;Release",
            "GDP\x00Release",
            "GDP\x01Release",
            "GDP\x7fRelease",
            "GDP\x85Release",
            "GDP\u202eRelease",
            "GDP\u200dRelease",
            " GDP Release",
            "GDP Release ",
            "GDP  Release",
            "",
            "x" * (news_data.MAX_TEXT_LENGTH + 1),
            "x" * (news_data.MAX_TITLE_INPUT_LENGTH + 1),
        )
        for product_name in invalid_names:
            with self.subTest(product_name=repr(product_name)), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_parser.parse_bea_release_dates(
                    json.dumps({
                        product_name: {"release_dates": [valid_timestamp]},
                        "file_last_updated": "2026-07-29T16:45:00Z",
                    }, separators=(",", ":")).encode("utf-8"),
                    self.bea_source,
                    "2026-07-30T08:00:00Z",
                )

        accepted_names = (
            "Gross Domestic Product",
            "الناتج المحلي الإجمالي",
        )
        for product_name in accepted_names:
            with self.subTest(product_name=product_name):
                events = news_parser.parse_bea_release_dates(
                    json.dumps({
                        product_name: {"release_dates": [valid_timestamp]},
                        "file_last_updated": "2026-07-29T16:45:00Z",
                    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
                    self.bea_source,
                    "2026-07-30T08:00:00Z",
                )
                self.assertEqual([event["event_name"] for event in events], [product_name])

    def test_bea_product_and_raw_date_bounds_count_before_deduplication(self):
        metadata = "2026-07-29T16:45:00Z"
        empty_200 = {
            "Product {:03d}".format(index): {"release_dates": []}
            for index in range(200)
        }
        empty_200["file_last_updated"] = metadata
        self.assertEqual(
            news_parser.parse_bea_release_dates(
                json.dumps(empty_200, separators=(",", ":")).encode("utf-8"),
                self.bea_source,
                "2026-07-30T08:00:00Z",
            ),
            [],
        )

        empty_201 = {
            "Product {:03d}".format(index): {"release_dates": []}
            for index in range(201)
        }
        empty_201["file_last_updated"] = metadata
        with self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
        ):
            news_parser.parse_bea_release_dates(
                json.dumps(empty_201, separators=(",", ":")).encode("utf-8"),
                self.bea_source,
                "2026-07-30T08:00:00Z",
            )

        raw_200 = [
            news_data.utc_timestamp(
                datetime(2026, 8, 1, tzinfo=timezone.utc) + timedelta(hours=index)
            )
            for index in range(200)
        ]
        accepted = news_parser.parse_bea_release_dates(
            json.dumps({
                "Bounded Product": {"release_dates": raw_200},
                "file_last_updated": metadata,
            }, separators=(",", ":")).encode("utf-8"),
            self.bea_source,
            "2026-07-30T08:00:00Z",
        )
        self.assertEqual(len(accepted), 200)

        for dates in (raw_200 + ["2026-09-01T00:00:00Z"], [raw_200[0]] * 201):
            with self.subTest(unique=len(set(dates))), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_parser.parse_bea_release_dates(
                    json.dumps({
                        "Oversized Product": {"release_dates": dates},
                        "file_last_updated": metadata,
                    }, separators=(",", ":")).encode("utf-8"),
                    self.bea_source,
                    "2026-07-30T08:00:00Z",
                )

        self.assertEqual(
            news_parser.parse_bea_release_dates(
                json.dumps({
                    "file_last_updated": metadata,
                }, separators=(",", ":")).encode("utf-8"),
                self.bea_source,
                "2026-07-30T08:00:00Z",
            ),
            [],
        )

    def test_bea_product_release_mapping_rejects_unbounded_or_variant_shapes(self):
        valid_timestamp = "2026-07-30T08:30:00-04:00"
        cases = (
            {"GDP": {"release_dates": [valid_timestamp]}},
            {"GDP": {"release_dates": valid_timestamp}, "file_last_updated": "x"},
            {"GDP": {"release_dates": ["2026-07-30"]}, "file_last_updated": "x"},
            {
                "GDP": {"release_dates": ["Wed, 29 Jul 2026 10:01:38 EDT"]},
                "file_last_updated": "x",
            },
            {
                "GDP": {"release_dates": [valid_timestamp], "extra": []},
                "file_last_updated": "x",
            },
            {"GDP": {"release_dates": [valid_timestamp]}, "file_last_updated": None},
            {
                "GDP": {"release_dates": [valid_timestamp]},
                "file_last_updated": "x" * 101,
            },
            {
                "GDP": {"release_dates": [valid_timestamp]},
                "file_last_updated": "bad\nmetadata",
            },
            {
                "GDP": {"release_dates": [valid_timestamp] * 201},
                "file_last_updated": "x",
            },
        )
        for document in cases:
            with self.subTest(document=document), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_parser.parse_bea_release_dates(
                    json.dumps(document, separators=(",", ":")).encode("utf-8"),
                    self.bea_source,
                    "2026-07-30T08:00:00Z",
                )

    def test_event_series_and_scheduled_occurrence_identities_are_distinct(self):
        body = json.dumps({"release_dates": [
            {"ReleaseDate": "2026-07-30", "ReleaseName": "GDP"},
            {"ReleaseDate": "2026-08-27", "ReleaseName": "GDP"},
            {"ReleaseDate": "2026-07-30", "ReleaseName": "Personal Income"},
        ]}, separators=(",", ":")).encode("utf-8")
        first = news_parser.parse_bea_release_dates(
            body, self.bea_source, "2026-07-27T12:00:00Z"
        )
        repeated = news_parser.parse_bea_release_dates(
            body, self.bea_source, "2026-07-28T12:00:00Z"
        )
        gdp = [event for event in first if event["event_name"] == "GDP"]
        repeated_gdp = [
            event for event in repeated if event["event_name"] == "GDP"
        ]
        self.assertEqual(len(gdp), 2)
        self.assertEqual(len({event["event_id"] for event in gdp}), 2)
        self.assertEqual(len({event["event_series_id"] for event in gdp}), 1)
        self.assertEqual(
            [event["event_id"] for event in gdp],
            [event["event_id"] for event in repeated_gdp],
        )
        personal_income = next(
            event for event in first if event["event_name"] == "Personal Income"
        )
        self.assertNotEqual(gdp[0]["event_series_id"], personal_income["event_series_id"])
        other_source = news_sources.load_source_registry()["sources"][0]
        other_source_event = news_data.economic_event(
            other_source, "GDP", "2026-07-30", None,
            "2026-07-27T12:00:00Z", None,
        )
        self.assertNotEqual(gdp[0]["event_series_id"], other_source_event["event_series_id"])
        self.assertNotEqual(gdp[0]["event_id"], other_source_event["event_id"])
        for event in gdp:
            self.assertEqual(
                event["event_occurrence_identity_limitation"],
                news_data.EVENT_OCCURRENCE_IDENTITY_LIMITATION,
            )

        registry = news_sources.load_source_registry()
        document = cached_document(*(
            cached_wrapper(event, "event") for event in gdp
        ))
        accepted = news_cache.validate_document(document, FIXED_NOW, registry)
        self.assertEqual(
            [(wrapper["record"]["event_series_id"], wrapper["identity"])
             for wrapper in accepted["records"]],
            [(event["event_series_id"], event["event_id"]) for event in gdp],
        )

        transport = valid_transport(registry)
        transport.responses[self.bea_source["exact_endpoint"]] = response(
            self.bea_source, body=body
        )
        clock = FakeClock()
        service = enabled_service(transport, clock)
        first_service_events = service.economic_events_document()["events"]
        clock.advance(900)
        repeated_service_events = service.economic_events_document()["events"]
        self.assertEqual(len(first_service_events), 3)
        self.assertEqual(
            [event["event_id"] for event in first_service_events],
            [event["event_id"] for event in repeated_service_events],
        )
        self.assertEqual(
            [event["scheduled_timestamp_utc"] for event in first_service_events],
            sorted(event["scheduled_timestamp_utc"] for event in first_service_events),
        )

    def test_bea_optional_value_limit_matches_complete_record_validation(self):
        accepted_value = "x" * news_data.MAX_TEXT_LENGTH
        accepted_body = json.dumps({"release_dates": [{
            "ReleaseDate": "2026-07-30",
            "ReleaseName": "Bounded value",
            "actual": accepted_value,
        }]}, separators=(",", ":")).encode("utf-8")
        accepted = news_parser.parse_bea_release_dates(
            accepted_body, self.bea_source, "2026-07-27T12:00:00Z"
        )[0]
        self.assertEqual(accepted["actual"], accepted_value)
        news_data.validate_cached_record("event", accepted, self.bea_source)

        rejected_body = json.dumps({"release_dates": [{
            "ReleaseDate": "2026-07-30",
            "ReleaseName": "Oversized value",
            "actual": accepted_value + "x",
        }]}, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(
            news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
        ):
            news_parser.parse_bea_release_dates(
                rejected_body, self.bea_source, "2026-07-27T12:00:00Z"
            )
        self.assertNotIn("bullish", json.dumps(accepted).lower())
        self.assertNotIn("bearish", json.dumps(accepted).lower())

    def test_no_full_text_html_script_image_or_body_retention(self):
        item = self.parse_xml(RSS_BODY)[0]
        encoded = json.dumps(item).lower()
        for forbidden in ("body not retained", "<script", "tracking", "<img", "description"):
            self.assertNotIn(forbidden, encoded)
        title_markup = b"<rss><channel><item><title><![CDATA[Safe <b>title</b><script>bad()</script>]]></title></item></channel></rss>"
        self.assertEqual(self.parse_xml(title_markup)[0]["title"], "Safe title")
        for punctuation in ("=", "!", "?", "@"):
            with self.subTest(punctuation=punctuation), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                self.parse_xml(
                    (
                        "<rss><channel><item><title><![CDATA[Safe <script"
                        + punctuation
                        + "foo>secret</script"
                        + punctuation
                        + "foo> Tail]]></title></item></channel></rss>"
                    ).encode("utf-8")
                )

    def test_title_markup_uses_tag_aware_blocking_and_preserves_text_after_images(self):
        cases = (
            ('Before<img src="track">After', "Before After"),
            ('Before<img src="track"/>After', "Before After"),
            ("Before<form>hidden<object>nested</object>hidden</form>After", "Before After"),
            ("Before<script>script text</script>Middle<style>style text</style>After", "Before Middle After"),
            ("Before<template>template text</template><noscript>fallback text</noscript>After", "Before After"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                first = news_parser.safe_title(value)
                second = news_parser.safe_title(value)
                self.assertEqual(first, expected)
                self.assertEqual(second, expected)
        for malformed in (
            "Before<form><object>hidden</form></object>After",
            "Before<form>unclosed",
            "Before</img>After",
        ):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_parser.safe_title(malformed)

    def test_xml_title_tree_is_sanitized_before_text_flattening(self):
        cases = (
            (b"<title>Safe<script>secret()</script>After</title>", "SafeAfter"),
            (b"<title>Safe<script>one<style>two</style></script><template>three</template>After</title>", "SafeAfter"),
            (b'<title xmlns:x="urn:test">Safe<x:script>secret()</x:script>After</title>', "SafeAfter"),
            (b"<title>Safe<script.foo>secret()</script.foo>After</title>", "SafeAfter"),
            (b"<title>Safe<b> formatted </b>After</title>", "Safe formatted After"),
            (b'<title>Safe<img src="tracking"/>After</title>', "SafeAfter"),
            (b"<title>Safe&lt;script&gt;secret()&lt;/script&gt;After</title>", "Safe After"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                body = b"<rss><channel><item>" + title + b"</item></channel></rss>"
                original = bytes(body)
                first = self.parse_xml(body)[0]["title"]
                second = self.parse_xml(body)[0]["title"]
                self.assertEqual(first, expected)
                self.assertEqual(second, expected)
                self.assertEqual(body, original)
                self.assertNotIn("secret", first)

    def test_shared_title_canonicalizer_is_bounded_idempotent_and_cache_enforced(self):
        encoded_cases = (
            "Safe &amp;lt;script&amp;gt;secret()&amp;lt;/script&amp;gt; After",
            "Safe &amp;amp;lt;style&amp;amp;gt;hidden&amp;amp;lt;/style&amp;amp;gt; After",
            "Before &amp;lt;template&amp;gt;hidden&amp;lt;/template&amp;gt; Tail",
        )
        for value in encoded_cases:
            with self.subTest(value=value):
                canonical = news_data.canonical_title(value)
                self.assertNotIn("secret", canonical)
                self.assertNotIn("hidden", canonical)
                self.assertNotIn("<", canonical)
                self.assertEqual(news_data.canonical_title(canonical), canonical)

        safe_arabic = "بيانات اقتصادية رسمية"
        self.assertEqual(news_data.canonical_title(safe_arabic), safe_arabic)
        self.assertEqual(news_data.canonical_title("Café – 東京"), "Café – 東京")
        for misleading in ("safe\u202etext", "safe\u2066text", "safe\u200btext"):
            with self.subTest(misleading=repr(misleading)), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_data.canonical_title(misleading)

        registry, valid_news, valid_event = governed_cache_fixtures()
        malicious_news = copy.deepcopy(valid_news)
        malicious_news["title"] = encoded_cases[0]
        malicious_news_document = cached_document(
            cached_wrapper(malicious_news, "news")
        )
        malicious_event = copy.deepcopy(valid_event)
        malicious_event["event_name"] = "Official\u202eEvent"
        malicious_event["event_series_id"] = news_data.stable_identifier(
            "EVENT-SERIES",
            (
                malicious_event["source_id"], malicious_event["event_name"],
                malicious_event["event_series_identity_basis"],
                malicious_event["source_url_availability_status"],
            ),
        )
        malicious_event["event_id"] = news_data.stable_identifier(
            "EVENT",
            (
                malicious_event["event_series_id"],
                malicious_event["scheduled_timestamp_utc"],
                malicious_event["scheduled_time_precision"],
            ),
        )
        malicious_event_document = cached_document(
            cached_wrapper(malicious_event, "event")
        )
        for document in (malicious_news_document, malicious_event_document):
            with self.assertRaisesRegex(news_cache.CacheError, "NEWS_CACHE_INVALID"):
                news_cache.validate_document(document, FIXED_NOW, registry)

        arabic_news = news_data.news_item(
            self.rss_source, safe_arabic,
            "https://www.federalreserve.gov/newsevents/pressreleases/arabic.htm",
            "2026-07-27T10:00:00Z", "2026-07-27T12:00:00Z",
        )
        accepted = news_cache.validate_document(
            cached_document(cached_wrapper(arabic_news, "news")),
            FIXED_NOW, registry,
        )
        self.assertEqual(accepted["records"][0]["record"]["title"], safe_arabic)

    def test_namespace_dotted_and_malformed_blocked_markup_hardening(self):
        cases = (
            ("Safe <x:script>secret()</x:script> Tail", "Safe Tail"),
            ("Safe &lt;x:script&gt;secret()&lt;/x:script&gt; Tail", "Safe Tail"),
            ("Safe <svg:style>secret</svg:style> Tail", "Safe Tail"),
            ("Safe <script.foo>secret</script.foo> Tail", "Safe Tail"),
            (
                "Before<X:FoRm>hidden<SVG:STYLE>nested</SVG:STYLE></X:FoRm>After",
                "Before After",
            ),
            (
                "Before &amp;lt;X:SCRIPT&amp;gt;hidden&amp;lt;/X:SCRIPT&amp;gt; After",
                "Before After",
            ),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                canonical = news_data.canonical_title(value)
                self.assertEqual(canonical, expected)
                self.assertEqual(news_data.canonical_title(canonical), canonical)
                self.assertNotIn("secret", canonical.lower())
                self.assertNotIn("hidden", canonical.lower())
                self.assertNotIn("nested", canonical.lower())

        for malformed in (
            "Safe <script secret Tail",
            "Safe <x:script>secret Tail",
            "Safe <x:script>secret</svg:script> Tail",
            "Safe </script.foo> Tail",
            "Safe <script=foo>secret</script=foo> Tail",
            "Safe <script!foo>secret</script!foo> Tail",
            "Safe <script?foo>secret</script?foo> Tail",
            "Safe <script@foo>secret</script@foo> Tail",
            "Safe <STYLE=foo>secret</STYLE=foo> Tail",
            "Safe <style!foo>secret</style!foo> Tail",
            "Safe <style?foo>secret</style?foo> Tail",
            "Safe <style@foo>secret</style@foo> Tail",
            "Safe <x:script=foo>secret</x:script=foo> Tail",
            "Safe <safe.script!foo>secret</safe.script!foo> Tail",
            "Safe <script.foo?bar>secret</script.foo?bar> Tail",
            "Safe <x:script.foo@bar>secret</x:script.foo@bar> Tail",
            "Safe &lt;script=foo&gt;secret&lt;/script=foo&gt; Tail",
            "Safe &amp;lt;STYLE@foo&amp;gt;secret&amp;lt;/STYLE@foo&amp;gt; Tail",
        ):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_data.canonical_title(malformed)

        self.assertEqual(
            news_data.canonical_title("1 < 2 and 3 > 2"),
            "1 < 2 and 3 > 2",
        )
        self.assertEqual(
            news_data.canonical_title('<span class="safe">Text</span>'),
            "Text",
        )
        safe_arabic = "بيانات اقتصادية رسمية"
        self.assertEqual(news_data.canonical_title(safe_arabic), safe_arabic)

        registry, valid_news, valid_event = governed_cache_fixtures()
        injected = copy.deepcopy(valid_news)
        injected["title"] = "Safe <x:script>secret()</x:script> Tail"
        malformed_news = copy.deepcopy(valid_news)
        malformed_news["title"] = "Safe <script=foo>secret</script=foo> Tail"
        malformed_event = copy.deepcopy(valid_event)
        malformed_event["event_name"] = (
            "Safe <STYLE@foo>secret</STYLE@foo> Tail"
        )
        series_material = (
            malformed_event["source_url"]
            if malformed_event["source_url_availability_status"]
            == "GOVERNED_ITEM_LINK_AVAILABLE"
            else malformed_event["source_url_availability_status"]
        )
        malformed_event["event_series_id"] = news_data.stable_identifier(
            "EVENT-SERIES",
            (
                malformed_event["source_id"],
                malformed_event["event_name"],
                malformed_event["event_series_identity_basis"],
                series_material,
            ),
        )
        malformed_event["event_id"] = news_data.stable_identifier(
            "EVENT",
            (
                malformed_event["event_series_id"],
                malformed_event["scheduled_timestamp_utc"],
                malformed_event["scheduled_time_precision"],
            ),
        )
        for document in (
            cached_document(cached_wrapper(injected, "news")),
            cached_document(cached_wrapper(malformed_news, "news")),
            cached_document(cached_wrapper(malformed_event, "event")),
        ):
            with self.assertRaisesRegex(
                news_cache.CacheError, "NEWS_CACHE_INVALID",
            ):
                news_cache.validate_document(document, FIXED_NOW, registry)

    def test_bea_date_only_grammar_and_fractional_publication_precision(self):
        exact = news_data.parse_schedule_timestamp("2026-07-30")
        self.assertEqual(exact, (
            "2026-07-30T00:00:00Z", "SOURCE_DATE_ONLY", True,
        ))
        for invalid in (
            "20260730", "2026-W31-4", " 2026-07-30",
            "2026-07-30 ", "2026-07-30suffix", "2026-02-30",
        ):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                news_data.NewsValidationError, "NEWS_SOURCE_SCHEMA_INVALID"
            ):
                news_data.parse_schedule_timestamp(invalid)
        timestamp = news_data.parse_schedule_timestamp(
            "2026-07-30T09:00:00.125Z"
        )
        self.assertEqual(timestamp, (
            "2026-07-30T09:00:00.125Z", "SOURCE_TIMESTAMP_VALID", False,
        ))

        first = news_data.news_item(
            self.rss_source, "Fractional fallback", None,
            "2026-07-27T10:00:00.1Z", "2026-07-27T12:00:00Z",
        )
        second = news_data.news_item(
            self.rss_source, "Fractional fallback", None,
            "2026-07-27T10:00:00.2Z", "2026-07-28T12:00:00Z",
        )
        equivalent = news_data.news_item(
            self.rss_source, "Fractional fallback", None,
            "2026-07-27T14:00:00.100000+04:00", "2026-07-29T12:00:00Z",
        )
        repeated = news_data.news_item(
            self.rss_source, "Fractional fallback", None,
            "2026-07-27T10:00:00.100000Z", "2026-07-30T12:00:00Z",
        )
        self.assertEqual(first["published_timestamp_utc"], "2026-07-27T10:00:00.1Z")
        self.assertEqual(equivalent["published_timestamp_utc"], first["published_timestamp_utc"])
        self.assertNotEqual(first["published_timestamp_utc"], second["published_timestamp_utc"])
        self.assertNotEqual(first["news_id"], second["news_id"])
        self.assertEqual(first["news_id"], equivalent["news_id"])
        self.assertEqual(first["news_id"], repeated["news_id"])


class IdentityCacheAndServiceTests(unittest.TestCase):
    def test_bea_canonical_order_survives_cache_round_trip_and_api(self):
        registry = news_sources.load_source_registry()
        bea = next(
            source for source in registry["sources"]
            if source["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        retrieved = news_data.utc_timestamp(FIXED_NOW)
        first_document = {
            "Alpha Product": {"release_dates": [
                "2026-08-01T12:00:00.1Z",
                "2026-08-01T16:00:00.100000+04:00",
                "2026-08-01T12:00:00Z",
                "2026-08-01T16:00:00+04:00",
                "2026-08-01T12:00:00.001Z",
                "2026-08-01T07:00:00.001-05:00",
                "2026-08-01T11:59:59.999999Z",
            ]},
            "Beta Product": {"release_dates": [
                "2026-08-01T12:00:01.000001Z",
                "2026-08-01T12:00:00.01Z",
                "2026-08-01T07:00:00.010-05:00",
                "2026-08-01T12:00:00.000001Z",
                "2026-08-01T12:00:01Z",
            ]},
            "file_last_updated": "2026-07-29T16:45:00Z",
        }
        reversed_document = {
            "Beta Product": {
                "release_dates": list(reversed(
                    first_document["Beta Product"]["release_dates"]
                )),
            },
            "Alpha Product": {
                "release_dates": list(reversed(
                    first_document["Alpha Product"]["release_dates"]
                )),
            },
            "file_last_updated": first_document["file_last_updated"],
        }

        def encoded(document):
            return json.dumps(document, separators=(",", ":")).encode("utf-8")

        expected = news_parser.parse_bea_release_dates(
            encoded(first_document), bea, retrieved,
        )
        expected_ids = [event["event_id"] for event in expected]
        expected_fingerprints = [
            news_data.observation_fingerprint(event) for event in expected
        ]
        expected_revisions = [event["revision_number"] for event in expected]
        expected_timestamps = [
            "2026-08-01T11:59:59.999999Z",
            "2026-08-01T12:00:00Z",
            "2026-08-01T12:00:00.000001Z",
            "2026-08-01T12:00:00.001Z",
            "2026-08-01T12:00:00.01Z",
            "2026-08-01T12:00:00.1Z",
            "2026-08-01T12:00:01Z",
            "2026-08-01T12:00:01.000001Z",
        ]
        self.assertEqual(
            [event["scheduled_timestamp_utc"] for event in expected],
            expected_timestamps,
        )

        cache_document = cached_document(*(
            cached_wrapper(event, "event") for event in expected
        ))
        round_trip_storage = news_cache.InMemoryCacheStorage()
        round_trip_storage.write(cache_document)
        loaded = news_cache.validate_document(
            round_trip_storage.load(), FIXED_NOW, registry,
        )
        self.assertEqual(
            [wrapper["record"]["event_id"] for wrapper in loaded["records"]],
            expected_ids,
        )

        clock = FakeClock()
        storage = news_cache.InMemoryCacheStorage()
        transport = valid_transport(registry)
        transport.responses[bea["exact_endpoint"]] = response(
            bea, body=encoded(first_document),
        )
        service = enabled_service(transport, clock, storage)
        try:
            first_api = [
                event for event in service.economic_events_document()["events"]
                if event["source_id"] == bea["source_id"]
            ]
            self.assertEqual(
                [event["event_id"] for event in first_api], expected_ids
            )
            self.assertEqual(
                [event["scheduled_timestamp_utc"] for event in first_api],
                expected_timestamps,
            )
            self.assertEqual(
                [news_data.observation_fingerprint(event) for event in first_api],
                expected_fingerprints,
            )
            self.assertEqual(
                [event["revision_number"] for event in first_api],
                expected_revisions,
            )

            transport.responses[bea["exact_endpoint"]] = response(
                bea, body=encoded(reversed_document),
            )
            clock.advance(900)
            repeated_api = [
                event for event in service.economic_events_document()["events"]
                if event["source_id"] == bea["source_id"]
            ]
            self.assertEqual(
                [event["event_id"] for event in repeated_api], expected_ids
            )
            self.assertEqual(
                [event["scheduled_timestamp_utc"] for event in repeated_api],
                expected_timestamps,
            )
            self.assertEqual(
                [news_data.observation_fingerprint(event)
                 for event in repeated_api],
                expected_fingerprints,
            )
            self.assertEqual(
                [event["revision_number"] for event in repeated_api],
                expected_revisions,
            )
        finally:
            self.assertTrue(service.shutdown())

        failed_transport = FakeTransport({
            source["exact_endpoint"]: RetrievalError("NEWS_SOURCE_TIMEOUT")
            for source in registry["sources"]
        })
        reloaded = enabled_service(
            failed_transport, FakeClock(clock.value), storage,
        )
        try:
            cached_api = [
                event for event in reloaded.economic_events_document()["events"]
                if event["source_id"] == bea["source_id"]
            ]
            self.assertEqual(
                [event["event_id"] for event in cached_api], expected_ids
            )
            self.assertEqual(
                [event["scheduled_timestamp_utc"] for event in cached_api],
                expected_timestamps,
            )
            self.assertEqual(
                [news_data.observation_fingerprint(event) for event in cached_api],
                expected_fingerprints,
            )
            self.assertEqual(
                [event["revision_number"] for event in cached_api],
                expected_revisions,
            )
        finally:
            self.assertTrue(reloaded.shutdown())

    def test_bea_equivalent_dates_remain_valid_stable_and_cache_reloadable(self):
        registry = news_sources.load_source_registry()
        bea = next(
            source for source in registry["sources"]
            if source["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        equivalent_dates = [
            "2026-08-01T12:00:00Z",
            "2026-08-01T16:00:00+04:00",
            "2026-08-01T12:00:00Z",
        ]

        def schedule_body(dates):
            return json.dumps({
                "Gross Domestic Product": {"release_dates": dates},
                "file_last_updated": "2026-07-29T16:45:00Z",
            }, separators=(",", ":")).encode("utf-8")

        clock = FakeClock()
        storage = news_cache.InMemoryCacheStorage()
        transport = valid_transport(registry)
        transport.responses[bea["exact_endpoint"]] = response(
            bea, body=schedule_body(equivalent_dates)
        )
        service = enabled_service(transport, clock, storage)
        self.assertEqual(service.health_document()["status"], "NEWS_VALID")
        first = [
            event for event in service.economic_events_document()["events"]
            if event["source_id"] == bea["source_id"]
        ]
        self.assertEqual(len(first), 1)
        first = first[0]
        first_fingerprint = news_data.observation_fingerprint(first)

        transport.responses[bea["exact_endpoint"]] = response(
            bea, body=schedule_body(list(reversed(equivalent_dates)))
        )
        clock.advance(900)
        self.assertEqual(service.health_document()["status"], "NEWS_VALID")
        repeated = [
            event for event in service.economic_events_document()["events"]
            if event["source_id"] == bea["source_id"]
        ]
        self.assertEqual(len(repeated), 1)
        repeated = repeated[0]
        self.assertEqual(repeated["event_series_id"], first["event_series_id"])
        self.assertEqual(repeated["event_id"], first["event_id"])
        self.assertEqual(
            news_data.observation_fingerprint(repeated), first_fingerprint
        )
        self.assertEqual(repeated["revision_number"], first["revision_number"])

        failed_transport = FakeTransport({
            source["exact_endpoint"]: RetrievalError("NEWS_SOURCE_TIMEOUT")
            for source in registry["sources"]
        })
        reloaded = enabled_service(failed_transport, FakeClock(clock.value), storage)
        self.assertEqual(
            reloaded.health_document()["status"], "NEWS_ALL_SOURCES_FAILED"
        )
        cached = [
            event for event in reloaded.economic_events_document()["events"]
            if event["source_id"] == bea["source_id"]
        ]
        self.assertEqual(len(cached), 1)
        cached = cached[0]
        self.assertEqual(cached["event_series_id"], first["event_series_id"])
        self.assertEqual(cached["event_id"], first["event_id"])
        self.assertEqual(news_data.observation_fingerprint(cached), first_fingerprint)
        self.assertEqual(cached["revision_number"], first["revision_number"])

    def test_rejected_bea_product_name_never_reaches_cache_or_api(self):
        registry = news_sources.load_source_registry()
        bea = next(
            source for source in registry["sources"]
            if source["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        rejected_canonical_result = "Rejected Product"
        rejected_body = json.dumps({
            "Rejected<script>secret</script> Product": {
                "release_dates": ["2026-08-01T12:00:00Z"],
            },
            "file_last_updated": "2026-07-29T16:45:00Z",
        }, separators=(",", ":")).encode("utf-8")
        storage = InspectingCacheStorage(rejected_canonical_result)
        transport = valid_transport(registry)
        transport.responses[bea["exact_endpoint"]] = response(
            bea, body=rejected_body
        )
        service = enabled_service(transport, cache=storage)
        health = service.health_document()
        bea_health = next(
            item for item in health["source_health"]
            if item["source_id"] == bea["source_id"]
        )
        serialized_api = json.dumps(
            service.economic_events_document(), ensure_ascii=False
        )
        serialized_cache = json.dumps(storage.value, ensure_ascii=False)
        self.assertEqual(health["status"], "NEWS_PARTIAL")
        self.assertEqual(bea_health["status"], "NEWS_SOURCE_SCHEMA_INVALID")
        self.assertEqual(storage.invalid_candidate_writes, 0)
        self.assertNotIn("Rejected", serialized_api)
        self.assertNotIn("Rejected", serialized_cache)

    def test_oversized_bea_raw_duplicates_are_transactional_and_recover(self):
        registry = news_sources.load_source_registry()
        bea = next(
            source for source in registry["sources"]
            if source["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        fed = registry["sources"][0]
        clock = FakeClock()
        forbidden = "Oversized BEA Product"
        storage = InspectingCacheStorage(forbidden)
        transport = valid_transport(registry)
        service = enabled_service(transport, clock, storage)
        self.assertEqual(service.health_document()["status"], "NEWS_VALID")
        trusted = next(
            event for event in service.economic_events_document()["events"]
            if event["source_id"] == bea["source_id"]
        )

        oversized = json.dumps({
            forbidden: {
                "release_dates": ["2026-08-01T12:00:00Z"] * 201,
            },
            "file_last_updated": "2026-07-29T16:45:00Z",
        }, separators=(",", ":")).encode("utf-8")
        transport.responses[bea["exact_endpoint"]] = response(
            bea, body=oversized
        )
        transport.responses[fed["exact_endpoint"]] = response(
            fed,
            body=RSS_BODY.replace(
                b"Official &amp; governed release", b"Independent valid update"
            ),
        )
        clock.advance(900)
        partial = service.health_document()
        bea_health = next(
            item for item in partial["source_health"]
            if item["source_id"] == bea["source_id"]
        )
        retained = next(
            event for event in service.economic_events_document()["events"]
            if event["event_id"] == trusted["event_id"]
        )
        updated_fed = next(
            item for item in service.news_items_document()["items"]
            if item["source_id"] == fed["source_id"]
        )
        self.assertEqual(partial["status"], "NEWS_PARTIAL")
        self.assertEqual(bea_health["status"], "NEWS_SOURCE_SCHEMA_INVALID")
        self.assertEqual(retained["operational_freshness_status"], "NEWS_RECORD_STALE")
        self.assertEqual(retained["event_id"], trusted["event_id"])
        self.assertEqual(retained["revision_number"], trusted["revision_number"])
        self.assertEqual(updated_fed["title"], "Independent valid update")
        self.assertEqual(storage.invalid_candidate_writes, 0)
        self.assertNotIn(forbidden, json.dumps(storage.value, ensure_ascii=False))

        transport.responses[bea["exact_endpoint"]] = response(bea)
        clock.advance(900)
        recovered = service.health_document()
        recovered_event = next(
            event for event in service.economic_events_document()["events"]
            if event["event_id"] == trusted["event_id"]
        )
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertEqual(
            recovered_event["operational_freshness_status"], "NEWS_RECORD_CURRENT"
        )
        self.assertEqual(
            recovered_event["revision_number"], trusted["revision_number"]
        )

    def test_official_format_compatibility_through_injected_transport(self):
        registry = news_sources.load_source_registry()
        transport = valid_transport(registry)
        by_id = {source["source_id"]: source for source in registry["sources"]}

        bls_description = "x" * 4589
        bls_body = (
            "<rss><channel><item><title>Synthetic BLS metadata</title>"
            "<link>https://www.bls.gov/bls/</link>"
            "<pubDate>Wed, 29 Jul 2026 10:01:38 -0400</pubDate>"
            "<description>" + bls_description + "</description>"
            "</item></channel></rss>"
        ).encode("utf-8")
        bls = by_id["BLS_LATEST_RELEASES_RSS"]
        transport.responses[bls["exact_endpoint"]] = response(
            bls, body=bls_body, content_type="application/rss+xml"
        )

        bea_rows = "".join(
            "<item><title>Synthetic BEA metadata {0}</title>"
            "<link>https://www.bea.gov/news/synthetic-{0}</link>"
            "<description>Discarded synthetic description {0}</description>"
            "<pubDate>Wed, 29 Jul 2026 10:01:38 EDT</pubDate></item>".format(index)
            for index in range(46)
        )
        bea_rss_body = ("<rss><channel>" + bea_rows + "</channel></rss>").encode(
            "utf-8"
        )
        bea_rss = by_id["BEA_NEWS_RELEASE_RSS"]
        transport.responses[bea_rss["exact_endpoint"]] = response(
            bea_rss, body=bea_rss_body, content_type="text/xml"
        )

        bea_json_body = json.dumps({
            "Gross Domestic Product": {
                "release_dates": [
                    "2026-07-30T08:30:00-04:00",
                    "2026-08-27T08:30:00-04:00",
                ],
            },
            "Personal Income and Outlays": {
                "release_dates": ["2026-07-31T08:30:00-04:00"],
            },
            "file_last_updated": "2026-07-29T16:45:00Z",
        }, separators=(",", ":")).encode("utf-8")
        bea_json = by_id["BEA_RELEASE_DATES_JSON"]
        transport.responses[bea_json["exact_endpoint"]] = response(
            bea_json, body=bea_json_body, content_type="application/json"
        )

        service = enabled_service(
            transport,
            clock=FakeClock(
                datetime(2026, 7, 30, 8, 0, 0, tzinfo=timezone.utc)
            ),
        )
        health = service.health_document()
        news = service.news_items_document()["items"]
        events = service.economic_events_document()["events"]
        source_health = {
            source["source_id"]: source
            for source in service.sources_document()["sources"]
        }

        self.assertEqual(health["status"], "NEWS_VALID")
        self.assertEqual(health["network_request_count"], 6)
        self.assertEqual(len(transport.calls), 6)
        self.assertEqual(set(transport.calls), {
            source["exact_endpoint"] for source in registry["sources"]
        })
        self.assertEqual(len(news), 50)
        self.assertEqual(len(events), 3)
        self.assertEqual(
            source_health["BLS_LATEST_RELEASES_RSS"]["health"][
                "retrieved_entry_count"
            ], 1
        )
        self.assertEqual(
            source_health["BEA_NEWS_RELEASE_RSS"]["health"][
                "retrieved_entry_count"
            ], 46
        )
        self.assertEqual(
            source_health["BEA_RELEASE_DATES_JSON"]["health"][
                "retrieved_entry_count"
            ], 3
        )
        retained = json.dumps({"news": news, "events": events})
        self.assertNotIn(bls_description, retained)
        self.assertNotIn("Discarded synthetic description", retained)
        self.assertNotIn("file_last_updated", retained)

    def test_complete_cache_record_schema_and_governance_validation(self):
        registry, valid_news, valid_event, cases = adversarial_cache_documents()
        valid_document = cached_document(
            cached_wrapper(valid_news, "news"),
            cached_wrapper(valid_event, "event"),
        )
        accepted = news_cache.validate_document(valid_document, FIXED_NOW, registry)
        self.assertEqual(len(accepted["records"]), 2)
        for original, wrapper in zip((valid_news, valid_event), accepted["records"]):
            self.assertEqual(wrapper["record"], original)
            self.assertEqual(
                wrapper["fingerprint"], news_data.observation_fingerprint(original)
            )
        for label, document in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(news_cache.CacheError, "NEWS_CACHE_INVALID"):
                    news_cache.validate_document(document, FIXED_NOW, registry)

    def test_cache_persistence_health_is_independent_and_recovers(self):
        registry = news_sources.load_source_registry()
        full_storage = news_cache.InMemoryCacheStorage(fail_write=True)
        full = enabled_service(cache=full_storage)
        full_health = full.health_document()
        self.assertEqual(
            full_health["schema_version"], "TRL-OFFICIAL-NEWS-HEALTH-1.2"
        )
        self.assertIn(
            "NEWS_SOURCE_INTERNAL_ERROR", full_health["stable_health_codes"]
        )
        self.assertEqual(full_health["status"], "NEWS_VALID")
        self.assertEqual(
            full_health["cache_persistence_status"], "NEWS_CACHE_WRITE_FAILED"
        )
        self.assertEqual(full_storage.write_attempt_count, 1)

        partial_transport = valid_transport(registry)
        failed_source = registry["sources"][0]
        partial_transport.responses[failed_source["exact_endpoint"]] = RetrievalError(
            "NEWS_SOURCE_TIMEOUT"
        )
        partial_storage = news_cache.InMemoryCacheStorage(fail_write=True)
        partial = enabled_service(partial_transport, cache=partial_storage)
        partial_health = partial.health_document()
        self.assertEqual(partial_health["status"], "NEWS_PARTIAL")
        self.assertEqual(
            partial_health["cache_persistence_status"], "NEWS_CACHE_WRITE_FAILED"
        )
        self.assertEqual(partial_storage.write_attempt_count, 1)
        self.assertEqual(
            partial_health["cache_persistence_diagnostic"],
            "Current in-memory news updates were not persisted and may be lost after restart.",
        )
        visible = partial.news_items_document()["items"]
        self.assertTrue(visible)
        self.assertTrue(all(
            item["operational_freshness_status"] == "NEWS_RECORD_CURRENT"
            for item in visible
        ))

        all_failed_storage = news_cache.InMemoryCacheStorage(fail_write=True)
        all_failed = enabled_service(
            FakeTransport(default=RetrievalError("NEWS_SOURCE_TIMEOUT")),
            cache=all_failed_storage,
        )
        all_failed_health = all_failed.health_document()
        self.assertEqual(all_failed_health["status"], "NEWS_ALL_SOURCES_FAILED")
        self.assertEqual(
            all_failed_health["cache_persistence_status"],
            "NEWS_CACHE_WRITE_FAILED",
        )
        self.assertEqual(all_failed_storage.write_attempt_count, 1)

        invalid_storage = news_cache.InMemoryCacheStorage(
            initial={"malformed": True}, fail_write=True
        )
        invalid_recovery = enabled_service(cache=invalid_storage)
        invalid_health = invalid_recovery.health_document()
        self.assertEqual(invalid_health["status"], "NEWS_VALID")
        self.assertEqual(
            invalid_health["cache_persistence_status"], "NEWS_CACHE_WRITE_FAILED"
        )
        self.assertEqual(invalid_storage.write_attempt_count, 1)

        for document in (
            partial_health, partial.sources_document(),
            partial.news_items_document(), partial.economic_events_document(),
        ):
            self.assertEqual(
                document["cache_persistence_status"], "NEWS_CACHE_WRITE_FAILED"
            )
            serialized = json.dumps(document)
            self.assertNotIn("Traceback", serialized)
            self.assertNotIn("LOCALAPPDATA", serialized)
            self.assertNotIn("C:\\\\", serialized)
        self.assertEqual(
            partial.news_items_document()["schema_version"],
            "TRL-OFFICIAL-NEWS-COLLECTION-1.2",
        )
        self.assertEqual(
            partial.economic_events_document()["schema_version"],
            "TRL-OFFICIAL-ECONOMIC-EVENT-COLLECTION-1.3",
        )

        first = visible[0]
        partial_storage.fail_write = False
        partial_transport.responses[failed_source["exact_endpoint"]] = response(
            failed_source
        )
        partial._clock.advance(900)
        recovered = partial.health_document()
        recovered_item = next(
            item for item in partial.news_items_document()["items"]
            if item["news_id"] == first["news_id"]
        )
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertEqual(recovered["cache_persistence_status"], "NEWS_VALID")
        self.assertEqual(partial_storage.write_attempt_count, 2)
        self.assertEqual(partial_storage.write_count, 1)
        self.assertIsNone(recovered["cache_persistence_diagnostic"])
        self.assertEqual(recovered_item["news_id"], first["news_id"])
        self.assertEqual(recovered_item["revision_number"], first["revision_number"])

    def test_invalid_production_cache_storage_is_retained_repaired_and_reloads(self):
        repository_timestamp = BASE.stat().st_mtime_ns
        cache_path = operating_system_temporary_file("trl-news-cache-repair-")
        failed_path = operating_system_temporary_file(
            "trl-news-cache-failed-repair-"
        )
        temporary_paths = (
            cache_path, cache_path.with_name(cache_path.name + ".tmp"),
            failed_path, failed_path.with_name(failed_path.name + ".tmp"),
        )
        self.assertTrue(cache_path.exists())
        self.assertTrue(failed_path.exists())
        self.assertFalse(cache_path.resolve().is_relative_to(BASE.resolve()))
        self.assertFalse(failed_path.resolve().is_relative_to(BASE.resolve()))
        try:
            cache_path.write_bytes(b'{"records":[')
            storage = CountingFileCacheStorage(cache_path)
            transport = valid_transport()
            service = OfficialNewsService(
                OfficialNewsConfiguration(True, 900),
                transport=transport,
                clock=FakeClock(),
                cache_storage=storage,
            )

            with service._lock:
                service._initialize_enabled()
                service._last_attempt = FIXED_NOW
            rejected = service.health_document()
            self.assertEqual(rejected["status"], "NEWS_CACHE_INVALID")
            self.assertEqual(
                rejected["cache_persistence_status"], "NEWS_CACHE_INVALID"
            )
            self.assertIn(
                "The local cache was rejected and was not trusted.",
                rejected["diagnostics"],
            )
            self.assertEqual(service.news_items_document()["items"], [])
            self.assertEqual(service.economic_events_document()["events"], [])
            self.assertIs(service._cache_storage, storage)
            self.assertEqual(storage.write_attempt_count, 0)
            self.assertEqual(transport.calls, [])

            with service._lock:
                service._last_attempt = None
            service.health_document()
            self.assertTrue(service.wait_for_refresh(5))
            repaired_health = service.health_document()
            self.assertEqual(repaired_health["status"], "NEWS_VALID")
            self.assertEqual(
                repaired_health["cache_persistence_status"], "NEWS_VALID"
            )
            self.assertEqual(storage.write_attempt_count, 1)
            self.assertEqual(storage.write_count, 1)
            repaired = storage.load()
            validated = news_cache.validate_document(
                repaired, FIXED_NOW, news_sources.load_source_registry()
            )
            self.assertTrue(validated["records"])

            second_storage = news_cache.FileCacheStorage(cache_path)
            second_transport = FakeTransport(
                default=RetrievalError("NEWS_SOURCE_HTTP_ERROR")
            )
            second = OfficialNewsService(
                OfficialNewsConfiguration(True, 900),
                transport=second_transport,
                clock=FakeClock(),
                cache_storage=second_storage,
            )
            with second._lock:
                second._initialize_enabled()
            self.assertEqual(second._cache, validated)
            self.assertEqual(second._cache_persistence_status, "NEWS_VALID")
            self.assertNotIn(
                "The local cache was rejected and was not trusted.",
                second._diagnostics,
            )
            self.assertEqual(second_transport.calls, [])
            first_identity = [
                (
                    wrapper["kind"], wrapper["identity"], wrapper["fingerprint"],
                    wrapper["record"]["revision_number"],
                )
                for wrapper in validated["records"]
            ]
            second_identity = [
                (
                    wrapper["kind"], wrapper["identity"], wrapper["fingerprint"],
                    wrapper["record"]["revision_number"],
                )
                for wrapper in second._cache["records"]
            ]
            self.assertEqual(second_identity, first_identity)

            failed_path.write_bytes(b'{"records":[')
            failed_storage = CountingFileCacheStorage(
                failed_path, fail_write=True
            )
            failed = enabled_service(cache=failed_storage)
            failed_health = failed.health_document()
            self.assertEqual(failed_health["status"], "NEWS_VALID")
            self.assertEqual(
                failed_health["cache_persistence_status"],
                "NEWS_CACHE_WRITE_FAILED",
            )
            self.assertEqual(failed_storage.write_attempt_count, 1)
            self.assertEqual(failed_storage.write_count, 0)
            self.assertEqual(failed_path.read_bytes(), b'{"records":[')
        finally:
            for target in (cache_path, failed_path):
                for sibling in target.parent.glob(
                    "." + target.name + ".*.tmp"
                ):
                    sibling.unlink(missing_ok=True)
            for path in temporary_paths:
                path.unlink(missing_ok=True)
        self.assertTrue(all(not path.exists() for path in temporary_paths))
        self.assertEqual(BASE.stat().st_mtime_ns, repository_timestamp)

    def test_atomic_file_writes_ignore_stale_temps_and_clean_current_failure(self):
        registry, valid_news, valid_event, _ = adversarial_cache_documents()
        document = cached_document(
            cached_wrapper(valid_news, "news"),
            cached_wrapper(valid_event, "event"),
        )
        target = operating_system_temporary_file("trl-news-atomic-target-")
        unrelated = operating_system_temporary_file("trl-news-unrelated-")
        legacy = target.with_name(target.name + ".tmp")
        stale_unique = target.with_name(
            "." + target.name + ".crash-left.tmp"
        )
        exact_paths = (target, unrelated, legacy, stale_unique)
        pattern = "." + target.name + ".*.tmp"
        before_temporaries = set()
        self.assertFalse(target.resolve().is_relative_to(BASE.resolve()))
        try:
            target.write_bytes(b"rejected old target")
            legacy.write_bytes(b"legacy stale temporary")
            stale_unique.write_bytes(b"unique stale temporary")
            unrelated.write_bytes(b"unrelated content")
            before_temporaries = set(target.parent.glob(pattern))

            storage = news_cache.FileCacheStorage(target)
            storage.write(document)
            loaded = storage.load()
            accepted = news_cache.validate_document(loaded, FIXED_NOW, registry)
            self.assertEqual(accepted, document)
            self.assertEqual(legacy.read_bytes(), b"legacy stale temporary")
            self.assertEqual(stale_unique.read_bytes(), b"unique stale temporary")
            self.assertEqual(unrelated.read_bytes(), b"unrelated content")
            after_success = set(target.parent.glob(pattern))
            self.assertEqual(after_success - before_temporaries, set())

            storage.write(document)
            self.assertEqual(storage.load(), document)
            self.assertEqual(
                set(target.parent.glob(pattern)) - before_temporaries, set()
            )

            target_before_failure = target.read_bytes()
            before_failure = set(target.parent.glob(pattern))
            with mock.patch(
                "trading_lab_app.news_cache.os.replace",
                side_effect=OSError("controlled replacement failure"),
            ), self.assertRaisesRegex(
                news_cache.CacheError, "NEWS_CACHE_WRITE_FAILED"
            ):
                storage.write(document)
            self.assertEqual(target.read_bytes(), target_before_failure)
            self.assertEqual(
                set(target.parent.glob(pattern)) - before_failure, set()
            )
            self.assertEqual(legacy.read_bytes(), b"legacy stale temporary")
            self.assertEqual(stale_unique.read_bytes(), b"unique stale temporary")
            self.assertEqual(unrelated.read_bytes(), b"unrelated content")
        finally:
            for sibling in target.parent.glob(pattern):
                if sibling == stale_unique or sibling not in before_temporaries:
                    sibling.unlink(missing_ok=True)
            for path in exact_paths:
                path.unlink(missing_ok=True)
        self.assertTrue(all(not path.exists() for path in exact_paths))
        self.assertEqual(list(target.parent.glob(pattern)), [])

    def test_storage_construction_failure_is_controlled_and_disabled_is_silent(self):
        enabled_transport = valid_transport()
        with mock.patch(
            "trading_lab_app.news_cache.production_storage",
            side_effect=news_cache.CacheError("NEWS_CACHE_INVALID"),
        ) as factory:
            service = AwaitingOfficialNewsService(
                OfficialNewsConfiguration(True, 900),
                transport=enabled_transport,
                clock=FakeClock(),
            )
            health = service.health_document()
        factory.assert_called_once_with()
        self.assertEqual(health["status"], "NEWS_VALID")
        self.assertEqual(
            health["cache_persistence_status"], "NEWS_CACHE_WRITE_FAILED"
        )
        self.assertIn(
            "The local cache storage was unavailable; persistence failed closed.",
            health["diagnostics"],
        )
        serialized = json.dumps(health)
        self.assertNotIn("LOCALAPPDATA", serialized)
        self.assertNotIn("Traceback", serialized)
        self.assertIsNone(service._cache_storage)

        disabled_transport = FakeTransport()
        with mock.patch(
            "trading_lab_app.news_cache.production_storage"
        ) as disabled_factory, mock.patch(
            "trading_lab_app.news_sources.load_source_registry"
        ) as registry_loader:
            disabled = OfficialNewsService(transport=disabled_transport)
            self.assertEqual(disabled.health_document()["status"], "NEWS_DISABLED")
            self.assertEqual(disabled.news_items_document()["items"], [])
            self.assertEqual(disabled.economic_events_document()["events"], [])
        disabled_factory.assert_not_called()
        registry_loader.assert_not_called()
        self.assertEqual(disabled_transport.calls, [])
        self.assertIsNone(disabled._cache_storage)

    def test_oversized_source_row_is_transactionally_isolated_and_recovers(self):
        registry = news_sources.load_source_registry()
        bea = next(
            source for source in registry["sources"]
            if source["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        fed = registry["sources"][0]
        clock = FakeClock()
        forbidden = "x" * (news_data.MAX_TEXT_LENGTH + 1)
        storage = InspectingCacheStorage(forbidden)
        transport = valid_transport(registry)
        service = enabled_service(transport, clock, storage)
        self.assertEqual(service.health_document()["status"], "NEWS_VALID")
        trusted_event = service.economic_events_document()["events"][0]
        trusted_id = trusted_event["event_id"]
        trusted_revision = trusted_event["revision_number"]
        trusted_count = len(service._cache["records"])

        oversized = json.dumps({"release_dates": [{
            "ReleaseDate": "2026-07-30",
            "ReleaseName": "Gross Domestic Product",
            "ReleaseURL": "https://www.bea.gov/news/example",
            "actual": forbidden,
        }]}, separators=(",", ":")).encode("utf-8")
        transport.responses[bea["exact_endpoint"]] = response(bea, body=oversized)
        transport.responses[fed["exact_endpoint"]] = response(
            fed,
            body=RSS_BODY.replace(
                b"Official &amp; governed release", b"Independent valid update"
            ),
        )
        clock.advance(900)
        partial = service.health_document()
        bea_health = next(
            item for item in partial["source_health"]
            if item["source_id"] == bea["source_id"]
        )
        retained = next(
            event for event in service.economic_events_document()["events"]
            if event["event_id"] == trusted_id
        )
        updated_fed = next(
            item for item in service.news_items_document()["items"]
            if item["source_id"] == fed["source_id"]
        )
        self.assertEqual(partial["status"], "NEWS_PARTIAL")
        self.assertEqual(bea_health["status"], "NEWS_SOURCE_SCHEMA_INVALID")
        self.assertEqual(retained["operational_freshness_status"], "NEWS_RECORD_STALE")
        self.assertEqual(retained["revision_number"], trusted_revision)
        self.assertEqual(updated_fed["title"], "Independent valid update")
        self.assertGreaterEqual(len(service._cache["records"]), trusted_count)
        self.assertNotEqual(service._cache["records"], [])
        self.assertEqual(storage.invalid_candidate_writes, 0)
        self.assertEqual(storage.write_attempt_count, 2)

        httpd = server.create_server(0, official_news_service=service)
        thread = threading.Thread(
            target=httpd.serve_forever, name="test-oversized-row-server"
        )
        thread.start()
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1", httpd.server_address[1], timeout=5
            )
            connection.request("GET", "/api/news-health")
            reply = connection.getresponse()
            self.assertEqual(reply.status, 200)
            self.assertEqual(json.loads(reply.read())["status"], "NEWS_PARTIAL")
            connection.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive())

        transport.responses[bea["exact_endpoint"]] = response(bea)
        clock.advance(900)
        recovered = service.health_document()
        recovered_event = next(
            event for event in service.economic_events_document()["events"]
            if event["event_id"] == trusted_id
        )
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertEqual(
            recovered_event["operational_freshness_status"], "NEWS_RECORD_CURRENT"
        )
        self.assertEqual(recovered_event["revision_number"], trusted_revision)
        self.assertFalse(recovered["refreshing"])

    def test_final_candidate_failure_rolls_back_without_write_or_empty_replacement(self):
        clock = FakeClock()
        storage = news_cache.InMemoryCacheStorage()
        service = enabled_service(clock=clock, cache=storage)
        self.assertEqual(service.health_document()["status"], "NEWS_VALID")
        trusted_cache = copy.deepcopy(service._cache)
        trusted_items = service.news_items_document()["items"]
        attempts_before = storage.write_attempt_count

        clock.advance(900)
        with mock.patch.object(
            news_cache,
            "prune_document",
            side_effect=news_cache.CacheError("NEWS_CACHE_INVALID"),
        ):
            failed = service.health_document()
        self.assertEqual(failed["status"], "NEWS_CACHE_INVALID")
        self.assertFalse(failed["refreshing"])
        self.assertEqual(service._cache, trusted_cache)
        self.assertNotEqual(service._cache["records"], [])
        self.assertEqual(storage.write_attempt_count, attempts_before)
        self.assertEqual(storage.value, trusted_cache)

        httpd = server.create_server(0, official_news_service=service)
        thread = threading.Thread(
            target=httpd.serve_forever, name="test-candidate-rollback-server"
        )
        thread.start()
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1", httpd.server_address[1], timeout=5
            )
            connection.request("GET", "/api/news-health")
            reply = connection.getresponse()
            self.assertEqual(reply.status, 200)
            reply.read()
            connection.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive())

        clock.advance(900)
        recovered = service.health_document()
        recovered_items = service.news_items_document()["items"]
        before_identity = {
            item["news_id"]: item["revision_number"] for item in trusted_items
        }
        after_identity = {
            item["news_id"]: item["revision_number"] for item in recovered_items
        }
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertEqual(before_identity, after_identity)
        self.assertFalse(recovered["refreshing"])

    def test_per_source_record_freshness_partial_failure_throttle_and_recovery(self):
        registry = news_sources.load_source_registry()
        fed = registry["sources"][0]
        bls = registry["sources"][1]
        bea = next(
            item for item in registry["sources"]
            if item["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        clock = FakeClock()
        transport = valid_transport(registry)
        service = enabled_service(transport, clock)

        first_health = service.health_document()
        self.assertEqual(first_health["status"], "NEWS_VALID")
        self.assertFalse(first_health["refreshing"])
        first_fed = next(
            item for item in service.news_items_document()["items"]
            if item["source_id"] == fed["source_id"]
        )
        first_event = service.economic_events_document()["events"][0]
        self.assertEqual(first_fed["schema_version"], "TRL-OFFICIAL-NEWS-ITEM-1.3")
        self.assertEqual(
            first_event["schema_version"], "TRL-OFFICIAL-ECONOMIC-EVENT-1.3"
        )
        self.assertEqual(first_fed["operational_freshness_status"], "NEWS_RECORD_CURRENT")
        self.assertIsNone(first_fed["latest_source_failure_reason"])

        transport.responses[fed["exact_endpoint"]] = RetrievalError("NEWS_SOURCE_TIMEOUT")
        clock.advance(900)
        partial_health = service.health_document()
        self.assertEqual(partial_health["status"], "NEWS_PARTIAL")
        self.assertEqual(partial_health["cache_freshness_status"], "NEWS_SOURCE_STALE")
        self.assertFalse(partial_health["refreshing"])
        partial_items = service.news_items_document()["items"]
        stale_fed = next(item for item in partial_items if item["source_id"] == fed["source_id"])
        current_bls = next(item for item in partial_items if item["source_id"] == bls["source_id"])
        self.assertEqual(stale_fed["operational_freshness_status"], "NEWS_RECORD_STALE")
        self.assertEqual(stale_fed["latest_source_status"], "NEWS_SOURCE_TIMEOUT")
        self.assertEqual(stale_fed["latest_source_failure_reason"], "NEWS_SOURCE_TIMEOUT")
        self.assertEqual(
            stale_fed["last_successfully_observed_timestamp_utc"],
            "2026-07-27T12:00:00Z",
        )
        self.assertEqual(
            stale_fed["latest_source_attempt_timestamp_utc"],
            "2026-07-27T12:15:00Z",
        )
        self.assertEqual(current_bls["operational_freshness_status"], "NEWS_RECORD_CURRENT")
        self.assertIsNone(current_bls["latest_source_failure_reason"])
        self.assertEqual(stale_fed["news_id"], first_fed["news_id"])
        self.assertEqual(stale_fed["revision_number"], first_fed["revision_number"])
        self.assertEqual(
            news_data.observation_fingerprint(stale_fed),
            news_data.observation_fingerprint(first_fed),
        )

        throttled = service.health_document()
        self.assertEqual(throttled["reason_code"], "NEWS_RATE_LIMITED_LOCALLY")
        still_stale = next(
            item for item in service.news_items_document()["items"]
            if item["source_id"] == fed["source_id"]
        )
        self.assertEqual(still_stale["operational_freshness_status"], "NEWS_RECORD_STALE")

        transport.responses[fed["exact_endpoint"]] = response(fed)
        clock.advance(900)
        recovered_health = service.health_document()
        recovered_fed = next(
            item for item in service.news_items_document()["items"]
            if item["source_id"] == fed["source_id"]
        )
        self.assertEqual(recovered_health["status"], "NEWS_VALID")
        self.assertEqual(recovered_health["cache_freshness_status"], "NEWS_VALID")
        self.assertEqual(recovered_fed["operational_freshness_status"], "NEWS_RECORD_CURRENT")
        self.assertIsNone(recovered_fed["latest_source_failure_reason"])
        self.assertEqual(recovered_fed["news_id"], first_fed["news_id"])
        self.assertEqual(recovered_fed["revision_number"], first_fed["revision_number"])

        transport.responses[bea["exact_endpoint"]] = RetrievalError("NEWS_SOURCE_HTTP_ERROR")
        clock.advance(900)
        event_partial = service.health_document()
        stale_event = service.economic_events_document()["events"][0]
        self.assertEqual(event_partial["status"], "NEWS_PARTIAL")
        self.assertEqual(event_partial["cache_freshness_status"], "NEWS_SOURCE_STALE")
        self.assertEqual(stale_event["operational_freshness_status"], "NEWS_RECORD_STALE")
        self.assertEqual(stale_event["latest_source_failure_reason"], "NEWS_SOURCE_HTTP_ERROR")
        self.assertEqual(stale_event["event_id"], first_event["event_id"])
        self.assertEqual(stale_event["revision_number"], first_event["revision_number"])

    def test_partial_failure_without_retained_records_does_not_claim_stale_cache(self):
        registry = news_sources.load_source_registry()
        failed_source = registry["sources"][0]
        transport = valid_transport(registry)
        transport.responses[failed_source["exact_endpoint"]] = RetrievalError(
            "NEWS_SOURCE_TIMEOUT"
        )
        service = enabled_service(transport)
        health = service.health_document()
        records = service.news_items_document()["items"]
        self.assertEqual(health["status"], "NEWS_PARTIAL")
        self.assertEqual(health["cache_freshness_status"], "NEWS_VALID")
        self.assertFalse(any(
            item["source_id"] == failed_source["source_id"] for item in records
        ))
        self.assertTrue(all(
            item["operational_freshness_status"] == "NEWS_RECORD_CURRENT"
            for item in records
        ))

    def test_deep_json_and_unexpected_worker_failure_are_isolated_and_recoverable(self):
        registry = news_sources.load_source_registry()
        bea = next(
            item for item in registry["sources"]
            if item["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        clock = FakeClock()
        transport = valid_transport(registry)
        depth = 2000
        deep = b'{"release_dates":' + b"[" * depth + b"0" + b"]" * depth + b"}"
        transport.responses[bea["exact_endpoint"]] = response(bea, body=deep)
        service = enabled_service(transport, clock)
        failed = service.health_document()
        failed_bea = next(
            item for item in failed["source_health"] if item["source_id"] == bea["source_id"]
        )
        self.assertEqual(failed["status"], "NEWS_PARTIAL")
        self.assertEqual(failed_bea["reason_code"], "NEWS_SOURCE_SCHEMA_INVALID")
        self.assertFalse(failed["refreshing"])
        self.assertEqual(failed["network_request_count"], 6)

        transport.responses[bea["exact_endpoint"]] = response(bea)
        clock.advance(900)
        recovered = service.health_document()
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertFalse(recovered["refreshing"])
        self.assertEqual(recovered["network_request_count"], 12)

        exploding = valid_transport(registry)
        exploding.responses[bea["exact_endpoint"]] = RuntimeError("must not escape")
        unexpected = enabled_service(exploding).health_document()
        unexpected_bea = next(
            item for item in unexpected["source_health"]
            if item["source_id"] == bea["source_id"]
        )
        self.assertEqual(unexpected["status"], "NEWS_PARTIAL")
        self.assertEqual(unexpected_bea["reason_code"], "NEWS_SOURCE_SCHEMA_INVALID")
        self.assertFalse(unexpected["refreshing"])
        self.assertNotIn("must not escape", json.dumps(unexpected))

        executor_clock = FakeClock()
        executor_service = enabled_service(valid_transport(registry), executor_clock)
        with mock.patch(
            "trading_lab_app.news_service.ThreadPoolExecutor",
            side_effect=RuntimeError("executor detail must not escape"),
        ):
            executor_failed = executor_service.health_document()
        self.assertEqual(executor_failed["status"], "NEWS_ALL_SOURCES_FAILED")
        self.assertFalse(executor_failed["refreshing"])
        self.assertNotIn("executor detail", json.dumps(executor_failed))
        executor_clock.advance(900)
        executor_recovered = executor_service.health_document()
        self.assertEqual(executor_recovered["status"], "NEWS_VALID")
        self.assertFalse(executor_recovered["refreshing"])

    def test_fallback_identity_distinguishes_stories_without_using_retrieval_time(self):
        source = news_sources.load_source_registry()["sources"][0]
        different_titles = b"""<rss><channel>
        <item><title>One</title></item><item><title>Two</title></item>
        </channel></rss>"""
        items = news_parser.parse_xml_news(
            different_titles, source, "2026-07-27T12:00:00Z"
        )
        self.assertEqual([item["title"] for item in items], ["One", "Two"])
        self.assertEqual(len({item["news_id"] for item in items}), 2)
        self.assertTrue(all(
            item["source_url_availability_status"] == "SOURCE_ENDPOINT_FALLBACK"
            for item in items
        ))

        ungoverned = b"""<rss><channel>
        <item><title>One</title><link>https://example.invalid/one</link></item>
        <item><title>Two</title><link>https://example.invalid/two</link></item>
        </channel></rss>"""
        ungoverned_items = news_parser.parse_xml_news(
            ungoverned, source, "2026-07-27T12:00:00Z"
        )
        self.assertEqual(len({item["news_id"] for item in ungoverned_items}), 2)
        self.assertTrue(all(
            item["source_url_reason_code"] == "SOURCE_ITEM_LINK_HOST_NOT_GOVERNED"
            for item in ungoverned_items
        ))

        timestamped = b"""<rss><channel>
        <item><title>Same</title><pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate></item>
        <item><title>Same</title><pubDate>Mon, 27 Jul 2026 11:00:00 GMT</pubDate></item>
        </channel></rss>"""
        timestamped_items = news_parser.parse_xml_news(
            timestamped, source, "2026-07-27T12:00:00Z"
        )
        self.assertEqual(len({item["news_id"] for item in timestamped_items}), 2)

        repeated_a = news_parser.parse_xml_news(
            different_titles, source, "2026-07-27T12:00:00Z"
        )
        repeated_b = news_parser.parse_xml_news(
            different_titles, source, "2026-07-28T12:00:00Z"
        )
        self.assertEqual(
            [item["news_id"] for item in repeated_a],
            [item["news_id"] for item in repeated_b],
        )
        valid = news_parser.parse_xml_news(RSS_BODY, source, "2026-07-27T12:00:00Z")[0]
        self.assertEqual(
            valid["news_id"],
            news_data.stable_identifier("NEWS", (source["source_id"], valid["source_url"])),
        )
        self.assertEqual(valid["news_id"], "NEWS-014A97670421C5F2758F384B")

        ambiguous = news_parser.parse_xml_news(
            b"<rss><channel><item><title>Same</title></item><item><title>Same</title></item></channel></rss>",
            source, "2026-07-27T12:00:00Z",
        )
        self.assertEqual(ambiguous[0]["news_id"], ambiguous[1]["news_id"])
        self.assertEqual(
            ambiguous[0]["identity_ambiguity_reason"],
            "SOURCE_IDENTITY_AMBIGUOUS_WITHOUT_LINK_OR_TIMESTAMP",
        )

        registry = news_sources.load_source_registry()
        transport = valid_transport(registry)
        transport.responses[source["exact_endpoint"]] = response(source, body=different_titles)
        clock = FakeClock()
        service = enabled_service(transport, clock)
        merged = [
            item for item in service.news_items_document()["items"]
            if item["source_id"] == source["source_id"]
        ]
        self.assertEqual([item["title"] for item in merged], ["Two", "One"])
        self.assertEqual(len({item["news_id"] for item in merged}), 2)
        clock.advance(900)
        repeated = [
            item for item in service.news_items_document()["items"]
            if item["source_id"] == source["source_id"]
        ]
        self.assertEqual(
            [item["news_id"] for item in repeated],
            [item["news_id"] for item in merged],
        )
        self.assertEqual([item["revision_number"] for item in repeated], [1, 1])

    def test_duplicate_fallback_batch_is_rejected_transactionally_and_recovers(self):
        registry = news_sources.load_source_registry()
        source = registry["sources"][0]
        clock = FakeClock()
        storage = InspectingCacheStorage("Ambiguous duplicate")
        transport = valid_transport(registry)
        service = enabled_service(transport, clock, storage)
        initial = service.health_document()
        trusted = next(
            item for item in service.news_items_document()["items"]
            if item["source_id"] == source["source_id"]
        )
        writes_before = storage.write_attempt_count
        self.assertEqual(initial["status"], "NEWS_VALID")

        duplicate_body = b"""<rss><channel>
        <item><title>Ambiguous duplicate</title><pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate></item>
        <item><title>Ambiguous duplicate</title><pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        transport.responses[source["exact_endpoint"]] = response(
            source, body=duplicate_body
        )
        clock.advance(900)
        partial = service.health_document()
        source_health = next(
            item for item in partial["source_health"]
            if item["source_id"] == source["source_id"]
        )
        retained = next(
            item for item in service.news_items_document()["items"]
            if item["news_id"] == trusted["news_id"]
        )
        self.assertEqual(partial["status"], "NEWS_PARTIAL")
        self.assertEqual(source_health["status"], "NEWS_SOURCE_SCHEMA_INVALID")
        self.assertEqual(retained["operational_freshness_status"], "NEWS_RECORD_STALE")
        self.assertEqual(retained["revision_number"], trusted["revision_number"])
        self.assertEqual(storage.invalid_candidate_writes, 0)
        self.assertEqual(storage.write_attempt_count, writes_before + 1)
        self.assertNotIn(
            "Ambiguous duplicate", json.dumps(storage.value, ensure_ascii=False)
        )

        transport.responses[source["exact_endpoint"]] = response(source)
        clock.advance(900)
        recovered = service.health_document()
        recovered_record = next(
            item for item in service.news_items_document()["items"]
            if item["news_id"] == trusted["news_id"]
        )
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertEqual(
            recovered_record["operational_freshness_status"],
            "NEWS_RECORD_CURRENT",
        )
        self.assertEqual(recovered_record["news_id"], trusted["news_id"])
        self.assertEqual(
            recovered_record["revision_number"], trusted["revision_number"]
        )
        self.assertFalse(recovered["refreshing"])

    def test_distinct_governed_bea_links_have_distinct_ids_and_survive_merge(self):
        registry = news_sources.load_source_registry()
        source = next(item for item in registry["sources"] if item["source_id"] == "BEA_NEWS_RELEASE_RSS")
        body = b"""<rss><channel>
        <item><title>BEA release one</title><link>https://www.bea.gov/news/2026/release-one</link><pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate></item>
        <item><title>BEA release two</title><link>https://www.bea.gov/news/2026/release-two</link><pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        parsed = news_parser.parse_xml_news(body, source, "2026-07-27T12:00:00Z")
        self.assertEqual([item["source_url"] for item in parsed], [
            "https://www.bea.gov/news/2026/release-one",
            "https://www.bea.gov/news/2026/release-two",
        ])
        self.assertEqual(len({item["news_id"] for item in parsed}), 2)
        self.assertTrue(all(
            item["source_url_availability_status"] == "GOVERNED_ITEM_LINK_AVAILABLE"
            for item in parsed
        ))
        transport = valid_transport(registry)
        transport.responses[source["exact_endpoint"]] = response(source, body=body)
        service = enabled_service(transport)
        merged = [
            item for item in service.news_items_document()["items"]
            if item["source_id"] == source["source_id"]
        ]
        self.assertEqual(len(merged), 2)
        self.assertEqual(len({item["news_id"] for item in merged}), 2)

    def test_deterministic_ids_dedup_source_separation_and_revision(self):
        registry = news_sources.load_source_registry()
        clock = FakeClock()
        transport = valid_transport(registry)
        service = enabled_service(transport, clock)
        first = service.news_items_document()["items"]
        self.assertEqual(len(first), 5)
        ids = [item["news_id"] for item in first]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(first, service.news_items_document()["items"])
        fed = registry["sources"][0]
        bea = next(item for item in registry["sources"] if item["source_id"] == "BEA_RELEASE_DATES_JSON")
        changed = RSS_BODY.replace(b"Official &amp; governed release", b"Official revised release")
        transport.responses[fed["exact_endpoint"]] = response(fed, body=changed)
        transport.responses[bea["exact_endpoint"]] = response(
            bea, body=BEA_BODY.replace(b"2026-07-30", b"2026-07-31")
        )
        clock.advance(901)
        revised = service.news_items_document()["items"]
        selected = next(item for item in revised if item["source_id"] == fed["source_id"])
        self.assertEqual(selected["revision_number"], 2)
        self.assertEqual(selected["title"], "Official revised release")
        self.assertEqual(len(revised), 5)
        events = service.economic_events_document()["events"]
        self.assertEqual(
            [event["scheduled_timestamp_utc"] for event in events],
            ["2026-07-30T00:00:00Z", "2026-07-31T00:00:00Z"],
        )
        self.assertEqual([event["revision_number"] for event in events], [1, 1])
        self.assertEqual(events[0]["event_series_id"], events[1]["event_series_id"])
        self.assertNotEqual(events[0]["event_id"], events[1]["event_id"])

    def test_partial_success_all_failure_and_stale_cache_are_distinct(self):
        registry = news_sources.load_source_registry()
        partial = valid_transport(registry)
        first_source = registry["sources"][0]
        partial.responses[first_source["exact_endpoint"]] = RetrievalError("NEWS_SOURCE_TIMEOUT")
        partial_health = enabled_service(partial).health_document()
        self.assertEqual(partial_health["status"], "NEWS_PARTIAL")
        self.assertEqual(partial_health["network_request_count"], 6)
        self.assertEqual(
            next(item for item in partial_health["source_health"] if item["source_id"] == first_source["source_id"])["status"],
            "NEWS_SOURCE_TIMEOUT",
        )
        all_failed = FakeTransport(default=RetrievalError("NEWS_SOURCE_HTTP_ERROR"))
        service = enabled_service(all_failed)
        self.assertEqual(service.health_document()["status"], "NEWS_ALL_SOURCES_FAILED")
        self.assertEqual(service.health_document()["cache_freshness_status"], "NEWS_ENABLED_NO_DATA")
        retained = news_cache.InMemoryCacheStorage()
        enabled_service(cache=retained).health_document()
        stale = enabled_service(all_failed, cache=retained).health_document()
        self.assertEqual(stale["status"], "NEWS_ALL_SOURCES_FAILED")
        self.assertEqual(stale["cache_freshness_status"], "NEWS_SOURCE_STALE")
        stale_service = enabled_service(all_failed, cache=retained)
        stale_service.health_document()
        retained_records = (
            stale_service.news_items_document()["items"]
            + stale_service.economic_events_document()["events"]
        )
        self.assertTrue(retained_records)
        self.assertTrue(all(
            item["operational_freshness_status"] == "NEWS_RECORD_STALE"
            for item in retained_records
        ))

    def test_local_refresh_throttling_and_fake_clock(self):
        clock = FakeClock()
        transport = valid_transport()
        service = enabled_service(transport, clock)
        first = service.health_document()
        self.assertEqual(len(transport.calls), 6)
        self.assertEqual(first["network_request_count"], 6)
        second = service.health_document()
        self.assertEqual(len(transport.calls), 6)
        self.assertEqual(second["network_request_count"], 6)
        self.assertEqual(second["reason_code"], "NEWS_RATE_LIMITED_LOCALLY")
        self.assertEqual(first["next_permitted_refresh_utc"], "2026-07-27T12:15:00Z")
        self.assertEqual(service.sources_document()["status"], "NEWS_VALID")
        service.news_items_document()
        service.economic_events_document()
        self.assertEqual(service.health_document()["network_request_count"], 6)
        clock.advance(900)
        refreshed = service.health_document()
        self.assertEqual(len(transport.calls), 12)
        self.assertEqual(refreshed["network_request_count"], 12)

    def test_coordinator_start_failure_clears_reference_and_recovers(self):
        clock = FakeClock()
        transport = valid_transport()
        service = enabled_service(
            transport=transport,
            clock=clock,
            cache=news_cache.InMemoryCacheStorage(),
            asynchronous=True,
        )
        with mock.patch(
            "trading_lab_app.news_service.threading.Thread.start",
            side_effect=RuntimeError("controlled coordinator start failure"),
        ):
            failed = service.health_document()
        self.assertEqual(failed["status"], "NEWS_ALL_SOURCES_FAILED")
        self.assertFalse(failed["refreshing"])
        self.assertIsNone(service._refresh_thread)
        self.assertIsNone(service._refresh_owner)
        self.assertEqual(service._cache["records"], [])
        self.assertEqual(transport.calls, [])
        self.assertTrue(service.shutdown())
        self.assertTrue(service.shutdown())

        recovery_clock = FakeClock()
        recovery_transport = valid_transport()
        recovery_service = enabled_service(
            transport=recovery_transport,
            clock=recovery_clock,
            cache=news_cache.InMemoryCacheStorage(),
            asynchronous=True,
        )
        with mock.patch(
            "trading_lab_app.news_service.threading.Thread.start",
            side_effect=RuntimeError("controlled coordinator start failure"),
        ):
            recovery_service.health_document()
        recovery_clock.advance(900)
        recovering = recovery_service.health_document()
        self.assertTrue(recovering["refreshing"])
        self.assertTrue(recovery_service.wait_for_refresh(5))
        recovered = recovery_service.health_document()
        self.assertEqual(recovered["status"], "NEWS_VALID")
        self.assertFalse(recovered["refreshing"])
        self.assertIsNone(recovery_service._refresh_owner)
        self.assertIsNone(recovery_service._refresh_thread)
        self.assertEqual(len(recovery_transport.calls), NEWS_REFRESH_WORKERS)
        self.assertTrue(recovery_service.shutdown())

    def test_persistence_phase_is_nonblocking_and_refresh_owner_safe(self):
        for fail_write in (False, True):
            with self.subTest(fail_write=fail_write):
                registry = news_sources.load_source_registry()
                transport = valid_transport(registry)
                storage = GateCacheStorage(fail_write=fail_write)
                service = enabled_service(
                    transport=transport,
                    cache=storage,
                    asynchronous=True,
                )
                initial = service.health_document()
                self.assertTrue(initial["refreshing"])
                self.assertTrue(storage.write_started.wait(3))
                with service._lock:
                    owner = service._refresh_owner
                    accepted_snapshot = copy.deepcopy(service._cache)
                self.assertIsNotNone(owner)
                self.assertTrue(accepted_snapshot["records"])

                lock_available = service._lock.acquire(blocking=False)
                self.assertTrue(lock_available)
                if lock_available:
                    service._lock.release()
                started = time.monotonic()
                visible = service.news_items_document()
                self.assertLess(time.monotonic() - started, 0.5)
                self.assertTrue(visible["refreshing"])
                self.assertTrue(visible["items"])
                self.assertEqual(len(transport.calls), NEWS_REFRESH_WORKERS)
                with service._lock:
                    self.assertEqual(service._cache, accepted_snapshot)
                    self.assertEqual(service._refresh_owner, owner)

                storage.release_write.set()
                self.assertTrue(service.wait_for_refresh(3))
                final = service.health_document()
                expected_persistence = (
                    "NEWS_CACHE_WRITE_FAILED" if fail_write else "NEWS_VALID"
                )
                self.assertEqual(
                    final["cache_persistence_status"], expected_persistence,
                )
                self.assertFalse(final["refreshing"])
                self.assertIsNone(service._refresh_owner)
                self.assertEqual(service._cache, accepted_snapshot)
                self.assertEqual(len(transport.calls), NEWS_REFRESH_WORKERS)
                self.assertTrue(service.shutdown())

    def test_refresh_is_bounded_concurrent_and_completion_order_is_deterministic(self):
        registry = news_sources.load_source_registry()
        responses = {
            source["exact_endpoint"]: response(source) for source in registry["sources"]
        }
        gated = ConcurrentGateTransport(responses)
        service = enabled_service(gated)
        result = {}

        def refresh():
            result["health"] = service.health_document()

        thread = threading.Thread(target=refresh, name="test-news-refresh")
        thread.start()
        self.assertTrue(gated.more_than_one_active.wait(timeout=3))
        self.assertTrue(gated.all_workers_active.wait(timeout=3))
        self.assertLessEqual(gated.maximum_active, NEWS_REFRESH_WORKERS)
        gated.release.set()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result["health"]["network_request_count"], 6)
        self.assertGreater(gated.maximum_active, 1)
        self.assertEqual(gated.maximum_active, NEWS_REFRESH_WORKERS)

        source_ids = [source["source_id"] for source in registry["sources"]]
        documents = []
        for order in (source_ids, list(reversed(source_ids))):
            ordered = CompletionOrderTransport(responses, order)
            ordered_service = enabled_service(ordered)
            ordered_service.health_document()
            documents.append(server.deterministic_json_bytes({
                "news": ordered_service.news_items_document(),
                "events": ordered_service.economic_events_document(),
            }))
        self.assertEqual(documents[0], documents[1])

    def test_cache_retention_corruption_and_write_failure(self):
        source = news_sources.load_source_registry()["sources"][0]
        record = news_data.news_item(
            source, "Old", source["exact_endpoint"], "2026-06-01T00:00:00Z", "2026-06-01T00:00:00Z",
        )
        wrapper = {
            "kind": "news", "identity": record["news_id"],
            "fingerprint": news_data.observation_fingerprint(record),
            "first_seen_timestamp_utc": "2026-06-01T00:00:00Z",
            "last_seen_timestamp_utc": "2026-06-01T00:00:00Z", "record": record,
        }
        document = news_cache.empty_document("2026-07-27T12:00:00Z")
        document["records"] = [wrapper]
        registry = news_sources.load_source_registry()
        self.assertEqual(
            news_cache.validate_document(document, FIXED_NOW, registry)["records"], []
        )
        incompatible = copy.deepcopy(document)
        incompatible["records"][0]["record"]["schema_version"] = (
            "TRL-OFFICIAL-NEWS-ITEM-1.2"
        )
        incompatible["records"][0]["fingerprint"] = news_data.observation_fingerprint(
            incompatible["records"][0]["record"]
        )
        with self.assertRaisesRegex(news_cache.CacheError, "NEWS_CACHE_INVALID"):
            news_cache.validate_document(
                incompatible, datetime(2026, 6, 2, tzinfo=timezone.utc), registry
            )
        corrupt = news_cache.InMemoryCacheStorage(initial={"bad": True})
        health = enabled_service(cache=corrupt).health_document()
        self.assertIn("The local cache was rejected and was not trusted.", health["diagnostics"])
        failed_write = news_cache.InMemoryCacheStorage(fail_write=True)
        failed_write_health = enabled_service(cache=failed_write).health_document()
        self.assertEqual(failed_write_health["status"], "NEWS_VALID")
        self.assertEqual(
            failed_write_health["cache_persistence_status"],
            "NEWS_CACHE_WRITE_FAILED",
        )
        self.assertFalse(failed_write_health["refreshing"])
        with self.assertRaisesRegex(news_cache.CacheError, "NEWS_CACHE_INVALID"):
            news_cache.deterministic_bytes({"nonfinite": float("nan")})
        circular = []
        circular.append(circular)
        with self.assertRaisesRegex(news_cache.CacheError, "NEWS_CACHE_INVALID"):
            news_cache.deterministic_bytes(circular)

    def test_cache_count_size_and_deterministic_pruning(self):
        registry = news_sources.load_source_registry()
        responses = {}
        for source in registry["sources"]:
            if source["format"] == "JSON":
                rows = [{"ReleaseDate": "2026-08-{:02d}".format((i % 28) + 1), "ReleaseName": "Event {}".format(i), "ReleaseURL": "https://www.bea.gov/event/{}".format(i)} for i in range(200)]
                responses[source["exact_endpoint"]] = response(source, body=json.dumps({"release_dates": rows}).encode("utf-8"))
            else:
                rows = "".join("<item><title>Item {0}</title><link>https://{1}/item/{0}</link><pubDate>Mon, 27 Jul 2026 10:00:00 GMT</pubDate></item>".format(i, source["permitted_item_link_hostnames"][0]) for i in range(200))
                responses[source["exact_endpoint"]] = response(source, body=("<rss><channel>" + rows + "</channel></rss>").encode("utf-8"))
        caches = []
        for _ in range(2):
            storage = news_cache.InMemoryCacheStorage()
            enabled_service(FakeTransport(responses), cache=storage).health_document()
            caches.append(storage.value)
        self.assertEqual(caches[0], caches[1])
        self.assertEqual(len(caches[0]["records"]), 1000)
        self.assertLessEqual(len(news_cache.deterministic_bytes(caches[0])), news_cache.MAX_CACHE_BYTES)

    def test_no_personal_credentials_mt5_or_strategy_surface(self):
        transport = valid_transport()
        market_service = mock.Mock()
        service = enabled_service(transport)
        for document in (
            service.health_document(), service.sources_document(),
            service.news_items_document(), service.economic_events_document(),
        ):
            text = json.dumps(document).lower()
            for forbidden in ("password", "account_number", '"api_key":', "strategy_id", "signal", "order_id", "mt5_tick"):
                self.assertNotIn(forbidden, text)
        market_service.snapshot_document.assert_not_called()
        self.assertEqual(set(server.NEWS_API_ROUTES), {
            "/api/news-health", "/api/news-sources", "/api/news-items", "/api/economic-events",
        })

    def test_offline_validation_leaves_no_repository_or_temporary_artifacts(self):
        forbidden = []
        for path in BASE.rglob("*"):
            lowered = path.name.lower()
            if path.is_dir() and lowered in {"__pycache__", ".pytest_cache", ".mypy_cache"}:
                forbidden.append(path)
            if path.is_file() and (
                path.suffix.lower() in {".pyc", ".pyo", ".tmp", ".bak"}
                or lowered.startswith("cache-v1.json")
            ):
                forbidden.append(path)
        self.assertEqual(forbidden, [])


class ApiCliAndDashboardTests(unittest.TestCase):
    def request(self, httpd, method, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=10)
        connection.request(method, path, headers=headers or {})
        response_value = connection.getresponse()
        body = response_value.read()
        result = response_value.status, dict(response_value.getheaders()), body
        connection.close()
        return result

    def raw_response(self, reader):
        status_line = reader.readline()
        self.assertTrue(status_line.startswith(b"HTTP/"), status_line)
        status = int(status_line.split()[1])
        headers = {}
        while True:
            line = reader.readline()
            if line == b"\r\n":
                break
            self.assertTrue(line, "response headers ended unexpectedly")
            name, value = line.decode("iso-8859-1").split(":", 1)
            headers[name.lower()] = value.strip()
        body = reader.read(int(headers.get("content-length", "0")))
        return status, headers, body

    def test_cli_is_explicit_and_refresh_is_bounded(self):
        parser = app.build_parser()
        self.assertFalse(parser.parse_args([]).enable_official_news)
        self.assertEqual(parser.parse_args(["--enable-official-news"]).official_news_refresh_seconds, None)
        self.assertEqual(parser.parse_args(["--enable-official-news", "--official-news-refresh-seconds", "300"]).official_news_refresh_seconds, 300)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--official-news-refresh-seconds", "299"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["--official-news-refresh-seconds", "3601"])
        self.assertEqual(app.main(["--official-news-refresh-seconds", "900"]), 2)

    def test_nonfinite_cache_constants_recover_without_http_500(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                storage = InvalidJsonCacheStorage(
                    ('{"schema_version":"x","value":' + constant + '}').encode("ascii")
                )
                transport = valid_transport()
                service = enabled_service(transport=transport, cache=storage)
                httpd = server.create_server(0, official_news_service=service)
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                try:
                    status, _, body = self.request(httpd, "GET", "/api/news-health")
                finally:
                    httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)
                self.assertEqual(status, 200)
                health = json.loads(body)
                self.assertEqual(health["status"], "NEWS_VALID")
                self.assertEqual(health["cache_persistence_status"], "NEWS_VALID")
                self.assertIn(
                    "The local cache was rejected and was not trusted.",
                    health["diagnostics"],
                )
                self.assertEqual(health["network_request_count"], 6)
                self.assertEqual(storage.load_count, 1)
                self.assertEqual(len(transport.calls), 6)

    def test_every_adversarial_cache_fails_closed_with_http_200_and_no_transport(self):
        _, _, _, cases = adversarial_cache_documents()
        for label, document in cases:
            with self.subTest(label=label):
                storage = news_cache.InMemoryCacheStorage(initial=document)
                transport = FakeTransport(
                    default=RetrievalError("NEWS_SOURCE_HTTP_ERROR")
                )
                service = enabled_service(transport=transport, cache=storage)
                with service._lock:
                    service._initialize_enabled()
                    service._last_attempt = FIXED_NOW
                httpd = server.create_server(0, official_news_service=service)
                thread = threading.Thread(
                    target=httpd.serve_forever,
                    name="test-adversarial-cache-server",
                )
                thread.start()
                try:
                    health_status, _, health_body = self.request(
                        httpd, "GET", "/api/news-health"
                    )
                    items_status, _, items_body = self.request(
                        httpd, "GET", "/api/news-items"
                    )
                    events_status, _, events_body = self.request(
                        httpd, "GET", "/api/economic-events"
                    )
                finally:
                    httpd.shutdown()
                    httpd.server_close()
                    thread.join(timeout=3)
                health = json.loads(health_body)
                items = json.loads(items_body)["items"]
                events = json.loads(events_body)["events"]
                self.assertEqual(
                    (health_status, items_status, events_status), (200, 200, 200)
                )
                self.assertEqual(health["status"], "NEWS_CACHE_INVALID")
                self.assertEqual(
                    health["cache_persistence_status"], "NEWS_CACHE_INVALID"
                )
                self.assertEqual(items, [])
                self.assertEqual(events, [])
                self.assertEqual(transport.calls, [])
                self.assertFalse(thread.is_alive())

    def test_deep_json_failure_returns_controlled_http_200_health(self):
        registry = news_sources.load_source_registry()
        bea = next(
            item for item in registry["sources"]
            if item["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        transport = valid_transport(registry)
        depth = 2000
        deep = b'{"release_dates":' + b"[" * depth + b"0" + b"]" * depth + b"}"
        transport.responses[bea["exact_endpoint"]] = response(bea, body=deep)
        service = enabled_service(transport)
        httpd = server.create_server(0, official_news_service=service)
        thread = threading.Thread(target=httpd.serve_forever, name="test-deep-json-server")
        thread.start()
        try:
            status, _, body = self.request(httpd, "GET", "/api/news-health")
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)
        health = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "NEWS_PARTIAL")
        self.assertFalse(health["refreshing"])
        self.assertEqual(
            next(
                item for item in health["source_health"]
                if item["source_id"] == bea["source_id"]
            )["reason_code"],
            "NEWS_SOURCE_SCHEMA_INVALID",
        )
        self.assertFalse(thread.is_alive())

    def test_get_head_methods_host_traversal_and_deterministic_json(self):
        service = enabled_service()
        httpd = server.create_server(0, official_news_service=service)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            for path in sorted(server.NEWS_API_ROUTES):
                status, headers, body = self.request(httpd, "GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(body, server.deterministic_json_bytes(json.loads(body)))
                self.assertEqual(headers["Cache-Control"], "no-store, max-age=0")
                head_status, head_headers, head_body = self.request(httpd, "HEAD", path)
                self.assertEqual(head_status, 200)
                self.assertEqual(head_body, b"")
                self.assertGreater(int(head_headers["Content-Length"]), 0)
                for method in ("POST", "PUT", "PATCH", "DELETE"):
                    method_status, method_headers, _ = self.request(httpd, method, path)
                    self.assertEqual(method_status, 405)
                    self.assertEqual(method_headers["Allow"], "GET, HEAD")
            status, _, body = self.request(httpd, "GET", "/api/news-health", {"Host": "example.invalid"})
            self.assertEqual(status, 421)
            self.assertEqual(json.loads(body)["error"], "LOCAL_HOST_REQUIRED")
            for path in ("/api/../news-health", "/api/%2e%2e/news-health", "/api/..%5cnews-health"):
                self.assertIn(self.request(httpd, "GET", path)[0], (400, 404))
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)

    def test_news_api_does_not_invoke_mt5(self):
        market = mock.Mock()
        httpd = server.create_server(0, market_data_service=market, official_news_service=enabled_service())
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertEqual(self.request(httpd, "GET", "/api/news-items")[0], 200)
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)
        market.snapshot_document.assert_not_called()
        market.connection_document.assert_not_called()

    def test_publisher_deadline_releases_refresh_handler_and_all_workers(self):
        context = FakeProcessContext()
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            wait_function=fake_process_wait,
        )
        service = OfficialNewsService(
            OfficialNewsConfiguration(True, 900),
            transport=transport,
            clock=FakeClock(),
            cache_storage=news_cache.InMemoryCacheStorage(),
        )
        httpd = server.create_server(0, official_news_service=service)
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-publisher-deadline-server"
        )
        server_thread.start()
        try:
            news_status, _, news_body = self.request(
                httpd, "GET", "/api/news-health"
            )
            wait_until = time.monotonic() + 2
            while context.start_count != NEWS_REFRESH_WORKERS and time.monotonic() < wait_until:
                threading.Event().wait(0.01)
            health_status, _, _ = self.request(httpd, "GET", "/api/health")
            health = json.loads(news_body)
            self.assertEqual(news_status, 200)
            self.assertEqual(health_status, 200)
            self.assertEqual(health["status"], "NEWS_REFRESHING")
            self.assertTrue(health["refreshing"])
            self.assertEqual(context.start_count, NEWS_REFRESH_WORKERS)
            self.assertEqual(context.active_count(), NEWS_REFRESH_WORKERS)

            refresh_lock_released = threading.Event()

            def acquire_refresh_lock():
                with service._lock:
                    refresh_lock_released.set()

            lock_thread = threading.Thread(
                target=acquire_refresh_lock, name="test-refresh-lock-check"
            )
            lock_thread.start()
            lock_thread.join(timeout=1)
            self.assertTrue(refresh_lock_released.is_set())
            self.assertFalse(lock_thread.is_alive())
            shutdown_started = time.monotonic()
            self.assertTrue(service.shutdown())
            self.assertLess(time.monotonic() - shutdown_started, 2)
            self.assertEqual(context.active_count(), 0)
            self.assertEqual(context.open_process_handle_count(), 0)
            self.assertEqual(transport.active_child_count(), 0)
            self.assertEqual(transport.active_process_handle_count(), 0)
            self.assertEqual(transport.active_ipc_handle_count(), 0)
            self.assertIsNone(service._refresh_owner)
            self.assertFalse(service._refreshing)
            deadline = time.monotonic() + 1
            while httpd.active_request_count() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(httpd.active_request_count(), 0)
        finally:
            shutdown_started = time.monotonic()
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=3)
            shutdown_duration = time.monotonic() - shutdown_started
        self.assertFalse(server_thread.is_alive())
        self.assertLess(shutdown_duration, 3)
        self.assertEqual(httpd.active_request_count(), 0)
        self.assertEqual(httpd.active_header_deadline_count(), 0)
        self.assertFalse(any(
            thread.is_alive() and (
                thread.name == "trl-news-source-deadline"
                or thread.name.startswith("trl-news-refresh")
                or thread.name.startswith("trl-news-coordinator")
                or thread.name.startswith("fake-trl-news-source")
            )
            for thread in threading.enumerate()
        ))

    def test_run_server_shutdown_owns_six_children_and_coordinator(self):
        context = FakeProcessContext()
        transport = DirectHttpsTransport(
            process_context=context,
            child_target=blocked_source_child,
            wait_function=fake_process_wait,
        )
        news_service = OfficialNewsService(
            OfficialNewsConfiguration(True, 900),
            transport=transport,
            clock=FakeClock(),
            cache_storage=news_cache.InMemoryCacheStorage(),
        )
        news_service.health_document()
        deadline = time.monotonic() + 2
        while context.start_count != NEWS_REFRESH_WORKERS and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(context.start_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.active_count(), NEWS_REFRESH_WORKERS)

        events = []
        actual_shutdown = news_service.shutdown

        def observed_shutdown():
            result = actual_shutdown()
            events.append("news-shutdown-complete")
            return result

        news_service.shutdown = mock.Mock(side_effect=observed_shutdown)
        fake_server = mock.Mock()
        fake_server.server_address = ("127.0.0.1", 8765)
        fake_server.official_news_service = news_service
        fake_server.serve_forever.side_effect = KeyboardInterrupt
        fake_server.server_close.side_effect = lambda: events.append("server-close")

        def capture_print(*values, **_options):
            if values and values[0] == "Local dashboard stopped.":
                events.append("stopped-message")

        with mock.patch(
            "trading_lab_app.app.create_server", return_value=fake_server,
        ), mock.patch("builtins.print", side_effect=capture_print):
            self.assertEqual(app.run_server(
                open_browser=False,
                official_news_service=news_service,
            ), 0)

        news_service.shutdown.assert_called_once_with()
        self.assertEqual(
            events,
            ["news-shutdown-complete", "server-close", "stopped-message"],
        )
        self.assertEqual(context.active_count(), 0)
        self.assertEqual(context.open_process_handle_count(), 0)
        self.assertEqual(context.join_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(context.process_close_count, NEWS_REFRESH_WORKERS)
        self.assertEqual(transport.child_record_count(), 0)
        self.assertEqual(transport.active_process_handle_count(), 0)
        self.assertEqual(transport.active_ipc_handle_count(), 0)
        self.assertFalse(news_service._refreshing)
        self.assertIsNone(news_service._refresh_owner)
        self.assertIsNone(news_service._refresh_thread)
        self.assertTrue(actual_shutdown())
        self.assertTrue(actual_shutdown())
        self.assertFalse(any(
            thread.is_alive() and (
                thread.name.startswith("trl-news-refresh")
                or thread.name.startswith("trl-news-coordinator")
                or thread.name.startswith("fake-trl-news-source")
            )
            for thread in threading.enumerate()
        ))

    def test_idle_partial_line_and_incomplete_headers_have_bounded_shutdown(self):
        cases = (
            ("idle", b""),
            ("partial_request_line", b"GET /api/health HTTP/1.1"),
            (
                "incomplete_headers",
                b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\n",
            ),
        )
        for label, payload in cases:
            with self.subTest(label=label):
                httpd = server.create_server(0)
                httpd.client_request_read_timeout_seconds = 0.4
                server_thread = threading.Thread(
                    target=httpd.serve_forever,
                    name="test-idle-server-{}".format(label),
                )
                client = None
                server_thread.start()
                try:
                    client = socket.create_connection(httpd.server_address, timeout=2)
                    if payload:
                        client.sendall(payload)
                    deadline = time.monotonic() + 2
                    while httpd.active_request_count() != 1 and time.monotonic() < deadline:
                        threading.Event().wait(0.01)
                    self.assertEqual(httpd.active_request_count(), 1)
                    status, _, body = self.request(httpd, "GET", "/api/health")
                    self.assertEqual(status, 200)
                    self.assertEqual(json.loads(body)["status"], "ok")
                    started = time.monotonic()
                    httpd.shutdown()
                    httpd.server_close()
                    duration = time.monotonic() - started
                    server_thread.join(timeout=2)
                    self.assertLess(duration, server.CLIENT_SHUTDOWN_BOUND_SECONDS)
                    self.assertFalse(server_thread.is_alive())
                    self.assertEqual(httpd.active_request_count(), 0)
                    client.settimeout(1)
                    try:
                        closed_data = client.recv(1)
                    except ConnectionResetError:
                        closed_data = b""
                    self.assertEqual(closed_data, b"")
                    handler_threads = list(getattr(httpd, "_threads", ()))
                    self.assertFalse(any(thread.is_alive() for thread in handler_threads))
                finally:
                    if client is not None:
                        client.close()
                    if server_thread.is_alive():
                        httpd.shutdown()
                    httpd.server_close()
                    server_thread.join(timeout=2)

    def test_absolute_header_deadline_releases_all_sixteen_slow_clients(self):
        httpd = server.create_server(0)
        httpd.client_request_read_timeout_seconds = 0.25
        httpd.client_request_header_deadline_seconds = 2.0
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-header-deadline-server"
        )
        clients = []
        trickle_threads = []
        stop_trickle = threading.Event()
        health_done = threading.Event()
        health_result = {}

        def trickle(client):
            while not stop_trickle.wait(0.04):
                try:
                    client.sendall(b"x")
                except OSError:
                    return

        def request_health():
            try:
                health_result["response"] = self.request(
                    httpd, "GET", "/api/health"
                )
            except OSError as error:
                health_result["error"] = type(error).__name__
            finally:
                health_done.set()

        server_thread.start()
        try:
            for index in range(server.MAX_HTTP_REQUEST_WORKERS):
                client = socket.create_connection(httpd.server_address, timeout=2)
                client.settimeout(2)
                if index % 2:
                    client.sendall(
                        b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\nX-Slow: "
                    )
                else:
                    client.sendall(b"G")
                thread = threading.Thread(
                    target=trickle,
                    args=(client,),
                    name="test-slow-header-trickle",
                )
                clients.append(client)
                trickle_threads.append(thread)
                thread.start()

            wait_until = time.monotonic() + 3
            while (
                (
                    httpd.active_request_count() != server.MAX_HTTP_REQUEST_WORKERS
                    or httpd.active_header_deadline_count()
                    != server.MAX_HTTP_REQUEST_WORKERS
                )
                and time.monotonic() < wait_until
            ):
                threading.Event().wait(0.01)
            self.assertEqual(
                httpd.active_request_count(), server.MAX_HTTP_REQUEST_WORKERS
            )
            self.assertEqual(
                httpd.active_header_deadline_count(),
                server.MAX_HTTP_REQUEST_WORKERS,
            )

            health_thread = threading.Thread(
                target=request_health, name="test-health-after-header-release"
            )
            health_started = time.monotonic()
            health_thread.start()
            self.assertTrue(health_done.wait(1.0))
            health_thread.join(timeout=1)
            self.assertIn("error", health_result)
            self.assertLess(
                time.monotonic() - health_started,
                1.0,
            )

            stop_trickle.set()
            for thread in trickle_threads:
                thread.join(timeout=1)
            wait_until = time.monotonic() + 2
            while httpd.active_request_count() and time.monotonic() < wait_until:
                threading.Event().wait(0.01)
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertFalse(any(thread.is_alive() for thread in trickle_threads))
            status, _, body = self.request(httpd, "GET", "/api/health")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["status"], "ok")
            self.assertFalse(any(
                thread.name == "trl-http-header-deadline" and thread.is_alive()
                for thread in threading.enumerate()
            ))
            for client in clients:
                try:
                    closed = client.recv(1)
                except OSError:
                    closed = b""
                self.assertEqual(closed, b"")
        finally:
            stop_trickle.set()
            for client in clients:
                client.close()
            for thread in trickle_threads:
                thread.join(timeout=1)
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
        self.assertFalse(server_thread.is_alive())
        self.assertEqual(httpd.active_request_count(), 0)
        self.assertEqual(httpd.active_header_deadline_count(), 0)
        self.assertFalse(any(
            thread.is_alive() for thread in list(getattr(httpd, "_threads", ()))
        ))

    def test_slow_header_shutdown_is_bounded_by_absolute_deadline(self):
        httpd = server.create_server(0)
        httpd.client_request_read_timeout_seconds = 0.2
        httpd.client_request_header_deadline_seconds = 0.5
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-slow-shutdown-server"
        )
        stop = threading.Event()
        client = None

        def trickle():
            while not stop.wait(0.04):
                try:
                    client.sendall(b"x")
                except OSError:
                    return

        server_thread.start()
        trickle_thread = None
        try:
            client = socket.create_connection(httpd.server_address, timeout=2)
            client.sendall(b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\nX: ")
            trickle_thread = threading.Thread(
                target=trickle, name="test-shutdown-header-trickle"
            )
            trickle_thread.start()
            wait_until = time.monotonic() + 2
            while httpd.active_request_count() != 1 and time.monotonic() < wait_until:
                threading.Event().wait(0.01)
            self.assertEqual(httpd.active_request_count(), 1)
            started = time.monotonic()
            httpd.shutdown()
            httpd.server_close()
            duration = time.monotonic() - started
            self.assertLess(
                duration, httpd.client_request_header_deadline_seconds + 1.0
            )
        finally:
            stop.set()
            if client is not None:
                client.close()
            if trickle_thread is not None:
                trickle_thread.join(timeout=1)
            if server_thread.is_alive():
                httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
        self.assertEqual(httpd.active_request_count(), 0)
        self.assertEqual(httpd.active_header_deadline_count(), 0)
        self.assertFalse(server_thread.is_alive())
        self.assertFalse(trickle_thread.is_alive())

    def test_overflow_is_rejected_without_queued_handler_or_second_deadline(self):
        httpd = server.create_server(0)
        httpd.client_request_read_timeout_seconds = 0.25
        httpd.client_request_header_deadline_seconds = 0.8
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-overflow-admission-server"
        )
        all_clients = []
        trickle_threads = []
        active_max = 0

        def saturate(label, overflow_attempts):
            nonlocal active_max
            clients = []
            stop = threading.Event()
            for _index in range(server.MAX_HTTP_REQUEST_WORKERS):
                client = socket.create_connection(httpd.server_address, timeout=2)
                client.settimeout(2)
                client.sendall(b"G")
                clients.append(client)
                all_clients.append(client)

            def trickle():
                while not stop.wait(0.04):
                    for client in clients:
                        try:
                            client.sendall(b"x")
                        except OSError:
                            pass

            trickle_thread = threading.Thread(
                target=trickle, name="test-overflow-trickle-{}".format(label)
            )
            trickle_threads.append(trickle_thread)
            trickle_thread.start()
            wait_until = time.monotonic() + 2
            while time.monotonic() < wait_until:
                active = httpd.active_request_count()
                active_max = max(active_max, active)
                if (
                    active == server.MAX_HTTP_REQUEST_WORKERS
                    and httpd.active_header_deadline_count()
                    == server.MAX_HTTP_REQUEST_WORKERS
                ):
                    break
                threading.Event().wait(0.01)
            self.assertEqual(
                httpd.active_request_count(), server.MAX_HTTP_REQUEST_WORKERS
            )
            self.assertEqual(
                httpd.active_header_deadline_count(),
                server.MAX_HTTP_REQUEST_WORKERS,
            )

            rejections_before = httpd.overflow_rejection_count()
            overflow = socket.create_connection(httpd.server_address, timeout=2)
            overflow.settimeout(1)
            all_clients.append(overflow)
            rejected_started = time.monotonic()
            try:
                overflow.sendall(b"G")
                rejected_payload = overflow.recv(64)
            except OSError:
                rejected_payload = b""
            rejected_duration = time.monotonic() - rejected_started
            self.assertEqual(rejected_payload, b"")
            self.assertLess(rejected_duration, 0.6)

            for _attempt in range(overflow_attempts - 1):
                extra = socket.create_connection(httpd.server_address, timeout=2)
                extra.settimeout(1)
                all_clients.append(extra)
                try:
                    extra.sendall(b"G")
                    extra.recv(1)
                except OSError:
                    pass
            wait_until = time.monotonic() + 2
            while (
                httpd.overflow_rejection_count()
                < rejections_before + overflow_attempts
                and time.monotonic() < wait_until
            ):
                threading.Event().wait(0.01)
            self.assertEqual(
                httpd.overflow_rejection_count(),
                rejections_before + overflow_attempts,
            )
            self.assertEqual(httpd.queued_accepted_connection_count(), 0)
            self.assertEqual(
                httpd.active_request_count(), server.MAX_HTTP_REQUEST_WORKERS
            )
            self.assertEqual(
                httpd.active_header_deadline_count(),
                server.MAX_HTTP_REQUEST_WORKERS,
            )
            return clients, stop, trickle_thread

        def reconcile_slots():
            acquired = []
            try:
                for _index in range(server.MAX_HTTP_REQUEST_WORKERS):
                    self.assertTrue(httpd._request_slots.acquire(blocking=False))
                    acquired.append(True)
                self.assertFalse(httpd._request_slots.acquire(blocking=False))
            finally:
                for _item in acquired:
                    httpd._request_slots.release()

        server_thread.start()
        try:
            first_clients, first_stop, first_trickle = saturate("first", 9)
            wait_until = time.monotonic() + 2
            while (
                (
                    httpd.active_request_count()
                    or httpd.active_header_deadline_count()
                )
                and time.monotonic() < wait_until
            ):
                active_max = max(active_max, httpd.active_request_count())
                threading.Event().wait(0.01)
            first_stop.set()
            first_trickle.join(timeout=1)
            for client in first_clients:
                client.close()
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(httpd.queued_accepted_connection_count(), 0)
            threading.Event().wait(0.1)
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            reconcile_slots()

            status, _, body = self.request(httpd, "GET", "/api/health")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["status"], "ok")

            _clients, second_stop, second_trickle = saturate("shutdown", 5)
            shutdown_started = time.monotonic()
            httpd.shutdown()
            httpd.server_close()
            shutdown_duration = time.monotonic() - shutdown_started
            second_stop.set()
            second_trickle.join(timeout=1)
            server_thread.join(timeout=2)

            self.assertEqual(active_max, server.MAX_HTTP_REQUEST_WORKERS)
            self.assertLess(
                shutdown_duration,
                httpd.client_request_header_deadline_seconds + 1.0,
            )
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(httpd.queued_accepted_connection_count(), 0)
            self.assertFalse(server_thread.is_alive())
            self.assertFalse(any(thread.is_alive() for thread in trickle_threads))
            self.assertFalse(any(
                thread.is_alive() for thread in list(getattr(httpd, "_threads", ()))
            ))
            self.assertFalse(any(
                thread.name == "trl-http-header-deadline" and thread.is_alive()
                for thread in threading.enumerate()
            ))
            self.assertEqual(httpd.socket.fileno(), -1)
            reconcile_slots()
        finally:
            for client in all_clients:
                client.close()
            for thread in trickle_threads:
                if thread.is_alive():
                    thread.join(timeout=1)
            if server_thread.is_alive():
                httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)

        self.assertTrue(all(client.fileno() == -1 for client in all_clients))

    def test_handler_thread_start_failure_is_unregistered_and_server_recovers(self):
        httpd = server.create_server(0)
        accepted, client = socket.socketpair()
        handler_start_calls = []
        server_thread = None
        permits = []

        class FailingHandlerThread(threading.Thread):
            def start(thread):
                handler_start_calls.append(thread)
                self.assertEqual(httpd.active_header_deadline_count(), 1)
                raise RuntimeError("controlled private handler start failure")

        httpd.handler_thread_factory = FailingHandlerThread
        try:
            with self.assertRaisesRegex(RuntimeError, "controlled private"):
                httpd.process_request(accepted, ("127.0.0.1", 1))

            client.settimeout(1)
            self.assertEqual(client.recv(1), b"")
            self.assertEqual(len(handler_start_calls), 1)
            self.assertEqual(list(httpd._threads), [])
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(httpd.queued_accepted_connection_count(), 0)
            self.assertEqual(accepted.fileno(), -1)
            for _index in range(server.MAX_HTTP_REQUEST_WORKERS):
                permits.append(httpd._request_slots.acquire(blocking=False))
            self.assertTrue(all(permits))
            self.assertFalse(httpd._request_slots.acquire(blocking=False))
            for acquired in permits:
                if acquired:
                    httpd._request_slots.release()
            permits.clear()

            httpd.handler_thread_factory = threading.Thread
            server_thread = threading.Thread(
                target=httpd.serve_forever,
                name="test-handler-start-recovery-server",
            )
            server_thread.start()
            status, _, body = self.request(httpd, "GET", "/api/health")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["status"], "ok")
            registered = list(httpd._threads)
            self.assertEqual(len(registered), 1)
            self.assertTrue(registered[0]._started.is_set())
            self.assertFalse(registered[0].daemon)

            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
            self.assertFalse(server_thread.is_alive())
            self.assertFalse(any(thread.is_alive() for thread in registered))
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            client.close()
            for acquired in permits:
                if acquired:
                    httpd._request_slots.release()
            if server_thread is not None and server_thread.is_alive():
                httpd.shutdown()
            httpd.server_close()
            if server_thread is not None:
                server_thread.join(timeout=2)

    def test_handler_start_failure_racing_header_expiry_cleans_exact_state(self):
        httpd = server.create_server(0)
        httpd.client_request_header_deadline_seconds = 0.05
        accepted, client = socket.socketpair()
        expiry_seen = threading.Event()
        handler_start_calls = []
        permits = []
        original_expire = httpd._expire_header_deadline

        def record_expiry(request, timer):
            original_expire(request, timer)
            expiry_seen.set()

        class ExpiryRaceFailingThread(threading.Thread):
            def start(thread):
                handler_start_calls.append(thread)
                if not expiry_seen.wait(1):
                    raise AssertionError("header deadline did not expire")
                raise RuntimeError("controlled handler start failure after expiry")

        httpd._expire_header_deadline = record_expiry
        httpd.handler_thread_factory = ExpiryRaceFailingThread
        try:
            with self.assertRaisesRegex(RuntimeError, "after expiry"):
                httpd.process_request(accepted, ("127.0.0.1", 1))
            self.assertTrue(expiry_seen.is_set())
            self.assertEqual(len(handler_start_calls), 1)
            self.assertEqual(list(httpd._threads), [])
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(accepted.fileno(), -1)
            for _index in range(server.MAX_HTTP_REQUEST_WORKERS):
                permits.append(httpd._request_slots.acquire(blocking=False))
            self.assertTrue(all(permits))
            self.assertFalse(httpd._request_slots.acquire(blocking=False))
            httpd.server_close()
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            client.close()
            for acquired in permits:
                if acquired:
                    httpd._request_slots.release()
            httpd.server_close()

    def test_failed_start_waits_for_active_deadline_callback_exact_ownership(self):
        expiry_shutdown_entered = threading.Event()
        release_expiry = threading.Event()
        failed_start_returned = threading.Event()
        errors = []
        timers = []
        handler_threads = []
        permits = []

        class ControlledSocket:
            def __init__(controlled):
                controlled.close_count = 0

            def shutdown(controlled, _how):
                if threading.current_thread().name == "trl-http-header-deadline":
                    expiry_shutdown_entered.set()
                    if not release_expiry.wait(2):
                        raise AssertionError("deadline expiry was not released")

            def close(controlled):
                controlled.close_count += 1

        class CountingTimer(threading.Timer):
            def __init__(timer, interval, function):
                super().__init__(interval, function)
                timer.join_count = 0

            def join(timer, timeout=None):
                timer.join_count += 1
                return super().join(timeout)

        class FailingHandlerThread(threading.Thread):
            def __init__(thread, **kwargs):
                super().__init__(**kwargs)
                thread.join_count = 0
                handler_threads.append(thread)

            def start(thread):
                if not expiry_shutdown_entered.wait(2):
                    raise AssertionError("deadline callback did not begin")
                raise RuntimeError("controlled failure during deadline expiry")

            def join(thread, timeout=None):
                thread.join_count += 1
                return super().join(timeout)

        def timer_factory(interval, function):
            timer = CountingTimer(interval, function)
            timers.append(timer)
            return timer

        request = ControlledSocket()
        httpd = server.create_server(0)
        httpd.client_request_header_deadline_seconds = 0.01
        httpd.deadline_timer_factory = timer_factory
        httpd.handler_thread_factory = FailingHandlerThread

        def fail_start():
            try:
                httpd.process_request(request, ("127.0.0.1", 1))
            except RuntimeError as error:
                errors.append(str(error))
            finally:
                failed_start_returned.set()

        caller = threading.Thread(target=fail_start, name="test-fix15-failed-start")
        caller.start()
        try:
            self.assertTrue(expiry_shutdown_entered.wait(1))
            wait_until = time.monotonic() + 1
            while not timers[0].finished.is_set() and time.monotonic() < wait_until:
                threading.Event().wait(0.005)
            self.assertTrue(timers[0].finished.is_set())
            self.assertFalse(failed_start_returned.is_set())
            self.assertTrue(caller.is_alive())

            release_expiry.set()
            caller.join(timeout=2)
            self.assertFalse(caller.is_alive())
            self.assertTrue(failed_start_returned.is_set())
            self.assertEqual(
                errors, ["controlled failure during deadline expiry"]
            )
            self.assertFalse(timers[0].is_alive())
            self.assertTrue(timers[0].finished.is_set())
            self.assertEqual(timers[0].join_count, 1)
            self.assertEqual(handler_threads[0].join_count, 0)
            self.assertEqual(request.close_count, 1)
            self.assertEqual(httpd.deadline_record_count(), 0)
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(list(httpd._threads), [])

            for _index in range(server.MAX_HTTP_REQUEST_WORKERS):
                permits.append(httpd._request_slots.acquire(blocking=False))
            self.assertTrue(all(permits))
            self.assertFalse(httpd._request_slots.acquire(blocking=False))
            httpd.server_close()
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            release_expiry.set()
            caller.join(timeout=2)
            for acquired in permits:
                if acquired:
                    httpd._request_slots.release()
            httpd.server_close()

    def test_handler_closure_never_joins_current_handler(self):
        close_errors = []
        close_returned = threading.Event()
        handler_threads = []
        accepted, client = socket.socketpair()

        class CloseFromHandler(server.ApplicationHandler):
            def do_GET(handler):
                try:
                    handler.server.server_close()
                except Exception as error:
                    close_errors.append("{}: {}".format(type(error).__name__, error))
                finally:
                    close_returned.set()
                handler._send_json(200, {"status": "closed-without-self-join"})

        class CountingHandlerThread(threading.Thread):
            def __init__(thread, **kwargs):
                super().__init__(**kwargs)
                thread.join_count = 0
                handler_threads.append(thread)

            def join(thread, timeout=None):
                thread.join_count += 1
                return super().join(timeout)

        httpd = server.create_server(0, handler_class=CloseFromHandler)
        httpd.handler_thread_factory = CountingHandlerThread
        try:
            client.sendall(
                b"GET / HTTP/1.0\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n"
            )
            httpd.process_request(accepted, ("127.0.0.1", 1))
            self.assertTrue(close_returned.wait(2))
            self.assertEqual(close_errors, [])
            httpd.server_close()
            self.assertEqual(handler_threads[0].join_count, 1)
            self.assertFalse(handler_threads[0].is_alive())
            self.assertEqual(list(httpd._threads), [])
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.deadline_record_count(), 0)
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            client.close()
            httpd.server_close()

    def test_concurrent_handler_closures_do_not_cross_join(self):
        closure_barrier = threading.Barrier(2)
        close_returned = [threading.Event(), threading.Event()]
        close_errors = []
        handler_threads = []
        socket_pairs = [socket.socketpair(), socket.socketpair()]

        class ConcurrentCloseHandler(server.ApplicationHandler):
            def do_GET(handler):
                index = int(handler.path.lstrip("/"))
                try:
                    closure_barrier.wait(timeout=2)
                    handler.server.server_close()
                except Exception as error:
                    close_errors.append("{}: {}".format(type(error).__name__, error))
                finally:
                    close_returned[index].set()
                handler._send_json(200, {"status": "close-returned"})

        class CountingHandlerThread(threading.Thread):
            def __init__(thread, **kwargs):
                super().__init__(**kwargs)
                thread.join_count = 0
                handler_threads.append(thread)

            def join(thread, timeout=None):
                thread.join_count += 1
                return super().join(timeout)

        httpd = server.create_server(0, handler_class=ConcurrentCloseHandler)
        httpd.handler_thread_factory = CountingHandlerThread
        try:
            for index, (accepted, client) in enumerate(socket_pairs):
                client.sendall(
                    "GET /{} HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n".format(index).encode(
                        "ascii"
                    )
                )
                httpd.process_request(accepted, ("127.0.0.1", index + 1))
            self.assertTrue(all(event.wait(2) for event in close_returned))
            self.assertEqual(close_errors, [])
            self.assertEqual([thread.join_count for thread in handler_threads], [0, 0])

            httpd.server_close()
            self.assertEqual([thread.join_count for thread in handler_threads], [1, 1])
            self.assertFalse(any(thread.is_alive() for thread in handler_threads))
            self.assertEqual(list(httpd._threads), [])
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.deadline_record_count(), 0)
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            for _accepted, client in socket_pairs:
                client.close()
            httpd.server_close()

    def test_finished_before_registration_is_joined_before_record_discard(self):
        handler_threads = []
        permits = []
        accepted, client = socket.socketpair()
        failed_socket, failed_client = socket.socketpair()

        class FinishedBeforeRegistrationThread(threading.Thread):
            def __init__(thread, **kwargs):
                super().__init__(**kwargs)
                thread.join_count = 0
                handler_threads.append(thread)

            def start(thread):
                super().start()
                threading.Thread.join(thread, 2)
                if thread.is_alive():
                    raise AssertionError("handler did not finish before registration")

            def join(thread, timeout=None):
                thread.join_count += 1
                return super().join(timeout)

        class FailingSecondThread(threading.Thread):
            def start(thread):
                raise RuntimeError("controlled later start failure")

        httpd = server.create_server(0)
        try:
            client.sendall(
                b"GET /api/health HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n"
            )
            httpd.handler_thread_factory = FinishedBeforeRegistrationThread
            httpd.process_request(accepted, ("127.0.0.1", 1))
            self.assertEqual(len(list(httpd._threads)), 1)
            self.assertFalse(handler_threads[0].is_alive())
            self.assertEqual(handler_threads[0].join_count, 0)

            httpd.handler_thread_factory = FailingSecondThread
            with self.assertRaisesRegex(RuntimeError, "later start failure"):
                httpd.process_request(failed_socket, ("127.0.0.1", 2))
            self.assertEqual(handler_threads[0].join_count, 1)
            self.assertEqual(list(httpd._threads), [])
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.deadline_record_count(), 0)

            for _index in range(server.MAX_HTTP_REQUEST_WORKERS):
                permits.append(httpd._request_slots.acquire(blocking=False))
            self.assertTrue(all(permits))
            self.assertFalse(httpd._request_slots.acquire(blocking=False))
            httpd.server_close()
            self.assertEqual(handler_threads[0].join_count, 1)
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            client.close()
            failed_client.close()
            for acquired in permits:
                if acquired:
                    httpd._request_slots.release()
            httpd.server_close()

    def test_server_close_race_keeps_successful_handler_join_ownership(self):
        route_started = threading.Event()
        release_route = threading.Event()
        failed_start_entered = threading.Event()
        release_failed_start = threading.Event()

        class BlockingHandler(server.ApplicationHandler):
            def do_GET(self):
                route_started.set()
                release_route.wait(timeout=3)
                self._send_json(200, {"status": "joined"})

        class BlockingFailingThread(threading.Thread):
            def start(thread):
                failed_start_entered.set()
                if not release_failed_start.wait(3):
                    raise AssertionError("failed handler start was not released")
                raise RuntimeError("controlled concurrent handler start failure")

        httpd = server.create_server(0, handler_class=BlockingHandler)
        server_thread = threading.Thread(
            target=httpd.serve_forever,
            name="test-handler-registry-race-server",
        )
        response = {}
        request_thread = threading.Thread(
            target=lambda: response.setdefault(
                "value", self.request(httpd, "GET", "/joined")
            ),
            name="test-successful-handler-client",
        )
        failed_socket = None
        failed_client = None
        failed_caller = None
        closer = None
        start_errors = []
        close_errors = []
        server_thread.start()
        request_thread.start()
        try:
            self.assertTrue(route_started.wait(2))
            httpd.shutdown()
            server_thread.join(timeout=2)
            self.assertFalse(server_thread.is_alive())
            successful_threads = list(httpd._threads)
            self.assertEqual(len(successful_threads), 1)
            self.assertTrue(successful_threads[0].is_alive())
            self.assertFalse(successful_threads[0].daemon)

            httpd.handler_thread_factory = BlockingFailingThread
            failed_socket, failed_client = socket.socketpair()

            def fail_request_start():
                try:
                    httpd.process_request(failed_socket, ("127.0.0.1", 2))
                except RuntimeError as error:
                    start_errors.append(str(error))

            def close_server():
                try:
                    httpd.server_close()
                except Exception as error:
                    close_errors.append(error)

            failed_caller = threading.Thread(
                target=fail_request_start,
                name="test-failed-handler-start-caller",
            )
            failed_caller.start()
            self.assertTrue(failed_start_entered.wait(2))
            closer = threading.Thread(
                target=close_server,
                name="test-concurrent-server-close",
            )
            closer.start()
            threading.Event().wait(0.05)
            self.assertTrue(closer.is_alive())

            release_failed_start.set()
            failed_caller.join(timeout=2)
            self.assertFalse(failed_caller.is_alive())
            self.assertEqual(
                start_errors, ["controlled concurrent handler start failure"]
            )
            self.assertEqual(list(httpd._threads), successful_threads)
            self.assertTrue(closer.is_alive())
            self.assertEqual(httpd.active_request_count(), 1)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(failed_socket.fileno(), -1)

            release_route.set()
            request_thread.join(timeout=2)
            closer.join(timeout=2)
            self.assertFalse(request_thread.is_alive())
            self.assertFalse(closer.is_alive())
            self.assertEqual(close_errors, [])
            self.assertEqual(response["value"][0], 200)
            self.assertFalse(successful_threads[0].is_alive())
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            self.assertEqual(httpd.socket.fileno(), -1)
        finally:
            release_failed_start.set()
            release_route.set()
            if failed_client is not None:
                failed_client.close()
            if failed_caller is not None:
                failed_caller.join(timeout=2)
            request_thread.join(timeout=2)
            if server_thread.is_alive():
                httpd.shutdown()
            server_thread.join(timeout=2)
            httpd.server_close()
            if closer is not None:
                closer.join(timeout=2)

    def test_first_header_deadline_begins_before_handler_setup(self):
        setup_entered = threading.Event()
        release_setup = threading.Event()

        class DelayedSetupHandler(server.ApplicationHandler):
            def setup(self):
                setup_entered.set()
                release_setup.wait(timeout=2)
                super().setup()

        httpd = server.create_server(0, handler_class=DelayedSetupHandler)
        httpd.client_request_header_deadline_seconds = 0.2
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-admission-deadline-server"
        )
        client = None
        server_thread.start()
        try:
            client = socket.create_connection(httpd.server_address, timeout=2)
            client.settimeout(1)
            client.sendall(b"G")
            self.assertTrue(setup_entered.wait(1))
            self.assertEqual(httpd.active_header_deadline_count(), 1)
            threading.Event().wait(0.3)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            try:
                payload = client.recv(1)
            except OSError:
                payload = b""
            self.assertEqual(payload, b"")
            release_setup.set()
            wait_until = time.monotonic() + 1
            while httpd.active_request_count() and time.monotonic() < wait_until:
                threading.Event().wait(0.01)
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
        finally:
            release_setup.set()
            if client is not None:
                client.close()
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
        self.assertFalse(server_thread.is_alive())

    def test_expired_header_deadline_wins_the_parse_completion_race(self):
        expiry_recorded = threading.Event()
        route_called = threading.Event()

        class ParseRaceHandler(server.ApplicationHandler):
            def parse_request(self):
                parsed = super().parse_request()
                if parsed:
                    expiry_recorded.wait(timeout=1)
                return parsed

            def do_GET(self):
                route_called.set()
                self._send_json(200, {"status": "must-not-run"})

        httpd = server.create_server(0, handler_class=ParseRaceHandler)
        httpd.client_request_header_deadline_seconds = 0.2
        original_expire = httpd._expire_header_deadline

        def record_expiry(request, timer):
            original_expire(request, timer)
            expiry_recorded.set()

        httpd._expire_header_deadline = record_expiry
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-header-parse-race-server"
        )
        client = None
        server_thread.start()
        try:
            client = socket.create_connection(httpd.server_address, timeout=2)
            client.settimeout(1)
            client.sendall(b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
            self.assertTrue(expiry_recorded.wait(1))
            try:
                payload = client.recv(64)
            except OSError:
                payload = b""
            self.assertEqual(payload, b"")
            self.assertFalse(route_called.is_set())
            wait_until = time.monotonic() + 1
            while httpd.active_request_count() and time.monotonic() < wait_until:
                threading.Event().wait(0.01)
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
        finally:
            if client is not None:
                client.close()
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
        self.assertFalse(server_thread.is_alive())

    def test_header_deadline_ends_before_long_route_processing(self):
        route_started = threading.Event()
        release_route = threading.Event()

        class LongRouteHandler(server.ApplicationHandler):
            def do_GET(self):
                route_started.set()
                release_route.wait(timeout=2)
                self._send_json(200, {"status": "long-route-complete"})

        httpd = server.create_server(0, handler_class=LongRouteHandler)
        httpd.client_request_header_deadline_seconds = 0.2
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-long-route-server"
        )
        result = {}

        def request_long_route():
            result["response"] = self.request(httpd, "GET", "/long")

        request_thread = threading.Thread(
            target=request_long_route, name="test-long-route-client"
        )
        server_thread.start()
        request_thread.start()
        try:
            self.assertTrue(route_started.wait(1))
            self.assertEqual(httpd.active_header_deadline_count(), 0)
            threading.Event().wait(0.35)
            self.assertTrue(request_thread.is_alive())
            release_route.set()
            request_thread.join(timeout=2)
            self.assertFalse(request_thread.is_alive())
            self.assertEqual(result["response"][0], 200)
            self.assertEqual(
                json.loads(result["response"][2])["status"],
                "long-route-complete",
            )
        finally:
            release_route.set()
            request_thread.join(timeout=1)
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
        self.assertEqual(httpd.active_header_deadline_count(), 0)
        self.assertEqual(httpd.active_request_count(), 0)

    def test_keep_alive_starts_an_independent_header_deadline(self):
        class KeepAliveHandler(server.ApplicationHandler):
            protocol_version = "HTTP/1.1"

        httpd = server.create_server(0, handler_class=KeepAliveHandler)
        httpd.client_request_read_timeout_seconds = 0.2
        httpd.client_request_header_deadline_seconds = 0.45
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-keep-alive-server"
        )
        stop = threading.Event()
        client = None
        reader = None
        trickle_thread = None

        def trickle_second_request():
            while not stop.wait(0.04):
                try:
                    client.sendall(b"x")
                except OSError:
                    return

        server_thread.start()
        try:
            client = socket.create_connection(httpd.server_address, timeout=2)
            client.settimeout(2)
            reader = client.makefile("rb")
            client.sendall(
                b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                b"Connection: keep-alive\r\n\r\n"
            )
            first_status, _, _ = self.raw_response(reader)
            self.assertEqual(first_status, 200)
            wait_until = time.monotonic() + 1
            while (
                httpd.active_header_deadline_count() != 1
                and time.monotonic() < wait_until
            ):
                threading.Event().wait(0.01)
            self.assertEqual(httpd.active_header_deadline_count(), 1)
            client.sendall(b"G")
            trickle_thread = threading.Thread(
                target=trickle_second_request,
                name="test-keep-alive-header-trickle",
            )
            trickle_thread.start()
            try:
                closed = reader.read(1)
            except OSError:
                closed = b""
            self.assertEqual(closed, b"")
            stop.set()
            trickle_thread.join(timeout=1)
            wait_until = time.monotonic() + 1
            while httpd.active_request_count() and time.monotonic() < wait_until:
                threading.Event().wait(0.01)
            self.assertEqual(httpd.active_request_count(), 0)
            self.assertEqual(httpd.active_header_deadline_count(), 0)
        finally:
            stop.set()
            if reader is not None:
                reader.close()
            if client is not None:
                client.close()
            if trickle_thread is not None:
                trickle_thread.join(timeout=1)
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=2)
        self.assertFalse(server_thread.is_alive())
        self.assertFalse(any(
            thread.name == "trl-http-header-deadline" and thread.is_alive()
            for thread in threading.enumerate()
        ))

    def test_blocked_news_refresh_does_not_block_health_or_duplicate_refresh(self):
        registry = news_sources.load_source_registry()
        transport = ConcurrentGateTransport({
            source["exact_endpoint"]: response(source) for source in registry["sources"]
        })
        service = enabled_service(transport, asynchronous=True)
        httpd = server.create_server(0, official_news_service=service)
        server_thread = threading.Thread(
            target=httpd.serve_forever, name="test-local-server"
        )
        server_thread.start()
        results = []
        failures = []

        def request_news():
            started = time.monotonic()
            try:
                status, headers, body = self.request(
                    httpd, "GET", "/api/news-items"
                )
                results.append((
                    status, headers, json.loads(body), time.monotonic() - started,
                ))
            except Exception as error:
                failures.append(error)

        clients = [
            threading.Thread(
                target=request_news, name="test-news-client-{}".format(index)
            )
            for index in range(server.MAX_HTTP_REQUEST_WORKERS)
        ]
        for client in clients:
            client.start()
        try:
            self.assertTrue(transport.all_workers_active.wait(timeout=3))
            with service._lock:
                trusted_snapshot = copy.deepcopy(service._cache)
                owner = service._refresh_owner
            for client in clients:
                client.join(timeout=2)
            self.assertTrue(all(not client.is_alive() for client in clients))
            self.assertEqual(len(results), server.MAX_HTTP_REQUEST_WORKERS)
            self.assertTrue(all(item[0] == 200 for item in results))
            self.assertTrue(all(item[2]["refreshing"] for item in results))
            self.assertTrue(all(item[3] < 2 for item in results))
            status, _, body = self.request(httpd, "GET", "/api/health")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["status"], "ok")
            self.assertFalse(transport.release.is_set())
            lock_available = service._lock.acquire(blocking=False)
            self.assertTrue(lock_available)
            if lock_available:
                service._lock.release()
            with service._lock:
                self.assertEqual(service._cache, trusted_snapshot)
                self.assertEqual(service._refresh_owner, owner)
                self.assertTrue(service._refreshing)
            self.assertEqual(service.health_document()["network_request_count"], 6)
        finally:
            transport.release.set()
            for client in clients:
                client.join(timeout=5)
            self.assertTrue(service.wait_for_refresh(5))
            httpd.shutdown()
            httpd.server_close()
            server_thread.join(timeout=5)
        self.assertEqual(failures, [])
        self.assertTrue(all(not client.is_alive() for client in clients))
        self.assertFalse(server_thread.is_alive())
        self.assertEqual(len(transport.calls), 6)
        self.assertEqual(service.health_document()["network_request_count"], 6)
        self.assertIsNone(service._refresh_owner)
        self.assertFalse(service._refreshing)
        self.assertEqual(httpd.active_request_count(), 0)
        self.assertFalse(any(
            (
                thread.name.startswith("trl-news-refresh")
                or thread.name.startswith("trl-news-coordinator")
            ) and thread.is_alive()
            for thread in threading.enumerate()
        ))

    def test_dashboard_accessibility_links_disclaimers_and_states(self):
        html = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
        javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        css = (STATIC_DIRECTORY / "styles.css").read_text(encoding="utf-8")
        for text in (
            'id="official-news"', "Official news and events", "OFFICIAL-SOURCE INFORMATION ONLY",
            "NO STRATEGY IS BEING SELECTED", "NO BULLISH OR BEARISH INTERPRETATION",
            "NO TRADE INSTRUCTION", "NO MT5 OR ORDER ACTION",
            "SOURCE TERMS AND AVAILABILITY CAN CHANGE", "news-disabled-state",
            "news-empty-state", "news-partial-state", "news-error-state",
            "news-persistence-state", "news-cache-persistence",
            "Upcoming BEA economic releases", "Event occurrence", "Series ID",
            "grouped by deterministic series identity", "<table", "<caption",
        ):
            self.assertIn(text, html)
        self.assertIn('link.target = "_blank"', javascript)
        self.assertIn('link.rel = "noopener noreferrer"', javascript)
        self.assertIn('getJson("/api/news-health")', javascript)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("news-card-grid", css)
        self.assertNotIn("innerHTML", javascript[javascript.index("function externalSourceLink"):javascript.index("function wireTabs")])

    def test_dashboard_links_only_governed_item_urls_and_marks_stale_records(self):
        javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        html = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
        source = news_sources.load_source_registry()["sources"][0]
        governed = news_parser.parse_xml_news(
            RSS_BODY, source, "2026-07-27T12:00:00Z"
        )[0]
        fallback = news_parser.parse_xml_news(
            b"<rss><channel><item><title>No link</title></item></channel></rss>",
            source, "2026-07-27T12:00:00Z",
        )[0]
        unsafe = news_parser.parse_xml_news(
            b"<rss><channel><item><title>Unsafe</title><link>https://example.invalid/item</link></item></channel></rss>",
            source, "2026-07-27T12:00:00Z",
        )[0]
        bea = next(
            item for item in news_sources.load_source_registry()["sources"]
            if item["source_id"] == "BEA_RELEASE_DATES_JSON"
        )
        event = news_parser.parse_bea_release_dates(
            b'{"release_dates":[{"ReleaseDate":"2026-07-30","ReleaseName":"No URL event"}]}',
            bea, "2026-07-27T12:00:00Z",
        )[0]

        def anchor_count(record):
            return int(
                record["source_url_availability_status"]
                == "GOVERNED_ITEM_LINK_AVAILABLE"
            )

        self.assertEqual(anchor_count(governed), 1)
        self.assertEqual(anchor_count(fallback), 0)
        self.assertEqual(anchor_count(unsafe), 0)
        self.assertEqual(anchor_count(event), 0)
        self.assertEqual(event["source_url"], bea["exact_endpoint"])
        self.assertEqual(event["source_url_reason_code"], "SOURCE_ITEM_LINK_NOT_PROVIDED")
        reference = javascript[
            javascript.index("function officialItemReference"):
            javascript.index("function operationalFreshnessLabel")
        ]
        self.assertIn('=== "GOVERNED_ITEM_LINK_AVAILABLE"', reference)
        self.assertEqual(reference.count("externalSourceLink("), 1)
        self.assertIn("Official item link unavailable", reference)
        self.assertIn("source_url_reason_code", reference)
        self.assertNotIn("innerHTML", reference)
        self.assertIn("STALE — SOURCE UNAVAILABLE", javascript)
        self.assertIn("source freshness are explicit", html)

    def test_dashboard_persistence_warning_remains_visible_during_partial_state(self):
        javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        html = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
        css = (STATIC_DIRECTORY / "styles.css").read_text(encoding="utf-8")
        partial_branch = javascript.index('health.status === "NEWS_PARTIAL"')
        persistence_branch = javascript.index(
            'health.cache_persistence_status === "NEWS_CACHE_WRITE_FAILED"'
        )
        self.assertLess(partial_branch, persistence_branch)
        self.assertIn('setText("news-cache-persistence"', javascript)
        self.assertIn('warning.hidden = false', javascript[persistence_branch:])
        self.assertIn(
            "Current in-memory news updates were not persisted and may be lost after restart.",
            html,
        )
        self.assertIn('id="news-persistence-state"', html)
        self.assertIn('role="alert"', html[html.index('id="news-persistence-state"'):])
        self.assertIn(".persistence-warning", css)
        self.assertNotIn(
            "innerHTML",
            javascript[javascript.index("function renderOfficialNews"):
                       javascript.index("async function loadOfficialNews")],
        )

    def test_capability_manifest_keeps_prohibited_surfaces_closed(self):
        manifest = capabilities.capability_manifest()
        self.assertTrue(manifest["official_news_metadata_capability"])
        self.assertFalse(manifest["official_news_enabled_by_default"])
        self.assertEqual(
            manifest["official_news_stable_health_reason_codes"],
            list(STABLE_HEALTH_CODES),
        )
        self.assertIn(
            "NEWS_SOURCE_INTERNAL_ERROR",
            manifest["official_news_stable_health_reason_codes"],
        )
        for field in (
            "official_news_full_text_capability", "official_news_sentiment_capability",
            "official_news_market_impact_capability", "official_news_event_price_join_capability",
            "external_order_capability", "credential_storage_capability", "telemetry",
        ):
            self.assertFalse(manifest[field])


if __name__ == "__main__":
    unittest.main(verbosity=2)
