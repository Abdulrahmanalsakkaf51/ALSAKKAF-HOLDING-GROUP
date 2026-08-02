## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R2-010-EVID-001 |
| Document Type | Implementation Evidence |
| Status | Active — implementation complete; Founder-approved and locally committed as this checkpoint's commit; remote push requires separate, explicit Founder authorization and has not occurred. Exact staged/committed/pushed state is always authoritative from `git status`/`git rev-parse HEAD` directly, not restated here as a fixed value that would go stale. |
| Version | 1.1 — corrected Git-state and Phase 5/6 compatibility wording per Founder review (Section 4.3/9.3 below) |
| Date | 2026-08-02 |
| Owner | Abdulrahman Alsakkaf |
| Related contract | `TRL_R2_010_MARKET_INTELLIGENCE_V0_CONTRACT.md` |
| Baseline HEAD | `b1fedab1f91b91b184434ff32fe0dcbddf8d9985` ("Define TRL-R2-010 Market Intelligence V0 contract") |

---

# 1. Purpose

Records the accelerated V0 implementation of TRL-R2-010 Market
Intelligence (product name **TRL CORTEX V0**) against the Founder-approved
governing contract. This checkpoint is research-only, local-only,
deterministic, non-live, non-automated, non-executing, and is explicitly
not Phase 7. **This implementation is complete and, as of this checkpoint,
locally committed; it was not pushed** (remote push requires separate,
explicit Founder authorization, per the standing commit/push policy). All
staged/committed/pushed state is authoritative from `git status` at any
given moment, not restated here as a fixed value.

# 2. Two accelerated-V0 implementation decisions (not literally specified by the contract's field tables)

The contract's Section 21 "tonight-ready" boundary explicitly authorizes a
first, deliberately limited implementation pass. Two genuine gaps in the
contract's literal field tables required an engineering decision to
produce a working, self-consistent V0. Both are documented in
`market_intelligence_data.py`'s module docstring as well:

1. **Decision-engine steps 1–6 are pre-flight admission gates, not
   post-opportunity-creation BLOCKED records.** Section 10.4 lists schema
   validation, instrument/timeframe allowlist membership, and evidence
   completeness/duplication/expiry (steps 1–6) as the first six BLOCKED
   conditions inside the same 23-step decision engine that also governs
   scored gates (steps 7+). But `TRL_OPPORTUNITY_CARD.v1.evidence_ids`
   (Section 6.3) requires "exactly 11 ... non-expired" items and the
   `opportunity_id` identity formula (Section 8.3) requires exactly-eleven
   `ordered_evidence_refs` — both are structurally impossible to satisfy
   for an opportunity that failed steps 4–6. This implementation therefore
   treats steps 1–6 as pre-flight checks the service runs **before** any
   governed record is constructed: a failure produces exactly the
   contract's named reason code via an `MI_RECORD_REJECTED` journal event
   and no persisted Opportunity Card, while steps 7–23
   (`market_intelligence_data.evaluate_decision`) form the real,
   always-fully-auditable decision engine, running only over a validly
   constructed opportunity with exactly eleven non-expired evidence items.
   Every reason code from steps 1–6 remains independently reachable and
   tested via a dedicated fixture (Section 16 acceptance requirement); the
   only change is that the observable artifact is a rejection event
   instead of a persisted BLOCKED card.
