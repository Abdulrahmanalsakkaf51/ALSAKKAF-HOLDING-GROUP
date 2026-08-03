# TRL-R2-012 ALSAKKAF SCALPING Demo Automation V0 Evidence

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-012 (accelerated contract-and-implementation checkpoint, single sprint) |
| Status | **Formally closed: committed and pushed, remotely verified** |
| Related contract | `TRL_R2_012_ALSAKKAF_SCALPING_DEMO_AUTOMATION_V0_CONTRACT.md` |

> Implementation commit `791ea98118539b6bf30f37e5eaf81ffd85d3589c`
> ("Implement TRL-R2-012 ALSAKKAF SCALPING Demo Automation V0") and
> consecutive-suite verification commit
> `0edd4adf2019e8162011ada58f3e5962555271eb` ("Record TRL-R2-012
> consecutive suite verification") are both **committed and pushed**,
> range `02c48e0..0edd4ad`, independently re-verified via a fresh `git
> fetch`: local HEAD, the live remote branch ref, and the
> upstream-tracking ref all equal `0edd4adf2019e8162011ada58f3e5962555271eb`;
> ahead/behind `0 0`; working tree and index clean; no untracked file;
> `main` unchanged. This document records what was built, tested, and
> rehearsed against the governing contract. Per this program's
> Git-authoritative convention, the exact current state is always read
> from `git status`/`git rev-parse HEAD` directly, not restated here as a
> value that would otherwise go stale the moment either changes.

## 1. Governing contract

`TRL_R2_012_ALSAKKAF_SCALPING_DEMO_AUTOMATION_V0_CONTRACT.md`, authored and
internally reviewed in this checkpoint, including one implementation-
discovered correction applied in place (Section 16: granting
`market_intelligence_research` to `MT5_DEMO_AUTOMATED` so the R2-010
evidence bridge does not fail closed with `MARKET_INTELLIGENCE_CAPABILITY_DENIED`
during `DEMO_AUTO`).

## 2. Exact file scope

**New (24 files):**

Contract and evidence: `TRL_R2_012_ALSAKKAF_SCALPING_DEMO_AUTOMATION_V0_CONTRACT.md`,
`TRL_R2_012_ALSAKKAF_SCALPING_DEMO_AUTOMATION_V0_EVIDENCE.md`.

Source (8): `trading_lab_app/alsakkaf_scalping_data.py`,
`alsakkaf_scalping_indicators.py`, `alsakkaf_scalping_strategy.py`,
`alsakkaf_scalping_risk.py`, `alsakkaf_scalping_journal.py`,
`alsakkaf_scalping_mt5.py`, `alsakkaf_scalping_service.py`,
`alsakkaf_scalping_cli.py`.

Tests (11) + support + fixture: `test_alsakkaf_scalping_data.py`,
`_indicators.py`, `_strategy.py`, `_risk.py`, `_journal.py`, `_mt5.py`,
`_service.py`, `_cli.py`, `_http.py`, `_concurrency.py`, `_safety.py`,
`alsakkaf_scalping_test_support.py`,
`fixtures/alsakkaf_scalping_synthetic_market.json`.

Launchers (2): `Start_ALSAKKAF_SCALPING_DEMO.ps1`, `Stop_ALSAKKAF_SCALPING_DEMO.ps1`.

**Modified (7, all additive):** `trading_lab_app/mode_service.py` (Section
16 capability/transition amendment), `trading_lab_app/app.py` (scalping
adapter/service construction, wired into `_subsystem_builder_for_mode`
and the `run_server` call site), `trading_lab_app/server.py` (read-only
scalping routes + the program's first POST mutation routes, gated by
local-host header + CSRF-style action token), `trading_lab_app/service.py`
(thin scalping HTTP document wrappers), `trading_lab_app/static/index.html`
/ `static/app.js` (additive ALSAKKAF SCALPING dashboard section),
`test_operating_mode.py` (three assertions updated to reflect the
contract-authorized `MT5_DEMO_AUTOMATED` availability change — see
Section 6 below; no assertion was weakened, only updated to match the
newly authorized behavior).

**Deleted:** none. **`main` unchanged.** R2-010/R2-011 contracts, source,
and tests unmodified. Phase 5/6 source and tests unmodified.

## 3. Product-state implementation

Five states (`OFF, ANALYZE_ONLY, DEMO_AUTO, PAUSED, EMERGENCY_STOP`),
event-sourced from `SCALPING_STATE_CHANGED` journal events, exactly per
contract Section 3. Verified by `test_alsakkaf_scalping_service.py`'s
`ProductStateMachineTests` (starts `OFF`; invalid transitions rejected
and leave state unchanged; `DEMO_AUTO` requires both the ModeService
capability and a passing preflight; `EMERGENCY_STOP` reachable from every
state and returns only to `OFF`).

## 4. Three strategy profiles

`ALSAKKAF_PRECISION_SCALPING`, `ALSAKKAF_BREAKOUT_LADDER`,
`ALSAKKAF_INTRADAY` implemented per contract Section 4. Precision
Scalping/Intraday produce one market-order plan; Breakout Ladder produces
up to six stop-order plans (bounded `MAX_LADDER_ORDERS = 6`,
`MAX_LADDER_ORDERS_PER_SIDE = 3`), spaced by the exact `ladder_distance_floor`
formula, with OCO cancellation and equal-risk division proven in the
synthetic rehearsal (Section 12) and `test_alsakkaf_scalping_safety.py`.

## 5. MT5 preflight and demo-account proof

`alsakkaf_scalping_mt5.run_preflight` implements all twenty checks from
contract Section 6 in order, returning the first blocking reason code.
`ACCOUNT_IS_DEMO`/`ACCOUNT_NOT_CONTEST_OR_REAL` independently re-verify
`trade_mode == ACCOUNT_TRADE_MODE_DEMO` on every call — never cached, never
inferred. 23 tests in `test_alsakkaf_scalping_mt5.py::PreflightTests`
cover every individual check failing in isolation (dependency missing,
disconnected terminal, non-demo account, Algo Trading disabled, symbol
unavailable, stale quote, market closed, excessive spread, daily-loss
breach, emergency-stop latch, manual event-risk block, account
disconnected) plus the full-pass case.

## 6. Real-account hard lock (independent of `ModeService`)

`test_alsakkaf_scalping_safety.py::RealAccountHardLockTests` proves: (a)
even with `ModeService` granting `alsakkaf_scalping_demo_automation`, a
`REAL`-classified account is independently rejected at the adapter
preflight layer with `SCALPING_ACCOUNT_NOT_PROVEN_DEMO`; (b)
`MT5_LIVE_MANUAL`/`MT5_LIVE_AUTOMATED` remain fully unavailable in
`ModeService`, unchanged by this checkpoint; (c) `alsakkaf_scalping_demo_automation`
is granted to exactly one mode (`MT5_DEMO_AUTOMATED`) across all seven
governed modes; (d) `RealScalpingMT5Adapter()` construction never imports
`MetaTrader5`.

`test_operating_mode.py` was updated (not weakened) to reflect that
`MT5_DEMO_AUTOMATED` is now contract-authorized to be available — this is
the identical, established pattern R2-009 used when it first made
`MT5_DEMO_MANUAL` available in Phase 5: `test_mt5_demo_automated_represented_but_unavailable`
became `test_mt5_demo_automated_available_since_r2_012` (asserting
availability, zero `unavailable_reasons`, and the exact new transition
edges `RESEARCH -> MT5_DEMO_AUTOMATED -> {OFF, RESEARCH}`);
`test_exact_transition_matrix` was extended with the new edge and the new
mode's own destinations. Every other Phase 3 assertion (seven modes, no
eighth mode, no HTTP mode-mutation route, `MT5_LIVE_MANUAL`/`MT5_LIVE_AUTOMATED`
still unavailable, restart-cannot-restore-automated-modes) is byte-for-byte
unchanged and still passes.

