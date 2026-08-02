# TRL-R2-010 Market Intelligence V0 Contract

> **RESEARCH ONLY — LOCAL ONLY — NO BROKER CALL EXISTS ANYWHERE IN THIS CONTRACT — NO EXECUTION AUTHORITY IS CREATED, GRANTED, OR IMPLIED**

Product working name: **TRL CORTEX V0**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-010 (contract-authoring checkpoint only; not an implementation checkpoint; not Phase 7) |
| Status | **Founder-approved.** This is the governing TRL-R2-010 contract for TRL CORTEX V0, reached through three Founder-directed passes: (1) canonical instrument/timeframe allowlists, the non-circular evidence identity model, exact evidence-completeness and score-aggregation formulas, final decision thresholds, precise blocker scoping, and an authorized `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` capability amendment; (2) the final analysis-input envelope, an eighth transport-only schema, an exact Decimal/`ROUND_HALF_EVEN` numeric policy, exact virtual-candidate geometry and reward/risk ranking formulas, the final closed basket-preview schema, exact quantity-conservation behavior (fail-closed, no redistribution), the exact 23-step decision order, exact CLI input-safety rules, and a bounded demonstration-fixture requirement. Contract-only: TRL CORTEX V0 implementation has not started. This checkpoint's exact staged/committed/pushed state is, per this program's Git-authoritative convention, always read from `git rev-parse HEAD`/`git status` directly rather than restated here as a fixed value. |
| Depends on | TRL-R2-005 (paper engine/timeline conventions), TRL-R2-006 (signal-intelligence evidence-role conventions, `signal_strategy_registry`), TRL-R2-007 (MT5 execution adapter, deterministic lookup-key/hash conventions), `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (`ModeService` authority; narrowly amended by this checkpoint, Section 5.2), TRL-R2-009 (controlled basket execution — Phase 6, complete; this contract's non-executable basket preview is deliberately economic-shape-compatible with it but never becomes it) |
| Feeds | No phase. This checkpoint is research-only and does not authorize, gate, or advance Phase 7, Phase 9, or Phase 10. Any future conversion of a virtual opportunity or basket preview into a real Phase 5/6 execution artifact requires a separate, explicitly Founder-approved handoff contract (Section 5). |

---

## 0. Numbering and classification decision

This contract is numbered **TRL-R2-010**. It does not reuse, rename, or
reinterpret any existing `TRL-R2-0XX` document: R2-005 (paper engine),
R2-006 (signal intelligence), R2-007 (MT5 execution), R2-008 (private
online operations, still not started), and R2-009 (controlled basket
execution, Phase 6, complete) are all unrelated checkpoints and remain
unchanged.

**This checkpoint is not a Phase in the existing 0–14 `TRL_FULL_VISION_MASTER_PROGRAM.md`
phase table.** Inserting it into that sequence would require renumbering
every phase from 7 onward, which is out of scope and not requested. Instead
it is recorded as a new, independent row — **Phase 6A — Market Intelligence
V0 (TRL-R2-010)** — positioned informationally after Phase 6 to reflect that
it was authored immediately afterward, but it is not a prerequisite for, and
does not block, gate, or reorder, Phases 7 through 14. It is explicitly not
Phase 7 (optional TradingView signal intake remains a separate, unrelated,
not-started checkpoint).

## 1. Checkpoint purpose

TRL CORTEX V0 converts a bounded, research-time market observation into
structured, auditable research intelligence: an **Opportunity Card**, a
**Virtual Opportunity Lattice** of hypothetical entry levels, an
evidence-council-scored **TRADE_CANDIDATE / WAIT / REJECT / BLOCKED /
EXPIRED** decision, a non-executable multi-target **basket preview**, and
**learning telemetry** recording what actually happened afterward — all
locally, deterministically (in V0), and with full reasoning exposed. It
captures the useful shape of the Founder-provided trading videos (governed
signal cards, internal level evaluation, multi-target previews, honest
performance reporting, outcome learning) while explicitly refusing the
unsafe behaviors those videos also showed (Section 4, Section 5).

## 2. Checkpoint classification

**Is:** research-only, local-only, deterministic in V0, evidence-based,
auditable, non-live, non-automated, non-executing, compatible with Phase 6,
safe for hypothetical and replay data.

**Is not:** Phase 7, a live strategy, an approved production signal, an
execution strategy, an automatic trading bot, a portfolio manager, a
self-modifying production system, an accuracy or profit guarantee.

## 3. Scope

In scope for the future implementation this contract authorizes (not this
checkpoint — Section 23):

- Seven governed record schemas (Section 6) plus one transport-only
  analysis input envelope (Section 7).
- Deterministic, non-circular identity formulas for every governed record
  type (Section 8).
- The eleven-category Evidence Council and its completeness rule
  (Section 9).
- The exact V0 decision model, including its Decimal/`ROUND_HALF_EVEN`
  numeric policy, producing `TRADE_CANDIDATE` / `WAIT` / `REJECT` /
  `BLOCKED` / `EXPIRED` via an exact 23-step evaluation order (Section 10).
- Exact virtual-candidate geometry validation and a deterministic
  reward/risk ranking model (Section 11).
- The Virtual Opportunity Lattice and its exact state derivation
  (Section 12).
- The non-executable basket preview, with exact quantity conservation
  (Section 13).
- Learning telemetry recording, with no automatic threshold/rule/strategy
  change (Section 14).
- A local-only CLI (with exact input-safety rules) and strictly read-only
  HTTP routes (Section 15).
- A bounded, append-only, hash-chained Market Intelligence journal, separate
  from the Phase 5/6 execution journal (Section 17).
- Local synthetic/fixture/replay data input only, with strict validation, a
  fixed canonical instrument/timeframe allowlist, and a bounded
  demonstration fixture (Sections 18, 21).
- New governed blockers for capabilities not yet approved, precisely scoped
  (Section 19).
- The narrow `market_intelligence_research` capability amendment authorized
  in Section 5.2.

### 3.1 Complete analysis input (Founder-finalized data-input model)

TRL CORTEX V0 does not claim to derive validated intelligence from live
market feeds. V0 accepts only committed synthetic fixtures, isolated test
fixtures, and strictly validated local user-supplied JSON (Section 18). No
external API, broker, TradingView, news feed, or AI model is required or
implemented.

**There is no automatic evidence generator in TRL CORTEX V0 — this is a
final decision, not an open question.** `analyze-market-snapshot` consumes
exactly one complete, strictly validated local JSON bundle — the
`TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1` transport envelope (Section 7)
— containing one market snapshot, one proposed side, exactly eleven
evidence inputs (one per required category, Section 9.1), one to six
virtual-candidate inputs, and the opportunity's strategy identity and
activation/invalidation signals. The service validates and transforms these
inputs into governed records (Section 6); it never infers evidence
automatically from raw candles, and never calls an AI model, an external
API, a broker, MetaTrader5, TradingView, a news provider, or a macro
provider. Committed synthetic demonstrations may use hand-authored evidence
bundles (Section 21). Local user evidence is treated as user-supplied
research input, not as verified market truth. Any automatic technical,
news, sentiment, macro, or cross-asset evidence generator requires a later,
separately Founder-approved contract.

## 4. Explicit exclusions (video-derived anti-patterns, not carried forward)

Not in scope, regardless of any apparent convenience or resemblance to the
source videos:

- Hundreds of real pending broker orders, or any real pending order at all.
- Uncontrolled grids of any kind.
- Unverified or promotional win-rate claims.
- Guaranteed-profit or guaranteed-accuracy claims of any kind.
- Automatic live trading, or automatic submission of anything to a broker.
- Autonomous self-modification of decision thresholds, rules, or code.
- Hidden risk, hidden levels, or an unexplained single black-box score.
- Any HTTP route that mutates state.
- Any promotion of a strategy, rule, or model without a human decision.
- Any modification, extension, or reinterpretation of a Phase 5/6 `v1`
  schema, function, or persisted document.
- An automatic raw-market evidence generator (Section 3.1).
- Silent alias-guessing of an instrument or timeframe identifier
  (Section 18.1).
- Quantity rounding or redistribution in a basket preview (Section 13.3) —
  a non-conserving quantity fails closed instead.

## 5. Hard execution boundary

TRL CORTEX V0 must not, anywhere in its design or future implementation:

- call `order_check`,
- call `order_send`,
- construct `RealMT5ExecutionAdapter`,
- connect to MetaTrader5,
- connect to a broker,
- build an executable Phase 6 `TRL_BASKET_PLAN.v1`/`TRL_BASKET_CHILD_INTENT.v1`,
- request or accept a Phase 6 basket confirmation,
- invoke `send-basket-next`,
- alter a Phase 6 basket or a Phase 5 order intent,
- create a real or demo broker order,
- bypass `ModeService`,
- activate a live or automated mode.

It may generate only: research opportunity records, virtual entry
candidates, evidence records, decision records, non-executable basket
previews, and outcome telemetry. **Any future execution handoff requires a
separate, explicitly Founder-approved contract** — this contract authorizes
none. `EXECUTION_HANDOFF_NOT_APPROVED` (Section 19) blocks every conversion
from any CORTEX V0 record into a Phase 5 order intent, a Phase 6 basket, a
confirmation request, or a broker instruction.

### 5.1 Operating-mode authority

`ModeService` remains the sole authority over every capability, including
Market Intelligence capabilities. No basket-mode file, second
operating-mode service, environment-variable bypass, CLI-only override, or
browser-side execution mode may exist. Every governed Market Intelligence
mutation independently calls `ModeService` — no module infers permission
from a mode-name string, a cached capability set, or a prior successful
check.

**`market_intelligence_research` is granted only to `RESEARCH`,
`SYNTHETIC_PAPER`, and `MT5_DEMO_MANUAL`.** It is granted to
`MT5_DEMO_MANUAL` because research-only analysis running alongside a
demo-manual execution mode creates no execution risk by itself (the
capability grants no order/basket authority of any kind); it is **not**
granted to `OFF`, `MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`, or
`MT5_LIVE_AUTOMATED`. This capability grants no `order_check`,
`order_send`, `manual_broker_execution`, `manual_basket_execution`,
`basket_execution`, live execution, automated execution, or execution
handoff of any kind — it is purely a gate on Market Intelligence *mutation*
(Section 15.1).

**Read-only operations remain available regardless of mode**, including
while `OFF` — status, list, inspect, journal inspection, and every read-only
HTTP route (Section 15) — matching the existing repository convention that
`show-mode`/`list-modes` and other pure-read commands never require a
capability grant.

### 5.2 Capability-matrix amendment (authorized this checkpoint)

This checkpoint is authorized to modify `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`
narrowly (Section 23) — mirroring exactly how the R2-009 contract added
`manual_basket_execution` in that file's Section 3.1. A new, eighteenth
governed capability, `market_intelligence_research`, is added:

| Mode | `market_intelligence_research` granted? |
|---|---|
| `OFF` | No |
| `RESEARCH` | **Yes** |
| `SYNTHETIC_PAPER` | **Yes** |
| `MT5_DEMO_MANUAL` | **Yes** |
| `MT5_DEMO_AUTOMATED` | No |
| `MT5_LIVE_MANUAL` | No |
| `MT5_LIVE_AUTOMATED` | No |

Granting this capability to `MT5_DEMO_MANUAL` does not, by itself, activate,
arm, or otherwise change the availability of `MT5_DEMO_AUTOMATED`,
`MT5_LIVE_MANUAL`, or `MT5_LIVE_AUTOMATED`, and grants none of
`mt5_order_check`/`mt5_order_send`/`manual_broker_execution`/
`manual_basket_execution`/`basket_execution` by implication. **This
contract-authoring checkpoint does not modify `mode_service.py`** — only the
governing document. Wiring the actual `ModeService` capability-matrix
constant is future implementation work (Section 22).

## 6. Required versioned schemas (seven governed records)

There are **seven immutable governed record schemas** — not six; the
non-executable basket preview (Section 6.7) is a governed schema in its own
right, formalized here rather than left informally described. Separately,
one **transport-only** input envelope (Section 7) carries analysis input
into the service but is never itself a governed record. All seven governed
schemas are independent, closed (unknown fields rejected), exactly
versioned, and validated the same way Phase 5/6 schemas are validated
(`validate_*` functions rejecting non-finite numbers, wrong types, and
out-of-range enums). No credential, raw account identity, or broker
connection detail appears in any field of any schema below.

### 6.1 `TRL_MARKET_SNAPSHOT.v1`

One bounded, research-time market observation.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_MARKET_SNAPSHOT.v1"` (closed) |
| `snapshot_id` | `"mkt_" + sha256(...)[:32]` (Section 8.1) |
| `instrument` | exactly one of the canonical instrument allowlist (Section 18.1) |
| `timeframe` | exactly one of the canonical timeframe allowlist (Section 18.1) |
| `observed_at_utc` | ISO-8601 UTC timestamp, finite, not in the future relative to ingestion |
| `open`, `high`, `low`, `close` | finite decimals, `low <= open,close <= high`, all `> 0` |
| `spread` | finite decimal `>= 0` |
| `volatility_measure` | finite decimal `>= 0` (governed metric, e.g. ATR-equivalent; method name carried in `volatility_method`) |
| `volatility_method` | non-empty string identifying the deterministic method used |
| `session` | one of `ASIA, LONDON, NEW_YORK, OVERLAP, OFF_HOURS` |
| `data_source_classification` | one of `COMMITTED_FIXTURE, ISOLATED_TEST_FIXTURE, LOCAL_USER_SUPPLIED, HISTORICAL_REPLAY` |
| `data_quality_status` | one of `SUFFICIENT, DEGRADED, INSUFFICIENT` |
| `event_risk_classification` | optional; one of `NONE, LOW, MEDIUM, HIGH`, or `null` when not manually supplied |
| `canonical_snapshot_hash` | sha256 over the complete record (Section 8.1) |

