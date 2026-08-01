# ALSAKKAF Trading Research Lab - Local Application Quick Start

> **PAPER/RESEARCH ONLY - SYNTHETIC DEFAULT - OPTIONAL FORWARD PAPER ENGINE - OPTIONAL OFFICIAL NEWS - OPTIONAL LOCAL MT5 READ-ONLY DATA - NO ORDERS**

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R2-005-QUICK-START-005 |
| Document Type | Local Application Operator Guide |
| Status | ACTIVE FOR TRL-R2-005 SOURCE LAUNCH; Section 16 added for TRL Phase 3 operating-mode state machine; Sections 3 and 16.2 corrected after Founder review removed the legacy-flag bypass; Section 17 added for Phase 4 signal intelligence; Section 18 added for Phase 5 MT5 execution adapter |
| Version | 4.3 |
| Date | 2026-08-01 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-005 - Causal Market Timeline and Forward Paper Engine |

These instructions are for Windows PowerShell. The source application is Windows-first and local-first. Python's standard library, the committed Release 1 kernel, and the synthetic demonstration pack remain the baseline. The forward paper engine and official-news collection are disabled by default. Paper enablement creates only local application-data storage and never creates a broker order. Official news uses exact governed no-key endpoints only after explicit enablement. The official `MetaTrader5` package remains a separate optional local dependency imported only after explicit MT5 read-only use.

# 1. Open the Repository

Open PowerShell and move to the repository root:

```powershell
Set-Location 'C:\ALSAKKAF_WT\PRJ017_CODEX'
```

# 2. Start the Default Synthetic Application

Start the local dashboard and allow it to open the default browser:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app
```

The application binds only to `127.0.0.1`. It never falls back to `0.0.0.0` or another port. If port 8765 is already in use, stop the conflicting local process or choose an explicit unused local port:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --port 8876
```

Synthetic mode is always the default. This command does not initialize paper storage, MT5, the official-news source registry, the news transport, or the news cache. Paper health returns `PAPER_ENGINE_DISABLED`, Market connection returns `MT5_DISABLED`, and official-news health returns `NEWS_DISABLED`. No fake live values are displayed and no news DNS or HTTP request occurs.

# 3. Start the Explicit Forward Paper Engine

**As of TRL Phase 3, `--enable-forward-paper-engine` is deprecated and
always fails closed.** No approved Phase 3 operating mode authorizes the
unrestricted forward-paper engine, so this command now prints
`LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE` to `stderr`, exits with status `2`,
and never starts a server, constructs a paper store, or opens a network
connection:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --enable-forward-paper-engine
```

Use Section 16 (`SYNTHETIC_PAPER` mode) instead. The starting value in that
mode is a clearly synthetic research balance held in memory only — it does
not use the `forward-paper-timeline-v1.json` production store this section
previously described, because that store has no governed operating mode
authorizing it yet in Phase 3.

# 4. Start Explicit Official-News Mode

This optional mode uses your PC and internet connection to retrieve title/link metadata and BEA release dates from the exact governed official sources. It requires no API key, ALSAKKAF account, paid subscription, or shared service:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app `
  --no-browser `
  --enable-official-news
```

The default refresh interval is 900 seconds. The optional `--official-news-refresh-seconds` value must be an integer from 300 through 3600. Do not combine official news with MT5 during TRL-R2-004 automated or manual validation. See `TRL_OFFICIAL_NEWS_SETUP_GUIDE.md` and `TRL_NEWS_SOURCE_GOVERNANCE.md`. Source terms, formats, and availability can change; full article text is not retained or redistributed.

# 5. Start Explicit Local MT5 Read-Only Mode

Use this only after the separately governed local setup in `TRL_MT5_LOCAL_SETUP_GUIDE.md`. MetaTrader 5 must be installed and running on this PC, the operator must authenticate directly inside MT5, and the exact symbol must be visible in Market Watch.

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --enable-mt5-read-only --mt5-symbol XAUUSD --mt5-timeframes M1,M5,H4,D1 --mt5-bars 500
```

PRJ-017 never requests a login, password, investor password, broker server, API key, or remote host. Never put broker credentials on this command line. Only exact safe symbols, M1/M5/H4/D1, and 1 through 2,000 bars are accepted. No alternate symbol is selected automatically.

# 6. Start Without Opening a Browser

Use the no-browser option for testing or when you want to open the page yourself:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --no-browser
```