## 7. Broker-symbol mapping

`SymbolMapStore`/`InMemorySymbolMapStore` (contract Section 7), editable
only while the product state is `OFF` (`test_alsakkaf_scalping_service.py::test_save_symbol_map_requires_off_state`).
`discover_symbols` never returns a single chosen candidate
(`test_alsakkaf_scalping_mt5.py::test_symbol_ambiguity_never_silently_resolved`).

## 8. Indicator implementation

Nine deterministic `Decimal`-only indicators/statistics over closed bars
only (EMA 9/21/50, RSI 14, ATR 14, ADX 14, MACD 12/26/9, 5-bar-fractal
swing points, candle statistics, spread-to-ATR, multi-timeframe direction).
13 tests including an explicit no-look-ahead proof (`test_ema_never_uses_more_than_supplied_closed_bars`).

## 9. Scoring implementation

Six categories summing to exactly 100 (trend 25, momentum 20,
market_structure 20, volatility_suitability 15, spread_and_cost 10,
multi_timeframe_alignment 10); thresholds 75/60/0 map to
`TRADE_CANDIDATE`/`WAIT`/`REJECT`; direction `NONE` forces `WAIT`
regardless of score. This checkpoint's one accelerated-V0 engineering
decision (per-category sub-formulas) is documented in
`alsakkaf_scalping_strategy.py`'s module docstring.