**`snapshot_mid_price` (derived, not stored):** the canonical current
research reference price used by Section 11's ranking model,
`quantize_4((high + low) / Decimal("2"))`. This contract defines it
explicitly, since Section 11's formulas require an exact, non-ambiguous
reference price; it is a computed value, not a schema field, and does not
participate in `canonical_snapshot_hash`.

### 6.2 `TRL_EVIDENCE_ITEM.v1`

One supporting, opposing, or neutral evidence item, scoped to a snapshot and
a proposed side — **never to an opportunity** (Founder correction, Section
8.2): this is exactly what makes evidence computable before any opportunity
exists and avoids the evidence↔opportunity identity cycle a naive schema
would otherwise create.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_EVIDENCE_ITEM.v1"` (closed) |
| `evidence_id` | `"evd_" + sha256(...)[:32]` (Section 8.2) |
| `snapshot_id`, `canonical_snapshot_hash` | pinned reference to Section 6.1 |
| `proposed_side` | `BUY` or `SELL` |
| `category` | one of the eleven Evidence Council categories (Section 9) |
| `evidence_direction` | one of `SUPPORTS, OPPOSES, NEUTRAL` |
| `normalized_strength` | decimal in `[0.0000, 1.0000]`, 4 dp |
| `confidence` | decimal in `[0.0000, 1.0000]`, 4 dp |
| `source_classification` | exactly one of `SYNTHETIC_FIXTURE, LOCAL_USER_INPUT` (Founder-finalized; no other value is approved for V0 evidence) |
| `source_reference` | non-empty string, maximum 256 Unicode code points; a bounded logical label (fixture ID, snapshot field name, or method name) — never an absolute filesystem path, never a URL requiring retrieval, never a credential, and never treated as independent proof |
| `observed_at_utc` | ISO-8601 UTC timestamp |
| `expires_at_utc` | ISO-8601 UTC timestamp, strictly after `observed_at_utc` |
| `explanation` | non-empty string, maximum 1000 Unicode code points, plain language, no HTML |
| `canonical_evidence_hash` | sha256 over the complete record (Section 8.2) |

