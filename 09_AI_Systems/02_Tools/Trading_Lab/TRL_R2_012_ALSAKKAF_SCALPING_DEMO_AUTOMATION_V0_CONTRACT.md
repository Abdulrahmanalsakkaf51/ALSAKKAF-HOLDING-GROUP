# TRL-R2-012 ALSAKKAF SCALPING Demo Automation V0 Contract

> **MT5 DEMO ACCOUNT ONLY — REAL-MONEY AUTOMATION IS HARD-LOCKED OUT OF THIS
> CONTRACT AND FAILS CLOSED INDEPENDENTLY OF `ModeService` — NO MARTINGALE —
> NO UNCONTROLLED GRID — NO LOT ESCALATION AFTER LOSS**

Product name displayed everywhere: **ALSAKKAF SCALPING**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-012 (accelerated contract-and-implementation checkpoint, single sprint) |
| Status | Founder-authorized this session via the TRL-R2-012 accelerated prompt. Contract authored, then implemented in the same uncommitted checkpoint. |
| Depends on | `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (`ModeService` authority; narrowly amended, Section 16), Phase 5 (`mt5_execution_adapter.py` demo/real account-mode detection pattern, reused), TRL-R2-010 (Market Intelligence V0 / TRL CORTEX V0 — unmodified, called as a bridge dependency only, Section 10), TRL-R2-011 (Data Fabric and Replay V0 — unmodified, optional replay-data input source, Section 10) |
| Feeds | No later phase. This checkpoint narrowly authorizes MT5-demo-only automated execution for exactly one product surface (ALSAKKAF SCALPING). It does not authorize, gate, or advance Phase 7, live automation, or any other checkpoint. |

---

## 0. Numbering and classification decision

This contract is numbered **TRL-R2-012**. It reuses no existing `TRL-R2-0XX`
document and modifies no existing R2-010/R2-011 contract, schema, journal,
or test. It is recorded as a new, independent, informational row —
**Phase 6C — ALSAKKAF SCALPING Demo Automation V0 (TRL-R2-012)** — in
`TRL_FULL_VISION_MASTER_PROGRAM.md`, positioned after Phase 6B. It is not
Phase 7 and does not reorder Phases 7–14.

## 1. Checkpoint purpose and classification

ALSAKKAF SCALPING is a narrowly bounded, demo-only, automated scalping and
intraday execution product built on the existing MT5 demo-manual adapter
architecture (Phase 5), the existing Market Intelligence V0 decision engine
(TRL-R2-010), and a new deterministic technical-evidence bridge. It is the
**first** checkpoint in this program authorized to call `order_check` and
`order_send` automatically, without a human confirming each individual
order — and that authority exists **only** while every demo-account
safety gate in Section 7 passes, for the local, already-authenticated MT5
demo terminal.

**Is:** demo-only, locally executed, deterministic decision-to-order
pipeline, bounded-risk, auditable, restart-safe, emergency-stoppable.

**Is not:** a real-money system, a guaranteed-profit system, a martingale
system, an uncontrolled grid system, a Phase 7 artifact, a replacement for
Phase 5/6 manual execution (which remain unchanged and available), or a
modification of R2-010's research-only classification engine.

## 2. Hard execution boundary (real-money lock)

This contract authorizes automated `order_check`/`order_send` for
**MT5 demo accounts only**. The following are true everywhere in the
implementation, with no exception and no configuration override:

- `alsakkaf_scalping_mt5.py` independently verifies `trade_mode ==
  ACCOUNT_TRADE_MODE_DEMO` (identical constant/pattern to
  `mt5_execution_adapter.py`) on **every** preflight call, immediately
  before every `order_check` and every `order_send` — never cached from an
  earlier check, never inferred from `ModeService`.
- If the account cannot be positively proven DEMO, `DEMO_AUTO` cannot be
  entered, `order_check`/`order_send` are refused with
  `SCALPING_ACCOUNT_NOT_PROVEN_DEMO`, and no further inference or guess is
  attempted.
- `ModeService`'s `MT5_DEMO_AUTOMATED` mode and the new
  `alsakkaf_scalping_demo_automation` capability (Section 16) are the
  *first* gate; the independent adapter-level demo check (this section) is
  the *second*, unconditional gate. Either gate failing blocks execution —
  there is no path where only one of the two gates is checked.
- No code path in this checkpoint constructs `RealMT5ExecutionAdapter`,
  grants `MT5_LIVE_AUTOMATED`/`MT5_LIVE_MANUAL` new authority, stores a
  credential, or reads a password/token of any kind. The Founder's already
  logged-in local terminal session is reused exactly as Phase 5 already
  does; no login flow is implemented.
- Martingale, lot-escalation-after-loss, and uncontrolled/unbounded grid
  behavior are structurally impossible per Sections 11–13: lot size is a
  pure function of a fixed risk percentage and current stop-loss geometry,
  never of prior cycle outcome; every ladder is bounded to six orders
  sharing one fixed total-risk budget; no cycle ever creates a replacement
  order after a loss.

## 3. Product operating states

Five states, held by `ScalpingProductState` (separate from `ModeService`'s
`current_mode`, exactly the way R2-009 basket state is separate from
`ModeService`):

| State | Meaning |
|---|---|
| `OFF` | No analysis loop, no new order, no new pending order. Existing owned positions remain visible (read-only). |
| `ANALYZE_ONLY` | Live demo quotes/bars may be read; decisions and order *plans* may be generated and displayed; `order_check`/`order_send` are refused with `SCALPING_STATE_FORBIDS_EXECUTION`. |
| `DEMO_AUTO` | Automated `order_check`/`order_send`/position management permitted, **only** while the operating mode is `MT5_DEMO_AUTOMATED` and every Section 7 gate passes on every cycle. |
| `PAUSED` | No new entries, no new pending orders. Existing owned positions/pending orders remain managed (stop/target/breakeven/trailing/time-exit remain active). Entered automatically on a risk-limit breach (Section 11) or manually. |
| `EMERGENCY_STOP` | Latched. Blocks every new decision/order. Cancels every ALSAKKAF-owned pending demo order and closes every ALSAKKAF-owned demo position via bounded, audited attempts (Section 14.5). Never touches an order/position not owned by this application. Remains latched until an explicit `scalping-reset-emergency-stop` local-operator action. |

State transitions are event-sourced in the ALSAKKAF SCALPING journal
(Section 15) exactly as `ModeService` event-sources mode transitions —
`current_product_state` is always derived by replaying
`SCALPING_STATE_CHANGED` events, never stored as an independently editable
field. Allowed transitions:

```
OFF             -> ANALYZE_ONLY, DEMO_AUTO*, EMERGENCY_STOP
ANALYZE_ONLY    -> OFF, DEMO_AUTO*, EMERGENCY_STOP
DEMO_AUTO       -> OFF, ANALYZE_ONLY, PAUSED, EMERGENCY_STOP
PAUSED          -> OFF, ANALYZE_ONLY, DEMO_AUTO*, EMERGENCY_STOP
EMERGENCY_STOP  -> OFF (only via scalping-reset-emergency-stop, which
                   additionally requires zero owned open pending orders
                   and a fresh reconciliation pass, Section 14.6)