## 10. R2-010 evidence bridge

`build_analysis_input`/`run_r2010_bridge` construct a complete, valid
`TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1` envelope and call R2-010's
**unmodified** `MarketIntelligenceService.analyze_market_snapshot`. Only
`final_status == "TRADE_CANDIDATE"` proceeds to a demo order plan
(`test_alsakkaf_scalping_service.py::test_wait_setup_creates_no_cycle`).
Confidence for every deterministic-indicator-derived evidence item is
`1.0000` (the *degree* of support is carried entirely by
`normalized_strength`) — a second accelerated-V0 decision, documented
in-module, needed to keep this module's own 75-point threshold and
R2-010's independent `supporting_score >= 0.65` gate mutually achievable
for a genuinely strong setup (verified in the synthetic rehearsal, both
gates pass together for the committed fixture). The scratch input file is
always removed after the call (`test_run_r2010_bridge_never_leaves_scratch_file_behind`).

## 11. Risk policy and hard caps

`alsakkaf_scalping_risk.py` implements every Section 11 default and hard
cap; `validate_risk_settings` fails closed (never clamps) on any hard-cap
violation. `calculate_lots` fails closed on missing/non-finite inputs,
below-minimum lots, and unbounded excess-risk after volume-max capping.
22 risk tests + dedicated no-martingale/no-escalation tests
(`test_no_lot_escalation_after_loss`: post-loss lot size is never larger,
because `calculate_lots`'s signature has no loss/streak parameter at all —
structurally impossible, not merely policy).

## 12. Breakout Ladder / OCO / no-martingale proof

Proven three ways: (1) unit tests (`test_alsakkaf_scalping_risk.py::LadderRiskConservationTests`,
`test_alsakkaf_scalping_safety.py::NoUncontrolledGridTests`); (2) the
synthetic rehearsal (Section 22 below) building a real 3-order ladder from
the committed fixture, proving exact risk conservation
(`25.0000 == 8.333... × 3`) and running the OCO cap function; (3)
structural proof — `MAX_LADDER_ORDERS`/`MAX_LADDER_ORDERS_PER_SIDE` are
fixed module constants enforced at plan-construction time, and
`divide_ladder_risk` rejects more than six orders outright.

## 13. Order ownership, `order_check`, `order_send`