**There is no `opportunity_id` field on this schema.** An opportunity
references its evidence items by `evidence_id`/`canonical_evidence_hash`
(Section 6.3); the reverse question ("which opportunities cite this
evidence item") is answered by querying the Market Intelligence journal by
`evidence_id`, never by a stored backward-reference field.

### 6.3 `TRL_OPPORTUNITY_CARD.v1`

The complete research opportunity.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_OPPORTUNITY_CARD.v1"` (closed) |
| `opportunity_id` | `"opp_" + sha256(...)[:32]` (Section 8.3) |
| `snapshot_id`, `canonical_snapshot_hash` | pinned reference to Section 6.1 |
| `instrument`, `timeframe` | inherited from the snapshot |
| `proposed_side` | `BUY` or `SELL` |
| `market_regime` | one of `TRENDING, RANGING, VOLATILE_EXPANSION, VOLATILE_CONTRACTION, UNCLASSIFIED` |
| `strategy_id` | non-empty string; defaults to `"CORTEX-V0-HEURISTIC"` (Section 19.3) when the entry concept cites no specific registered strategy; `"SMA-001"` or `"FIB-001"` when it explicitly does |
| `strategy_version` | non-empty string; `"1.0.0"` for `CORTEX-V0-HEURISTIC` |
| `entry_concept` | non-empty string, plain-language description (not an order) |
| `invalidation_concept` | non-empty string |
| `stop_concept` | non-empty string |
| `ordered_target_concepts` | list of 2–4 non-empty strings, ordered nearest-to-farthest from entry |
| `evidence_ids` | ordered list of **exactly 11** `evidence_id` values, one per Evidence Council category, in the fixed Section 9 category order, each resolvable in the journal and non-expired as of `created_at_utc` (Section 9.1) |
| `activation_satisfied`, `invalidation_satisfied` | booleans — **opportunity-level** signals supplied directly in the analysis input envelope (Section 7), driving decision Section 10.4 steps 12/16. Distinct from each virtual candidate's own **candidate-level** `activation_satisfied`/`invalidation_satisfied` (Section 11.1), which drive only that candidate's own state (Section 12.2). The two levels are independently supplied and not derived from one another in V0 — an intentional simplification. |
| `supporting_score`, `contradiction_score`, `uncertainty_score`, `data_quality_score`, `estimated_cost_score`, `event_risk_score`, `risk_exposure_score` | each a decimal in `[0.0000, 1.0000]`, 4 dp (Section 10.2) |
| `decision_status` | one of `TRADE_CANDIDATE, WAIT, REJECT, BLOCKED, EXPIRED` (denormalized copy of the latest `TRL_OPPORTUNITY_DECISION.v1`) |
| `decision_reason_codes` | list of governed reason codes (Section 10.4), denormalized copy |
| `created_at_utc` | ISO-8601 UTC timestamp — **display-only, excluded from `opportunity_id`** (Section 8.3) |
| `expiry_utc` | ISO-8601 UTC timestamp, strictly after `created_at_utc` |
| `canonical_opportunity_hash` | sha256 over the complete record excluding `decision_status`/`decision_reason_codes`/`created_at_utc` (Section 8.3 — a mutable lifecycle/display projection must not change this hash) |

### 6.4 `TRL_VIRTUAL_OPPORTUNITY.v1`

One hypothetical internal level, **derived** from one
`virtual_candidate_input` (Section 7) plus the geometry/ranking formulas of
Section 11. Explicitly non-executable.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_VIRTUAL_OPPORTUNITY.v1"` (closed) |
| `virtual_opportunity_id` | `"vop_" + sha256(...)[:32]` (Section 8.4) |
| `opportunity_id`, `canonical_opportunity_hash` | pinned parent reference |
| `rank` | integer `>= 1`, unique within the lattice, **service-assigned only** — no user-supplied rank is ever authoritative (Section 11.3) |
| `hypothetical_entry_trigger` | finite decimal `> 0` (copied from the candidate input's `entry_trigger`) |
| `stop` | finite decimal `> 0` (copied from `stop_price`), on the correct side of the trigger for `proposed_side` (Section 11.1) |
| `ordered_targets` | list of 2–4 finite decimals `> 0` (copied from `target_prices`), ordered nearest-to-farthest, all on the correct side of the trigger |
| `expected_reward_risk_ratio` | finite decimal `>= 0`; **exactly** `reward_risk_ratio` from Section 11.2 — not an estimate |
| `estimated_transaction_cost` | finite decimal `>= 0`, same unit as price |
| `activation_condition` | non-empty string (plain-language trigger rule) |
| `invalidation_condition` | non-empty string |
| `state` | one of `WATCHING, ACTIVATED, INVALIDATED, EXPIRED, REJECTED, SELECTED_FOR_PREVIEW` (Section 12.2 — a mutable lifecycle projection; each transition is recorded as its own immutable `MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED` journal event, never an in-place rewrite of an earlier canonical record) |
| `expiry_utc` | ISO-8601 UTC timestamp (copied from `expires_at_utc`) |
| `non_executable` | literal `true` (always; schema-enforced, not a display convention) |
| `canonical_virtual_opportunity_hash` | sha256 over the complete record excluding `state` (a lifecycle projection, Section 12.2) |

### 6.5 `TRL_OPPORTUNITY_DECISION.v1`

The deterministic V0 classification.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_OPPORTUNITY_DECISION.v1"` (closed) |
| `decision_id` | `"dec_" + sha256(...)[:32]` (Section 8.5) |
| `opportunity_id`, `canonical_opportunity_hash` | pinned parent reference |
| `decision_input_hash` | sha256 over the exact scored inputs used (Section 8.5) |
| `final_status` | one of `TRADE_CANDIDATE, WAIT, REJECT, BLOCKED, EXPIRED` |
| `supporting_evidence_ids`, `opposing_evidence_ids` | lists of `evidence_id` values partitioned by resolved `evidence_direction`, restricted to the five directional categories (Section 10.2) |
| `uncertainty_score`, `event_risk_score`, `risk_exposure_score` | decimals `[0.0000, 1.0000]`, 4 dp |
| `evidence_completeness_passed` | boolean — exactly 11 non-expired, non-duplicated required-category items were present, none of them individually expired (Section 9.1) |
| `data_sufficiency_passed` | boolean — `data_quality_score >= DATA_QUALITY_MIN` |
| `cost_sufficiency_passed` | boolean — `estimated_cost_score < TRADE_CANDIDATE_COST_MAX` |
| `strategy_gate_passed` | boolean — the strategy-specific registry re-check (Section 10.3), scoped only to `strategy_id in {"SMA-001", "FIB-001"}`; always `true` for `CORTEX-V0-HEURISTIC` |
| `reason_codes` | ordered list of governed reason codes (Section 10.4), first-triggered-gate first |
| `evaluated_at_utc` | ISO-8601 UTC timestamp — display-only, excluded from `decision_id` |
| `canonical_decision_hash` | sha256 over the complete record excluding `evaluated_at_utc` |

### 6.6 `TRL_LEARNING_TELEMETRY.v1`

What happened after a research opportunity.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_LEARNING_TELEMETRY.v1"` (closed) |
| `telemetry_id` | `"tel_" + sha256(...)[:32]` (Section 8.6) |
| `opportunity_id`, `canonical_opportunity_hash`, `decision_id` | pinned references |
| `observation_window_start_utc`, `observation_window_end_utc` | ISO-8601 UTC, end strictly after start |
| `predicted_direction` | `BUY` or `SELL` (copy of `proposed_side`) |
| `predicted_entry`, `predicted_stop`, `predicted_targets` | copied from the selected virtual opportunity at recording time (Section 13) |
| `realized_movement` | finite decimal (signed, price units) |
| `maximum_favorable_excursion`, `maximum_adverse_excursion` | finite decimals `>= 0` |
| `theoretical_result_after_costs` | finite decimal (signed) |
| `original_decision_status` | one of `TRADE_CANDIDATE, WAIT, REJECT, BLOCKED` (never `EXPIRED` — Section 14.1) |
| `calibration_bucket` | one of `HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE, UNCALIBRATED` |
| `outcome_classification` | one of `TRUE_POSITIVE, FALSE_POSITIVE, TRUE_NEGATIVE, FALSE_NEGATIVE, INDETERMINATE` |
| `missing_data_status` | one of `COMPLETE, PARTIAL, UNAVAILABLE` |
| `regime_at_recording` | copy of `market_regime` |
| `recorded_at_utc` | ISO-8601 UTC — display-only, excluded from `telemetry_id` |
| `canonical_telemetry_hash` | sha256 over the complete record excluding `recorded_at_utc` |

Telemetry is append-only and must never rewrite `TRL_OPPORTUNITY_CARD.v1`,
`TRL_OPPORTUNITY_DECISION.v1`, or any evidence item.

### 6.7 `TRL_MARKET_INTELLIGENCE_BASKET_PREVIEW.v1` (Founder-finalized closed schema)

A read-only research projection of the `SELECTED_FOR_PREVIEW` virtual
opportunity, shaped economically like a Phase 6 basket for legibility, but
never becoming one. Its distinct `schema_version` alone causes Phase 6's
closed-schema validators to reject it naturally, with no Phase 6 source
change required.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_MARKET_INTELLIGENCE_BASKET_PREVIEW.v1"` (closed) |
| `preview_id` | `"prv_" + sha256(...)[:32]` (Section 8.7) |
| `opportunity_id`, `canonical_opportunity_hash` | pinned parent reference |
| `selected_virtual_opportunity_id`, `canonical_virtual_opportunity_hash` | pinned reference to the one `SELECTED_FOR_PREVIEW` virtual opportunity (Section 12.3) |
| `instrument`, `proposed_side` | inherited from the opportunity |
| `entry_trigger` | finite decimal `> 0` (copied from the selected virtual opportunity's `hypothetical_entry_trigger`) |
| `stop_price` | finite decimal `> 0` (copied from its `stop`) |
| `ordered_target_prices` | 2–4 finite decimals `> 0`, ordered nearest-to-farthest (copied from `ordered_targets`) |
| `ordered_target_allocations` | one per target, each `> 0.0000`, 4 dp, summing to **exactly** `100.0000` (validated as an input constraint on the originating virtual-candidate input, Section 11.1 — never computed or redistributed by the service) |
| `hypothetical_total_quantity` | `null`, or a finite positive canonical decimal (up to 8 dp, Section 13.2) |
| `ordered_hypothetical_child_quantities` | `null` when `hypothetical_total_quantity` is `null`; otherwise a list of finite positive decimals, one per target, each exactly representable at up to 8 dp, summing **exactly** to `hypothetical_total_quantity` (Section 13.2 — no residue redistribution; a non-conserving result fails closed instead) |
| `total_hypothetical_risk` | finite decimal `>= 0`, computed from `entry_trigger`/`stop_price` and, when supplied, `hypothetical_total_quantity` |
| `non_executable` | literal `true` |
| `execution_handoff_status` | literal `"EXECUTION_HANDOFF_NOT_APPROVED"` (Section 19.5) |
| `created_at_utc` | ISO-8601 UTC timestamp — display-only, excluded from `preview_id` |
| `expires_at_utc` | ISO-8601 UTC timestamp, strictly after `created_at_utc` |
| `canonical_preview_hash` | sha256 over the complete record excluding `created_at_utc` |

This preview is **never** represented as, converted to, or validated
against `TRL_BASKET_PLAN.v1` or `TRL_BASKET_CHILD_INTENT.v1`; it is never
written into the Phase 5/6 execution journal. SMA-001 and FIB-001 remain
blocked here exactly as in Section 10.3, scoped identically (narrowly, not
globally). Any future conversion of a preview into a real basket requires a
separate, explicitly Founder-approved handoff contract (Section 5).

## 7. Analysis input envelope (transport-only — not a governed record)

`TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1` is the sole accepted shape for
`analyze-market-snapshot`'s input file. It is **validated but is not an
authoritative journal record, is not independently persisted as a business
record, has no independent business identity (no `_id`/canonical-hash
field of its own), is not an execution document, and is never accepted by
Phase 5 or Phase 6.** Once validated, the service derives and persists the
seven governed records (Section 6) from it; the envelope itself is not
retained as a governed artifact.

### 7.1 Closed top-level fields

| Field | Type / domain |
|---|---|
| `schema_version` | must equal `"TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1"` exactly |
| `snapshot` | one embedded object validated against `TRL_MARKET_SNAPSHOT.v1`'s field rules (Section 6.1), minus `snapshot_id`/`canonical_snapshot_hash` (service-derived) |
| `proposed_side` | exactly `BUY` or `SELL` |
| `strategy_id` | non-empty string; may default to `"CORTEX-V0-HEURISTIC"` for the accelerated V0 fixture |
| `strategy_version` | non-empty string; may default to `"1.0.0"` |
| `evidence_inputs` | exactly 11 closed evidence objects, one per required category (Section 9.1), each validated against `TRL_EVIDENCE_ITEM.v1`'s field rules minus `evidence_id`/`canonical_evidence_hash` (service-derived) |
| `virtual_candidate_inputs` | between 1 and 6 closed candidate objects (Section 11.1) |
| `activation_satisfied` | strict JSON boolean — opportunity-level (Section 6.3) |
| `invalidation_satisfied` | strict JSON boolean — opportunity-level (Section 6.3) |

Unknown top-level or nested fields fail closed. No field may be omitted;
there is no implicit default for any field other than `strategy_id`/
`strategy_version` as stated above.

### 7.2 Envelope-level safety rules

- Maximum total input size: **262144 bytes**.
- Input must be **strict UTF-8 JSON**.
- **No** JSON comments, `NaN`, `Infinity`, `-Infinity`, or duplicate object
  keys are permitted anywhere in the document — any of these fails closed.
- The envelope must not contain: a credential, an account number, a broker
  server address, an API key, Python code, a shell command, an executable
  path, a Phase 5 order intent, or a Phase 6 basket plan.
- `source_reference` fields (Section 6.2) are stored as bounded logical
  labels only — never the absolute input file path, never a retrievable
  URL.

## 8. Deterministic identities

All identities use the established Phase 5/6 pattern: `"<prefix>_" +
sha256("<DOMAIN>.v1\n" + canonical_json(<non-circular field set>))[:32]`,
using the existing `trading_lab_core.canonical.canonical_json` encoder for
byte-stable ordering. No identity contains a nonce. No identity depends on
a display-only or mutable-lifecycle field (`created_at_utc`,
`evaluated_at_utc`, `recorded_at_utc`, `state`, `decision_status`,
`decision_reason_codes`). **The transport-only analysis input envelope
(Section 7) has no identity formula at all — it is never persisted as a
governed record, so no `_id`/canonical-hash is ever computed for it.**
Computation for the seven governed schemas proceeds strictly in this
order — matching the Founder-mandated sequence exactly (snapshot →
evidence → opportunity → {virtual opportunity, decision} → {basket
preview, telemetry}) — so no formula ever references a hash computed after
it:

1. **Market snapshot ID** — `TRL-MARKET-SNAPSHOT-ID.v1` over `instrument,
   timeframe, observed_at_utc, open, high, low, close, spread,
   volatility_measure, volatility_method, session,
   data_source_classification, data_quality_status,
   event_risk_classification`. `canonical_snapshot_hash` covers the same
   fields plus `snapshot_id` itself.

2. **Evidence ID** — `TRL-EVIDENCE-ID.v1` over `snapshot_id, proposed_side,
   category, evidence_direction, normalized_strength, confidence,
   source_classification, source_reference, observed_at_utc,
   expires_at_utc`. **`opportunity_id` is never an input — there is no such
   field on `TRL_EVIDENCE_ITEM.v1` at all** (Section 6.2). `canonical_evidence_hash`
   covers the same fields plus `evidence_id` and `explanation`.

3. **Opportunity ID** — `TRL-OPPORTUNITY-ID.v1` over `snapshot_id,
   proposed_side, market_regime, strategy_id, strategy_version,
   entry_concept, invalidation_concept, stop_concept,
   ordered_target_concepts, activation_satisfied, invalidation_satisfied,
   ordered_evidence_refs`, where `ordered_evidence_refs` is the list of
   `(evidence_id, canonical_evidence_hash)` pairs for the opportunity's
   exactly-eleven required evidence items, ordered by the fixed Evidence
   Council category order (Section 9). Pinning each item's
   `canonical_evidence_hash` makes the opportunity identity tamper-evident
   against any evidence record's content changing after being cited. This
   makes opportunity generation idempotent by content (opportunity reuse —
   Section 22). `canonical_opportunity_hash` covers the same fields plus
   `opportunity_id` and the seven scores (Section 10.2); it explicitly
   excludes `decision_status`, `decision_reason_codes`, and `created_at_utc`.

4. **Virtual opportunity ID** — `TRL-VIRTUAL-OPPORTUNITY-ID.v1` over
   `opportunity_id, canonical_opportunity_hash, hypothetical_entry_trigger,
   stop, ordered_targets`. **`rank` is deliberately not an input** — rank is
   a service-assigned projection over already-identified candidates
   (Section 11.3), so including it in the identity would make the ID depend
   on the outcome of ranking every other candidate, an unnecessary and
   avoidable coupling. Re-running lattice construction over unchanged
   candidate inputs reproduces identical virtual-opportunity IDs (lattice
   determinism — Section 22) regardless of ranking order.

5. **Decision ID** — `TRL-OPPORTUNITY-DECISION-ID.v1` over `opportunity_id,
   canonical_opportunity_hash, decision_input_hash`, where
   `decision_input_hash` is itself `sha256(canonical_json(supporting_score,
   contradiction_score, uncertainty_score, data_quality_score,
   estimated_cost_score, event_risk_score, risk_exposure_score,
   evidence_completeness_passed, data_sufficiency_passed,
   cost_sufficiency_passed, strategy_gate_passed, activation_satisfied,
   invalidation_satisfied, expiry_status))`. This makes decision evaluation
   idempotent by content: re-evaluating an opportunity whose scored inputs
   have not changed returns the existing decision record rather than
   minting a new one (decision reuse).

6. **Telemetry ID** — `TRL-LEARNING-TELEMETRY-ID.v1` over `opportunity_id,
   canonical_opportunity_hash, decision_id, observation_window_start_utc,
   observation_window_end_utc`.

7. **Basket preview ID** — `TRL-BASKET-PREVIEW-ID.v1` over
   `opportunity_id, canonical_opportunity_hash,
   selected_virtual_opportunity_id, canonical_virtual_opportunity_hash`.

No identity formula above takes as input a hash computed from data that
includes that identity's own value or any value computed after it — there
is no cycle in the dependency graph `snapshot -> evidence -> opportunity ->
{virtual_opportunity, decision} -> {basket_preview, telemetry}`. A direct
acceptance test for this dependency-order property is required
(Section 22).

## 9. Evidence Council V0

Eleven deterministic V0 categories, in this fixed order (used for
`evidence_ids` ordering, Section 6.3, and for the `ordered_evidence_refs`
identity input, Section 8.3). Each produces its own `TRL_EVIDENCE_ITEM.v1`
record with its own `evidence_direction`/`normalized_strength`/`confidence`
— never collapsed into one unexplained score:

| # | Category | What it evaluates | Feeds |
|---|---|---|---|
| 1 | `MARKET_STRUCTURE` | Higher-high/higher-low or equivalent structural read from the snapshot | `supporting_score`/`contradiction_score` (directional, Section 10.2) |
| 2 | `TREND` | Directional bias over the snapshot's timeframe | `supporting_score`/`contradiction_score` (directional) |
| 3 | `MOMENTUM` | Rate-of-change / oscillator-style read | `supporting_score`/`contradiction_score` (directional) |
| 4 | `VOLATILITY` | Fit between `volatility_measure` and the proposed geometry | Required category; recorded for display/regime context only in V0 — **not** scored into `supporting_score`, `contradiction_score`, or any cost/risk score |
| 5 | `LIQUIDITY_AND_SPREAD` | `spread` relative to a governed acceptable-spread ceiling | Required category; recorded for display context only in V0 |
| 6 | `MULTI_TIMEFRAME_ALIGNMENT` | Agreement/conflict of the proposed side against a higher timeframe | `supporting_score`/`contradiction_score` (directional) |
| 7 | `EVENT_RISK` | `event_risk_classification`, when supplied | `event_risk_score` (severity) only — never support/contradiction |
| 8 | `EXECUTION_COST` | Spread + a governed commission/slippage estimate vs. theoretical reward | `estimated_cost_score` (severity) only |
| 9 | `RISK_EXPOSURE` | Registry/geometry blocker re-check context and any governed exposure limit | `risk_exposure_score` (severity) only — never support/contradiction |
| 10 | `CONTRADICTING_EVIDENCE` | Any explicit counter-thesis observation, scored on its own terms | `supporting_score`/`contradiction_score` (directional) |
| 11 | `DATA_QUALITY` | `data_quality_status`, source classification, staleness relative to `observed_at_utc` | `data_quality_score` only |

**Directional evidence categories are exactly five:** `MARKET_STRUCTURE`,
`TREND`, `MOMENTUM`, `MULTI_TIMEFRAME_ALIGNMENT`, `CONTRADICTING_EVIDENCE`.
`VOLATILITY` and `LIQUIDITY_AND_SPREAD` remain required categories (one
evidence item each, contributing to the eleven-category completeness rule
below) but do not feed any numeric score in this checkpoint.

### 9.1 Evidence completeness rule (Founder-finalized)

A valid V0 decision requires **exactly one active evidence item for each of
the eleven categories** — no more, no fewer:

- A **duplicate** active (non-expired) item for the same category fails
  closed: `MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_DUPLICATED` → `BLOCKED`.
- A **missing** required category fails closed:
  `MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_MISSING` → `BLOCKED`.
- An item present for its category but individually **expired**
  (`expires_at_utc` already passed as of `created_at_utc`) fails closed on
  its own, distinct reason:
  `MARKET_INTELLIGENCE_EVIDENCE_EXPIRED` → `BLOCKED` (Section 10.4, step 6)
  — distinguished from the missing-category case (step 4) so an operator
  can tell "nothing was ever submitted for this category" apart from
  "something was submitted but it went stale."
- Category ordering follows the exact Section 9 list (1–11) — there is no
  hidden category.
- Every `normalized_strength`/`confidence` value must be finite and bounded
  `[0.0000, 1.0000]`, represented at a fixed four-decimal precision
  (`quantize_4`, Section 10.1).

**V0 remains exactly one evidence item per category for deterministic
simplicity.** A later contract amendment may permit multiple items per
category — this contract authorizes only the exactly-one-per-category
model.

### 9.2 Evidence identity scoping (why there is no `opportunity_id` field)

Restated from Section 6.2/8.2 for emphasis: evidence is scoped to
`(snapshot_id, proposed_side)` and its own category/direction/strength/
confidence/source/timing fields — never to the opportunity that will later
cite it. This is what makes every evidence ID fully computable before any
opportunity exists, and is the specific correction that closes the
evidence↔opportunity identity-cycle risk a naive schema (evidence carrying
`opportunity_id`, opportunity carrying `evidence_ids`) would otherwise
create.

## 10. V0 decision model

A research classification heuristic, **not a validated trading edge**
(`INTELLIGENCE_SCORING_NOT_VALIDATED`, Section 19).

### 10.1 Numeric and quantization policy (Founder-finalized)

All scoring and ranking arithmetic **must use Python `Decimal` arithmetic —
never binary floating-point** — for every canonical decision, hash input,
or ranking comparison.

```
quantize_4(value) = Decimal(value).quantize(
    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
)
```

- Score scale: `0.0000` through `1.0000`.
- Score precision: exactly four decimal places.
- Rounding mode: `ROUND_HALF_EVEN` (banker's rounding) — exact, not
  `ROUND_HALF_UP` or any other mode.
- Canonical score text is always the fixed four-decimal string form; no
  exponent notation is ever produced or accepted.
- A negative-zero result canonicalizes to `0.0000`.
- Non-finite values (`NaN`, `Infinity`, `-Infinity`) fail closed wherever
  they would otherwise be computed or accepted.
- All intermediate multiplication, addition, and division use `Decimal`
  throughout — no field is ever cast to a binary float at any stage.
- `quantize_4` is applied **only at the exact stages this contract
  specifies** (Section 10.2) — never repeatedly at undocumented
  intermediate steps, so that a sum of several already-quantized values is
  itself computed and divided in full precision before its own single,
  final `quantize_4` call.
- Price and quantity fields follow the repository's existing canonical
  finite-decimal policy (no exponent notation).

### 10.2 Scores and thresholds (exact aggregation formulas)

Define `effective_evidence_score(item) = quantize_4(normalized_strength *
confidence)` — the one quantization stage per evidence item.

**Directional aggregation** (over exactly the five directional categories
— Section 9 — each contributing exactly one item under the completeness
rule). The five per-item `effective_evidence_score` values are summed with
full `Decimal` precision (no intermediate re-quantization), and only the
final division result is quantized:

```
supporting_effective_score_sum = sum(effective_evidence_score(item)
    for item in the 5 directional items
    where item.evidence_direction == SUPPORTS)

opposing_effective_score_sum = sum(effective_evidence_score(item)
    for item in the 5 directional items
    where item.evidence_direction == OPPOSES)

supporting_score    = quantize_4(supporting_effective_score_sum / Decimal("5"))
contradiction_score = quantize_4(opposing_effective_score_sum / Decimal("5"))
```

A `NEUTRAL` item contributes zero to both sums. **The denominator remains
exactly `5` in every case**, regardless of how many of the five items are
`NEUTRAL`.

**Uncertainty** (over all eleven required items, not just the directional
five):

```
uncertainty_sum = sum(Decimal("1.0000") - item.confidence
    for item in the 11 required items)

uncertainty_score = quantize_4(uncertainty_sum / Decimal("11"))
```

**Single-category severity/quality scores** (each is simply the effective
score of that category's one required item — no further aggregation):

```
data_quality_score   = effective_evidence_score(DATA_QUALITY item)
estimated_cost_score = effective_evidence_score(EXECUTION_COST item)
event_risk_score     = effective_evidence_score(EVENT_RISK item)
risk_exposure_score  = effective_evidence_score(RISK_EXPOSURE item)
```

For `EXECUTION_COST`, `EVENT_RISK`, and `RISK_EXPOSURE`, `normalized_strength`
is interpreted as **severity**, not positive support: `0.0000` = negligible
impact, `1.0000` = prohibitive/maximal impact. These three severity scores
are never mixed into `supporting_score` or `contradiction_score`.

Named threshold constants (exact, bounded, fixed by this contract; all
comparisons use exact four-decimal `Decimal` values — no floating-point
tolerance window):

| Constant | Value |
|---|---|
| `DATA_QUALITY_MIN` | `0.6000` |
| `TRADE_CANDIDATE_SUPPORT_MIN` | `0.6500` |
| `TRADE_CANDIDATE_CONTRADICTION_MAX` | `0.3500` |
| `REJECT_CONTRADICTION_MIN` | `0.6000` |
| `TRADE_CANDIDATE_UNCERTAINTY_MAX` | `0.4000` |
| `TRADE_CANDIDATE_COST_MAX` | `0.3000` |
| `REJECT_COST_MIN` | `0.7000` |
| `HARD_EVENT_RISK_BLOCK_MIN` | `0.9000` |
| `HARD_RISK_EXPOSURE_BLOCK_MIN` | `0.9000` |
| `WAIT_EVENT_RISK_MIN` | `0.6000` |
| `WAIT_RISK_EXPOSURE_MIN` | `0.6000` |

### 10.3 Hard gates (evaluated before any score threshold)

- **Schema/input gate:** every input record (envelope, snapshot, all eleven
  evidence items) must pass Section 6/7's closed-schema validation.
- **Instrument/timeframe gate:** `instrument` and `timeframe` must each be
  on the canonical allowlist (Section 18.1) — no alias is guessed.
- **Evidence-completeness gate:** exactly one non-expired item per category,
  no duplicates (Section 9.1).
- **Data-quality gate:** `data_quality_score >= DATA_QUALITY_MIN`.
- **Hard event-risk gate:** `event_risk_score >= HARD_EVENT_RISK_BLOCK_MIN`.
- **Hard risk-exposure gate:** `risk_exposure_score >= HARD_RISK_EXPOSURE_BLOCK_MIN`.
- **Strategy-specific gate (narrowly scoped):** applies **only** when
  `strategy_id == "SMA-001"` (re-checks
  `signal_strategy_registry.executable_status("SMA-001")`, fails closed
  with `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`) or `strategy_id ==
  "FIB-001"` (re-checks the equivalent FIB-001 registry status, fails
  closed with `STRATEGY_PARAMETERS_NOT_APPROVED`). **It does not apply for
  `strategy_id == "CORTEX-V0-HEURISTIC"` or any other non-registered
  identifier.**

### 10.4 Exact evaluation order and reason codes (23 steps, Founder-finalized)

Evaluated strictly in this order; the first matching rule determines
`final_status` and is the first entry in `reason_codes`. Later-triggered
conditions (at a strictly lower rule number) are appended for auditability
but never change `final_status`.

**BLOCKED (before any scoring), in order:**

1. Schema or canonical validation failed on any input record ->
   `MARKET_INTELLIGENCE_SCHEMA_VALIDATION_FAILED`.
2. `instrument` not on the canonical allowlist ->
   `MARKET_INTELLIGENCE_INSTRUMENT_NOT_ALLOWED`.
3. `timeframe` not on the canonical allowlist ->
   `MARKET_INTELLIGENCE_TIMEFRAME_NOT_ALLOWED`.
4. Required evidence category missing ->
   `MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_MISSING`.
5. Duplicate active evidence item for one category ->
   `MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_DUPLICATED`.
6. A required category's evidence item is individually expired ->
   `MARKET_INTELLIGENCE_EVIDENCE_EXPIRED`.

**EXPIRED (its own status, evaluated immediately after the structural gates
above, strictly before any further gate):**

7. The opportunity's own `expiry_utc` has already passed as of evaluation
   time -> `MARKET_INTELLIGENCE_OPPORTUNITY_EXPIRED`. (`TRL_MARKET_SNAPSHOT.v1`
   carries no independent expiry/staleness field in V0, so this step is
   driven entirely by the opportunity's own `expiry_utc` — there is no
   separate "expired snapshot" condition to evaluate.)

**BLOCKED, continued:**

8. `data_quality_score < DATA_QUALITY_MIN` ->
   `MARKET_INTELLIGENCE_DATA_QUALITY_BELOW_MINIMUM`.
9. `event_risk_score >= HARD_EVENT_RISK_BLOCK_MIN` ->
   `MARKET_INTELLIGENCE_HARD_EVENT_RISK_BLOCK`.
10. `risk_exposure_score >= HARD_RISK_EXPOSURE_BLOCK_MIN` ->
    `MARKET_INTELLIGENCE_HARD_RISK_EXPOSURE_BLOCK`.
11. Strategy-specific gate fails (Section 10.3, `strategy_id` in
    `{"SMA-001", "FIB-001"}` only) -> `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`
    or `STRATEGY_PARAMETERS_NOT_APPROVED` (reused exactly, never renamed).

**REJECT, in order (only reached if no BLOCKED/EXPIRED rule above fired):**

12. Opportunity-level `invalidation_satisfied == true` ->
    `MARKET_INTELLIGENCE_INVALIDATION_ALREADY_OCCURRED`.
13. Structural inconsistency: **every** virtual candidate derived from this
    opportunity is `REJECTED` under Section 12.2's geometry/consistency
    check (zero structurally valid candidates exist) ->
    `MARKET_INTELLIGENCE_STRUCTURALLY_INCONSISTENT`.
14. `contradiction_score >= REJECT_CONTRADICTION_MIN` ->
    `MARKET_INTELLIGENCE_CONTRADICTION_REJECTED`.
15. `estimated_cost_score >= REJECT_COST_MIN` ->
    `MARKET_INTELLIGENCE_TRANSACTION_COST_DESTROYS_EDGE`.

**WAIT, in order (only reached if no BLOCKED/EXPIRED/REJECT rule fired):**

16. Opportunity-level `activation_satisfied == false` ->
    `MARKET_INTELLIGENCE_TRIGGER_NOT_ACTIVE`.
17. `event_risk_score >= WAIT_EVENT_RISK_MIN` ->
    `MARKET_INTELLIGENCE_EVENT_RISK_WAIT`.
18. `risk_exposure_score >= WAIT_RISK_EXPOSURE_MIN` ->
    `MARKET_INTELLIGENCE_RISK_EXPOSURE_WAIT`.
19. `uncertainty_score > TRADE_CANDIDATE_UNCERTAINTY_MAX` ->
    `MARKET_INTELLIGENCE_UNCERTAINTY_ABOVE_THRESHOLD`.
20. `supporting_score < TRADE_CANDIDATE_SUPPORT_MIN` ->
    `MARKET_INTELLIGENCE_SUPPORT_BELOW_THRESHOLD`.
21. `contradiction_score > TRADE_CANDIDATE_CONTRADICTION_MAX` ->
    `MARKET_INTELLIGENCE_CONTRADICTION_ABOVE_THRESHOLD`.
22. `estimated_cost_score > TRADE_CANDIDATE_COST_MAX` ->
    `MARKET_INTELLIGENCE_TRANSACTION_COST_MARGINAL`.

**TRADE_CANDIDATE:**

23. All gates and thresholds above pass ->
    `MARKET_INTELLIGENCE_ALL_GATES_PASSED`.

**`TRADE_CANDIDATE` never means execution approval.** It is a research
classification only; converting it into anything Phase 5/6 recognizes
requires a separate, human-operated construction of a real signal proposal
and order intent through the existing, unmodified Phase 4/5/6 pipelines —
never a direct promotion of a `TRL_OPPORTUNITY_CARD.v1`.
`INTELLIGENCE_SCORING_NOT_VALIDATED` and `EXECUTION_HANDOFF_NOT_APPROVED`
(Section 19) do not replace this research classification — they continue to
block only claims, promotion, and execution handoff, never the internal
`TRADE_CANDIDATE`/`WAIT`/`REJECT`/`BLOCKED` classification itself.

## 11. Virtual-candidate geometry and reward/risk ranking model

### 11.1 `virtual_candidate_input` (closed, part of the Section 7 envelope)

| Field | Type / domain |
|---|---|
| `entry_trigger` | finite positive decimal |
| `stop_price` | finite positive decimal |
| `target_prices` | 2–4 finite positive decimals |
| `target_allocations` | same count as `target_prices`; each `> 0.0000`, 4 dp, summing to **exactly** `100.0000` — validated as an input constraint, never computed or redistributed by the service |
| `hypothetical_total_quantity` | `null`, or a finite positive canonical decimal |
| `activation_satisfied` | strict boolean — **candidate-level** (Section 6.4/12.2), distinct from the opportunity-level field of the same name (Section 6.3/7.1) |
| `invalidation_satisfied` | strict boolean — candidate-level |
| `expires_at_utc` | ISO-8601 UTC, contract-approved canonical format |

Geometry rules (validated per candidate; a failing candidate is not
rejected from the input — it is derived into a `TRL_VIRTUAL_OPPORTUNITY.v1`
with `state = REJECTED`, Section 12.2):

- **BUY:** `stop_price < entry_trigger`; every `target_price >
  entry_trigger`; `target_prices` strictly increasing.
- **SELL:** `stop_price > entry_trigger`; every `target_price <
  entry_trigger`; `target_prices` strictly decreasing.

Unknown fields fail closed. Candidate IDs and hashes are always
service-derived (Section 8.4) — an input may never supply or override
`virtual_opportunity_id` or any canonical hash.

### 11.2 Exact reward/risk formulas

Using `snapshot_mid_price = quantize_4((high + low) / Decimal("2"))`
(Section 6.1) as the current research reference price:

```
risk_distance = abs(entry_trigger - stop_price)     # must be > 0
```

For each target `i` with price `target_price_i` and allocation
`target_allocation_i`:

```
target_reward_distance_i = abs(target_price_i - entry_trigger)

weighted_reward_distance = sum(
    target_reward_distance_i * (target_allocation_i / Decimal("100.0000"))
    for i in targets
)

reward_risk_ratio = quantize_4(weighted_reward_distance / risk_distance)

distance_to_market = quantize_4(abs(entry_trigger - snapshot_mid_price))
```

`reward_risk_ratio` becomes `TRL_VIRTUAL_OPPORTUNITY.v1.expected_reward_risk_ratio`
exactly (Section 6.4) — not an independent estimate.

### 11.3 Deterministic ranking

Bounds unchanged: `LATTICE_MIN_SIZE = 1`, `LATTICE_MAX_SIZE = 6`,
`MAX_SELECTED_FOR_PREVIEW = 1` (Section 12.1). Ranking, most-preferred
first, over every valid (non-`INVALIDATED`, non-`EXPIRED`) derived virtual
opportunity:

1. `reward_risk_ratio` descending.
2. `distance_to_market` ascending.
3. `virtual_opportunity_id` ascending (final, fully deterministic
   tie-break).

`rank` is assigned `1..N` in this order **by the service only** — no
user-supplied rank field exists anywhere in the input envelope (Section
11.1), and none is ever authoritative.

## 12. Virtual Opportunity Lattice

### 12.1 Bounds

`LATTICE_MIN_SIZE = 1`, `LATTICE_MAX_SIZE = 6` virtual opportunities per
opportunity card. `MAX_SELECTED_FOR_PREVIEW = 1` — at most one virtual
opportunity per card may carry state `SELECTED_FOR_PREVIEW` at a time.
Constructing or listing the lattice, and generating a preview from it, both
require the `market_intelligence_research` capability (Section 5.1) — the
read-only `list-virtual-opportunities`/`inspect-virtual-opportunity`
lookups do not. No level is ever hidden from the lattice listing regardless
of `state`.

### 12.2 Exact state derivation (first-match, per candidate)

1. `expires_at_utc` already passed -> **`EXPIRED`**.
2. Else `invalidation_satisfied == true` (candidate-level) ->
   **`INVALIDATED`**.
3. Else the candidate's geometry or research consistency fails
   (Section 11.1) -> **`REJECTED`**.
4. Else `activation_satisfied == false` (candidate-level) ->
   **`WATCHING`**.
5. Else -> **`ACTIVATED`**.

Each state is recorded as its own immutable `MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED`
journal event — the canonical record (excluding `state`, per Section 6.4)
is never rewritten in place; `state` is a mutable lifecycle projection
reconstructed from the event history, exactly like Phase 5/6's own
projection conventions.

### 12.3 Selection for preview

After the opportunity's own decision (Section 10.4) is computed:

- **Selection is permitted only when the opportunity's `final_status ==
  TRADE_CANDIDATE`.** `WAIT`, `REJECT`, `BLOCKED`, and `EXPIRED` decisions
  select zero records — no preview exists for them.
- At most one `ACTIVATED` record may be changed, in an immutable selection
  projection (its own `MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED` event, target
  state `SELECTED_FOR_PREVIEW`), never by mutating an earlier canonical
  record in place.
- Selection uses the deterministic ranking of Section 11.3 — rank `1`
  among `ACTIVATED` candidates, if any exist; if none is `ACTIVATED`, no
  selection occurs even for a `TRADE_CANDIDATE` decision.
- `SELECTED_FOR_PREVIEW` means selected only for visual research preview
  (Section 13) — it never produces execution authority of any kind.

## 13. Non-executable basket preview

A read-only research projection of the `SELECTED_FOR_PREVIEW` virtual
opportunity (Section 6.7's full closed schema). **Preview generation
requires the `market_intelligence_research` capability** (Section 5.1) —
the same gate as opportunity/decision/lattice creation.

### 13.1 Behavior

Copies `entry_trigger`/`stop_price`/`ordered_target_prices`/
`ordered_target_allocations` directly from the selected virtual
opportunity's originating candidate input (Section 11.1) — the allocations
are **never recomputed or redistributed**; they were already validated to
sum to exactly `100.0000` at input time.

### 13.2 Quantity conservation (Founder-finalized — fail-closed, no redistribution)

For V0 preview quantities only: canonical quantity precision is **up to
eight decimal places**, no exponent notation, no broker minimum/maximum/step
is implied, and no quantity is executable. When `hypothetical_total_quantity`
is supplied:

```
child_quantity_i = hypothetical_total_quantity * target_allocation_i / Decimal("100.0000")
```

- Each `child_quantity_i` must be **exactly representable** at up to 8
  decimal places.
- The child quantities must **sum exactly** to `hypothetical_total_quantity`
  — **no residue redistribution, no hidden child, no zero child.**
- If any result requires more than 8 decimal places for exact
  representation, or the sum does not conserve exactly, **preview creation
  fails closed** with `MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE`
  — the service never rounds or redistributes to force conservation.
- When `hypothetical_total_quantity` is `null`, `ordered_hypothetical_child_quantities`
  is also `null`.

### 13.3 Boundary restated

Never `TRL_BASKET_PLAN.v1` or `TRL_BASKET_CHILD_INTENT.v1`; never written
into the Phase 5/6 execution journal; Phase 6 requires no source change to
reject it (Section 6.7). SMA-001/FIB-001 remain blocked identically to
Section 10.3. Any future conversion into a real basket requires a separate,
explicitly Founder-approved handoff contract (Section 5).

## 14. Learning telemetry

### 14.1 What may be recorded

Original decision preservation (`original_decision_status` — one of
`TRADE_CANDIDATE, WAIT, REJECT, BLOCKED`; an `EXPIRED` opportunity records
telemetry against whatever `final_status` its last real decision held
before expiry, never `EXPIRED` itself), point-in-time evidence preservation
(via the pinned `opportunity_id`/`canonical_opportunity_hash`), the
observation window, result after estimated costs, MFE/MAE, decision
calibration (`calibration_bucket`), false-positive/false-negative research
classification (`outcome_classification`), missing-outcome status, and
regime-specific grouping (`regime_at_recording`).

### 14.2 What telemetry must never do

It must not automatically change a decision threshold in Section 10.2,
promote a rule, authorize a strategy, deploy a model, modify source code,
or modify any Phase 6 permission. Future champion/challenger learning
requires another contract, not this one.

### 14.3 Immutability

Telemetry is append-only. Recording an outcome never rewrites the
originating `TRL_OPPORTUNITY_CARD.v1` or `TRL_OPPORTUNITY_DECISION.v1` — a
correction, if ever needed, is a new telemetry record referencing the same
`opportunity_id`, never an edit of an old one.

## 15. Local CLI and read-only HTTP routes

### 15.1 CLI (local-only, contract-approved command shapes)

Commands requiring the `market_intelligence_research` capability (denied
outright, fail-closed, if the current mode is not `RESEARCH`,
`SYNTHETIC_PAPER`, or `MT5_DEMO_MANUAL` — Section 5.1/5.2):

- `analyze-market-snapshot <input-json-path>` (creates evidence/opportunity/
  decision/lattice records — exact input-safety rules below)
- `preview-opportunity-basket <opportunity_id>`
- `record-opportunity-outcome <opportunity_id> <outcome-fixture-path>`

Commands available regardless of mode, including `OFF` (pure read, no
mutation):

- `market-intelligence-status`
- `list-opportunities [--status <status>]`
- `inspect-opportunity <opportunity_id>`
- `list-virtual-opportunities <opportunity_id>`
- `inspect-virtual-opportunity <virtual_opportunity_id>`
- `market-intelligence-journal [--since <event_id>]`

Only the three capability-gated CLI/service calls above may mutate the
Market Intelligence journal. No HTTP route ever does (Section 15.2).

### 15.2 Exact `analyze-market-snapshot` input-safety rules (Founder-finalized)

- Exactly one local path argument.
- Maximum file size: **262144 bytes**.
- Must be a regular file — never a directory, device path, network/UNC
  path, URL, archive, or symlink/reparse-point traversal (where the
  platform exposes it).
- Strict UTF-8 JSON; duplicate JSON object keys rejected; the exact
  Section 7 envelope schema is required — no other shape is accepted.
- Input bytes are read exactly once.
- No executable content in the file is ever evaluated.
- Only a bounded logical source label is stored (Section 6.2/7.2) — never
  the absolute input file path.
- The CLI writes governed records only through the authoritative service
  and the Market Intelligence journal — never directly.

### 15.3 HTTP routes (strictly read-only)

- `GET /api/market-intelligence-status`
- `GET /api/market-opportunities`
- `GET /api/market-opportunity/<safe-id>`
- `GET /api/virtual-opportunities`
- `GET /api/market-intelligence-telemetry`

`<safe-id>` is validated against the exact `opportunity_id` format
(`^opp_[0-9a-f]{32}$`) before any lookup — never interpolated into a
filesystem path or query string unescaped. Any non-`GET` method on any of
these five routes returns HTTP 405. No route may generate an executable
order, create a Phase 6 basket, confirm, send, alter an execution journal,
or activate a mode. All five routes remain available regardless of mode.

## 16. Application experience (future panel; no code yet)

The future V0 panel must clearly show: **TRL CORTEX V0**, **RESEARCH
ONLY**, **LIVE EXECUTION DISABLED**, **NOT FINANCIAL ADVICE**; current
snapshot; market regime; opportunity cards; the five decision statuses with
their supporting/contradicting evidence, uncertainty, data quality, and
estimated transaction-cost impact; the virtual opportunity lattice; the
selected basket preview; learning telemetry; and the SMA/FIB blockers. No
promotional claim (guaranteed profit, guaranteed accuracy, "90% win rate",
"risk-free", "AI always knows", "automatic wealth") may appear anywhere. No
browser-computed value is authoritative. No `innerHTML` use.

## 17. Storage and audit

A new, bounded, append-only **Market Intelligence journal**
(`market_intelligence_journal.py`, mirroring `mt5_execution_journal.py`'s
architecture), separate from the authoritative Phase 5/6 execution journal.
It follows the identical safety principles: canonical event records, hash
chaining, atomic persistence, a bounded size ceiling, strict validation,
fail-closed corruption handling, cross-process locking via the existing
`_CrossProcessFileLock` pattern, owner-token lock safety, no unlocked
fallback, and a reload of the journal from disk immediately after lock
acquisition. Loading the journal must never make an external call or take a
market action.

### 17.1 Event vocabulary (closed, additive to nothing — this is a new journal)

`MI_SNAPSHOT_RECORDED`, `MI_OPPORTUNITY_CREATED`, `MI_OPPORTUNITY_REUSED`,
`MI_EVIDENCE_RECORDED`, `MI_DECISION_RECORDED`, `MI_LATTICE_CREATED`,
`MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED`, `MI_BASKET_PREVIEW_CREATED`,
`MI_TELEMETRY_RECORDED`, `MI_RECORD_REJECTED`,
`MI_JOURNAL_INTEGRITY_FAILURE`.

## 18. Data input boundary

### 18.1 Canonical instrument and timeframe allowlists (Founder-final)

**Canonical V0 instrument identifiers (exact, uppercase, stored form):**
`XAUUSD`, `NAS100`, `EURUSD`, `GBPUSD`, `USDJPY`.

**Canonical V0 timeframe identifiers:** `M5`, `M15`, `H1`, `H4`, `D1`.

Rules:

1. Stored identities must use these exact uppercase canonical values.
2. Input aliases (`XAU/USD`, `GOLD`, `US100`, `USTEC`, `EUR/USD`, etc.) are
   **not** automatically guessed or silently normalized in V0.
3. An unsupported instrument fails closed with
   `MARKET_INTELLIGENCE_INSTRUMENT_NOT_ALLOWED` (Section 10.4, step 2).
4. An unsupported timeframe fails closed with
   `MARKET_INTELLIGENCE_TIMEFRAME_NOT_ALLOWED` (Section 10.4, step 3).
5. Expanding either allowlist requires a later, separately Founder-approved
   contract amendment.
6. These identifiers are research identifiers only — never passed to an
   adapter, MetaTrader5, or a broker.

### 18.2 Local input validation

May use: committed synthetic fixtures, isolated temporary test fixtures,
local user-supplied JSON, and future historical replay input. Must not
require: a live broker, MetaTrader5, TradingView, paid APIs, external AI
credits, news APIs, or external network access of any kind. Every
`analyze-market-snapshot` input additionally follows Section 15.2's exact
input-safety rules (size limit, regular-file-only, strict UTF-8 JSON, no
duplicate keys, exact envelope schema, no path disclosure).

## 19. Blockers (Founder-finalized precise scoping)

New blockers added to `TRL_BLOCKERS.md`, each scoped to apply **only** when
the specific prohibited capability is actually being attempted:

### 19.1 SMA blocker (narrowly scoped)

`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` applies **only when
`strategy_id == "SMA-001"`**.

### 19.2 FIB blocker (narrowly scoped)

`STRATEGY_PARAMETERS_NOT_APPROVED` applies **only when
`strategy_id == "FIB-001"`**.

### 19.3 Generic V0 research identity

Founder-approved research heuristic identifier: **`CORTEX-V0-HEURISTIC`**,
version **`1.0.0`**. Not a production strategy, not approved for execution,
not evidence of profitability, not authorized for broker handoff. Default
`strategy_id` on every `TRL_OPPORTUNITY_CARD.v1` that cites no specific
registered strategy.

### 19.4 `INTELLIGENCE_SCORING_NOT_VALIDATED` (precisely scoped)

Blocks marketing scoring as validated predictive performance, authorizing
execution, or promoting a production strategy. **Does not prevent**
internal `TRADE_CANDIDATE`/`WAIT`/`REJECT` research classification.

### 19.5 `EXECUTION_HANDOFF_NOT_APPROVED` (precisely scoped)

Blocks only conversion of a CORTEX V0 record into a Phase 5 order intent, a
Phase 6 basket, a confirmation request, or a broker instruction (the
literal value stored in every preview's `execution_handoff_status` field,
Section 6.7).

### 19.6 Other new blockers (retained, precisely scoped)

| Blocker | Blocks (only) |
|---|---|
| `LIVE_MARKET_DATA_NOT_APPROVED` | A live/streaming market-data source for `TRL_MARKET_SNAPSHOT.v1` construction |
| `AUTOMATIC_LEARNING_NOT_APPROVED` | An automatic threshold/rule/strategy change from telemetry |
| `STRATEGY_PROMOTION_NOT_APPROVED` | Automatic promotion of a strategy or model |
| `NEWS_SENTIMENT_SOURCE_NOT_APPROVED` | A news/sentiment evidence source beyond the already-governed Phase 4 News/Event contract |
| `MACRO_DATA_SOURCE_NOT_APPROVED` | A macro/economic-calendar data source as an evidence input |

None of these seven new blockers, nor `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`/
`STRATEGY_PARAMETERS_NOT_APPROVED`, is resolved by this checkpoint.

## 20. Capability requirement summary

`market_intelligence_research` grants no `order_check`, `order_send`,
`manual_broker_execution`, `manual_basket_execution`, `basket_execution`,
live execution, automated execution, or execution handoff.
`ModeService` remains the sole capability authority.

## 21. Tonight-ready implementation boundary

**The first V0 implementation may demonstrate:**

- Loading one validated local JSON analysis-input envelope (Section 7).
- Generating one Opportunity Card, one deterministic decision, up to six
  virtual opportunities, one non-executable preview selection, two-to-four
  preview targets, and hypothetical outcome telemetry.
- Showing all records in the local dashboard.

**It does not need, and is not authorized, to build in this first pass:**
live data; automatic evidence extraction; news ingestion beyond the
already-governed Phase 4 source; macro ingestion; AI APIs; broker
connection; strategy promotion; execution conversion.

### 21.1 Required demonstration fixture

The future implementation must include one clearly labeled committed
synthetic demonstration bundle covering: one approved instrument, one
approved timeframe, one proposed side, all eleven evidence categories, a
`TRADE_CANDIDATE` result, between three and six virtual candidate inputs,
one selected preview with three preview targets, a hypothetical quantity or
`null`, and no live-data, accuracy, or execution-authority claim. The
fixture must state prominently:

> **SYNTHETIC RESEARCH EXAMPLE — NOT LIVE MARKET DATA — NON-EXECUTABLE**

It must not contain fabricated broker account information.

This limitation is intentional and supports accelerated delivery — not a
defect to fix within V0's own scope; expanding it requires a separate
contract amendment.

## 22. Implementation acceptance requirements (future checkpoint)

The future implementation must pass tests covering at minimum: all seven
governed schemas' closed-field enforcement and unsupported-version
rejection, plus the transport-only envelope's own closed-field enforcement
and its explicit non-persistence as a governed record; non-finite-value
rejection on every numeric field; the exact canonical instrument allowlist
(`XAUUSD, NAS100, EURUSD, GBPUSD, USDJPY`) and timeframe allowlist (`M5,
M15, H1, H4, D1`) with unsupported aliases failing closed and no silent
normalization; deterministic IDs and hashes recomputing identically across
restarts and processes; no circular identity (including that
`TRL_EVIDENCE_ITEM.v1` carries no `opportunity_id` field, and that
`virtual_opportunity_id` does not depend on `rank`); snapshot/opportunity
reuse; exactly one evidence item per category (missing, duplicate, and
individually-expired all fail closed with distinct reason codes); `Decimal`
arithmetic and `ROUND_HALF_EVEN` used throughout, never binary float, for
every canonical score; the exact four-decimal `effective_evidence_score`,
`supporting_score`/`contradiction_score` (fixed denominator `5`),
`uncertainty_score` (fixed denominator `11`) formulas; cost/event-risk/
risk-exposure severity interpretation; the exact 23-step decision order
with every one of `TRADE_CANDIDATE`/`WAIT`/`REJECT`/`BLOCKED`/`EXPIRED`
reachable via a dedicated fixture; BUY and SELL virtual-candidate geometry
validation; the exact `weighted_reward_distance`/`reward_risk_ratio`/
`distance_to_market` formulas; deterministic ranking (all three tie-break
levels) with no user-supplied rank ever authoritative; the exact
first-match virtual-opportunity state derivation order; that only a
`TRADE_CANDIDATE` decision may select a preview and at most one preview is
ever selected; that virtual-opportunity state history is event-derived, not
an in-place canonical rewrite; the closed `TRL_MARKET_INTELLIGENCE_BASKET_PREVIEW.v1`
schema rejected naturally by Phase 6 due to its distinct `schema_version`;
exact preview quantity conservation (fails closed with
`MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE` rather than
rounding/redistributing when not exactly representable at 8 dp); a fixture
proving generic CORTEX research is never blocked by the SMA/FIB registry
gate, and dedicated fixtures proving SMA-001/FIB-001 each remain blocked; a
test proving `INTELLIGENCE_SCORING_NOT_VALIDATED` permits research
classification but blocks execution-authority claims; a test proving
`EXECUTION_HANDOFF_NOT_APPROVED` blocks every Phase 5/6 conversion; a test
proving `market_intelligence_research` exists only in `RESEARCH`/
`SYNTHETIC_PAPER`/`MT5_DEMO_MANUAL`; a test proving `OFF` still permits
every read-only CLI/HTTP operation; the exact `analyze-market-snapshot`
input-safety rules (size limit, regular-file-only, no duplicate JSON keys,
no path/URL/archive/symlink traversal, no path disclosure); no broker order
or adapter call anywhere in the test run; the one required synthetic
demonstration fixture producing its exact expected deterministic records;
telemetry immutability; no automatic threshold change; restart persistence;
journal hash-chain integrity; corruption fail-closed behavior; true
cross-process creation/reuse; lock timeout; no unlocked fallback; read-only
HTTP (405 on mutation, available in every mode); no `innerHTML`; no
external network call; no `MetaTrader5` import anywhere in the Market
Intelligence module tree; no write to the Phase 5/6 execution journal from
any Market Intelligence code path; the full existing Phase 5 and Phase 6
test suites passing unchanged; and a direct assertion that no Phase 7
module or test file exists.

## 23. Authorized document scope (this checkpoint only)

Exactly one new file:

`09_AI_Systems/02_Tools/Trading_Lab/TRL_R2_010_MARKET_INTELLIGENCE_V0_CONTRACT.md`

Modified only where factually required:

1. `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` — the narrow
   `market_intelligence_research` capability amendment (Section 5.2).
2. `TRL_FULL_VISION_MASTER_PROGRAM.md` — the informational Phase 6A row.
3. `TRL_CONTINUATION_STATE.md` — record this correction pass.
4. `TRL_CONTINUATION_STATE.json` — machine-readable twin.
5. `TRL_DECISION_LOG.md` — dated entry recording this pass's decisions.
6. `TRL_BLOCKERS.md` — the seven new blocker rows (Section 19.6), precisely
   scoped.

Expected maximum scope: 1 new, up to 6 modified, 0 deleted. Not modified:
Phase 5 source, Phase 6 source, `mode_service.py`, any test file, any
JavaScript/HTML/CSS file, any existing execution contract, Phase 6
evidence, or `main`.

This is R2-010, not Phase 7, contract-only, Founder-approved as the
governing contract for TRL CORTEX V0, and unimplemented — TRL CORTEX V0
implementation has not started. This checkpoint's exact staged/committed/
pushed state is always determined by Git directly, not restated here as a
fixed value.