```

`*` A transition into `DEMO_AUTO` additionally requires
`ModeService.current_mode == MT5_DEMO_AUTOMATED` and a passing preflight
(Section 7); otherwise it is rejected with
`SCALPING_DEMO_AUTO_PREFLIGHT_FAILED` and the product state is unchanged.
Every rejected transition still leaves the state unchanged, mirroring
`ModeService`'s fail-closed transition contract.

## 4. Strategy profiles

Three closed profile identifiers: `ALSAKKAF_PRECISION_SCALPING`,
`ALSAKKAF_BREAKOUT_LADDER`, `ALSAKKAF_INTRADAY`. Exactly one profile is
active per symbol cycle. Profile parameters are configurable within the
Section 11/12 hard bounds; the profile identifier and its resolved
parameter set are recorded on every `CYCLE_CREATED` event.

### 4.1 ALSAKKAF PRECISION SCALPING

- Timeframes: `M1` entry, `M5` confirmation, `M15` context.
- One active entry cycle per symbol maximum.
- Entry: market or stop order, selected deterministically by setup type
  (breakout setup → stop order at structure; pullback/reversal setup →
  market order at confirmed close) — never a coin-flip or unspecified
  choice.
- Mandatory stop loss (Section 13). Three bounded take-profit allocations
  (Section 13.2). Breakeven + ATR trailing (Section 13.3). Time exit at 30
  minutes (Section 11). Cooldown after a losing cycle: 15 minutes.

### 4.2 ALSAKKAF BREAKOUT LADDER

- Up to 3 Buy Stop orders above current price, up to 3 Sell Stop orders
  below current price; 6 pending orders maximum per cycle.
- Every pending order carries an expiration time (5 minutes default,
  Section 11) and a mandatory stop loss.
- All orders in the cycle share **one** total cycle-risk budget
  (Section 12.1); lot sizes are divided from that one approved risk
  amount; no order in the ladder increases lot size relative to any other
  order in the same cycle based on prior loss.
- Ladder-distance floor (exact):

  ```
  ladder_distance_floor = max(
      Decimal("0.25") * entry_timeframe_atr,
      Decimal("2") * current_spread,
      broker_minimum_stop_distance,
      one_broker_point,
  )
  ```

  Every pending level must be at least `ladder_distance_floor` from the
  current reference price, computed in exact `Decimal` price units.
- On first directional fill: cancel every remaining owned
  opposite-direction pending order in the cycle; recompute remaining
  cycle risk; cancel any remaining same-direction order that would push
  cumulative filled+pending risk above the cycle's original total-risk
  budget. No replacement order is ever created automatically
  (Section 14.4).
- Both directional ladders are never simultaneously "armed as a hedge" —
  cancellation on first fill is unconditional, not configurable.
- On expiry, `PAUSED`, or `EMERGENCY_STOP`: cancel every remaining owned
  pending order in the cycle.

### 4.3 ALSAKKAF INTRADAY

- Timeframes: `M15` entry, `H1` confirmation, `H4` context.
- Wider structural stop (`1.5 x ATR` floor instead of Precision Scalping's
  `1.0 x ATR`), longer holding time (8 hours, Section 11), no rapid ladder
  by default (ladder profile fields unset; a single market/stop entry
  only).
- Fewer trades: one active cycle per symbol, minimum 15-minute gap between
  two Intraday cycles on the same symbol regardless of cooldown state.

## 5. Operating-mode capability

### 5.1 New capability: `alsakkaf_scalping_demo_automation`

A twentieth governed capability, added to
`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (Section 16 of this document
records the exact amendment). Granted **only** to `MT5_DEMO_AUTOMATED`:

| Mode | `alsakkaf_scalping_demo_automation` granted? |
|---|---|
| `OFF` | No |
| `RESEARCH` | No |
| `SYNTHETIC_PAPER` | No |
| `MT5_DEMO_MANUAL` | No |
| `MT5_DEMO_AUTOMATED` | **Yes** |
| `MT5_LIVE_MANUAL` | No |
| `MT5_LIVE_AUTOMATED` | No |

This is the first checkpoint that makes `MT5_DEMO_AUTOMATED` reachable in
the transition matrix: `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 4
gains exactly one new row, `RESEARCH -> MT5_DEMO_AUTOMATED` and
`MT5_DEMO_AUTOMATED -> OFF, RESEARCH`, subject to the existing
`is_available()`/prerequisite-check machinery. `MT5_DEMO_AUTOMATED`
continues to grant no live-account authority whatsoever — it is a
strictly demo-scoped mode, enforced independently by Section 2's adapter
lock regardless of what `ModeService` reports.

### 5.2 Read-only availability

Read-only ALSAKKAF SCALPING dashboard/CLI/HTTP operations (status, list
cycles, inspect cycle, list owned orders/positions, journal tail) require
no capability grant and remain available in every mode including `OFF`,
matching the existing repository convention.

## 6. Demo-only MT5 safety gate (preflight, exactly 20 checks)

Before `DEMO_AUTO` may be entered or any cycle executed, **all twenty**
checks below must pass, in this order; the first failing check is the
reported blocker, but every check's result is recorded on the
`SCALPING_PREFLIGHT_RECORDED` — wait, preflight is read-only and does not
mutate the journal by itself; it is recorded only as part of the cycle
that consumes it (Section 14.1). A failed preflight blocks `DEMO_AUTO`
entry and blocks every order plan from proceeding to `order_check`.

1. `MetaTrader5` Python package imports successfully.
2. `mt5.initialize()` succeeds against the local terminal.
3. `mt5.terminal_info().connected` is `True`.
4. `mt5.account_info()` is readable and non-`None`.
5. `account_info().trade_mode == ACCOUNT_TRADE_MODE_DEMO` (Section 2).
6. Account is not `CONTEST` and not `REAL` (redundant with #5, checked
   independently as defense in depth against a future constant change).
7. `account_info().trade_allowed` is `True`.
8. `terminal_info().trade_allowed` (Algo Trading) is `True`.
9. The mapped broker symbol (Section 8) exists via `mt5.symbol_info()`.
10. The symbol is visible, or `mt5.symbol_select(symbol, True)` succeeds.
11. The latest tick (`mt5.symbol_info_tick()`) is not older than
    `MAX_QUOTE_STALENESS_SECONDS = 10`.
12. The symbol's trading session is open (`symbol_info().trade_mode` is
    not `SYMBOL_TRADE_MODE_DISABLED`/`SYMBOL_TRADE_MODE_CLOSEONLY`, and a
    fresh tick was obtainable per #11).
13. `volume_min`, `volume_max`, `volume_step` are readable and
    `0 < volume_min <= volume_max`, `volume_step > 0`.
14. `digits` and `point` are readable and `point > 0`.
15. `trade_stops_level` and `trade_freeze_level` are readable (`>= 0`).
16. Current spread (`ask - bid`, in points) is within the active
    profile's configured `max_spread_points` bound.
17. `account_info().equity > 0`.
18. Current computed daily loss and session drawdown (Section 11) have
    not breached their hard caps.
19. `EMERGENCY_STOP` is not the current product state.
20. No manual event-risk block (Section 9's `EVENT_RISK` local flag) is
    active for the mapped symbol.

If check 5 or 6 cannot positively prove DEMO, preflight fails closed with
`SCALPING_ACCOUNT_NOT_PROVEN_DEMO` and no further check is evaluated or
inferred. No credential, password, investor password, access token, full
account login, or broker-server string is ever included in a preflight
result, a journal payload, a CLI response, an HTTP response, or a log
line — only the redacted `account_login_last4` (last 4 digits) and
`trade_mode_name` (`"DEMO"`) are ever surfaced.

## 7. Broker symbol discovery and mapping

`alsakkaf_scalping_data.py` implements `discover_symbol_candidates(canonical_instrument)`
for the canonical research instruments `XAUUSD, NAS100, EURUSD, GBPUSD,
USDJPY` (same allowlist as R2-010/R2-011, reused verbatim). It enumerates
`mt5.symbols_get()` read-only metadata and returns every broker symbol
whose name, after case-insensitive normalization, contains the canonical
instrument's known aliases (`XAUUSD` -> `xauusd`, `gold`; `NAS100` ->
`nas100`, `us100`, `usa100`, `ustec`, `nq100`) — this is discovery/display
only, **never** an automatic selection.

The active mapping (`canonical_instrument -> broker_symbol`) is stored
locally in `TRL_SCALPING_SYMBOL_MAP.v1`
(`%LOCALAPPDATA%\ALSAKKAF\TradingLab\scalping-symbol-map-v1.json`),
editable only while the product state is `OFF`, and is never treated as
universal broker truth — it is re-validated against live `symbol_info()`
on every preflight (Section 6, check 9). Saving a mapping while the
product state is not `OFF` fails with
`SCALPING_SYMBOL_MAP_REQUIRES_OFF_STATE`. Ambiguous candidates (more than
one match) are never silently resolved; the CLI/dashboard must show all
candidates and require an explicit `scalping-save-symbol-map` selection.

## 8. Technical intelligence and evidence

### 8.1 Indicators (`alsakkaf_scalping_indicators.py`)

Computed with `Decimal` arithmetic (`quantize_4`, `ROUND_HALF_EVEN` — same
policy as R2-010 Section 10.1, reused verbatim) over **closed bars only**:
EMA 9/21/50, RSI 14, ATR 14, ADX 14, MACD (12/26/9), recent swing
high/low (fractal-based, 5-bar), nearest support/resistance (recent swing
cluster), candle-body/range statistics, spread-to-ATR ratio, and
multi-timeframe direction (EMA 21 slope sign on the confirmation
timeframe). The current, unfinished bar is used only for the current
quote (spread/execution-price checks) — never for a directional
indicator value.

### 8.2 Scoring (100 points, six categories)

```
trend                     : 25
momentum                  : 20
market_structure          : 20
volatility_suitability    : 15
spread_and_cost           : 10
multi_timeframe_alignment : 10
```

Each category score is an integer `0..<cap>` computed deterministically
from the Section 8.1 indicators (e.g. `trend` awards points for
EMA9>EMA21>EMA50 alignment plus ADX strength bucket; full per-category
formulas are implemented in `alsakkaf_scalping_strategy.py` and documented
in its module docstring, since the mega-prompt does not fix exact
sub-formulas — this is the one accelerated-V0 engineering decision this
contract makes, mirroring how R2-010 documented its own two accelerated-V0
decisions in Section 2 of its evidence document).

Thresholds: `75-100 -> TRADE_CANDIDATE`, `60-74 -> WAIT`, `0-59 -> REJECT`;
any hard safety/risk failure (Section 6 preflight, missing stop geometry,
broker constraint, journal corruption, uncertain prior result) ->
`BLOCKED`, overriding any score. Direction is `BUY`, `SELL`, or `NONE`
(`NONE` when the setup does not identify a clear side, e.g. inside
consolidation) and forces `WAIT` regardless of score.

### 8.3 R2-010 evidence bridge

`alsakkaf_scalping_strategy.py` constructs a complete, valid
`TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1` envelope (R2-010 Section 7)
from live demo bars/quotes (or validated R2-011 replay data) and the
Section 8.1/8.2 evidence above, mapped one-for-one onto R2-010's eleven
Evidence Council categories (`MARKET_STRUCTURE`, `TREND`, `MOMENTUM`,
`VOLATILITY`, `LIQUIDITY_AND_SPREAD`, `MULTI_TIMEFRAME_ALIGNMENT`,
`EVENT_RISK`, `EXECUTION_COST`, `RISK_EXPOSURE`, `CONTRADICTING_EVIDENCE`,
`DATA_QUALITY`), then calls R2-010's unmodified
`market_intelligence_service.analyze_market_snapshot(...)` exactly as any
other caller would. `EVENT_RISK` evidence strength/direction is derived
**only** from the Section 7 local manual event-risk flag — no external
news or macro API is called, matching R2-010's own hard boundary.

**Only a `TRADE_CANDIDATE` result may proceed to a demo order plan.**
`WAIT`, `REJECT`, `BLOCKED`, and `EXPIRED` create no demo order — the
ALSAKKAF SCALPING service checks
`decision.final_status == "TRADE_CANDIDATE"` before calling
`alsakkaf_scalping_risk.py` at all. R2-010's source is not modified; this
bridge is purely an additional caller of its existing public service
function, exactly as Section 5 of the R2-010 contract already anticipates
("Any future conversion... requires a separate, explicitly
Founder-approved handoff contract" — this is that contract, and it does
not weaken any R2-010 validation, gate, or threshold).

## 9. Event-risk manual block

A local, dashboard/CLI-editable per-canonical-instrument boolean flag
(`event_risk_blocked`), defaulting to `false`, persisted in the same
symbol-map store as Section 7. When `true` for the cycle's instrument,
preflight check 20 fails with `SCALPING_MANUAL_EVENT_RISK_BLOCK` and the
R2-010 bridge's `EVENT_RISK` evidence item is forced to
`normalized_strength = 1.0000` (maximal severity), which independently
drives R2-010's own hard event-risk gate. No automatic news/macro
detection exists in V0.

## 10. Optional R2-011 replay input

`ANALYZE_ONLY` and synthetic rehearsal may source bars from a validated
R2-011 replay snapshot instead of live MT5 bars, via
`alsakkaf_scalping_data.bars_from_replay_snapshot(...)`. This is a
read-only consumer of R2-011's existing public replay-snapshot shape; it
does not write to the R2-011 journal, does not create a replay session
automatically, and is never used as the bar source while `DEMO_AUTO` is
active (`DEMO_AUTO` requires live MT5 bars only — `SCALPING_DEMO_AUTO_REQUIRES_LIVE_DATA`
if a replay source is configured while entering `DEMO_AUTO`).

## 11. Risk policy

All risk arithmetic uses `Decimal`. Configurable settings, each with a
**safe default** and a **hard V0 cap** the dashboard cannot exceed
(reducing risk below the default is always permitted):

| Setting | Safe default | Hard cap |
|---|---|---|
| Risk per cycle (% of current equity) | 0.25% | 0.50% |
| Maximum total active ALSAKKAF risk (% of equity) | 0.50% | 1.00% |
| Maximum daily loss (% of start-of-day equity) | 1.00% | 2.00% |
| Maximum session drawdown | 2.00% | 3.00% |
| Maximum consecutive losing cycles | 3 | 3 (not configurable) |
| Cooldown after a losing cycle | 15 minutes | minimum 15 minutes |
| Maximum owned open positions | 3 | 5 |
| Maximum owned pending orders | 6 | 8 |
| Market-open cooldown | 10 minutes | minimum 10 minutes |
| Scalping max holding time | 30 minutes | maximum 30 minutes |
| Intraday max holding time | 8 hours | maximum 8 hours |
| Pending expiry (scalping / intraday) | 5 min / 30 min | maximum 15 min / 60 min |

One active cycle per symbol, always (not configurable). A daily-loss or
session-drawdown breach transitions the product state to `PAUSED`
automatically and records `DAILY_LIMIT_REACHED`; three consecutive losing
cycles transition to `PAUSED` and start the cooldown timer; neither
condition creates a martingale response — the *next* cycle after cooldown
uses the identical Section 11 risk-per-cycle percentage, never an
increased one.

A dashboard-submitted configuration that exceeds any hard cap is rejected
with `SCALPING_RISK_SETTING_EXCEEDS_HARD_CAP` and the prior configuration
is retained unchanged (fail closed, not clamp-and-accept).

### 11.1 Lot sizing (fail closed)

```
risk_amount   = equity * (risk_per_cycle_pct / Decimal("100"))
stop_distance = abs(entry_price - stop_price)          # > 0, required
value_per_point = tick_value / tick_size                # from symbol info
raw_lots      = risk_amount / (stop_distance * value_per_point)
lots          = floor_to_step(raw_lots, volume_step)
```

`lots` is then clamped: if `lots < volume_min`, the cycle fails closed
with `SCALPING_LOT_BELOW_BROKER_MINIMUM` (never silently rounded up past
the risk budget); if `lots > volume_max`, `lots = volume_max` **and** the
plan is re-validated to confirm the resulting risk does not exceed
`risk_amount` (if it would, fail closed with
`SCALPING_LOT_CANNOT_BE_BOUNDED_TO_RISK` rather than silently accepting
extra risk). No fixed-lot override may exceed this calculated budget,
ever. Any missing/non-finite input (`tick_value`, `tick_size`,
`volume_step`, `stop_distance == 0`) fails closed with
`SCALPING_LOT_CALCULATION_UNPROVABLE` before any `order_check` call.

## 12. Ladder cycle-risk conservation (Breakout Ladder)

### 12.1 Total-risk budget

One cycle-risk budget (`risk_amount` above, Section 11.1) is divided
across up to 6 pending orders by equal per-order risk
(`per_order_risk = risk_amount / order_count`), each order's own lot size
computed from Section 11.1 using its own stop distance. The sum of every
order's individual risk contribution must equal `risk_amount` exactly
within one `volume_step`'s worth of rounding tolerance; any residual from
step-rounding is **never** redistributed onto another order — it is
recorded as `unallocated_risk_remainder` on the cycle record and simply
left unused (fail-closed-safe under-allocation, never over-allocation).

### 12.2 OCO cancellation exactness

On the first ladder fill (Section 4.2), remaining opposite-direction
orders are cancelled unconditionally; remaining same-direction orders are
kept only while cumulative risk (filled + still-pending same-direction)
stays `<= risk_amount`, evaluated order-by-order in ascending distance
from the fill price; any order that would breach the cap is cancelled,
never resized. This is directly test-verified (Section 21) as "exact
total-risk conservation" and "no lot escalation."

## 13. Stop, target, and management rules

### 13.1 Mandatory stop-loss geometry

Every order requires a stop loss before `order_check` is ever called —
there is no code path that calls `order_check`/`order_send` with a
missing or non-finite stop. Default Precision Scalping distance:

```
stop_distance = max(
    Decimal("1.0") * entry_timeframe_atr,
    broker_minimum_stop_distance,
    spread_safety_floor,   # 1.5 * current_spread
)
```

Intraday uses `Decimal("1.5")` in place of `Decimal("1.0")`.

### 13.2 Targets and allocation

Target 1 = `1.0R`, Target 2 = `1.5R`, Target 3 = `2.0R` (`R = stop_distance`).
Default allocation `50% / 30% / 20%`, summing to exactly `100%`. When
broker volume constraints prevent an exact three-part split at the
computed `lots`, the service computes the **largest valid deterministic
allocation that preserves total risk** (never increases total volume): it
reduces the number of targets actually filled (3 -> 2 -> 1) until each
part is `>= volume_min`, and records `actual_allocation_pct` truthfully
(never silently claiming `50/30/20` when reality is `100/0/0`).

### 13.3 Management

- Move stop to breakeven after `0.8R` favorable movement.
- Begin ATR trailing after `1.0R` favorable movement (`trail_distance =
  1.0 * ATR14`, tightened toward price, never loosened).
- A stop modification is only ever submitted if it is at least as close
  to safety as the previous stop (`SCALPING_STOP_CANNOT_WIDEN` blocks any
  attempt to move a stop farther from the current price than its current
  value on the risk-reducing side).
- Close remaining volume at the profile's maximum holding time
  (Section 11).
- Close/cancel immediately when `EMERGENCY_STOP` requires it (Section 14.5).

## 14. Execution model

### 14.1 Exact per-cycle mutation sequence

Every automatic demo action (`order_check`, `order_send`, cancel, modify,
close) follows exactly:

1. Acquire the authoritative ALSAKKAF SCALPING mutation lock
   (`SCALPING_STRATEGY_LOCK`, same cross-process owner-token file-lock
   primitive as `mt5_execution_journal.py`/`market_data_replay_journal.py`,
   `LOCK_TIMEOUT_SECONDS = 10.0`, `LOCK_POLL_INTERVAL_SECONDS = 0.02`, no
   unlocked fallback).
2. Reload the ALSAKKAF SCALPING journal and derive current execution
   state after lock acquisition.
3. Verify no `UNCERTAIN` cycle exists that would freeze this mutation
   (Section 14.3).
4. Re-run the full Section 6 preflight (all 20 checks) fresh — never
   reused from an earlier cycle or an earlier moment in this same cycle.
5. Construct exactly one deterministic order plan (`TRL_SCALPING_ORDER_PLAN.v1`,
   Section 15.2).
6. Assign ownership metadata: a dedicated magic number
   (`ALSAKKAF_SCALPING_MAGIC = 384512`, fixed constant, never shared with
   Phase 5/6/basket magic numbers) and comment prefix
   `"ALSAKKAF_SCALPING"` (truncated to the broker's comment length limit,
   never silently changed).
7. Call `order_check` exactly once for this plan.
8. Interpret the result using the governed result-code mapping
   (Section 14.2).
9. If approved, call `order_send` exactly once for this plan — **never**
   retried blindly on any ambiguous outcome.
10. Persist the exact returned MT5 ticket/retcode/comment/identifiers.
11. Reload/confirm the resulting order or position via a fresh
    `positions_get`/`orders_get` call filtered by the magic number.
12. If the result is uncertain (Section 14.3), freeze the cycle, send
    nothing else in this mutation, and require `scalping-reconcile`.
13. Release the lock via owner-token safety (matching the existing
    journal lock release pattern exactly).

### 14.2 Governed `order_check`/`order_send` result codes

`order_check` results map to exactly three outcomes:
`CHECK_APPROVED` (proceed to `order_send`), `CHECK_REJECTED` (cycle ->
`BLOCKED`, reason recorded, no `order_send` call), `CHECK_UNCERTAIN`
(adapter/timeout error — cycle -> `UNCERTAIN`, Section 14.3, no
`order_send` call). `order_send` results map to exactly three outcomes:
`SEND_CONFIRMED` (broker `retcode == TRADE_RETCODE_DONE` and a resulting
ticket was confirmed present), `SEND_REJECTED` (a definite broker
rejection retcode, e.g. `TRADE_RETCODE_INVALID_STOPS`), `SEND_UNCERTAIN`
(timeout, connection loss, or any retcode not in the governed
confirmed/rejected sets) — `SEND_UNCERTAIN` always freezes the cycle.

### 14.3 Uncertain-result freeze and reconciliation

A cycle in `UNCERTAIN` blocks **only its own symbol's** further mutation
(other symbols' cycles are unaffected) until `scalping-reconcile` runs:
reconciliation re-queries MT5 by magic number, comment prefix, and the
cycle's deterministic `order_plan_id`, and resolves the cycle to exactly
one of `ACTIVE` (a matching position/order was found), `CANCELLED` (no
matching order/position and no fill possible, per broker history), or
remains `UNCERTAIN` (ambiguous — requires a further reconciliation pass,
never a blind retry of `order_send`).

### 14.4 Restart recovery

On startup, the service reconciles every non-terminal cycle in the
journal by magic number + comment + deterministic cycle/order-plan ID
against live MT5 state, exactly as Section 14.3. The application never
manages an order/position that does not carry the ALSAKKAF SCALPING
magic number and comment prefix — a cross-check against
`Section 2` demo-account identity plus magic-number ownership runs before
any cancel/close/modify call, and a mismatch fails closed with
`SCALPING_UNOWNED_ORDER_PROTECTION` rather than acting.

### 14.5 Emergency stop execution

Entering `EMERGENCY_STOP` (manual, or automatic on an unrecoverable
journal-integrity failure) immediately, under the Section 14.1 lock:
cancels every ALSAKKAF-owned open pending order (bounded retry, max 3
attempts per order, each recorded), then closes every ALSAKKAF-owned open
position at market (same bounded-retry policy), verifying ownership via
magic number + comment on every single order/position before acting. Any
order/position that cannot be resolved within the bounded attempts is
recorded as `emergency_stop_unresolved` and surfaced prominently on the
dashboard — the state remains latched `EMERGENCY_STOP` regardless.

### 14.6 Emergency-stop reset

`scalping-reset-emergency-stop` is accepted only when zero
`emergency_stop_unresolved` items remain and a fresh reconciliation pass
(Section 14.4) confirms zero ALSAKKAF-owned open pending orders and the
reset is an explicit local-operator action — never automatic.

## 15. Journal and concurrency

A new journal, `TRL_SCALPING_JOURNAL.v1` embedded in
`TRL_SCALPING_JOURNAL_STORE.v1`
(`%LOCALAPPDATA%\ALSAKKAF\TradingLab\scalping-journal-store-v1.json`),
architecturally identical to `mt5_execution_journal.py`
(append-only, closed event vocabulary, hash-chained
`previous_event_hash`/`current_event_hash`, bounded event size
`262144` bytes, bounded journal size `268435456` bytes, bounded event
count `100000`, atomic temp-file + `os.replace` persistence,
cross-process owner-token lock, `LOCK_TIMEOUT_SECONDS = 10.0`,
`LOCK_POLL_INTERVAL_SECONDS = 0.02`, no unlocked fallback, reload after
lock, restart-safe projection, uncertain-result freeze, strict corruption
failure — never an automatic replacement journal). It is separate from
the Phase 5/6 execution journal, the R2-010 Market Intelligence journal,
and the R2-011 Market Data/Replay journal; no journal writes to another
journal's store.

### 15.1 Governed schemas

`TRL_SCALPING_ORDER_PLAN.v1` (deterministic plan: symbol, side, entry
type/price, stop, targets, lot(s), magic number, comment, profile,
risk amount — identity via the same
`"<prefix>_" + sha256("<DOMAIN>.v1\n" + canonical_json(fields))[:32]`
pattern used throughout the repository) and `TRL_SCALPING_CYCLE.v1`
(symbol, profile, reference price/ATR/spread at creation, ladder levels
when applicable, expiry, stop/target geometry, lot allocations, total
risk, broker tickets, current state).

Cycle states: `PLANNED, CHECKED, ARMED, PARTIALLY_TRIGGERED, ACTIVE,
COMPLETED, CANCELLED, EXPIRED, BLOCKED, UNCERTAIN, EMERGENCY_STOPPED`.

### 15.2 Closed event vocabulary (twenty governed types)

`SCALPING_STATE_CHANGED`, `SYMBOL_MAPPING_SAVED`, `PROFILE_CONFIGURED`,
`ANALYSIS_COMPLETED`, `DECISION_RECORDED`, `CYCLE_CREATED`,
`ORDER_PLAN_CREATED`, `ORDER_CHECK_RECORDED`, `ORDER_SEND_RECORDED`,
`ORDER_RESULT_UNCERTAIN`, `PENDING_ORDER_CANCELLED`, `POSITION_OPENED`,
`POSITION_UPDATED`, `POSITION_PARTIALLY_CLOSED`, `POSITION_CLOSED`,
`CYCLE_COMPLETED`, `CYCLE_BLOCKED`, `DAILY_LIMIT_REACHED`,
`EMERGENCY_STOP_ACTIVATED`, `EMERGENCY_STOP_RESET`,
`JOURNAL_INTEGRITY_FAILURE`. Every event is appended exactly once per
logical branch — no duplicate append for the same logical mutation. No
journal mutation occurs outside the Section 14.1 lock.

## 16. `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` amendment (authorized this checkpoint)

Exactly the amendment described in Section 5.1 above: a twentieth governed
capability, `alsakkaf_scalping_demo_automation`, granted only to
`MT5_DEMO_AUTOMATED`; a new transition-matrix row making
`MT5_DEMO_AUTOMATED` reachable from `RESEARCH` and returning to
`OFF`/`RESEARCH`.

**Implementation-discovered correction (found while building the Section
8.3 bridge, corrected in place here rather than left as a silent gap):**
R2-010's existing `market_intelligence_research` capability is granted
only to `RESEARCH`, `SYNTHETIC_PAPER`, and `MT5_DEMO_MANUAL`
(`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.2) — not to
`MT5_DEMO_AUTOMATED`. Since the Section 8.3 bridge calls R2-010's
unmodified `market_intelligence_service.analyze_market_snapshot(...)`
while the operating mode is `MT5_DEMO_AUTOMATED` during `DEMO_AUTO`, that
call would otherwise fail closed with `MARKET_INTELLIGENCE_CAPABILITY_DENIED`
on every cycle. This checkpoint therefore additionally grants
`market_intelligence_research` to `MT5_DEMO_AUTOMATED`, for exactly the
same reasoning R2-010 already documented for granting it to
`MT5_DEMO_MANUAL`: the capability grants no `order_check`, `order_send`,
`manual_broker_execution`, `manual_basket_execution`, `basket_execution`,
live execution, automated execution, or execution handoff of any kind by
itself — it gates only Market Intelligence record creation — so granting
it alongside a demo execution mode creates no additional execution risk.
This does not, by itself, grant any ALSAKKAF SCALPING execution authority;
that remains gated exclusively by `alsakkaf_scalping_demo_automation`
(Section 5.1) plus the independent Section 2 adapter-level demo-account
lock. No other row, mode, or capability changes.
`mode_service.py`'s `_CAPABILITY_MATRIX` and `MODES`/transition dict are
updated to implement exactly this amendment (Section 22 lists the file as
modified). `MT5_LIVE_AUTOMATED` and `MT5_LIVE_MANUAL` remain fully
unavailable, unchanged, per the existing Section 6 startup-safety
downgrade in that document (a forged persisted completion targeting
either live mode still forces `OFF` on load — this checkpoint does not
touch that logic).

