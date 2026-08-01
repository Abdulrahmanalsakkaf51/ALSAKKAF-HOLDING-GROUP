# TRL-R2-009 Controlled Basket Execution Contract

> **DEMO-MANUAL BASKET EXECUTION ONLY — NO AUTOMATED, LIVE, OR UNATTENDED BASKET PATH EXISTS IN THIS CONTRACT — NO AUTOMATED TEST MAY SUBMIT A REAL ORDER**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-009 (implementation checkpoint: Phase 6 — Controlled Basket Execution) |
| Status | **Founder-approved**, governing Phase 6 contract, through four Founder correction passes (`TRL_DECISION_LOG.md` entries 2026-08-01-013 through -016; approval recorded in entry 2026-08-01-017). Design contract only — Phase 6 implementation itself has not started and is deferred to a separate, later checkpoint. |
| Depends on | TRL-R2-005 (paper engine), TRL-R2-006 (signal proposals), TRL-R2-007 (MT5 execution adapter, Phase 5 `MT5_DEMO_MANUAL` slice, committed at `49b8f74`), `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (as narrowly amended alongside this contract) |
| Feeds | Phase 6 implementation (a later checkpoint); Phase 9 (live-automation arming) and Phase 10 (reconciliation) remain independently gated and are not advanced by this contract |

## 0. Numbering decision

This contract is numbered **TRL-R2-009**, not TRL-R2-006 (already governed
signal intelligence, implemented) and not TRL-R2-008 (already exists and
governs a different future checkpoint,
`TRL_R2_008_PRIVATE_ONLINE_OPERATIONS_CONTRACT.md` — Phase 8 private online
and mobile operations, unrelated to baskets). R2-008 is not renamed,
overwritten, reinterpreted, or otherwise modified in substance by this
contract. The implementation checkpoint this contract governs remains named
**Phase 6 — Controlled Basket Execution** in `TRL_FULL_VISION_MASTER_PROGRAM.md`;
only the contract document's `TRL-R2-0XX` number is new. See
`TRL_DECISION_LOG.md` for the dated record of this numbering decision.

## 1. Authority and relationship to prior contracts

This contract governs **only** the controlled, manual, demo-only basket
execution checkpoint (Phase 6). It does not replace, weaken, or duplicate:

- `TRL_R2_007_MT5_EXECUTION_CONTRACT.md` — the single-order execution
  adapter this contract's basket children are ultimately sent through.
  Section 1.1 below states precisely how this contract relates to that
  committed, closed `v1` schema.
- `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` — remains ModeService's sole
  authority over capability grants. Section 6 records the one narrow,
  Founder-approved amendment this contract requires; every other Phase 3
  rule is unchanged.
- `TRL_FULL_SYSTEM_THREAT_MODEL.md` Section 3.6 — the threat/mitigation
  framing this contract implements in full operational detail.

Where this contract is silent, the R2-007 contract and Phase 3 contract
govern. Where a term is defined in both, this contract's definition governs
for basket-specific behavior only; single-order behavior is unchanged.

### 1.1 Phase 5 backward-compatibility guarantee

1. **`TRL_MT5_ORDER_INTENT.v1` remains unchanged.** This contract adds no
   field to `mt5_execution_data.ORDER_INTENT_FIELDS`, changes no validation
   rule in `validate_order_intent`, and changes no computation in
   `execution_intent_lookup_key`, `order_intent_id_for`,
   `execution_attempt_id_for`, `order_intent_hash_for`, or
   `confirmation_challenge_code`. Every existing Phase 5 persisted order
   intent, execution attempt, confirmation, and journal event remains
   readable and valid, byte-for-byte, exactly as Phase 5 left it.
2. Phase 6 introduces **separate, independently versioned basket
   documents** — `TRL_BASKET_PLAN.v1`, `TRL_BASKET_CHILD_INTENT.v1`,
   `TRL_BASKET_CHECK_RESULT.v1`, `TRL_BASKET_CONFIRMATION.v1`,
   `TRL_BASKET_CHILD_EXECUTION_RESULT.v1`, and `TRL_BASKET_STATUS.v1`
   (Sections 9–12, 36). None of these six schemas is `TRL_MT5_ORDER_INTENT.v1`
   under a new name — each is its own closed schema with its own
   `schema_version` string, its own field list, and its own validator.
   Every field this contract's confirmation-cycle design (Section 13)
   needs — `confirmation_basis_hash`, `confirmation_request_id`, ordered
   filled-child/check identities — lives exclusively on
   `TRL_BASKET_CONFIRMATION.v1`; none of it is added to any Phase 5
   document.
3. A basket child **references and derives from** the Phase 5 parent order
   intent (by `order_intent_id` and a pinned content hash — Section 17) but
   never adds a basket-only field to `TRL_MT5_ORDER_INTENT.v1` itself, and
   is never itself validated as, stored as, or represented as a
   `TRL_MT5_ORDER_INTENT.v1` document. A basket child is a
   `TRL_BASKET_CHILD_INTENT.v1` document — structurally parallel to
   (reusing familiar field names and value domains from) the Phase 5
   schema for consistency, but a genuinely separate, independent type.
4. Basket journal events (Section 16) are **additive** to the existing
   `mt5_execution_journal.EVENT_TYPES` tuple. No existing event type's
   schema, validation, or meaning changes. Phase 5's own confirmation
   rules (`confirmation_challenge_code`, `CONFIRMATION_LIFETIME_SECONDS`
   applied to single orders) are unchanged; this contract's confirmation
   design (Section 13) is a Phase-6-owned parallel mechanism that
   references the same `CONFIRMATION_LIFETIME_SECONDS` *value* without
   modifying the Phase 5 function that uses it.
5. If a future version of the Phase 5 order-intent document is ever
   required, that is out of scope for Phase 6 and requires a separate,
   explicitly Founder-approved migration/versioning contract. This
   contract authorizes no such migration.
6. The later Phase 6 implementation checkpoint must include
   backward-compatibility regression tests proving that a corpus of
   existing Phase 5 persisted journals and order intents (recorded before
   any Phase 6 code exists) still loads, validates, and replays unchanged
   after the Phase 6 modules are added (Section 40).

## 2. Scope

In scope for the Phase 6 implementation this contract authorizes:

- Controlled construction of a basket (2–4 children) derived from one
  existing, eligible `MT5_DEMO_MANUAL` order intent's targets and
  allocations, represented as separate `TRL_BASKET_*` documents (Section
  1.1) rather than an extension of the Phase 5 schema.
- Independent, per-child governed `order_check` against the existing
  adapter boundary, using each child's own extracted request parameters.
- A basis-bound local manual basket confirmation whose challenge and
  authorization scope are recomputed whenever the set of already-filled
  children or the set of currently-required fresh checks changes
  (Section 13).
- Strict, service-enforced, single-next-child-at-a-time sending, using the
  existing durable journal, cross-process locking, and duplicate
  protection, with previously filled children permanently protected from
  re-check, re-send, or reset.
- Truthful partial-success, rejection, failure, and uncertain-result
  reporting, with partial-success (basket-level, permanent stop) kept
  distinct both from partial-fill (child-level) and from a recoverable
  stale-check recheck cycle (Section 14).
- A local-only CLI and a read-only HTTP/dashboard surface.
- Extension of the existing Phase 5 execution journal with a closed,
  additive set of new basket event types (Section 16).

## 3. Explicit exclusions

Not in scope for Phase 6, regardless of any apparent convenience:

- `MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`, `MT5_LIVE_AUTOMATED` — remain
  fully unavailable; this contract grants no capability to any of them.
- Automated, scheduled, or unattended basket construction, checking,
  confirmation, or sending.
- Automatic reconciliation (Phase 10) — a frozen/partial basket requires a
  human operator; this contract defines the boundary where Phase 6 stops
  and Phase 10 would begin, and implements none of Phase 10.
- Live-automation arming (Phase 9) — not touched, not activated, not
  referenced as available.
- TradingView webhook intake (Phase 7).
- Private/remote/mobile access (Phase 8, TRL-R2-008).
- Multi-account routing, portfolio-level orchestration, or any
  cross-basket aggregation.
- Any compensation trade, rollback claim, or automatic retry of any kind.
- Broker-side, automatic, or reconciliation-driven cancellation of any
  child order (Section 14.5) — Phase 6 implements none of these, so the
  child-state vocabulary carries no `CANCELLED` value.
- SMA-001 executable geometry approval or FIB-001 numeric parameter
  approval — both blockers remain fully active and are independently
  re-checked before basket construction (Section 42).
- Any change to `mode_service.py`, `mt5_execution_service.py`,
  `mt5_execution_data.py`, `mt5_execution_journal.py`,
  `mt5_execution_adapter.py`, `mt5_execution_cli.py`, `app.py`,
  `server.py`, `service.py`, dashboard files, or any test file. This
  contract-authoring checkpoint changes documentation only; implementing
  the design below is a separate, later checkpoint.
- Any modification, extension, or reinterpretation of `TRL_MT5_ORDER_INTENT.v1`
  or any other Phase 5 `v1` schema, function, or persisted document
  (Section 1.1).

## 4. Terminology

| Term | Meaning |
|---|---|
| **Parent order intent** | An existing, valid `TRL_MT5_ORDER_INTENT.v1` document (Phase 5, unchanged) whose `targets` list has 2–4 entries — the sole input a basket may be derived from. |
| **Basket** | One governed `TRL_BASKET_PLAN.v1` document (Section 9) grouping the deterministic child breakdown of one parent order intent's targets/allocations. Immutable once persisted (Section 17). |
| **Basket child** | One independent `TRL_BASKET_CHILD_INTENT.v1` document (Section 10) representing exactly one of the parent's targets and carrying its own quantity slice. A basket child is **not** a `TRL_MT5_ORDER_INTENT.v1` document and never adds a field to that schema (Section 1.1). |
| **Aggregate risk identity** | `approved_aggregate_risk_id` — the single risk-budget identity shared by every child of one basket, preventing per-child risk from being counted independently of the parent's approved budget. |
| **Confirmation basis** | `confirmation_basis_hash` (Section 13.1) — the exact, deterministically encoded snapshot of the current *execution authority*: the basket, the account, the already-filled children, the currently-required fresh checks, and the next eligible child. Changes whenever any of those change. Contains no per-request timestamp and no cycle number, so it stays identical across a same-basis re-request. |
| **Confirmation cycle** | One immutable, sequentially numbered attempt (`confirmation_cycle_number`, Section 13.1a) to obtain a confirmation for a given basis. The first cycle for a basket is `1`; a new cycle is required every time the active one expires, is invalidated, or the basis changes. Cycle numbers are never reused, decremented, or reset. |
| **Confirmation request** | One `TRL_BASKET_CONFIRMATION.v1` record — one specific confirmation cycle — identified by a deterministic `confirmation_request_id` derived from the basket, its basis, its cycle number, and its own fixed timestamps (Section 13.1b). Once created, a request's identity, challenge, and timestamps never change; only its `status` does. |
| **Partial success** | A basket-level, *permanent* outcome: `PARTIALLY_COMPLETED` — one or more children reached `FILLED` and the basket then stopped for a non-recoverable reason. Distinct from partial fill and from a recoverable stale-check recheck cycle (Section 14.3/14.4). |
| **Partial fill** | A child-level outcome: one specific child's own broker result was `PARTIALLY_FILLED` (less than its full requested quantity filled). Does not by itself imply anything about the basket's other children. |
| **Reconciliation-required** | A derived, orthogonal flag (Section 14.4) — `true` exactly when `basket_status` is `PARTIALLY_COMPLETED` or `FROZEN`. Phase 6 can detect and freeze these states truthfully but not resolve them; resolution is explicitly Phase 10 (Section 33), not implemented here. |

## 5. Operating-mode authority

`ModeService` (`trading_lab_app/mode_service.py`) remains the sole authority
over every basket capability. No basket-mode file, second operating-mode
service, environment-variable bypass, CLI-only override, or browser-side
execution mode may exist. Every governed basket operation independently
calls `ModeService` — no module infers permission from a mode-name string,
a cached capability set, or a prior successful check.

**Phase 6 is available only when the current mode is `MT5_DEMO_MANUAL`.**
`OFF`, `RESEARCH`, and `SYNTHETIC_PAPER` deny every basket-mutating
operation. `MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`, and `MT5_LIVE_AUTOMATED`
remain unavailable exactly as Phase 3 already defines — this contract does
not change their availability, and no basket path may activate, arm, or
otherwise treat any of them as reachable.

## 6. Capability-matrix amendment

The broad `basket_execution` capability (already represented in Phase 3's
schema, granted only to the still-future `MT5_DEMO_AUTOMATED` and
`MT5_LIVE_AUTOMATED` rows) **remains reserved for those future automated
modes and is not granted to `MT5_DEMO_MANUAL` by this contract.** Founder
decision: introduce a narrower, additional capability instead of widening
the broad one.

### 6.1 New capability: `manual_basket_execution`

| Property | Value |
|---|---|
| Name | `manual_basket_execution` |
| Meaning | Manual, demo-only, locally confirmed, non-automated, non-live basket construction/check/confirm/send, subject to every Phase 5 MT5 safeguard and this contract |
| Granted to | `MT5_DEMO_MANUAL` **only** |
| Denied to | `OFF`, `RESEARCH`, `SYNTHETIC_PAPER`, `MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`, `MT5_LIVE_AUTOMATED` — unless a later, separately Founder-approved contract changes this |

`manual_basket_execution` is necessary but never sufficient by itself.
Every basket operation additionally requires the pre-existing capability
its underlying action already needs:

| Basket operation | Required capabilities (all must be granted) |
|---|---|
| Basket construction (create/reuse, no broker call) | `manual_basket_execution` |
| Basket child `order_check` | `manual_basket_execution`, `mt5_order_check` |
| Basket child `order_send` | `manual_basket_execution`, `mt5_order_send`, `manual_broker_execution` |

Because `MT5_DEMO_MANUAL`'s existing capability set already contains
`mt5_order_check`, `mt5_order_send`, and `manual_broker_execution`
(`trading_lab_app/mode_service.py` `_CAPABILITY_MATRIX`), adding
`manual_basket_execution` to that same row is the only capability-matrix
change this contract requires. No other mode's row changes. See Section 44
for the exact, narrow amendment made to `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`.

No CLI flag, environment variable, helper call, HTTP request, or direct
Python entry point may bypass this capability check. Every check is
performed against a freshly resolved `ModeService` state — never cached
across the lifetime of one CLI invocation's individual steps.

## 7. Strategy blockers (unchanged, independently re-enforced)

`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` (SMA-001) and
`STRATEGY_PARAMETERS_NOT_APPROVED` (FIB-001) remain fully active. This
contract approves no SMA entry/stop/target geometry, no SMA target
allocation, and no FIB numeric parameter. A production basket cannot be
constructed from either strategy until a separately Founder-approved
strategy contract resolves the relevant blocker. Basket construction
(Section 20) independently re-checks
`signal_strategy_registry.executable_status(strategy_id)` **and** the
existing Phase 5 `EXECUTION_GEOMETRY_APPROVED_STRATEGIES` allowlist before
ever deriving a child — a hand-built parent order intent cannot bypass
either gate merely because it already exists. A construction attempt that
fails either gate transitions the (would-be) basket to `BLOCKED`
(Section 14), not `REJECTED` — Section 14.3 explains the distinction.
Hypothetical, clearly labeled test-only fixtures may be used in automated
tests and manual fake-adapter rehearsal only (Section 41).

## 8. Parent prerequisites

A basket may be constructed **only** from a parent order intent that
independently satisfies every one of the following, revalidated fresh at
construction time (never trusted from a cached or prior check):

1. The parent order intent validates against `TRL_MT5_ORDER_INTENT.v1`
   (`mt5_execution_data.validate_order_intent`) unchanged. Its
   `schema_version` must equal `"TRL_MT5_ORDER_INTENT.v1"` exactly; any
   other value fails closed with `PARENT_SCHEMA_VERSION_UNSUPPORTED`
   (never assumed forward/backward compatible).
2. `operating_mode == "MT5_DEMO_MANUAL"`.
3. `execution_status == "CREATED"` — a parent that has already reached
   `CHECK_PASSED`, any terminal state, or has any existing single-order
   attempt history is not eligible for basket derivation. A basket is an
   alternative execution path for a multi-target intent, chosen **before**
   any single-order attempt is made under it — never a retrofit onto an
   intent already mid-flight as a single order.
4. `len(targets) == len(target_allocations_percent)` and
   `2 <= len(targets) <= 4` (Founder decision: baskets are 2–4 children;
   a 1-target intent has no basket to build — it executes as a Phase 5
   single order, unchanged).
5. `canonical_proposal_hash` matches an independent re-hash of the
   referenced R2-006 proposal, fetched fresh, not from the stored intent
   alone.
6. The referenced proposal has not expired, and is not `BLOCKED`, `HOLD`,
   or `WAIT`.
7. `strategy_id`/`strategy_version` are registered, enabled, and pass both
   Section 7 blocker gates.
8. `risk_policy_hash` matches the currently governed risk configuration.
9. `account_fingerprint_hash` matches the configured, approved demo
   fingerprint; `ACCOUNT_UNAVAILABLE` fails closed exactly as Phase 5.
10. The parent intent's `expires_at_utc` has not passed.

Any failure fails closed with the specific Section-15 reason code; no
basket is created, persisted, or returned as partially valid.

## 9. Basket schema — `TRL_BASKET_PLAN.v1`

The authoritative, durable, hash-chained-journal-backed document
describing one basket's **immutable plan**. Strict required fields;
unexpected fields rejected. This document never changes after it is first
persisted — every mutable fact about a basket's progress lives in the
separate `TRL_BASKET_STATUS.v1` read model (Section 36) and the individual
`TRL_BASKET_CHILD_INTENT.v1`/check/send-result/confirmation records, never
here.

| Field | Meaning |
|---|---|
| `schema_version` | `"TRL_BASKET_PLAN.v1"` |
| `basket_id` | `"bsk_" + sha256(...)[:32]`, deterministic, **no nonce** (Section 17.2) |
| `basket_lookup_key` | `"blk_" + sha256(...)[:32]`, deterministic, no nonce (Section 17.1) |
| `parent_proposal_id` | the R2-006 proposal ID (`sp_...`) |
| `canonical_parent_proposal_hash` | independently re-verified at construction time |
| `parent_order_intent_id` | the `exi_...` this basket was derived from |
| `canonical_parent_order_intent_hash` | the parent's `canonical_order_intent_hash` at construction time |
| `account_fingerprint_hash` | inherited from parent, unchanged |
| `broker_native_instrument` | inherited from parent, unchanged |
| `side` | inherited from parent, unchanged (`BUY`/`SELL`) |
| `order_type` | inherited from parent, unchanged (`BUY_LIMIT`/`SELL_LIMIT`) |
| `entry_price` | inherited from parent, unchanged |
| `stop_loss` | inherited from parent, unchanged |
| `total_quantity` | the parent's `quantity` — the basket's conserved total |
| `approved_aggregate_risk_id` | `"agg_" + sha256(basket_id)[:32]` — the one shared risk-budget identity for every child |
| `child_count` | integer, `2 <= child_count <= 4`, equal to `len(children)` |
| `children` | ordered list of **immutable plan-only** child descriptors (Section 10.1), index-preserving with the parent's `targets` order — contains no execution-progress field of any kind |
| `strategy_id` | inherited from parent, unchanged |
| `strategy_version` | inherited from parent, unchanged |
| `risk_policy_hash` | inherited from parent, unchanged |
| `operating_mode` | `"MT5_DEMO_MANUAL"` (the only value this contract permits) |
| `created_at_utc` | basket construction timestamp |
| `expires_at_utc` | `min(parent.expires_at_utc, construction_time + governed basket TTL)` — a basket never outlives its parent |
| `canonical_basket_plan_hash` | Section 9.1 |

No credential, no secret account value, and no raw account login/company/
server ever appears in this document — only `account_fingerprint_hash`,
exactly as Phase 5.

### 9.1 Canonical basket-plan hash — immutable fields only

`canonical_basket_plan_hash = sha256(deterministic_json(fields))` where
`fields` is **every field in the table above except `canonical_basket_plan_hash`
itself**. It excludes every mutable fact by construction — check status,
confirmation status, send status, any child execution result, basket
result, rejection history, and journal sequence live exclusively in
`TRL_BASKET_STATUS.v1` (Section 36), `TRL_BASKET_CONFIRMATION.v1`
(Section 12), and the per-child records (Sections 10, 11, 11.1). Because
`TRL_BASKET_PLAN.v1` is persisted once and never mutated,
`canonical_basket_plan_hash` never changes for the lifetime of a basket.

## 10. Basket child schema — `TRL_BASKET_CHILD_INTENT.v1`

A standalone, closed schema — **not** an extension of
`TRL_MT5_ORDER_INTENT.v1` and not a document validated against
`ORDER_INTENT_FIELDS` (Section 1.1). Field names deliberately mirror the
familiar Phase 5 vocabulary for readability, but this is an independent
type with its own `schema_version`, its own validator, and its own
identity derivation (Section 17.3–17.5).

| Field | Meaning |
|---|---|
| `schema_version` | `"TRL_BASKET_CHILD_INTENT.v1"` |
| `basket_id` | the owning basket |
| `canonical_basket_plan_hash_at_creation` | pins the exact basket-plan content this child was derived under |
| `basket_child_id` | Section 17.4 |
| `child_index` | `0`-based, matches this child's position in the parent's `targets` array |
| `parent_order_intent_id` | traceability back to the Phase 5 parent, read-only reference — never mutates the parent |
| `account_fingerprint_hash` / `broker_native_instrument` / `side` / `order_type` / `entry_price` / `stop_loss` / `strategy_id` / `strategy_version` / `risk_policy_hash` / `operating_mode` / `expires_at_utc` | inherited from the basket plan (Section 9), unchanged — identical across every sibling child of one basket |
| `target_price` | this child's own single target, from `targets[child_index]` |
| `target_allocation_percent` | this child's own allocation share, from `target_allocations_percent[child_index]` |
| `child_quantity` | computed per Section 21; exact, never rounded to fit |
| `idempotency_key` | `== basket_child_id` (Section 17.5) |
| `canonical_basket_child_hash` | sha256 of the deterministic-JSON of every field above except this field itself |

A `TRL_BASKET_CHILD_INTENT.v1` document is itself immutable once persisted
— exactly like `TRL_BASKET_PLAN.v1`. Its own execution progress (check
result, send reservation, send result) is tracked in the separate
`TRL_BASKET_CHECK_RESULT.v1` (Section 11) and
`TRL_BASKET_CHILD_EXECUTION_RESULT.v1` (Section 11.1) records, keyed by
`basket_child_id`, never by mutating this document.

Every child preserves, unchanged from the parent/basket plan, exactly:
`account_fingerprint_hash`, `broker_native_instrument`, `side`,
`order_type`, `entry_price`, `stop_loss`, `strategy_id`,
`strategy_version`, `risk_policy_hash`, `operating_mode`,
`expires_at_utc`. A child may differ from its siblings **only** in:
`child_index`/`basket_child_id`, `target_price`,
`target_allocation_percent`, `child_quantity`,
`canonical_basket_child_hash`. No other field may vary. Basket
construction that would require any other field to differ fails closed
with `BASKET_ECONOMIC_MEANING_CHANGED` (Section 15) rather than silently
permitting the divergence.

### 10.1 Immutable plan-only child descriptor (embedded in `TRL_BASKET_PLAN.v1.children`)

A strictly smaller projection than the full `TRL_BASKET_CHILD_INTENT.v1`
document above — this is what actually appears inside the basket plan's
`children` list and therefore inside `canonical_basket_plan_hash`:
`{child_index, basket_child_id, target_price, target_allocation_percent, child_quantity}`.
No execution-progress field is ever added to this projection.

## 11. Basket check-result schema — `TRL_BASKET_CHECK_RESULT.v1`

A basket-owned, standalone schema (not a reuse of Phase 5's
`TRL_MT5_ORDER_CHECK_RESULT.v1`, since a basket child is not an order
intent — Section 1.1). One record per child per check attempt:

| Field | Meaning |
|---|---|
| `schema_version` | `"TRL_BASKET_CHECK_RESULT.v1"` |
| `check_result_id` | `"bcr_" + sha256("TRL-BASKET-CHECK.v1\n" + basket_id + "\n" + basket_child_id + "\n" + canonical_basket_child_hash_at_check + "\n" + checked_at_utc)[:16]` — deterministic identity for this specific check attempt (Section 13.1 binds confirmations to this exact value, not to a re-derivable summary) |
| `basket_id` / `basket_child_id` | identity |
| `canonical_basket_child_hash_at_check` | pins the exact child content this check was run against |
| `checked_at_utc` | timestamp of this specific check attempt |
| `check_outcome` | one of `("PASSED", "FAILED", "MALFORMED")` — a basket-owned closed vocabulary, textually aligned with Phase 5's `CHECK_OUTCOMES` for familiarity but independently defined |
| `reason_codes` | bounded list, drawn from `BASKET_REASON_CODES` (Section 15) |
| `canonical_basket_check_hash` | `sha256(deterministic_json({basket_id, basket_child_id, canonical_basket_child_hash_at_check, checked_at_utc, check_outcome}))` — the value bound into a confirmation's `ordered_required_check_hashes` (Section 13.1) |

A basket-level rollup (`all_required_children_passed`, current freshness
per child) is computed on demand from the latest `TRL_BASKET_CHECK_RESULT.v1`
per `basket_child_id` — it is not itself a separately persisted document.
"Required" here always means *currently required*: a child that has
already reached `FILLED` is never re-checked and is never part of the
required set again (Section 24.2).

## 11.1 Basket child execution-result schema — `TRL_BASKET_CHILD_EXECUTION_RESULT.v1`

Not a reuse of Phase 5's `TRL_MT5_ORDER_SEND_RESULT.v1`, since that schema
is scoped to `order_intent_id`/`execution_attempt_id`, which basket
children do not have (Section 1.1).

| Field | Meaning |
|---|---|
| `schema_version` | `"TRL_BASKET_CHILD_EXECUTION_RESULT.v1"` |
| `basket_id` / `basket_child_id` | identity |
| `canonical_basket_child_hash_at_send` | pins the exact child content this send reservation/result belongs to |
| `send_reserved_at_utc` | when the durable reservation (Section 26, step 9) was persisted |
| `send_outcome` | one of `("FILLED", "PARTIALLY_FILLED", "REJECTED", "UNCERTAIN", "MALFORMED")` — basket-owned, textually aligned with Phase 5's `SEND_OUTCOMES` for familiarity but independently defined |
| `broker_response_hash` | sha256 of the normalized, sanitized broker response payload |
| `filled_quantity` | nullable; present when a fill occurred |
| `broker_order_ticket` / `broker_deal_ticket` / `broker_position_ticket` | nullable; present only on a confirmed successful/partial result, never fabricated on an uncertain one |
| `result_recorded_at_utc` | when this result was normalized and persisted |

Once a `TRL_BASKET_CHILD_EXECUTION_RESULT.v1` record reaches
`send_outcome == "FILLED"`, it is **permanently immutable** — no later
basket operation (a stale-check recheck cycle, a fresh confirmation, a
restart) ever creates, replaces, or supersedes it (Section 24.2, Section
27).

## 12. Basket confirmation schema — `TRL_BASKET_CONFIRMATION.v1`

See Section 13 for the full derivation, syntax, and lifecycle. Every field
this schema needs is Phase-6-owned; none of it is added to any Phase 5
document (Section 1.1). One persisted record is one immutable-once-created
confirmation cycle (Section 4) — a new cycle is always a **new** record,
never a rewrite of an old one.

| Field | Meaning |
|---|---|
| `schema_version` | `"TRL_BASKET_CONFIRMATION.v1"` |
| `confirmation_request_id` | `"creq_" + sha256(...)[:32]`, deterministic, no nonce, computed once at cycle creation (Section 13.1b) |
| `confirmation_cycle_number` | positive integer, `1` for the basket's first cycle, strictly increasing thereafter, immutable once assigned (Section 13.1a) |
| `basket_id` | the basket this confirmation is for |
| `canonical_basket_plan_hash` | the immutable plan hash (unchanging for this basket's lifetime) |
| `confirmation_basis_hash` | Section 13.1 |
| `account_fingerprint_hash` | the account fingerprint this basis was computed against |
| `authorized_prior_filled_child_ids` | ordered list of `basket_child_id` — every child already `FILLED` **before** this cycle was requested (Section 13.1.1a). Normally empty for a basket's first cycle. An **immutable snapshot**, fixed at cycle-request time; never updated as later fills occur during this same cycle. |
| `authorized_remaining_child_ids` | ordered list of `basket_child_id` — the **complete** set of unsent children this cycle, once accepted, may authorize sending, in sequence (Section 13.1.1b). An immutable snapshot; a child leaving this list never happens mid-cycle merely because it filled — it stays listed, and progress is tracked separately via live journal state (Section 26). |
| `authorized_start_child_id` | the lowest-`child_index` member of `authorized_remaining_child_ids` at the moment this cycle was requested (Section 13.1.1c) — the first child eligible under this cycle. Informational: it is **not** required to remain the *live* next-eligible child once normal successful progression begins (Section 26). |
| `ordered_required_check_ids` | ordered list of `check_result_id` (Section 11) — one per member of `authorized_remaining_child_ids`, the exact successful check attempt this cycle relies on for that child |
| `ordered_required_check_hashes` | ordered list of the matching `canonical_basket_check_hash` values, positionally aligned with `ordered_required_check_ids` |
| `challenge_derivation_version` | `"TRL-BASKET-CONFIRM.v1"` — the exact domain-separator string used in Section 13.1c, recorded for forward traceability |
| `challenge_hex` | the 16-lowercase-hex-character value the operator must retype (Section 13.1c), immutable once assigned |
| `requested_at_utc` | when this specific cycle's record was created — immutable; never changed, including on reuse (Section 13.3) |
| `expires_at_utc` | `requested_at_utc + CONFIRMATION_LIFETIME_SECONDS` (the existing Phase 5 `mt5_execution_service.CONFIRMATION_LIFETIME_SECONDS = 300` constant, referenced unchanged) — immutable once assigned |
| `status` | one of `("REQUESTED", "ACCEPTED", "INVALIDATED", "EXPIRED")` — the only mutable field group on this record, together with the three timestamp/reason fields below |
| `accepted_at_utc` | nullable; populated only on acceptance |
| `expired_at_utc` | nullable; populated the moment this cycle's expiry is materialized (Section 13.3, Section 13.6) — once set, this record is permanently terminal and is never touched again |
| `invalidated_at_utc` / `invalidation_reason` | nullable; populated per Section 13.6, `invalidation_reason` drawn from `BASKET_REASON_CODES` |
| `canonical_confirmation_request_hash` | Section 12.1 |

The entered confirmation phrase (Section 13.2) is never stored as a secret
and is not a credential — it is a content-derived binding code, safe to
appear in `challenge_hex`, in CLI output, and in journal payloads
(Section 39).

### 12.1 Canonical confirmation-request hash — immutable identity only

`canonical_confirmation_request_hash = sha256(deterministic_json(fields))`
where `fields` is every field on this schema **except**
`canonical_confirmation_request_hash` itself, `status`, `accepted_at_utc`,
`expired_at_utc`, `invalidated_at_utc`, and `invalidation_reason` — i.e.
exactly the *immutable request-cycle identity* (`confirmation_request_id`,
`confirmation_cycle_number`, `basket_id`, `canonical_basket_plan_hash`,
`confirmation_basis_hash`, `account_fingerprint_hash`,
`authorized_prior_filled_child_ids`, `authorized_remaining_child_ids`,
`authorized_start_child_id`, the ordered required-check lists,
`challenge_derivation_version`, `challenge_hex`, `requested_at_utc`,
`expires_at_utc`). The five excluded fields are the record's *mutable
lifecycle status*, tracked separately — mirroring exactly the
`canonical_basket_plan_hash` pattern (Section 9.1): identity is hashed
once, at creation, and never changes for the life of that cycle; status
changes freely without ever touching the identity hash, and a status
change is never represented by rewriting the record's identity fields —
only by an append-only journal event (Section 16) plus the status/
timestamp/reason fields above.

## 13. Basket confirmation — basis, cycle, derivation, syntax, and lifecycle

### 13.1 Confirmation basis hash — an immutable authorization checkpoint

*Corrected: an earlier draft of this contract bound `confirmation_basis_hash`
to `ordered_filled_child_ids` and `next_eligible_child_id` as **live,
continuously changing** values, re-derived and re-compared against the
current journal state at every send. Because a basket's Section 13.4.1
design already required one accepted confirmation to authorize a
**sequence** of child sends, and every successful fill necessarily changes
the live filled-child set and the live next-eligible child, that draft
would have invalidated the confirmation the instant the first child
filled — contradicting the one-confirmation-per-basket-cycle design it
also claimed to implement. This section replaces that draft: the basis is
now a fixed **authorization checkpoint**, computed once at the moment a
confirmation is requested, never recomputed against a moving target
during normal progression.*

The basis is computed **once**, at `request-basket-confirmation` time
(Section 13.3), from exactly:

| Field | Meaning |
|---|---|
| `basket_id` | — |
| `canonical_basket_plan_hash` | — |
| `account_fingerprint_hash` | freshly re-verified at request time, not cached |
| `authorized_prior_filled_child_ids` | Section 13.1.1(A) |
| `authorized_remaining_child_ids` | Section 13.1.1(B) |
| `authorized_start_child_id` | Section 13.1.1(C) |
| `ordered_required_check_ids` / `ordered_required_check_hashes` | Section 13.1.1(D) |
| `operating_mode` | `"MT5_DEMO_MANUAL"` |
| `confirmation_lifetime_seconds` | the *value* of the existing Phase 5 `CONFIRMATION_LIFETIME_SECONDS` constant (`300`), bound by value, not by any per-request timestamp |

```
confirmation_basis_hash = sha256(deterministic_json(above fields))
```

**This hash deliberately excludes:** the basket's live/current
`basket_status`; the live, continuously advancing next-eligible-child
projection (Section 26); any child result generated after this
confirmation is accepted; journal append sequence; the confirmation
record's own mutable lifecycle `status`; and any random value. It contains
no per-request timestamp and no cycle number either (those live on
`confirmation_request_id` instead — Section 13.1a–13.1b). **Once computed,
this hash is fixed for the life of this cycle and is never recomputed
against a later, more-advanced live state** — Section 13.4's acceptance
check re-verifies it only against the state *at the moment of acceptance*
(which always precedes the first child send of this cycle), never again
afterward during the sequential sends that follow (Section 13.4.1,
Section 26). Basis identity and confirmation-*cycle* identity (Section
13.1a–13.1b) remain two separate concepts: the same unchanged basis can
still legitimately span more than one cycle (an expired-and-reissued cycle
for that same basis — Section 13.3).

### 13.1.1 Authorization-checkpoint fields — precise definitions

All four fields below are computed once, at `request-basket-confirmation`
time, from the durable journal, and become part of the immutable basis —
none of them is ever recomputed or mutated for the life of this cycle.

**(A) `authorized_prior_filled_child_ids`** — the ordered `basket_child_id`
list of every child that had already reached `FILLED` **before** this
confirmation cycle was requested. For a basket's first confirmation cycle
this list is normally empty (no child could have filled before any
confirmation ever existed). For a cycle created after a prior cycle's
children partially progressed (Section 13.3, new-cycle-after-invalidation),
this list contains exactly those earlier-filled children — permanently,
truthfully, and it is never revised as *this* cycle's own children later
fill.

**(B) `authorized_remaining_child_ids`** — the complete ordered
`basket_child_id` list of every child **not yet** `FILLED` at the moment
this cycle is requested (i.e. every basket child minus
`authorized_prior_filled_child_ids`). This is the entire set one accepted
cycle may authorize sending, **in sequence, one at a time** (Section 26) —
not merely "the next one." A child remains listed here for the whole
cycle even after it fills; live progress within the cycle is tracked
separately (Section 26), never by shrinking this immutable list.

**(C) `authorized_start_child_id`** — the lowest-`child_index` member of
`authorized_remaining_child_ids`, i.e. the first child eligible for sending
under this cycle. Purely informational/display (Section 36) once the cycle
is accepted: the contract does **not** require the *live* next-eligible
child (Section 26) to keep equaling this field as normal successful
progression advances past it.

**(D) `ordered_required_check_ids` / `ordered_required_check_hashes`** —
for every member of `authorized_remaining_child_ids`, in the same order,
that child's exact current `check_result_id`/`canonical_basket_check_hash`
(Section 11) at the moment this cycle is requested. All of
`authorized_remaining_child_ids` must have a successful, fresh check
before a confirmation may be requested at all (`BASKET_NOT_CHECK_COMPLETE`
otherwise — Section 13.3).

### 13.1a Confirmation cycle number — durable, monotonic, never reused

`confirmation_cycle_number` is a positive integer, unique per basket,
allocated **only** at the moment a genuinely new `TRL_BASKET_CONFIRMATION.v1`
record is created (Section 13.3):

1. The first confirmation-request record ever created for a `basket_id`
   uses cycle number `1`.
2. Every subsequent new cycle for that same `basket_id` uses
   `(highest confirmation_cycle_number ever recorded for this basket_id, across every status) + 1`
   — computed by scanning the durable journal for every
   `TRL_BASKET_CONFIRMATION.v1` record belonging to this `basket_id`,
   under the cross-process lock (Section 19), and reloading from disk
   before deciding.
3. Repeated invocation while the current cycle remains active (Section
   13.3, reuse case) returns that same cycle number unchanged — it is
   never incremented merely because `request-basket-confirmation` was
   called again.
4. Cycle-number allocation is atomic under the cross-process lock: two
   concurrent `request-basket-confirmation` invocations for the same
   basket can allocate at most one new cycle number between them (the
   loser resolves to the winner's newly created record instead, exactly
   like every other lookup-before-create pattern in this contract).
5. Cycle numbers are **never reused, decremented, or reset** — not across
   restart, not across a corrupted-then-recovered journal, not for any
   reason. If the journal cannot be reliably scanned to determine the
   highest existing cycle number (corruption or unavailability), the
   operation fails closed with `BASKET_JOURNAL_INTEGRITY_UNCERTAIN`
   (Section 15) — it never falls back to assuming no prior cycle existed
   and never restarts numbering at `1`, which could silently collide with
   or shadow a real prior cycle.

### 13.1b Confirmation request ID — deterministic, no nonce, unique per cycle

Computed **once**, only at the moment a new cycle's record is created
(never recomputed later for an existing record):

```
confirmation_request_id = "creq_" + sha256(
    "TRL-BASKET-CONFIRM-REQUEST.v1\n" + basket_id + "\n"
    + canonical_basket_plan_hash + "\n" + confirmation_basis_hash + "\n"
    + str(confirmation_cycle_number) + "\n"
    + requested_at_utc + "\n" + expires_at_utc
)[:32]
```

`confirmation_cycle_number` is encoded as its canonical decimal-integer
text (no leading zeros, no sign for a positive value); `requested_at_utc`/
`expires_at_utc` use the repository's existing canonical UTC timestamp
text representation (the same one every other `..._at_utc` field in this
codebase already uses). No nonce is used or required — including
`confirmation_cycle_number` and this cycle's own fixed timestamps in the
hash material is what makes each cycle's `confirmation_request_id`
distinct from every other cycle's, including a same-basis reissue after
expiry (Section 13.3), without needing any randomness.

### 13.1c Challenge derivation

Computed **once**, at the same moment as `confirmation_request_id`, from
the now-fixed `confirmation_request_id` itself:

```
challenge_hex = sha256(
    "TRL-BASKET-CONFIRM.v1\n" + confirmation_request_id + "\n"
    + basket_id + "\n" + canonical_basket_plan_hash + "\n"
    + confirmation_basis_hash
)[:16]
```

using lowercase hexadecimal digits only. Because `confirmation_request_id`
is itself unique per cycle (Section 13.1b), `challenge_hex` is
automatically unique per cycle too — **an expired or invalidated cycle's
challenge can never coincide with any later cycle's challenge, even one
sharing the identical basis**, which is exactly the property an earlier
draft of this contract lacked (a plan-hash-only, and later a
basis-hash-only, formula could regenerate an identical challenge across
two different request instances). `challenge_hex` still transitively
binds everything `confirmation_basis_hash` covers (the basket, the
account, the filled-child set, the required-check set, the next eligible
child) plus this specific cycle's own unique identity.

### 13.2 Exact local entry syntax

```
CONFIRM-BASKET <16-hex-challenge>
```

Example (fake values only): `CONFIRM-BASKET 0123456789abcdef`.

Parsing rules, all mandatory: ASCII only; exactly the literal prefix
`CONFIRM-BASKET` (case-sensitive); exactly one ordinary space (`0x20`)
between the prefix and the challenge; exactly 16 characters after the
space, each one of `0-9a-f` (lowercase only, never case-folded); no
additional content of any kind — the entire submitted string must equal
the prefix, one space, and the 16 hex characters, nothing more.

Rejected, each with the specific reason code from Section 13.5 (precedence
order in Section 13.4): a bare `yes`/`confirm`/`proceed`; the hexadecimal
fragment without the exact `CONFIRM-BASKET ` prefix; any case variation of
the prefix; extra tokens or hidden leading/trailing data; a syntactically
valid entry whose hex value belongs to a different cycle or a different
basket entirely; a syntactically valid entry whose hex value belongs to
this basket's own **expired** prior cycle; a syntactically valid entry
whose hex value belongs to this basket's own **invalidated** prior cycle;
and any confirmation received through HTTP (there is no HTTP confirmation
route at all — Section 35, and this remains prohibited without exception).

**The challenge is a binding, accidental-action safeguard, not a
credential**, and is never treated or stored as a secret (Section 39).

### 13.3 Requesting a confirmation — reuse, new cycle, and expiry handling

`request-basket-confirmation <basket_id>` is only ever reachable while
`basket_status` is `CHECK_COMPLETE` or `AWAITING_CONFIRMATION`
(Section 14.1) — i.e. strictly **before** the first child of the current
cycle has been sent. It may be called only when every child not yet
`FILLED` (i.e. every prospective member of
`authorized_remaining_child_ids`, Section 13.1.1(B)) has a check result
with `check_outcome == "PASSED"` whose `checked_at_utc` is within
`CHECK_FRESHNESS_SECONDS` (Section 24.1). Otherwise fails closed with
`BASKET_NOT_CHECK_COMPLETE`.

All of the following runs under the cross-process lock (Section 19),
reloading the durable journal before deciding:

1. Compute `authorized_prior_filled_child_ids`, `authorized_remaining_child_ids`,
   `authorized_start_child_id`, and the required-check lists fresh from
   current durable state (Section 13.1.1), then compute
   `confirmation_basis_hash` (Section 13.1) from them.
2. Locate this basket's current cycle, if any (the highest
   `confirmation_cycle_number` record on file for this `basket_id`).
3. **No prior cycle exists:** allocate cycle `1` (Section 13.1a), compute
   `requested_at_utc`/`expires_at_utc` fresh, compute
   `confirmation_request_id`/`challenge_hex` (Section 13.1b–13.1c),
   persist a brand-new `TRL_BASKET_CONFIRMATION.v1` record,
   `status = "REQUESTED"`. Append `BASKET_CONFIRMATION_REQUESTED`
   (payload includes `confirmation_request_id` and
   `confirmation_cycle_number`).
4. **The current cycle's `status == "REQUESTED"`, it has not reached
   `expires_at_utc`, and its stored `confirmation_basis_hash` equals the
   one just recomputed:** this is the same still-current request — return
   it exactly as persisted. **`requested_at_utc`, `expires_at_utc`,
   `confirmation_request_id`, and `challenge_hex` are never modified or
   regenerated**; no new record and no new cycle number is created; a mere
   status inspection or a repeated identical call never extends the
   confirmation window. Append `BASKET_CONFIRMATION_REQUEST_REUSED`
   (referencing the same `confirmation_request_id`/
   `confirmation_cycle_number`) — an informational event, not a failure.
5. **The current cycle's `status == "REQUESTED"` but
   `now >= expires_at_utc`:** materialize the expiry truthfully and
   permanently **before anything else happens**: `status → "EXPIRED"`,
   `expired_at_utc = now`, append `BASKET_CONFIRMATION_EXPIRED`
   (referencing that cycle's own `confirmation_request_id`/
   `confirmation_cycle_number`) — this record's `requested_at_utc`/
   `expires_at_utc`/`confirmation_request_id`/`challenge_hex` are **never**
   changed by this or any later step; it is now permanently terminal.
   Then: revalidate the confirmation basis fresh (it may or may not have
   changed), allocate the **next** cycle number (Section 13.1a),
   compute a fresh `requested_at_utc`/`expires_at_utc`, compute a
   **new** `confirmation_request_id`/`challenge_hex` for that new cycle
   (Section 13.1b–13.1c), and persist it, `status = "REQUESTED"`. Append
   `BASKET_CONFIRMATION_REQUESTED` for the new cycle. The operator must
   enter the **new** challenge; the old one is never valid again
   (Section 13.4).
6. **The current cycle's `status == "REQUESTED"`, has not expired, but the
   freshly recomputed `confirmation_basis_hash` differs from the one
   stored on it:** invalidate that cycle (Section 13.6,
   `BASKET_CONFIRMATION_BASIS_CHANGED`), then follow the same "allocate
   next cycle" procedure as step 5 (new cycle number, new timestamps, new
   ID, new challenge). This case is defensive rather than a normal-flow
   path: because `request-basket-confirmation` is only ever reachable
   before the current cycle's first child send (this section's opening
   gate), and no child can fill without first passing through `CONFIRMED`/
   `SENDING`, `authorized_prior_filled_child_ids` cannot legitimately
   differ between two consecutive re-requests of the same still-`REQUESTED`
   cycle under normal operation — this branch exists to fail closed on an
   otherwise-unexpected drift (e.g. a hand-edited or externally corrupted
   record), not to handle ordinary multi-child progress (Section 26 covers
   that entirely differently, without ever calling back into this
   section).
7. **The current cycle's `status == "ACCEPTED"`:** unreachable through the
   normal CLI flow as defense in depth only — `request-basket-confirmation`
   is gated on `basket_status == "CHECK_COMPLETE"`/`"AWAITING_CONFIRMATION"`
   (Section 14.1), and an accepted cycle always means `basket_status ==
   "CONFIRMED"` or later, which this gate already excludes.
8. `basket_status → "AWAITING_CONFIRMATION"` (steps 3–6, whichever fired).

### 13.4 Accepting a confirmation

`confirm-basket <basket_id> <entry-text>` first parses `<entry-text>`
exactly per Section 13.2 (`BASKET_CONFIRMATION_FORMAT_INVALID` on any
syntax failure). Once parsed, the extracted 16-hex value is resolved
against this basket's confirmation-cycle history in this exact precedence
order — **the first matching case governs**, and reaching a later case
requires no earlier case having matched:

1. **Matches the current cycle's `challenge_hex` exactly:** proceed to the
   full acceptance checks below.
2. **Matches an earlier cycle of this same basket whose `status ==
   "EXPIRED"`:** reject with `BASKET_CONFIRMATION_EXPIRED`. This is the
   Founder's explicit rule — an old challenge is never accepted merely
   because a newer cycle now exists; the exact `EXPIRED` reason is
   returned rather than a generic mismatch.
3. **Matches an earlier cycle of this same basket whose `status ==
   "INVALIDATED"`:** reject with `BASKET_CONFIRMATION_INVALIDATED`.
4. **Matches a cycle belonging to a different `basket_id` entirely (or an
   `ACCEPTED` prior cycle of this basket — Section 13.3, step 7's
   unreachable-in-practice case):** reject with
   `BASKET_CONFIRMATION_WRONG_REQUEST`.
5. **Matches nothing findable at all:** reject with
   `BASKET_CONFIRMATION_MISMATCH`.

Only case 1 continues. The full acceptance requires **all** of the
following, revalidated fresh (never cached):

- `basket_status == "AWAITING_CONFIRMATION"`.
- The current cycle's `status == "REQUESTED"` and
  `now < expires_at_utc` — if `now >= expires_at_utc` is discovered only
  now, materialize the expiry exactly as Section 13.3 step 5 describes
  (permanently, immutably) and reject this specific attempt with
  `BASKET_CONFIRMATION_EXPIRED`; a fresh `request-basket-confirmation`
  call is required to obtain the next cycle's challenge.
- Recomputing `confirmation_basis_hash` fresh (from freshly recomputed
  `authorized_prior_filled_child_ids`/`authorized_remaining_child_ids`/
  `authorized_start_child_id`/required-check lists, per Section 13.1.1)
  yields the **identical** value already stored on the current cycle — as
  with Section 13.3 step 6, this should always hold under normal operation
  (no child of this cycle can have filled yet, since acceptance always
  precedes the first send — Section 13.4.1); a mismatch here is a
  defensive fail-closed check, not something normal progression ever
  triggers. If it does mismatch, this fails as
  `BASKET_CONFIRMATION_BASIS_CHANGED`, and the current cycle is
  invalidated (Section 13.6) rather than accepted.
- The confirmation is being submitted through the local CLI
  (`actor_channel == "LOCAL_OPERATOR"`) — never through any HTTP route
  (`BASKET_CONFIRMATION_CHANNEL_NOT_LOCAL`).
- The current cycle's `status` is not already `"ACCEPTED"`
  (`BASKET_CONFIRMATION_ALREADY_ACCEPTED`) — a cycle is accepted at most
  once, ever.

On success: `status → "ACCEPTED"`, `accepted_at_utc` set, append
`BASKET_CONFIRMATION_ACCEPTED` (referencing `confirmation_request_id`/
`confirmation_cycle_number`), transition `basket_status → "CONFIRMED"`.

On failure: append `BASKET_CONFIRMATION_REJECTED` — an **attempt-level**
journal event only — with the specific reason code (referencing whichever
cycle's `confirmation_request_id`/`confirmation_cycle_number` was actually
matched, or the current cycle's if nothing matched); `basket_status`
returns to (or remains) `"CHECK_COMPLETE"`; no adapter call occurs either
way. **A failed acceptance attempt never creates a competing confirmation
record and never introduces a `"REJECTED"` value into the request-lifecycle
`status` vocabulary** (Section 12: `REQUESTED`/`ACCEPTED`/`INVALIDATED`/
`EXPIRED` only) — unless this specific attempt also independently
triggered expiry (the branch above) or a genuine basis mismatch (the
branch above), the current cycle's own `status` simply remains
`"REQUESTED"`, exactly as it was before the wrong entry, and the operator
may immediately retry `confirm-basket` against that same still-active
cycle. A future, separately Founder-approved contract could add a bounded
wrong-attempt count that itself invalidates a cycle; this contract defines
no such limit, so an incorrect entry alone, on its own, never invalidates
or expires the current cycle.

**Acceptance is atomic and cross-process protected** (Section 19): two
concurrent `confirm-basket` invocations racing the same basket produce at
most one `BASKET_CONFIRMATION_ACCEPTED` event, for at most one cycle.

### 13.4.1 One accepted cycle authorizes the entire remaining sequence

The `ACCEPTED` `TRL_BASKET_CONFIRMATION.v1` record for the current cycle
is a **durable, checkpoint-scoped authorization**, not a per-child token
and not something that must be re-derived after every fill. Once accepted,
it authorizes sending, **in sequence, one at a time**, every child in
`authorized_remaining_child_ids` (Section 13.1.1(B)) — the complete
unsent set that was fixed the moment this cycle was requested — starting
from `authorized_start_child_id` and continuing through the live-computed
next-eligible child (Section 26) as each prior one reaches `FILLED`.

**A child successfully reaching `FILLED` does not, by itself:**

- invalidate the current cycle's authorization,
- create a new confirmation cycle,
- require the challenge to be entered again,
- change `confirmation_basis_hash` (which is fixed at request time and
  never recomputed against post-acceptance progress — Section 13.1), or
- permit parallel or out-of-order execution.

This is possible precisely *because* the confirmation basis (Section 13.1)
is a fixed checkpoint rather than a live, continuously-recomputed
projection: `authorized_remaining_child_ids` already names every child
this cycle may ever authorize, so advancing from one filled child to the
next never touches the accepted record at all — only the *live*
next-eligible-child computation (Section 26) changes, which is derived
service state, not a field on the confirmation record. The first
successful child send does **not** consume, delete, or otherwise
invalidate this cycle's authorization for the remaining children. Each
child send nonetheless remains its own separate, explicit local operator
action (the `send-basket-next` command, Section 26/34) — the operator
must still issue one command per child, and no child is ever sent
automatically as a side effect of another child filling — but that action
does not require, accept, or re-prompt for the confirmation code a second
time, because the code itself was already single-use-consumed at
acceptance and the resulting authorization is what governs every
subsequent send in this cycle. Only an explicit invalidation condition
(Section 13.6) — never ordinary successful progress — ends this
authorization early and forces a new cycle where continuation remains
possible at all. An accepted cycle for one basket **never** authorizes any
other basket, under any circumstance, and once invalidated it is **never**
reactivated.

### 13.5 Confirmation-specific reason codes

`BASKET_CONFIRMATION_FORMAT_INVALID`, `BASKET_CONFIRMATION_MISMATCH`,
`BASKET_CONFIRMATION_WRONG_REQUEST`, `BASKET_CONFIRMATION_EXPIRED`,
`BASKET_CONFIRMATION_ALREADY_ACCEPTED`, `BASKET_CONFIRMATION_UNAVAILABLE`
(no active cycle exists to accept against),
`BASKET_CONFIRMATION_INVALIDATED`, `BASKET_CONFIRMATION_BASIS_CHANGED`,
`BASKET_CONFIRMATION_REQUEST_REUSED` (informational, Section 13.3 step 4),
`BASKET_CONFIRMATION_CHANNEL_NOT_LOCAL`, `BASKET_NOT_CHECK_COMPLETE`. Full
list cross-referenced in Section 15.

### 13.6 Confirmation invalidation

The **current** cycle's confirmation record — whether `REQUESTED` or
`ACCEPTED` — becomes invalid: `status → "INVALIDATED"`,
`invalidated_at_utc` set, `invalidation_reason` recorded,
`BASKET_CONFIRMATION_INVALIDATED` appended with that cycle's own
`confirmation_request_id` and `confirmation_cycle_number` in its payload
(never a credential — Section 39), and no further child may be sent under
it — immediately upon any of:

- Any required child's check going stale (Section 24.1–24.2) — see the
  precise pre-fill vs. post-fill handling there.
- An account-fingerprint change detected on revalidation.
- A basket-plan mismatch (defensive; the plan is immutable, Section 9, so
  this is unreachable except under corruption).
- A child-set or child-order mismatch against `authorized_remaining_child_ids`
  (equally defensive, for the same reason).
- Loss of the required `ModeService` mode/capability grant (Section 5–6) —
  e.g. the operator manually left `MT5_DEMO_MANUAL`.
- Loss of an active risk-halt-free state (a risk halt becoming active).
- A child rejection, partial fill, or uncertain result (Sections 27–29) —
  the basket has already stopped sending by the time any of these occurs,
  so the current cycle is invalidated as part of that same transition,
  never left dangling in an `ACCEPTED` state on a terminal basket.
- A malformed broker result (Section 29).
- The basket reaching any terminal `basket_status` (Section 14.2),
  including a basket freeze (Section 29).
- Integrity uncertainty in the durable store.

**The following, explicitly, never invalidate the current cycle's
authorization:**

- A child successfully reaching `FILLED` (Section 13.4.1) — the entire
  point of the authorization-checkpoint design (Section 13.1) is that
  ordinary successful progress never touches the confirmation record.
- The live next-eligible child (Section 26) advancing from one child to
  the next as a normal consequence of a fill.
- `completed_quantity` or `filled_child_count` increasing through approved
  fills (Section 36).
- Ordinary read-only status inspection (`basket-status`, `inspect-basket`,
  the read-only HTTP routes) — none of these ever mutate confirmation
  state, exactly as none of them ever extend a confirmation's window
  (Section 13.3).

(Expiry, Section 13.3/13.4, is handled as its own distinct `EXPIRED`
transition, not as an `INVALIDATED` one — the two are kept separate so
`BASKET_CONFIRMATION_EXPIRED` can always be returned precisely, per
Founder instruction, rather than folded into the more general
`INVALIDATED` reason.)

**An invalidated (or expired) record is never reactivated, never rewritten
to simulate a new cycle, and never has its cycle number reassigned or
reused.** Every field on it besides `status`/`invalidated_at_utc`/
`invalidation_reason` (or `expired_at_utc` for the expiry case) is exactly
as it was the moment it was created. Where this contract permits
continuation at all (Section 13.3 steps 5–6, Section 24.2), continuation
always means creating a **new** cycle with its own new `confirmation_cycle_number`,
`confirmation_request_id`, and `challenge_hex` — never resurrecting the
old one.

There is no operator-initiated "cancel confirmation" action in this
contract; an operator who wants to stop simply does not issue the next
`send-basket-next` command, and the current cycle naturally expires per
`CONFIRMATION_LIFETIME_SECONDS` if unused.

## 14. State machine

### 14.1 Basket status — `BASKET_STATUSES`

```
CREATED, CHECK_REQUIRED, CHECKING, CHECK_COMPLETE, AWAITING_CONFIRMATION,
CONFIRMED, SENDING, COMPLETED, FAILED, PARTIALLY_COMPLETED, REJECTED,
BLOCKED, FROZEN, EXPIRED
```

```
CREATED
  --(check-basket invoked for the very first time for this basket)--> CHECKING
