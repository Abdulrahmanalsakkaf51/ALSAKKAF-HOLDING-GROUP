# TRL-R2-013 ALSAKKAF SCALPING Operational Dashboard Hotfix Contract

> **MT5 DEMO ACCOUNT ONLY — NO ORDER_CHECK — NO ORDER_SEND — NO DEMO_AUTO
> ENTRY BY THIS CHECKPOINT — DEMO AUTO REMAINS DASHBOARD-LOCKED PENDING A
> SEPARATELY GOVERNED BROKER EXECUTION PROOF**

Product name displayed everywhere: **ALSAKKAF SCALPING**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-013 (accelerated operational hotfix, single sprint) |
| Status | Founder-authorized this session via the TRL-R2-013 accelerated prompt |
| Depends on | `TRL_R2_012_ALSAKKAF_SCALPING_DEMO_AUTOMATION_V0_CONTRACT.md` (unmodified — this checkpoint corrects integration/usability defects discovered during the Founder's first real launch of that implementation; it does not reopen R2-012's execution model, risk policy, ladder logic, or journal schema), `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (`ModeService` authority, unmodified) |
| Feeds | No later phase. Narrowly fixes the operational gap between "R2-012 tests pass" and "the Founder can actually use the dashboard for real read-only MT5 demo analysis." Does not authorize Phase 7, `DEMO_AUTO` entry, or any broker mutation. |

---

## 0. Numbering and classification decision

Numbered **TRL-R2-013**, an operational hotfix on top of the closed and
pushed R2-012 checkpoint (commit range `02c48e0..0edd4ad`). Recorded as an
additional row, **Phase 6C-1 — ALSAKKAF SCALPING Operational Dashboard
Hotfix (TRL-R2-013)**, in `TRL_FULL_VISION_MASTER_PROGRAM.md`, immediately
after Phase 6C. Not Phase 7; does not reorder Phases 7-14.

## 1. Problem statement (Founder-observed, this session)

The Founder's first real launch of the R2-012 dashboard against the
already-authenticated local MT5 DEMO terminal showed: the server starts and
the HTML shell renders, but (a) operating mode stayed `OFF` because the
launcher never requested a mode transition; (b) the ALSAKKAF SCALPING
product state stayed `OFF` for the same reason; (c) `Demo Verified`,
`Equity`, `Daily P&L`, and `Last Decision` were placeholders because no
server-side analysis had ever run; (d) the dashboard's `MT5 CONNECTION: OK`
badge was in fact derived from `ScalpingService.status_document()`'s
`journal_startup_diagnostic_code`, never from a real terminal/account read;
(e) there was no symbol/profile configuration workflow the browser could
drive to a persisted result — `configure_profile`/`save_symbol_map` existed
as service methods but nothing in the UI called them meaningfully and
`_profiles`/`_risk_settings`/`_max_spread_points` were held only in
`ScalpingService`'s process memory, never persisted, so they could not
survive a restart even if set; (f) the only analysis route,
`/api/scalping-run-cycle`, required the browser to supply
`entry_bars`/`confirmation_bars`/`current_price`/`spread` JSON — the
browser never did, and no ordinary operator can construct that JSON by
hand; (g) there was no read-only monitoring loop; (h) `Start demo auto`
was rendered as an active, clickable control before any of the above was
proven to work.

This checkpoint corrects (a)-(h) without touching R2-012's execution
model, ladder/risk math, journal event vocabulary, or the `DEMO_AUTO`
capability gate.

## 2. Scope boundary (explicit, matches the Founder's authorization)

**In scope:** safe `RESEARCH`/`ANALYZE_ONLY` startup; a server-authoritative
live-analysis path that fetches its own bars/quote from the real MT5
adapter; a sanitized live-status document with explicit unavailable
reasons; a corrected MT5-connection indicator separate from journal health;
usable dashboard controls for connection recheck, symbol discovery/mapping,
profile/side/risk/spread/event-risk configuration, `Run Analysis Now`,
read-only monitoring start/stop/pause/resume, emergency stop/reset;
persisted configuration; new HTTP routes and CLI commands; a locked/greyed
`DEMO AUTO` control; UI quality fixes.

**Out of scope (unchanged from R2-012, still hard-blocked):**
`order_check`, `order_send`, opening/modifying/cancelling an order,
opening/modifying/closing a position, `DEMO_AUTO` execution, real-money
trading, a real/contest account, continuous unattended automation,
martingale, grid recovery, lot escalation, guaranteed-profit claims, Phase
7. `ScalpingService.request_state_change("DEMO_AUTO", ...)` is not called
anywhere in this checkpoint's new code, its tests, or its rehearsals.

## 3. Root causes (confirmed by reading the R2-012 implementation, not assumed)

1. `Start_ALSAKKAF_SCALPING_DEMO.ps1` never requested any `ModeService`
   transition and never requested any `ScalpingService` product-state
   transition — it only checked the `MetaTrader5` import and launched the
   process. Operating mode and product state therefore always resolved to
   whatever was last durably persisted (`OFF`/`OFF` on a clean profile).
2. `ScalpingService.status_document()` (contract Section 15 of R2-012's
   evidence) exposes `journal_startup_diagnostic_code`, which the R2-012
   dashboard's `MT5 CONNECTION` badge was wired to — that field describes
   journal-store integrity, not `terminal_info()/account_info()` truth.
3. `ScalpingService.__init__` resets `_profiles`, `_risk_settings`,
   `_max_spread_points` to defaults on every construction; `configure_profile`/
   `set_event_risk_block` write to a `SymbolMapStore`-adjacent structure
   only for the symbol map and event-risk flag — profile/side/risk/spread
   settings are never persisted at all.
4. `ScalpingService.analyze`/`run_cycle` (R2-012 Section 9's documented
   accelerated-V0 boundary) require the caller to already have
   `entry_bars`/`confirmation_bars`/`current_price`/`spread` — no code
   anywhere in `alsakkaf_scalping_mt5.py` fetches OHLC bars from MT5
   (`copy_rates_from_pos` is not in `RealScalpingMT5Adapter`'s allowlist or
   method set at all; only `symbol_info`/`symbol_info_tick` are). The
   `/api/scalping-run-cycle` HTTP route is a thin pass-through of
   browser-supplied JSON with no server-side data-sourcing path.
5. `app.py`'s real running `_scalping_service_for_mode(...)` call site
   (inside `main()`) never passes `scratch_directory=`, so
   `strategy.run_r2010_bridge`'s `os.makedirs(scratch_directory, ...)`
   would raise `TypeError` the first time a real `TRADE_CANDIDATE` reached
   the bridge in production — an additional, previously untriggered defect
   found while building this checkpoint's server-authoritative path.
6. No monitoring loop, no `Run Analysis Now` HTTP route wired to a real
   data source, and `Start demo auto` was rendered as a normal enabled
   button in `static/index.html`, ahead of any of the above being proven.

## 4. Corrected safe startup (launcher)

`Start_ALSAKKAF_SCALPING_DEMO.ps1` is rewritten to, in order: verify Python
on `PATH`; verify the `MetaTrader5` import; run a bounded read-only Python
probe (new `alsakkaf_scalping_cli.py scalping-recheck` command) that calls
`mt5.initialize()/terminal_info()/account_info()/shutdown()` exactly once
and reports terminal-connected, account-is-demo, account-trade-allowed, and
Algo-Trading-enabled truthfully, without requiring Algo Trading for
`ANALYZE_ONLY`; refuse a duplicate listener on the target port exactly as
before; resolve the repository directory exactly as before; request
`RESEARCH` via `python -m trading_lab_app.mode_cli request-mode RESEARCH
--actor "ALSAKKAF_SCALPING_LAUNCHER" --reason "R2-013 safe launch"`
(the existing governed CLI, unmodified); request `ANALYZE_ONLY` via the
existing `python -m trading_lab_app.alsakkaf_scalping_cli scalping-resume`
command (already a valid `OFF -> ANALYZE_ONLY` transition per R2-012
Section 3, unmodified); then start the dashboard process and open it
directly at `http://127.0.0.1:8765/#alsakkaf-scalping`. If the MT5 recheck
reports the terminal disconnected or the account not proven DEMO, the
launcher still starts the dashboard (so the Founder can see the exact
blocking reason on-screen) but prints the true condition instead of a
generic success line, and never silently continues by requesting
`RESEARCH` if the recheck could not run the MT5 package import check at
all. The launcher never requests `DEMO_AUTO` and never calls
`scalping-start-demo-auto`. `Stop_ALSAKKAF_SCALPING_DEMO.ps1` is extended to
additionally request `python -m trading_lab_app.alsakkaf_scalping_cli
scalping-monitoring-stop` before the existing pause/emergency-stop
fallback, then transition the product state to `OFF` (existing pause
already does this via `ANALYZE_ONLY`... final `OFF` is requested
explicitly via a new bounded stop sequence: pause -> request `OFF`),
returns operating mode to `OFF` via `python -m trading_lab_app.mode_cli
request-mode OFF`, then stops only the confirmed owned process exactly as
before.

