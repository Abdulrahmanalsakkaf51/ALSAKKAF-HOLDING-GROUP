# TRL-R2-004 Live Rehearsal and Compatibility Evidence

> **SANITIZED METADATA EVIDENCE ONLY - NO RAW PUBLISHER BODIES - NO LIVE FIX VALIDATION**

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-004-LIVE-REHEARSAL-EVIDENCE-001 |
| Document Type | Controlled Rehearsal and Offline Compatibility Evidence |
| Status | LIVE-FIX-01 IMPLEMENTED; FOLLOW-UP LIVE REHEARSAL NOT PERFORMED |
| Version | 1.0 |
| Date | 2026-07-30 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Baseline commit | `a2f3cf9` |
| Branch | `codex/TRL-R2-004-live-compatibility` |

## Authorization and Boundary

Founder Abdulrahman Yaseen Alsakkaf authorized `TRL-R2-004-LIVE-FIX-01` after the committed TRL-R2-004 rehearsal returned a governed partial result. The authorization permits narrow local compatibility for the observed BEA release-date mapping and metadata-only RSS structures, followed later by one separately operated controlled rehearsal against the same six governed endpoints.

LIVE-FIX-01 does not authorize new endpoints, arbitrary URLs, webpage scraping, article-body retention, credentials, paid services, strategies, signals, advice, broker activity, orders, execution, accounts, cloud services, subscriptions, telemetry, or TRL-R2-005. Implementation and automated validation used sanitized synthetic fixtures and injected transports only. No internet, DNS, publisher, MT5, broker, or external API access was performed.

## Committed Live Rehearsal Result

The committed application at `a2f3cf9` ran with official news enabled and MT5 disabled. It made exactly six requests, persisted a `NEWS_VALID` cache containing 45 records, and returned overall `NEWS_PARTIAL`. A local retry was correctly blocked by `NEWS_RATE_LIMITED_LOCALLY`. Shutdown completed through Ctrl+C, port 8765 was no longer listening, and Git remained clean.

| Source | Governed result | Records |
|---|---|---:|
| FED_MONETARY_POLICY_RSS | `NEWS_VALID` | 15 |
| ECB_PRESS_RELEASE_RSS | `NEWS_VALID` | 15 |
| ECB_STATISTICAL_RELEASE_RSS | `NEWS_VALID` | 15 |
| BEA_NEWS_RELEASE_RSS | `NEWS_SOURCE_HTTP_ERROR` | 0 |
| BEA_RELEASE_DATES_JSON | `NEWS_SOURCE_SCHEMA_INVALID` | 0 |
| BLS_LATEST_RELEASES_RSS | `NEWS_SOURCE_SCHEMA_INVALID` | 0 |

The retained collection schema was `TRL-OFFICIAL-NEWS-COLLECTION-1.2`. All 45 retained records were governed title/link/time metadata. No article bodies or economic events were retained.

## Sanitized Structural Observations

No raw response body is included in this repository.

| Source | Status and content type | Size | Sanitized structure | SHA-256 |
|---|---|---:|---|---|
| BEA news RSS | HTTP 200; `text/xml`; no redirect; no DTD/entity declaration | 84,866 bytes | RSS root; 46 items; direct fields included `dbid`, `title`, `link`, `guid`, `description`, `data`, `nextreleasedate`, `unitsofmeasure`, `changeunit`, `linkhistoric`, `linkarchive`, `pdf`, and `pubdate`; governed `www.bea.gov` links; named EDT publication dates | `c863977d1675c6da40a4ce77c30d34cc52b8b1c18376b189d8827f8092b2a245` |
| BEA release dates | HTTP 200; `application/json`; no redirect | 9,053 bytes | Top-level object; product-name keys mapped to exact `release_dates` arrays of RFC3339 timestamps; reserved `file_last_updated` metadata key | `a6541c6003af77ce6d151d97f1503475bf63caccc305bad7a9300f934a95c752` |
| BLS latest RSS | HTTP 200; `application/rss+xml`; no redirect | 5,333 bytes | RSS root; one item; governed `https://www.bls.gov/bls/` link; numeric-offset publication date; publisher creator metadata; 4,589-character description not authorized for retention | `2ea38e576b2dc5214ca490f3a421a2e994b0cdeb869953322bb6f2ce449776b0` |

## LIVE-FIX-01 Compatibility Decision

- BEA product mappings expand each strict RFC3339 value into one existing economic-event occurrence. Product names use the existing bounded title canonicalizer. The combined result remains capped at 200 entries. `file_last_updated` is bounded and validated but is neither retained nor treated as an event.

- RSS timestamp parsing adds only uppercase `EDT` and `EST` to the existing strict GMT, UTC, and numeric-offset grammar. Arbitrary named timezone abbreviations remain invalid.

- RSS `description` text may pass structural validation only within 64 KiB and the existing 1 MiB response limit. It is never selected, copied, cached, returned by an API, or written into evidence. Other XML text remains bounded at 4,096 characters, and retained titles remain bounded at 500 canonical characters.

- Exact endpoints, source registry records and digests, item-link host allowlists, response content-type policy, cache schema, public item/event/collection schemas, health codes, throttling, and disabled-by-default behavior remain unchanged.

## Offline Automated Evidence

Focused validation used five local tests covering the observed compatible shapes, strict rejection boundaries, no description or publisher-metadata retention, and one six-source refresh through an injected transport. Result: **5 tests passed**.

The fixtures were constructed synthetic metadata. They contained no copied publisher response body and opened no network connection. The injected refresh recorded exactly six governed transport calls and returned `NEWS_VALID`, 50 synthetic news metadata records, and three synthetic BEA occurrences. The synthetic record count is test-only and is not presented as a publisher result.

Complete local validation ran `python -B -W error -m unittest test_news_events.py test_trading_lab_app.py`. Result: **120 tests passed in 38.565 seconds**. Bytecode generation was disabled, warnings were treated as errors, and no production cache or external transport was used.

## Follow-Up Rehearsal State

The separately operated controlled follow-up rehearsal was not performed during LIVE-FIX-01 implementation or automated validation. It remains limited to the same six governed endpoints and must follow the stop conditions in `TRL_OFFICIAL_NEWS_SETUP_GUIDE.md`. No additional rehearsal is authorized by LIVE-FIX-01.

TRL-R2-005 remains unauthorized and has not begun.
