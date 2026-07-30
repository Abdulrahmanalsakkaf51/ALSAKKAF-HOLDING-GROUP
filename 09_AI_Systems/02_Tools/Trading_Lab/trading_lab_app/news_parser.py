"""Bounded standard-library parsers for narrow RSS, Atom, and BEA metadata."""

import json
import re
import unicodedata
import xml.etree.ElementTree as element_tree

from . import news_data


MAX_RESPONSE_BYTES = 1024 * 1024
MAX_ENTRIES = 200
MAX_XML_ELEMENTS = 5000
MAX_XML_DEPTH = 24
MAX_JSON_DEPTH = 16
MAX_JSON_COLLECTION = 2000
MAX_STRING_LENGTH = 4096
MAX_NONRETAINED_DESCRIPTION_LENGTH = 64 * 1024
_UNSAFE_XML = re.compile(br"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
def safe_title(value):
    return news_data.canonical_title(value)


def _local_name(tag):
    if type(tag) is not str or not tag:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    local = tag.rsplit("}", 1)[-1]
    if not local:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    return local.lower()


def _child(element, names):
    for child in element:
        if _local_name(child.tag) in names:
            return child
    return None


def _required_timestamp_text(element):
    value = _element_text(element)
    if value is None:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    return value


def _atom_publication_timestamp(entry):
    published = _child(entry, {"published"})
    if published is not None:
        return news_data.parse_source_timestamp(
            _required_timestamp_text(published)
        )
    updated = _child(entry, {"updated"})
    if updated is not None:
        return news_data.parse_source_timestamp(
            _required_timestamp_text(updated)
        )
    return None


def _rss_publication_timestamp(item):
    pubdate = _child(item, {"pubdate"})
    if pubdate is not None:
        return news_data.parse_source_timestamp(
            _required_timestamp_text(pubdate)
        )
    date = _child(item, {"date"})
    if date is not None:
        return news_data.parse_source_timestamp(
            _required_timestamp_text(date)
        )
    return None


def _atom_alternate_link(entry):
    candidates = []
    html_types = {"text/html", "application/xhtml+xml"}
    for position, child in enumerate(entry):
        if _local_name(child.tag) != "link":
            continue
        relation = child.attrib.get("rel")
        if relation is not None and relation.strip().lower() != "alternate":
            continue
        href = child.attrib.get("href")
        if type(href) is not str or not href.strip():
            continue
        media_type = child.attrib.get("type")
        normalized_type = (
            media_type.strip().lower()
            if type(media_type) is str and media_type.strip() else None
        )
        base_type = (
            normalized_type.split(";", 1)[0].strip()
            if normalized_type is not None else None
        )
        if base_type in html_types:
            rank = 0
        elif normalized_type is None:
            rank = 1
        else:
            rank = 2
        candidates.append((rank, position, href))
    if not candidates:
        return None
    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
    return candidates[0][2]


def _element_text(element):
    if element is None:
        return None
    value = "".join(element.itertext()).strip()
    return value or None


def _sanitized_title_tree_text(element):
    """Flatten safe title subtrees while preserving only safe following tails."""
    if element is None:
        return None

    def safe_parts(current):
        name = _local_name(current.tag)
        if (
            news_data.title_tag_has_governed_component(
                name, news_data.BLOCKED_TITLE_CONTAINERS
            )
            or news_data.title_tag_has_governed_component(
                name, news_data.DISCARDED_VOID_TITLE_ELEMENTS
            )
        ):
            return []
        parts = []
        if current.text:
            parts.append(current.text)
        for child in current:
            parts.extend(safe_parts(child))
            if child.tail:
                parts.append(child.tail)
        return parts

    value = "".join(safe_parts(element)).strip()
    return value or None


def _validate_xml_tree(root):
    count = 0
    stack = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        count += 1
        if count > MAX_XML_ELEMENTS or depth > MAX_XML_DEPTH:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        if len(element.attrib) > 20:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        text_limit = (
            MAX_NONRETAINED_DESCRIPTION_LENGTH
            if _local_name(element.tag) == "description"
            else MAX_STRING_LENGTH
        )
        if element.text is not None and len(element.text) > text_limit:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        if element.tail is not None and len(element.tail) > MAX_STRING_LENGTH:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        stack.extend((child, depth + 1) for child in element)


def parse_xml_news(body, source, retrieved_timestamp_utc):
    if type(body) is not bytes or len(body) > MAX_RESPONSE_BYTES:
        raise news_data.NewsValidationError("NEWS_SOURCE_TOO_LARGE")
    if _UNSAFE_XML.search(body):
        raise news_data.NewsValidationError("NEWS_SOURCE_XML_UNSAFE")
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise news_data.NewsValidationError("NEWS_SOURCE_UTF8_INVALID") from error
    try:
        root = element_tree.fromstring(text)
    except element_tree.ParseError as error:
        raise news_data.NewsValidationError("NEWS_SOURCE_PARSE_ERROR") from error
    _validate_xml_tree(root)
    entries = [element for element in root.iter() if _local_name(element.tag) in {"item", "entry"}]
    if len(entries) > MAX_ENTRIES:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    result = []
    for entry in entries:
        entry_kind = _local_name(entry.tag)
        title_value = _sanitized_title_tree_text(_child(entry, {"title"}))
        if title_value is None:
            continue
        if entry_kind == "entry":
            link = _atom_alternate_link(entry)
            published = _atom_publication_timestamp(entry)
        else:
            link_element = _child(entry, {"link"})
            link = None
            if link_element is not None:
                link = link_element.attrib.get("href") or _element_text(link_element)
            published = _rss_publication_timestamp(entry)
        result.append(news_data.news_item(
            source, safe_title(title_value), link,
            published, retrieved_timestamp_utc,
        ))
    return result


def _duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        result[key] = value
    return result


def _nonfinite(value):
    raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")


def _validate_json(value, depth=1):
    if depth > MAX_JSON_DEPTH:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    if type(value) is list:
        if len(value) > MAX_JSON_COLLECTION:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        for item in value:
            _validate_json(item, depth + 1)
    elif type(value) is dict:
        if len(value) > MAX_JSON_COLLECTION:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        for key, item in value.items():
            _validate_json(key, depth + 1)
            _validate_json(item, depth + 1)


def _release_rows(document):
    if type(document) is dict and set(document) == {"release_dates"}:
        return document["release_dates"]
    if type(document) is dict and set(document) == {"BEAAPI"}:
        api = document["BEAAPI"]
        if type(api) is dict and set(api) == {"Results"}:
            results = api["Results"]
            if type(results) is dict and set(results) == {"ReleaseDates"}:
                return results["ReleaseDates"]
    raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")


def _bounded_publisher_metadata_timestamp(value):
    if (
        type(value) is not str
        or not value
        or len(value) > 100
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")


def _strict_product_name(value):
    if (
        type(value) is not str
        or not value
        or len(value) > news_data.MAX_TITLE_INPUT_LENGTH
        or any(unicodedata.category(character) in {"Cc", "Cf"} for character in value)
    ):
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID") from error
    canonical = safe_title(value)
    if canonical != value:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    return canonical


def _product_release_events(document, source, retrieved_timestamp_utc):
    if type(document) is not dict or "file_last_updated" not in document:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    _bounded_publisher_metadata_timestamp(document["file_last_updated"])
    products = [
        (name, value) for name, value in document.items()
        if name != "file_last_updated"
    ]
    if len(products) > MAX_ENTRIES:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    result = []
    raw_release_date_count = 0
    unique_occurrence_count = 0
    for name, value in products:
        if type(value) is not dict or set(value) != {"release_dates"}:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        release_dates = value["release_dates"]
        if type(release_dates) is not list:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        product_name = _strict_product_name(name)
        if len(release_dates) > MAX_ENTRIES - raw_release_date_count:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        raw_release_date_count += len(release_dates)
        normalized_dates = set()
        for scheduled in release_dates:
            normalized_dates.add(news_data.parse_rfc3339_timestamp(scheduled))
        if len(normalized_dates) > MAX_ENTRIES - unique_occurrence_count:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        unique_occurrence_count += len(normalized_dates)
        for strict_scheduled in sorted(
            normalized_dates, key=news_data.chronological_timestamp_key,
        ):
            result.append(news_data.economic_event(
                source, product_name, strict_scheduled, None,
                retrieved_timestamp_utc, None,
            ))
    return sorted(result, key=lambda event: (
        news_data.chronological_timestamp_key(
            event["scheduled_timestamp_utc"]
        ),
        event["event_series_id"],
        event["event_id"],
    ))


def _pick(row, names, required=False):
    matches = [row[name] for name in names if name in row]
    if len(matches) > 1:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    if not matches:
        if required:
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        return None
    return matches[0]


def parse_bea_release_dates(body, source, retrieved_timestamp_utc):
    if type(body) is not bytes or len(body) > MAX_RESPONSE_BYTES:
        raise news_data.NewsValidationError("NEWS_SOURCE_TOO_LARGE")
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise news_data.NewsValidationError("NEWS_SOURCE_UTF8_INVALID") from error
    try:
        document = json.loads(
            text, object_pairs_hook=_duplicate_object, parse_constant=_nonfinite,
        )
    except (json.JSONDecodeError, RecursionError) as error:
        raise news_data.NewsValidationError("NEWS_SOURCE_PARSE_ERROR") from error
    try:
        _validate_json(document)
    except RecursionError as error:
        raise news_data.NewsValidationError("NEWS_SOURCE_PARSE_ERROR") from error
    if type(document) is dict and "file_last_updated" in document:
        return _product_release_events(
            document, source, retrieved_timestamp_utc,
        )
    rows = _release_rows(document)
    if type(rows) is not list or len(rows) > MAX_ENTRIES:
        raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    result = []
    allowed = {
        "ReleaseDate", "release_date", "scheduled_timestamp_utc",
        "ReleaseName", "release_name", "event_name", "ReleaseURL", "url",
        "source_url", "Published", "published_timestamp_utc", "actual",
        "forecast", "previous", "importance",
    }
    for row in rows:
        if type(row) is not dict or not set(row).issubset(allowed):
            raise news_data.NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        name = _pick(row, ("ReleaseName", "release_name", "event_name"), required=True)
        scheduled = _pick(row, ("ReleaseDate", "release_date", "scheduled_timestamp_utc"), required=True)
        published = _pick(row, ("Published", "published_timestamp_utc"))
        url = _pick(row, ("ReleaseURL", "url", "source_url"))
        result.append(news_data.economic_event(
            source, safe_title(name), scheduled, published,
            retrieved_timestamp_utc, url,
            {field: row.get(field) for field in ("actual", "forecast", "previous", "importance")},
        ))
    return result
