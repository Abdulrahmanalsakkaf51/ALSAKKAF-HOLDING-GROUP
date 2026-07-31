# TRL-R2-006 Governed Signal Intelligence Contract

> **RESEARCH SIGNAL — NOT A TRADE INSTRUCTION — CONFIDENCE IS NOT A PROFIT PROMISE**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-006 |
| Status | Implemented, Founder-corrected (durable storage, SMA-001 geometry removed, performance reporting added, honest confidence status), tested (569/569 twice), manually rehearsed; see `TRL_R2_006_SIGNAL_INTELLIGENCE_EVIDENCE.md`; not yet committed |
| Depends on | TRL-R2-005 (forward paper timeline, committed) |
| Feeds | TRL-R2-007 (MT5 execution adapter consumes only proposals that pass this pipeline) |

**Implementation note (2026-08-01, superseding the 2026-07-31 note below):**
FIB-001 remains exactly as specified below — present in the registry,
disabled, `APPROVAL_PENDING`, no numeric parameters implemented or
fabricated. The first Phase 4 implementation pass invented an SMA-001
entry-zone/stop/TP1-TP4 geometry (a swing-high/swing-low stop with equal
25% TP1-TP4 allocations at 1x/2x/3x/4x the stop distance) with no citable
Founder approval; a Founder correction pass removed it entirely from the
executable code path. **No SMA-001 execution geometry is approved in this
checkpoint.** SMA-001's crossing *direction* (the exact, unmodified
Release-1 kernel calculation) is still produced and recorded for research
traceability as `candidate_direction`, but every crossing fails closed at
Role 3 with `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`, and the final
proposal is `BLOCKED` — the pipeline cannot currently authorize an
executable BUY/SELL proposal for SMA-001, exactly like FIB-001. See
`TRL_BLOCKERS.md` and `TRL_R2_006_SIGNAL_INTELLIGENCE_EVIDENCE.md`.

## 1. Boundary

R2-006 adds governed signal generation on top of the R2-005 causal timeline and
paper engine. It produces `PAPER_PROPOSAL` events only. It does not call any
broker function, does not mutate any account, and does not gain any authority
R2-005 did not already have. A proposal produced here still carries
`paper_only_status: PAPER_ONLY_NO_BROKER_ORDER` until an execution adapter
(R2-007) independently re-validates it end to end. No proposal is ever treated
as pre-approved for execution because it was accepted by this pipeline.

Generative/LLM components may summarize, classify, explain, and propose
hypotheses. They may never construct, size, or directly emit an executable
proposal. Every field that determines size, stop, target, or eligibility must
pass through the deterministic validators in Section 6 regardless of what any
model suggested.

## 2. Pipeline roles

Six sequential partner roles process one instrument/timeframe evaluation. Each
role returns a typed result; a `BLOCKED` or failing result from any role
short-circuits the pipeline for that evaluation and the proposal (if any)
becomes `BLOCKED` with the originating role's reason code.

| Order | Role | Responsibility | Failure output |
|---|---|---|---|
| 1 | Data Quality Partner | Validates observation freshness, spread sanity, tick/bar completeness, instrument metadata presence | `DATA_QUALITY_REJECTED` |
| 2 | Market Regime Partner | Classifies TREND_UP / TREND_DOWN / RANGE / HIGH_VOLATILITY / UNKNOWN from governed features only | `REGIME_UNCLASSIFIABLE` |
| 3 | Technical Strategy Partner | Runs the selected strategy (SMA-001, FIB-001, ...) against governed evidence; emits BUY/SELL/HOLD candidate with entry/stop/targets | `NO_STRATEGY_SIGNAL` |
| 4 | News/Event Risk Partner | Checks governed news/economic-event evidence for the instrument within its lookback window; flags elevated-risk windows | `NEWS_EVENT_RISK_BLOCK` |
| 5 | Independent Risk Partner | Re-derives position size, applies account/risk-halt state, applies correlated-exposure and per-instrument limits, from a **separately implemented module that never imports or calls the strategy partner's sizing code** | `RISK_REJECTED` (with the same reason-code vocabulary R2-005 already uses, extended per Section 6.4) or `SIZE_MISMATCH_BETWEEN_PARTNERS` |
| 6 | Execution Eligibility Partner | Final deterministic gate: schema, evidence, instrument, spread, market-hours, expiry, account-state | `EXECUTION_INELIGIBLE` |

