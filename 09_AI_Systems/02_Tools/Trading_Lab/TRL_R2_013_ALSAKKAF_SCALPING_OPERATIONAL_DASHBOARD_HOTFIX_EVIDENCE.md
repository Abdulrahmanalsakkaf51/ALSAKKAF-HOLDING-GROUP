# TRL-R2-013 ALSAKKAF SCALPING Operational Dashboard Hotfix Evidence

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-013 (accelerated operational hotfix, single sprint) |
| Status | Implementation complete, including the same-session Founder shutdown-correction addendum (Section 19). Founder visually accepted the operational dashboard and the corrected shutdown. **Locally committed this session; remote push remains a separate, later, Founder-authorized step.** See `git status`/`git rev-parse HEAD` directly for the exact current state. |
| Related contract | `TRL_R2_013_ALSAKKAF_SCALPING_OPERATIONAL_DASHBOARD_HOTFIX_CONTRACT.md` |

---

## 1. Governing contract and problem statement

`TRL_R2_013_ALSAKKAF_SCALPING_OPERATIONAL_DASHBOARD_HOTFIX_CONTRACT.md`,
authored this session. The Founder's first real launch of the closed
R2-012 dashboard, against the already-authenticated local MT5 DEMO
terminal, found the server started and the HTML shell rendered, but the
dashboard was not operational (contract Section 1/3 lists every observed
symptom in full). This checkpoint corrects it without touching R2-012's
execution model, risk policy, ladder logic, journal event vocabulary, or
the `DEMO_AUTO` capability gate.

## 2. Root causes (confirmed by reading the R2-012 implementation)

1. `Start_ALSAKKAF_SCALPING_DEMO.ps1` never requested any `ModeService` or
   `ScalpingService` product-state transition — it only checked the
   `MetaTrader5` import and launched the process. Operating mode and
   product state therefore always resolved to whatever was last durably
   persisted (`OFF`/`OFF` on a clean profile).
2. The dashboard's `MT5 CONNECTION` badge was wired to
   `status_document()["journal_startup_diagnostic_code"]` — journal-store
   integrity, not a real `terminal_info()`/`account_info()` read.
3. `ScalpingService.__init__` reset `_profiles`/`_risk_settings`/
   `_max_spread_points` to defaults on every construction; nothing
   persisted profile/side/risk/spread/monitoring-interval configuration.
4. No code in `alsakkaf_scalping_mt5.py` fetched OHLC bars from MT5 at all
   (`copy_rates_from_pos` was not in `RealScalpingMT5Adapter`'s allowlist
   or method set); the only analysis route,
   `/api/scalping-run-cycle`, required the browser to already have
   `entry_bars`/`confirmation_bars`/`current_price`/`spread`, which it
   never supplied.
5. The real running `_scalping_service_for_mode` call site in `app.py`
   never passed `scratch_directory=`, so `strategy.run_r2010_bridge`'s
   `os.makedirs(scratch_directory, ...)` would raise `TypeError` the first
   time a real `TRADE_CANDIDATE` reached the bridge in production —
   previously untriggered because no dashboard analysis workflow ever ran.
6. No read-only monitoring loop existed, and `Start demo auto` rendered as
   an ordinary enabled button ahead of any of the above being proven.

## 3. Corrected safe launcher

`Start_ALSAKKAF_SCALPING_DEMO.ps1` now: verifies Python and the
`MetaTrader5` import (unchanged), runs a real read-only
`scalping-recheck` and prints the true terminal-connected/demo-verified
state, requests `RESEARCH` via `python -m trading_lab_app.mode_cli
request-mode RESEARCH` (the existing governed CLI, unmodified), requests
`ANALYZE_ONLY` via the existing `scalping-resume` command (unmodified),
then starts the server with `--open-fragment alsakkaf-scalping` so the
browser opens directly at `http://127.0.0.1:8765/#alsakkaf-scalping`.
Never requests `DEMO_AUTO`. `Stop_ALSAKKAF_SCALPING_DEMO.ps1` additionally
stops read-only monitoring, requests product state `OFF` via a new
`scalping-stop` CLI command (which deliberately refuses while
`EMERGENCY_STOP` is latched — see Section 8 below), and requests operating
mode `OFF`, before the existing owned-process-confirmation stop logic.

## 4. Server-authoritative live analysis

