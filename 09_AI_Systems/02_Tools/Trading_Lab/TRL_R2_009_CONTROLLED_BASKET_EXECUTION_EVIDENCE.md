# TRL-R2-009 Controlled Basket Execution (Phase 6) — Implementation and Evidence

> **DEMO ONLY — LIVE EXECUTION DISABLED — AUTOMATED EXECUTION DISABLED — MANUAL CONFIRMATION REQUIRED FOR EVERY CHILD SEND — NO REAL ORDER WAS EVER SUBMITTED**

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-009-BASKET-EXECUTION-EVIDENCE-001 |
| Document Type | Implementation and Evidence Record |
| Status | Implemented, tested (900 automated tests, two identical zero-failure discovery runs), manually rehearsed via the real CLI entry points including true separate-process proof; **held by the Founder for correction once (identity circularity, partial-fill governance, full-suite recovery, test-count arithmetic, true cross-process proof — Decision Log entry 2026-08-01-020), corrected, and re-verified — see Section 21**; **Founder-approved and locally committed; remote push remains a separate, later, Founder-authorized checkpoint** |
| Version | 2.0 (supersedes v1.0's child-identity formula and partial-fill status — see Section 21) |
| Date | 2026-08-02 |
| Owner | Abdulrahman Alsakkaf |
| Checkpoint | Phase 6 (`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md`) |
| Depends on | Phase 5 (`TRL_R2_007_MT5_EXECUTION_CONTRACT.md`, adapter/journal/lock reused unchanged), Phase 3 (`ModeService`, extended with one new capability) |
| Feeds | Phase 10 (reconciliation of `FROZEN`/`PARTIALLY_COMPLETED` baskets) — not started |

## 1. Scope

Phase 6 implements exactly TRL-R2-009's controlled, manual, demo-only, 2–4-child basket
execution flow: deterministic basket/child construction from an already-eligible Phase 5 parent
order intent, per-child `order_check`, a single confirmation cycle authorizing the complete
ordered remaining child set, one explicit `send-basket-next` per child with no automatic
progression, truthful partial/rejection/uncertain terminal outcomes, and no retry, rollback, or
compensation. No new adapter, no new journal, no new lock. Live and automated basket execution
remain entirely unimplemented; SMA-001 and FIB-001 remain fully blocked.

## 2. Modules

| Module | Role |
|---|---|
| `basket_execution_data.py` (new) | Six independent schemas, deterministic identities, quantity/allocation conservation, the closed `BASKET_REASON_CODES`/event-type-adjacent vocabularies. Pure data/validation — no I/O, no MetaTrader5 import. |
| `basket_execution_service.py` (new) | The sole authority for basket decisions — `BasketExecutionService` (`build_basket`, `check_basket`, `request_basket_confirmation`, `confirm_basket`, `send_basket_next`, plus read-only status/inspect/journal methods) and `DisabledBasketExecutionService`. |
| `basket_execution_cli.py` (new) | Local-only operator CLI: `basket-status`, `inspect-basket`, `build-basket`, `check-basket`, `request-basket-confirmation`, `confirm-basket`, `send-basket-next`, `inspect-basket-child`, `basket-journal`. |
| `mt5_execution_journal.py` (modified, additive only) | `EVENT_TYPES` gains the 25 Section-16 basket event types verbatim, in contract order. No Phase 5 event type renamed, removed, or reinterpreted. |
| `mode_service.py` (modified, additive only) | `CAPABILITIES` gains `manual_basket_execution`; `_CAPABILITY_MATRIX["MT5_DEMO_MANUAL"]` gains it. No other mode's row changed; `basket_execution` (the broad, still-reserved-for-later-automated-modes capability) is untouched. |
| `app.py` (modified) | `_basket_service_for_mode` / `_validate_basket_subsystem_consistency`, mirroring `_execution_service_for_mode` exactly — same adapter-tier selection rule, same default journal/account-fingerprint construction — plus `run_server`/`main` wiring (status banner, shutdown chain, `basket_service=` passthrough). |
| `server.py` / `service.py` (modified) | Four read-only routes (Section 6 below); GET/HEAD only. |
| `static/index.html` / `static/app.js` (modified) | Read-only "Basket execution" dashboard panel; no `innerHTML`. |

## 3. Schemas and identities

Six schemas, each independently versioned, none touching `TRL_MT5_ORDER_INTENT.v1`:
`TRL_BASKET_PLAN.v1`, `TRL_BASKET_CHILD_INTENT.v1`, `TRL_BASKET_CHECK_RESULT.v1`,
`TRL_BASKET_CONFIRMATION.v1`, `TRL_BASKET_CHILD_EXECUTION_RESULT.v1`, `TRL_BASKET_STATUS.v1`
(read model). Every deterministic-identity formula (`basket_lookup_key`, `basket_id`,
`basket_child_lookup_key`, `basket_child_id`, `check_result_id`, `confirmation_request_id`,
`challenge_hex`) matches Section 17 exactly, including the no-nonce requirement and the
per-confirmation-cycle uniqueness fold (`confirmation_cycle_number` + fixed
`requested_at_utc`/`expires_at_utc` in the hash material — Section 13.1b/c).

**Superseded by the Founder correction round (Section 21, Decision Log entry
2026-08-01-020):** the basket-child lookup key formula previously listed
`canonical_basket_plan_hash` as an input, undisclosed-substituted here with `basket_id` as a
workaround. That substitution is **not approved**. The Founder found the underlying formula
itself circular — a plan hash can never be an input to the child IDs that are themselves part
of that plan hash — and specified the corrected, non-circular formula: the lookup key now
derives from `basket_id` plus the immutable `parent_proposal_id`/`canonical_parent_proposal_hash`
and `parent_order_intent_id`/`canonical_parent_order_intent_hash`, plus each child's own economic
fields, under a new domain separator `TRL-BASKET-CHILD-LOOKUP.v1` — never from
`canonical_basket_plan_hash`. See Section 21.2 for the full correction; the existing `bc_`/16-hex
`basket_child_id` prefix and length are unchanged.

## 4. Conservation

`compute_child_quantities` (2–4 children, `Decimal` arithmetic, zero rounding) fails the entire
basket closed on the first violated rule: exact allocation sum of 100, exact step alignment (no
remainder redistribution), volume-min/max bounds, non-zero quantity, and exact aggregate-equals-
total conservation. `validate_basket_plan` independently re-verifies the same conservation
invariant from the assembled document. 51 dedicated tests in `test_basket_execution_data.py`
cover the schema/identity/conservation layer in isolation.

## 5. ModeService capability

`manual_basket_execution` — granted only to `MT5_DEMO_MANUAL`; denied to `OFF`, `RESEARCH`,
`SYNTHETIC_PAPER`, `MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`, `MT5_LIVE_AUTOMATED` (Section 6.1).
Necessary but never sufficient alone: basket construction additionally requires nothing beyond
`manual_basket_execution`; child `order_check` additionally requires `mt5_order_check`; child
`order_send` additionally requires `mt5_order_send` and `manual_broker_execution` — all three
already existed in `MT5_DEMO_MANUAL`'s Phase 5 grant, so this is the only capability-matrix change
this contract required. `test_basket_execution_service.CapabilityGatingTests` proves exact
presence/absence across every mode and that no CLI/HTTP/direct-call path bypasses
`_require_capability`.

## 6. Phase 5 compatibility

`TRL_MT5_ORDER_INTENT.v1` and every Phase 5 identity function are byte-for-byte unchanged —
`basket_execution_service.py` only *reads* an existing parent intent via `med.validate_order_intent`
and the Phase 5 journal's own hash-chain integrity; it never constructs, mutates, or re-hashes one.
The same `ExecutionJournalWriter`, the same `_CrossProcessFileLock`/`_ThreadLock`, and the same
three-tier adapter boundary (`disabled`/`fake`/`real`) are reused, never duplicated — `app.py`'s
`_basket_service_for_mode` calls the identical `_execution_adapter_for_mode` tier-selection rule
and the identical default journal/fingerprint construction `_execution_service_for_mode` uses, so
both services always agree on adapter tier, journal file, and fingerprint without reaching into
either service's private attributes. All 27 Phase 5 journal tests, all 53 mode-service tests, and
every other pre-existing test file pass unchanged (Section 10 below).

## 7. Journal extension

25 new `BASKET_*` event types appended verbatim, in Section-16 order, to `EVENT_TYPES` — purely
additive; no Phase 5 event renamed or removed. Confirmed via the existing
`test_mt5_execution_journal.py` / `test_mt5_execution_journal_lock.py` (27/27 passing unchanged)
and a new structural test asserting Phase 5 event types remain present alongside the basket ones.

## 8. Confirmation basis, cycles, and expiry

The "authorization checkpoint" design from Decision Log entry 016: `_build_confirmation_basis`
computes a fixed snapshot (`authorized_prior_filled_child_ids`, `authorized_remaining_child_ids`,
`authorized_start_child_id`, ordered check IDs/hashes) once, at request time. Ordinary successful
progress — a child reaching `FILLED`, the live next-eligible child advancing — never touches this
snapshot or invalidates the cycle; only the closed list of Section 13.6 triggers (stale check,
fingerprint change, capability loss, rejection/partial/uncertain result, basket-plan/child-set
mismatch, integrity uncertainty, terminal `basket_status`) does. `CHECK_FRESHNESS_SECONDS = 120`
and `CONFIRMATION_LIFETIME_SECONDS = 300` are the exact, unchanged Phase 5 constants (referenced
via `mt5_execution_service`, never redefined). An active, unexpired, same-basis `REQUESTED` cycle
is reused byte-for-byte (`BASKET_CONFIRMATION_REQUEST_REUSED`) rather than reissued; an expired or
basis-changed cycle is immutably closed (`status`/`invalidated_at_utc`/`invalidation_reason` or
`expired_at_utc` only — every other field frozen) and a brand-new cycle is opened with a
monotonically incremented `confirmation_cycle_number`, so an old challenge can never coincide with
a new one and is never reactivated. `test_basket_execution_service.ConfirmationCycleTests` (7
tests) exercises cycle 1, active-request reuse, format/challenge rejection, second-acceptance
rejection, expiry immutability plus cycle-2 uniqueness, and restart-safe cycle numbering.

## 9. Sequential progression and send-basket-next

One accepted cycle authorizes every remaining child in its fixed set — not just the next one.
`send_basket_next` takes no child-identifying argument; `_compute_live_next_eligible` derives the
next child live, on every call, from cycle membership plus current fill state, enforcing strict
order (a lower-index unsent-and-not-prior-authorized child always blocks a later one) and
at-most-one durable `SEND_RESERVED` reservation. `test_basket_execution_service.SequentialSendTests`
(5 tests) proves one cycle authorizing all four sends, zero automatic sends between children, the
argument-free command's inability to skip, restart-safe mid-basket resumption, and exactly one
`order_send` adapter call per child.

## 10. Stale-check recovery

A single shared method, `_verify_fresh_or_recover`, implements both Section 24.2 cases by
recognizing "currently required" already excludes `FILLED` children in both: zero-prior-fill
staleness returns every unsent child to `CHECK_REQUIRED`; post-fill staleness does the same while
leaving every `FILLED` child's record permanently untouched — never `PARTIALLY_COMPLETED` on its
own. Either case invalidates the active cycle (if any) and requires fresh rechecks plus a brand-new
cycle before any further send. `test_basket_execution_service.StaleCheckRecoveryTests` (5 tests)
proves both cases, no automatic recheck, and old-challenge rejection after a new cycle.

## 11. Rejection, partial-fill, and uncertain-result behavior

- **Rejection, zero prior fills:** `basket_status → FAILED`.
- **Rejection, ≥1 prior fill:** `basket_status → PARTIALLY_COMPLETED`, `reconciliation_required = true`; every earlier `FILLED` child preserved immutable.
- **Partial fill:** child `→ PARTIALLY_FILLED` (terminal for Phase 6, never upgraded/downgraded); `basket_status → FROZEN` (never `PARTIALLY_COMPLETED`, **regardless of prior fills** — corrected by the Founder correction round, Section 21.3), `reconciliation_required = true`.
- **Uncertain/malformed:** child `→ FROZEN_PENDING_RECONCILIATION`; `basket_status → FROZEN`, `reconciliation_required = true`; the send reservation is retained, never released; no automatic retry; survives restart.

All three invalidate the active confirmation cycle as part of the same transition (never left
dangling `ACCEPTED` on a terminal basket) and set `terminal_reason` plus append to
`rejection_reasons`. `test_basket_execution_service.ResultBehaviorTests` (6 tests) covers all four
outcomes plus restart-preserves-`FROZEN` and no-rollback/no-compensation.

### 11.1 Genuine contract gap found and resolved (Founder decision)

While implementing `_finalize_send`, the closed `BASKET_REASON_CODES` list (Section 15) had no
code for a child `order_send` coming back `REJECTED` or `PARTIALLY_FILLED` — only
`BASKET_CHILD_CHECK_FAILED` existed, and that covers only the earlier `order_check` stage. The
draft implementation papered over this with a dead `"X" if False else new_status` expression that
evaluated to a basket-status string (not a governed reason code), silently falling back to the
wrong `BASKET_FROZEN` invalidation reason. This was raised to the Founder via a direct question
rather than resolved unilaterally (see `TRL_DECISION_LOG.md` entry 2026-08-01-019); the Founder
chose to add two new, narrowly-scoped, additively-named codes —
`BASKET_CHILD_SEND_REJECTED` and `BASKET_CHILD_SEND_PARTIALLY_FILLED` — to both
`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` Section 15 and `basket_execution_data.py`.
No approved behavior changed; only the missing vocabulary entry was supplied. `_finalize_send` now
uses these exactly, and `_check_basket_expiry`'s pre-existing `terminal_reason` handling was made
consistent by also appending to `rejection_reasons`.

### 11.2 Interpretation ambiguity — resolved by the Founder (superseded)

An earlier draft of this document disclosed an apparent tension between Section 28 (which then
stated a `PARTIALLY_FILLED` child unconditionally marks the basket `PARTIALLY_COMPLETED`) and
Section 14.3's general definition of `PARTIALLY_COMPLETED`, which requires "at least one child
reached `FILLED`" — a first-child partial fill (zero prior `FILLED` children) was representable
under the old Section 28 wording but not Section 14.3's general one. The Founder correction round
(Section 21.3) resolved this by correcting Section 28 itself: a partial fill now freezes the
basket unconditionally, so it never needs to satisfy `PARTIALLY_COMPLETED`'s prior-fill
requirement in the first place. This is no longer an interpretation choice; it is the contract's
own, corrected rule.

## 12. No retry, no rollback, no compensation

No code path in `basket_execution_service.py` re-sends a filled or terminal child, generates a
replacement child, closes an earlier fill, or creates any compensating/hedging order. No
`CANCELLED` child state exists. `ResultBehaviorTests.test_no_rollback_or_compensation_on_later_failure`
and the structural absence of `"CANCELLED"` from `BASKET_CHILD_STATES` (asserted in
`test_basket_execution_data.VocabularyClosureTests`) are the direct evidence.

## 13. Concurrency and restart

Every mutating method acquires the same `ExecutionJournalWriter.acquire_creation_lock()` Phase 5
uses, which reloads the writer's in-memory state from the durable store before yielding — so a
second, later-constructed `BasketExecutionService` instance reading the same journal always sees
every prior basket/child/confirmation-cycle event, with no adapter call ever made merely by
loading. `test_basket_execution_service.JournalAndConcurrencyTests` and repeated restart-simulating
service reconstructions inside `ConfirmationCycleTests`/`SequentialSendTests`/`ResultBehaviorTests`
exercise this directly.

## 14. CLI

`basket_execution_cli.py` mirrors `mt5_execution_cli.py`'s exact conventions: local-only mutation,
stable nonzero rejection exit codes, `LIVE EXECUTION DISABLED`/`MANUAL CONFIRMATION REQUIRED`
banners on every mutating command, and — critically — `send-basket-next` takes no child argument,
so the CLI cannot compute or select its own next child. 17 tests in
`test_basket_execution_cli.py` cover argument parsing, mode-gated fail-closed behavior at `OFF`,
output redaction, and stable exit codes.

### 14.1 Genuine bug found and fixed during CLI rehearsal

`confirm_basket` called `bed.parse_confirmation_entry(entry_text)` — raw, untrusted, operator-typed
text — before entering its own `try`/`except` block, and `parse_confirmation_entry` raises
`basket_execution_data.BasketValidationError`, a type the CLI's `except
basket_execution_service.BasketExecutionServiceError` clause does not catch. A malformed
confirmation phrase (e.g. a bare `"yes"`) would have crashed the CLI process with an uncaught
traceback instead of the required stable, governed rejection. Found while building the manual
rehearsal script (not by an automated test, since the automated suite happened to only exercise
this path directly against the service, where the wrong-but-real exception type still satisfied a
loosely-written assertion — that assertion has been corrected alongside the fix). Fixed by wrapping
the call and re-raising as `BasketExecutionServiceError(error.reason_code, ...)`, exactly matching
every other governed rejection in `confirm_basket`. The analogous internal-consistency
`bed.validate_*`/`compute_child_quantities` calls elsewhere in the service were deliberately left
unwrapped: unlike operator-typed confirmation text, they process data the service just computed
internally from already-validated sources, so a failure there would indicate a genuine internal
defect rather than a normal, expected external-input rejection.

## 15. HTTP and dashboard

Four read-only routes, GET/HEAD only, every mutation method 405 with `Allow: GET, HEAD`:
`/api/basket-execution-status`, `/api/execution-baskets`, `/api/execution-basket/<safe-id>`
(id validated against the exact `bsk_[0-9a-f]{32}` shape before ever reaching the basket service;
anything else is treated as an unregistered route — 404 on GET/HEAD, generic 405 on mutation),
`/api/execution-basket-journal` (bounded to the 500 most recent events, per Section 35's explicit
"bounded" requirement). The dashboard's new "Basket execution" panel displays operating mode,
capability grant, the basket list, and the latest basket's full detail (confirmation
cycle/status, authorized child set, live next-eligible child, completed/remaining quantity,
reconciliation state, terminal/rejection reasons, and per-child check/send state) using
`textContent`/`createElement` only — no `innerHTML` anywhere in `renderBasketExecution`. 16 tests
in `test_basket_execution_http.py` cover every route's 200/404/405 behavior and the no-`innerHTML`
guarantee.

## 16. Testing

### 16.1 New Phase 6 test files

| File | Tests | Focus |
|---|---|---|
| `test_basket_execution_data.py` | 52 | Schemas, deterministic identities, conservation, vocabulary closure |
| `test_basket_execution_service.py` | 45 | Full lifecycle: capability gating, build/check/confirm/send, confirmation cycles, stale-check recovery, rejection/partial/uncertain, journal/restart |
| `test_basket_execution_cli.py` | 17 | Argument parsing, mode-gated fail-closed behavior, output safety |
| `test_basket_execution_http.py` | 16 | Route 200/404/405, dashboard content, no-`innerHTML` |
| `test_basket_execution_concurrency.py` | 8 | True separate-process basket-creation and next-child-send races (Section 21.5) |
| **Total new** | **138** | |

Counts independently verified two ways: direct `python -m unittest <module>` runs, and a
`grep -c "^    def test_"` count per file, which matched exactly — see Decision Log entry
2026-08-01-020 item 4.

### 16.2 Full-suite runs (`python -B -W error -m unittest discover -s . -p "test_*.py"`)

| Run | Tests | Failures | Errors |
|---|---|---|---|
| Baseline (pre-Phase-6, committed `3b6d4db`, independently re-verified via an isolated `git worktree --detach` export) | 762 | 2 | 3 |
| Run 1 (post-correction-round) | 900 | 0 | 0 |
| Run 2 (post-correction-round) | 900 | 0 | 0 |

900 = 762 + 138 new, verified by direct measurement, not asserted. **The originally reported
889-test run (2 failures, 3 errors) is superseded** — those 5 failures/errors were reproduced with
`-v`, root-caused to a single stale hardcoded fixture timestamp in the pre-existing Phase 5
`test_mt5_execution_concurrency.py` (`expires_at_utc="2026-08-01T13:00:00.000000Z"`, now in the past
relative to real wall-clock time; confirmed present, and already failing, in the *committed* baseline
itself via the isolated worktree export — this predates Phase 6 entirely), and fixed by the narrow,
Founder-authorized test-fixture maintenance described in Section 21.1. Both current runs are
identical, deterministic, and show **zero** failures and **zero** errors — not merely zero
*new* failures.

### 16.3 Manual fake-adapter rehearsal

A standalone, non-`test_*.py` script drove the real `mode_cli`/`mt5_execution_cli`/
`basket_execution_cli` entry points in-process, with the one adapter-construction seam
(`app._execution_adapter_for_mode`) patched to return a `FakeExecutionAdapter` instead of
`RealMT5ExecutionAdapter` for `MT5_DEMO_MANUAL` — no `MetaTrader5` import, no terminal, no network,
no credential, ever. Isolated `LOCALAPPDATA` temp directory; script and directory deleted at the
end of the run (git status confirms nothing remains). 23 consolidated checkpoints, all passed:
OFF/RESEARCH/SYNTHETIC_PAPER denial; `MT5_DEMO_MANUAL` authorization; SMA-001 blocker (parent
construction itself rejected with `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` — basket construction
is consequently unreachable, the strongest possible demonstration of the blocker); FIB-001 blocker
(parent rejected with `STRATEGY_PARAMETERS_NOT_APPROVED`, same reasoning); deterministic
four-child basket creation and reuse; exact conservation; four successful checks with zero
`order_send` calls; confirmation cycle request, active reuse, invalid-format rejection, wrong-
challenge rejection, correct acceptance, second-acceptance rejection; four sequential
`send-basket-next` calls (including a simulated mid-basket restart) with completion only after the
fourth; all basket HTTP routes returning 405 on every mutation method; and confirmation that only
the fake adapter tier was ever used with no `MetaTrader5` reference anywhere in its call log.

**Disclosed scope note:** stale-check recovery (both cases), rejected/partial/uncertain-result
terminal behavior, restart-preserves-`FROZEN`, and journal-corruption fail-closed behavior are
demonstrated by the automated `StaleCheckRecoveryTests`/`ResultBehaviorTests`/
`JournalAndConcurrencyTests` (Sections 10–13 above) rather than as separate CLI-driven rehearsal
steps, to keep the manual walkthrough to a reviewable length. A second rehearsal (Section 21.6)
specifically re-covers the corrected identity formula, the corrected `FROZEN` partial-fill rule,
and true cross-process proof. Every one of those scenarios is
exercised by a real (fake-adapter-backed) `BasketExecutionService`, not mocked away.

## 17. Other bugs found and fixed during implementation (not contract-related)

- **`_finalize_send`'s dead-code reason-code expression** — see Section 11.1.
- **`confirm_basket`'s check ordering:** the generic `basket_status != "AWAITING_CONFIRMATION"`
  gate fired before the more specific `active["status"] == "ACCEPTED"` check, so a second
  confirmation attempt against an already-accepted cycle was always misreported as the vaguer
  `BASKET_CONFIRMATION_UNAVAILABLE` instead of the contract-mandated
  `BASKET_CONFIRMATION_ALREADY_ACCEPTED`. Found by `ConfirmationCycleTests.test_second_acceptance_rejected`.
  Fixed by reordering the two checks.
- **`EXECUTION_GEOMETRY_APPROVED_STRATEGIES` import style:** the service imported this constant by
  value (`from .mt5_execution_service import EXECUTION_GEOMETRY_APPROVED_STRATEGIES`), which
  freezes a snapshot at import time. Phase 5's own tests monkeypatch
  `mt5_execution_service.EXECUTION_GEOMETRY_APPROVED_STRATEGIES` at the module level to exercise
  happy-path flows — that patch was never visible to the frozen import, meaning no basket could
  ever be successfully built under test, and — more importantly — the basket service would
  silently diverge from Phase 5's own SMA-001/FIB-001 enforcement state if that module-level
  constant were ever legitimately changed at runtime. Fixed by importing the module and referencing
  `mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES` dynamically at each use site, matching how Phase 5's
  own code references its own global.
- **Dead/incorrect `self.account_fingerprint` assignment** in `BasketExecutionService.__init__`:
  `account_fingerprint or med.account_fingerprint_hash` assigned a *function object* (not a
  value) when no config was passed, and the attribute was never read anywhere else in the file —
  the real logic correctly uses `self._account_fingerprint_config` via `_fingerprint_hash()`.
  Removed the dead line.
- **`entry_text` parsing exception type** — see Section 14.1.
- Cleaned up a functionally-correct but needlessly convoluted placeholder-then-delete pattern in
  `build_basket`'s child-lookup-key construction (no behavior change).

## 18. Known limitations (disclosed, not defects)

- **Journal-append cost scales with the current record's size**, inherited unchanged from Phase 5's
  own "revalidate the full store on every append" design (`mt5_execution_journal.py`, not modified
  by this checkpoint beyond additive event types). A basket's full-snapshot-per-event payload
  (plan + up to 4 children + confirmation-cycle history) is substantially larger than Phase 5's own
  single-intent snapshot, so the same pre-existing O(size) per-append cost is proportionally
  higher for baskets — the 130 service/data/cli/http Phase 6 tests take roughly 30 of their
  contribution to the whole ~132-second, 900-test run for this reason. Not a correctness issue, and not a
  Phase-6-introduced architecture — the contract does not specify a performance SLA, and fixing
  the underlying journal-validation strategy would be an out-of-scope Phase 5 change.
- **Section 8 item 5** (independent re-fetch of the R2-006 proposal's own canonical hash from a
  live proposal store) is not literally implemented as a separate lookup; `build_basket` instead
  relies on the parent intent's own hash-chain integrity (`med.validate_order_intent`) plus the
  journal's own integrity check. No live `SignalIntelligenceService` proposal store is wired into
  `BasketExecutionService` in this checkpoint, and the parent order intent already carries
  `canonical_parent_proposal_hash`/`canonical_proposal_hash` fields that this hash-chain integrity
  check transitively covers. Disclosed as a scope limitation rather than silently assumed
  equivalent.
- ~~The Section 14.3/28 interpretation choice~~ — resolved by the Founder correction round; see Section 11.2 and Section 21.3.

## 19. Blockers, mode, and network posture

SMA-001 (`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`) and FIB-001
(`STRATEGY_PARAMETERS_NOT_APPROVED`) remain fully blocked at the parent (Phase 5) construction
gate, before any basket call is reachable — the strongest layer of enforcement, verified directly
in the rehearsal. No `MetaTrader5` import occurs anywhere in `basket_execution_data.py` or at
`basket_execution_service.py` module scope; the optional real adapter is reachable only through
the existing, unchanged Phase 5 lazy-construction path. No automated test, and no step of the
manual rehearsal, ever constructed a real adapter, connected to a broker, or submitted a real
order. Phase 7 was not started; no Phase 7 file exists anywhere in the working tree.

## 20. Verdict (superseded by Section 21 — see the final checkpoint report)

Phase 6 implementation is functionally complete against `TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md`,
fully tested (138 new tests, 900-test suite run twice with identical, deterministic, **zero total**
failures and errors), and manually rehearsed twice via the real CLI entry points with a fake
adapter only, including true separate-process proof. One narrow, disclosed, Founder-approved
reason-code vocabulary gap was found and closed (Section 11.1); a genuine child-identity
circularity and a partial-fill status defect were found by the Founder and corrected (Section 21);
every other finding in Section 17 was a straightforward implementation bug, fixed and covered by a
regression test. See the final checkpoint report for the complete git-state, quality/security-
validation, and cleanup confirmation required before this evidence record can be considered ready
for Founder commit/push approval.

## 21. Founder correction round (2026-08-01, Decision Log entry 2026-08-01-020)

The first "PHASE 6 READY FOR FOUNDER REVIEW" checkpoint was held by the Founder for six specific
corrections. Full detail is in `TRL_DECISION_LOG.md` entry 2026-08-01-020; this section summarizes
what changed and re-states the current, sole governing facts (the sections above have been edited
in place to match; this section is the narrative record of the correction itself).

### 21.1 Full-suite recovery

Reproduced the reported 889-test, 5-failure/error run with `-v`. Every failure/error was
`ExecutionServiceError: PROPOSAL_EXPIRED`, from a hardcoded `expires_at_utc="2026-08-01T13:00:00.000000Z"`
fixture (two occurrences) in the pre-existing Phase 5 `test_mt5_execution_concurrency.py`, now in the
past relative to real wall-clock time. Confirmed via an isolated `git worktree --detach` export of
the *committed* baseline (`3b6d4db052144da92e7376f6bc3b0268a17e92ee`) that this staleness already
existed there too — it predates all Phase 6 work. Per Founder authorization, replaced both
occurrences with one named far-future constant (`FIXTURE_PROPOSAL_EXPIRES_AT_UTC`); no assertion
weakened, removed, skipped, or hidden. Result: 7/7 passing.

### 21.2 Child-identity circularity — corrected, non-circular formula

`basket_child_lookup_key` previously listed `canonical_basket_plan_hash` as an input — but that
hash is computed *from* the child IDs this function produces, a genuine circularity in the contract
itself (Section 17.4), papered over in an earlier implementation draft by silently substituting
`basket_id` (not approved). Corrected per the Founder's exact specification: the lookup key now
derives from `basket_id` + `parent_proposal_id` + `canonical_parent_proposal_hash` +
`parent_order_intent_id` + `canonical_parent_order_intent_hash` + each child's own economic fields,
under domain separator `TRL-BASKET-CHILD-LOOKUP.v1` — never `canonical_basket_plan_hash`. The
existing `bc_`/16-hex `basket_child_id` prefix/length are unchanged. No seventh persisted schema
was added.

### 21.3 Final partial-fill governance — FROZEN, never PARTIALLY_COMPLETED

A broker-confirmed partial fill now freezes the basket (`basket_status → FROZEN`,
`reconciliation_required = true`) exactly as an uncertain/malformed result does — **regardless of
whether any earlier child already reached FILLED** — rather than the previous
`basket_status → PARTIALLY_COMPLETED`. `PARTIALLY_COMPLETED` is now reserved exclusively for
Section 27's later-rejection-after-fills case. The child's own state and reason code
(`PARTIALLY_FILLED` / `BASKET_CHILD_SEND_PARTIALLY_FILLED`) are unchanged. This also resolves the
Section 14.3/28 interpretation ambiguity disclosed in the original draft (Section 11.2) — it is no
longer an ambiguity, since a partial fill no longer needs to satisfy `PARTIALLY_COMPLETED`'s
prior-fill requirement at all.

### 21.4 Test-count arithmetic — independently reconciled

Recounted every Phase 6 file directly (`python -m unittest <module>` plus an independent
`grep -c "^    def test_"` cross-check, which matched exactly): 52 + 45 + 17 + 16 + 8 = 138.
Re-verified the 762-test baseline via a genuinely isolated `git worktree add --detach` export of
the committed `3b6d4db` (outside the repository, isolated `LOCALAPPDATA`, no branch created,
working tree/index untouched, worktree removed afterward). 762 + 138 = 900, matching the actual
full-suite discovery count exactly, both runs, both with zero failures and zero errors. The
originally reported 889-vs-890 one-test gap cannot be forensically re-diagnosed after the fact (the
state it described has been superseded by this round's own edits), but the current arithmetic is
now proven exactly self-consistent by direct, independent measurement.

### 21.5 True cross-process proof — `test_basket_execution_concurrency.py` (new, 8 tests)

Mirrors `test_mt5_execution_concurrency.py`'s exact house style: real, separate `subprocess.Popen`
worker processes (never threads, never sequential in-process calls, never a mocked lock),
synchronized with readiness-marker files polled with a bounded timeout.

- `ConcurrentBasketCreationTests` (4 tests): two independently spawned processes racing
  `build_basket` against the same isolated journal/parent-intent converge on the identical
  `basket_id`; exactly one authoritative `BASKET_CREATED` event and one `BASKET_REUSED` event exist
  in the journal; the post-race journal is a valid hash chain; no lock file remains; neither
  worker's adapter ever reaches `order_check`/`order_send` (basket construction never calls either).
- `ConcurrentChildSendTests` (4 tests): two processes racing `send_basket_next` against the same
  accepted confirmation cycle result in exactly one process reaching the adapter's `order_send` —
  proven by an independent, per-call marker file written inside the isolated temp directory at the
  exact moment of the call (in-memory call counters are invisible across process boundaries, so
  this is the required test-only cross-process observation mechanism); the other process fails
  closed with exactly `BASKET_CHILD_SEND_ALREADY_RESERVED`; exactly one `BASKET_CHILD_SEND_RESERVED`
  and one `BASKET_CHILD_SEND_RESULT` event exist in the journal; the won child is never resent after
  a simulated restart; no lock file remains.

All 8 tests use `FakeExecutionAdapter` only and were confirmed deterministic across 4 repeated runs.

### 21.6 Second manual rehearsal

A second standalone, non-`test_*.py` rehearsal script (same isolation discipline as Section 16.3:
isolated `LOCALAPPDATA`, the same one-seam fake-adapter patch, deleted afterward) specifically
re-covered every item this correction round touched, 12 consolidated checkpoints, all passed:
deterministic basket creation under the corrected non-circular identity formula; child IDs and
plan hash stable across a simulated restart; one accepted confirmation still governs sequential
children across two explicit sends under the same cycle; a rejected child's `terminal_reason` is
exactly `BASKET_CHILD_SEND_REJECTED` (and never reuses `BASKET_CHILD_CHECK_FAILED`); a first-child
partial fill produces `basket_status = FROZEN` with `reconciliation_required = true`; a partial
fill *after* an earlier `FILLED` child also produces `FROZEN`, never `PARTIALLY_COMPLETED`, while
the earlier fill is preserved and still counted; partial-fill `FROZEN` state and fill count survive
restart; a further send attempt after freezing fails closed with `BASKET_ALREADY_TERMINAL`; no
`CANCELLED` state exists anywhere; and — live, inside the rehearsal process — both
`ConcurrentBasketCreationTests` and `ConcurrentChildSendTests` were invoked as real subprocesses and
both suites passed, directly demonstrating the true cross-process proof as part of the rehearsal
walkthrough rather than only as a separately-run automated suite. The rehearsal script and its
isolated temp directory were deleted at the end of the run.