Every role's output is itself recorded as timeline evidence (new category
`SIGNAL_PIPELINE_STEP`, append-only, same hash-chain rules as R2-005) so a
`BLOCKED` outcome is fully auditable after the fact — not just logged to a
transient console.

**Role 5 independence, precisely defined** (added in the Phase 2 correction
pass): "independent" means role 5 is implemented in a separate module from
role 3's strategy partner, does not import, call, or otherwise share the
sizing function role 3 used to compute its candidate entry/stop/targets, and
independently recomputes position size from governed account state, the
active risk-policy hash, and the proposal's stop distance alone — it does not
read role 3's suggested size as an input to its own calculation. If role 5's
independently recomputed size disagrees with role 3's candidate size by more
than a documented rounding tolerance, that disagreement is itself a rejection
(`SIZE_MISMATCH_BETWEEN_PARTNERS`) rather than something silently reconciled
by trusting one number over the other. This turns role 5 into a genuine
second check rather than a second invocation of the same code path — a
defect in the shared sizing formula (if one ever existed) cannot pass both
roles silently, because role 5 does not depend on that formula at all.

## 3. Signal outputs

The pipeline produces exactly one of:

- `BUY` — executable proposal, passed all six roles
- `SELL` — executable proposal, passed all six roles
- `HOLD` — evaluated, no actionable setup; not an error
- `WAIT` — evidence exists but is not yet sufficient (matches R2-005's existing WAIT semantics)
- `BLOCKED` — a role rejected the candidate; reason code from Section 2's table is mandatory and visible in the dashboard, never silently dropped

`HOLD` and `WAIT` are distinct: `WAIT` means "a setup may be forming, watch
this evidence"; `HOLD` means "no setup, nothing to watch right now." Both
carry zero risk and no entry/stop/target fields, following the same WAIT
validation rule R2-005 already enforces in `validate_proposal`.

## 4. Proposal schema — `TRL_SIGNAL_PROPOSAL.v1`

Extends `TRL_PAPER_PROPOSAL.v1` (R2-005) with the following additional
required fields. All R2-005 invariants (stop/entry/TP ordering, allocation sum
= 100%, causal evidence IDs, no prohibited-claim strings) still apply
unchanged.

| Field | Type | Notes |
|---|---|---|
| `strategy_id` | string | e.g. `SMA-001`, `FIB-001` |
| `strategy_version` | string | semantic version of the strategy implementation, not the file's mtime |
| `broker_native_instrument` | string, nullable | exact broker symbol mapping; null until R2-007 resolves it; never guessed |
| `regime_classification` | enum | `TREND_UP` / `TREND_DOWN` / `RANGE` / `HIGH_VOLATILITY` / `UNKNOWN` |
| `feature_snapshot_hash` | string (sha256 hex) | hash of the exact governed feature vector used, for reproducibility |
| `data_quality_result` | object | `{status, reasons[]}` from role 1 |
| `news_event_risk_result` | object | `{status, reasons[], evidence_ids[]}` from role 4 |
| `confidence_score` | integer 0–100 | already present in R2-005; reaffirmed here as **calibrated model confidence, not a win probability** |
| `confidence_calibration_source` | string | e.g. `WALK_FORWARD_2024H2` — must reference a real stored calibration record, never a bare adjective |
| `explanation` | string, bounded | beginner-safe, no prohibited-claim strings (same filter as R2-005) |
| `rejection_reasons` | array of strings | populated only when `side == BLOCKED`; empty otherwise |
| `model_rule_versions` | object | `{strategy_version, risk_engine_version, pipeline_version}` |

`proposal_id` remains content-derived (sha256 of the canonical field set,
excluding the ID itself), matching R2-005's `proposal_id_for`.

## 5. Strategy registry

- `SMA-001` — the existing approved moving-average strategy, ported unchanged in behavior; only its I/O is adapted to this pipeline's typed interface.
- `FIB-001` — new strategy following a Fibonacci retracement/extension approach: entry zone from a governed retracement level, stop beyond the invalidation swing, TP1–TP4 from extension levels, exactly like R2-005's four-target model. **Its exact numeric parameters (which retracement/extension ratios, which swing-detection rule, which invalidation distance) are not fixed by this document and require explicit Founder sign-off, recorded as a dated `TRL_DECISION_LOG.md` entry, before implementation begins** — this contract corrects an earlier draft that referred to these parameters as "previously Founder-approved" without a citable record; no such record exists yet, so none is claimed.
- Registry format: `{strategy_id, version, module_path, enabled, description, parameters_schema}`, stored in a single governed JSON/py registry file, never hot-loaded from an untrusted path.
- Strategy comparison report: per-strategy walk-forward and out-of-sample metrics (Section 7) rendered side by side; adding a strategy to the registry never changes another strategy's recorded historical metrics.

## 6. Deterministic validation (must pass regardless of model/LLM output)

1. **Schema validation** — exact field set, types, bounded strings (reuse `paper_data.py` validators; extend, don't fork).
2. **Evidence validation** — market-data observation exists, is not stale (same `maximum_observation_age_seconds` bound as R2-005), occurs before the proposal per the existing causal rules.
3. **Strategy rules** — entry/stop/TP ordering and allocation-sum invariants (R2-005, unchanged).
4. **Risk calculations** — independently re-derived by role 5 from a separately implemented module (Section 2), not trusted from and not sharing code with the strategy partner; must match R2-005's formula (`equity × risk% ÷ stop-distance value`, floored to quantity step, rejected below minimum); a disagreement between role 5's recomputed size and role 3's candidate size beyond the documented rounding tolerance rejects with `SIZE_MISMATCH_BETWEEN_PARTNERS`.
5. **Instrument validation** — instrument exists in governed metadata; broker-native mapping (if present) matches an allowlisted symbol table, never inferred.
6. **Spread validation** — current spread ≤ proposal's `maximum_spread`.
7. **Market-hours validation** — instrument's governed trading-session table; a proposal cannot fill outside session hours (this is new: R2-005 tests fills against arbitrary UTC timestamps because it has no execution adapter yet — R2-006 introduces the session table and R2-007 enforces it against a real terminal).
8. **Proposal expiry validation** — reuses R2-005's expiry semantics.
9. **Account-state validation** — no active risk halt, one-open-position-per-instrument, no averaging down, no risk increase after a loss (all reused from R2-005 verbatim).

## 7. Walk-forward and out-of-sample reporting

- Every backtest/calibration run is tagged with exactly one of: `IN_SAMPLE`, `OUT_OF_SAMPLE`, `WALK_FORWARD`, `SYNTHETIC_PAPER`, `BROKER_DEMO`, `BROKER_LIVE`.
- A report never blends samples from different tags into a single headline number; each tag's metric is shown with its own sample size.
- Minimum sample-size floor before a metric is displayed at all (e.g. fewer than 20 closed trades renders `INSUFFICIENT_SAMPLE`, not a misleadingly precise percentage).
- Confidence-score calibration is validated against realized outcomes per tag; a calibration source string in a proposal must point to a report that actually exists in storage.

## 8. Failure modes

| Failure | Handling |
|---|---|
| Any role raises an unexpected exception | Proposal is `BLOCKED` with reason `PIPELINE_INTERNAL_ERROR`; exception detail is logged locally only, never returned in the API response (matches R2-005's no-exception-detail-disclosure pattern) |
| Strategy module missing/disabled in registry | `NO_STRATEGY_SIGNAL`, pipeline does not fall back to a different strategy silently |
| Feature snapshot hash cannot be computed (missing governed input) | `DATA_QUALITY_REJECTED` |
| Confidence calibration source does not resolve | Proposal is rejected at schema validation, not published with an unverifiable confidence number |

## 9. Acceptance tests (before this checkpoint is considered complete)

- Every pipeline role has unit tests for its pass and every documented block reason.
- SMA-001 parity test: identical signals to the pre-R2-006 SMA-001 behavior on the same fixture data.
- FIB-001 unit tests covering retracement/extension math and invalidation.
- End-to-end test: a `BLOCKED` proposal from role 4 (news/event) never reaches role 5 or 6, and its `PAPER_PROPOSAL` timeline event records the exact blocking role and reason.
- Adversarial test: LLM/generative component output is fed a manipulated "recommend maximum risk" string and the deterministic validators still cap risk at the governed maximum — proving Section 1's "LLM output may not directly become an order" boundary holds even under a hostile prompt.
- Walk-forward report test: mixing sample tags in one metric raises a validation error rather than silently averaging them.

## 10. Next checkpoint

R2-007 (MT5 Execution Adapter) is the only consumer authorized to move a
proposal from `PAPER_ONLY_NO_BROKER_ORDER` toward an actual broker action, and
only after its own independent preflight (terminal/account/symbol/risk/
execution) passes in full.
