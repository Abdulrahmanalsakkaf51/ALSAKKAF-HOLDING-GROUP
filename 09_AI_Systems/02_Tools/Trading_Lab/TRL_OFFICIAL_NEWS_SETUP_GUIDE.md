# ALSAKKAF TRL Official News Local Setup Guide

> **OPTIONAL - DISABLED BY DEFAULT - OFFICIAL METADATA ONLY - NO API KEY - NO TRADE INSTRUCTION**

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-004-OFFICIAL-NEWS-SETUP-001 |
| Document Type | Local Operator Guide |
| Status | ACTIVE FOR TRL-R2-004 SOURCE VALIDATION |
| Version | 1.1 |
| Date | 2026-07-30 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-004 - Local Governed Official News and Economic-Event Collection |

## Authorization and Boundary

Founder authorization is: “I, Abdulrahman Yaseen Alsakkaf, authorize TRL-R2-004.” It covers only local read-only metadata collection from the six endpoints below. It does not authorize a live rehearsal during implementation, MT5 combination, strategy selection, sentiment, impact prediction, price joining, signals, advice, fills, orders, accounts, cloud services, paid services, subscriptions, telemetry, or custody.

## Exact Initial Sources

| Source ID | Exact endpoint |
|---|---|
| FED_MONETARY_POLICY_RSS | `https://www.federalreserve.gov/feeds/press_monetary.xml` |
| BLS_LATEST_RELEASES_RSS | `https://www.bls.gov/feed/bls_latest.rss` |
| BEA_NEWS_RELEASE_RSS | `https://apps.bea.gov/rss/rss.xml` |
| BEA_RELEASE_DATES_JSON | `https://apps.bea.gov/API/signup/release_dates.json` |
| ECB_PRESS_RELEASE_RSS | `https://www.ecb.europa.eu/rss/press.html` |
| ECB_STATISTICAL_RELEASE_RSS | `https://www.ecb.europa.eu/rss/statpress.html` |

These official publisher endpoints initially require no API key or paid subscription. That is not a promise of permanent free access. `OFFICIAL_PUBLISHER`, `NO_API_KEY_REQUIRED`, `LOCAL_RETRIEVAL_ONLY`, `REDISTRIBUTION_NOT_AUTHORIZED`, `FULL_TEXT_NOT_RETAINED`, `TITLE_LINK_METADATA_ONLY`, `TERMS_CAN_CHANGE`, and `SOURCE_NOT_CERTIFIED_BY_ALSAKKAF` apply. No public-domain conclusion is made.

## Ordinary Offline Startup

From `C:\ALSAKKAF_WT\PRJ017_CODEX`, run:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --no-browser
```

This mode does not load news sources, open the cache, resolve source DNS, or send news HTTP. `/api/news-health` returns `NEWS_DISABLED`. Synthetic behavior and MT5-disabled behavior remain as before.

To confirm disabled silence during an authorized local diagnostic, start in ordinary mode, inspect `/api/news-health`, and use an operating-system network monitor filtered to the Python process. There must be no connection to any registry hostname. The automated proof injects a transport that would count calls and confirms zero calls, no registry initialization, and no cache read/write.

## Explicit News-Enabled Startup

Enabling news uses this PC and its internet connection:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app `
  --no-browser `
  --enable-official-news
```

The default refresh interval is 900 seconds. An optional integer from 300 through 3600 seconds is accepted:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app `
  --no-browser `
  --enable-official-news `
  --official-news-refresh-seconds 900
```

Do not add MT5 controls during TRL-R2-004 validation. Simultaneous MT5 and official-news operation is a future integration test.

## Local APIs and Dashboard

Open only `http://127.0.0.1:8765/`. The browser calls localhost routes `/api/news-health`, `/api/news-sources`, `/api/news-items`, and `/api/economic-events`; it never retrieves publisher feeds directly. The dashboard shows status, attribution, complete validated item links, and BEA scheduled occurrences grouped by series ID. Different dates are separate occurrences. `GET` and `HEAD` are allowed. There is no write, refresh-bypass, URL-input, strategy, signal, broker, or order route.