## 5. Server-authoritative live analysis path

New `trading_lab_app/alsakkaf_scalping_runtime.py` module, wrapping a
`ScalpingService` instance with no change to that service's public state
machine. Adds:

- `RealScalpingMT5Adapter.fetch_completed_bars(broker_symbol, timeframe,
  count)` (new adapter method, `alsakkaf_scalping_mt5.py`, mirroring
  `mt5_connector.py`'s existing `copy_rates_from_pos` pattern exactly —
  same lazy import, same allowlist technique, same
  `market_data.normalize_bars` reuse) for `M1, M5, M15, H1, H4` (the two
  additional constants, `TIMEFRAME_M15`/`TIMEFRAME_H1`, added to a local
  allowlist private to this adapter — `mt5_connector.py` itself is not
  modified). Uses `start_pos=1` so the currently-forming bar is always
  excluded (contract Section 8.1 of R2-012's "closed bars only" rule,
  reused, never weakened) and returns exactly `count` closed bars, oldest
  first. `FakeScalpingAdapter`/`DisabledScalpingAdapter` gain matching
  deterministic/refused implementations for tests.
- `ScalpingRuntime.analyze_now(canonical_instrument)`: resolves the
  broker symbol from the persisted mapping, resolves the active profile's
  entry/confirmation timeframes
  (`alsakkaf_scalping_strategy.CONFIRMATION_TIMEFRAME_FOR_PROFILE`, plus a
  new `ENTRY_TIMEFRAME_FOR_PROFILE` mapping in the same module: `M1` for
  Precision Scalping/Breakout Ladder, `M15` for Intraday), fetches a fresh
  tick (`adapter.symbol_status`) and completed entry/confirmation bars via
  the new adapter method, then calls the existing, unmodified
  `ScalpingService.run_cycle(...)` with those server-fetched values. The
  prior `/api/scalping-run-cycle` route (browser-supplied bars) is
  **removed from the routes the production dashboard ever calls** and
  retained only as `service.py`'s already-existing function, now reachable
  solely through the test suite's direct service calls, never through an
  HTTP path the shipped `static/app.js` uses — the HTTP route itself is
  removed from `SCALPING_MUTATION_API_ROUTES` and replaced by
  `/api/scalping-analyze-now`, which never accepts a market-data field in
  its request body (an empty JSON object `{}` is the only accepted body;
  any market-data-shaped key present is rejected with
  `SCALPING_CLIENT_MARKET_DATA_REJECTED`).