New `trading_lab_app/alsakkaf_scalping_runtime.py` (`ScalpingRuntime`),
wrapping a `ScalpingService` with no change to its state machine. Adds
`RealScalpingMT5Adapter.fetch_completed_bars(symbol, timeframe, count)`
(new local `TIMEFRAME_M15`/`TIMEFRAME_H1` constants; `copy_rates_from_pos`
added to the allowlist; `start_pos=1` always excludes the currently-
forming bar) and matching `FakeScalpingAdapter`/`DisabledScalpingAdapter`
implementations. `ScalpingRuntime.analyze_now(instrument)` resolves the
mapped broker symbol, the active profile's entry/confirmation timeframes
(new `alsakkaf_scalping_strategy.ENTRY_TIMEFRAME_FOR_PROFILE`), fetches a
fresh quote and completed bars, then calls the existing, unmodified
`ScalpingService.run_cycle(...)`. `/api/scalping-run-cycle` is removed
from `SCALPING_MUTATION_API_ROUTES`; `/api/scalping-analyze-now` replaces
it and rejects any request body containing a market-data-shaped key
(`entry_bars`, `confirmation_bars`, `current_price`, `spread`, `bars`,
`price`, `bid`, `ask`, `candles`) with `SCALPING_CLIENT_MARKET_DATA_REJECTED`.
`app.py`'s `_scalping_service_for_mode` now always supplies a real
`scratch_directory` (`alsakkaf_scalping_data.default_scratch_directory()`),
fixing root cause 5.

## 5. Live status document and the corrected MT5 indicator

`ScalpingRuntime.live_status_document(instrument=None)` returns
`TRL_SCALPING_LIVE_STATUS.v1`: application/operating-mode/product state,
adapter tier, MT5 package/terminal/account truth, redacted login suffix,
currency/leverage/balance/equity/daily P&L/session drawdown, mapping/
profile/side/event-risk state, quote/symbol metadata, completed-bar
readiness, monitoring status, last-analysis summary, owned cycle/order/
position counts, emergency-stop state, journal health, `last_update_utc`.
Unavailable fields carry an explicit reason from the fixed set
(`TERMINAL_NOT_CONNECTED`, `ACCOUNT_NOT_DEMO`, `SYMBOL_NOT_MAPPED`,
`QUOTE_UNAVAILABLE`, `HISTORY_INSUFFICIENT`, `ANALYSIS_NOT_RUN`,
`OPERATING_MODE_NOT_RESEARCH`) — never a bare dash.

`ScalpingService.mt5_connected()` (new) is `True` only when
`terminal_status().connected` **and** `account_status()` proves
`trade_mode == ACCOUNT_TRADE_MODE_DEMO` in the same read — never derived
from `journal_startup_diagnostic_code`, which is now surfaced separately
as `journal_health`. Proven by `Mt5ConnectionVsJournalHealthTests`
(healthy journal + disconnected terminal is not `mt5_connected`; connected
terminal + a deliberately failing journal still reports `mt5_connected`
`True` with `journal_health` reported separately; the disabled adapter
never reports connected; an unknown/non-demo account type is never
"Demo Verified").

## 6. Configuration persistence

New `TRL_SCALPING_CONFIG.v1` schema, `ScalpingConfigStore`/
`InMemoryScalpingConfigStore` (`alsakkaf_scalping_data.py`, same atomic
temp-file + `os.replace` technique as `SymbolMapStore`). `ScalpingService`
accepts an optional `config_store`, loads persisted profile/side/risk/
spread/monitoring-interval at construction, and `configure_profile`/new
`configure_side`/`set_monitoring_interval_seconds` persist immediately,
each guarded by `_require_non_demo_auto_for_config()`
(`SCALPING_CONFIG_REQUIRES_NON_AUTO_STATE` while `DEMO_AUTO`). Proven to
survive a fresh `ScalpingService` construction against the same store
files (`ConfigurationPersistenceTests.test_profile_side_and_monitoring_interval_survive_restart`).

## 7. Dashboard controls and the Demo Auto lock