Every order plan carries `magic_number = 384512` and
`comment = "ALSAKKAF_SCALPING"` (`alsakkaf_scalping_data.build_order_plan`,
identity-validated in `validate_order_plan`). The Section 14.1 sequence
(lock → reload → uncertain-freeze check → fresh preflight → plan → tag →
`order_check` → `order_send`-at-most-once → persist → reconcile → release)
is implemented in `ScalpingService.run_cycle`, verified end-to-end by
`test_demo_auto_trade_candidate_creates_active_cycle_with_order_check_and_send`
(exact call sequence `["order_check", "order_send"]`, never more).
`order_check` rejection blocks the cycle without ever calling `order_send`
(`test_order_check_rejected_blocks_cycle_without_order_send`).

## 14. Uncertain-result freeze and restart reconciliation

An `UNCERTAIN` `order_send` outcome freezes further mutation for that
symbol only (`test_uncertain_order_send_freezes_cycle`), requiring
`reconcile()` before any further cycle on that symbol. Restart
reconciliation is journal-derived: a fresh `ScalpingService` against the
same durable journal file immediately reflects the prior process's
committed state (`test_restart_reconciliation_uses_durable_journal`; also
demonstrated live in the synthetic rehearsal, Section 22 step 11).

## 15. Emergency stop and unrelated-order protection

`EMERGENCY_STOP` cancels every ALSAKKAF-owned pending order and closes
every ALSAKKAF-owned position (filtered by magic number), never touching
an order/position owned by a different magic number
(`test_emergency_stop_never_touches_unowned_order`,
`test_emergency_stop_reports_only_owned_tickets`, and reproduced live in
the synthetic rehearsal with a genuine unrelated ticket present).
`scalping-reset-emergency-stop` requires zero owned pending orders
remaining (`test_reset_requires_zero_owned_pending_orders`).

## 16. Journal and concurrency

`TRL_SCALPING_JOURNAL.v1`, architecturally identical to
`mt5_execution_journal.py` (hash-chained, bounded, atomic, cross-process
owner-token lock, no unlocked fallback), with its own 21-event closed
vocabulary and its own store path — separate from Phase 5/6, R2-010, and
R2-011 journals. Real separate-process lock contention proven by
`test_alsakkaf_scalping_concurrency.py` (two live OS processes racing to
append; final journal hash-chain valid, exactly 2 events, contiguous
sequence numbers).

**Genuine defect found and fixed during this pass:** `configure_profile`'s
original journal payload (`canonical_instrument`, `profile_id` only) could
make two distinct reconfigurations that changed only risk settings
journal-indistinguishable from each other if they landed in the same
system-clock tick (observed on this Windows machine, whose clock
resolution is coarser than one microsecond in practice) — a real
duplicate-event-ID collision, not a hypothetical one, reproduced during
this checkpoint's own test-suite hardening. Fixed by including the
effective `risk_settings`/`max_spread_points` in the payload, so two
different reconfigurations are never payload-identical merely because
they share a clock tick.

**Second genuine defect found and fixed:** the oversized-body-rejection
path in the new HTTP mutation handler (`_read_json_body`) closed the
connection without draining a merely-oversized-for-this-app (but still
small, e.g. 70 KB) request body, which caused an intermittent TCP abortive
reset race on Windows, reproduced 2 of 3 times when run immediately after
the concurrency test. Fixed by draining up to a bounded 4 MiB ceiling
before responding 413 (a truly enormous declared length is still never
drained, so a genuinely hostile request still gets a cheap abortive
reset) — reconfirmed clean across 8 consecutive repeated runs after the
fix, and clean across two full-suite runs (Section 21).

## 17. CLI commands

