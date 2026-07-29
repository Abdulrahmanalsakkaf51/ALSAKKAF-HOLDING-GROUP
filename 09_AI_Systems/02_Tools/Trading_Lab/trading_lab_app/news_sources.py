"""Fail-closed loader for the immutable TRL-R2-004 source registry."""

import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit


REGISTRY_PATH = Path(__file__).resolve().parent / "official_news_sources.json"
REGISTRY_VERSION = "TRL-OFFICIAL-NEWS-SOURCES-1.1"
EXPECTED_SOURCE_ENDPOINTS = {
    "FED_MONETARY_POLICY_RSS": "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "BLS_LATEST_RELEASES_RSS": "https://www.bls.gov/feed/bls_latest.rss",
    "BEA_NEWS_RELEASE_RSS": "https://apps.bea.gov/rss/rss.xml",
    "BEA_RELEASE_DATES_JSON": "https://apps.bea.gov/API/signup/release_dates.json",
    "ECB_PRESS_RELEASE_RSS": "https://www.ecb.europa.eu/rss/press.html",
    "ECB_STATISTICAL_RELEASE_RSS": "https://www.ecb.europa.eu/rss/statpress.html",
}
EXPECTED_ITEM_LINK_HOSTNAMES = {
    "FED_MONETARY_POLICY_RSS": ("www.federalreserve.gov",),
    "BLS_LATEST_RELEASES_RSS": ("www.bls.gov",),
    "BEA_NEWS_RELEASE_RSS": ("www.bea.gov",),
    "BEA_RELEASE_DATES_JSON": ("www.bea.gov",),
    "ECB_PRESS_RELEASE_RSS": ("www.ecb.europa.eu",),
    "ECB_STATISTICAL_RELEASE_RSS": ("www.ecb.europa.eu",),
}
EXPECTED_SOURCE_RECORD_SHA256 = {
    "FED_MONETARY_POLICY_RSS": "fe0e97fb17e2a5d407afaebfa98c27340e347aa81a6b5e8451396e11203e1fa6",
    "BLS_LATEST_RELEASES_RSS": "0d151b92558af483eaee1d9fc873d4135b616c691db9a4629ad9c2394e1571ee",
    "BEA_NEWS_RELEASE_RSS": "52f5f3a9c6ecbde5a9591cd09cfef021f91331ad7d0100d719c508bcc5f9437f",
    "BEA_RELEASE_DATES_JSON": "f2f876cc0e6f46a3648c2f9b3a922ca8ab5d7b1a28c39c3c403f74f42a5d3720",
    "ECB_PRESS_RELEASE_RSS": "8008f7b76a2fcd83077350a4a34cd20926195e3072a35d247c9085f366b69fd7",
    "ECB_STATISTICAL_RELEASE_RSS": "07f76afaa0b087111e4a0a4f9fb1ad2f786e7457d26c90b442626282aa8b4b48",
}
REQUIRED_SOURCE_FIELDS = frozenset((
    "source_id", "publisher", "official_homepage", "exact_endpoint",
    "exact_hostname", "exact_path", "format", "country_or_region",
    "currency_tags", "source_category", "authentication_requirement",
    "local_retrieval_permission_status", "redistribution_status",
    "full_text_retention_status", "source_terms_review_status",
    "terms_review_date", "enabled_by_checkpoint_status", "limitations",
    "permitted_item_link_hostnames",
))


class SourceRegistryError(ValueError):
    """The committed source registry is incompatible or has changed."""


