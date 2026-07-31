# TRL-R2-005 Forward Paper Timeline Contract

> **PAPER ONLY — LOCAL RESEARCH — NO BROKER ORDER — NO LIVE EXECUTION — NO FINANCIAL ADVICE**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-005 |
| Status | Implementation contract for independent uncommitted review |
| Application version | 2.0.0-r2.005 |
| Runtime | Python standard library, local host only |
| Next checkpoint | R2-006 beginner XAUUSD Signal Desk |

## 1. Boundary

TRL-R2-005 provides a causal market-information timeline and a forward paper-account projection. It does not generate a BUY, SELL, or WAIT proposal. The proposal schema exists solely as the production contract for R2-006. No HTTP write route, broker order, MT5 trade call, credential collector, account mutation, remote service, telemetry, paid provider, profitability promise, accuracy promise, or financial-advice claim exists.

The paper engine is available but disabled by default. Disabled mode constructs no paper store and performs no network or filesystem operation. Enabling the paper engine creates only a local research projection. Its synthetic starting cash is never presented as a brokerage balance.

## 2. Stable schemas

| Document | Schema identifier |
|---|---|
| Timeline | `TRL_MARKET_TIMELINE.v1` |
| Timeline event | `TRL_TIMELINE_EVENT.v1` |
| Storage envelope | `TRL_FORWARD_PAPER_STORE.v1` |
| Proposal | `TRL_PAPER_PROPOSAL.v1` |
| Market observation | `TRL_PAPER_MARKET_OBSERVATION.v1` |
| Instrument metadata | `TRL_PAPER_INSTRUMENT_METADATA.v1` |
| Account | `TRL_PAPER_ACCOUNT.v1` |
| Position | `TRL_PAPER_POSITION.v1` |
| Positions response | `TRL_PAPER_POSITIONS.v1` |
| History response | `TRL_PAPER_HISTORY.v1` |
| Health response | `TRL_PAPER_HEALTH.v1` |
| Timeline API response | `TRL_MARKET_TIMELINE_API.v1` |

Decimal values are stored and returned as canonical decimal strings. Python `Decimal` is used for calculations. Booleans and binary floating-point values are rejected as exact numbers; NaN and infinity are forbidden. Quantities are rounded down to the governed instrument quantity step. No ungoverned rounding or hidden estimate is permitted.

## 3. Causal timeline

The governed categories are:

- `MARKET_OBSERVATION`
- `OFFICIAL_NEWS_OBSERVATION`
- `ECONOMIC_EVENT_OBSERVATION`
- `PAPER_PROPOSAL`
- `PAPER_ENTRY`
- `PAPER_MARK`
- `PAPER_TP`
- `PAPER_STOP`
- `PAPER_EXIT`
- `PAPER_RISK_REJECTION`
- `PAPER_SESSION_EVENT`

Every event contains its schema, stable event ID, category, nullable instrument, occurrence UTC, first-observed UTC, contiguous append sequence, governed source/basis, bounded sanitized payload, payload SHA-256, previous-event hash, and current-event hash.

Timestamps use strict RFC3339 UTC in `YYYY-MM-DDTHH:MM:SS.ffffffZ` form. Local-time inference and offsets are rejected. An occurrence cannot follow its first observation, and a new first-observation time cannot precede the previous appended observation. Stable event identities exclude unrelated retrieval/process timing supplied outside these causal fields. Canonical UTF-8 JSON with sorted keys and no NaN supplies all hashes and identities.

The loader validates the schema, exact field sets, event count, contiguous sequence, unique stable IDs, payload hashes, previous hashes, current hashes, tail hash, observation ordering, and byte/count bounds. Corruption, truncation, reordering, duplicate identity, or mismatch fails closed. Records are never updated or replaced.

## 4. Proposal contract

The contract supports `BUY`, `SELL`, and `WAIT`, an expiry, an entry zone, one fixed stop, TP1 through TP4, four exact allocations totaling 100 percent, a 0–100 research confidence score, governed evidence status, invalidation and beginner explanations, strategy/research basis IDs, market evidence, optional governed news/event evidence, governed paper risk, and the permanent status `PAPER_ONLY_NO_BROKER_ORDER`.

For BUY:

`stop < entry-zone lower <= entry-zone upper < TP1 < TP2 < TP3 < TP4`

For SELL:

`TP4 < TP3 < TP2 < TP1 < entry-zone lower <= entry-zone upper < stop`

WAIT requires an explicit reason, zero risk, and no entry, stop, size, target, or allocation. Confidence is a research score, not a probability or profit guarantee. Prohibited claims such as guaranteed profit and “99% accurate” fail validation.

Executable paper proposals require an existing governed market observation for the same instrument. Missing, stale, invalid, or future evidence fails closed. Optional news and economic-event IDs must resolve to the correct governed categories and must already have been observed.

## 5. Forward fills and no look-ahead

A proposal can fill only from a market event whose append sequence follows the proposal event. The market observation used as proposal evidence can never fill it. A later observation must reach the entry zone before expiry. Each proposal fills at most once, and position/fill identities derive deterministically from the proposal, forward observation, and modeled entry.

BUY entry tests and fills use the ask side. SELL entry tests and fills use the bid side. Spread, side, slippage price, slippage amount, fee, metadata identity, and observation identity are explicit. A quote uses its observed side price. A bar that intersects the zone uses the conservative edge: the BUY upper bound or SELL lower bound. No unavailable tick path is interpolated.

Missing timestamp, spread, tick size, tick value, contract size, quantity step, or quantity bounds rejects the observation or fill. An observation or metadata age beyond the configured bound cannot fill or mark a position.