## 17. User interface

A new dashboard section titled exactly **ALSAKKAF SCALPING**, with badges
`DEMO ACCOUNT ONLY`, `AUTOMATION STATUS`, `LIVE MONEY LOCKED`,
`EMERGENCY STOP`; controls and display fields exactly as enumerated in the
originating TRL-R2-012 prompt Section 17 (master state, profile,
canonical/mapped symbol, side restriction, risk/loss/position/pending/
spread/slippage/cooldown/session settings, manual event-risk block,
start/pause/emergency-stop/reset controls; connection/account/balance/
equity/P&L/drawdown/spread/ATR/score/decision/reasons/cycle/orders/
positions/stop-target/breakeven-trailing/journal/health/last-update
display). Implemented with safe DOM creation and `textContent` only — no
`innerHTML` anywhere in the new rendering code. All dashboard mutations
call the governed local HTTP routes (Section 18); no browser-side value is
authoritative. Layout uses responsive flex/grid so the panel is usable
from a phone browser, with an explicit on-page note that the automation
engine itself runs only on the Windows PC, and that positions/orders
placed by ALSAKKAF SCALPING are also visible in the MT5 mobile app for the
same demo account.

## 18. CLI and local HTTP

### 18.1 CLI

`python -B -W error -m trading_lab_app.alsakkaf_scalping_cli <command>`,
implementing exactly the eighteen commands listed in the originating
prompt Section 18 (`scalping-status`, `scalping-preflight`,
`scalping-discover-symbols`, `scalping-save-symbol-map`,
`scalping-configure-profile`, `scalping-analyze`,
`scalping-start-demo-auto`, `scalping-pause`, `scalping-resume`,
`scalping-emergency-stop`, `scalping-reset-emergency-stop`,
`scalping-run-cycle`, `scalping-list-cycles`, `scalping-inspect-cycle`,
`scalping-list-owned-orders`, `scalping-list-owned-positions`,
`scalping-reconcile`, `scalping-journal`), each a thin, bounded-input CLI
wrapper over `alsakkaf_scalping_service.py`, mirroring
`mt5_execution_cli.py`'s existing input-safety conventions (bounded
argument length, no shell/path injection surface, JSON output only).