`static/index.html`/`static/app.js` rewritten (additive to the existing
badges — `DEMO ACCOUNT ONLY` retained) with: connection recheck,
instrument selector, discover/save-mapping, profile/side/risk/spread/
event-risk-block controls, save-configuration, Run Analysis Now, start/
stop read-only monitoring, pause/resume, emergency stop/reset. `Start demo
auto` is replaced by a permanently `disabled` control labelled exactly
`DEMO AUTO — LOCKED PENDING BROKER EXECUTION PROOF`; no function in
`app.js` calls `/api/scalping-start-demo-auto` (`DemoAutoLockedInDashboardTests`).
Live status/latest-analysis/monitoring-status refresh every 5 seconds;
heavy analysis runs only on an explicit click or while monitoring is
enabled. All new rendering uses `textContent`/safe DOM creation only —
proven for `renderScalping`, `renderScalpingLive`, and
`wireScalpingControls` (`NoInnerHtmlTests`).

## 8. Read-only monitoring

`ScalpingRuntime` runs a single bounded daemon thread per process (started
only by an explicit `start_monitoring` call), interval `5`-`300` seconds
(default from persisted configuration), a non-blocking `_overlap_lock`
guarding against overlapping ticks, and a distinct `_cache_lock` guarding
the `_last_analysis` cache (deliberately two separate locks — see the
genuine defect below). Each tick re-checks: not `EMERGENCY_STOP`; product
state in `(ANALYZE_ONLY, DEMO_AUTO)`; terminal connected; account proven
DEMO; operating mode still real-adapter-granting — any failure stops
monitoring and records the reason. Never calls
`request_state_change("DEMO_AUTO")`. `stop_monitoring`/`shutdown` join the
thread with a bounded timeout; `app.py`'s shutdown cascade now calls
`scalping_runtime_instance.shutdown()` before the final
`scalping_service_instance.shutdown()` journal courtesy call.