def _source_record_digest(source):
    try:
        encoded = json.dumps(
            source,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as error:
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED") from error
    return hashlib.sha256(encoded).hexdigest()


def validated_endpoint_parts(source):
    """Validate the complete compiled source identity and derive its destination."""
    if type(source) is not dict or set(source) != REQUIRED_SOURCE_FIELDS:
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    source_id = source.get("source_id")
    endpoint_value = source.get("exact_endpoint")
    if (
        type(source_id) is not str
        or type(endpoint_value) is not str
        or EXPECTED_SOURCE_ENDPOINTS.get(source_id) != endpoint_value
        or EXPECTED_SOURCE_RECORD_SHA256.get(source_id) != _source_record_digest(source)
    ):
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    try:
        endpoint = urlsplit(endpoint_value)
        port = endpoint.port
    except (TypeError, ValueError) as error:
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED") from error
    if (
        endpoint.scheme != "https"
        or endpoint.username is not None
        or endpoint.password is not None
        or port is not None
        or endpoint.query
        or endpoint.fragment
        or not endpoint.hostname
        or not endpoint.path
        or endpoint.netloc != endpoint.hostname
        or source.get("exact_hostname") != endpoint.hostname
        or source.get("exact_path") != endpoint.path
    ):
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    return endpoint.hostname, endpoint.path


def _reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
        result[key] = value
    return result


def load_source_registry(path=REGISTRY_PATH):
    """Load a fresh validated registry; no network operation occurs."""
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="strict")
        document = json.loads(raw, object_pairs_hook=_reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED") from error
    if set(document) != {"immutable", "registry_version", "sources"}:
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    if document["immutable"] is not True or document["registry_version"] != REGISTRY_VERSION:
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    sources = document["sources"]
    if type(sources) is not list or len(sources) != len(EXPECTED_SOURCE_ENDPOINTS):
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    seen = set()
    for source in sources:
        try:
            endpoint_hostname, endpoint_path = validated_endpoint_parts(source)
        except SourceRegistryError as error:
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED") from error
        source_id = source["source_id"]
        if source_id in seen:
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
        seen.add(source_id)
        item_link_hostnames = source["permitted_item_link_hostnames"]
        homepage = urlsplit(source["official_homepage"])
        if (
            endpoint_hostname != source["exact_hostname"]
            or endpoint_path != source["exact_path"]
            or homepage.scheme != "https" or not homepage.hostname
            or source["authentication_requirement"] != "NO_API_KEY_REQUIRED"
            or source["local_retrieval_permission_status"] != "LOCAL_RETRIEVAL_ONLY"
            or source["redistribution_status"] != "REDISTRIBUTION_NOT_AUTHORIZED"
            or source["terms_review_date"] != "2026-07-27"
            or source["format"] not in {"RSS/XML", "JSON"}
            or type(source["currency_tags"]) is not list
            or not source["currency_tags"]
            or type(item_link_hostnames) is not list
            or tuple(item_link_hostnames) != EXPECTED_ITEM_LINK_HOSTNAMES.get(source_id)
        ):
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
        required_labels = {
            "OFFICIAL_PUBLISHER", "TERMS_CAN_CHANGE",
            "SOURCE_NOT_CERTIFIED_BY_ALSAKKAF",
        }
        if not required_labels.issubset(set(source["source_terms_review_status"])):
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
        if set(source["full_text_retention_status"]) != {
            "FULL_TEXT_NOT_RETAINED", "TITLE_LINK_METADATA_ONLY",
        }:
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    if seen != set(EXPECTED_SOURCE_ENDPOINTS):
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    return copy.deepcopy(document)


def validated_source_map(registry):
    """Return immutable compiled sources keyed by ID after complete revalidation."""
    if (
        type(registry) is not dict
        or set(registry) != {"immutable", "registry_version", "sources"}
        or registry.get("immutable") is not True
        or registry.get("registry_version") != REGISTRY_VERSION
        or type(registry.get("sources")) is not list
        or len(registry["sources"]) != len(EXPECTED_SOURCE_ENDPOINTS)
    ):
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    result = {}
    for source in registry["sources"]:
        validated_endpoint_parts(source)
        source_id = source["source_id"]
        if source_id in result:
            raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
        result[source_id] = source
    if set(result) != set(EXPECTED_SOURCE_ENDPOINTS):
        raise SourceRegistryError("NEWS_PROVIDER_CHANGED")
    return copy.deepcopy(result)


def endpoint_is_allowlisted(source, endpoint):
    """Require the exact immutable HTTPS endpoint without query data."""
    if type(endpoint) is not str:
        return False
    try:
        validated_endpoint_parts(source)
    except SourceRegistryError:
        return False
    return endpoint == source["exact_endpoint"]


def item_link_host_is_allowlisted(source, hostname):
    """Apply the independent immutable article-link host policy."""
    try:
        validated_endpoint_parts(source)
    except SourceRegistryError:
        return False
    source_id = source["source_id"]
    declared = source.get("permitted_item_link_hostnames")
    expected = EXPECTED_ITEM_LINK_HOSTNAMES.get(source_id)
    return (
        type(hostname) is str
        and type(declared) is list
        and tuple(declared) == expected
        and hostname in expected
    )