### 18.2 HTTP

Local-only routes (bound to `127.0.0.1:8765` exclusively, mirroring the
existing server) for: status, preflight, symbol candidates,
configuration, current analysis, cycles, owned orders, owned positions,
journal tail (`GET`/`HEAD` only) and start/pause/resume/emergency-stop/
emergency-reset/one-cycle-execution (`POST` only, rejecting `GET` with
`405`, validating the existing local action-token/bounded-guard mechanism
`server.py` already uses for other mutation routes — no new mechanism is
invented). No route ever returns a credential, account number, or broker
server string. No outbound HTTP client, no websocket, is added anywhere
in this checkpoint.

## 19. One-click local deployment

`Start_ALSAKKAF_SCALPING_DEMO.ps1`: resolves the repository directory
safely, verifies Python and the `MetaTrader5` import, verifies terminal
state read-only, starts the dashboard on `127.0.0.1:8765`, opens it in the
default browser, leaves the initial product state `OFF`, never enables
`DEMO_AUTO` automatically, contains no credential, shows clear errors, and
avoids starting a duplicate server process (checks port 8765 first).
`Stop_ALSAKKAF_SCALPING_DEMO.ps1`: requests a governed pause (or
emergency stop if pause fails) first, then stops only the owned local
process, leaves no lock file, exposes no credential.