- Insufficient bar history, a stale quote, or a disconnected terminal fail
  closed with an explicit reason (`HISTORY_INSUFFICIENT`,
  `QUOTE_UNAVAILABLE`, `TERMINAL_NOT_CONNECTED`) and never fabricate a
  result.
- `_scalping_service_for_mode` in `app.py` is corrected to pass a real
  `scratch_directory` (the same `%LOCALAPPDATA%\ALSAKKAF\TradingLab\scratch`
  directory pattern already used elsewhere in this program), fixing root
  cause 5 above.

## 6. Live status document

`ScalpingRuntime.live_status_document(canonical_instrument=None)` returns a
single sanitized document (`TRL_SCALPING_LIVE_STATUS.v1`) carrying every
field enumerated in the originating prompt Section 7: application/operating
mode/product state, real adapter tier, MT5 package/terminal/account/session
truth (Section 7 below), redacted account suffix, currency, leverage,
balance, equity, daily P&L, session drawdown, instrument/mapping/profile/
side/event-risk state, quote and symbol metadata, completed-bar readiness,
monitoring status, last-analysis summary (classification, direction, score,
six categories, indicators, support/resistance, reasons, blocker), owned
cycle/order/position counts, emergency-stop state, journal health, and
`last_update_utc`. Any field that cannot be produced carries an explicit
string reason from the fixed set `TERMINAL_NOT_CONNECTED`,
`ACCOUNT_NOT_DEMO`, `SYMBOL_NOT_MAPPED`, `QUOTE_UNAVAILABLE`,
`HISTORY_INSUFFICIENT`, `ANALYSIS_NOT_RUN`, `OPERATING_MODE_NOT_RESEARCH`
— never a bare `null`/dash with no explanation attached in the same
response.

