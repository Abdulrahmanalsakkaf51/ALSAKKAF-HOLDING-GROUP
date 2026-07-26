# ALSAKKAF HOLDING GROUP

# TRL-R2-001 Application Foundation Contract

> "WINDOWS-FIRST - LOCAL-FIRST - PAPER/RESEARCH ONLY - SYNTHETIC DATA - NO EXTERNAL ORDERS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R2-001-APP-CONTRACT-001 |
| Title | Portable Application Foundation and Local Dashboard Shell |
| Status | IMPLEMENTED AND LOCALLY VALIDATED WITHIN THE AUTHORIZED SYNTHETIC PAPER/RESEARCH BOUNDARY |
| Version | 1.0 |
| Date | 2026-07-26 |
| Owner and Founder | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-001 - Portable Application Foundation |
| Release 1 Baseline | Git `f223367`; stable kernel checkpoint `TRL-R1-004` |
| Application Version | `2.0.0-r2.001` |

# 1. Founder Authorization

Abdulrahman Yaseen Alsakkaf explicitly authorized TRL-R2-001 on 2026-07-26. The authorization is limited to a Windows-first, local-first application foundation and polished functional dashboard powered only by committed synthetic demonstration data and the Release 1 paper/research kernel.

The authorization does not include external or live market data, customer distribution, subscriptions, credentials, broker connectivity, order submission, assisted execution, automated execution, live trading, customer funds, personalized investment advice, or a later checkpoint.

# 2. Implemented Scope

TRL-R2-001 implements:

- A side-effect-free Python application package using only the standard library.
- A read-only application service that invokes the committed Release 1 kernel with independent input copies.
- A fixed IPv4 loopback HTTP server and explicit lifecycle command.
- Exact API endpoints for health, versions, capabilities, synthetic market data, deterministic results and deterministic reports.
- An offline browser-native HTML, CSS, JavaScript and Canvas dashboard.
- Interactive synthetic price, SMA, research-event, marked-equity and drawdown charts.
- Accessible chart descriptions, keyboard point navigation and tabular fallbacks.
- In-browser JSON and Markdown downloads that do not write server-side files.
- A machine-readable, fail-closed capability manifest.
- Focused application, service, security, provenance, user-interface and negative-surface tests.

This application displays a historical synthetic replay. It does not implement the future `INSIGHT_MODE` product experience or the future forward `PAPER_MODE` portfolio service.

# 3. Explicit Exclusions

The following are absent and unauthorized:

- External or live market data and market-data adapters.
- Forward paper portfolio state or service.
- Strategy Registry and Vault.
- Independent Risk Guardian service and persistent audit ledger.
- Accounts, authentication, subscriptions, payments and customer distribution.
- Broker or venue credentials, storage, connectivity or adapters.
- Order preparation, submission, amendment, cancellation or reconciliation.
- Assisted execution, automated execution and live trading.
- Customer funds, custody and personalized investment advice.
- Atlas integration or any mandatory cloud service.
- Installation packaging and claims of macOS or Linux support.

# 4. Module Ownership

| Module | Ownership |
|--------|-----------|
| `trading_lab_app/__init__.py` | Application identity and inert package contract. |
| `trading_lab_app/__main__.py` | Direct/module launch entry point and alternate-working-directory bootstrap. |
| `trading_lab_app/app.py` | Command-line parsing, browser option, startup, shutdown and clear port-failure reporting. |
| `trading_lab_app/server.py` | Fixed localhost bind, exact routes, method denial, security headers and deterministic UTF-8 transport. |
| `trading_lab_app/service.py` | Module-relative synthetic fixture loading, independent input copies, Release 1 invocation and view documents. |
| `trading_lab_app/capabilities.py` | Closed machine-readable capability manifest. |
| `trading_lab_app/static/index.html` | Semantic dashboard structure, disclosures and accessible fallbacks. |
| `trading_lab_app/static/styles.css` | Responsive institutional-finance visual system and reduced-motion behavior. |
| `trading_lab_app/static/app.js` | Read-only local data loading, charts, keyboard inspection, tables, states and browser downloads. |
| `test_trading_lab_app.py` | Application behavior, security, compatibility and negative-surface evidence. |

The Release 1 files remain independently owned by the Release 1 contract. The application package is outside the Release 1 engine-source manifest.

# 5. Localhost and Security Boundary

The server binds to the literal IPv4 address `127.0.0.1`. No host argument or fallback can select `0.0.0.0`. A port collision produces a clear startup failure and does not select another port.

Only six exact read-only API paths and four exact static paths are served. Unsupported methods return HTTP 405. Encoded paths, parent traversal and backslash traversal are rejected; unknown paths receive HTTP 404. Non-local HTTP `Host` values receive HTTP 421 to reduce DNS-rebinding exposure.

Every response carries no-store caching, MIME sniffing prevention, frame denial, no-referrer, restricted permissions, same-origin opener policy and a restrictive Content Security Policy. The policy denies resources by default, permits only same-origin scripts, styles and API connections, and denies objects, forms, framing, external fonts and base changes.

The application performs no outbound request, telemetry or analytics. It has no arbitrary path, command or user-code execution. It accepts no upload, credential, account, payment or order payload.

# 6. Dashboard Capabilities

The dashboard provides:

- An overview of mode, synthetic freshness, outcome, reason, paper cash, marked equity, P&L, costs, drawdown and position status.
- A responsive synthetic close chart with fast/slow SMA overlays and research entry/exit-event markers.
- Marked-equity and drawdown charts with the negative 15% halt reference.
- Research-signal timestamps, strategy identity, event explanations, stable reason codes, source/freshness and a non-instruction label.
- SMA-001 parameters, experimental status, definition hash and the explicit lack of Founder investment approval.
- Full Markdown and machine-readable results, browser-only downloads and all reproducibility identifiers.
- System risk limits and the closed broker/external-order boundary.
- Honest planned, disabled and prohibited future-mode states without action controls.
- Application/kernel versions, checkpoint, release disclaimer and Atlas as a future optional adapter only.

The design includes semantic regions and headings, a skip link, visible focus styles, keyboard chart inspection, accessible tables, sufficient contrast, responsive desktop/tablet/small-screen behavior and reduced-motion support.

# 7. Synthetic-Data Boundary

The only market fixture is committed `sample_data/TRL-PACK-DEMO.json`. It is loaded from a path resolved from the application module, not the process working directory. The service does not accept a user path or remote URL.

Every service evaluation loads a fresh JSON value and passes independent deep copies of both the strategy definition and market pack to Release 1. The source fixture and application-owned strategy template remain unchanged. The dashboard labels the data synthetic and records its source, quality note, static freshness and `as_of` date.

# 8. Release 1 Compatibility Evidence

At baseline `f223367`, the original 132 tests passed with bytecode disabled and warnings treated as errors. After application implementation, the same direct suite passed again and the combined discovery suite passed.

The committed demonstration retains:

| Field | Preserved value |
|-------|-----------------|
| Run ID | `TRL-RUN-6922AEA31AE2630B4DA1` |
| Input-data hash | `6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56` |
| Configuration hash | `3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd` |
| Strategy-definition hash | `e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955` |
| Engine-source digest | `f9f555d37e0820c39eb2afe1156fca4912d255debc23c7ab27c6111c31da3952` |
| Outcome / reason | `HYPOTHETICAL_FILL` / `OPEN_TERMINAL_POSITION` |
| Final cash / marked equity | `94.9975` / `100.22673707083118` paper units |
| Realized / unrealized P&L | `0.0` / `0.2267370708311804` paper units |
| Commission / slippage | `0.0025` / `0.002498750624687196` paper units |
| Maximum drawdown | `-0.03237704819428881%` |

The engine-source manifest remains exactly the Release 1 facade and eight `trading_lab_core` files. No application, static, documentation or application-test file enters that manifest.

# 9. Test Evidence

Validation on 2026-07-26 uses Python bytecode suppression and treats warnings as errors.

```text
python -B -W error 09_AI_Systems/02_Tools/Trading_Lab/test_trading_lab.py
Ran 132 tests
OK

python -B -W error 09_AI_Systems/02_Tools/Trading_Lab/test_trading_lab_app.py
Ran 23 tests
OK

python -B -W error -m unittest discover -s 09_AI_Systems/02_Tools/Trading_Lab -p 'test*.py'
Ran 155 tests
OK
```

Warnings: zero. The tests cover import safety, root and alternate-working-directory launch, browser suppression, port conflict, fixed loopback binding, exact endpoints, deterministic UTF-8 JSON, static allowlisting, traversal, method rejection, local Host enforcement, security headers, deterministic result, independent inputs, exact Release 1 provenance, report rendering, serialization, closed capabilities, required dashboard content, accessibility structure, local assets and artifact absence.

The dashboard was also served from the repository root with `--no-browser`; its HTML and all six local API endpoints returned successfully through `127.0.0.1`. The process was then shut down without persisting a report.

# 10. Known Limitations

- This checkpoint validates source launch on the current Windows environment; it does not provide or test an installer.
- macOS and Linux are portability targets only and are untested.
- The interface shows one fixed, synthetic, historical, single-instrument SMA-001 run.
- The fixed costs and historical replay remain Release 1 engineering assumptions, not market-realistic evidence.
- There is no persistent application state; browser downloads go to the browser-configured download location.
- There is no identity, entitlement, cloud, Atlas, adapter, live-data or forward-paper service.
- Localhost restriction and negative-surface tests are scoped engineering controls, not a security certification.
- No strategy is approved for investment use and no product/customer distribution is authorized.

# 11. Definition of Done

TRL-R2-001 is done within its authorized boundary because:

- The application starts from the repository root and resolves its own assets and committed fixture.
- The dashboard and all data views operate without internet access.
- Synthetic charts, signal explanations, risk information and deterministic reports function.
- Release 1 source and tests remain unmodified, and Release 1 provenance and behavior remain identical.
- Direct Release 1, direct application and combined discovery tests pass with zero warnings.
- No external network, broker, credential, order, payment, account, customer-fund or personalized-advice capability exists.
- No cache, bytecode or generated report artifact is required or retained.
- Only authorized Trading Lab files are changed and no changes are staged, committed or pushed by this checkpoint work.

This definition does not establish customer, commercial, legal, regulatory, strategy, security, packaging or live-trading readiness.

# 12. Proposed Next Checkpoint

The exact proposed next checkpoint is **TRL-R2-002 - GOVERNED STRATEGY REGISTRY AND VAULT**.

TRL-R2-002 is proposed only. This contract does not authorize starting it, modifying its scope, implementing a strategy approval workflow, or enabling any later capability.