`NEWS_VALID` means all sources passed the current retrieval. `NEWS_PARTIAL` means at least one passed and at least one failed. `NEWS_ALL_SOURCES_FAILED` means none passed. Per-source timeout, HTTP, internal lifecycle/control, redirect, size, content-type, UTF-8, XML safety, parse, schema, and provider-change codes identify the boundary. `NEWS_SOURCE_INTERNAL_ERROR` is a sanitized local lifecycle/control failure, is not attributed to HTTP or a publisher, and exposes no exception detail. Its addition advances only the health API to `TRL-OFFICIAL-NEWS-HEALTH-1.2`; all content, collection, cache, and source identities remain unchanged. Retained records from a failed source are labeled `NEWS_RECORD_STALE` with the latest failure and last confirmed time, while records from successful sources remain `NEWS_RECORD_CURRENT`; any exposed stale record makes cache freshness `NEWS_SOURCE_STALE`. A failure with no retained record does not manufacture stale data. `NEWS_RATE_LIMITED_LOCALLY` is not a publisher failure and does not change record freshness. Cache persistence is separate: `NEWS_CACHE_WRITE_FAILED` means current in-memory updates were not saved and may be lost after restart, even if source state is `NEWS_VALID` or `NEWS_PARTIAL`. The dashboard displays both states and a prominent local warning. A later successful write clears the persistence failure. Source and cache failures are not market events.

## Cache Location, Limits, and Clearing

The only production location is:

```text
%LOCALAPPDATA%\ALSAKKAF_TRL\official_news\cache-v1.json
```

It is local JSON with at most 1,000 combined records, 5 MiB, and 30 days retention. It contains metadata only. Every stored record is untrusted and is revalidated for exact fields/types, attribution, timestamps, complete query/link policy, fallback consistency, news or series/occurrence identities, and fingerprint. During refresh, the validated cache remains trusted until a deep candidate containing only successful source batches passes pruning, full validation, bounds, and canonical serialization. A malformed source batch retains that source's previous records as stale; a final-candidate failure keeps the complete prior cache and performs no write. If the existing file itself is rejected, its production-storage object remains attached: the application starts from a new empty trusted in-memory document and, after a complete valid refresh, atomically replaces the invalid file. Each attempt creates a unique same-directory temporary file atomically, flushes and closes it, and then replaces the target. An old fixed `.tmp` or crash-left unique sibling cannot block the write and is not opened or deleted. A later application instance then loads the repaired cache normally. Manual deletion is unnecessary while the location is writable. If replacement fails, persistence reports `NEWS_CACHE_WRITE_FAILED`; a storage-construction failure also fails closed without revealing a filesystem path. Operational freshness is never trusted from disk. Writes use atomic replacement and no cloud synchronization.

After stopping the application, clear it with resolved-path verification:

```powershell
$trlNewsCache = Join-Path $env:LOCALAPPDATA 'ALSAKKAF_TRL\official_news'
$trlResolvedParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $trlNewsCache))
$trlResolvedCache = [System.IO.Path]::GetFullPath($trlNewsCache)
if ($trlResolvedCache -ne (Join-Path $trlResolvedParent 'official_news')) { throw 'Unexpected cache path' }
Remove-Item -LiteralPath $trlResolvedCache -Recurse -Force -ErrorAction SilentlyContinue
```

This removes only the explicit local cache directory and is not recoverable unless separately backed up. It does not remove source code.

## Security, Schemas, and Retention

