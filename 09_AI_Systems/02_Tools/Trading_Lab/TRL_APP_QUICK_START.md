# ALSAKKAF Trading Research Lab - Local Application Quick Start

> **PAPER/RESEARCH ONLY - SYNTHETIC DEFAULT - OPTIONAL LOCAL MT5 READ-ONLY DATA - NO ORDERS**

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R2-003-QUICK-START-003 |
| Document Type | Local Application Operator Guide |
| Status | ACTIVE FOR TRL-R2-003 SOURCE LAUNCH |
| Version | 3.0 |
| Date | 2026-07-26 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-003 - Local MT5 Read-Only Market-Data Connector |

These instructions are for Windows PowerShell. The source application is Windows-first and local-first. Python's standard library, the committed Release 1 kernel, and the synthetic demonstration pack remain the baseline. The official `MetaTrader5` package is an optional local dependency and is imported only after explicit MT5 read-only use.

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

Synthetic mode is always the default. This command does not initialize MT5. The Market connection area returns a calm `MT5_DISABLED` state and does not display fake live values.

# 3. Start Explicit Local MT5 Read-Only Mode

Use this only after the separately governed local setup in `TRL_MT5_LOCAL_SETUP_GUIDE.md`. MetaTrader 5 must be installed and running on this PC, the operator must authenticate directly inside MT5, and the exact symbol must be visible in Market Watch.

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --enable-mt5-read-only --mt5-symbol XAUUSD --mt5-timeframes M1,M5,H4,D1 --mt5-bars 500
```

PRJ-017 never requests a login, password, investor password, broker server, API key, or remote host. Never put broker credentials on this command line. Only exact safe symbols, M1/M5/H4/D1, and 1 through 2,000 bars are accepted. No alternate symbol is selected automatically.

# 4. Start Without Opening a Browser

Use the no-browser option for testing or when you want to open the page yourself:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --no-browser
```

# 5. Open the Local URL

With the default port, open this local address:

```text
http://127.0.0.1:8765/
```

From another PowerShell window, the following opens only that local URL:

```powershell
Start-Process 'http://127.0.0.1:8765/'
```

No internet connection, Atlas service, cloud account, external font, content delivery network or analytics service is required.

# 6. Stop the Application

Return to the PowerShell window running the application and press:

```text
Ctrl+C
```

The application prints its shutdown status and closes its local listening socket.

# 7. Run the Tests

From the repository root, disable bytecode and run the Release 1, application, registry, and combined discovery tests:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_trading_lab.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_trading_lab_app.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_strategy_registry.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_mt5_connector.py

python -B -W error -m unittest discover -s 09_AI_Systems\02_Tools\Trading_Lab -p 'test*.py'
```

`-B` prevents Python bytecode files. `-W error` makes any Python warning fail validation.

# 8. Download and Remove Local Reports

The JSON and Markdown download buttons create files in the browser only. The server never silently writes a report. Your browser normally places them in the Windows Downloads folder.

To remove the two known downloaded demonstration filenames:

```powershell
$trlDownloads = Join-Path $env:USERPROFILE 'Downloads'
Remove-Item -LiteralPath (Join-Path $trlDownloads 'TRL-R2-001-synthetic-result.json') -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $trlDownloads 'TRL-R2-001-synthetic-paper-report.md') -ErrorAction SilentlyContinue
```

These commands target only the two explicitly named local downloads. They do not remove repository files.

# 9. Confirm the Closed Capability Boundary

While the local application is running, inspect its capability manifest:

```powershell
$trlCapabilities = Invoke-RestMethod 'http://127.0.0.1:8765/api/capabilities'
$trlCapabilities | Select-Object paper_research_only, local_mt5_read_only_connector_capability, local_mt5_order_capability, external_order_capability, credential_storage_capability, telemetry
$trlCapabilities.not_implemented
```

The narrow local read-only connector value is `True`. Local MT5 order, external order, credential storage, and telemetry values are `False`. The unavailable list includes certified broker compatibility, news, live strategy signals, positions and balances, strategy selection, order proposals, assisted execution, and automated execution.

There is no credential endpoint, account endpoint, position endpoint, order endpoint, hidden order control, or live-trading mode in TRL-R2-003.

# 10. Inspect the Local Market Boundary

```powershell
$trlConnection = Invoke-RestMethod 'http://127.0.0.1:8765/api/market-connection'
$trlSnapshot = Invoke-RestMethod 'http://127.0.0.1:8765/api/market-snapshot'
$trlConnection
$trlSnapshot.data_quality
```

In ordinary mode both routes return `MT5_DISABLED`. In explicitly enabled mode, values are broker-native and read-only. Commission is unknown, market-session state is unknown, no strategy is applied to MT5 data, and no order capability exists.

# 11. Inspect the Governed Strategy Registry

While the application is running, inspect the deterministic read-only registry document:

```powershell
$trlRegistry = Invoke-RestMethod 'http://127.0.0.1:8765/api/strategy-registry'
$trlRegistry.registry_health
$trlRegistry.installed_executable_strategies
$trlRegistry.research_backlog
$trlRegistry.vault
```

Health must be `VALID / REGISTRY_VALID`. The executable collection must contain only SMA-001 version 1.0.0. The separate backlog entries must all be `PLANNED_NOT_IMPLEMENTED` with `execution_eligible` equal to `False`.

The registry does not choose a best strategy. No strategy is approved for investment use. The optional local MT5 connector is a separate data-only surface and never invokes the registry or Release 1 evaluation. News, order proposals, and execution remain unavailable.
