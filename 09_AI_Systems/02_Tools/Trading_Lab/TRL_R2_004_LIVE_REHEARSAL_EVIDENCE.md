# TRL-R2-004 Live Rehearsal and Compatibility Evidence

> **SANITIZED METADATA EVIDENCE ONLY - NO RAW PUBLISHER BODIES - NO LIVE FIX VALIDATION**

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-004-LIVE-REHEARSAL-EVIDENCE-001 |
| Document Type | Controlled Rehearsal and Offline Compatibility Evidence |
| Status | SECOND CONTROLLED REHEARSAL RECORDED; LIVE-FIX-05 UNCOMMITTED |
| Version | 1.1 |
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

## Second Controlled Rehearsal Result

This section is a separate historical observation and does not alter the first committed rehearsal above. The application at commit `4c15810` performed exactly six governed source requests at retrieval timestamp `2026-07-30T01:32:35.629179Z`, with no retry. It returned overall `NEWS_PARTIAL`; subsequent health access reported `NEWS_RATE_LIMITED_LOCALLY`. Cache persistence remained `NEWS_VALID`, and the combined cache contained 182 records.

| Source | Governed result | Records |
|---|---|---:|
| BEA_NEWS_RELEASE_RSS | `NEWS_SOURCE_HTTP_ERROR` | 0 |
| BEA_RELEASE_DATES_JSON | `NEWS_VALID` | 136 economic events |
| BLS_LATEST_RELEASES_RSS | `NEWS_VALID` | 1 metadata-only news item |
| ECB_PRESS_RELEASE_RSS | `NEWS_VALID` | 15 news items |
| ECB_STATISTICAL_RELEASE_RSS | `NEWS_VALID` | 15 news items |
| FED_MONETARY_POLICY_RSS | `NEWS_VALID` | 15 news items |

The API collections contained 46 news records and 136 economic events. BEA events were chronologically ordered, and `file_last_updated` did not become an event. The BLS record retained zero description, summary, content, creator, body, or image fields. API reads did not trigger another retrieval: the final request count remained exactly six.

The application stopped through Ctrl+C. Port 8765 had no listener afterward, and Git remained clean on `4c15810`. This was a controlled partial result, not a complete six-source pass. Live evidence did not prove the low-level BEA RSS cause. Subsequent offline diagnosis confirmed uncontrolled same-host concurrency as an architectural susceptibility and evidence-compatible explanation, not proof of publisher policy.

No raw publisher body, credential, MT5, broker, account, position, order, strategy, signal, or cloud data was retained. This evidence is not publisher certification, production authorization, trading advice, or profitability evidence.

## Follow-Up Rehearsal State

The second controlled rehearsal is recorded above. Another live rehearsal remains pending and may be separately authorized only after LIVE-FIX-05 independent review and commit. LIVE-FIX-05 implementation and automated validation authorize no external access or rehearsal.

TRL-R2-005 remains unauthorized and has not begun.

## Final Controlled Live Rehearsal Result

This section is a separate final-rehearsal observation. It preserves both historical rehearsal sections above unchanged. The authorized baseline was commit `a0c7a4a` on branch `codex/TRL-R2-004-live-compatibility`. All mandatory local prechecks passed before the application was started: the exact worktree, branch, commit, clean index and worktree, absence of untracked files and mode changes, free port 8765, absence of a Trading Lab Python process, six complete compiled source identities and unchanged endpoints, disabled-by-default official news, disabled MT5, literal `127.0.0.1` binding, and a unique nonexistent operating-system-temporary cache target were confirmed.

The production application was started with official news explicitly enabled, MT5 disabled, no browser, the committed 900-second refresh interval, and the isolated production-derived cache location. The normal localhost health path triggered one eligible refresh. The orchestration command was then terminated by its command-runner timeout after 1.681 seconds, before the final health document and sanitized source outcomes were captured. No second eligible refresh, retry, extra probe, direct publisher request, browser operation, DNS diagnostic, MT5 operation, or other external operation was initiated. Because the in-memory `network_request_count` was lost, exactly six requests and zero retries are **not confirmed** and must not be inferred from cache persistence.

| Field | Final rehearsal observation |
|---|---|
| Baseline commit | `a0c7a4a` |
| Branch | `codex/TRL-R2-004-live-compatibility` |
| UTC rehearsal/cache timestamp | `2026-07-30T20:52:43.90341Z` |
| Exact application duration | Not recoverable; the orchestration command was terminated after 1.681 seconds |
| Overall status / reason code | Not captured |
| Final refreshing state | Not captured |
| Network request count | Not captured; exactly six cannot be confirmed |
| Retry count | Not captured; zero cannot be confirmed |
| Cache persistence status / reason | Health fields not captured; a deterministic valid empty cache file was present |
| Cache freshness | Not captured |
| Cache schema and records | `TRL-OFFICIAL-NEWS-CACHE-1.0`; 0 records |
| News collection schema / status / items | Not captured / not captured / 0 retained in cache |
| Economic-event collection schema / status / events | Not captured / not captured / 0 retained in cache |

The exact per-source production health outcomes were not captured. The deterministic cache retained zero records for every governed source:

