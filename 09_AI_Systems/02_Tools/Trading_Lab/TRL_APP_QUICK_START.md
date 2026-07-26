# ALSAKKAF Trading Research Lab - Local Application Quick Start

> **PAPER/RESEARCH ONLY - COMMITTED SYNTHETIC DATA - NO BROKER - NO EXTERNAL ORDERS**

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R2-001-QUICK-START-001 |
| Document Type | Local Application Operator Guide |
| Status | ACTIVE FOR TRL-R2-001 SOURCE LAUNCH |
| Version | 1.0 |
| Date | 2026-07-26 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-001 - Portable Application Foundation |

These instructions are for Windows PowerShell. The source application is Windows-first and local-first. It uses only Python's standard library and the committed Release 1 kernel and synthetic demonstration pack.

# 1. Open the Repository

Open PowerShell and move to the repository root:

```powershell
Set-Location 'C:\ALSAKKAF_WT\PRJ017_CODEX'
```

# 2. Start the Application

Start the local dashboard and allow it to open the default browser:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app
```

The application binds only to `127.0.0.1`. It never falls back to `0.0.0.0` or another port. If port 8765 is already in use, stop the conflicting local process or choose an explicit unused local port:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --port 8876
```

# 3. Start Without Opening a Browser

Use the no-browser option for testing or when you want to open the page yourself:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --no-browser
```

# 4. Open the Local URL

With the default port, open this local address:

```text
http://127.0.0.1:8765/
```

From another PowerShell window, the following opens only that local URL:

```powershell
Start-Process 'http://127.0.0.1:8765/'
```

No internet connection, Atlas service, cloud account, external font, content delivery network or analytics service is required.

# 5. Stop the Application

Return to the PowerShell window running the application and press:

```text
Ctrl+C
```

The application prints its shutdown status and closes its local listening socket.

# 6. Run the Tests

From the repository root, run the Release 1 tests, application tests and combined discovery tests:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_trading_lab.py

python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\test_trading_lab_app.py

python -B -W error -m unittest discover -s 09_AI_Systems\02_Tools\Trading_Lab -p 'test*.py'
```

`-B` prevents Python bytecode files. `-W error` makes any Python warning fail validation.

# 7. Download and Remove Local Reports

The JSON and Markdown download buttons create files in the browser only. The server never silently writes a report. Your browser normally places them in the Windows Downloads folder.

To remove the two known downloaded demonstration filenames:

```powershell
$trlDownloads = Join-Path $env:USERPROFILE 'Downloads'
Remove-Item -LiteralPath (Join-Path $trlDownloads 'TRL-R2-001-synthetic-result.json') -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $trlDownloads 'TRL-R2-001-synthetic-paper-report.md') -ErrorAction SilentlyContinue
```

These commands target only the two explicitly named local downloads. They do not remove repository files.

# 8. Confirm the Closed Capability Boundary

While the local application is running, inspect its capability manifest:

```powershell
$trlCapabilities = Invoke-RestMethod 'http://127.0.0.1:8765/api/capabilities'
$trlCapabilities | Select-Object paper_research_only, broker_capability, external_order_capability, credential_storage_capability, telemetry
$trlCapabilities.not_implemented
```

The four capability values for broker, external order, credential storage and telemetry must be `False`. The not-implemented list must include live data, broker connectivity, assisted execution, automated execution, external orders, customer funds and personalized investment advice.

There is no broker endpoint, credential endpoint, order endpoint, hidden order control or live-trading mode in TRL-R2-001.
