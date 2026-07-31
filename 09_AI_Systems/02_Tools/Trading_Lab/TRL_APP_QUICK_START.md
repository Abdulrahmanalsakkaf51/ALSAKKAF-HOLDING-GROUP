# ALSAKKAF Trading Research Lab - Local Application Quick Start

> **PAPER/RESEARCH ONLY - SYNTHETIC DEFAULT - OPTIONAL FORWARD PAPER ENGINE - OPTIONAL OFFICIAL NEWS - OPTIONAL LOCAL MT5 READ-ONLY DATA - NO ORDERS**

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R2-005-QUICK-START-005 |
| Document Type | Local Application Operator Guide |
| Status | ACTIVE FOR TRL-R2-005 SOURCE LAUNCH |
| Version | 4.0 |
| Date | 2026-07-27 |
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

Enable the local causal timeline and forward paper projection without enabling any signal generator or broker path:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --enable-forward-paper-engine
```

The starting value is a clearly synthetic research balance. Production storage is `%LOCALAPPDATA%\ALSAKKAF\TradingLab\forward-paper-timeline-v1.json`. Do not describe this projection as a brokerage account or live balance. The dashboard remains empty until a future governed Signal Desk submits proposals through the internal contract; R2-005 exposes no HTTP write route.

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