The stable application operating mode is `LOCAL_RESEARCH_WITH_OPTIONAL_MT5_READ_ONLY_AND_OFFICIAL_NEWS_METADATA`. Its data boundary is committed synthetic data by default, optional operator-enabled local MT5 read-only data, and optional operator-enabled exact official-news metadata; both optional sources remain independently disabled by default. The local server retrieves only the six unchanged query-free endpoints. Item links use the separate exact-host policy. Raw and strict-UTF-8 percent-decoded paths and queries must exclude backslashes and control/format characters. Valid escaped query text is retained in its original order only within 1,024 bytes and 32 parameters. Invalid paths or queries fall back and render as non-links, and cache validation uses the same policy. Atom uses `published` before `updated` and selects only a direct explicit/default alternate link, with HTML/XHTML preferred deterministically; self, enclosure, related, payment, and other relations are excluded. RSS separately prefers `pubDate`, then `date`. One shared bounded, idempotent canonicalizer repeatedly decodes markup to a fixed limit, compares tag components case-insensitively across colon and dot boundaries, removes complete blocked namespace-like/dotted elements and contents, preserves safe surrounding text and Arabic, and rejects malformed or residual blocked-looking markup plus controls and format characters. A tag-like blocked stem followed by unsupported punctuation, including `script=foo`, `script!foo`, `script?foo`, `script@foo` and style, namespace, dotted, case, or encoded equivalents, is rejected before `HTMLParser` can discard the ambiguous syntax. Safe attributes on ordinary elements and safe mathematical `<` or `>` text remain accepted. Fresh and cached titles/event names use the identical rule. BEA date-only input must exactly match `YYYY-MM-DD`; canonical UTC publication timestamps preserve nonzero fractional seconds and trim only unnecessary trailing zeros. Duplicate endpoint-fallback identities reject the entire new source batch, retain its trusted records as stale, and never reach a candidate write. News uses `TRL-OFFICIAL-NEWS-ITEM-1.3`; events use `TRL-OFFICIAL-ECONOMIC-EVENT-1.3`; news collection `TRL-OFFICIAL-NEWS-COLLECTION-1.2` and event collection `TRL-OFFICIAL-ECONOMIC-EVENT-COLLECTION-1.3` expose refresh state. Event series and occurrences are separate, and a changed date is a new occurrence when the source supplies no occurrence ID. Optional values are bounded to the same 500 characters in parser and complete-record validation. A refresh uses a generation/owner token and three stages: short locked preparation and snapshot capture; unlocked six-source retrieval, parsing, validation, merge, pruning, and serialization; then short locked owner-checked application. Atomic persistence also runs without the state lock. While I/O is blocked, news readers immediately receive a deep-copied trusted snapshot with `refreshing=true`, ordinary health remains responsive, and no second refresh starts. A persistence failure keeps the accepted in-memory candidate and records the restart-loss warning. The 16-handler admission limit is nonblocking: overflow sockets are closed without parsing, response, handler, timer, queue, or permit release. An admitted socket begins its first fixed ten-second header deadline before handler-thread scheduling, keeps the fixed five-second inactivity timeout, uses one deadline per request, and cancels and joins it before route processing. The shutdown-plus-close bound remains 11 seconds. Each complete publisher operation runs in an owned Windows-spawn-compatible standard-library child. The exact record is registered as `STARTING` before synchronous Windows `Process.start()` executes, and no global record lock is held during that platform call. Windows process creation is local and outside the post-spawn 20-second publisher-retrieval deadline because Python's standard multiprocessing API cannot safely preempt a blocked start. Shutdown marks a starting record cancelled and waits; a child returned late by the platform is immediately terminated, joined once, closed once, and removed by the record-owned finalizer. The fixed non-configurable deadline begins immediately after successful start and covers child import and entry, DNS, connection, TLS, request, response status, headers, bounded body, and IPC. A parent clock failure becomes sanitized `NEWS_SOURCE_INTERNAL_ERROR`; genuine HTTP failures remain `NEWS_SOURCE_HTTP_ERROR`. The child retains five-second connection and ten-second inactivity limits. One state-machine finalizer owns exit status, terminate or kill, the only join, both parent pipe endpoints, the only process close, and record removal for success, timeout, internal clock failure, crash, malformed IPC, start failure, and shutdown. No join occurs before start, repeated shutdown is harmless, and shutdown completion is not reported while a starting or started record remains. IPC is bounded consistently with the one-MiB response limit. The application invokes the actual server-owned news service during shutdown, then guarantees server closure, and only afterward prints the stopped message. Broad, commercial, full-text, broker-provided, and registry-owned news capabilities remain unavailable. Strategies, signals, order proposals, and execution also remain unavailable. No summary, sentiment, importance, direction, strategy association, or causal claim is generated.

## LIVE-FIX-01 Publisher-Format Compatibility

The exact source endpoints and normal startup commands are unchanged. The parser now recognizes the observed BEA product-name mapping to strict RFC3339 `release_dates`, treats `file_last_updated` as bounded non-retained publisher metadata, accepts uppercase `EDT` and `EST` RSS offsets, and structurally accepts a non-retained RSS description only up to 64 KiB within the existing one-MiB response bound. Descriptions and all other article-body fields remain absent from records, cache, APIs, and evidence.