**Genuine defect found and fixed during this pass (test hardening):** the
monitor loop's overlap guard and `analyze_now`'s own result-cache write
originally shared one `threading.Lock`. Since the loop acquired that lock
*before* calling `analyze_now`, and `analyze_now` itself tried to acquire
the same non-reentrant lock again to cache its result, the monitor thread
self-deadlocked on its very first tick — `stop_monitoring` then blocked for
its full 5-second join timeout on every call. Reproduced directly (a
diagnostic script dumped the stuck thread's stack, showing it blocked
inside `analyze_now`'s own `with self._analysis_lock:`) and fixed by
splitting into two distinct locks, `_overlap_lock` (monitor-loop-only) and
`_cache_lock` (result-cache-only, used by any caller/thread). Confirmed:
the full monitoring-lifecycle test suite dropped from 23.4s (with the
deadlock, still passing only because the join timeouts happened to be
long enough) to 1.6s after the fix.

**Second genuine defect found and fixed (real-terminal rehearsal):**
`RealScalpingMT5Adapter.symbol_status`'s tick timestamp came from
`market_data.normalize_tick`, which formats to millisecond precision (3
fractional digits); this repository's own `timeline_data.validate_utc_timestamp`
(used by every preflight/analyze quote-age check) requires exactly 6.
Never triggered by the fake adapter (whose timestamps already come from
`format_utc`), it surfaced immediately on the first real-terminal
`analyze_now` call during Section 15 below and was fixed by reformatting
the real adapter's tick timestamp through `format_utc` before returning it.

**Third genuine defect found and fixed (during this pass's own writing):**
`ScalpingRuntime.live_status_document`'s "is this instrument mapped"
guard originally checked `if not mappings or canonical_instrument is
None:` — true only when *no* instrument was mapped at all, so a request
for an *unmapped* instrument while a *different* instrument was already
mapped fell through to `mappings[canonical_instrument]` and raised
`KeyError`. Fixed to `if canonical_instrument is None or
canonical_instrument not in mappings:`. Caught by
`LiveStatusDocumentTests.test_unmapped_instrument_reports_explicit_reason`.

## 9. HTTP routes and CLI

New read-only `GET`: `/api/scalping-live-status[?instrument=]`,
`/api/scalping-configuration`, `/api/scalping-latest-analysis?instrument=`,
`/api/scalping-monitoring-status`. New mutation `POST` (same action-token
gate): `/api/scalping-recheck`, `/api/scalping-save-configuration`,
`/api/scalping-analyze-now`, `/api/scalping-monitoring-start`,
`/api/scalping-monitoring-stop`. `/api/scalping-run-cycle` removed.
New CLI commands: `scalping-live-status`, `scalping-recheck`,
`scalping-save-configuration`, `scalping-show-configuration`,
`scalping-analyze-now`, `scalping-monitoring-start/-stop/-status`,
`scalping-latest-analysis`, `scalping-stop` (documented process-scoped
limitation for CLI-invoked monitoring — see the module docstring of
`_build_runtime` in `alsakkaf_scalping_cli.py`).

## 10. Safety hardening beyond the contract's minimum ask

`scalping-stop`/the CLI's `_cmd_stop` deliberately refuse while
`EMERGENCY_STOP` is latched, even though R2-012's `_TRANSITIONS` table
technically allows `EMERGENCY_STOP -> OFF` directly. Only
`reset_emergency_stop()` may take that path, since it alone enforces the
zero-owned-pending-orders/reconciliation gate (contract Section 14.6 of
R2-012). Proven by
`ConfigurationPersistenceTests.test_scalping_stop_cli_refuses_during_emergency_stop`.

## 11. File scope

**New (5):** `trading_lab_app/alsakkaf_scalping_runtime.py`,
`TRL_R2_013_ALSAKKAF_SCALPING_OPERATIONAL_DASHBOARD_HOTFIX_CONTRACT.md`,
this evidence document, `test_alsakkaf_scalping_live_analysis.py`,
`test_alsakkaf_scalping_operational_dashboard.py`.

**Modified (16):** `Start_ALSAKKAF_SCALPING_DEMO.ps1`,
`Stop_ALSAKKAF_SCALPING_DEMO.ps1`, `trading_lab_app/app.py`,
`trading_lab_app/server.py`, `trading_lab_app/service.py`,
`trading_lab_app/alsakkaf_scalping_data.py`,
`trading_lab_app/alsakkaf_scalping_mt5.py`,
`trading_lab_app/alsakkaf_scalping_service.py`,
`trading_lab_app/alsakkaf_scalping_strategy.py`,
`trading_lab_app/alsakkaf_scalping_cli.py`,
`trading_lab_app/static/index.html`, `trading_lab_app/static/app.js`,
`TRL_APP_QUICK_START.md`, `TRL_CONTINUATION_STATE.md`,
`TRL_CONTINUATION_STATE.json`, `TRL_FULL_VISION_MASTER_PROGRAM.md`.

**Not modified:** `TRL_BLOCKERS.md` (no new external/Founder-input
blocker was created by this checkpoint — the one open blocker, a real
broker-verified `order_check`/`order_send` round trip, is unchanged and
already tracked there), `TRL_R2_010`/`TRL_R2_011`/`TRL_R2_012` contracts,
source, and tests, Phase 5/6 contracts/source/tests, `main`.

**Deleted:** none.

## 12. Test counts

Per-module net-new counts: `test_alsakkaf_scalping_live_analysis.py` 33,
`test_alsakkaf_scalping_operational_dashboard.py` 22. **Net-new total: 55.**

Existing R2-012 test modules were not weakened; no existing assertion was
removed or loosened. One pre-existing R2-012 HTTP test
(`test_scalping_section_present_in_index_html`) needed the restored
`DEMO ACCOUNT ONLY` badge text after the dashboard rewrite (the badge was
briefly dropped mid-rewrite in this session and restored before this
document was written) — the assertion itself was never changed.

Targeted 13-module scalping run (11 R2-012 modules + both new R2-013
modules): **228 tests, 0 failures, 0 errors.**

Complete-suite arithmetic: `1422` (prior baseline, R2-012-closed) `+ 55`
(net-new) `= 1477`.

| Run | Command | Tests | Result |
|---|---|---|---|
| Full-suite Run A | `python -B -W error -m unittest discover -s . -p "test_*.py"` | 1477 | 0 failures, 0 errors |
| Full-suite Run B | same | 1477 | 0 failures, 0 errors |

Two genuine defects (Section 8, monitor-lock deadlock and the real-tick
timestamp format mismatch) were found and fixed **after** Run A/B, during
the real-terminal rehearsal and this document's own writing — per this
program's established convention (R2-012 evidence Section 21), the
accepted consecutive pair must occur **after** the final source/test
change. Full-suite Run A/B above were therefore re-run as Run C/D after
every fix in this document was applied:

| Run | Command | Tests | Result |
|---|---|---|---|
| Full-suite Run C (post-fix) | same | 1477 | 0 failures, 0 errors |
| Full-suite Run D (post-fix, consecutive) | same | 1477 | 0 failures, 0 errors |

**The accepted consecutive pair is Run C and Run D**, both occurring after
every source/test change in this checkpoint, with no intervening edit
between them.

No intermittent failure was observed in any of these runs (unlike
R2-012's disclosed `test_mt5_execution_concurrency.py` flake, which did
not recur here).

## 13. Synthetic operational rehearsal

Executed end-to-end against the fake MT5 adapter and isolated temp-file
stores (standalone script, not part of the automated suite): started
`OFF`/`RESEARCH`; discovered and mapped `XAUUSD -> XAUUSDm`; configured
profile/side/monitoring-interval; restarted with a fresh `ScalpingService`
against the same store files and confirmed persistence
(`ALSAKKAF_PRECISION_SCALPING`/`BOTH`/`20`); transitioned to
`ANALYZE_ONLY`; ran Analysis Now against a flat fixture (`REJECT`, no
reasons) and against the R2-012 chop-then-breakout fixture (this module's
own classification `TRADE_CANDIDATE` at score 80/100, R2-010's
independent bridge returning `WAIT` — proving the bridge's own stricter
gate is still consulted, never bypassed); displayed every indicator
(ATR/RSI/ADX/EMA9/21/50); confirmed zero `order_check`/`order_send` calls;
started read-only monitoring; simulated a stale quote (`QUOTE_UNAVAILABLE`,
never fabricated); simulated a terminal disconnect (monitoring safety
check correctly reports `TERMINAL_NOT_CONNECTED`); stopped monitoring;
reconfirmed zero `order_check`/`order_send`; returned product state and
operating mode to `OFF`; removed the isolated temp store. All steps
passed.

## 14. Real 4T MT5 demo read-only rehearsal

Performed after the synthetic rehearsal, using a standalone script
constructing the real production objects
(`RealScalpingMT5Adapter`/`ScalpingService`/`ScalpingRuntime`) against
isolated temp-file symbol-map/config stores (never the Founder's real
persisted Trading Lab state), with an in-memory journal and in-memory
`ModeService`. Permitted calls only: `initialize`, `terminal_info`,
`account_info`, `symbols_get`, `symbol_info`, `symbol_info_tick`,
`copy_rates_from_pos`, `orders_get`, `positions_get`, `shutdown`
(`symbol_select` only inside the already-disclosed R2-012 bounded-
subscription path, unchanged). No `login`. No `order_check`. No
`order_send`. No modification/cancellation of any order or position.

**Real result:** terminal connected (`trade_allowed` true, Algo Trading
enabled); account proven DEMO (redacted login `...1837`, balance/equity
`125248.83 USD`, leverage `100`) — matching the account already documented
in R2-012's own real rehearsal; `XAUUSD` uniquely discovered and mapped;
product state transitioned `OFF -> ANALYZE_ONLY`; real bid/ask
`4061.06`/`4061.36`; `Analyze Now` fetched real completed M1/M5 bars and
computed real indicators (`ATR=1.7745`, `RSI=71.55`, `ADX=40.80`,
`total_score=68`, `classification=WAIT`, `direction=BUY`) — a genuine
`WAIT`, not manufactured, not overridden, no threshold adjusted. `order_check`
count: `0`. `order_send` count: `0`. Product state returned to `OFF`;
operating mode returned to `OFF`. Real owned orders/positions confirmed
empty both before and after (broker state unchanged). Isolated temp store
removed.

This real rehearsal directly exercised the corrected code paths this
checkpoint introduces (`mt5_connected()`, `fetch_completed_bars`,
`analyze_now`, the live-status document) against the Founder's actual
authenticated terminal — not merely the fake-adapter synthetic path —
and is what surfaced the tick-timestamp-format defect (Section 8) fixed
in this same pass.

## 15. No-network-client / no-credential / no-live-account proof

No new `import requests`/`urllib.request`/`websocket` anywhere in
`alsakkaf_scalping_runtime.py` or any modified module. No password,
investor password, access token, or broker-server string is ever stored,
journaled, or returned by any new CLI/HTTP response — `account_status()`
still exposes only `login_last4`/`trade_mode_name`, unchanged from R2-012,
plus the newly added `currency`/`leverage`/`balance` (none of which are
credential-shaped). `RealScalpingMT5Adapter` still never imports
`MetaTrader5` at module or construction time (unchanged R2-012 property,
re-verified: this checkpoint's real rehearsal only imported it inside a
method call, exactly as designed).

## 16. Known limitations

- CLI-invoked `scalping-monitoring-start` is process-scoped: the
  background thread ends when that one CLI process exits, since each
  invocation is a fresh Python process (documented in-module). The
  intended continuous-monitoring path is the long-running dashboard
  server's own `/api/scalping-monitoring-start`.
- `daily_pnl`/`session_drawdown_pct` in the live-status document are only
  established once the first preflight-equivalent read runs in this
  process (`ANALYSIS_NOT_RUN`-shaped `None` beforehand) — matching this
  program's existing "resolved once per process" convention.
- The analysis cache (`ScalpingRuntime._last_analysis`) is in-process
  memory only, not journal-derived, and does not survive a server
  restart — an explicit, documented accelerated-V0 boundary for this
  hotfix, consistent with R2-012's own two documented accelerated-V0
  decisions.

## 17. Remaining blockers

Unchanged from R2-012 (`TRL_BLOCKERS.md`): an actual broker-verified
`order_check`/`order_send` round trip on the real 4T demo terminal remains
open, achievable only during a further, separately authorized bounded
rehearsal at a moment a genuine `TRADE_CANDIDATE` occurs. This checkpoint
does not attempt to close that item — it was not authorized to, and does
not call `order_check`/`order_send` anywhere in its own new code or
rehearsals.

## 18. Final state

Final product state: `OFF` (real rehearsal never left `ANALYZE_ONLY`).
Final operating mode: `OFF`. Port `8765`: confirmed clear. Process: no
stray `python.exe`. Isolated rehearsal temp directories: removed (both
scripts confirmed `not Path(tmp).exists()`). Broker positions/orders:
unchanged (`0`/`0` before and after the real rehearsal). Git: nothing
staged, nothing committed, nothing pushed; `main` unchanged.

## 19. Addendum — Founder shutdown correction (same session, additive)

The Founder visually accepted the operational dashboard: real MT5
connection, DEMO verification, live account balance/equity, `XAUUSD`
mapping, real quotes and indicators, `Run Analysis Now`, repeated
15-second read-only monitoring, `WAIT`/`NONE` refusal behavior, `Demo
Auto` visibly locked, and no broker order or position — all confirmed
working exactly as this document already describes. The Founder's first
corrected-stop attempt then exposed a genuine shutdown defect.

### 19.1 Exact defect

`Stop_ALSAKKAF_SCALPING_DEMO.ps1` called `scalping-pause` unconditionally
as its first product-state step, falling back to `scalping-emergency-stop`
on any rejection. The R2-012 `_TRANSITIONS` table
(`alsakkaf_scalping_service.py`) never allows `ANALYZE_ONLY -> PAUSED` at
all — `PAUSED` is reachable only from `DEMO_AUTO`/`PAUSED` itself.
`scalping-pause` therefore **deterministically** failed from exactly the
state this checkpoint's own corrected launcher establishes
(`ANALYZE_ONLY`), and the fallback latched an unnecessary `EMERGENCY_STOP`
on every ordinary shutdown. Confirmed directly against the Founder's real,
already-running session: `scalping-status` showed
`"product_state": "EMERGENCY_STOP"`, `"emergency_stop_active": true`;
`scalping-list-owned-orders`/`-positions` both empty; the journal tail
showed the exact sequence `SCALPING_STATE_CHANGED
ANALYZE_ONLY -> EMERGENCY_STOP` immediately followed by
`EMERGENCY_STOP_ACTIVATED` with empty `cancelled_orders`/`closed_positions`
— proving no broker action occurred, but the latch was real. Operating
mode had independently and correctly reached `OFF` (its own transition
does not depend on `ScalpingService`'s state).

### 19.2 Corrected stop state machine

New `ScalpingService.graceful_stop()` (`alsakkaf_scalping_service.py`):
deterministic, idempotent, never uses `EMERGENCY_STOP` as a generic
fallback, never attempts a bare `EMERGENCY_STOP -> OFF` transition.

- `OFF` -> no-op, `{"outcome": "ALREADY_OFF", ...}`, no journal event.
- `ANALYZE_ONLY`/`PAUSED` -> direct governed `request_state_change("OFF")`.
- `DEMO_AUTO` -> `request_state_change("EMERGENCY_STOP")` (flattens owned
  exposure per the unmodified R2-012 emergency-stop execution), then
  `reconcile()` and a new explicit zero-owned-orders-**and**-positions
  check (`_require_zero_owned_state_or_raise`, stricter than
  `reset_emergency_stop()`'s own orders-only check — a defensive addition,
  not a change to R2-012's own method), then `reset_emergency_stop()`.
- `EMERGENCY_STOP` -> the same zero-owned-state check, then
  `reset_emergency_stop()`.

The CLI's `scalping-stop` command (`_cmd_stop`) now calls
`graceful_stop()` directly; the HTTP/dashboard surface is unaffected (this
command is launcher/CLI-only).

### 19.3 Corrected startup recovery

New `ScalpingService.recover_stale_emergency_stop()`: acts **only** when
`current_state == "EMERGENCY_STOP"`; no-ops
(`{"outcome": "NO_ACTION_NEEDED", ...}`) for every other state, including
`DEMO_AUTO` (startup recovery must never force-stop what could be
genuinely active automation from a still-running prior process — that is
the shutdown script's job, not startup's, contract Section 4). Resets via
`reset_emergency_stop()` only when the same zero-owned-orders-and-
positions check passes; fails closed (nothing reset) otherwise. New CLI
command `scalping-startup-recover`.
`Start_ALSAKKAF_SCALPING_DEMO.ps1` now calls it **before** requesting
`ANALYZE_ONLY`; if recovery fails, `ANALYZE_ONLY` is not requested and an
explicit on-screen blocker is printed (the dashboard still starts so the
Founder can see it).
`Stop_ALSAKKAF_SCALPING_DEMO.ps1` now calls `scalping-stop`
(`graceful_stop()`) instead of pause-then-emergency-fallback, then
verifies `product_state == "OFF"` **and** `operating_mode == "OFF"` via
fresh `scalping-status`/`mode_cli show-mode` calls before printing
`"ALSAKKAF SCALPING dashboard stopped."` — that line is never printed on a
partial or unverified shutdown, and the script exits non-zero in that
case.

### 19.4 Tests

20 net-new tests in `test_alsakkaf_scalping_operational_dashboard.py`
(`GracefulStopStateMachineTests` 9, `RecoverStaleEmergencyStopTests` 4,
`LauncherShutdownCorrectionScriptTests` 5,
`PauseTransitionDocumentationTests` 1, plus the two
`ConfigurationPersistenceTests` cases rewritten from "refuses" to
"resets when zero-owned/fails-closed when non-zero" to match the
corrected, now-genuinely-useful behavior — the assertions were
strengthened, not weakened: the old test only proved a hard refusal; the
new pair proves both the successful reset path and the fail-closed path).
Covers: stopping from every one of the five product states; `DEMO_AUTO`
shutdown sequencing (fake adapter only, zero `order_check`/`order_send`
calls); pause-rejection-does-not-trigger-emergency-stop (documented via
the R2-012 transition-table fact itself); reset-before-OFF ordering;
zero-owned-state requirement before both reset paths; idempotent repeated
stop; stale-latch recovery at startup; startup recovery never acting on
`DEMO_AUTO`; both launcher scripts' corrected text (no `scalping-pause`/
`scalping-emergency-stop` invocation in the Stop script; `scalping-stop`
present; final-state verification present; `scalping-startup-recover`
called before `scalping-resume` in the Start script).

**Updated net-new total: 55 (prior) + 20 (this addendum) = 75. Updated
complete-suite arithmetic: `1422 + 75 = 1497`.**

Targeted 13-module scalping run (re-run after this addendum's changes):
**248 tests, 0 failures, 0 errors.**

| Run | Command | Tests | Result |
|---|---|---|---|
| Full-suite Run A (post-addendum) | `python -B -W error -m unittest discover -s . -p "test_*.py"` | 1497 | 0 failures, 0 errors |
| Full-suite Run B (post-addendum, consecutive) | same | 1497 | 0 failures, 0 errors |

No intermittent failure was observed in either run. No intervening
source/test edit occurred between Run A and Run B.

### 19.5 Synthetic shutdown rehearsal

Standalone script against the fake adapter and isolated in-memory state,
proving all 8 mega-prompt-mandated steps: (1) `OFF -> stop -> OFF/OFF`;
(2) `ANALYZE_ONLY` with monitoring running `-> monitoring stopped ->
OFF/OFF`; (3) `PAUSED -> OFF/OFF`; (4) `EMERGENCY_STOP` with zero owned
broker state `-> reset -> OFF -> operating mode OFF`; (5) `DEMO_AUTO`
with a fake owned position: `graceful_stop()` correctly fails closed
(`SCALPING_GRACEFUL_STOP_OWNED_STATE_REMAINS`, state remains
`EMERGENCY_STOP`) until the position is fake-closed/reconciled, then
succeeds; (6) repeated stop remains successful
(`ALREADY_OFF` both times); (7) zero `order_check`/`order_send` calls
against the fake adapter across the entire rehearsal; (8) no monitor
thread remains alive. All steps passed.

### 19.6 Real local read-only shutdown rehearsal

Performed against the Founder's actual already-authenticated 4T MT5 DEMO
terminal, using the real, corrected `Start_ALSAKKAF_SCALPING_DEMO.ps1` /
`Stop_ALSAKKAF_SCALPING_DEMO.ps1` scripts and the real running dashboard
server process (not an isolated script):

1. Launched `Start_ALSAKKAF_SCALPING_DEMO.ps1 -NoBrowser`; server bound to
   `127.0.0.1:8765` within 1 second.
2. Confirmed via the real running server's own HTTP endpoints:
   `operating_mode = RESEARCH`, `product_state = ANALYZE_ONLY`,
   `mt5_connected = true`, real live bid/ask (`4052.02`/`4052.32`).
3. Started read-only monitoring via `/api/scalping-monitoring-start`
   (interval `5` seconds) against the real running server.
4. Observed **9 real completed monitoring iterations** (`tick_count: 9`
   at stop, far exceeding the required minimum of 2), each producing a
   genuine `WAIT` classification from real market data — never
   manufactured, never overridden.
5. Stopped monitoring via `/api/scalping-monitoring-stop`.
6. Invoked the corrected `Stop_ALSAKKAF_SCALPING_DEMO.ps1` for real.
7. **Confirmed no unnecessary emergency-stop activation** — the script's
   output shows only `"Product-state stop outcome: STOPPED
   (product_state=OFF)"`, with no pause-rejection or emergency-stop
   fallback message anywhere (contrast with the Founder's original
   observed output in Section 19.1, which showed both).
8. Product state: `OFF` (verified in-script and independently after).
9. Operating mode: `OFF` (verified in-script and independently after).
10. Port `8765`: confirmed clear (only harmless `TIME_WAIT` remnants of
    already-closed client connections; no `LISTENING` socket).
11. No `python.exe` process remained.
12. No monitor thread (server process itself exited).
13. Broker positions/orders: `0`/`0`, confirmed both before this
    rehearsal (Section 14) and after this correction — unchanged
    throughout.
14. `order_check`/`order_send` counts: `0` throughout (never called
    anywhere in `ANALYZE_ONLY` or read-only monitoring).

No credential was requested or exposed. No broker mutation occurred.

### 19.7 Real environment correction

The Founder's actual persisted local state (found latched at
`EMERGENCY_STOP` per Section 19.1, confirmed zero owned orders/positions)
was corrected in place using the new governed `scalping-stop` CLI command
against the real persisted stores — resolving to
`{"outcome": "STOPPED", "product_state": "OFF"}` — before this addendum's
real rehearsal (Section 19.6) began, so the rehearsal started from a
clean, genuinely verified `OFF`/`OFF` baseline rather than merely
asserting it.

### 19.8 Final state (post-addendum, before this checkpoint's local commit)

Final product state: `OFF`. Final operating mode: `OFF`. Port `8765`:
confirmed clear. Process: no stray `python.exe`. Broker positions/orders:
`0`/`0`, unchanged throughout this addendum's real rehearsal.
`order_check` count: `0`. `order_send` count: `0`. Git at this point:
nothing staged, nothing committed, nothing pushed; `main` unchanged.

## 20. Founder-authorized local commit

Following Founder visual acceptance of both the operational dashboard
(Section 19, opening paragraph) and the corrected shutdown (Section 19.6),
the Founder separately authorized exactly one local implementation commit
of this checkpoint's full approved 22-file scope (5 added, 17 modified, 0
deleted — Section 11) with the message `Implement TRL-R2-013 ALSAKKAF
SCALPING Operational Dashboard Hotfix`. This checkpoint (including this
document) is therefore **locally committed** as of that commit; **remote
push remains a separate, later, Founder-authorized step**, not performed
in this pass. `main` is unaffected by a local commit on this feature
branch. See `git status`/`git rev-parse HEAD`/`git log -1` directly for
the exact current committed state, rather than a SHA restated here (this
document is itself part of the commit it describes).