## 7. Corrected MT5 connection indicator

`mt5_connected` in the live-status document is `true` only when, in the
same read: `MetaTrader5` imports, `mt5.initialize()` succeeds,
`terminal_info().connected` is `True`, `account_info()` is readable, and
`account_info().trade_mode == ACCOUNT_TRADE_MODE_DEMO`. `journal_health`
is reported as an independent field
(`ScalpingService.status_document()["journal_startup_diagnostic_code"]`,
unchanged, just no longer conflated with `mt5_connected` in the UI or the
new document). The dashboard's `MT5 CONNECTION` badge reads `mt5_connected`
only; a new `JOURNAL HEALTH` badge reads `journal_health` only.

## 8. Configuration persistence

New `TRL_SCALPING_CONFIG.v1` schema and `ScalpingConfigStore`/
`InMemoryScalpingConfigStore` in `alsakkaf_scalping_data.py` (same
atomic-temp-file-plus-`os.replace` technique as `SymbolMapStore`), storing
per-instrument `profile_id`, `side_restriction`, `max_spread_points`, and
global `risk_settings` and `monitoring_interval_seconds`. `ScalpingService`
accepts an optional `config_store` and loads it at construction (falling
back to defaults exactly as today when no store or an empty store is
supplied — no behavior change for existing R2-012 callers/tests that do not
pass one); `configure_profile`/a new `configure_side` persist through it
immediately. Editable only while the product state is not `DEMO_AUTO`
(mirrors R2-012 Section 7's `OFF`-only rule for the symbol map, slightly
relaxed to allow reconfiguration during `ANALYZE_ONLY`/`PAUSED` inspection,
since no order authority exists until `DEMO_AUTO`; still rejected during
`DEMO_AUTO` with `SCALPING_CONFIG_REQUIRES_NON_AUTO_STATE`).

## 9. Dashboard controls and Demo Auto lock