# 7. Open the Local URL

With the default port, open this local address:

```text
http://127.0.0.1:8765/
```

From another PowerShell window, the following opens only that local URL:

```powershell
Start-Process 'http://127.0.0.1:8765/'
```

No internet connection, Atlas service, cloud account, external font, content delivery network or analytics service is required.

# 8. Stop the Application

Return to the PowerShell window running the application and press:

```text
Ctrl+C
```

The application first marks any starting official-news child cancelled, waits for the synchronous Windows process-start call to return, finalizes every successfully started child and the refresh coordinator, and closes the local listening socket. It prints `Local dashboard stopped.` only after official-news shutdown and server closure complete. Python's standard Windows multiprocessing API cannot safely preempt a blocked `Process.start()` call, so process creation is outside the post-spawn 20-second publisher-retrieval deadline and can extend shutdown until the exact record can be finalized. Local HTTP admission is nonblocking at 16 handlers: an overflow socket is immediately closed without parsing or response, while each admitted connection starts its first ten-second header deadline before handler scheduling. This preserves the 11-second HTTP shutdown-plus-close bound under slow-header overload.

# 9. Run the Tests

From the repository root, disable bytecode and run the Release 1, application, registry, and combined discovery tests:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_trading_lab.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_trading_lab_app.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_strategy_registry.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_mt5_connector.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_news_events.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_forward_paper.py

