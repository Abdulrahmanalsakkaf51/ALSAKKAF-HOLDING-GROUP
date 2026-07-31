# TRL-R2-006 Signal Intelligence — Implementation and Evidence

> **RESEARCH SIGNAL — NOT A TRADE INSTRUCTION — CONFIDENCE IS NOT A PROFIT PROMISE — NO BROKER EXECUTION**

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-006-SIGNAL-INTELLIGENCE-EVIDENCE-001 |
| Document Type | Implementation and Evidence Record |
| Status | Implemented, Founder-corrected, tested, and manually rehearsed; awaiting Founder review and commit approval |
| Version | 2.0 (supersedes v1.0's now-corrected in-memory-persistence and SMA-001-geometry claims) |
| Date | 2026-08-01 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Depends on | TRL-R2-005 (paper engine/timeline, unchanged), Phase 3 (ModeService, unchanged in its transition logic) |
| Feeds | TRL-R2-007 (MT5 execution adapter; not started) |

## 0. Founder correction pass (2026-08-01)

The first Phase 4 implementation (v1.0 of this document) passed its own tests but Founder review
found four contract-level gaps, all now corrected:

1. **Durable persistence.** The originally wired signal service was in-memory only in both
   available modes; proposal/audit history was lost on every restart. Corrected: mode-transition
   *preflight* (side-effect-free, used only to check a transition would succeed) is now cleanly
   separated from *runtime* construction (durable, used only after a mode is actually resolved) —
   see Section 10.
2. **Invented SMA-001 execution geometry.** The first pass invented a 20-bar swing-stop,
   1x/2x/3x/4x-target, 25%-allocation geometry with no citable Founder approval. Corrected:
   removed entirely from the executable path — see Section 5.
3. **Missing performance/walk-forward reporting.** Not started in the first pass. Corrected:
   `signal_reporting.py` — see Section 9.
4. **Confidence honesty.** The first pass's confidence score was numerically presented without an
   explicit machine-readable "this is not calibrated" signal. Corrected: `confidence_status` is
   now a required, closed-vocabulary schema field — see Section 8.

## 1. Boundary restated

This checkpoint implements the governed six-role signal-intelligence pipeline defined by
`TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md`. It produces `PAPER_PROPOSAL` timeline events
only. It never calls `order_check`, `order_send`, or any broker/MT5 function, never imports the
real `MetaTrader5` module, and never mutates the R2-005 paper account. Every proposal carries
`paper_only_status == PAPER_ONLY_NO_BROKER_ORDER` regardless of operating mode.

## 2. Six-role pipeline architecture

Implemented as one pure orchestrator, `trading_lab_app/signal_pipeline.py`, calling six
independently testable role modules in strict order:

| Order | Role | Module | Failure code |
|---|---|---|---|
| 1 | Data Quality Partner | `signal_role1_data_quality.py` | `DATA_QUALITY_REJECTED` |
| 2 | Market Regime Partner | `signal_role2_market_regime.py` | `REGIME_UNCLASSIFIABLE` |
| 3 | Technical Strategy Partner | `signal_role3_strategy.py` | `NO_STRATEGY_SIGNAL` |
| 4 | News/Event Risk Partner | `signal_role4_news_risk.py` | `NEWS_EVENT_RISK_BLOCK` |
| 5 | Independent Risk Partner | `signal_role5_independent_risk.py` | `RISK_REJECTED` / `SIZE_MISMATCH_BETWEEN_PARTNERS` |
| 6 | Execution Eligibility Partner | `signal_role6_execution_eligibility.py` | `EXECUTION_INELIGIBLE` |

A `BLOCKED`/failing result from any role short-circuits the pipeline by early return — later
roles literally never execute (verified: `BlockedShortCircuitTests` and the dedicated
`SMAGeometryBlockTests::test_role5_and_role6_do_not_execute_after_geometry_block`). Roles 4-6
still execute for a HOLD/WAIT candidate (nothing to block, but still audited) and Roles 1/6 also
run their unconditional checks (evidence integrity, risk-halt, instrument-allowlist) regardless of
candidate side. An unexpected exception anywhere in the six roles is caught by the orchestrator
and converted into a `BLOCKED`/`PIPELINE_INTERNAL_ERROR` proposal rather than propagating.

Each role is a **pure function** (no timeline/storage/network access); the orchestrator records
every role's result and the single authoritative service (`signal_service.py`) appends one
append-only `SIGNAL_PIPELINE_STEP` timeline event per role result, then one `PAPER_PROPOSAL`
event for the final outcome — reusing `timeline_data.MarketTimeline`'s existing hash-chain,
exactly as R2-005's paper engine does. `SIGNAL_PIPELINE_STEP` is a new governed timeline event
category (`timeline_data.EVENT_CATEGORIES` now has 12 entries, up from 11). `generate_proposal`
is idempotent by content: re-submitting an identical governed evaluation against the same
timeline returns the already-recorded proposal unchanged rather than attempting (and failing) to
append duplicate events — proposal_id is derived purely from governed evidence/configuration, so
this is provably deterministic, not a cache.

## 3. Governed proposal schema — `TRL_SIGNAL_PROPOSAL.v1`

`signal_data.py` implements the schema. It extends R2-005's `TRL_PAPER_PROPOSAL.v1`
(`paper_data.py`) rather than forking it: for an executable BUY/SELL proposal, the R2-005 field
subset is validated by calling `paper_data.validate_proposal` itself (reusing its
ordering/allocation-sum/causal-timestamp/prohibited-claim invariants unchanged); R2-006 extends
the `side` vocabulary to five values (`BUY`/`SELL`/`HOLD`/`WAIT`/`BLOCKED`, versus R2-005's three),
so the WAIT-shaped branch (HOLD/WAIT/BLOCKED — zero risk, no entry/stop/targets) is validated
directly in `signal_data.py`. The 45-field schema adds `strategy_id`, `strategy_version`,
`broker_native_instrument`, `regime_classification`, `feature_snapshot_hash`,
`data_quality_result`, `news_event_risk_result`, `confidence_calibration_source`,
`confidence_status`, `explanation`, `rejection_reasons`, `model_rule_versions`, `role_results`
(one typed sub-object per role, including Role 3's `candidate_direction` — see Section 5),
`candidate_quantity`, `independent_quantity`, `maximum_spread`, `active_risk_policy_hash`,
`operating_mode`, `sample_label`, and `canonical_proposal_hash` on top of the R2-005 base fields.
`sample_label` now has seven governed values — `IN_SAMPLE`, `VALIDATION`, `OUT_OF_SAMPLE`,
`WALK_FORWARD`, `SYNTHETIC_PAPER`, `BROKER_DEMO`, `BROKER_LIVE` — `VALIDATION` was added during
the Founder correction pass alongside the R2-006 contract's original six, because the governing
prompt's performance-reporting requirement separates IN_SAMPLE/VALIDATION/OUT_OF_SAMPLE as three
distinct labels.

`proposal_id` remains content-derived (`sp_` + 32 hex chars of a sha256 digest over the canonical
field set excluding the ID itself); `canonical_proposal_hash` is the full 64-hex digest. Identical
governed evidence/configuration reproducibly yields the identical proposal ID (verified:
`SMA001ParityTests::test_repeated_identical_evidence_produces_identical_proposal_id`, and via the
real durable-store restart/CLI rehearsal in Section 15).

## 4. Strategy registry

`signal_strategy_registry.py` is a new, distinct registry from the Release-1 kernel's
`strategy_registry.py` (vault-digest based, used by the R1 backtest demo only). It is a literal,
reviewed-in-source tuple of two records — never hot-loaded from an untrusted path:

- **SMA-001** — `enabled: true`, `implementation_status: IMPLEMENTED`,
  `approval_status: EXPERIMENTAL_RESEARCH_ONLY`.
- **FIB-001** — `enabled: false`, `implementation_status: PLANNED_NOT_IMPLEMENTED`,
  `approval_status: APPROVAL_PENDING`, `module_path: null`, `parameter_schema: {}`.

`executable_status(strategy_id)` checks `approval_status == APPROVAL_PENDING` **before** the
generic enabled/implemented gate, so FIB-001 always surfaces the precise
`STRATEGY_PARAMETERS_NOT_APPROVED` reason rather than the generic `STRATEGY_DISABLED`.

## 5. SMA-001 — crossing parity is exact; execution geometry is not approved

Role 3 (`signal_role3_strategy.py`) imports and calls `trading_lab_core.strategy.sma` and
`sma_cross_signals` **directly, unmodified** — the identical functions the Release-1 kernel's
`execution.run_backtest` uses. The crossing-detection logic (independent stable fast/slow
windows, transition-only enter/exit signals, close-at-time-t, no look-ahead) is therefore
byte-for-byte the ported R1 behavior. `SMA001ParityTests` proves this directly by calling
`sma_cross_signals` on fixture bar series and asserting the pipeline's outcome matches the
kernel's enter/exit/none classification for every one of them.

**Founder correction (2026-08-01): no SMA-001 execution geometry is approved.** A repository-wide
search of `TRL_DECISION_LOG.md`, `TRL_BLOCKERS.md`, and every R2-006 document found no dated,
citable Founder approval covering a geometry lookback window, entry-zone rule, stop rule,
TP1-TP4 formula, target allocations, or rounding/tolerance behavior for SMA-001 — the exact same
absence of approval that already blocks FIB-001. The first implementation pass had invented one
(a 20-bar swing-high/swing-low stop, TP1-TP4 at 1x/2x/3x/4x the stop distance, equal 25%
allocations) and presented it as an "I/O adaptation"; that framing did not change the fact that no
Founder ever approved those specific numbers. It has been **removed entirely** from
`signal_role3_strategy.py`: the functions that computed it (`_trade_geometry`,
`_candidate_quantity`, the `_GEOMETRY_LOOKBACK`/`TARGET_MULTIPLES`/`EQUAL_ALLOCATIONS` constants)
no longer exist in the file (verified:
`SMAGeometryBlockTests::test_no_hidden_geometry_defaults_remain_in_executable_code`, a source
scan for exactly those names).

Current behavior: every detected crossing is recorded as a non-executable research
`candidate_direction` (`"BUY"` or `"SELL"`) on Role 3's typed result, and Role 3 itself fails
closed with `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` (a new reason code, exported as
`signal_role3_strategy.REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`). The pipeline's existing
short-circuit rule then makes the final proposal `BLOCKED` with `rejection_reasons ==
["NO_STRATEGY_SIGNAL"]` and Roles 5/6 never run — SMA-001 is therefore, today, in the same
position as FIB-001: research-eligible for its *signal*, blocked for *execution*, pending a dated
Founder decision recorded in `TRL_DECISION_LOG.md` and a new blocker row now present in
`TRL_BLOCKERS.md`. HOLD (no crossing) and WAIT (insufficient bar history) are unaffected by this
correction — neither ever needed execution geometry.

Fully covered by the dedicated `SMAGeometryBlockTests` test class: positive/negative crossing
direction recorded, no-approval-means-blocked, the exact reason code present in the serialized
proposal, every entry/stop/target/allocation/quantity field null on both the top-level proposal
and Role 3's own result, Roles 5/6 not executed, no hidden geometry constant remains in source,
and future approval can only come from the governed registry plus a dated Decision Log entry (not
a runtime flag or request field).

## 6. FIB-001 — approval blocker preserved

No FIB-001 numeric parameter (retracement ratio, extension ratio, swing-detection rule,
invalidation distance) is implemented or fabricated. `signal_strategy_registry.py`'s FIB-001
record has `module_path: null` and `parameter_schema: {}`. Requesting FIB-001 fails closed with
`STRATEGY_PARAMETERS_NOT_APPROVED` (the contract-specified fallback code, since no more specific
contract-defined code exists). `TRL_BLOCKERS.md`'s existing FIB-001 row is unchanged and remains
active, alongside the new SMA-001 execution-geometry blocker row added in this correction pass. No
Decision Log entry approves FIB-001 or SMA-001 execution-geometry numeric values.

## 7. Role 5 structural independence

`signal_role5_independent_risk.py` is a separate module from `signal_role3_strategy.py`:

- It does not import `signal_role3_strategy` (verified by parsing its actual `import`/`from`
  statement lines specifically, not just absence of the substring anywhere in the file, since the
  module's own docstring legitimately *names* Role 3 in prose explaining the independence
  requirement).
- It does not receive Role 3's candidate quantity as an input to its own sizing calculation —
  only the candidate's entry/stop *prices* (needed to know what trade is being sized) and
  governed account state/risk policy are consumed; the quantity is computed by
  `_independent_quantity()`, a separately implemented evaluation of the same governed formula
  (`equity × risk% ÷ stop-distance value`, floored to quantity step).
- The only code shared with Role 3 is `paper_data.quantity_floor`, a bare floor-to-step numeric
  utility containing no sizing formula or strategy logic — explicitly documented as the
  contract-permitted shared low-level utility.
- A disagreement beyond the documented rounding tolerance
  (`risk_policy.quantity_step_tolerance_percent`, floored at one quantity step) rejects with
  `SIZE_MISMATCH_BETWEEN_PARTNERS` rather than silently reconciling.

Because no SMA-001 execution geometry is approved (Section 5), the full pipeline currently never
reaches Role 5 with an executable candidate. `Role5IndependenceTests` and
`SpreadSessionAccountTests` therefore exercise Role 5 (and Role 6) **directly**, via the
`executable_role456_request()` test helper, with a clearly hypothetical BUY/SELL candidate — this
proves each role's own safety mechanism is correct and ready for the moment execution geometry is
eventually approved, without claiming the full pipeline can reach that state today. No test
represents this hypothetical fixture as approved SMA-001 behavior.

## 8. Generative/LLM component boundary and confidence honesty

`signal_llm_adapter.py` defines a strict `GenerativeAdapter` interface. The only adapter wired
into the pipeline is `NoOpGenerativeAdapter` — deterministic, `enabled = False`, no network
call, no credential. Its only output is a bounded, sanitized `model_annotation` string, which is
**not a field of `TRL_SIGNAL_PROPOSAL.v1`** — the governed proposal schema has no slot a model can
write to, so no numeric, eligibility, or outcome field can ever be model-controlled by
construction, not merely by convention. `annotate_safely()` fails closed to an inert result for
any adapter exception or malformed return value. Verified: `GenerativeAdapterBoundaryTests` feeds
a hostile adapter that returns forged `entry_zone_lower`/`risk_percent`/`side` overrides and
confirms none of them reach the proposal, that a BLOCKED scenario stays BLOCKED under the same
hostile adapter, and that a 2000-character ANSI-escape/prompt-injection string is bounded and
sanitized before it could ever be persisted or displayed.

**Confidence honesty correction (2026-08-01).** `signal_confidence.py`'s
`compute_confidence()` now returns an explicit, machine-readable `confidence_status` alongside the
0-100 heuristic score — currently always `UNCALIBRATED_HEURISTIC`, the only value in
`CONFIDENCE_STATUSES`, because no realized-outcome calibration study exists yet. This is a
required, closed-vocabulary field on every proposal (`signal_data.py` rejects any proposal whose
`confidence_status` does not match the resolved `confidence_calibration_source`'s governed status,
and rejects any `confidence_calibration_source` that does not resolve to a real registered record
at schema validation — Section 8 of the contract). Every generated proposal's `explanation` field
also carries `signal_confidence.CONFIDENCE_DISCLAIMER` in full: "this confidence score is an
uncalibrated heuristic research value only... not a win probability, not a profit forecast, and
has no effect on position size or risk." Confidence never appears in `signal_role3_strategy.py` or
`signal_role5_independent_risk.py`'s sizing code (verified by source-scanning both files) and
cannot override `BLOCKED` (verified: `test_confidence_cannot_override_blocked`).

## 9. Performance and walk-forward reporting

New module: `signal_reporting.py`, implementing `TRL_SIGNAL_PERFORMANCE_REPORT.v1` — added during
the Founder correction pass; not present in the first implementation. Research reporting only: it
never calls `order_check`/`order_send`, never connects to MT5, never claims live performance, does
not approve SMA-001 execution geometry, and does not resolve FIB-001.

- **One sample label per report.** `build_report()` requires every included proposal to share the
  report's declared `sample_label` and `strategy_id`; mixing labels or strategies raises
  `ReportValidationError` (verified: `test_no_cross_sample_blending`,
  `test_strategy_comparison_rejects_incompatible_sample_definitions`). `IN_SAMPLE`, `VALIDATION`,
  and `OUT_OF_SAMPLE` are three separate governed labels (see Section 3).
- **Walk-forward segments.** `WALK_FORWARD` reports carry a `walk_forward_segments` list, each
  with its own boundaries, proposal count, and outcome counts; segments must be chronologically
  ordered and non-overlapping (verified: `test_deterministic_walk_forward_segment_ordering`,
  `test_segment_boundaries_validated`).
- **Minimum sample floor.** `MINIMUM_COMPLETED_TRADES = 20` (matching the contract's own example
  threshold). Because no SMA-001 execution geometry is approved, `completed_trade_count`,
  `open_position_count`, and `incomplete_trade_count` are always exactly zero, honestly — never
  fabricated from direction-only proposals — so **every report in this checkpoint is
  `sample_status == INSUFFICIENT_SAMPLE`**, and the document never implies zero loss, perfect
  accuracy, proven profitability, or completed validation (verified:
  `test_insufficient_sample_visibly_fails_closed`).
- **Outcome counts** (`proposal_count`/`buy_count`/`sell_count`/`hold_count`/`wait_count`/
  `blocked_count`) are always present and must sum to `proposal_count`; BUY/SELL crossings are
  recorded as `blocked_count` at the report level (execution not approved), with the underlying
  research direction visible per-proposal via `role_results.technical_strategy.candidate_direction`.
- **Fees/slippage/spread assumptions** are always present, sourced from `paper_data.
  PaperConfiguration`'s governed defaults (fee/slippage) and each proposal's own governed
  `maximum_spread` field, explicitly labeled as research assumptions never charged/applied to a
  real fill.
- **Deterministic JSON and Markdown export**, generated from the *same* validated document
  (`report_markdown()` calls `validate_report()` first and introduces no fact not already in the
  JSON) — `canonical_report_hash`/`report_id` are content-derived exactly like proposal IDs.
- **CLI**: `performance-report`, `export-performance-report`, `walk-forward-report` (all pull from
  the durable proposal history), plus `compare-strategies` extended with explicit
  `has_approved_execution_geometry: false` / `has_completed_trade_performance: false` fields for
  both registered strategies.
- **No HTTP reporting routes were added.** The existing loopback dispatcher only supports fixed
  paths (no query-string routing), and a useful report route needs `strategy_id`/`sample_label`
  parameters; rather than force those into an awkward fixed-path encoding, this checkpoint keeps
  reporting CLI-only, consistent with the governing prompt's "may be added" (not "must be added")
  phrasing for HTTP reporting routes. All existing HTTP routes remain GET/HEAD-only regardless.

Fully covered by `PerformanceReportingTests` (30 tests: schema strictness, sample-label
separation, walk-forward ordering/boundaries, every outcome-count case, the minimum-sample floor,
fee/slippage/spread assumption presence, JSON/Markdown determinism and fact-parity, no
live-performance/guaranteed-profit wording, FIB-001/SMA-001 blocker visibility, confidence status,
and the no-network/no-MT5/no-order-call source scan).

## 10. Operating-mode integration and durable persistence

Mode gating uses the **existing** `ModeService` (`mode_service.py`) as the sole authority; no
parallel mode check exists anywhere in the signal-intelligence code. One new governed capability,
`signal_proposal_generation`, was added to `CAPABILITIES`/`_CAPABILITY_MATRIX` (denied by default,
granted only to `RESEARCH` and `SYNTHETIC_PAPER`).

**Founder correction (2026-08-01): preflight/runtime construction separated, both modes now
durable.** `app.py` now has two distinct signal-service builder functions instead of one:

- `_signal_service_preflight_for_mode(current_mode)` — side-effect-free (always
  `InMemorySignalStore`), used **only** as (part of) `ModeService`'s `subsystem_builder` via
  `_subsystem_builder_for_mode`, which is exercised on every transition attempt (including from
  automated tests) purely to check construction *would* succeed. The constructed object is
  discarded immediately; it never touches the filesystem regardless of mode (verified:
  `test_mode_transition_preflight_does_not_create_production_store`).
- `_signal_service_for_mode(current_mode)` — the real runtime builder, called only *after* a mode
  has actually been resolved (at application startup in `main()`, and by `signal_cli.py`). Both
  `RESEARCH` and `SYNTHETIC_PAPER` now construct a real `SignalIntelligenceService` using its own
  bare-construction default, `LocalSignalStore` (durable, atomic, matching
  `ForwardPaperService`'s own convention) — the earlier draft that kept `SYNTHETIC_PAPER`
  in-memory-only was rejected; synthetic evaluations are still real governed evidence worth
  auditing. Both modes share the **one** durable store file
  (`%LOCALAPPDATA%\ALSAKKAF\TradingLab\signal-intelligence-timeline-v1.json`); every persisted
  proposal still carries its own `operating_mode` and `sample_label` fields, so RESEARCH and
  SYNTHETIC_PAPER records sharing that one append-only timeline can never become indistinguishable
  (verified: `test_synthetic_paper_records_remain_labelled_synthetic_after_restart`,
  `test_both_available_modes_use_durable_runtime_construction`).

`SignalIntelligenceService.__init__` independently refuses to construct for any mode outside
`{RESEARCH, SYNTHETIC_PAPER}` (defense in depth against a future direct-construction mistake,
verified: `test_direct_helper_calls_cannot_bypass_mode_service`).

## 11. Persistence and audit design

`signal_store.py` mirrors `paper_store.py`: `TRL_SIGNAL_INTELLIGENCE_STORE.v1`, atomic
temp-file-plus-`os.replace` writes, strict UTF-8 JSON with no NaN/Infinity, corruption fails
closed with the stable reason `SIGNAL_STORE_INTEGRITY_FAILURE` (no R2-006 contract-defined code
covers local-storage corruption, matching `paper_service.py`'s own precedent of defining its own
implementation-layer codes), `InMemorySignalStore` for every automated test, `LocalSignalStore`
for durable real use. Corruption never silently replaces the store with an empty one, never drops
history, never generates a new proposal, and never relabels/repairs an unverifiable hash — the
service simply becomes non-operational (`generate_proposal` raises `SignalEngineError`) until an
operator explicitly corrects the file.

`SignalIntelligenceService` owns its own `timeline_data.MarketTimeline` instance (independent of
the R2-005 paper engine's timeline), so RESEARCH-mode signal evaluation works even when the paper
engine itself is `DisabledPaperService` (no forward-paper fills exist in RESEARCH mode).

`DurablePersistenceTests` (18 tests, all using an isolated `tempfile.TemporaryDirectory()` —
**never the real `%LOCALAPPDATA%`**) verify: a proposal and its audit events survive a real service
restart (fresh `SignalIntelligenceService`/`LocalSignalStore` objects against the same file, not
the same in-memory object); two sequential proposals stay append-only and ordered across a
restart; an identical-evidence retry after restart returns the identical `proposal_id`; a torn/
truncated file fails closed rather than silently loading; malformed JSON, an unsupported schema
version, a broken event `append_sequence`, a broken `previous_event_hash`, and tampered proposal
content inside an otherwise-well-formed document each independently fail closed with
`SignalStorageValidationError`; mode-transition preflight never creates the production store; and
a real, separate `mode_cli.py`/`signal_cli.py` subprocess pair — sharing one isolated
`LOCALAPPDATA` override, never the real one — proves `generate-proposal` in one process is visible
to `proposal-history` in a completely separate later process.

## 12. CLI

`trading_lab_app/signal_cli.py` (`python -m trading_lab_app.signal_cli <command>`):
`signal-status`, `list-strategies`, `explain-strategy <id>`, `evaluate-strategy <id> <request.json>`
(role-results-only output), `generate-proposal <id> <request.json>` (full proposal),
`validate-proposal <proposal.json>`, `proposal-history`, `export-proposal <proposal.json>`,
`performance-report <id> <sample_label>`, `export-performance-report <id> <sample_label>`,
`walk-forward-report <id> <segments.json>`, `compare-strategies`. Every mutating command builds
its service through the same `app.py._signal_service_for_mode` mode-gated durable-construction
path `mode_cli.py`'s own request-mode command effectively validates via the combined preflight
builder, so a CLI-driven evaluation is denied exactly when the persisted mode denies it, and a
proposal generated by one CLI invocation is visible to a later, separate `proposal-history`
invocation (Section 11).

## 13. Dashboard and read-only HTTP API

Read-only GET/HEAD-only routes: `/api/signal-status`, `/api/signal-strategy-registry`,
`/api/signal-proposals`, `/api/signal-timeline` (wired in `server.py`'s `SIGNAL_API_ROUTES`,
covered by the existing generic 405 `Allow: GET, HEAD` handling — verified with a live POST/PUT/
PATCH/DELETE against a real running server in `HTTPSurfaceTests`). No route generates, approves,
modifies, or executes a proposal or report; no HTTP reporting route exists (Section 9).

The dashboard's "Signal intelligence" section (`static/index.html` `#signal-intelligence`,
rendered by `renderSignalIntelligence()` in `static/app.js`) shows: current operating mode, signal
capability availability, the strategy registry (including the FIB-001 approval-pending notice),
the latest proposal's outcome/entry/stop/targets/quantities/confidence (with the explicit
`confidence_status`)/sample label/BLOCKED reason, and a per-role status/reasons table — using
`textContent` only, no `innerHTML`, matching the existing dashboard's XSS-safety convention. A
`NO BROKER EXECUTION` banner is present in the section.

## 14. Test evidence

`test_signal_intelligence.py`, 122 tests, covering: all six roles' pass/fail paths, exact role
order, BLOCKED short-circuiting, unknown-role-result fail-closed, proposal schema strictness,
evidence-existence/hash-mismatch/staleness/future-dating, instrument/broker-mapping validation,
entry/stop/target ordering, allocation conservation (tested via a clearly-labeled schema-level
example, since the pipeline cannot currently produce an executable proposal — Section 5),
spread/session/risk-halt/correlated-exposure/quantity-step gates (Role 4/5/6 exercised directly
via `executable_role456_request()`), Role 5 independence, the generative-adapter boundary,
SMA-001 crossing parity and the geometry-not-approved block (`SMAGeometryBlockTests`, 8 tests),
FIB-001, confidence bounds/status/calibration-source resolution, sample-label separation
(including the new `VALIDATION` label), performance/walk-forward reporting
(`PerformanceReportingTests`, 30 tests), mode integration across OFF/RESEARCH/SYNTHETIC_PAPER/MT5,
the read-only HTTP surface, dashboard content, durable persistence
(`DurablePersistenceTests`, 18 tests, isolated temp directories only), and the absence of any
`order_check`/`order_send`/real-`MetaTrader5`/network-call surface, scanned across **every**
`trading_lab_app/signal_*.py` module by directory glob rather than a hand-maintained list.

Existing `test_forward_paper.py::test_governed_categories_and_schema` was updated (11 -> 12
categories) to reflect the additive `SIGNAL_PIPELINE_STEP` category; no existing test was
weakened, skipped, or deleted.

Full suite, `python -B -W error -m unittest discover -s . -p "test_*.py"`, run twice from the
`Trading_Lab` directory:

| Run | Tests | Result |
|---|---|---|
| 1 | 569 | 0 failures, 0 errors |
| 2 | 569 | 0 failures, 0 errors |

(447 pre-existing R2-001–005/Phase-3 tests, unchanged and unweakened, plus 122 Phase 4 tests.)

## 15. Manual rehearsal evidence

Performed against the real application and real port 8765 (not mocks), following the persisted
mode from OFF through RESEARCH and SYNTHETIC_PAPER and back to OFF, plus a real separate-CLI
durable-persistence rehearsal isolated to a temporary `LOCALAPPDATA`:

| Step | Action | Result |
|---|---|---|
| 1 | Confirm persisted mode starts at `OFF` | `mode_cli.py show-mode` -> `current_mode: OFF` |
| 2 | Start normally, check `/api/signal-status` | `enabled: false`, `operating_mode: OFF` |
| 3 | Stop | Port left in `TIME_WAIT` only, no listener |
| 4 | `mode_cli.py request-mode RESEARCH` | Accepted; `resulting_mode: RESEARCH` |
| 5 | Start; check `/api/signal-status` | `enabled: true`, `operating_mode: RESEARCH` |
| 6 | `signal_cli.py generate-proposal SMA-001 <bullish-crossing fixture>` | `side: BLOCKED`, `role_results.technical_strategy.candidate_direction: "BUY"`, `reasons: ["STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED"]`, every entry/stop/target/quantity field `null` |
| 7 | Stop; restart; `signal_cli.py proposal-history` | Same `proposal_id` from step 6 still present — durable across a real restart |
| 8 | From a separate CLI invocation with an isolated `LOCALAPPDATA`, `mode_cli.py request-mode RESEARCH` then `signal_cli.py generate-proposal` then, in a third separate process, `signal_cli.py proposal-history` | The third process's `proposal-history` reports the exact `proposal_id` the second process generated |
| 9 | `generate-proposal FIB-001 <fixture>`; `explain-strategy FIB-001` | `side: BLOCKED`, `reasons: ["STRATEGY_PARAMETERS_NOT_APPROVED"]` |
| 10 | Controlled Role 5 mismatch fixture (direct role call, not through Role 3) | `SIZE_MISMATCH_BETWEEN_PARTNERS` |
| 11 | `signal_cli.py performance-report SMA-001 SYNTHETIC_PAPER` over the durable history | `sample_status: INSUFFICIENT_SAMPLE`, `completed_trade_count: 0`, fee/slippage/spread assumptions visible, `confidence_calibration_status: UNCALIBRATED_HEURISTIC` |
| 12 | Deliberately corrupt an **isolated temporary copy** of the store file (never the real one) and reload | `SIGNAL_STORE_INTEGRITY_FAILURE`; `generate_proposal` raises rather than silently recovering |
| 13 | Stop; `mode_cli.py request-mode OFF`, then `request-mode SYNTHETIC_PAPER` | Both accepted |
| 14 | Start; check `/api/signal-status` and `/api/mode-status` | `enabled: true`, `operating_mode: SYNTHETIC_PAPER`, `broker_execution_available: false` |
| 15 | Generate a proposal, stop, restart | Proposal still present with `sample_label: "SYNTHETIC_PAPER"` and `operating_mode: "SYNTHETIC_PAPER"` intact |
| 16 | `mode_cli.py request-mode OFF` | Accepted; `current_mode: OFF` |
| 17 | Final port/process check | No listener on 8765, no `python.exe` process remaining |

No external network call, broker call, or model API call occurred at any point; every evaluation
used a locally authored fixture file.

## 16. Limitations

- Market-session state (`session_window`) and news/event-risk context (`news_context`) are
  governed **inputs** the caller supplies (fixtures in tests, an operator-prepared JSON file for
  the CLI) rather than a live trading-calendar or live news-feed integration — consistent with
  Phase 4's scope.
- **No SMA-001 execution geometry is approved** (Section 5) — SMA-001 currently produces research
  crossing directions only, exactly like FIB-001 produces no executable output at all. Neither
  strategy can currently produce an executable BUY/SELL proposal.
- Every performance report is `INSUFFICIENT_SAMPLE` in this checkpoint, because no strategy can
  yet produce a completed trade (Section 9) — this is the correct, honest state, not a defect.
- Correlated-exposure grouping uses a simple governed `correlation_group` string on each open
  position (caller-supplied) rather than a live instrument-correlation model.
- No HTTP route exists for performance/walk-forward reporting (CLI only — Section 9).

## 17. Explicit statement

**No proposal produced by this pipeline ever caused, authorized, or was treated as pre-approval
for a paper or broker order.** No code path in this checkpoint calls `order_check`, `order_send`,
constructs a real `MetaTrader5` connection, or makes any external network call. Neither the
SMA-001 execution-geometry blocker nor the FIB-001 parameter blocker is marked resolved. Phase 5
(MT5 execution adapter) was not started.