## 20. Known limitations (V0, stated up front)

- Category-score sub-formulas (Section 8.2) are this checkpoint's one
  accelerated-V0 engineering decision, documented in
  `alsakkaf_scalping_strategy.py`'s module docstring — a later contract
  may refine them without changing the 100-point/six-category shape.
- Product-state changes take effect only through the running service's
  own journal-derived projection (matching `ModeService`'s existing
  "resolved once, not hot-polled from a second process" limitation) —
  see `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 12 for the
  precedent this follows.
- V0 ships exactly three profiles and five canonical instruments; adding
  either requires a later contract amendment.

## 21. Testing requirements

Progressive automated coverage (fake MT5 adapter; no real MT5 order is
sent during the general unit-test suite) across the categories listed in
the originating prompt Section 21, implemented across eleven new test
modules (Section 22) plus real separate-process concurrency proof and
full compatibility regression against `ModeService`, Phase 5, Phase 6,
R2-010, and R2-011.

## 22. Expected file scope

New: `alsakkaf_scalping_data.py`, `alsakkaf_scalping_indicators.py`,
`alsakkaf_scalping_strategy.py`, `alsakkaf_scalping_risk.py`,
`alsakkaf_scalping_journal.py`, `alsakkaf_scalping_mt5.py`,
`alsakkaf_scalping_service.py`, `alsakkaf_scalping_cli.py`,
`alsakkaf_scalping_test_support.py`,
`test_alsakkaf_scalping_data.py`, `test_alsakkaf_scalping_indicators.py`,
`test_alsakkaf_scalping_strategy.py`, `test_alsakkaf_scalping_risk.py`,
`test_alsakkaf_scalping_journal.py`, `test_alsakkaf_scalping_mt5.py`,
`test_alsakkaf_scalping_service.py`, `test_alsakkaf_scalping_cli.py`,
`test_alsakkaf_scalping_http.py`, `test_alsakkaf_scalping_concurrency.py`,
`test_alsakkaf_scalping_safety.py`,
`fixtures/alsakkaf_scalping_synthetic_market.json`,
`TRL_R2_012_ALSAKKAF_SCALPING_DEMO_AUTOMATION_V0_EVIDENCE.md`,
`Start_ALSAKKAF_SCALPING_DEMO.ps1`, `Stop_ALSAKKAF_SCALPING_DEMO.ps1`.

Modified: `mode_service.py` (Section 16 amendment only),
`app.py`/`server.py`/`service.py` (additive wiring, same pattern as every
prior checkpoint), `static/index.html`/`static/app.js` (additive
dashboard section), `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`,
`TRL_BLOCKERS.md`, `TRL_APP_QUICK_START.md`,
`TRL_FULL_VISION_MASTER_PROGRAM.md`, `TRL_CONTINUATION_STATE.md`,
`TRL_CONTINUATION_STATE.json`, `TRL_DECISION_LOG.md`.

Not modified: R2-010 contract/source/tests, R2-011 contract/source/tests,
Phase 5/6 source/tests, `main`.

## 23. Explicit statement

**Real-money automation is not created, granted, or implied anywhere in
this contract.** `MT5_LIVE_MANUAL` and `MT5_LIVE_AUTOMATED` remain fully
unavailable per `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`, unchanged by
this checkpoint's narrow amendment. Every automated order path in this
contract additionally requires, independently of `ModeService`, a
positively proven MT5 demo account (Section 2) on every single
`order_check`/`order_send` call.