| Source | Production status | Production reason | Retained records |
|---|---|---|---:|
| FED_MONETARY_POLICY_RSS | Not captured | Not captured | 0 |
| BLS_LATEST_RELEASES_RSS | Not captured | Not captured | 0 |
| BEA_NEWS_RELEASE_RSS | Not captured | Not captured | 0 |
| BEA_RELEASE_DATES_JSON | Not captured | Not captured | 0 |
| ECB_PRESS_RELEASE_RSS | Not captured | Not captured | 0 |
| ECB_STATISTICAL_RELEASE_RSS | Not captured | Not captured | 0 |

The committed production cache validator accepted the serialized empty cache. Reload preserved its record count, record order, IDs, fingerprints, revisions, and schemas, and deterministic reserialization was byte-identical. Because it contained no records, the event ordering, equivalent-timestamp deduplication, unique-event-ID, and `file_last_updated` checks were vacuously true only; they do not establish live publisher compatibility. `file_last_updated` produced zero retained events. There were no retained URLs to assess. There was no retained BLS record, so the required metadata-only BLS observation and forbidden-field retention check could not be established.

The application process tree was terminated by the command runner rather than completing the controlled application shutdown path; no `Local dashboard stopped.` confirmation was captured. This fails the clean controlled shutdown criterion. Final local inspection found no listener on port 8765 and no Python process. The one cache file and its exact empty temporary hierarchy were removed, no temporary sibling existed, no relevant operating-system-temp artifact remained, and no repository artifact was generated. Before this evidence append, the Git worktree and index were clean. After the append, the intended final inventory is this evidence document as the only worktree modification with an empty index.

The final success criteria **failed** because the exact request count, retry count, final overall health, six source statuses, collection documents, BLS metadata-only record, URL-governance result, and clean application shutdown were not captured or established. This is a bounded compatibility observation only. It is not publisher certification, profitability evidence, financial advice, trading authorization, or production execution approval.

**R2-004 FINAL LIVE REHEARSAL FAILED**

## Final Manual Replacement Rehearsal at a0c7a4a

This section records the final manual replacement rehearsal. All preceding historical rehearsal sections, including the first historical observation, the second controlled observation at `4c15810`, and the aborted command-runner rehearsal, are preserved unchanged.

### Baseline

- Branch: `codex/TRL-R2-004-live-compatibility`
- Commit: `a0c7a4a`
- Rehearsal start: `2026-07-30T22:39:53.8241088Z`
- Rehearsal completion: `2026-07-30T22:39:56.8571406Z`
- Duration: `3.0330318` seconds
- Production localhost application
- Official news enabled
- MT5 disabled
- Isolated OS-temporary cache
- Exactly six requests
- Zero retries

### Overall result

- Status: `NEWS_PARTIAL`
- Final reason: `NEWS_RATE_LIMITED_LOCALLY`
- Refreshing: `false`
- Cache persistence: `NEWS_VALID`
- Cache freshness: `NEWS_VALID`
- Cache records: `182`
- News items: `46`
- Economic events: `136`

### Source outcomes

1. `BEA_NEWS_RELEASE_RSS`
   - `NEWS_SOURCE_HTTP_ERROR`
   - 0 retained records
   - No successful timestamp

2. `BEA_RELEASE_DATES_JSON`
   - `NEWS_VALID`
   - 136 economic events

3. `BLS_LATEST_RELEASES_RSS`
   - `NEWS_VALID`
   - 1 metadata-only news item

4. `ECB_PRESS_RELEASE_RSS`
   - `NEWS_VALID`
   - 15 news items

5. `ECB_STATISTICAL_RELEASE_RSS`
   - `NEWS_VALID`
   - 15 news items

6. `FED_MONETARY_POLICY_RSS`
   - `NEWS_VALID`
   - 15 news items

### Verified properties

- Exactly six source results captured.
- Exactly six network requests.
- Zero retries.
- Five sources valid.
- BEA release-date events valid.
- BLS metadata-only retention passed.
- Economic events were chronologically ordered.
- `file_last_updated` produced no event.
- Governed URL validation passed.
- Cache persistence succeeded.
- No full publisher content was retained.
- No MT5 or trading operation occurred.

### Shutdown and cleanup

- Application reported “Shutdown requested.”
- Application reported “Local dashboard stopped.”
- Port 8765 listeners: 0.
- Relevant Python/Trading Lab processes: 0.
- Isolated temporary directory remained: false.
- Repository artifacts: 0.
- Final Git scope contained only this evidence-document modification.
- Index remained empty.

### Required interpretation

The all-six-source success criterion failed. This rehearsal must not be labelled fully passed. Hostname serialization did not resolve BEA RSS compatibility. The low-level BEA RSS failure cause remains unproven. No additional live probe or retry was performed. Five governed sources operated successfully. The application behaved correctly in degraded `NEWS_PARTIAL` mode. The valid BEA JSON calendar still supplied 136 economic events. This is evidence of bounded interoperability, not publisher certification. It is not profitability evidence, financial advice, trading authorization or live-execution approval.

### Closure decision

TRL-R2-004 is accepted and closed with a known `BEA_NEWS_RELEASE_RSS` compatibility limitation.

The limitation is deferred to a future separately governed maintenance checkpoint. It will not block the forward paper-trading and Signal Desk roadmap.

No schema, source identity, endpoint, health code or production behavior was changed to implement this closure decision.
