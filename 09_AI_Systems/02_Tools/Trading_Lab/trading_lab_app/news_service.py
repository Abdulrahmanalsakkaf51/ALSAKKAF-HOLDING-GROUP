"""Local-only service, refresh governance, health, revisions, and cache facade."""

import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading

from . import news_cache, news_data, news_sources
from .news_connector import OfficialNewsConnector, RetrievalError


DEFAULT_REFRESH_SECONDS = 900
MIN_REFRESH_SECONDS = 300
MAX_REFRESH_SECONDS = 3600
MAX_API_RECORDS = 1000
MAX_SOURCE_RECORDS = 200
NEWS_REFRESH_WORKERS = 6
SERVICE_REFRESH_SHUTDOWN_BOUND_SECONDS = 3.0
HEALTH_SCHEMA = "TRL-OFFICIAL-NEWS-HEALTH-1.2"
CACHE_PERSISTENCE_WARNING = (
    "Current in-memory news updates were not persisted and may be lost after restart."
)
STABLE_HEALTH_CODES = (
    "NEWS_DISABLED", "NEWS_ENABLED_NO_DATA", "NEWS_REFRESHING", "NEWS_VALID",
    "NEWS_PARTIAL", "NEWS_ALL_SOURCES_FAILED", "NEWS_SOURCE_TIMEOUT",
    "NEWS_SOURCE_HTTP_ERROR", "NEWS_SOURCE_REDIRECT_BLOCKED",
    "NEWS_SOURCE_INTERNAL_ERROR",
    "NEWS_SOURCE_TOO_LARGE", "NEWS_SOURCE_CONTENT_TYPE_INVALID",
    "NEWS_SOURCE_UTF8_INVALID", "NEWS_SOURCE_XML_UNSAFE",
    "NEWS_SOURCE_PARSE_ERROR", "NEWS_SOURCE_SCHEMA_INVALID", "NEWS_SOURCE_STALE",
    "NEWS_RATE_LIMITED_LOCALLY", "NEWS_CACHE_INVALID",
    "NEWS_CACHE_WRITE_FAILED", "NEWS_PROVIDER_CHANGED",
)


@dataclass(frozen=True)
class OfficialNewsConfiguration:
    enabled: bool = False
    refresh_seconds: int = DEFAULT_REFRESH_SECONDS

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        if (
            type(self.refresh_seconds) is not int
            or not MIN_REFRESH_SECONDS <= self.refresh_seconds <= MAX_REFRESH_SECONDS
        ):
            raise ValueError("official-news refresh must be from 300 through 3600 seconds")


def _utc_now(clock):
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("clock must return an aware datetime")
    return value.astimezone(timezone.utc)