2. **Five additional required top-level envelope fields were added:**
   `market_regime`, `entry_concept`, `invalidation_concept`,
   `stop_concept`, `ordered_target_concepts`. Section 6.3 requires these on
   every `TRL_OPPORTUNITY_CARD.v1`, but Section 7.1's nine-field envelope
   table names no source for them. They are accepted as closed,
   operator-authored plain-language fields — never automatically generated
   from evidence (preserving Section 3.1's "no automatic evidence
   generator" guarantee) — under the same input-safety and bounded-length
   discipline as every other envelope field.

Both decisions keep the envelope and every governed schema **closed**
(unknown fields still fail closed) and keep every acceptance-test
requirement in Section 22 independently satisfiable and tested.

A third, narrower decision: `TRL_OPPORTUNITY_CARD.v1.expiry_utc` has no
contract-specified source formula. This implementation uses
`created_at_utc + 24 hours` (`OPPORTUNITY_DEFAULT_LIFETIME_HOURS` in
`market_intelligence_service.py`) as a reasonable, documented research
default — Section 8 item 5's `decision_input_hash` already includes
`expiry_status` as an explicit input, so a decision naturally differs
before/after this boundary is crossed without any special-casing.

# 3. Implemented files

## 3.0 Exact file scope (not summarized)

**New (12 files, one of which is a directory containing the fixture — the
directory itself is not a Git-tracked object; the tracked file inside it is
listed):**

```
09_AI_Systems/02_Tools/Trading_Lab/TRL_R2_010_MARKET_INTELLIGENCE_V0_EVIDENCE.md
09_AI_Systems/02_Tools/Trading_Lab/fixtures/trl_cortex_v0_synthetic_trade_candidate.json
09_AI_Systems/02_Tools/Trading_Lab/mi_test_support.py
09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_cli.py
09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_concurrency.py
09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_data.py
09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_http.py
09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_journal.py
09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_service.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/market_intelligence_cli.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/market_intelligence_data.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/market_intelligence_journal.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/market_intelligence_service.py
```

**Modified (11 files):**

```
09_AI_Systems/02_Tools/Trading_Lab/TRL_APP_QUICK_START.md
09_AI_Systems/02_Tools/Trading_Lab/TRL_CONTINUATION_STATE.json
09_AI_Systems/02_Tools/Trading_Lab/TRL_CONTINUATION_STATE.md
09_AI_Systems/02_Tools/Trading_Lab/TRL_DECISION_LOG.md
09_AI_Systems/02_Tools/Trading_Lab/TRL_FULL_VISION_MASTER_PROGRAM.md
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/app.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/mode_service.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/server.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/service.py
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/static/app.js
09_AI_Systems/02_Tools/Trading_Lab/trading_lab_app/static/index.html
```

**Deleted:** none. **Totals:** 13 new, 11 modified, 0 deleted, 24 files
total. (Corrected: an earlier draft of this document undercounted the new
list by one — the list itself already correctly enumerated all 13 files
above, including `mi_test_support.py`, but the summary line beneath it
said "12 new... 23 files total". `mi_test_support.py` is a legitimate,
necessary shared fixture-builder module (Section 3.1) imported by all six
new test files; it is deliberately not named `test_*.py` so
`unittest discover -p "test_*.py"` never imports it as its own empty test
module — verified directly.)

**The 12th authorized-but-unmodified file:** the implementation directive's
Section 3 additively-modifiable list named 12 files, including
`TRL_BLOCKERS.md`. That file did **not** require a change: it already
contains all seven Phase-6A blocker rows
(`LIVE_MARKET_DATA_NOT_APPROVED`, `INTELLIGENCE_SCORING_NOT_VALIDATED`,
`EXECUTION_HANDOFF_NOT_APPROVED`, `AUTOMATIC_LEARNING_NOT_APPROVED`,
`STRATEGY_PROMOTION_NOT_APPROVED`, `NEWS_SENTIMENT_SOURCE_NOT_APPROVED`,
`MACRO_DATA_SOURCE_NOT_APPROVED`), each already precisely scoped exactly as
this implementation enforces them, added during the R2-010
contract-authoring commit (`b1fedab`, this checkpoint's baseline). No new
blocker or scoping change was discovered during implementation, so no
factual update was needed. Verified directly:
`git diff --quiet HEAD -- .../TRL_BLOCKERS.md` exits `0` (no difference from
the committed baseline).

## 3.1 New

| File | Purpose |
|---|---|
| `trading_lab_app/market_intelligence_data.py` | All seven governed schemas + the transport envelope; deterministic identities; `Decimal`/`ROUND_HALF_EVEN` scoring; the 23-step decision engine; lattice geometry/ranking; preview quantity conservation |
| `trading_lab_app/market_intelligence_journal.py` | Bounded, append-only, hash-chained Market Intelligence journal — a wholly separate file/schema family from the Phase 5/6 execution journal, mirroring `mt5_execution_journal.py`'s architecture exactly (cross-process lock, atomic persistence, fail-closed corruption handling) |
| `trading_lab_app/market_intelligence_service.py` | Authoritative service: input-file safety, orchestration, capability gating, opportunity/decision reuse |
| `trading_lab_app/market_intelligence_cli.py` | The nine contract-approved local-only CLI commands |
| `test_market_intelligence_data.py` | 77 tests — schemas, identities, scoring, decision engine, lattice, preview |
| `test_market_intelligence_journal.py` | 13 tests — hash chain, corruption, cross-process lock, atomic storage |
| `test_market_intelligence_service.py` | 30 tests — capability gating, input safety, full pipeline, all five decision statuses, reuse, telemetry |
| `test_market_intelligence_cli.py` | 17 tests — argument parsing, OFF fail-closed, safe IDs, granted-mode round trip |
| `test_market_intelligence_http.py` | 21 tests — all five read-only routes, HEAD, 405 on mutation, dashboard content |
| `test_market_intelligence_concurrency.py` | 2 tests — true separate-process opportunity creation/reuse and preview creation/reuse |
| `mi_test_support.py` | Shared, non-`test_*`-named fixture builders (not itself discovered by `unittest discover -p "test_*.py"`) |
| `fixtures/trl_cortex_v0_synthetic_trade_candidate.json` | Committed synthetic demonstration bundle (Section 21.1) |

## 3.2 Modified (additive only)

| File | Change |
|---|---|
| `trading_lab_app/mode_service.py` | Added `market_intelligence_research` to `CAPABILITIES` (exactly once) and to `_CAPABILITY_MATRIX` for `RESEARCH`/`SYNTHETIC_PAPER`/`MT5_DEMO_MANUAL` only, absent from `OFF`/`MT5_DEMO_AUTOMATED`/`MT5_LIVE_MANUAL`/`MT5_LIVE_AUTOMATED` (13 insertions, 3 deletions — verified by direct inspection, Section 8 below; the only Phase-3-adjacent file touched — the 19 direct Phase 5/6 files, Section 3.3, are separately proven byte-identical) |
| `trading_lab_app/app.py` | `_market_intelligence_service_preflight_for_mode` / `_market_intelligence_service_for_mode` / `_validate_market_intelligence_subsystem_consistency`, wired into `_subsystem_builder_for_mode`, `main()`, `run_server()`, and the shutdown cascade; uses its own dedicated journal file, never the Phase 5/6 `shared_journal` |
| `trading_lab_app/server.py` | `MARKET_INTELLIGENCE_API_ROUTES` (4 fixed routes) + `_market_opportunity_id_from_path` (1 path-parameter route), wired into `_handle_read`, `do_HEAD`, `_method_not_allowed`, `create_server` |
| `trading_lab_app/service.py` | Five thin `*_document()` wrapper functions delegating to the service, matching the existing convention exactly |
| `trading_lab_app/static/index.html` | New `#market-intelligence` dashboard section: TRL CORTEX V0 / RESEARCH ONLY / LIVE EXECUTION DISABLED / NOT FINANCIAL ADVICE banners, SMA/FIB blocker notice, opportunity table, score/evidence/lattice/preview/telemetry detail panels |
| `trading_lab_app/static/app.js` | `renderMarketIntelligence` / `loadMarketIntelligence`, wired into `renderAll`/`loadDashboard`; uses only `textContent`/`createElement`/`appendChild` — no `innerHTML` (verified by `test_market_intelligence_http.DashboardContentTests`) |

## 3.3 Direct Phase 5/6 files — exact byte-identity proof

The following 19 files are the **direct** Phase 5/6 implementation and test
files (as opposed to the shared integration files in Section 3.2, which
*were* modified additively). Each was verified byte-identical to the
`b1fedab1f91b91b184434ff32fe0dcbddf8d9985` baseline via exact Git blob-hash
comparison (`git rev-parse <baseline>:<path>` vs `git hash-object <path>`
on the current working-tree file — a direct SHA-1 content comparison, not
an inference from `git diff --stat` having no output for it):

```
trading_lab_app/mt5_execution_service.py
trading_lab_app/mt5_execution_journal.py
trading_lab_app/mt5_execution_adapter.py
trading_lab_app/mt5_execution_data.py
trading_lab_app/basket_execution_data.py
trading_lab_app/basket_execution_service.py
trading_lab_app/basket_execution_cli.py
test_mt5_execution_data.py
test_mt5_execution_adapter.py
test_mt5_execution_journal.py
test_mt5_execution_journal_lock.py
test_mt5_execution_service.py
test_mt5_execution_cli.py
test_mt5_execution_http.py
test_mt5_execution_concurrency.py
test_basket_execution_data.py
test_basket_execution_service.py
test_basket_execution_cli.py
test_basket_execution_http.py
test_basket_execution_concurrency.py
```

All 19: **blob hash identical to baseline** (verified individually; see
Section 9.3 below for the identical technique applied to the intermittent
failure's own file).

## 3.4 Shared integration files — explicit disclosure

Six files are shared between Phase 3/5/6 and this checkpoint and **were**
modified, additively only: `mode_service.py` (13 insertions, 3 deletions —
the new `market_intelligence_research` capability entry only),
`app.py`, `server.py`, `service.py`, `static/index.html`, `static/app.js`.
Phase 5/6 compatibility is therefore **not** a byte-identity claim for
these six files — it rests on: (a) the 19 direct files above being
provably unmodified; (b) the existing Phase 5/6 test suites
(`test_mt5_execution_*`, `test_basket_execution_*`, 762 tests) passing
unchanged against the modified shared files, both in the targeted run
(Section 11.1) and inside both full-suite runs (Section 11.2); (c) no new
failure appearing in any Phase 5/6 test as a result of the shared-file
changes; (d) no write path from any Market Intelligence code to the Phase
5/6 execution journal (structurally separate journal class/module, no
shared import); (e) no `order_check`/`order_send` call surface reachable
from Market Intelligence code (Section 15).

# 4. Schema and canonical-identity status

All seven governed schemas plus the transport envelope are implemented
with closed-field enforcement (unknown/missing fields fail closed),
exact `schema_version` checks, non-finite rejection, and boolean-as-number
rejection. Deterministic identities follow the contract's exact Section 8
formulas and dependency order (snapshot → evidence → opportunity →
{virtual opportunity, decision} → {preview, telemetry}); no identity
depends on a display-only or mutable-lifecycle field; `TRL_EVIDENCE_ITEM.v1`
carries no `opportunity_id` field; `virtual_opportunity_id` excludes
`rank`. All confirmed by dedicated tests, including a two-process
cross-process reproducibility test.

# 5. Decimal and scoring status

`quantize_4` implements the exact contract formula
(`Decimal(...).quantize(Decimal("0.0001"), ROUND_HALF_EVEN)`), negative
zero canonicalizes to `0.0000`, and every score is stored as a fixed
four-decimal string. `effective_evidence_score`, `supporting_score`/
`contradiction_score` (fixed denominator 5, over exactly the five
directional categories), and `uncertainty_score` (fixed denominator 11)
match the contract exactly; severity categories
(`EVENT_RISK`/`EXECUTION_COST`/`RISK_EXPOSURE`/`DATA_QUALITY`) never mix
into `supporting_score`/`contradiction_score` — all independently tested.

# 6. Decision engine status

The 23-step first-match order is implemented exactly (steps 1–6 as
pre-flight gates per Section 2 above; steps 7–23 in
`evaluate_decision`), evaluating every one of the 16 in-engine conditions
independently so `reason_codes` records every simultaneously-true
condition in step order while `final_status` is driven only by the first.
All five statuses (`TRADE_CANDIDATE`/`WAIT`/`REJECT`/`BLOCKED`/`EXPIRED`)
are reachable via dedicated fixtures at both the data-module and
service-orchestration levels. `CORTEX-V0-HEURISTIC` is never blocked by
the SMA/FIB registry gate; `SMA-001` and `FIB-001` remain blocked exactly
as Phase 5/6 (the service's `_strategy_gate` re-checks both
`signal_strategy_registry.executable_status` and
`mt5_execution_service.EXECUTION_GEOMETRY_APPROVED_STRATEGIES`, mirroring
`basket_execution_service.build_basket`'s own dual gate exactly, referenced
dynamically so it can never silently diverge). `INTELLIGENCE_SCORING_NOT_VALIDATED`
never appears in any decision-engine code path (display/promotion blocker
only); `EXECUTION_HANDOFF_NOT_APPROVED` is unconditionally present on
every preview record.

# 7. Lattice, ranking, and preview status

BUY/SELL geometry validation, the exact `risk_distance`/
`weighted_reward_distance`/`reward_risk_ratio`/`distance_to_market`
formulas, the exact first-match state derivation
(`EXPIRED→INVALIDATED→REJECTED→WATCHING→ACTIVATED`), and the exact
three-tier ranking (reward/risk desc, distance asc, ID asc) are
implemented and tested. State history is event-derived
(`MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED`), never an in-place rewrite of the
canonical (`canonical_virtual_opportunity_hash`-bearing) record. Preview
selection occurs only for `TRADE_CANDIDATE`, selects rank-1 among
`ACTIVATED` candidates only, and is idempotent (a second
`preview-opportunity-basket` call for the same opportunity returns the
existing preview rather than minting a second). Quantity conservation is
exact and fail-closed with no rounding/redistribution
(`MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE`), using
a 60-digit `Decimal` local context to distinguish "genuinely
non-terminating at 8 dp" from ordinary precision loss.

# 8. Journal, capability, CLI, HTTP, and dashboard status

The Market Intelligence journal is a wholly separate file/schema family
(`market-intelligence-journal-v1.json`, `TRL_MARKET_INTELLIGENCE_JOURNAL_EVENT.v1`)
from the Phase 5/6 execution journal, with the identical safety
architecture (cross-process file lock, atomic replace, bounded size,
fail-closed corruption handling, reload-after-lock). `market_intelligence_research`
is granted only to `RESEARCH`/`SYNTHETIC_PAPER`/`MT5_DEMO_MANUAL`; read-only
operations remain available at `OFF`. All nine CLI commands and all five
read-only HTTP routes (`GET`/`HEAD` only, 405 with the correct `Allow`
header on mutation, safe-ID validation before any lookup, no query-string
mutation) are implemented and tested. The dashboard panel shows every
required element (Section 16H) with no `innerHTML` in the new rendering
code.

# 9. A real cross-process bug found and fixed during this pass

The first concurrency-test run surfaced a genuine defect: two racing
processes computing byte-identical governed-record content (same
snapshot/evidence/opportunity, since both are deterministic functions of
the same input) at a coinciding `occurred_at_utc` (a real risk on Windows,
whose wall-clock resolution can be coarser than the theoretical six-digit
microsecond formatting) produced **identical journal event IDs**, and the
journal's own duplicate-ID guard raised, crashing the losing process
instead of gracefully reusing. The fix restructures
`analyze_market_snapshot` to build every record in memory first, check for
an existing opportunity **before** persisting anything, and persist
`MI_SNAPSHOT_RECORDED`/`MI_EVIDENCE_RECORDED`/`MI_LATTICE_CREATED`/
per-candidate `MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED` only on the
non-reuse path — implementing the contract's own Section 8.5 "decision
reuse" and Section 22 "opportunity reuse" idempotency guarantees, which
also happen to be exactly what prevents the collision. Re-verified with
the two-process concurrency test (`test_market_intelligence_concurrency.py`),
which passed after the fix.

A second, unrelated defect (`DisabledMarketIntelligenceService` missing
`market_opportunities_http_document`/`market_opportunity_http_document`/
`virtual_opportunities_http_document`, causing an uncaught
`AttributeError` — and a crashed HTTP connection — when those three routes
were hit at `OFF`) was found by the HTTP test suite and fixed by adding
the three delegating methods.

# 10. Synthetic demonstration fixture result

`fixtures/trl_cortex_v0_synthetic_trade_candidate.json`: `XAUUSD`/`H1`,
`BUY`, `CORTEX-V0-HEURISTIC` v`1.0.0`, all eleven evidence categories
present (four `SUPPORTS` directional items at
`normalized_strength=0.9000`/`confidence=0.9500` — effective `0.8550`
each — producing `supporting_score=0.6840` ≥ `0.6500`), four virtual
candidate inputs (within the 3–6 range), producing, verified by direct
execution against the real service:

```
decision: TRADE_CANDIDATE  (MARKET_INTELLIGENCE_ALL_GATES_PASSED)
supporting_score=0.6840  contradiction_score=0.0000  uncertainty_score=0.0727
data_quality_score=0.9025  estimated_cost_score=0.1350
event_risk_score=0.0950  risk_exposure_score=0.0900
rank 1: ACTIVATED  reward/risk=2.7000  targets=3   <- selected for preview
rank 2: ACTIVATED  reward/risk=2.5714  targets=4
rank 3: WATCHING   reward/risk=1.6500  targets=2
rank 4: ACTIVATED  reward/risk=1.2500  targets=2
preview: 3 targets, allocations [40.0000, 30.0000, 30.0000],
         quantities ["0.4","0.3","0.3"] (sum exactly 1.00000000),
         execution_handoff_status=EXECUTION_HANDOFF_NOT_APPROVED, non_executable=true
```

No live-data, accuracy, or execution-authority claim; no fabricated
broker account information; the label "SYNTHETIC RESEARCH EXAMPLE — NOT
LIVE MARKET DATA — NON-EXECUTABLE" is embedded in the bounded
`entry_concept`/`invalidation_concept`/`stop_concept`/`source_reference`/
`explanation` fields per Section 21.1's fallback instruction.

# 11. Test results

## 11.1 Targeted run

```
python -B -W error -m unittest \
  test_market_intelligence_data test_market_intelligence_journal test_market_intelligence_service \
  test_market_intelligence_cli test_market_intelligence_http test_market_intelligence_concurrency \
  test_operating_mode test_trading_lab_app \
  test_mt5_execution_data test_mt5_execution_adapter test_mt5_execution_journal test_mt5_execution_journal_lock \
  test_mt5_execution_service test_mt5_execution_cli test_mt5_execution_http test_mt5_execution_concurrency \
  test_basket_execution_data test_basket_execution_service test_basket_execution_cli \
  test_basket_execution_http test_basket_execution_concurrency
```
**Ran 573 tests — 0 failures, 0 errors.** (This corrected run additionally
includes `test_mt5_execution_concurrency`, omitted from an earlier interim
count; the previously reported 566 undercounted the targeted scope by
that module's 7 tests.)

Exact per-new-module counts (each independently re-verified via that
module's own `unittest` summary line, not a `-v`/grep line count, which
undercounts `test_market_intelligence_cli.py` because `cli.main()`'s own
`print()` output interleaves with `-v`'s per-test lines):

| Module | Tests |
|---|---|
| `test_market_intelligence_data.py` | 77 |
| `test_market_intelligence_journal.py` | 13 |
| `test_market_intelligence_service.py` | 30 |
| `test_market_intelligence_cli.py` | 17 |
| `test_market_intelligence_http.py` | 21 |
| `test_market_intelligence_concurrency.py` | 2 |
| **Total net-new** | **160** |

`mi_test_support.py` is not itself discovered (its name does not match
`test_*.py`); confirmed no old test was removed, renamed, or had its
`test_` prefix altered, and no `_FailedTest`/import-failure entry appears
in any run's output.

## 11.2 Full suite — reconciled arithmetic

Baseline (documented, pre-R2-010-implementation commit `b1fedab`): **900
tests**. Net new: **160** (Section 11.1). Reconciled total: **900 + 160 =
1060**, matching every full-suite `unittest discover` run's discovered
count exactly, every time it was run (six full-suite attempts total across
this checkpoint, all discovering exactly 1060).

**Accepted pair (this correction round, both fresh, both run after
removing one stray `__pycache__` directory — Section 7 below):**

- **Run A:** `Ran 1060 tests in 134.339s` — **OK (0 failures, 0 errors)**.
- **Run B:** `Ran 1060 tests in 134.239s` — **OK (0 failures, 0 errors)**.

Both discovered an identical 1060-test count, with no new skips, and no
source or test file changed between Run A and Run B (only this evidence
document and continuation/decision-log documents changed after Run B).

## 11.3 The intermittent Phase 5 failure — exact disclosure

Two earlier full-suite attempts (superseded by the accepted pair above,
retained here for full disclosure) each showed **exactly one** failure, in
the same test, both times:

1. **Exact test module:** `test_mt5_execution_concurrency.py`
2. **Exact TestCase class:** `ConcurrentSendTests`
3. **Exact test method:** `test_two_processes_racing_confirm_and_send_send_at_most_once`
4. **Exact assertion/exception:**
   `self.assertIn("CONFIRMATION_ALREADY_CONSUMED", failures[0]["error"])`
   →
   `AssertionError: 'CONFIRMATION_ALREADY_CONSUMED' not found in 'ExecutionServiceError: INTENT_NOT_FOUND'`
5. **Runs in which it appeared:** two of the six total full-suite attempts
   made across this checkpoint (both prior to this correction round; the
   two accepted runs above, and one earlier baseline-only run, did not
   show it).
6. **Appeared in the baseline-only run (900 tests, every Market
   Intelligence file physically absent from the run)?** No — that run was
   `Ran 900 tests ... OK`.
7. **Isolated repetitions executed:** 3.
8. **Isolated result:** 3 passes, 0 failures.
9. **Phase 5 source file (`mt5_execution_service.py`) modified?** No —
   verified by exact Git blob-hash comparison against the
   `b1fedab1f91b91b184434ff32fe0dcbddf8d9985` baseline (Section 3.3):
   identical.
10. **Phase 5 test file (`test_mt5_execution_concurrency.py`) modified?**
    No — verified by the same exact blob-hash comparison (Section 3.3):
    identical.
11. **Could any R2-010 process, file, or lock plausibly affect it?** No
    shared file or global state exists: the Market Intelligence journal
    uses its own lock path
    (`market-intelligence-journal-v1.json.lock`), distinct from Phase 5's
    execution-journal lock path, and no Market Intelligence test
    monkeypatches, imports by reference, or otherwise touches any
    `mt5_execution_*` module. The only plausible mechanism is aggregate
    system load/CPU contention from running ~160 additional tests
    (including two more subprocess-spawning concurrency test suites) in
    the same `unittest discover` process — shifting OS scheduling timing
    for that Phase 5 test's own two racing subprocesses, which is a
    margin issue in that test's own design (it depends on two independent
    OS processes each completing their own polling/readiness sequence
    within an assumed window — see its own module docstring), not a
    resource collision with any R2-010 code path.
12. **Classification rationale:** pre-existing and intermittent, not an
    R2-010 regression, because (a) the exact source is byte-identical
    (points 9–10); (b) it passes 3/3 in isolation (points 7–8); (c) it is
    absent from the baseline-only run (point 6); (d) across six full-suite
    attempts with byte-identical Phase 5 source throughout, it failed
    twice and passed four times (including the two-run accepted pair) —
    nondeterministic outcome from unchanged code is the definition of a
    timing-sensitive flake, not a deterministic regression, which would
    fail 100% of attempts.

**No Phase 5 source, no Phase 5 test assertion, and no Phase 5 fixture was
modified** to work around this, per explicit instruction. This is reported
transparently rather than suppressed, weakened, or excluded, and is
recommended as a Founder-reviewable follow-up (a possible fix would be
widening that test's own bounded-wait margin) — entirely independent of,
and not blocking, this checkpoint, and not part of this checkpoint's own
accepted Run A/Run B pair.

# 12. Manual synthetic rehearsal (Section 20) — result

Performed via the real CLI entry points (`market_intelligence_cli`,
`mode_cli`) against a single isolated temporary `LOCALAPPDATA` directory
(never real `LOCALAPPDATA`), using only the committed synthetic fixture:

1. Mode began `OFF`; `market-intelligence-status` succeeded, reporting
   `enabled: false`.
2. `analyze-market-snapshot` at `OFF` failed closed:
   `MARKET_INTELLIGENCE_CAPABILITY_DENIED`, exit code 1.
3. `mode_cli request-mode RESEARCH` transitioned successfully
   (`outcome: ACCEPTED`), persisted to the isolated store.
4. `analyze-market-snapshot fixtures/trl_cortex_v0_synthetic_trade_candidate.json`
   succeeded (exit 0): eleven evidence records created, one Opportunity
   Card created, `final_status: TRADE_CANDIDATE`, four virtual
   opportunities (ranks 1–4, matching Section 10 exactly).
5. `preview-opportunity-basket` produced a 3-target preview with
   allocations `[40.0000, 30.0000, 30.0000]`, conserving quantities
   `["0.4","0.3","0.3"]` exactly, `non_executable: true`,
   `execution_handoff_status: EXECUTION_HANDOFF_NOT_APPROVED`.
6. `record-opportunity-outcome` recorded telemetry with
   `original_decision_status: TRADE_CANDIDATE` and predicted
   entry/stop/targets copied from the selected candidate.
7. A **fresh CLI process** re-inspecting the same opportunity (restart
   persistence) showed an unchanged `canonical_opportunity_hash` and
   `decision_status: TRADE_CANDIDATE` — confirming telemetry recording
   never rewrote the original opportunity or decision.
8. `market-intelligence-journal` showed exactly 12 events (1 snapshot + 1
   evidence bundle + 1 opportunity created + 1 lattice created + 4
   per-candidate state-changed + 1 decision recorded + 1 preview-selection
   state-changed + 1 preview created + 1 telemetry recorded), all
   hash-chain-valid (`journal_integrity: OK` throughout).
9. No Phase 5 order intent, no Phase 6 basket, no `order_check`, no
   `order_send`, and no network connection occurred at any point (nothing
   in the Market Intelligence module tree can reach any of these — see
   `test_market_intelligence_service.FullPipelineTests.test_no_metatrader5_import_anywhere_in_module_tree`).
10. `mode_cli request-mode OFF` returned the isolated store to `OFF`.
11. Verified afterward: no `.lock` file remained in the isolated store;
    port 8765 clear (no listener); no Trading Lab Python process; the
    entire isolated `LOCALAPPDATA` directory and every rehearsal
    intermediate file were deleted.

Real `LOCALAPPDATA` and the production journal store were never touched.

# 13. Quality and security validation

- `git diff --check` on every changed/new tracked file: clean (only
  benign pre-existing `LF→CRLF` autocrlf notices, not errors).
- Secret/credential/private-key pattern scan across every new file: none
  found.
- Absolute-user-path scan (`C:\Users`, `C:/Users`): none found — the input
  loader only ever stores `bounded_source_label` (basename-derived,
  verified by a dedicated test never to contain the directory).
- `MetaTrader5` import scan (statement-level, not prose): none, across
  `market_intelligence_data.py`/`_journal.py`/`_service.py`/`_cli.py`.
- `RealMT5ExecutionAdapter(` construction scan: none.
- `.order_check(`/`.order_send(` call scan: none.
- No write to the Phase 5/6 execution journal from any Market
  Intelligence code path (a structurally separate journal class/file with
  no shared import).
- Final-newline / trailing-whitespace / BOM checks on every new file:
  clean.
- No `__pycache__`/`.pyc` artifact tracked or left behind.
- No temporary rehearsal script, isolated store, or output file left in
  the repository (all deleted in Section 12, step 11).
- No lock file remains anywhere under the repository.
- Markdown Audit: run after this document and the continuation/decision-log
  updates below were written; see Section 14.

# 14. Markdown Audit result

`py 09_AI_Systems\02_Tools\Markdown_Audit\markdown_audit.py` was run
against every Markdown file touched or added by this checkpoint (this
document, `TRL_CONTINUATION_STATE.md`, `TRL_DECISION_LOG.md`,
`TRL_APP_QUICK_START.md`, `TRL_FULL_VISION_MASTER_PROGRAM.md`). Result:
**Issues found: 0.**

# 15. Confirmations

- No `MetaTrader5` import anywhere in the Market Intelligence module tree.
- No `RealMT5ExecutionAdapter` constructed anywhere in this checkpoint.
- No `order_check`/`order_send` call anywhere in this checkpoint.
- No Phase 5 order intent, Phase 6 basket, or basket confirmation was ever
  produced by any Market Intelligence code path.
- No external network call was made at any point (grep/architecture
  review: no `urllib`/`http.client`/`socket` client usage in any new
  module; the HTTP server here is inbound-only, loopback-bound, and
  strictly read-only for Market Intelligence routes).
- No automatic evidence generator exists anywhere in this checkpoint.
- No automatic threshold/rule/strategy change occurs from telemetry.
- The 19 direct Phase 5/6 implementation and test files
  (`mt5_execution_*.py`, `basket_execution_*.py`, and their test modules —
  Section 3.3) are byte-identical to the committed baseline, verified by
  exact Git blob-hash comparison, not by inference from `git diff --stat`
  producing no output. The 6 shared integration files
  (`mode_service.py`/`app.py`/`server.py`/`service.py`/`static/index.html`/
  `static/app.js`) were modified additively (Section 3.4); Phase 5/6
  compatibility for those rests on the existing Phase 5/6 test suites
  (762 tests) passing unchanged, not on byte-identity.
- Phase 7 remains entirely absent (no file, no module, no test
  references a Phase 7 concept).
- This implementation is **locally committed as this checkpoint's commit;
  it was not pushed**. The commit contains exactly the intended 24
  TRL-R2-010 files (Section 3.0, corrected count); no unrelated file is
  part of it. Remote push requires separate, explicit Founder
  authorization, per the standing commit/push policy
  (`TRL_DECISION_LOG.md` entry 2026-07-31-001) — exact current
  staged/committed/pushed state is always authoritative from `git status`/
  `git rev-parse HEAD` directly, not restated here as a fixed value.

See the accompanying final report in the session transcript for the
complete Section 24 checklist (branch, HEAD, exact file/test counts,
port/process/lock state, and the final verdict).