## 6. Stop and TP1–TP4 accounting

The initial stop remains fixed. R2-005 does not move it to breakeven or trail it. Default target allocation is 25 percent each, while any four exact positive allocations totaling 100 percent are permitted.

Targets close the governed allocation of initial quantity, rounded down to the quantity step. TP4 closes any rounding remainder. Each exit records quantity, modeled price, side, gross P&L, exit fee, allocated entry fee, net P&L, and slippage. Long P&L uses `(exit - entry)`; short P&L uses `(entry - exit)`, multiplied by quantity and governed tick value per price unit.

If a bar touches both the fixed stop and any pending target and intrabar order is unavailable, the whole remaining quantity exits at the modeled stop first. The event records `CONSERVATIVE_STOP_FIRST_UNKNOWN_INTRABAR_ORDER`. The engine never selects the profitable path or silently invents tick order.

## 7. Account and risk projection

The account projects starting cash, cash, marked equity, realized and unrealized P&L, closed-trade P&L, fees, modeled slippage, peak equity, drawdown, daily paper P&L, open fixed-stop risk, open positions, completed trades, session start, last observation, and sticky risk-halt state. Projection identity derives from the validated tail hash and governed configuration.

Hard defaults are:

- Default proposal risk: 0.5 percent of marked paper equity.
- Maximum proposal risk: 1.0 percent.
- Maximum daily paper loss: 2.0 percent.
- Maximum paper-account drawdown: 5.0 percent.
- One open position per instrument.
- No martingale, averaging down, or risk increase after a loss.
- No position without a fixed stop.
- No sizing without governed contract and tick-value metadata.
- No stale or missing fill price.

Risk size is `marked equity × risk percent ÷ stop-distance value`, rounded down to quantity step and bounded by governed minimum/maximum quantity. A size below minimum is rejected rather than estimated. Daily-loss or drawdown breach appends a sticky `RISK_HALT` session event. These are research controls, not a promise of safety.

## 8. Storage and recovery

Enabled production storage defaults to `%LOCALAPPDATA%\ALSAKKAF\TradingLab\forward-paper-timeline-v1.json`. It is bounded and strictly validated. Writes use a uniquely named temporary file in the target directory, flush and synchronize it, then atomically replace the document. Only the exact created temporary path is eligible for cleanup.

Startup rebuilds account and position projections solely from the validated event chain. Invalid storage produces the controlled diagnostic `INVALID_PAPER_STORAGE`; it is not replaced with an empty timeline. The last trusted snapshot remains retained by the store object. A write failure leaves the valid in-memory timeline available and independently reports `WRITE_FAILED_IN_MEMORY_VALID`. Shutdown is idempotent.

## 9. Read-only local APIs

The server remains literally bound to `127.0.0.1`. These fixed GET/HEAD surfaces are available:

- `/api/paper-account`
- `/api/paper-positions`
- `/api/paper-history`
- `/api/market-timeline`
- `/api/paper-health`

Responses use deterministic bounded JSON. Disabled responses are explicit and storage-silent. No POST, PUT, PATCH, DELETE, reset, delete, file, URL, MT5-write, or arbitrary input route exists. Existing host-header, traversal, static allowlist, timeout, worker-bound, security-header, and shutdown protections remain in force.

`/api/version`, `/api/capabilities`, and `/api/health` identify TRL-R2-005 accurately. Forward paper capability is true; default enablement, signal generation, trade recommendation, broker execution, real orders, account mutation, and automated trading are false.

## 10. Beginner dashboard

The Paper desk shows paper balance, paper equity, daily paper P&L, drawdown, open risk, active positions, completed trades, timeline activity, and risk halt. It carries a visible `PAPER ONLY` badge and states that values are not a brokerage account, live balance, recommendation, or order.

Disabled or empty state reads: “No active paper proposal yet. Market research proposals will appear here when the Signal Desk is enabled.” It does not show BUY/SELL proposals in R2-005. Schema, projection, tail hash, persistence, and last-observation fields are behind an expandable expert section.

## 11. Synthetic demonstration

`trading_lab_app/synthetic_paper_demonstration.json` is labeled `SYNTHETIC DEMONSTRATION — NOT LIVE MARKET DATA`. It contains no publisher body, user account, credential, or external URL. The offline runner demonstrates:

- one WAIT proposal;
- valid BUY and SELL entry-zone proposals;
- later forward fills;
- BUY TP1 and TP2 partial exits;
- a BUY bar that touches stop and TP3 and resolves stop-first;
- a SELL trade completed through TP1, TP2, TP3, and TP4;
- a one-position-per-instrument risk rejection; and
- exact account, position, history, and timeline reconstruction after restart.

The fixture is never loaded by disabled/default application startup and is never labeled live.

## 12. Known limitations

- R2-005 does not generate proposals, interpret news, rank evidence, or select a strategy.
- Bar simulation cannot know unavailable intrabar tick order; its explicit stop-first policy is intentionally conservative.
- Fees and slippage are governed research models, not broker quotations.
- Instrument metadata must be supplied by a governed local source; the engine does not infer missing values.
- The local hash chain detects internal corruption and envelope truncation but is not a remote notarization service.
- There is no live brokerage balance, broker position reconciliation, order management, multi-user account, cloud backup, or execution path.

## 13. Next checkpoint

The exact next checkpoint is **R2-006 beginner XAUUSD Signal Desk**. It may create governed BUY/SELL/WAIT research proposals using this contract. It must preserve the paper-only boundary, causal evidence IDs, no-look-ahead policy, and all false broker/execution capability flags.