Automated validation must use only sanitized synthetic response bytes, an injected transport, fake clocks, and in-memory storage. It must not start the application listener, access DNS or the internet, contact a publisher, use the production cache, or invoke MT5, brokers, credentials, external APIs, strategies, signals, recommendations, paper trades, orders, cloud services, subscriptions, or telemetry. LIVE-FIX-01 performs no live rehearsal. The one authorized follow-up rehearsal remains a separate later operator action against only the same six governed endpoints, subject to every existing stop condition; no additional rehearsal is authorized.

## LIVE-FIX-02 BEA Mapping Compatibility

BEA product names must already be exactly canonical; any name that would be trimmed, whitespace-collapsed, decoded, sanitized, removed, rewritten, or normalized is rejected with the complete source batch rather than repaired. The parser counts every non-reserved product record, including an empty `release_dates` record, against a 200-product limit. It separately counts all raw schedule entries, including duplicates, against a 200-entry limit before deduplication, and limits the final constructed occurrences to 200.

After strict RFC3339 parsing and UTC normalization, exact and UTC-equivalent dates are deduplicated deterministically within each exact product and sorted before event construction. Dates for different products remain distinct. The service-level duplicate-identity guard is unchanged and remains a fail-closed defense. These rules are compatibility corrections, not publisher certification, production authorization, strategy approval, trading advice, or profitability evidence.

## LIVE-FIX-05 Exact-Host Operation

The enabled connector validates each full immutable source record before deriving its hostname from the exact governed HTTPS endpoint. It admits one active retrieval per exact hostname, so the two BEA sources run successively and the two ECB sources run successively while FED, BLS, BEA, and ECB hostname groups remain concurrent. This adds no retry or request: an eligible refresh still performs exactly six governed attempts, uses separate child/pipe/response lifecycles, and applies results in registry order. Connections and responses are neither pooled nor shared.

A source waits for hostname admission before child creation and before its post-start 20-second deadline begins. It receives the complete deadline after admission; a two-source hostname can therefore take approximately two successive deadlines plus process-start and finalization time. During shutdown, the active child is canceled and a waiter rechecks closed state after admission, returning the existing controlled timeout result without starting a child or network operation. Windows `Process.start()` remains synchronous and cannot be safely preempted.

Non-timeout DNS, connection, TLS, socket, HTTP protocol, and genuine non-2xx status failures remain `NEWS_SOURCE_HTTP_ERROR`. Local process/pipe construction, spawn, parent wait, crash, IPC, serialization/decoding, invalid local result, abnormal exit, and cleanup/finalization failures use the existing `NEWS_SOURCE_INTERNAL_ERROR` without exposing exception details. No schema, stable-code inventory, endpoint, registry, digest, source identity, cache identity, or content identity changes. Exact-host serialization is a local safety correction, not a claim about publisher connection limits and not publisher certification.

## Test Evidence and Privacy

Offline tests use fake source responses, fake clocks, and in-memory cache. They do not access the internet, real `LOCALAPPDATA`, MT5, credentials, a broker, or an external service. Final command results are recorded in the checkpoint report. The collector sends no telemetry to ALSAKKAF and holds no customer data. Official publishers and the operator's network providers can observe ordinary connection metadata when collection is explicitly enabled.

## Manual Rehearsal Requires Separate Authorization

Do not perform a live rehearsal during LIVE-FIX-01 implementation or automated validation. The one Founder-authorized follow-up is a later, separately operated controlled rehearsal against the same six governed endpoints: stop the application and MT5; confirm the exact registry and current source terms; start only the news-enabled command; inspect the four localhost APIs; confirm exact destinations, no redirects, no credentials, metadata-only output, per-source health, and local throttling; capture sanitized evidence without article bodies; stop with Ctrl+C; and inspect or clear the cache. Stop immediately on provider change, paid/key requirement, redirect, unexpected hostname/path, ordinary webpage scraping need, or terms concern. No additional rehearsal is authorized.

## Financial-Advice and Next-Checkpoint Boundary

This information is not financial advice and provides no strategy, bullish/bearish interpretation, importance, recommendation, trade instruction, MT5 action, or order. The proposed next checkpoint is **TRL-R2-005 - LOCAL FORWARD PAPER PORTFOLIO AND EVENT TIMELINE**, subject to separate authorization and causal-time rules. It must not provide live trading or broker orders. TRL-R2-005 remains unauthorized and has not begun.