class OfficialNewsService:
    """Network-silent unless explicitly enabled; all collaborators are injectable."""

    def __init__(self, configuration=None, transport=None, clock=None, cache_storage=None):
        self.configuration = configuration or OfficialNewsConfiguration()
        self._transport = transport
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._cache_storage = cache_storage
        self._initialized = False
        self._registry = None
        self._connector = None
        self._cache = None
        self._source_health = {}
        self._last_attempt = None
        self._last_success = None
        self._overall_status = "NEWS_DISABLED" if not self.configuration.enabled else "NEWS_ENABLED_NO_DATA"
        self._reason_code = self._overall_status
        self._diagnostics = []
        self._network_request_count = 0
        self._refreshing = False
        self._refresh_generation = 0
        self._refresh_owner = None
        self._refresh_thread = None
        self._shutdown = False
        self._cache_persistence_status = (
            "NEWS_DISABLED" if not self.configuration.enabled else "NEWS_ENABLED_NO_DATA"
        )
        self._cache_persistence_reason = self._cache_persistence_status
        self._cache_persistence_diagnostic = None
        self._request_count_lock = threading.Lock()
        self._lock = threading.RLock()

    def _set_cache_persistence(self, status):
        self._cache_persistence_status = status
        self._cache_persistence_reason = status
        self._cache_persistence_diagnostic = (
            CACHE_PERSISTENCE_WARNING
            if status == "NEWS_CACHE_WRITE_FAILED" else None
        )
        self._diagnostics = [
            item for item in self._diagnostics
            if item != CACHE_PERSISTENCE_WARNING
        ]
        if self._cache_persistence_diagnostic is not None:
            self._diagnostics.append(self._cache_persistence_diagnostic)

    def _cache_persistence_fields(self):
        return {
            "cache_persistence_status": self._cache_persistence_status,
            "cache_persistence_reason": self._cache_persistence_reason,
            "cache_persistence_diagnostic": self._cache_persistence_diagnostic,
        }

    def _initialize_enabled(self):
        if self._initialized:
            return
        now = _utc_now(self._clock)
        try:
            self._registry = news_sources.load_source_registry()
        except Exception:
            self._overall_status = "NEWS_PROVIDER_CHANGED"
            self._reason_code = "NEWS_PROVIDER_CHANGED"
            self._diagnostics.append("The committed source registry failed closed.")
            self._initialized = True
            return
        self._connector = OfficialNewsConnector(transport=self._transport)
        storage_ready = True
        if self._cache_storage is None:
            try:
                self._cache_storage = news_cache.production_storage()
            except Exception:
                storage_ready = False
                self._cache = news_cache.empty_document(news_data.utc_timestamp(now))
                self._overall_status = "NEWS_CACHE_WRITE_FAILED"
                self._reason_code = "NEWS_CACHE_WRITE_FAILED"
                self._set_cache_persistence("NEWS_CACHE_WRITE_FAILED")
                self._diagnostics.append(
                    "The local cache storage was unavailable; persistence failed closed."
                )
        if storage_ready:
            try:
                loaded = self._cache_storage.load()
                self._cache = news_cache.validate_document(
                    loaded, now, self._registry
                )
                self._set_cache_persistence("NEWS_VALID")
            except Exception as error:
                self._cache = news_cache.empty_document(news_data.utc_timestamp(now))
                reason_code = (
                    error.reason_code
                    if isinstance(error, news_cache.CacheError)
                    else "NEWS_CACHE_INVALID"
                )
                self._overall_status = reason_code
                self._reason_code = reason_code
                self._set_cache_persistence("NEWS_CACHE_INVALID")
                self._diagnostics.append(
                    "The local cache was rejected and was not trusted."
                )
        if self._cache is None:
            self._cache = news_cache.empty_document(news_data.utc_timestamp(now))
        self._source_health = {
            source["source_id"]: {
                "source_id": source["source_id"],
                "status": "NEWS_ENABLED_NO_DATA",
                "reason_code": "NEWS_ENABLED_NO_DATA",
                "last_attempt_timestamp_utc": None,
                "last_success_timestamp_utc": None,
                "retrieved_entry_count": 0,
            }
            for source in self._registry["sources"]
        }
        self._initialized = True

    @staticmethod
    def _merge(cache_document, kind, records, observed):
        wrappers = {
            (wrapper["kind"], wrapper["identity"]): wrapper
            for wrapper in cache_document["records"]
        }
        id_field = "news_id" if kind == "news" else "event_id"
        for incoming in records:
            key = (kind, incoming[id_field])
            fingerprint = news_data.observation_fingerprint(incoming)
            existing = wrappers.get(key)
            if existing is None:
                wrapper = {
                    "kind": kind,
                    "identity": incoming[id_field],
                    "fingerprint": fingerprint,
                    "first_seen_timestamp_utc": observed,
                    "last_seen_timestamp_utc": observed,
                    "record": copy.deepcopy(incoming),
                }
                wrappers[key] = wrapper
            else:
                revision = existing["record"]["revision_number"]
                if existing["fingerprint"] != fingerprint:
                    revision += 1
                replacement = copy.deepcopy(incoming)
                replacement["revision_number"] = revision
                existing["record"] = replacement
                existing["fingerprint"] = news_data.observation_fingerprint(replacement)
                existing["last_seen_timestamp_utc"] = observed
        cache_document["records"] = list(wrappers.values())

    def _retrieve_source(self, source, observed):
        with self._request_count_lock:
            self._network_request_count += 1
        return self._connector.retrieve(source, observed)

    def _collect_outcomes(self, sources, observed):
        outcomes = {}
        with ThreadPoolExecutor(
            max_workers=NEWS_REFRESH_WORKERS,
            thread_name_prefix="trl-news-refresh",
        ) as executor:
            futures = {}
            for source in sources:
                try:
                    future = executor.submit(self._retrieve_source, source, observed)
                except Exception:
                    outcomes[source["source_id"]] = (None, "NEWS_SOURCE_SCHEMA_INVALID")
                else:
                    futures[future] = source["source_id"]
            try:
                completed = as_completed(futures)
                for future in completed:
                    source_id = futures[future]
                    try:
                        outcomes[source_id] = (future.result(), None)
                    except RetrievalError as error:
                        outcomes[source_id] = (None, error.reason_code)
                    except Exception:
                        outcomes[source_id] = (None, "NEWS_SOURCE_SCHEMA_INVALID")
            except Exception:
                pass
        for source in sources:
            outcomes.setdefault(
                source["source_id"], (None, "NEWS_SOURCE_SCHEMA_INVALID")
            )
        return outcomes

    def _apply_outcome(
        self, candidate, source, outcome, observed, source_health,
    ):
        source_id = source["source_id"]
        health = source_health[source_id]
        result, failure_reason = outcome
        if failure_reason is None:
            try:
                if (
                    type(result) is not tuple
                    or len(result) != 2
                ):
                    raise ValueError("invalid governed source result")
                items, events = result
                if (
                    type(items) is not list
                    or type(events) is not list
                    or len(items) + len(events) > MAX_SOURCE_RECORDS
                ):
                    raise ValueError("invalid governed source result")
                validated_items = [
                    news_data.validate_cached_record("news", item, source)
                    for item in items
                ]
                validated_events = [
                    news_data.validate_cached_record("event", event, source)
                    for event in events
                ]
                for records, id_field in (
                    (validated_items, "news_id"),
                    (validated_events, "event_id"),
                ):
                    fallback_identities = set()
                    for record in records:
                        if (
                            record["source_url_availability_status"]
                            != "SOURCE_ENDPOINT_FALLBACK"
                        ):
                            continue
                        identity = record[id_field]
                        if identity in fallback_identities:
                            raise ValueError("duplicate endpoint-fallback identity")
                        fallback_identities.add(identity)
                if any(
                    record["revision_number"] != 1
                    or record["retrieved_timestamp_utc"] != observed
                    for record in validated_items + validated_events
                ):
                    raise ValueError("invalid governed source observation")
                source_candidate = copy.deepcopy(candidate)
                self._merge(source_candidate, "news", validated_items, observed)
                self._merge(source_candidate, "event", validated_events, observed)
                count = len(items) + len(events)
            except Exception:
                failure_reason = "NEWS_SOURCE_SCHEMA_INVALID"
            else:
                health.update({
                    "status": "NEWS_VALID",
                    "reason_code": "NEWS_VALID",
                    "last_success_timestamp_utc": observed,
                    "retrieved_entry_count": count,
                })
                return source_candidate
        health.update({
            "status": failure_reason,
            "reason_code": failure_reason,
            "retrieved_entry_count": 0,
        })
        return candidate

    @staticmethod
    def _mark_candidate_failure(sources, previous_health, source_health):
        for source in sources:
            source_id = source["source_id"]
            health = source_health[source_id]
            if health["status"] == "NEWS_VALID":
                health.update({
                    "status": "NEWS_SOURCE_SCHEMA_INVALID",
                    "reason_code": "NEWS_SOURCE_SCHEMA_INVALID",
                    "last_success_timestamp_utc": previous_health[source_id][
                        "last_success_timestamp_utc"
                    ],
                    "retrieved_entry_count": 0,
                })

    @staticmethod
    def _source_status_summary(sources, source_health, now):
        successes = sum(
            source_health[source["source_id"]]["status"] == "NEWS_VALID"
            for source in sources
        )
        if successes:
            overall_status = (
                "NEWS_VALID" if successes == len(sources) else "NEWS_PARTIAL"
            )
        else:
            overall_status = "NEWS_ALL_SOURCES_FAILED"
        return successes, overall_status, now if successes else None

    @staticmethod
    def _finish_refreshing_health(sources, source_health):
        for source in sources:
            health = source_health[source["source_id"]]
            if health["status"] == "NEWS_REFRESHING":
                health.update({
                    "status": "NEWS_SOURCE_SCHEMA_INVALID",
                    "reason_code": "NEWS_SOURCE_SCHEMA_INVALID",
                    "retrieved_entry_count": 0,
                })

    def _build_refresh_result(
        self, sources, now, observed, registry, trusted_cache,
        source_health, previous_health,
    ):
        """Run all retrieval, parsing, and candidate work without the state lock."""
        candidate = copy.deepcopy(trusted_cache)
        diagnostic = None
        candidate_valid = True
        try:
            outcomes = self._collect_outcomes(sources, observed)
            for source in sources:
                candidate = self._apply_outcome(
                    candidate,
                    source,
                    outcomes[source["source_id"]],
                    observed,
                    source_health,
                )
            try:
                candidate = news_cache.prune_document(candidate, now, registry)
                candidate = news_cache.validate_document(candidate, now, registry)
                news_cache.deterministic_bytes(candidate)
            except Exception:
                candidate = copy.deepcopy(trusted_cache)
                self._mark_candidate_failure(
                    sources, previous_health, source_health,
                )
                candidate_valid = False
                diagnostic = "NEWS_CACHE_INVALID"
        except Exception:
            candidate = copy.deepcopy(trusted_cache)
            self._mark_candidate_failure(sources, previous_health, source_health)
            candidate_valid = False
        finally:
            self._finish_refreshing_health(sources, source_health)
        successes, overall_status, successful_time = self._source_status_summary(
            sources, source_health, now,
        )
        if not candidate_valid and diagnostic == "NEWS_CACHE_INVALID":
            overall_status = "NEWS_CACHE_INVALID"
        return {
            "cache": candidate,
            "candidate_valid": candidate_valid,
            "diagnostic": diagnostic,
            "last_success": successful_time,
            "overall_status": overall_status,
            "reason_code": overall_status,
            "source_health": source_health,
            "successes": successes,
        }

    def _clear_refresh_owner_locked(self, owner):
        if self._refresh_owner != owner:
            return False
        self._refresh_owner = None
        self._refreshing = False
        return True

    def _run_refresh(
        self, owner, now, observed, registry, trusted_cache,
        source_health, previous_health, cache_storage,
    ):
        """Own phases B/C and persistence for one unambiguous generation."""
        persistence_payload = None
        try:
            sources = list(registry["sources"])
            result = self._build_refresh_result(
                sources,
                now,
                observed,
                registry,
                trusted_cache,
                source_health,
                previous_health,
            )
            with self._lock:
                if self._refresh_owner != owner:
                    return
                if self._shutdown:
                    self._clear_refresh_owner_locked(owner)
                    return
                self._source_health = copy.deepcopy(result["source_health"])
                self._overall_status = result["overall_status"]
                self._reason_code = result["reason_code"]
                if result["last_success"] is not None:
                    self._last_success = result["last_success"]
                if result["diagnostic"] is not None:
                    self._diagnostics.append(result["diagnostic"])
                if result["candidate_valid"]:
                    self._cache = copy.deepcopy(result["cache"])
                    persistence_payload = copy.deepcopy(result["cache"])
            if persistence_payload is not None:
                persistence_status = "NEWS_VALID"
                try:
                    if cache_storage is None:
                        raise news_cache.CacheError("NEWS_CACHE_WRITE_FAILED")
                    cache_storage.write(persistence_payload)
                except Exception:
                    persistence_status = "NEWS_CACHE_WRITE_FAILED"
                with self._lock:
                    if self._refresh_owner == owner and not self._shutdown:
                        self._set_cache_persistence(persistence_status)
        except Exception:
            with self._lock:
                if self._refresh_owner == owner and not self._shutdown:
                    self._cache = copy.deepcopy(trusted_cache)
                    failed_health = copy.deepcopy(source_health)
                    self._finish_refreshing_health(
                        list(registry["sources"]), failed_health,
                    )
                    self._source_health = failed_health
                    self._overall_status = "NEWS_ALL_SOURCES_FAILED"
                    self._reason_code = "NEWS_ALL_SOURCES_FAILED"
        finally:
            with self._lock:
                self._clear_refresh_owner_locked(owner)

    def _refresh_if_permitted(self):
        if not self.configuration.enabled:
            return
        with self._lock:
            if self._shutdown:
                return
            self._initialize_enabled()
            if self._registry is None:
                return
            if self._refreshing:
                return
            now = _utc_now(self._clock)
            if self._last_attempt is not None:
                elapsed = (now - self._last_attempt).total_seconds()
                if elapsed < self.configuration.refresh_seconds:
                    self._reason_code = "NEWS_RATE_LIMITED_LOCALLY"
                    return
            self._last_attempt = now
            self._overall_status = "NEWS_REFRESHING"
            self._reason_code = "NEWS_REFRESHING"
            self._refreshing = True
            self._refresh_generation += 1
            owner = self._refresh_generation
            self._refresh_owner = owner
            observed = news_data.utc_timestamp(now)
            registry = copy.deepcopy(self._registry)
            sources = list(registry["sources"])
            trusted_cache = copy.deepcopy(self._cache)
            previous_health = copy.deepcopy(self._source_health)
            for source in sources:
                source_id = source["source_id"]
                self._source_health[source_id].update({
                    "status": "NEWS_REFRESHING",
                    "reason_code": "NEWS_REFRESHING",
                    "last_attempt_timestamp_utc": observed,
                    "retrieved_entry_count": 0,
                })
            source_health = copy.deepcopy(self._source_health)
            thread = threading.Thread(
                target=self._run_refresh,
                args=(
                    owner,
                    now,
                    observed,
                    registry,
                    trusted_cache,
                    source_health,
                    previous_health,
                    self._cache_storage,
                ),
                name="trl-news-coordinator-{}".format(owner),
                daemon=False,
            )
            self._refresh_thread = thread
            try:
                thread.start()
            except Exception:
                if self._refresh_thread is thread:
                    self._refresh_thread = None
                self._finish_refreshing_health(sources, self._source_health)
                self._overall_status = "NEWS_ALL_SOURCES_FAILED"
                self._reason_code = "NEWS_ALL_SOURCES_FAILED"
                self._clear_refresh_owner_locked(owner)

    def wait_for_refresh(self, timeout=SERVICE_REFRESH_SHUTDOWN_BOUND_SECONDS):
        with self._lock:
            thread = self._refresh_thread
        if thread is None or thread is threading.current_thread():
            return True
        thread.join(timeout)
        completed = not thread.is_alive()
        if completed:
            with self._lock:
                if self._refresh_thread is thread:
                    self._refresh_thread = None
        return completed

    def shutdown(self):
        """Cancel source children and join the one owned refresh coordinator."""
        with self._lock:
            self._shutdown = True
            connector = self._connector
            thread = self._refresh_thread
        if connector is not None:
            connector.close()
        if thread is not None and thread is not threading.current_thread():
            thread.join(SERVICE_REFRESH_SHUTDOWN_BOUND_SECONDS)
        with self._lock:
            if thread is None or not thread.is_alive():
                if self._refresh_thread is thread:
                    self._refresh_thread = None
                if self._refresh_owner is not None:
                    self._clear_refresh_owner_locked(self._refresh_owner)
                return True
            return False

    def _cache_freshness_status(self):
        if not self._cache or not self._cache["records"]:
            return "NEWS_ENABLED_NO_DATA"
        for wrapper in self._cache["records"]:
            source_id = wrapper["record"]["source_id"]
            health = self._source_health.get(source_id)
            if health is not None and health["status"] != "NEWS_VALID":
                return "NEWS_SOURCE_STALE"
        return "NEWS_VALID"

    def _project_record(self, wrapper):
        record = copy.deepcopy(wrapper["record"])
        health = self._source_health.get(record["source_id"], {})
        source_status = health.get("status", "NEWS_SOURCE_SCHEMA_INVALID")
        current = source_status == "NEWS_VALID"
        record.update({
            "operational_freshness_status": (
                "NEWS_RECORD_CURRENT" if current else "NEWS_RECORD_STALE"
            ),
            "latest_source_status": source_status,
            "latest_source_failure_reason": (
                None if current else health.get("reason_code", "NEWS_SOURCE_SCHEMA_INVALID")
            ),
            "latest_source_attempt_timestamp_utc": health.get(
                "last_attempt_timestamp_utc"
            ),
            "last_successfully_observed_timestamp_utc": wrapper[
                "last_seen_timestamp_utc"
            ],
        })
        return record

    def _disabled_health(self):
        return {
            "schema_version": HEALTH_SCHEMA,
            "enabled": False,
            "status": "NEWS_DISABLED",
            "reason_code": "NEWS_DISABLED",
            "refreshing": False,
            "last_successful_retrieval_utc": None,
            "next_permitted_refresh_utc": None,
            "refresh_interval_seconds": self.configuration.refresh_seconds,
            "source_health": [],
            "stable_health_codes": list(STABLE_HEALTH_CODES),
            "diagnostics": ["Official-news collection is disabled; no source or cache was initialized."],
            "network_request_count": 0,
            "cache_record_count": 0,
            "cache_freshness_status": "NEWS_DISABLED",
            **self._cache_persistence_fields(),
        }

    def health_document(self):
        if not self.configuration.enabled:
            return self._disabled_health()
        self._refresh_if_permitted()
        with self._lock:
            next_refresh = None
            if self._last_attempt is not None:
                next_refresh = news_data.utc_timestamp(
                    self._last_attempt + timedelta(seconds=self.configuration.refresh_seconds)
                )
            return {
                "schema_version": HEALTH_SCHEMA,
                "enabled": True,
                "status": self._overall_status,
                "reason_code": self._reason_code,
                "refreshing": self._refreshing,
                "last_successful_retrieval_utc": (
                    news_data.utc_timestamp(self._last_success) if self._last_success else None
                ),
                "next_permitted_refresh_utc": next_refresh,
                "refresh_interval_seconds": self.configuration.refresh_seconds,
                "source_health": [copy.deepcopy(self._source_health[key]) for key in sorted(self._source_health)],
                "stable_health_codes": list(STABLE_HEALTH_CODES),
                "diagnostics": list(self._diagnostics),
                "network_request_count": self._network_request_count,
                "cache_record_count": len(self._cache["records"]) if self._cache else 0,
                "cache_freshness_status": self._cache_freshness_status(),
                **self._cache_persistence_fields(),
            }

    def sources_document(self):
        if not self.configuration.enabled:
            return {
                "schema_version": news_sources.REGISTRY_VERSION,
                "enabled": False,
                "status": "NEWS_DISABLED",
                "refreshing": False,
                **self._cache_persistence_fields(),
                "sources": [],
            }
        self._refresh_if_permitted()
        with self._lock:
            sources = []
            for source in self._registry["sources"] if self._registry else ():
                item = copy.deepcopy(source)
                item["health"] = copy.deepcopy(
                    self._source_health[source["source_id"]]
                )
                sources.append(item)
            return {
                "schema_version": news_sources.REGISTRY_VERSION,
                "enabled": True,
                "status": self._overall_status,
                "refreshing": self._refreshing,
                **self._cache_persistence_fields(),
                "sources": sources,
            }

    def _records(self, kind):
        if not self.configuration.enabled:
            return []
        self._refresh_if_permitted()
        with self._lock:
            if self._cache is None:
                return []
            return [
                self._project_record(wrapper)
                for wrapper in self._cache["records"]
                if wrapper["kind"] == kind
            ]

    def news_items_document(self):
        records = self._records("news")
        records.sort(key=lambda item: (
            item["published_timestamp_utc"] or "", item["news_id"]
        ), reverse=True)
        with self._lock:
            return {
                "schema_version": news_data.NEWS_COLLECTION_SCHEMA,
                "enabled": self.configuration.enabled,
                "status": self._overall_status if self.configuration.enabled else "NEWS_DISABLED",
                "refreshing": self._refreshing,
                **self._cache_persistence_fields(),
                "items": records[:MAX_API_RECORDS],
            }

    def economic_events_document(self):
        records = self._records("event")
        records.sort(key=lambda item: (
            item["scheduled_timestamp_utc"],
            item["event_series_id"],
            item["event_id"],
        ))
        with self._lock:
            return {
                "schema_version": news_data.EVENT_COLLECTION_SCHEMA,
                "enabled": self.configuration.enabled,
                "status": self._overall_status if self.configuration.enabled else "NEWS_DISABLED",
                "refreshing": self._refreshing,
                **self._cache_persistence_fields(),
                "events": records[:MAX_API_RECORDS],
            }


_DISABLED_SERVICE = OfficialNewsService()


def disabled_service():
    return _DISABLED_SERVICE