`static/index.html`/`static/app.js` are rewritten (additive to the existing
badges) with: connection recheck, canonical-instrument selector, discover
broker symbols, candidate selection, save mapping, profile/side/risk/
spread/event-risk-block controls, save configuration, `Run Analysis Now`,
start/stop read-only monitoring, pause/resume analysis, emergency stop/
reset. `Start demo auto` is replaced by a permanently disabled control
labelled exactly `DEMO AUTO — LOCKED PENDING BROKER EXECUTION PROOF`; no
code path in `static/app.js` enables it or calls
`/api/scalping-start-demo-auto`. The R2-012 backend `DEMO_AUTO` transition
path (`ScalpingService.request_state_change("DEMO_AUTO")`,
`/api/scalping-start-demo-auto`, `scalping-start-demo-auto` CLI command)
remains implemented and unit-tested exactly as it already was — this
checkpoint only removes the dashboard's ability to invoke it, per the
Founder's explicit instruction.

## 10. Read-only monitoring

`ScalpingRuntime` adds a single background daemon thread per running
process, started only by an explicit `scalping-monitoring-start`
call, bounded interval `5-300` seconds (default `15`), calling
`analyze_now` on a fixed schedule with a re-entrancy guard (a single
`threading.Lock` acquired non-blocking; an already-running analysis skips
that tick rather than overlapping). Before each tick it re-checks: account
still DEMO, terminal still connected, product state still
`ANALYZE_ONLY`/`DEMO_AUTO`, operating mode still grants
`market_intelligence_research`/is `RESEARCH`-family, not
`EMERGENCY_STOP` — any failed check stops monitoring immediately and
records the stopping reason. The monitor never calls
`request_state_change("DEMO_AUTO")` itself. `scalping-monitoring-stop`,
process shutdown, and `EMERGENCY_STOP` all join the thread with a bounded
timeout before returning/exiting; no thread survives server shutdown.

## 11. New HTTP routes