All 18 commands from contract Section 18.1 implemented in
`alsakkaf_scalping_cli.py`. `scalping-analyze`/`scalping-run-cycle` report
`SCALPING_ANALYZE_REQUIRES_BAR_INPUT`/`SCALPING_RUN_CYCLE_REQUIRES_BAR_INPUT`
in this V0 CLI (bar/quote sourcing is the HTTP/dashboard layer's job per
the module's documented accelerated-V0 boundary decision, Section 9); the
HTTP route `/api/scalping-run-cycle` is fully functional. 13 CLI tests,
isolated `LOCALAPPDATA`.

## 18. HTTP routes

Read-only: `/api/scalping-status` (also carries the CSRF-style action
token), `-cycles`, `-owned-orders`, `-owned-positions`, `-journal`,
`-preflight/<INSTRUMENT>`, `-symbol-candidates/<INSTRUMENT>`,
`-cycle/<cycle_id>`. **This is the first checkpoint in the program with
HTTP mutation routes** — `-start-demo-auto`, `-pause`, `-resume`,
`-emergency-stop`, `-emergency-reset`, `-save-symbol-map`,
`-configure-profile`, `-run-cycle`, all POST-only (GET returns
405/`Allow: POST`), local-host-header-gated exactly like every existing
read route, and additionally requiring the exact
`X-Scalping-Action-Token` value minted fresh per server process. 20 HTTP
tests, including token-missing/wrong-token 403, oversized-body 413,
unregistered-mutation-path 405, and the standard local-host/HEAD-matches-GET
checks every prior checkpoint already established.

## 19. Dashboard

New "ALSAKKAF SCALPING" section in `static/index.html` with the four
required badges (`DEMO ACCOUNT ONLY`, `AUTOMATION STATUS`,
`LIVE MONEY LOCKED`, `EMERGENCY STOP`) and every required control/display
field. `renderScalping`/`wireScalpingControls` in `static/app.js` use
`textContent`/safe DOM creation only —
`test_no_innerhtml_in_render_scalping`/`test_no_innerhtml_in_wire_scalping_controls`
grep both function bodies and confirm zero `innerHTML` occurrences,
matching the exact test pattern every prior checkpoint's dashboard panel
already uses.

## 20. Launcher scripts

`Start_ALSAKKAF_SCALPING_DEMO.ps1`: refuses a duplicate listener, checks
the `MetaTrader5` import (warns, does not block, if missing), never
enables `DEMO_AUTO`, leaves product/operating state `OFF`. `Stop_ALSAKKAF_SCALPING_DEMO.ps1`:
requests a governed pause (falling back to emergency stop) before
confirming and stopping only the owned local process, mirroring
`STOP_TRADING_LAB.ps1`'s exact ownership-confirmation safety check.

## 21. Test counts and complete-suite arithmetic

Per-module net-new counts: data 16, indicators 13, strategy 17, risk 22,
journal 9, mt5 23, service 22, cli 13, http 20, concurrency 1, safety 17.
**Net-new total: 173.**

Targeted combined run (37 modules — all 11 new scalping modules plus
`test_operating_mode`, `test_trading_lab_app`, all 7 Phase 5 modules, all
5 Phase 6 modules, all 6 R2-010 modules, all 7 R2-011 modules): **928
tests, 0 failures, 0 errors.**

Complete-suite arithmetic: `1249` (prior baseline) `+ 173` (net-new) `=
1422`.

**Exact chronology (corrected during post-commit consecutive-suite
verification):** `test_operating_mode.py` was strengthened (Section 6/16
Founder-review addendum, adding explicit per-mode capability-boundary
assertions) *after* the original Run A/Run B pair below, which therefore
do not qualify as the accepted consecutive pair for the final committed
state. All three layers were rerun afterward:

| Run | Command | Tests | Result |
|---|---|---|---|
| 11-module R2-012 suite (rerun) | `python -B -W error -m unittest test_alsakkaf_scalping_{data,indicators,strategy,risk,journal,mt5,service,cli,http,concurrency,safety}` | 173 | 0 failures, 0 errors |
| 37-module targeted suite (rerun) | same modules as Section above | 928 | 0 failures, 0 errors |
| Full-suite Run A (rerun) | `python -B -W error -m unittest discover -s . -p "test_*.py"` | 1422 | 0 failures, 0 errors |
| Full-suite Run B, first attempt | same | 1422 | **1 failure**: `test_mt5_execution_concurrency.ConcurrentSendTests.test_journal_has_exactly_one_send_reservation_after_race` |
| `test_mt5_execution_concurrency.py` in isolation | `python -B -W error -m unittest test_mt5_execution_concurrency` | 7 | 0 failures, 0 errors (×3 consecutive runs) |
| Full-suite Run B, second attempt | same as Run A | 1422 | 0 failures, 0 errors |
| Full-suite Run C (post-commit verification) | same as Run A | 1422 | 0 failures, 0 errors |

The one intermittent failure is in `test_mt5_execution_concurrency.py`, a
real separate-process race test, confirmed **untouched by this
checkpoint** (`git diff --stat` against that path reports zero changes)
and confirmed passing 3/3 in isolation — the same class of pre-existing,
system-load-timing-sensitive flake this repository's own R2-010/R2-011
evidence documents already disclosed in the identical test area. It was
not worked around by modifying the test, and the first Run B attempt is
**not** counted as an accepted clean run.

**The accepted consecutive pair is: Run B (second attempt) and Run C,
both 1422/1422 with zero failures/errors, both occurring after the final
source/test change in this checkpoint (`test_operating_mode.py`'s Founder-
review strengthening) and with no intervening source/test edit between
them.** All full-suite runs above used the working directory
`09_AI_Systems/02_Tools/Trading_Lab`, matching the R2-011 precedent. The
two genuine defects found and fixed during this checkpoint's own
hardening pass (Section 16) were caught and corrected before any of the
runs in this table — neither is a disclosed-but-unfixed pre-existing
flake; both are structurally prevented. The one disclosed intermittent
failure above is a pre-existing Phase 5 test-timing sensitivity, not an
R2-012 defect.

## 22. Synthetic rehearsal

Executed end-to-end against the fake MT5 adapter, an isolated
`LOCALAPPDATA`, and the committed `fixtures/alsakkaf_scalping_synthetic_market.json`
fixture (60 bars: a 20-bar chop building a clean swing low, then a
40-bar accelerating strong-bodied breakout leg). Every one of the 27
mega-prompt-mandated rehearsal steps passed:

1–2. Started `OFF`; fixture loaded (60 bars).
3–6. Indicators computed; R2-010 evidence bridge run;
`TRADE_CANDIDATE` demonstrated on **both** gates (this module's own
90/100 score and R2-010's independent `MARKET_INTELLIGENCE_ALL_GATES_PASSED`).
7–8. Precision Scalping plan created: entry `1961.00`, stop `1959.0966`,
three targets, lots `0.13`, risk `25.0000` (exactly `0.25%` of `10000`
equity).
9. Breakout Ladder plan created: 3 `BUY_STOP` orders at `1961.50`/`1962.00`/`1962.50`.
10. Exact total-risk conservation proven: `25.0000 == 8.333... × 3`.
11. OCO cancellation function exercised on the ladder's same-direction
set.
12. No lot escalation proven: lot size unchanged after simulating a
`$25` equity loss (`0.13 -> 0.13`, since `risk_per_cycle_pct` never
increases).
13–14. `order_check` then `order_send` simulated via the fake adapter in
`DEMO_AUTO`; cycle reached `ACTIVE` with exactly one filled position
(ticket `700001`).
15–18. Management-rule geometry (breakeven `0.8R`, ATR trailing `1.0R`,
stop-never-widens, time exit) recorded on the cycle and demonstrated
structurally via the dedicated unit tests (Section 11/13 of the
contract); no separate live position-management loop exists to
step through in this fake-adapter rehearsal, matching V0 scope.
19–20. Restarted with a fresh `ScalpingService` against the same durable
journal: resolved product state `DEMO_AUTO` immediately; `reconcile()`
returned the exact same owned position.
21. Daily-loss block triggered: a simulated 2% equity drop against the
default 1% daily-loss cap produced `SCALPING_DAILY_LIMIT_BREACHED`.
22–24. Emergency stop triggered with one owned pending order (ticket
`501`) and one deliberately unrelated foreign-magic order (ticket
`999`) present: exactly `[501]` was cancelled; `999` was never
referenced.
25. Product state and operating mode both returned to `OFF`.
26–27. Isolated `LOCALAPPDATA` removed; zero lock files remained before
removal.

## 23. Real 4T MT5 demo rehearsal

**Performed, in three explicit Founder-authorized stages, after the
synthetic rehearsal and two clean full-suite runs above:**

**Stage 1 — read-only preflight** (no `login`, `symbol_select`,
`order_check`, or `order_send`): connected to the Founder's already
authenticated local terminal via `initialize`/`terminal_info`/
`account_info`/`symbols_get`/`symbol_info`/`symbol_info_tick`/
`copy_rates_from_pos`/`orders_get`/`positions_get`/`shutdown` only.
Confirmed: demo account (`trade_mode` `0`, redacted login `...1837`),
terminal connected, Algo Trading initially disabled at the terminal level
(a real, correctly-detected blocking preflight condition, reported and
left unresolved by design pending the Founder's own terminal action) then
re-verified enabled on a second pass; `XAUUSD` uniquely discovered,
visible, tradeable, fresh tick, sufficient completed-bar history on every
required timeframe. All twenty governed preflight checks passed on the
second pass, re-verified against the actual `alsakkaf_scalping_mt5.run_preflight`
function fed the real observed values (not merely eyeballed).

**Stage 2 — governed local mutations plus a real `ANALYZE_ONLY` cycle**
(no broker mutation; `mt5.shutdown()` called before any local mutation):
`XAUUSD -> XAUUSD` symbol mapping saved via `ScalpingService.save_symbol_map`
(product state `OFF` at the time, as required); product state transitioned
`OFF -> ANALYZE_ONLY`; the profile's `risk_per_cycle_pct` was reduced to
`0.10%` for this one proof cycle (a Founder-specified tighter bound than
the module's own `0.25%` default, still within the `0.50%` hard cap);
real M1/M5 completed bars were fetched and fed through the exact same
`evaluate_setup`/`analyze` pipeline the automated test suite exercises.

**Real result: `direction = NONE`, `total_score = 0/100`, classification
`WAIT`.** No R2-010 bridge call was made (the bridge only runs when this
module's own classification is `TRADE_CANDIDATE`) — the real market did
not present a qualifying setup at the moment of this rehearsal. Per the
Founder's explicit instruction, this result was **not overridden, not
retried with different bars, and no threshold was adjusted.** Product
state was returned to `OFF` immediately; operating mode remained `OFF`
throughout (never transitioned to `MT5_DEMO_AUTOMATED`, since `DEMO_AUTO`
is only requested once a `TRADE_CANDIDATE` exists) — Stage 3
(`DEMO_AUTO`, `order_check`, `order_send`, position verification, governed
emergency-stop closure) was consequently **never reached**, because there
was nothing valid to trade. This is the system working exactly as
designed: `TRADE_CANDIDATE`-gated execution means no order is ever placed
merely because automation was armed.

**Minimum-volume risk pre-check (computed for completeness, not acted on
since no trade was authorized):** at the observed ATR/spread, the implied
risk of one minimum-volume (`0.01` lot) `XAUUSD` position was
`$1.4835`, against a `0.10%`-of-equity cap of `$125.25` (real equity
`$125,248.83`) — comfortably within bound, confirming the proof-cycle risk
plan itself was sound; only the market setup was absent.

Final broker state: unchanged (`0` positions, `0` pending orders, before
and after). No credential was read, stored, or logged at any point. Final
product state `OFF`; final operating mode `OFF`; port `8765` clear; no
Python process; no lock file. The fully implemented system remains
unmodified and ready for a further rehearsal attempt whenever the Founder
requests one — no code defect was found or needed correction during this
rehearsal.

## 24. Compatibility

Phase 5 (7 modules), Phase 6 (5 modules), R2-010 (6 modules), R2-011 (7
modules), and `ModeService`/`app.py`/`server.py` all pass unmodified
(save the three `test_operating_mode.py` assertions updated per Section
6) in both full-suite runs. No R2-010/R2-011 contract, source, or test
file was touched.

## 25. No-network-client / no-live-account / no-credential proof

No `import requests`, `urllib.request`, or `websocket` anywhere in the
eight new source modules (only `MetaTrader5`, lazily, inside
`RealScalpingMT5Adapter` methods — never at module or construction time,
`test_no_metatrader5_import_at_module_level`/`test_real_adapter_never_imports_metatrader5_at_construction`).
No live-account order path exists anywhere (Section 6). No password,
investor password, access token, or broker-server string is ever stored,
journaled, or returned by any CLI/HTTP response
(`test_account_status_never_exposes_full_login`,
`test_journal_payload_never_contains_credential_shaped_keys`,
`test_order_plan_never_contains_account_fields`).

## 26. Known limitations

- Category-score sub-formulas and the full-confidence evidence-strength
  mapping (Section 9, 10) are this checkpoint's two accelerated-V0
  engineering decisions, documented in-module; a later contract may
  refine them.
- ALSAKKAF SCALPING product-state changes are resolved from the durable
  journal at each service construction, not hot-polled by an already-
  running server process — identical, accepted limitation to
  `ModeService`'s own Section 12 "next start, not live" behavior.
- `ScalpingService.shutdown()` exists but is not yet wired into
  `app.py`'s nested nested-retry shutdown cascade (Section 776–816 of
  `app.py`) — every append is still durably persisted synchronously on
  every call regardless, so no audit event is lost; only the final
  `SERVICE_STOPPED` journal courtesy event is skipped on an ordinary
  dashboard shutdown. A later pass can fold it into the existing cascade.
- Position management (breakeven/trailing/time-exit) is implemented as
  contract-documented geometry and covered by unit tests, not yet as a
  standalone live polling loop against open positions — V0 scope is
  entry-cycle automation; a later checkpoint can add continuous
  management polling.

## 27. Remaining blockers

None for the implementation. The real 4T MT5 demo rehearsal (Section 23)
was performed under explicit Founder authorization and passed every gate
up to and including the point where a genuine `TRADE_CANDIDATE` is
required — none existed at that moment, so `order_check`/`order_send`
were correctly never reached. **One operational validation item remains
open: an actual broker-verified `order_check`/`order_send` round trip on
the real 4T demo terminal**, achievable only during a further, separately
authorized bounded rehearsal at a moment when the real market presents a
qualifying setup. This is not an implementation defect, not a reason to
weaken the strategy or lower its thresholds, and not permission to
manufacture a signal, trade a real account, or run unattended continuous
automation.

## 28. Final state

Final product state: `OFF` (never entered outside the bounded real proof
rehearsal, which itself never left `ANALYZE_ONLY`). Final operating mode:
`OFF`. Port `8765`: confirmed clear. Process: no `python.exe` running.
Lock files: none remaining. Git: **committed and pushed** — implementation
commit `791ea98...`, consecutive-suite verification commit `0edd4ad...`,
both independently re-verified equal to the live remote branch and
upstream-tracking ref via a fresh `git fetch`, ahead/behind `0 0`, working
tree and index clean, no untracked file, `main` unchanged. Broker-server
execution proof (an actual `order_check`/`order_send` round trip) remains
an open **operational validation item** — not an implementation defect —
pending a genuine `TRADE_CANDIDATE` during a further, separately
authorized bounded rehearsal. See `git status`/`git rev-parse HEAD`
directly for the exact current working-tree state at any later point this
document is read.