CHECKING
  --(the child just checked PASSED, and every other currently-required child already has a fresh PASSED check)--> CHECK_COMPLETE
  --(the child just checked PASSED, but another currently-required child still lacks one)--> CHECK_REQUIRED   (repeat check-basket for the remaining child)
  --(the child just checked FAILED/MALFORMED)--> CHECK_REQUIRED, with the reason recorded against that child
CHECK_REQUIRED
  --(check-basket invoked again)--> CHECKING
CHECK_COMPLETE
  --(request-basket-confirmation)--> AWAITING_CONFIRMATION
  --(any currently-required child's check goes stale while sitting in CHECK_COMPLETE)--> CHECK_REQUIRED (Section 24.1/24.2)
AWAITING_CONFIRMATION
  --(confirm-basket, exact challenge accepted, Section 13.4)--> CONFIRMED
  --(confirm-basket rejected)--> CHECK_COMPLETE   (no other state change beyond the rejection record; operator may re-request)
  --(any currently-required child's check goes stale before acceptance)--> CHECK_REQUIRED, confirmation invalidated
CONFIRMED
  --(send-basket-next: reservation persisted for the live next eligible child, Section 26)--> SENDING
  --(any currently-required child's check goes stale before the send)--> CHECK_REQUIRED, confirmation invalidated
SENDING
  --(every required child reaches FILLED)--> COMPLETED
  --(the first-ever-sent child is REJECTED/CANCELLED-equivalent broker outcome, zero prior FILLED children)--> FAILED
  --(a later child is REJECTED after >=1 prior child FILLED)--> PARTIALLY_COMPLETED
  --(any child result is UNCERTAIN / malformed / ambiguous)--> FROZEN
  --(a currently-required child's check goes stale before ITS OWN send, zero prior FILLED children)--> CHECK_REQUIRED, confirmation invalidated, every unsent child returns to CHECK_REQUIRED (Section 24.2.A)
  --(a currently-required child's check goes stale before ITS OWN send, >=1 prior child already FILLED)--> CHECK_REQUIRED, confirmation invalidated, filled children permanently preserved, only remaining unsent children return to CHECK_REQUIRED (Section 24.2.B) — this is NOT PARTIALLY_COMPLETED
  --(basket or confirmation expiry reached mid-sequence, zero prior FILLED)--> EXPIRED
  --(basket or confirmation expiry reached mid-sequence, >=1 prior FILLED)--> PARTIALLY_COMPLETED
Any state prior to CONFIRMED
  --(basket-plan or parent-intent expiry reached)--> EXPIRED
Any state prior to SENDING, during construction/check/confirm
  --(SMA-001/FIB-001 blocker or capability/mode gate fails, Section 7)--> BLOCKED
Any state prior to SENDING, during construction/check/confirm
  --(any other governance/schema/conservation failure, Section 15)--> REJECTED
COMPLETED / FAILED / PARTIALLY_COMPLETED / REJECTED / BLOCKED / FROZEN / EXPIRED
  --terminal for this basket, unconditionally--
```

### 14.2 Nonterminal vs. terminal

**Nonterminal (`NONTERMINAL_BASKET_STATUSES`):**
`CREATED, CHECK_REQUIRED, CHECKING, CHECK_COMPLETE, AWAITING_CONFIRMATION, CONFIRMED, SENDING`

**Terminal for Phase 6 (`TERMINAL_BASKET_STATUSES`):**
`COMPLETED, FAILED, PARTIALLY_COMPLETED, REJECTED, BLOCKED, FROZEN, EXPIRED`

No further construction, check, confirmation, or send may occur against a
terminal basket under any circumstance; a repeated request against a
terminal basket resolves to that basket's existing terminal outcome
(Section 18) and performs no further adapter call. **`FROZEN` is terminal
for Phase 6 sending specifically** — no Phase 6 code path ever resumes
sending, checking, or confirming a `FROZEN` basket — **but it is not a
claim that the basket's real-world state is permanently unexamined**; a
separate, later, explicitly Founder-approved reconciliation phase (Phase
10, Section 33) is the only mechanism ever authorized to examine or act on
a `FROZEN` basket further.

### 14.3 Rejection vs. blocked vs. failed vs. partial success — exact distinctions

- **`REJECTED`** — zero children were ever sent to the broker; the basket
  failed at construction, check, or confirmation time for a
  governance/schema/conservation reason. No broker interaction occurred.
- **`BLOCKED`** — the same "zero children ever sent" condition, caused
  specifically by the SMA-001/FIB-001 strategy blocker or a
  capability/mode gate (Section 7).
- **`FAILED`** — at least one `order_send` call was made, and that very
  first sent child was rejected by the broker with **zero** prior children
  filled.
- **`PARTIALLY_COMPLETED`** ("partial success") — a **permanent stop**
  condition requiring **both**: at least one child reached `FILLED`, and
  at least one required child did not (and, per the transition that
  produced this status, will not) successfully fill — caused by a later
  child's rejection, an uncertain result being resolved unfavorably (not
  applicable to Phase 6, which never resolves `FROZEN` itself), or basket/
  confirmation expiry reached after fills. **`PARTIALLY_COMPLETED` is never
  used for an ordinary, recoverable stale-check recheck cycle** — a basket
  that returns to `CHECK_REQUIRED` after one or more fills because a
  remaining child's check went stale (Section 14.4) is still fully
  recoverable and is not this status.
- **`FROZEN`** — an uncertain/ambiguous/malformed broker result on any
  child, regardless of how many prior children filled.
- A basket with one or more successfully filled children and a later,
  permanent stop is always `PARTIALLY_COMPLETED`, never `FAILED` or
  `REJECTED` — those two are reserved exclusively for the zero-prior-fill
  case.

### 14.4 `CHECK_REQUIRED` with prior progress — recoverable, not terminal

`CHECK_REQUIRED` may legitimately co-occur with `filled_child_count > 0`
(Section 36) whenever the remaining unsent, currently-required checks
became stale after one or more children had already filled
(Section 24.2.B). This **does not erase completed progress**:

- Every `FILLED` child's `TRL_BASKET_CHILD_EXECUTION_RESULT.v1` record and
  every journal event describing it remain exactly as recorded, permanent
  and unmodified.
- Only the remaining, still-unsent, nonterminal children return to
  `CHECK_REQUIRED`; child ordering never resets, and no already-filled
  child ever becomes eligible for anything again (Section 24.2.B, Section
  27's ban on generating a replacement or re-sending a filled child).
- The basket's own `basket_status` field reads `CHECK_REQUIRED` — the same
  value it would show for a basket that has never sent anything — but
  `TRL_BASKET_STATUS.v1` (Section 36) always additionally reports
  `filled_child_count`/`completed_quantity` truthfully, so this state is
  never mistaken for "nothing has happened yet."
- `reconciliation_required = (basket_status in ("PARTIALLY_COMPLETED", "FROZEN"))`,
  computed on read, never stored as an independently settable field — a
  recoverable `CHECK_REQUIRED`-with-progress basket is explicitly `false`
  here, because nothing ambiguous or broker-uncertain has occurred; the
  basket is simply mid-cycle, awaiting a fresh check and a fresh
  confirmation for its remaining children.

### 14.5 Basket child status — `BASKET_CHILD_STATES`

A separate, independently defined closed vocabulary belonging to
`TRL_BASKET_CHILD_INTENT.v1`'s execution progress (tracked via Section 11/
11.1 records, never by mutating the child document itself) — **not**
imported from or aliased to `mt5_execution_data.INTENT_STATES`
(Section 1.1):

```
CREATED, CHECK_REQUIRED, CHECKING, CHECK_PASSED, SEND_RESERVED, FILLED,
PARTIALLY_FILLED, REJECTED, FROZEN_PENDING_RECONCILIATION, EXPIRED, BLOCKED
```

**`CANCELLED` is deliberately absent.** Phase 6 implements no broker
cancellation, no automatic cancellation, no rollback cancellation, no
compensation cancellation, and no reconciliation-driven cancellation
(Section 3, Section 31) — there is no code path in this contract that
could ever legitimately produce a cancelled child, so the value is not
part of the vocabulary. A future, separately Founder-approved contract may
introduce cancellation behavior and its own state at that time.

**Child-level `AWAITING_CONFIRMATION` is deliberately absent.** Basket
confirmation (Section 13) is authoritative and scoped to the whole basket,
not to an individual child — a per-child confirmation state would
duplicate and could contradict that single source of truth. A child's
readiness to send is instead fully described by its own `CHECK_PASSED`
state combined with the *basket's* `basket_status` (`CONFIRMED`/`SENDING`).

**`EXPIRED` and `BLOCKED` producers, precisely:** when the owning basket
transitions to `basket_status == "EXPIRED"`, every one of its children not
already in a terminal child state (`FILLED`, `PARTIALLY_FILLED`,
`REJECTED`, `FROZEN_PENDING_RECONCILIATION`) is transitioned to `EXPIRED`
at the same moment. When the owning basket transitions to
`basket_status == "BLOCKED"`, every existing child record (if any were
persisted before the blocker was detected — Section 20 checks blockers
before basket construction in the common case, so typically none exist
yet) is transitioned to `BLOCKED`. A basket that reaches `REJECTED` most
commonly aborts before any child record is ever created (Section 20); on
the rarer path where children already exist, they are simply left in
whatever nonterminal state they last reached — Section 14.2's terminal-
basket lock, not a forced child-state transition, is what guarantees no
further action is ever taken against them.

**`TERMINAL_BASKET_CHILD_STATES`:**
`FILLED, PARTIALLY_FILLED, REJECTED, FROZEN_PENDING_RECONCILIATION, EXPIRED, BLOCKED`.
**Nonterminal:** `CREATED, CHECK_REQUIRED, CHECKING, CHECK_PASSED, SEND_RESERVED`.
A basket child that reaches `PARTIALLY_FILLED` is terminal for Phase 6 —
Phase 6 implements no further attempt to fill that same child's remaining
quantity (no automatic retry, Section 3); the owning basket stops per
Section 28 regardless.

### 14.6 Basket completion rule

A basket may be marked `COMPLETED` **only** when every required child's
own execution state is `FILLED`. One successful child is never basket
completion. A partial fill is never basket completion. An uncertain child
is never basket completion. A rejected child is never basket completion. A
missing/absent child result is never basket completion.

## 15. Reason-code vocabulary — `BASKET_REASON_CODES`

Additive to, and namespace-independent from, the existing
`mt5_execution_data.EXECUTION_REASON_CODES` (reused verbatim only for the
underlying Phase 5 *parent-intent* validation calls this contract invokes
unchanged — Section 8). No two codes below share the same meaning:

```
BASKET_SCHEMA_INVALID
BASKET_SCHEMA_VERSION_UNSUPPORTED
PARENT_SCHEMA_VERSION_UNSUPPORTED
BASKET_BACKWARD_COMPATIBILITY_FAILURE
BASKET_CHILD_COUNT_INVALID
BASKET_PARENT_INTENT_NOT_FOUND
BASKET_PARENT_INTENT_NOT_ELIGIBLE
BASKET_PARENT_PROPOSAL_HASH_MISMATCH
BASKET_PARENT_INTENT_HASH_MISMATCH
BASKET_PARENT_EXPIRED
BASKET_TARGET_COUNT_MISMATCH
BASKET_TARGET_ORDER_INVALID
BASKET_TARGET_NOT_UNIQUE
BASKET_ALLOCATION_SUM_INVALID
BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE
BASKET_CHILD_QUANTITY_ZERO
BASKET_CHILD_QUANTITY_BELOW_MINIMUM
BASKET_CHILD_QUANTITY_ABOVE_MAXIMUM
BASKET_CHILD_STEP_MISMATCH
BASKET_ORDER_TYPE_MISMATCH
BASKET_ECONOMIC_MEANING_CHANGED
BASKET_HIDDEN_CHILD_DETECTED
BASKET_HASH_MISMATCH
BASKET_JOURNAL_INTEGRITY_UNCERTAIN
BASKET_NOT_FOUND
BASKET_ALREADY_TERMINAL
BASKET_EXPIRED
BASKET_CAPABILITY_DENIED
BASKET_NOT_CHECK_COMPLETE
BASKET_CHECK_FAILED
BASKET_CHILD_CHECK_FAILED
BASKET_CHILD_CHECK_STALE
BASKET_RECHECK_REQUIRED
BASKET_CHILD_ALREADY_FILLED
BASKET_CONFIRMATION_FORMAT_INVALID
BASKET_CONFIRMATION_MISMATCH
BASKET_CONFIRMATION_WRONG_REQUEST
BASKET_CONFIRMATION_EXPIRED
BASKET_CONFIRMATION_ALREADY_ACCEPTED
BASKET_CONFIRMATION_UNAVAILABLE
BASKET_CONFIRMATION_INVALIDATED
BASKET_CONFIRMATION_BASIS_CHANGED
BASKET_CONFIRMATION_REQUEST_REUSED
BASKET_CONFIRMATION_CHANNEL_NOT_LOCAL
BASKET_DUPLICATE_BLOCKED
BASKET_CHILD_SEND_ALREADY_RESERVED
BASKET_CHILD_NOT_NEXT_ELIGIBLE
BASKET_CHILD_ALREADY_TERMINAL
BASKET_CHILD_UNCERTAIN_RESULT_BLOCKED
BASKET_FROZEN
BASKET_RECONCILIATION_REQUIRED
BASKET_EXECUTION_LOCK_UNAVAILABLE
```

`BASKET_CONFIRMATION_REQUEST_REUSED` is informational, not a failure — it
is the code recorded against a `request-basket-confirmation` call that
resolved to an existing, still-active cycle rather than creating a new one
(Section 13.3, step 4), distinguishing that outcome from a fresh
`BASKET_CONFIRMATION_REQUESTED` in the journal (Section 16) and CLI output
without implying anything went wrong. `BASKET_CONFIRMATION_WRONG_REQUEST`
replaces an earlier draft's `BASKET_CONFIRMATION_WRONG_BASKET` — renamed
because, with confirmation cycles now individually identified, an entered
challenge can be "wrong" either because it belongs to a different basket
or because it belongs to a different (non-expired, non-invalidated) cycle
entirely; "request" covers both without implying only the basket differs.
`BASKET_JOURNAL_INTEGRITY_UNCERTAIN` replaces an earlier draft's
`BASKET_LOOKUP_STORE_INTEGRITY_UNCERTAIN`, and
`BASKET_EXECUTION_LOCK_UNAVAILABLE` replaces an earlier draft's
`BASKET_LOCK_UNAVAILABLE` — both renamed for exact, final, consistent
naming; every other section of this contract that referenced the old
names uses the new ones.

## 16. Event vocabulary — basket journal extension

Additive to the existing `mt5_execution_journal.EVENT_TYPES` (19 values,
unchanged — Section 1.1). New basket event types, each with one and only
one meaning:

```
BASKET_REJECTED
BASKET_BLOCKED
BASKET_CREATED
BASKET_REUSED
BASKET_CHILD_CREATED
BASKET_CHILD_CHECK_REQUESTED
BASKET_CHILD_CHECK_RESULT
BASKET_CHILD_CHECK_STALE
BASKET_RECHECK_REQUIRED
BASKET_CONFIRMATION_REQUESTED
BASKET_CONFIRMATION_REQUEST_REUSED
BASKET_CONFIRMATION_REJECTED
BASKET_CONFIRMATION_ACCEPTED
BASKET_CONFIRMATION_EXPIRED
BASKET_CONFIRMATION_INVALIDATED
BASKET_CHILD_SEND_RESERVED
BASKET_CHILD_SEND_RESULT
BASKET_CHILD_PARTIAL
BASKET_CHILD_UNCERTAIN
BASKET_PARTIALLY_COMPLETED
BASKET_FAILED
BASKET_FROZEN
BASKET_RECONCILIATION_REQUIRED
BASKET_COMPLETED
BASKET_DUPLICATE_BLOCKED
BASKET_EXPIRED
```

`BASKET_PARTIALLY_COMPLETED` replaces an earlier draft's
`BASKET_PARTIAL_SUCCESS`, and `BASKET_COMPLETED` replaces an earlier
draft's `BASKET_COMPLETE` — both renamed so the event name is character-
for-character identical to the `basket_status` value it reports, removing
any possible synonym ambiguity. `BASKET_CONFIRMATION_EXPIRED` is new —
appended the moment a confirmation cycle's expiry is materialized
(Section 13.3 step 5, Section 13.4), distinct from the basket-level
`BASKET_EXPIRED` (which reports the whole basket's own expiry, Section
14). **Every** `BASKET_CONFIRMATION_*` and `BASKET_RECHECK_REQUIRED`
event's `payload` includes, at minimum, the affected cycle's
`confirmation_request_id` and `confirmation_cycle_number` (and, where
applicable, `confirmation_basis_hash`) — never a credential (Section 39).
No event name above is a synonym for any other; each has exactly one
meaning.

Each is a `TRL_MT5_EXECUTION_JOURNAL_EVENT.v1` event (unchanged schema —
Section 1.1) appended to the **same** journal file Phase 5 already writes
— not a second journal. `payload` for every basket event includes at
minimum `basket_id`; child-scoped events additionally include
`basket_child_id`.

## 17. Deterministic identities, no-nonce rules, idempotency

### 17.1 Basket lookup key — `TRL_BASKET_LOOKUP_KEY.v1`, deterministic, no nonce

Computed from exactly:

| Field | Meaning |
|---|---|
| `parent_order_intent_id` | the exact parent this basket would derive from |
| `canonical_parent_order_intent_hash` | pins the parent's exact content at lookup time |
| `account_fingerprint_hash` | same value the parent already carries |
| `broker_native_instrument` | same value the parent already carries |
| `side` | same value the parent already carries |
| `strategy_id` / `strategy_version` | same values the parent already carries |
| `risk_policy_hash` | same value the parent already carries |
| `operating_mode` | `"MT5_DEMO_MANUAL"` |
| `authorization_identity` | the local-operator confirmation/session identity that requested basket construction |
| `child_count` | the target count this basket would produce |
| `target_set_hash` | `sha256(deterministic_json([targets, target_allocations_percent]))` — pins the exact target/allocation content without embedding it field-by-field |

`basket_lookup_key = "blk_" + sha256(canonical_json(above fields))[:32]`.
Content-derived, stable across processes, stable across restart, stable
across any independently reconstructed valid state, and **excludes**
mutable status, wall-clock processing time, and any random value.

### 17.2 Basket ID — deterministic, no nonce

```
basket_id = "bsk_" + sha256("TRL-BASKET-ID.v1\n" + basket_lookup_key)[:32]
```

`basket_id` is a pure, deterministic function of `basket_lookup_key`
(Section 17.1) — identical governed input always produces the identical
`basket_id`, with no randomness anywhere in its derivation. This is what
makes "same governed input reuses the existing basket" (Section 20)
correct by construction.

### 17.3 Lookup-before-create (basket level)

1. Compute `basket_lookup_key` (Section 17.1) and `basket_id`
   (Section 17.2) — both deterministic, no nonce.
2. Under the cross-process lock (Section 19), search the durable journal
   for an existing `TRL_BASKET_PLAN.v1` record with this exact
   `basket_id`.
3. **Found:** reuse that exact basket — its complete state. If its
   `basket_status` is already terminal (Section 14.2), answer with the
   existing outcome; no child `order_check` or `order_send` is triggered
   merely because the request arrived again (`BASKET_REUSED` event). If
   non-terminal, resume from the existing basket's current state.
4. **Not found:** persist the new `TRL_BASKET_PLAN.v1` record (Sections
   9–10) atomically, in one durable write, before any child `order_check`
   is attempted, `basket_status = "CREATED"` (`BASKET_CREATED` event).
5. **Lookup or durable-store integrity uncertain:** fail closed with
   `BASKET_JOURNAL_INTEGRITY_UNCERTAIN`. **A new basket is never created
   as a fallback when the lookup itself cannot be trusted, and a
   corrupted or unavailable journal is never treated as permission to
   construct and send a replacement basket.**

### 17.4 Basket child identity — deterministic, no nonce

Each child's lookup key is computed from the basket's own immutable
identity plus this child's own immutable plan facts — never from Phase
5's `execution_intent_lookup_key`/`order_intent_id_for` functions, which
this contract does not call, extend, or modify (Section 1.1):

| Field | Meaning |
|---|---|
| `basket_id` | the owning basket |
| `canonical_basket_plan_hash` | pins the exact basket-plan content |
| `child_index` | this child's ordered position |
| `target_price` | this child's target |
| `target_allocation_percent` | this child's allocation |
| `child_quantity` | this child's computed quantity slice |
| `account_fingerprint_hash` / `broker_native_instrument` / `side` / `order_type` / `entry_price` / `stop_loss` / `strategy_id` / `strategy_version` / `risk_policy_hash` / `operating_mode` / `expires_at_utc` | inherited authority/execution-instruction fields, unchanged from the basket plan |

```
basket_child_lookup_key = "bclk_" + sha256(canonical_json(above fields))[:32]
basket_child_id = "bc_" + sha256("TRL-BASKET-CHILD-ID.v1\n" + basket_child_lookup_key)[:16]
```

Both are deterministic functions with **no nonce and no random value**.
This supersedes, for Phase 6 purposes, the forward-looking `basket_child_id`
derivation sketch in `TRL_R2_007_MT5_EXECUTION_CONTRACT.md` Section 5.6
(written before any basket contract existed; that file is not modified by
this checkpoint — Section 3).

### 17.5 Child idempotency key

`TRL_BASKET_CHILD_INTENT.v1.idempotency_key == basket_child_id` always,
identical in spirit to Phase 5's `idempotency_key == order_intent_id`
rule, applied at the basket-child layer.

### 17.6 Nonce rules

**No basket-layer identity contains a nonce anywhere in this contract** —
not `basket_lookup_key`, not `basket_id`, not `basket_child_lookup_key`,
not `basket_child_id`, not `confirmation_request_id`. This is a deliberate
departure from Phase 5's `order_intent_id`/`client_intent_nonce` pattern
(which remains completely untouched — Section 1.1). The **only** nonce
anywhere in the combined Phase 5 + Phase 6 design remains Phase 5's own
`client_intent_nonce` on the underlying parent order intent, which this
contract never touches.

## 18. Idempotency guarantees

- One authoritative basket per `basket_id` (deterministic — Section 17.2),
  enforced by lookup-before-create (Section 17.3) under the cross-process
  lock (Section 19).
- One authoritative child per `basket_child_id`, enforced the same way.
- One authoritative confirmation record per `confirmation_request_id`,
  with reuse (not duplication) when the identical basis is re-requested
  (Section 13.3).
- A restart cannot make an already-reserved child send eligible again
  (Section 30), and can never make an already-`FILLED` child eligible for
  anything again (Section 14.5, Section 27).
- Two concurrent CLI processes racing identical basket construction
  produce exactly one basket (Section 19).
- Two concurrent CLI processes racing the same child's send call
  `order_send` at most once for that child (Section 19, Section 26).
- Two concurrent `confirm-basket` commands produce at most one
  `BASKET_CONFIRMATION_ACCEPTED` event (Section 13.4).
- A corrupted or unavailable journal fails closed
  (`BASKET_JOURNAL_INTEGRITY_UNCERTAIN`) — never falls back to an
  unlocked, best-effort, or replacement-basket path.

## 19. Cross-process concurrency

Every basket-level search-decide-persist critical section uses the
**existing** Phase 5 owner-token-protected cross-process lock
(`_CrossProcessFileLock`/`_ThreadLock`/`_ReloadingLock` in
`mt5_execution_journal.py`) — no new lock class is introduced. Locked
critical sections:

- Basket lookup-before-create (Section 17.3).
- Child lookup-before-create, per child (Section 20).
- Confirmation-basis computation and request reuse-or-create decision
  (Section 13.3).
- Confirmation acceptance (Section 13.4).
- Child send reservation (Section 26, step 9).
- Every basket/child terminal-state transition (Section 14).

After acquiring the lock, the implementation must reload from disk,
validate the journal, and use only the latest durable state before
deciding anything. Lock timeout fails closed with
`BASKET_EXECUTION_LOCK_UNAVAILABLE`; there is no unlocked fallback for any
basket operation, ever. The durable journal lock is **never held across an
adapter/broker call** (Section 26).

## 20. Basket construction and child derivation

Given an eligible parent order intent (Section 8) and current mode
`MT5_DEMO_MANUAL` with `manual_basket_execution` granted:

1. Re-validate every Section 8 prerequisite fresh. If either Section 7
   blocker gate or the mode/capability gate fails, stop with the specific
   reason code and (if a `basket_id` was already computable) persist the
   basket as `BLOCKED`, not `REJECTED` (Section 14.3).
2. Compute `basket_lookup_key` and `basket_id` (Section 17.1–17.2) and run
   lookup-before-create (Section 17.3) under the cross-process lock.
3. If creating new: for each `child_index` in `0 .. child_count-1`, in
   ascending order (matching the parent's `targets` order exactly — no
   reordering, no dropping):
   - Compute `child_quantity` (Section 21). A zero, unresolvable, or
     out-of-bounds quantity for **any** child aborts the **entire** basket
     construction with `REJECTED` — no partial basket with fewer children
     than the parent declared is ever created.
   - Derive `basket_child_lookup_key`/`basket_child_id` (Section 17.4) and
     build the child's `TRL_BASKET_CHILD_INTENT.v1` document (Section 10).
   - Run the child-level lookup-before-create under the same
     cross-process lock (a child may already exist from a prior partial
     construction attempt against the identical basket — it is reused,
     never duplicated).
   - Persist `BASKET_CHILD_CREATED`.
4. Verify no hidden child exists: `len(children) == child_count == len(parent.targets)`
   exactly; any mismatch aborts with `BASKET_HIDDEN_CHILD_DETECTED`
   (`REJECTED`).
5. Compute `canonical_basket_plan_hash` (Section 9.1) over the complete,
   now-fully-populated `TRL_BASKET_PLAN.v1` and persist it atomically,
   `basket_status = "CREATED"` (`BASKET_CREATED`, or `BASKET_REUSED` if
   resolved via lookup).

No basket construction step ever calls `order_check` or `order_send` — a
freshly `CREATED` basket has zero broker-side effect.

## 21. Quantity and allocation conservation, rounding policy

**Founder-approved policy: exact conservation only, zero tolerance,
fail closed on any residue.** For each child `i`:

```
raw_child_quantity_i = total_quantity * (target_allocation_percent_i / 100)
```

computed in exact `Decimal` arithmetic (never `float`), matching every
other quantity computation in this codebase. `raw_child_quantity_i` is
accepted **only if it already lands exactly on the broker's
`volume_step` grid** for this symbol — **no rounding is performed at any
step.** If any child's raw quantity does not land exactly on the step
grid, basket construction fails closed for the **entire** basket with
`BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE`. There is no rounding
direction the Founder approved, so none is invented.

Additionally, independently, for each child: `child_quantity > 0` (else
`BASKET_CHILD_QUANTITY_ZERO`); `child_quantity >= volume_min` (else
`BASKET_CHILD_QUANTITY_BELOW_MINIMUM`); `child_quantity <= volume_max`
(else `BASKET_CHILD_QUANTITY_ABOVE_MAXIMUM`).

And in aggregate: `sum(child_quantity) == total_quantity` exactly
(guaranteed automatically by the zero-tolerance-step rule above, but
independently re-verified as a defense-in-depth assertion; a mismatch
here fails closed with `BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE` rather
than ever being silently accepted); `sum(target_allocation_percent) == 100`
exactly (already guaranteed by the parent's own Phase 5 validation,
re-verified here; mismatch fails with `BASKET_ALLOCATION_SUM_INVALID`).

## 22. Order-type and target policy

A basket child inherits the parent's `order_type` and `entry_price`
**unchanged** — Phase 6 never converts market to limit, limit to market,
stop to market, an entry zone to an arbitrary price, or `BUY` to `SELL`.
Every child of one basket shares one entry order type and one entry price;
what varies per child is exclusively the take-profit target and its
quantity slice: **one shared entry instruction, N independent take-profit-
differentiated child orders**, each its own broker-native order with its
own ticket. Where the parent's economic meaning cannot be preserved
exactly under this model — for example a parent whose `order_type` is not
in Phase 5's governed `ORDER_TYPES` (`BUY_LIMIT`, `SELL_LIMIT`) — basket
construction fails closed with `BASKET_ORDER_TYPE_MISMATCH`.

Target ordering and uniqueness: children are ordered exactly as the
parent's `targets` array is ordered (index-preserving), and every
`target_price` within one basket must be distinct —
`BASKET_TARGET_NOT_UNIQUE` fails closed on a duplicate.

## 23. Basket preflight

Before any basket confirmation may be requested and before any child send,
independently re-validate, in addition to every Section 8 parent check:
`ModeService` current mode and capability grants; `TRL_BASKET_PLAN.v1`
schema/hash; parent proposal/order-intent schema and hash (re-fetched, not
cached); proposal and basket expiry; account fingerprint and demo-account
classification; strategy registration/approval and both Section 7
blockers; risk-policy hash and any active risk halt; symbol mapping,
tradeability, current session, tick freshness, spread (per currently-
required child); quantity limits and quantity step (per child, Section
21); stop-level and freeze-level constraints; target ordering and
allocation conservation; duplicate basket lookup (Section 17.3) and
duplicate child lookup (Section 20), per child; and any prior uncertain,
partial, or terminal basket/child state. Unknown or contradictory data at
any preflight step fails closed with the specific reason code.

## 24. Check sequence

Every currently-required child (Section 24.2) must pass a fresh
`order_check` before basket confirmation may be requested. Checks are
**not** run in parallel; they run sequentially, one at a time, through the
existing Phase 5 `order_check` boundary, invoked with the exact request
parameters extracted from that child's `TRL_BASKET_CHILD_INTENT.v1` —
never by constructing or reusing a Phase 5 `TRL_MT5_ORDER_INTENT.v1`
object for the child (Section 1.1).

1. `ModeService` authorization re-verified.
2. Basket and parent identity re-verified.
3. **The targeted child must not already be `FILLED` or otherwise
   terminal** — an attempt to check an already-`FILLED` child fails
   closed with `BASKET_CHILD_ALREADY_FILLED` rather than silently
   running (and potentially recording a contradictory result against) a
   settled child.
4. Fresh account/symbol/tick state re-verified for this child's
   instrument.
5. Call the (fake or real) adapter's `order_check` exactly once for this
   child, with this child's own quantity and target.
6. Normalize and persist the result as a `TRL_BASKET_CHECK_RESULT.v1`
   record (Section 11), bound to `basket_id`, `basket_child_id`, and
   `canonical_basket_child_hash_at_check` (`BASKET_CHILD_CHECK_RESULT`).
7. `order_send` is never called from within this step.

If any currently-required child's check fails: `basket_status` returns to
`CHECK_REQUIRED`; the failed child's failure reason is recorded; no child
is silently omitted and no replacement child is substituted. A successful
full check set does not, by itself, advance past `CHECK_COMPLETE`;
`AWAITING_CONFIRMATION`/`CONFIRMED` still require the separate Section 13
confirmation.

### 24.1 Check-freshness duration

A `TRL_BASKET_CHECK_RESULT.v1` is **fresh** if and only if
`now - checked_at_utc <= CHECK_FRESHNESS_SECONDS`, where
`CHECK_FRESHNESS_SECONDS` is the existing, already-committed Phase 5
constant (`mt5_execution_service.CHECK_FRESHNESS_SECONDS = 120`),
referenced here unchanged. Freshness is revalidated at three points: at
`request-basket-confirmation`, at `confirm-basket`, and immediately before
every individual child send (Section 26, step 3).

### 24.2 Currently-required children, and stale-check handling

**"Currently required" always means: not `FILLED` and not otherwise
terminal.** A `FILLED` child is never part of the required set again, is
never re-checked, and is never re-sent — its check and send records are
permanent (Section 11.1). Two distinct stale-check scenarios exist:

**A. Stale check with zero prior fills.** If any currently-required
child's check is found stale (at confirmation request, confirmation
accept, or immediately before a send) and no child of this basket has
ever reached `FILLED`: no automatic re-check is run; the child is not
sent; the active confirmation (if any) is invalidated
(`BASKET_CHILD_CHECK_STALE`, `BASKET_RECHECK_REQUIRED`); `basket_status →
"CHECK_REQUIRED"`; **every** currently-required child (not only the one
found stale) must pass a fresh check again, and a brand-new confirmation
must be requested and accepted again.

**B. Stale check after one or more prior fills.** If the same staleness is
found but one or more children of this basket have already reached
`FILLED`: every already-`FILLED` child's result is preserved permanently,
unmodified, and is **never** rechecked, resent, replaced, rolled back,
compensated, or counted as pending; the active confirmation is invalidated
(`BASKET_CHILD_CHECK_STALE`, `BASKET_RECHECK_REQUIRED`, both payloads
naming the current `confirmation_request_id`/`confirmation_cycle_number`);
no further child is sent; no check is run automatically; `basket_status →
"CHECK_REQUIRED"` — **this is explicitly not `PARTIALLY_COMPLETED`**
(Section 14.3/14.4) — and only the remaining, still-unsent, nonterminal
children require a fresh passing check before a **new confirmation cycle**
can be requested and accepted (Section 13.3, Section 13.1.1): the new
cycle's `authorized_prior_filled_child_ids` is recomputed to include every
child already `FILLED` (Founder test: "previously filled children are
excluded from the refreshed remaining set"), its
`authorized_remaining_child_ids` recomputed to contain only the
still-unsent children, and its `ordered_required_check_ids`/
`ordered_required_check_hashes` recomputed from their freshly passed
checks. `TRL_BASKET_STATUS.v1` continues to report `filled_child_count`/
`completed_quantity`/`remaining_quantity` truthfully throughout (Section
36).

## 25. Confirmation sequence (summary)

Covered fully in Section 13. Summarized flow: `CHECK_COMPLETE` →
(`request-basket-confirmation`, reusing an unchanged active request or
creating a new one per Section 13.3) → `AWAITING_CONFIRMATION` →
(`confirm-basket` with `CONFIRM-BASKET <16-hex>` exactly matching the
active request's challenge) → `CONFIRMED`. A rejected confirmation
attempt returns the basket to `CHECK_COMPLETE`. A staleness-triggered
invalidation instead returns the basket to `CHECK_REQUIRED`
(Section 24.2) — with prior fills fully preserved if any exist.

## 26. Send sequence

Children are sent **strictly sequentially**, one command per child, never
in parallel, never in reverse, never in a random or retry-derived order.
The service — never the CLI, never the operator — computes the exact next
eligible child from durable state. The CLI command takes **no
child-identifying argument at all** (`send-basket-next <basket_id>`,
Section 34).

**Live next-eligible-child rule, exact** (computed fresh from durable
journal state before every `send-basket-next` call — this is a *derived
service projection*, never a field read back off the confirmation record;
Section 13.4.1 explains why the two are deliberately different concepts):
the live next eligible child is the lowest `child_index` such that:

(a) it is a member of the active, `ACCEPTED` confirmation cycle's
`authorized_remaining_child_ids` (Section 13.1.1(B)) — a child never
authorized by this cycle can never be sent under it, regardless of any
other condition;
(b) it is not itself in a terminal child state (Section 14.5);
(c) every child with a lower `child_index` is either listed in that same
cycle's `authorized_prior_filled_child_ids` (Section 13.1.1(A)) **or** has
durably reached `FILLED` during this same cycle (i.e. via an earlier
`send-basket-next` call under this same accepted authorization) — the two
together always cover every lower-indexed child by the time this one
becomes eligible;
(d) it has a currently fresh `CHECK_PASSED` result whose `check_result_id`
is one of that cycle's `ordered_required_check_ids` (Section 13.1.1(D));
and
(e) it has no existing send reservation.

After any stale-check-triggered invalidation (Section 24.2) or any other
Section 13.6 invalidation, no child is eligible again until a **new**
cycle's checks and acceptance are completed; child ordering never resets
and no prior (already-`FILLED`) child ever becomes eligible again, in this
cycle or any later one.

Before each authorized child send:

1. Reload and validate the durable journal under the cross-process lock
   (Section 19).
2. Revalidate `basket_status == "CONFIRMED"` or (`"SENDING"` with the
   immediately prior child already `FILLED`) — never with the prior
   required child still unresolved (`BASKET_CHILD_NOT_NEXT_ELIGIBLE`).
3. Compute the live next eligible child per the rule above and revalidate
   **that specific child's** check freshness (Section 24.1/24.2) — a
   stale check here invalidates the confirmation and returns the basket
   to `CHECK_REQUIRED` rather than sending, with any prior fills fully
   preserved. Per Section 8 of the Founder's authorization-progression
   correction, this step also re-verifies that **every other** child still
   listed in `authorized_remaining_child_ids` but not yet `FILLED` still
   has a fresh required check — the same basket-wide freshness discipline
   Section 24.1 already establishes, now expressed in terms of the fixed
   `authorized_remaining_child_ids` set rather than a live "currently
   required" recomputation.
4. Revalidate the account fingerprint.
5. Revalidate demo-account classification.
6. Revalidate symbol/tick/spread for this child's instrument, fresh.
7. Confirm no risk halt is active.
8. Confirm the basket confirmation (Section 13) for the current cycle is
   `ACCEPTED`, unexpired, and not invalidated — **and confirm the child
   computed in step 3 is a member of that cycle's
   `authorized_remaining_child_ids`** (it always will be, by construction
   of the live-eligibility rule itself, since membership is rule (a)
   above; this is a defense-in-depth re-check, not a new condition). This
   replaces an earlier draft's incorrect requirement that the child equal
   a single, frozen `next_eligible_child_id` field on the confirmation
   record — a requirement that would have wrongly rejected every child
   past the first one sent under a cycle (Section 13.1's corrected design
   note).
9. Confirm no send reservation already exists for this `basket_child_id`
   (else `BASKET_CHILD_SEND_ALREADY_RESERVED`); confirm the child is not
   already `FILLED` (else `BASKET_CHILD_ALREADY_FILLED`); persist the
   reservation now, under the lock, as a
   `TRL_BASKET_CHILD_EXECUTION_RESULT.v1` record with
   `send_reserved_at_utc` set (`BASKET_CHILD_SEND_RESERVED`).
10. Release the lock.
11. Call the adapter's `order_send` **at most once** for this child,
    outside the lock, using the request parameters extracted from this
    child's `TRL_BASKET_CHILD_INTENT.v1`.
12. Normalize and persist the result into the same
    `TRL_BASKET_CHILD_EXECUTION_RESULT.v1` record
    (`BASKET_CHILD_SEND_RESULT`), update the child's execution state
    (Section 14.5), and roll the basket's `basket_status` forward per
    Section 14.1/14.3. A result of `FILLED` makes this record permanently
    immutable (Section 11.1).

The durable reservation from step 9 prevents any other process from
sending this same child. Only one child may ever be in a send-reserved or
uncertain state at a time for one basket — the next-eligible-child
computation in step 3 returning any child other than one with no
reservation yet is impossible by construction.

## 27. Rejection behavior

- **Child rejected, zero prior fills (first child ever sent):**
  `basket_status → "FAILED"`; do not send any later child.
- **Child rejected after >=1 prior child filled:**
  `basket_status → "PARTIALLY_COMPLETED"` (a permanent stop —
  Section 14.3); preserve every earlier `FILLED` result unchanged and
  immutable; do not send later children; `reconciliation_required`
  becomes `true`.
- Never: generate a replacement child, retry automatically, close earlier
  fills, claim rollback, submit a compensation trade, recheck a filled
  child, resend a filled child, or reset a filled child to any other state
  for any reason (Section 31).

## 28. Partial-fill behavior

A child `PARTIALLY_FILLED` result is represented exactly as
`PARTIALLY_FILLED` on that child (Section 14.5, terminal for Phase 6) —
never silently upgraded to `FILLED`, never downgraded to `REJECTED`, never
treated as a zero fill, and never treated as basket completion by itself.
A partial fill on any child stops further child submission and marks the
basket `PARTIALLY_COMPLETED` with `reconciliation_required = true`. The
exact broker response is preserved unmodified. This is a **child-level**
partial fill, kept terminologically and structurally distinct from the
**basket-level, permanent** `PARTIALLY_COMPLETED` status it produces
(Section 4, Section 14.3) — which is itself kept distinct from a merely
**recoverable** stale-check `CHECK_REQUIRED`-with-progress cycle
(Section 14.4).

## 29. Uncertain-result behavior

A timeout, malformed response, ambiguous result, or otherwise
`UNCERTAIN`/`MALFORMED` child send outcome: persists the uncertain result
verbatim (`BASKET_CHILD_UNCERTAIN`); marks the affected child
`FROZEN_PENDING_RECONCILIATION`; freezes the basket
(`basket_status → "FROZEN"`, `reconciliation_required = true`); stops all
further child submission unconditionally; retains the durable send
reservation (never released merely because the outcome was uncertain);
never automatically retries; survives process restart (Section 30);
requires later reconciliation, explicitly out of scope for Phase 6
(Section 33).

## 30. Restart behavior

On process restart, basket and child state is loaded exclusively from the
durable, hash-chained journal — loading never triggers any adapter call,
any MT5 connection, any symbol query, or any retry. Specifically: a basket
found `SENDING` with its most recently reserved child not yet resolved is
treated as `FROZEN`; a child with an existing send reservation is never
eligible to be sent again after restart; a `PARTIALLY_COMPLETED`,
`FAILED`, or `FROZEN` basket remains exactly that after restart; a
`CHECK_REQUIRED`/`CHECKING`/`CHECK_COMPLETE` basket (with or without prior
fills) resumes from exactly where it was, with every `FILLED` child's
record intact and untouched, and any check found stale on reload treated
per Section 24.2 exactly as if discovered live; an
`AWAITING_CONFIRMATION`/`CONFIRMED` basket whose confirmation has expired
by wall-clock time on reload is treated as expired — restart never
extends a confirmation's lifetime.

## 31. No rollback or compensation policy

Independent broker orders are not an atomic database transaction. This
contract states explicitly and without exception: a successful earlier
child is never assumed rolled back merely because a later child failed or
froze; no automatic close order is created for any child, filled or
otherwise; no compensation order, hedge, or reversal trade is created; no
cancellation of an already-filled child is claimed or attempted (and no
`CANCELLED` child state exists to even represent one — Section 14.5); no
all-or-nothing guarantee is made anywhere. A partial basket is reported as
partial success, truthfully, and nothing more is implied about it.

## 32. Adapter boundary

No new adapter is introduced. Every basket child `order_check`/`order_send`
call goes through the **existing** `mt5_execution_adapter.py` three-tier
boundary (disabled/fake/real) unchanged, invoked with the concrete request
parameters extracted from that child's `TRL_BASKET_CHILD_INTENT.v1`. The
optional `MetaTrader5` import remains reachable only through the existing
lazy real-adapter construction path, after authorized construction — never
from a basket schema module, never from `mode_service.py`, never from a
dashboard module, never from a test-discovery path. Automated tests use
fake adapters only. No `MetaTrader5` package installation is required or
performed by this contract or its future implementation.

## 33. Reconciliation boundary

Phase 6 **detects and freezes** uncertain and partial-success basket
states truthfully; it does **not** resolve them. Automatic reconciliation
is explicitly Phase 10 and is not implemented by this contract or its
future Phase 6 implementation. A `FROZEN` or `PARTIALLY_COMPLETED` basket
requires a human operator using the existing Phase 5
`reconcile`/manual-investigation path exactly as a frozen single-order
intent already does today; Phase 6 adds no new reconciliation mechanism.

## 34. CLI surface

Local-operator-only, mirroring the existing `mt5_execution_cli.py` naming
style:

| Command | Effect |
|---|---|
| `basket-status` | Overall basket capability/status, mirroring `mt5-status`; shows `manual_basket_execution` grant state and live/automated-disabled banners. |
| `inspect-basket <basket_id>` | Full `TRL_BASKET_PLAN.v1` document plus the current `TRL_BASKET_STATUS.v1` rollup (Section 36). |
| `build-basket <parent_order_intent_id>` | Construct (or reuse, via lookup) a basket from an eligible parent (Section 20). |
| `check-basket <basket_id>` | Run the check for the next currently-required child (Section 24). |
| `request-basket-confirmation <basket_id>` | Issue the exact challenge for the current confirmation cycle — reusing an unchanged, still-active, unexpired cycle exactly as-is, or allocating a brand-new cycle (new ID, new challenge) if the prior one expired or the basis changed (Section 13.1a/13.3) — displayed as `CONFIRM-BASKET <16-hex>`. |
| `confirm-basket <basket_id> <entry-text>` | `<entry-text>` must be exactly `CONFIRM-BASKET <16-hex-challenge>` (Section 13.2/13.4). |
| `send-basket-next <basket_id>` | Send exactly the service-computed next eligible child (Section 26); takes **no** child-identifying argument. |
| `inspect-basket-child <basket_id> <basket_child_id>` | Full `TRL_BASKET_CHILD_INTENT.v1` document plus its check/send history — read-only. |
| `basket-journal [--limit N]` | The raw basket-scoped journal event slice. |

Every mutating command uses `ModeService` and the authoritative basket
service; never duplicates permission logic; never automatically retries;
returns a stable nonzero exit code on rejection; redacts account identity;
never prints a credential; clearly displays `LIVE EXECUTION DISABLED`,
`AUTOMATED EXECUTION DISABLED`, and `MANUAL CONFIRMATION REQUIRED`; and
clearly displays partial-success/recoverable-recheck/uncertain/frozen
states with no summarization — in particular, a `CHECK_REQUIRED` basket
with prior fills must never be displayed as if nothing has happened. There
is no live-send command and no command that sends more than one child per
invocation.

## 35. Read-only HTTP surface

Only `GET`/`HEAD`, added to the existing `EXECUTION_API_ROUTES` mechanism
in `server.py` (which already returns `405 Allow: GET, HEAD` for every
other method on every registered route):

| Route | Returns |
|---|---|
| `/api/basket-execution-status` | Overall basket capability/status. |
| `/api/execution-baskets` | List of baskets (bounded, redacted). |
| `/api/execution-basket/<safe-id>` | One basket's `TRL_BASKET_STATUS.v1` document (Section 36). |
| `/api/execution-basket-journal` | Bounded, read-only basket-scoped journal slice. |

No route may create, check, confirm, send, retry, cancel, compensate,
reconcile, or otherwise mutate any basket state — this remains true
without exception, including for confirmation requests (Section 13.2/2.G).
`POST`, `PUT`, `PATCH`, and `DELETE` return `405` on every one of these
routes.

## 36. Basket status document (dashboard/CLI/HTTP read model) — `TRL_BASKET_STATUS.v1`

| Field | Meaning |
|---|---|
| `schema_version` | `"TRL_BASKET_STATUS.v1"` |
| `basket_id` | — |
| `basket_status` | Section 14.1 value |
| `reconciliation_required` | Section 14.4 derived boolean |
| `parent_proposal_id` / `parent_order_intent_id` | — |
| `broker_native_instrument` / `side` | — |
| `total_quantity` / `child_count` | — |
| `filled_child_count` | derived count of children currently `FILLED`, always reported truthfully regardless of `basket_status` (in particular, remains nonzero through a post-fill `CHECK_REQUIRED` recheck cycle — Section 14.4) |
| `completed_quantity` | derived sum of `child_quantity` over `FILLED` children |
| `remaining_quantity` | derived `total_quantity - completed_quantity` |
| `children` | ordered list of `{basket_child_id, target_price, target_allocation_percent, child_quantity, check_status, check_fresh, send_status, execution_state}` |
| `confirmation_status` | `NOT_REQUESTED` / `AWAITING` / `ACCEPTED` / `EXPIRED` / `INVALIDATED` — mirrors the current cycle's own `status` (Section 12) exactly; there is no `REJECTED` value here, because a wrong confirmation entry is an attempt-level journal event (`BASKET_CONFIRMATION_REJECTED`, Section 13.4), never a request-lifecycle status |
| `active_confirmation_request_id` | nullable; the current cycle's `confirmation_request_id`, if any |
| `active_confirmation_cycle_number` | nullable; the current cycle's `confirmation_cycle_number`, if any — a rising count across a basket's lifetime is itself informative (a basket on cycle `4` has needed reconfirmation three times) |
| `authorized_start_child_id` | nullable; the active cycle's `authorized_start_child_id` (Section 13.1.1(C)), display-only |
| `authorized_remaining_child_ids` | nullable; the active cycle's complete `authorized_remaining_child_ids` (Section 13.1.1(B)), display-only |
| `live_next_eligible_child_id` | nullable; the **current, freshly derived** next-eligible child (Section 26) — distinct from `authorized_start_child_id`, which never changes for the life of the cycle; this field is what actually advances as children fill |
| `created_at_utc` / `expires_at_utc` | — |
| `rejection_reasons` | bounded list drawn from `BASKET_REASON_CODES` |
| `terminal_reason` | nullable; populated once `basket_status` reaches a terminal value (Section 14.2), summarizing why (e.g. the specific child rejection, freeze cause, or blocker) |
| `canonical_basket_plan_hash` | — |

`filled_child_count`, `completed_quantity`, `remaining_quantity`, and
`live_next_eligible_child_id` are all derived on read from the permanent
`TRL_BASKET_CHILD_EXECUTION_RESULT.v1` records and the active
confirmation's fixed `authorized_remaining_child_ids` — none of them is a
separately stored mutable counter requiring its own consistency proof, and
none of them ever overwrites or is confused with the immutable
authorization-checkpoint fields (`authorized_start_child_id`,
`authorized_remaining_child_ids` themselves) they are derived alongside.

## 37. Dashboard requirements

Read-only. No `innerHTML`. No browser-supplied value is ever authoritative
for any basket decision. Displays, at minimum: current operating mode;
`LIVE EXECUTION DISABLED`/`AUTOMATED EXECUTION DISABLED` banners; whether
`manual_basket_execution` is currently granted; parent identity; child
count and per-child quantities/targets; check states and freshness;
confirmation state; send states; `filled_child_count`/`completed_quantity`
truthfully, even during a recoverable recheck cycle; partial-success
state, truthfully, with no "success" framing; uncertain/frozen state with
a visible reconciliation-required warning; rejection reasons; and the
SMA-001/FIB-001 blocker status.

## 38. Persistence and journal rules

The **existing** Phase 5 execution journal is extended, not replaced.
Every rule R2-007 already establishes remains unchanged and applies
identically to basket events: local, durable, append-only, atomically
persisted, strictly bounded, hash-chained, corruption-detecting,
credential-free, and safe to load without any adapter activity
whatsoever. No second authoritative journal, no second storage file, and
no second hash-chain are introduced. Existing (Phase 5) event schemas and
validation are not changed incompatibly — new basket event types are
additive entries in the same closed `EVENT_TYPES` tuple (Section 16),
sharing the same unchanged event envelope schema.

## 39. Credential handling

Identical to R2-007 Section 12, unchanged and unweakened: no broker
credential, terminal secret, account secret, or credential-reconstructing
value ever appears in a basket log line, exception message, HTTP response,
CLI output, or exported report. Fingerprint values used in any basket
identity computation are always the existing hashed
`account_fingerprint_hash`, never the raw login/company/server. Neither
the basket confirmation challenge (Section 13.2) nor any confirmation
identity/basis field (`confirmation_request_id`, `confirmation_basis_hash`)
is ever treated or stored as a secret — none of them are broker/account
values; they are content-derived binding codes.

## 40. Testing requirements (for the future implementation checkpoint)

The later Phase 6 implementation checkpoint must add deterministic,
isolated-temporary-storage, fake-adapter-only tests covering at minimum:
every item in this contract's state machine (Section 14) including the
`CREATED`/`REJECTED`/`BLOCKED`/`FAILED`/`PARTIALLY_COMPLETED`/recoverable-
`CHECK_REQUIRED`-with-progress distinctions; every reason code
(Section 15) and event type (Section 16) with both a passing and a
governed-failing case; exact conservation (Section 21); order-type/target
policy (Section 22); the full check→confirm→send-next sequence including
the exact `CONFIRM-BASKET <16-hex>` syntax parser; the full confirmation-
cycle model (Section 13), specifically proving: (1) a repeated
`request-basket-confirmation` call while the current cycle remains active
returns the identical `confirmation_request_id`/`challenge_hex`/
`confirmation_cycle_number`, and does not update `requested_at_utc`/
`expires_at_utc`; (2) a mere status-inspection call never extends the
confirmation window; (3) an expired, never-accepted cycle's record is
permanently immutable after its `EXPIRED` transition (byte-for-byte
identical `confirmation_request_id`/`challenge_hex`/timestamps before and
after); (4) an expired cycle's challenge is rejected with
`BASKET_CONFIRMATION_EXPIRED` even after a newer cycle exists, never
accepted; (5) requesting again after expiry allocates the next cycle
number and produces a genuinely different `confirmation_request_id` and
`challenge_hex`; (6) a confirmation-basis change (independent of expiry)
also produces a new cycle, new request ID, and new challenge, and
invalidates the prior cycle; (7) two concurrent
`request-basket-confirmation` calls for the same basket allocate at most
one new cycle number between them; (8) restart preserves the highest
cycle number already recorded for a basket, and a corrupted/unreadable
journal fails closed rather than restarting numbering at `1`; (9) an
`ACCEPTED` cycle can never be accepted a second time; (10) an invalidated
`ACCEPTED` authorization is never reactivated, and continuation always
requires a brand-new cycle; **(11) the multi-child authorization-
progression model (Section 13.1/13.1.1/13.4.1, Section 26), specifically
proving**: one accepted confirmation cycle authorizes the sequential
sending of every child in `authorized_remaining_child_ids`, not merely the
first one; a first child reaching `FILLED` requires no new confirmation
before the second child is sent; a first child reaching `FILLED` does not
change `confirmation_basis_hash` on the active cycle; the live
next-eligible child (Section 26) advances from child to child while
`authorized_start_child_id` on the confirmation record itself never
changes; no child is ever sent automatically as a side effect of another
child filling; every child still requires its own separate
`send-basket-next` call; a child cannot be skipped, reordered, or sent
out of `authorized_remaining_child_ids`'s membership; a stale required
check invalidates the accepted authorization and forces a new cycle whose
`authorized_remaining_child_ids` excludes every already-filled child;
concurrent `send-basket-next` calls reserve the same live next-eligible
child at most once; restart preserves progress under the same still-valid
accepted authorization (a `FILLED` child before restart remains `FILLED`
and excluded from any later cycle's `authorized_remaining_child_ids`
after restart); a wrong `confirm-basket` entry produces
`BASKET_CONFIRMATION_REJECTED` as an attempt-level event without creating
a competing request and without introducing any `"REJECTED"` value into
the confirmation record's own `status` field (which remains `"REQUESTED"`
afterward, absent a separate expiry/basis-change trigger); and ordinary
read-only status inspection never alters the confirmation window,
progression, or authorization in any way; the two distinct stale-check
scenarios
(Section 24.2.A zero-fills and Section 24.2.B post-fill, proving a
`FILLED` child's record is byte-for-byte unchanged after a post-fill
recheck cycle and that `basket_status` in that case is `CHECK_REQUIRED`,
never `PARTIALLY_COMPLETED`); `send-basket-next` never accepting an
out-of-order child because it never accepts a child argument at all;
rejection/partial-fill/uncertain behavior including restart persistence;
concurrent basket creation producing exactly one basket; concurrent
`confirm-basket` producing at most one accepted event for at most one
cycle; concurrent child send calling `order_send` at most once; duplicate
protection across restart; corrupted-journal fail-closed with zero
adapter calls; lock timeout fail-closed with no unlocked fallback; HTTP
405 on every mutation method for every new route, including confirmation
request/accept; no `innerHTML` in the dashboard extension; the corrected
child-state vocabulary (proving no code path ever produces `CANCELLED` or
a child-level `AWAITING_CONFIRMATION`, and that `EXPIRED`/`BLOCKED` are
produced only by the exact basket-transition rules in Section 14.5);
Phase 5 backward-compatibility regression tests (Section 1.1); and that
all existing Phase 5 tests continue to pass unmodified and unweakened.

## 41. Manual rehearsal requirements (for the future implementation checkpoint)

The later implementation checkpoint must rehearse, using isolated temporary
storage and fake adapters only: mode-gated denial in `OFF`/`RESEARCH`/
`SYNTHETIC_PAPER`; SMA-001/FIB-001 remaining blocked (`basket_status ==
"BLOCKED"`); deterministic construction and reuse of a basket from a
clearly labeled hypothetical test-only parent fixture; exact conservation;
the full check→confirm→send-next sequence, using a basket with at least
three children, rehearsed to demonstrate **one** accepted confirmation
authorizing **all three** sequential sends — confirming exactly once,
then calling `send-basket-next` three separate times with no further
confirmation prompt or challenge entry in between, and verifying at each
step that `confirmation_basis_hash`/`confirmation_request_id`/
`confirmation_cycle_number` on the active record are unchanged from
acceptance through the final fill; a wrong-confirmation-syntax rejection
and a wrong-request-confirmation rejection (a challenge belonging to a
different cycle or a different basket); a
request-basket-confirmation-called-twice-unchanged rehearsal proving reuse
(identical `confirmation_request_id`/`challenge_hex`/`confirmation_cycle_number`
both times, unchanged timestamps); a confirmation-expiry rehearsal proving
the expired cycle's record is permanently unchanged, its old challenge is
rejected with `BASKET_CONFIRMATION_EXPIRED` specifically, and a fresh
request allocates the next cycle number with a genuinely different
challenge; a check-goes-stale-before-any-fill rehearsal (Section 24.2.A);
a check-goes-stale-after-one-fill rehearsal proving the filled child
survives untouched, a new confirmation cycle is required, and
`basket_status` becomes `CHECK_REQUIRED`, not `PARTIALLY_COMPLETED`
(Section 24.2.B); a first-child-rejected (`FAILED`) rehearsal; a
later-child-rejected-after-fills (`PARTIALLY_COMPLETED`) rehearsal; an
uncertain-child (`FROZEN`) rehearsal; two-process concurrent basket
creation, concurrent same-child send, and concurrent
`request-basket-confirmation` (proving at most one new cycle is
allocated); a corrupted-journal rehearsal, including one that specifically
corrupts confirmation-cycle history and confirms the operation fails
closed rather than restarting cycle numbering at `1`; HTTP
mutation-method rehearsal (405 on every route, including any confirmation
route); and full process/port cleanup at the end.

## 42. Remaining blockers

- **SMA-001** — blocked by `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`.
  Independently re-enforced at basket-construction time (`basket_status ==
  "BLOCKED"`).
- **FIB-001** — blocked by `STRATEGY_PARAMETERS_NOT_APPROVED`.
  Independently re-enforced the same way.
- **MT5 demo account fingerprint** — unchanged external prerequisite from
  Phase 5. Automated tests are unaffected (fake adapter only).
- Every other Phase 5 external prerequisite (`TRL_BLOCKERS.md`) applies
  unchanged to Phase 6 wherever it would gate the underlying parent
  single-order intent.

## 43. Acceptance criteria (contract-authoring checkpoint)

This document is ready for Founder review when it: identifies TRL-R2-009
as the governing Phase 6 contract without touching TRL-R2-008; leaves
`TRL_MT5_ORDER_INTENT.v1` and every other Phase 5 `v1` schema/function/
persisted document completely unchanged (Section 1.1); separates
confirmation-basis identity (the execution-authority snapshot, Section
13.1) from confirmation-cycle identity (a durable, monotonic, never-reused
`confirmation_cycle_number`, Section 13.1a) so that a same-basis re-request
reuses a cycle exactly while an expired-and-reissued cycle for that same
basis is always a genuinely new, separately identified, separately
challenged cycle; makes `confirmation_request_id` and `challenge_hex`
unique per cycle (via the cycle's own fixed timestamps/number in the hash
material, Section 13.1b–13.1c) so an expired or invalidated challenge can
never coincide with, or later be accepted as, any other cycle's challenge;
guarantees an expired or invalidated confirmation record is permanently
immutable — never rewritten, never reactivated, never has its identity
fields changed — with continuation always requiring a brand-new cycle;
defines the confirmation basis as a **fixed authorization checkpoint**
(`authorized_prior_filled_child_ids`/`authorized_remaining_child_ids`/
`authorized_start_child_id`, Section 13.1.1), computed once at request
time and never recomputed against live post-acceptance progress, so that
**one accepted confirmation correctly authorizes the entire sequential
send of every child it names** without a normal successful fill ever
invalidating it, changing its basis, or requiring reconfirmation —
resolving a genuine contradiction an earlier draft's live-recomputed basis
would have caused (invalidating the confirmation after the very first
successful child); permanently protects every `FILLED` child from
re-check, re-send, or reset, including through a post-fill stale-check
recheck cycle that returns the basket to `CHECK_REQUIRED` (not
`PARTIALLY_COMPLETED`) while preserving truthful progress reporting;
clarifies that a wrong confirmation entry is an attempt-level journal
event (`BASKET_CONFIRMATION_REJECTED`) that never creates a competing
request and never introduces a contradictory `"REJECTED"` value into the
confirmation record's own status vocabulary; defines a corrected, minimal,
Founder-approved child-state vocabulary with no `CANCELLED` and no
child-level `AWAITING_CONFIRMATION`; defines exact, deduplicated
reason-code and event vocabularies with no duplicate-meaning entries;
keeps `REJECTED`/`BLOCKED`/`FAILED`/`PARTIALLY_COMPLETED` truthfully
distinct from each other and from a recoverable recheck cycle; defines the
narrow `manual_basket_execution` capability without widening
`basket_execution`; keeps SMA-001 and FIB-001 fully blocked; keeps the
HTTP/dashboard surface strictly read-only (including for every
confirmation operation); and reuses the existing Phase 5 adapter, journal,
and locking architecture without introducing a second implementation of
any of them.

## 44. Phase 3 amendment reference

The exact, narrow amendment made to `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`
alongside this contract is recorded in that document directly (Section
3.1) and summarized in Section 6 above. No other Phase 3 rule changes.
Reviewed against this correction pass and confirmed to need no further
change — its only R2-009 cross-references are by section number.

## 45. Explicit statement

**Phase 6, as governed by this contract, is controlled, manual, demo-only
basket execution and nothing more.** No automated basket path, no live
basket path, no scheduled or unattended basket path, no automatic
reconciliation, no compensation trade, no cancellation of any kind, and no
rollback claim exists anywhere in this design. Every basket document is a
separate, independently versioned schema; `TRL_MT5_ORDER_INTENT.v1` and
every other Phase 5 `v1` schema, function, and persisted record are
completely unchanged. A `FILLED` child's result is permanent and is never
reset by any later event in this contract, including a recoverable
stale-check recheck cycle. **An expired or invalidated confirmation
challenge never becomes valid again, under any circumstance** — every
reconfirmation, for any reason, is a brand-new, separately numbered,
separately identified, separately challenged confirmation cycle, and the
append-only journal never rewrites or reactivates a prior one.
**Phase 7 (TradingView webhook intake) is
explicitly excluded and is not started, referenced as available, or
prepared for by any part of this contract.** This contract-authoring
checkpoint itself implements no source code, modifies no test, and stages,
commits, or pushes nothing.