Read-only `GET`: `/api/scalping-live-status`,
`/api/scalping-configuration`, `/api/scalping-symbol-candidates/<INSTRUMENT>`
(existing, unchanged), `/api/scalping-latest-analysis`,
`/api/scalping-monitoring-status`, `/api/scalping-journal` (existing,
unchanged). Mutation `POST` (existing action-token gate, unchanged
mechanism): `/api/scalping-recheck`, `/api/scalping-save-symbol-map`
(existing, unchanged), `/api/scalping-save-configuration`,
`/api/scalping-analyze-now` (replaces `/api/scalping-run-cycle` as the
dashboard's analysis path; the old route is removed),
`/api/scalping-monitoring-start`, `/api/scalping-monitoring-stop`,
`/api/scalping-pause` (existing), `/api/scalping-resume` (existing),
`/api/scalping-emergency-stop` (existing), `/api/scalping-emergency-reset`
(existing). No route accepts or returns a raw candle/price value as an
authoritative input; every mutation still requires the local-host header
and the exact `X-Scalping-Action-Token`.

## 12. CLI commands

`alsakkaf_scalping_cli.py` gains `scalping-live-status`, `scalping-recheck`,
`scalping-save-configuration`, `scalping-show-configuration`,
`scalping-analyze-now`, `scalping-monitoring-start`,
`scalping-monitoring-stop`, `scalping-monitoring-status`,
`scalping-latest-analysis`; existing `scalping-discover-symbols`,
`scalping-save-symbol-map`, `scalping-configure-profile`,
`scalping-pause`, `scalping-resume`, `scalping-emergency-stop`,
`scalping-reset-emergency-stop`, `scalping-list-cycles`,
`scalping-journal` are unchanged. `scalping-analyze`/`scalping-run-cycle`'s
existing `SCALPING_ANALYZE_REQUIRES_BAR_INPUT`/
`SCALPING_RUN_CYCLE_REQUIRES_BAR_INPUT` V0 stubs are superseded by
`scalping-analyze-now`, which fetches its own bars exactly like the new
HTTP route (no operator ever constructs a candle JSON array by hand).

## 13. UI quality

The dashboard opens directly at `#alsakkaf-scalping`; the top status area
distinguishes `LOCAL`, `MT5 DEMO`, `ANALYZE ONLY`, and `LIVE MONEY LOCKED`
as four independent facts rather than one generic "PAPER/RESEARCH ONLY"
label; every new render function uses `textContent`/safe DOM creation only
(no `innerHTML`); live status refreshes every 5 seconds; heavy analysis
runs only on an explicit `Run Analysis Now` click or while monitoring is
enabled (never on the 5-second status poll); empty/loading/terminal-
disconnected/symbol-unmapped/analysis-not-yet-run states each render a
specific, human-readable message instead of an empty table or an
unexplained dash; a browser refresh re-reads persisted configuration and
server-side monitoring status rather than resetting either.

## 14. File scope

New: `alsakkaf_scalping_runtime.py`,
`TRL_R2_013_ALSAKKAF_SCALPING_OPERATIONAL_DASHBOARD_HOTFIX_CONTRACT.md`,
`TRL_R2_013_ALSAKKAF_SCALPING_OPERATIONAL_DASHBOARD_HOTFIX_EVIDENCE.md`,
`test_alsakkaf_scalping_operational_dashboard.py`,
`test_alsakkaf_scalping_live_analysis.py`.

Modified: `Start_ALSAKKAF_SCALPING_DEMO.ps1`,
`Stop_ALSAKKAF_SCALPING_DEMO.ps1`, `trading_lab_app/app.py` (scratch
directory fix, wiring), `trading_lab_app/server.py` (new routes, removal of
`/api/scalping-run-cycle` from the dashboard-facing mutation set),
`trading_lab_app/service.py` (new HTTP document wrappers),
`trading_lab_app/alsakkaf_scalping_data.py` (config store),
`trading_lab_app/alsakkaf_scalping_mt5.py` (bar-fetch method),
`trading_lab_app/alsakkaf_scalping_service.py` (config persistence, minor
additive hooks), `trading_lab_app/alsakkaf_scalping_cli.py` (new commands),
`trading_lab_app/static/index.html`, `trading_lab_app/static/app.js`,
existing R2-012 test modules only where a new keyword-argument default
must be exercised (never weakened), `TRL_APP_QUICK_START.md`,
`TRL_BLOCKERS.md`, `TRL_FULL_VISION_MASTER_PROGRAM.md`,
`TRL_CONTINUATION_STATE.md`, `TRL_CONTINUATION_STATE.json`,
`TRL_DECISION_LOG.md`.

Not modified: `TRL_R2_010`/`TRL_R2_011`/`TRL_R2_012` contracts, their
source and tests, Phase 5/6 contracts/source/tests, `main`.

## 15. Testing

New coverage (fake adapter; zero real broker mutation in the automated
suite) across: safe launcher mode/state sequencing (via the underlying CLI
calls the script issues), MT5-connection-vs-journal-health separation,
persisted configuration surviving a fresh `ScalpingService` construction,
server-side bar/quote fetch excluding the current candle, rejection of a
client-supplied market-data field on the analyze-now route, monitoring
start/stop/interval bounds/no-overlap/stale-quote-block/disconnect-stop/
non-demo-stop/mode-change-stop/emergency-stop-stop, Demo Auto control
absence/lock in the rendered dashboard, no `innerHTML` in new rendering,
localhost-only and action-token gating on every new route, and zero
`order_check`/`order_send` calls anywhere in the new test modules.

## 16. Explicit statement

This checkpoint does not grant, widen, or exercise `DEMO_AUTO`,
`order_check`, or `order_send` anywhere in its new code, tests, or
rehearsals. `MT5_LIVE_MANUAL`/`MT5_LIVE_AUTOMATED` remain fully
unavailable, unchanged. The only broker-facing calls this checkpoint's real
rehearsal may make are the read-only set already enumerated in the
originating prompt Section 19: `initialize`, `version`, `terminal_info`,
`account_info`, `symbols_get`, `symbol_info`, `symbol_info_tick`,
`copy_rates`, `orders_get`, `positions_get`, `shutdown`.