python -B -W error -m unittest discover -s 09_AI_Systems\02_Tools\Trading_Lab -p 'test*.py'
```

`-B` prevents Python bytecode files. `-W error` makes any Python warning fail validation.

# 10. Download and Remove Local Reports

The JSON and Markdown download buttons create files in the browser only. The server never silently writes a report. Your browser normally places them in the Windows Downloads folder.

To remove the two known downloaded demonstration filenames:

```powershell
$trlDownloads = Join-Path $env:USERPROFILE 'Downloads'
Remove-Item -LiteralPath (Join-Path $trlDownloads 'TRL-R2-001-synthetic-result.json') -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $trlDownloads 'TRL-R2-001-synthetic-paper-report.md') -ErrorAction SilentlyContinue
```

These commands target only the two explicitly named local downloads. They do not remove repository files.

# 11. Confirm the Closed Capability Boundary

While the local application is running, inspect its capability manifest:

```powershell
$trlCapabilities = Invoke-RestMethod 'http://127.0.0.1:8765/api/capabilities'
$trlCapabilities | Select-Object paper_research_only, local_mt5_read_only_connector_capability, local_mt5_order_capability, external_order_capability, credential_storage_capability, telemetry
$trlCapabilities.not_implemented
```

The stable operating mode is `LOCAL_RESEARCH_WITH_OPTIONAL_FORWARD_PAPER_TIMELINE_MT5_READ_ONLY_AND_OFFICIAL_NEWS_METADATA`. Its machine-readable boundary is committed synthetic data by default, optional local forward paper storage, optional operator-enabled local MT5 read-only data, and optional operator-enabled exact official-news metadata. Paper, MT5, and official news are independently disabled by default. Forward paper, the narrow local read-only connector, and official-news metadata capability values are `True`. Signal generation, trade recommendation, local MT5 order, broker execution, real order, account mutation, credential storage, full-text or broad news, sentiment, market impact, event-price joining, and telemetry values are `False`.

There is no credential endpoint, broker-account endpoint, broker-position endpoint, order endpoint, hidden order control, or live-trading mode. The paper-account and paper-position routes are read-only local research projections and never represent broker state.

Inspect the disabled or explicitly enabled paper documents:

```powershell
$trlPaperAccount = Invoke-RestMethod 'http://127.0.0.1:8765/api/paper-account'
$trlPaperPositions = Invoke-RestMethod 'http://127.0.0.1:8765/api/paper-positions'
$trlPaperHistory = Invoke-RestMethod 'http://127.0.0.1:8765/api/paper-history'
$trlTimeline = Invoke-RestMethod 'http://127.0.0.1:8765/api/market-timeline'
$trlPaperHealth = Invoke-RestMethod 'http://127.0.0.1:8765/api/paper-health'
```

# 12. Inspect Official-News Health and Cache

```powershell
$trlNewsHealth = Invoke-RestMethod 'http://127.0.0.1:8765/api/news-health'
$trlNewsHealth | Select-Object enabled, status, reason_code, last_successful_retrieval_utc, next_permitted_refresh_utc, cache_freshness_status
```

The production cache is `%LOCALAPPDATA%\ALSAKKAF_TRL\official_news\cache-v1.json`, bounded to 1,000 records, 5 MiB, and 30 days. Stop the application before removing the verified `official_news` directory. The cache contains no article bodies, images, credentials, cookies, MT5 data, account data, or cloud synchronization. Publisher requests have fixed connection and inactivity limits plus a fixed 20-second absolute deadline covering connection, status, headers, and body. A parent-side deadline-clock failure reports sanitized `NEWS_SOURCE_INTERNAL_ERROR`; genuine HTTP failures remain `NEWS_SOURCE_HTTP_ERROR`. The health schema is `TRL-OFFICIAL-NEWS-HEALTH-1.2`; all content, collection, cache, source-registry, endpoint, host, and compiled source identities remain unchanged. Titles and event names use the same bounded, idempotent markup canonicalizer during retrieval and cache validation. BEA date-only values must exactly match `YYYY-MM-DD`; publication fractions are retained canonically. A live official-source rehearsal requires separate Founder authorization and is not part of automated validation.

# 13. Inspect the Local Market Boundary

```powershell
$trlConnection = Invoke-RestMethod 'http://127.0.0.1:8765/api/market-connection'
$trlSnapshot = Invoke-RestMethod 'http://127.0.0.1:8765/api/market-snapshot'
$trlConnection
$trlSnapshot.data_quality
```

In ordinary mode both routes return `MT5_DISABLED`. In explicitly enabled mode, values are broker-native and read-only. Commission is unknown, market-session state is unknown, no strategy is applied to MT5 data, and no order capability exists.

# 14. Inspect the Governed Strategy Registry

While the application is running, inspect the deterministic read-only registry document:

```powershell
$trlRegistry = Invoke-RestMethod 'http://127.0.0.1:8765/api/strategy-registry'
$trlRegistry.registry_health
$trlRegistry.installed_executable_strategies
$trlRegistry.research_backlog
$trlRegistry.vault
```

Health must be `VALID / REGISTRY_VALID`. The executable collection must contain only SMA-001 version 1.0.0. The separate backlog entries must all be `PLANNED_NOT_IMPLEMENTED` with `execution_eligible` equal to `False`.

The registry does not choose a best strategy. No strategy is approved for investment use. The optional local MT5 connector is a separate data-only surface and never invokes the registry or Release 1 evaluation. Broad, commercial, full-text, broker-provided, and registry-owned news capabilities remain unavailable. Order proposals and execution also remain unavailable.

# 15. LIVE-FIX-05 Official-News Host Admission

Official-news source identity is fully validated before the connector derives the exact endpoint hostname. The connector admits one active operation per exact governed hostname: BEA's two sources serialize with one another, ECB's two sources serialize with one another, and the FED, BLS, BEA, and ECB hostname groups remain concurrent. There is no retry, global six-source serialization, connection reuse, or response sharing; an eligible refresh still records exactly six governed attempts and applies results in registry order.

Hostname waiting occurs before child and pipe creation and before the source's fixed post-start 20-second deadline. Each admitted source keeps the complete deadline, so a two-source hostname may take approximately two successive publisher deadlines plus synchronous process-start and finalization time. Shutdown cancels active child work and releases waiting sources through the existing controlled timeout result without permitting a waiter to start child or network work. Synchronous Windows `Process.start()` remains non-preemptible.

Non-timeout DNS/connect/TLS/socket/HTTP failures and genuine non-2xx status remain `NEWS_SOURCE_HTTP_ERROR`. Provably local process, pipe, wait, crash, IPC, serialization, invalid-result, abnormal-exit, and cleanup/finalization failures use the existing sanitized `NEWS_SOURCE_INTERNAL_ERROR`. No exception details are exposed, and no schema, stable-code, endpoint, registry, digest, source, cache, or content identity changes. This is not evidence of a publisher connection-limit policy and is not publisher certification.

# 16. Operating-Mode State Machine (TRL Phase 3)

Every launch of the dashboard resolves a governed **operating mode** before
anything else starts. The seven modes are `OFF`, `RESEARCH`,
`SYNTHETIC_PAPER`, `MT5_DEMO_MANUAL`, `MT5_DEMO_AUTOMATED`,
`MT5_LIVE_MANUAL`, and `MT5_LIVE_AUTOMATED`. Only the first three are
available in this checkpoint; the four MT5 modes are represented in the
schema and dashboard but always fail closed with an explicit missing-
prerequisite reason, because no MT5 execution adapter (Phase 5) or
live-arming capability (Phase 9) exists yet. Full design detail lives in
`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`.

## 16.1 Local operator commands

Mode changes are made only with a local command-line tool — never through
any HTTP route or browser control. All commands run from the repository
root:

```powershell
python -B -W error -m trading_lab_app.mode_cli show-mode
python -B -W error -m trading_lab_app.mode_cli list-modes
python -B -W error -m trading_lab_app.mode_cli explain-mode SYNTHETIC_PAPER
python -B -W error -m trading_lab_app.mode_cli request-mode RESEARCH --reason "start research"
python -B -W error -m trading_lab_app.mode_cli transition-history --limit 10
```

`request-mode` only succeeds for an explicitly allowed transition among
`OFF`, `RESEARCH`, and `SYNTHETIC_PAPER` (any of the three can always
return to `OFF`). Requesting any `MT5_*` mode is rejected with a structured
reason (`MISSING_MT5_ADAPTER`, and additionally `MISSING_LIVE_ARMING` for
the two automated modes) — this is expected, correct behavior, not an
error to work around.

## 16.2 How mode affects what starts

**There is exactly one authoritative decision path, with no exception:**
`ModeService` resolved mode → capability check → paper-service
construction. No command-line flag constructs or activates a paper service
outside it — this was corrected after Founder review found the original
implementation let a CLI flag bypass the state machine.

A mode change made with `mode_cli.py` takes effect the **next time the
dashboard starts** — the running server resolves its mode once at startup
and does not poll the mode-state file while it is running (see Known
Limitations in the Phase 3 contract). At startup:

- `OFF` or `RESEARCH` → the paper engine stays disabled, exactly as
  Section 2 describes.
- `SYNTHETIC_PAPER` → the dashboard starts with the committed synthetic
  demonstration already loaded.

The legacy flags described in Sections 2–3 now route through this same
path rather than bypassing it:

- `--enable-forward-paper-demo` (deprecated) requests a transition to
  `SYNTHETIC_PAPER` through `ModeService`, the same way
  `mode_cli.py request-mode SYNTHETIC_PAPER` does — same audit events, same
  validation, same atomic persistence. It fails closed (server does not
  start) if the transition is rejected. It never activates synthetic paper
  while the authoritative mode remains `OFF` or `RESEARCH`.
- `--enable-forward-paper-engine` (deprecated) always fails closed with
  `LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE` before any other setup work,
  because no Phase 3 mode authorizes it. See Section 3.

`/api/mode-status` and `/api/paper-account` can never disagree about
whether synthetic paper is active — both are derived from the same
resolved mode through the same construction function.

## 16.3 Inspecting mode over HTTP (read-only)

```powershell
$trlMode = Invoke-RestMethod 'http://127.0.0.1:8765/api/mode-status'
$trlMode | Select-Object current_mode, broker_execution_available, automated_trading_available, live_arming_available
$trlMode.unavailable_modes
```

`broker_execution_available`, `automated_trading_available`,
`live_arming_available`, and `private_remote_access_available` are all
`False` in every mode this checkpoint can reach. There is no POST, PUT,
PATCH, or DELETE route for `/api/mode-status` — attempting one returns
`405` with `Allow: GET, HEAD`, matching every other route in this
application.

## 16.4 Persisted state location

The mode-state file is `%LOCALAPPDATA%\ALSAKKAF\TradingLab\operating-mode-state-v1.json`,
written atomically the same way as the forward-paper store (Section 3). It
never contains a credential, and hand-editing it has no effect beyond
making the file fail validation — an invalid or unsafe file always resolves
to `OFF` at the next startup, with the recovery recorded as an audit event.

## 17. Signal intelligence (TRL-R2-006, Phase 4)

**RESEARCH SIGNAL — NOT A TRADE INSTRUCTION — NO BROKER EXECUTION.** Available only in
`RESEARCH` and `SYNTHETIC_PAPER` modes; denied in `OFF` and every MT5 mode. Governed by the
same `ModeService` as every other subsystem — there is no separate mode check.

### 17.1 Local operator commands

```powershell
python -B -W error -m trading_lab_app.signal_cli signal-status
python -B -W error -m trading_lab_app.signal_cli list-strategies
python -B -W error -m trading_lab_app.signal_cli explain-strategy SMA-001
python -B -W error -m trading_lab_app.signal_cli evaluate-strategy SMA-001 request.json
python -B -W error -m trading_lab_app.signal_cli generate-proposal SMA-001 request.json
python -B -W error -m trading_lab_app.signal_cli validate-proposal proposal.json
python -B -W error -m trading_lab_app.signal_cli proposal-history
python -B -W error -m trading_lab_app.signal_cli export-proposal proposal.json
python -B -W error -m trading_lab_app.signal_cli compare-strategies
```

`request.json` is a `TRL_SIGNAL_EVALUATION_REQUEST.v1` document (see
`signal_data.py` for the exact field list, or `test_signal_intelligence.py`'s
`base_request()` helper for a complete worked example). `evaluate-strategy`
prints only the per-role results; `generate-proposal` prints the full
`TRL_SIGNAL_PROPOSAL.v1` document.

FIB-001 is present in `list-strategies`/`compare-strategies` but always fails
closed with `STRATEGY_PARAMETERS_NOT_APPROVED` — its numeric parameters are
not Founder-approved (see `TRL_BLOCKERS.md`).

### 17.2 Inspecting signal intelligence over HTTP (read-only)

```powershell
$trlSignal = Invoke-RestMethod 'http://127.0.0.1:8765/api/signal-status'
$trlSignal | Select-Object enabled, operating_mode, signal_generation
Invoke-RestMethod 'http://127.0.0.1:8765/api/signal-strategy-registry'
Invoke-RestMethod 'http://127.0.0.1:8765/api/signal-proposals'
```

Same read-only rule as every other route in this application: GET/HEAD only,
`405` with `Allow: GET, HEAD` for POST/PUT/PATCH/DELETE. There is no HTTP
route that generates, approves, modifies, or executes a proposal.

### 17.3 Persistence

Proposal/audit history for the wired application signal service is durable
in both `RESEARCH` and `SYNTHETIC_PAPER` (`LocalSignalStore`, atomic
temp-file-plus-`os.replace` writes, the same design as the R2-005 paper
timeline) — it survives an application restart and is shared with the
local CLI, so `generate-proposal` in one process is visible to
`proposal-history` in a later, separate process. The store file is
`%LOCALAPPDATA%\ALSAKKAF\TradingLab\signal-intelligence-timeline-v1.json`;
every persisted proposal carries its own `operating_mode` and
`sample_label`, so RESEARCH and SYNTHETIC_PAPER records sharing that one
file are never indistinguishable. A corrupted or hand-edited file fails
closed with `SIGNAL_STORE_INTEGRITY_FAILURE` rather than being silently
replaced or generating a new proposal.

### 17.4 Performance and walk-forward reports

```powershell
python -B -W error -m trading_lab_app.signal_cli performance-report SMA-001 SYNTHETIC_PAPER
python -B -W error -m trading_lab_app.signal_cli export-performance-report SMA-001 SYNTHETIC_PAPER
python -B -W error -m trading_lab_app.signal_cli walk-forward-report SMA-001 segments.json
```

Every report covers exactly one governed `sample_label` and is built from
the durable proposal history. Because no SMA-001 execution geometry is
Founder-approved yet (Section 17.5), `completed_trade_count` is always
zero and every report is honestly `INSUFFICIENT_SAMPLE` — this is expected,
not a bug.

### 17.5 SMA-001 research-only status

SMA-001's crossing *direction* (exact Release-1 kernel parity) is produced
and recorded as `role_results.technical_strategy.candidate_direction`, but
no execution geometry (entry zone, stop, TP1-TP4, allocations, quantity) is
Founder-approved. Every crossing therefore fails closed at Role 3 with
`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` and the final proposal is
`BLOCKED` — exactly like FIB-001's `STRATEGY_PARAMETERS_NOT_APPROVED`. See
`TRL_BLOCKERS.md`.

## 18. MT5 execution adapter (TRL-R2-007, Phase 5)

**DEMO ONLY — LIVE EXECUTION DISABLED — MANUAL CONFIRMATION REQUIRED FOR EVERY ORDER.**
Available only in `MT5_DEMO_MANUAL` (reachable only from `OFF`, returns only to `OFF`);
denied in every other mode. No HTTP route can check, confirm, or send an order — this
CLI is the only mutation path. SMA-001 and FIB-001 both remain blocked before ever
reaching the adapter (Section 17.5, `TRL_BLOCKERS.md`).

### 18.1 Enter the mode

```powershell
python -B -W error -m trading_lab_app.mode_cli request-mode MT5_DEMO_MANUAL --reason "demo rehearsal"
```

### 18.2 Local operator commands

```powershell
python -B -W error -m trading_lab_app.mt5_execution_cli mt5-status
python -B -W error -m trading_lab_app.mt5_execution_cli mt5-dependency-status
python -B -W error -m trading_lab_app.mt5_execution_cli mt5-terminal-status
python -B -W error -m trading_lab_app.mt5_execution_cli mt5-account-status
python -B -W error -m trading_lab_app.mt5_execution_cli mt5-symbol-status XAUUSD
python -B -W error -m trading_lab_app.mt5_execution_cli execution-capabilities
python -B -W error -m trading_lab_app.mt5_execution_cli execution-journal --limit 20
python -B -W error -m trading_lab_app.mt5_execution_cli inspect-proposal proposal.json
python -B -W error -m trading_lab_app.mt5_execution_cli build-order-intent proposal.json
python -B -W error -m trading_lab_app.mt5_execution_cli check-order <order_intent_id>
python -B -W error -m trading_lab_app.mt5_execution_cli send-demo-order <order_intent_id>
python -B -W error -m trading_lab_app.mt5_execution_cli send-demo-order <order_intent_id> --confirm <code>
python -B -W error -m trading_lab_app.mt5_execution_cli inspect-execution <order_intent_id>
```

`proposal.json` is an already-generated, fully validated `TRL_SIGNAL_PROPOSAL.v1`
document (e.g. exported from a `RESEARCH`/`SYNTHETIC_PAPER` session via
`signal_cli export-proposal`) — the argument accepts either a file path or literal JSON
text. `send-demo-order` without `--confirm` requests confirmation and prints a short
challenge code plus its expiry; re-run the exact same command with `--confirm <code>` to
actually submit. Every rejection prints `{"outcome": "REJECTED", "reason_code": ...}`
and exits nonzero.

### 18.3 Account fingerprint configuration (required before real execution)

No Founder-approved MT5 demo account fingerprint is configured by default — this is an
intentional external blocker (`ACCOUNT_UNAVAILABLE`; see `TRL_BLOCKERS.md`), never
silently bypassed. To configure one, set all three environment variables before starting
the application or CLI (never commit these to Git):

```powershell
$env:TRL_MT5_DEMO_LOGIN = "<demo account number>"
$env:TRL_MT5_DEMO_COMPANY = "<exact broker company name>"
$env:TRL_MT5_DEMO_SERVER = "<exact broker server name>"
```

### 18.4 Inspecting execution status over HTTP (read-only)

```powershell
Invoke-RestMethod 'http://127.0.0.1:8765/api/mt5-execution-status'
Invoke-RestMethod 'http://127.0.0.1:8765/api/mt5-account-status'
Invoke-RestMethod 'http://127.0.0.1:8765/api/mt5-terminal-status'
Invoke-RestMethod 'http://127.0.0.1:8765/api/execution-journal'
```

Same read-only rule as every other route: GET/HEAD only, `405` with
`Allow: GET, HEAD` for POST/PUT/PATCH/DELETE. The account-status response never
includes the raw login number — only a `login_redacted` value.

### 18.5 Execution journal persistence

The append-only, hash-chained execution journal is durable
(`%LOCALAPPDATA%\ALSAKKAF\TradingLab\mt5-execution-journal-v1.json`) and shared with the
local CLI, so an order intent built in one process is visible (and its duplicate/idempotency
protection still applies) in a later, separate process. A corrupted or hand-edited file
fails closed rather than being silently replaced or allowing any action to proceed.

### 18.6 Scope limitations

Single order per proposal only; one `order_check` and one manual-confirmed `order_send`
attempt per order intent (no automatic repriced retry); live modes and automated
submission remain unavailable (Phase 9); an uncertain `order_send` result freezes
permanently rather than being automatically reconciled (Phase 10). See
`TRL_R2_007_MT5_EXECUTION_EVIDENCE.md` for full detail. Basket (multi-child) execution
is Phase 6 — see Section 19 below.

## 19. Controlled basket execution (TRL-R2-009, Phase 6)

Manual, demo-only, 2–4-child basket execution built from an already-eligible Phase 5
parent order intent: per-child `order_check`, one confirmation cycle authorizing the
complete ordered remaining child set, one explicit `send-basket-next` per child with no
automatic progression. Live and automated basket execution do not exist. Reuses the
same adapter, journal, and lock Phase 5 uses — no new durable store.

### 19.1 Enter the mode

Same as Section 18.1: `python -m trading_lab_app.mode_cli request-mode MT5_DEMO_MANUAL`.
`manual_basket_execution` is granted only in this mode, and only in addition to the
Phase 5 capabilities each basket operation already needs (`mt5_order_check` for checks,
`mt5_order_send`/`manual_broker_execution` for sends).

### 19.2 Local operator commands

```
python -B -W error -m trading_lab_app.basket_execution_cli basket-status
python -B -W error -m trading_lab_app.basket_execution_cli inspect-basket <basket_id>
python -B -W error -m trading_lab_app.basket_execution_cli build-basket <parent_order_intent_id>
python -B -W error -m trading_lab_app.basket_execution_cli check-basket <basket_id>
python -B -W error -m trading_lab_app.basket_execution_cli request-basket-confirmation <basket_id>
python -B -W error -m trading_lab_app.basket_execution_cli confirm-basket <basket_id> "CONFIRM-BASKET <16-hex>"
python -B -W error -m trading_lab_app.basket_execution_cli send-basket-next <basket_id>
python -B -W error -m trading_lab_app.basket_execution_cli inspect-basket-child <basket_id> <basket_child_id>
python -B -W error -m trading_lab_app.basket_execution_cli basket-journal --limit 20
```

`send-basket-next` takes no child-identifying argument — the service alone computes
which child is next eligible; the operator cannot skip, reorder, or resend a child.

### 19.3 Inspecting basket status over HTTP (read-only)

`GET /api/basket-execution-status`, `GET /api/execution-baskets`,
`GET /api/execution-basket/<basket_id>`, `GET /api/execution-basket-journal`. Same
read-only rule as every other route: GET/HEAD only, `405` with `Allow: GET, HEAD` for
POST/PUT/PATCH/DELETE. No HTTP route can build, check, confirm, or send a basket child.

### 19.4 Scope limitations

No live or automated basket execution (Phase 9); a `FROZEN`/`PARTIALLY_COMPLETED`
basket requires the same manual, human-operator reconciliation path a frozen single
order already does today — Phase 6 detects and freezes these states truthfully but does
not resolve them (Phase 10). See `TRL_R2_009_CONTROLLED_BASKET_EXECUTION_EVIDENCE.md`
for full detail, including disclosed implementation-level design choices and
limitations.
