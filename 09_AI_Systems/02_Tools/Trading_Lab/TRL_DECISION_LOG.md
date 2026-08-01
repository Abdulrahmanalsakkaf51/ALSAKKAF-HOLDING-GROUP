## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-DECLOG-001 |
| Document Type | Decision Log |
| Status | Active |
| Version | 1.0 |
| Date | 2026-08-01 |
| Owner | Abdulrahman Alsakkaf |

# TRL Full-Vision Program — Decision Log

## 2026-07-31-001 — Commit/push approval gate

**Decision:** Follow `CLAUDE.md`'s explicit requirement that commits and
pushes need Founder approval each time, even though the full-vision program
instructions describe committing automatically at the end of each phase and
pushing when a remote is available.

**Why:** `CLAUDE.md` is checked into the repo and states its instructions
"OVERRIDE any default behavior." It explicitly says "Do not commit unless the
Founder approves" and "Do not push unless the Founder approves," and that
Claude "is not allowed to act as an uncontrolled autonomous agent." This
program spans live-money broker execution, credential handling, and public
network exposure — exactly the class of hard-to-reverse, high-blast-radius
work that benefits most from a human checkpoint before it becomes permanent
history.

**How to apply:** At the end of each phase, present the exact `git status`
and `git diff --stat` for review before proposing a commit message. Do not
run `git commit` or `git push` until the Founder responds with approval for
that specific commit/push. This applies for the whole program, not just
Phase 0/1.

## 2026-07-31-002 — Phase 0 verification results accepted

**Decision:** Backup ZIP verified valid (60 entries, SHA-256
`CEFCB4FFEC9ACA15E9450C551758AA285EA246E17251BB75B2126E7225EE2FFA`, 325,719
bytes) at `C:\ALSAKKAF_BACKUPS\PRJ017-R2-005-20260731-140412\Trading_Lab_R2_005.zip`.
Branch and HEAD match the program's stated expected values exactly. Git
status shows exactly 10 modified tracked files and 7 untracked new files, all
under `09_AI_Systems/02_Tools/Trading_Lab/`, matching the program's described
17-file inventory. Port 8765 has no listener; no `python.exe` process is
running.

**Why:** Phase 0 exists to confirm the starting state before any edits, so
that later work is provably built on a known-good, backed-up baseline.

**How to apply:** Phase 1 (independent review) may proceed on the assumption
that the working tree matches the program's described starting state.

## 2026-07-31-003 — Phase 1 independent review findings and fixes

**Decision:** Independent review (self-review of the causal timeline, storage,
and proposal contracts, plus a fresh background review pass of the fill/risk
engine, API/dashboard wiring, and test coverage) found the core engine sound
but surfaced one real defect and two required gaps, all now fixed:

1. `paper_service.py` `_process_open_positions`: when a target's floored
   quantity was zero (realistic on minimum-lot instruments), the loop did
   `break`, which could permanently stop TP4 from ever closing the remainder,
   leaving a position stuck OPEN. Fixed by removing the early `break` so a
   zero-quantity target event (financially inert — all P&L/fee terms scale by
   quantity) still advances `next_target_number` and lets later touched
   targets, including TP4, fire in the same pass. Added
   `test_zero_quantity_target_does_not_block_later_targets` in
   `test_forward_paper.py` to cover it.
2. The synthetic demonstration fixture had no operator-facing activation path
   — only unit tests could load it. Added `build_synthetic_demonstration_service()`
   in `paper_service.py` (extracted shared fixture-replay logic from
   `run_synthetic_demonstration()` into `_replay_synthetic_demonstration()`),
   a new `--enable-forward-paper-demo` CLI flag in `app.py` (mutually
   exclusive with `--enable-forward-paper-engine`), and an
   `is_synthetic_demonstration` flag on `ForwardPaperService` that makes
   `account_document()` correctly report `synthetic_demonstration_values`.
   Covered by `PaperDemoActivationTests` in `test_trading_lab_app.py`,
   including a real HTTP round-trip against `/api/paper-account` and
   `/api/market-timeline`.
3. The disabled-state dashboard message didn't show the exact enablement
   commands. Updated `_disabled_account_document()`'s message to name both
   `--enable-forward-paper-engine` and `--enable-forward-paper-demo`
   explicitly; also added a matching printed message in `app.py`'s
   `run_server()` disabled-state branch.
4. Added the four required lifecycle scripts (`START_TRADING_LAB_DISABLED.ps1`,
   `START_TRADING_LAB_DEMO.ps1`, `STOP_TRADING_LAB.ps1`,
   `GET_TRADING_LAB_STATUS.ps1`). Manually rehearsed: started demo mode,
   confirmed `SYNTHETIC DEMONSTRATION MODE` with 2 completed trades over
   `GET_TRADING_LAB_STATUS.ps1`, then stopped it with `STOP_TRADING_LAB.ps1`
   and confirmed the port listener was gone.

**Why:** The master program's own Phase 1 completion bar requires verified
defects fixed and the disabled/synthetic-demonstration UX to actually exist
before commit — not just be described in the contract doc.

**How to apply:** Full suite (396 tests, up from 391) passes twice under
`python -B -W error`. Markdown Audit reports 0 issues after adding proper
Document Information headers to this session's new tracking files. Ready to
propose the R2-005 commit to the Founder per the 2026-07-31-001 approval-gate
decision.

## 2026-07-31-004 — Founder Phase 2 document review: corrections required, then applied

**Decision:** The Founder reviewed all six Phase 2 documents (contracts,
threat model, runbooks) against a 20-point safety checklist and issued the
verdict **CORRECTIONS REQUIRED BEFORE COMMIT**, with ten specific findings,
one of them high severity. All ten were applied in this same session,
document-only, with no implementation code touched and nothing staged,
committed, or pushed.

**Finding 1 (High) — idempotency-key ambiguity in `TRL_R2_007_MT5_EXECUTION_CONTRACT.md`:**
the original design derived its duplicate-order protection key partly from
repriceable fields ("entry parameters"), so a legitimate retry after an
ambiguous broker result could compute a different key and slip past the
protection. **Fixed** by replacing the single idempotency-key model with two
separate identities: an immutable **execution intent** (derived only from
proposal ID, hashed account/broker fingerprint, instrument, side, approved
size/aggregate-risk identity, strategy ID/version, risk-policy hash,
operating mode, authorization identity, and a one-time nonce — never price)
and a per-try **execution attempt** (intent ID, attempt sequence, quoted
price, timestamp, request hash). Added an explicit state machine
(`CREATED` → `ATTEMPT_PENDING` → `FILLED`/`PARTIALLY_FILLED`/`REJECTED`/
`CANCELLED`/`FROZEN_PENDING_RECONCILIATION` → `NOT_FOUND_SAFE_TO_RETRY`/
`MANUAL_REVIEW_REQUIRED`) so an ambiguous outcome freezes the intent,
forces reconciliation before any new attempt, and only a
`NOT_FOUND_SAFE_TO_RETRY` classification permits a further attempt — always
under the same intent. New acceptance tests added for intent stability
across repricing, restart handling, and ambiguous-reconciliation fail-closed
behavior.

**Finding 2 (Medium) — Role 5 "Independent Risk Partner" independence undefined**
in `TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md`: fixed by requiring role 5 to
be a separately implemented module that never imports or calls role 3's
sizing code, and by adding a `SIZE_MISMATCH_BETWEEN_PARTNERS` rejection when
role 5's independently recomputed size disagrees with role 3's candidate
beyond a documented tolerance.

**Finding 3 (Medium) — credential exposure at the adapter layer** not
addressed in `TRL_R2_007_MT5_EXECUTION_CONTRACT.md`: fixed with an explicit
Section 11 prohibiting credentials/secrets/connection detail in logs,
exceptions, HTTP responses, or exported reports, plus a dedicated
acceptance test.

**Finding 4 (Medium) — no Founder lockout-recovery path** in
`TRL_R2_008_PRIVATE_ONLINE_OPERATIONS_CONTRACT.md`: fixed with a
local-command-only recovery procedure (proof of host control by requiring
local execution; single-use, non-default, non-committed token; session
rotation on use; audit events on generation and use; never weakens
live-trading reauthentication or arming).

**Finding 5 (Medium) — no first-live-activation risk ceiling** in
`TRL_LIVE_EXECUTION_RUNBOOK.md`: fixed with an explicit floor (0.1% of
equity or the broker's absolute minimum size, whichever is larger) for the
first live activation only, raised to the normal default only by deliberate
later decision.

**Finding 6 (Low) — FIB-001 cited a non-existent prior approval** in
`TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md`: fixed by removing the
fabricated citation and requiring an explicit, dated Decision Log entry for
FIB-001's numeric parameters before implementation — none exists yet, so
none is claimed.

**Finding 7 (Low) — fabricated checkpoint labels "TRL-R2-009"/"TRL-R2-010"**
in `TRL_R2_007_MT5_EXECUTION_CONTRACT.md` and
`TRL_FULL_SYSTEM_THREAT_MODEL.md`: fixed — replaced with "Phase 9"/"Phase 10"
respectively, matching the master program's actual phase naming.

**Finding 8 (Low) — typo "R2-R2/Phase 7"** in
`TRL_FULL_SYSTEM_THREAT_MODEL.md` §3.4: fixed to "Phase 7".

**Finding 9 (Low) — no mid-phase threat-model review trigger** in
`TRL_FULL_SYSTEM_THREAT_MODEL.md` §6: fixed — added an explicit trigger for
any security-relevant design change mid-phase, not just phase boundaries.

**Finding 10 (Low) — no escalation path for a fully unreachable host** in
`TRL_EMERGENCY_RUNBOOK.md` §1: fixed — added a row covering broker-app-on-
another-device as the fallback when the host itself, not just the
dashboard, is unreachable.

**Why:** The Founder's review exists precisely to catch design-level gaps
before they become expensive-to-fix code, especially for a system that will
eventually hold live-execution authority. Finding 1 in particular governs
the exact mechanism responsible for preventing a duplicate real-money order
after a crash or ambiguous broker response — worth getting right on paper.

**How to apply:** All six Phase 2 documents now reflect the corrected
design. Terminology (execution intent/attempt, `UNKNOWN_OUTCOME`,
reconciliation, arming, emergency stop) cross-checked for consistency across
all six documents and the five tracking files. Nothing has been staged,
committed, or pushed — awaiting a separate Founder approval pass before
Phase 3 begins.

## 2026-07-31-005 — Final Founder/CTO correction pass: fail-closed first activation and deterministic intent lookup

**Decision:** Two further safety clarifications were requested and applied to
`TRL_R2_007_MT5_EXECUTION_CONTRACT.md` and `TRL_LIVE_EXECUTION_RUNBOOK.md`,
document-only, on top of the 2026-07-31-004 correction pass.

**Correction A — first live activation must fail closed:** the prior rule
("0.1% of equity or the broker minimum, whichever is larger") was replaced
with an explicit computation: before a first live activation, the exact
risk of the broker's *minimum permitted volume* is computed from validated
entry price, mandatory stop, tick value/size, contract size, and currency
conversion where required. At or below 0.1% of equity, the proposal proceeds
normally. Above 0.1%, execution fails closed with
`FIRST_LIVE_MINIMUM_VOLUME_EXCEEDS_TARGET_RISK` and displays the target
percentage, actual percentage, monetary risk, instrument, entry, stop, and
minimum volume in full. Proceeding past that block requires a separate,
single-use, proposal/account/instrument-specific, quickly-expiring Founder
override (`TRL_FIRST_LIVE_OVERRIDE_APPROVAL.v1`) that is an audit event on
both creation and use — and that override **cannot be created at all** if
the minimum-volume risk exceeds 0.5%; that case is an unconditional
prohibition with no override path. The system never raises the target
automatically. New Section 4 added to the R2-007 contract; the Live
Execution Runbook's Section 2 rewritten to walk through the exact block and
override procedure step by step.

**Correction B — deterministic intent lookup before nonce creation:** the
`client_intent_nonce` introduced in 2026-07-31-004 could, in principle, be
generated independently by two near-simultaneous submissions of the same
logical order before either had persisted, producing two different
`execution_intent_id`s for what should have been one intent. Fixed by adding
a new, nonce-free `TRL_EXECUTION_INTENT_LOOKUP_KEY.v1`, derived only from
proposal, account/broker fingerprint, instrument, side, approved size (or
aggregate-risk identity), basket-child identity, strategy, risk-policy hash,
operating mode, and authorization identity. This key is computed and
searched against the durable audit store *before* any nonce or intent is
created: a match reuses the existing intent (including its stored nonce and
full attempt history) and, for an already-terminal intent, answers the
repeat without any new `order_check`/`order_send` call at all; no match
means a nonce and a brand-new intent are generated and persisted atomically,
before any broker call. A lookup or durable-store integrity failure fails
closed to `MANUAL_REVIEW_REQUIRED` rather than ever falling back to creating
a new intent. Basket children each get a stable, deterministically derived
`basket_child_id` folded into the lookup key, so a repeated parent-basket
submission resolves every child individually rather than duplicating or
dropping any of them. R2-007 Section 4 (execution identity) restructured
into new Sections 5.1 (lookup key) and 5.2 (lookup-before-create flow),
ahead of the existing intent-ID/attempt-ID/state-machine content (now 5.3–
5.6); all downstream section cross-references in this document, the Threat
Model, and the Emergency Runbook updated to match the new numbering.

**Why:** Both corrections close gaps in the exact mechanism that will
someday be responsible for a real broker order — worth resolving on paper,
for free, rather than in code, at cost, later.

**How to apply:** No implementation code exists yet, so no test suite was
run; the Markdown Audit, `git diff --check`, UTF-8/BOM/whitespace, JSON
parse, and secret-pattern scans were all re-run clean after this pass (one
Markdown Audit warning, a table row broken by a literal `|` in prose, was
found and fixed during Correction 1 of the prior pass — not reintroduced
here). Nothing staged, committed, or pushed. Branch remains
`codex/TRL-R2-full-vision-execution`, HEAD remains `49fa62c`. Awaiting a
further Founder decision on whether to commit.

## 2026-07-31-006 — Phase 2 committed and pushed; Phase 3 implemented

**Decision:** The Founder approved the twice-corrected Phase 2 documents
without further changes. They were staged (11 files, all under
`Trading_Lab/`), reviewed via `git diff --cached`, and committed as
`ffcdd7417d3fa5dceb40144b74ea5a659309644b` ("Add TRL full-vision Phase 2
contracts, threat model, and runbooks"), then pushed to
`origin/codex/TRL-R2-full-vision-execution` after a separate push
authorization and verification pass. Phase 3 (operating-mode state machine)
was then implemented on top of that commit.

**Phase 3 implementation summary:** one new authoritative module,
`trading_lab_app/mode_service.py` — a `ModeService` class implementing the
seven governed modes (`OFF`, `RESEARCH`, `SYNTHETIC_PAPER`,
`MT5_DEMO_MANUAL`, `MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`,
`MT5_LIVE_AUTOMATED`), a 16-capability governed matrix, the exact three-mode
transition matrix, fail-closed transition rules, and an event-sourced,
hash-chained, atomically-persisted audit log mirroring R2-005's proven
architecture — plus `trading_lab_app/mode_cli.py`, the local-only operator
CLI (`show-mode`, `list-modes`, `explain-mode`, `request-mode`,
`transition-history`). `app.py`, `server.py`, and `service.py` were extended
(new `/api/mode-status` read-only route; startup now resolves and prints
the operating mode; the paper engine is constructed from the resolved mode
when no legacy `--enable-forward-paper-*` flag is given). The dashboard
gained a new "Operating mode" panel. Full detail, the exact transition and
capability matrices, persistence format, and rehearsal evidence are in
`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`.

**A real bug was found and fixed during implementation:** the mode-status
print path in `app.py`'s `run_server()` initially assumed any non-`None`
`server.mode_service` attribute was a real `ModeService`, but several
existing tests pass `mock.Mock()` as a fake server object — `Mock()`
auto-creates attributes, so `getattr(server, "mode_service", None)`
returned a Mock, not `None`, and `mode_status["current_mode"]` crashed with
`TypeError: 'Mock' object is not subscriptable`. Fixed by adding the same
`isinstance(...)` type guard the existing `paper_service`/
`official_news_service` code already uses for exactly this reason, falling
back to a safe in-memory mode service when the object isn't a real
`ModeService`.

**Why the mode/paper integration was decoupled rather than unified:** the
master program's "Required mappings" section (OFF/RESEARCH → disabled
paper; SYNTHETIC_PAPER → synthetic demo) is honored, but only when neither
legacy `--enable-forward-paper-engine` nor `--enable-forward-paper-demo` is
passed. Forcing the legacy flags to also drive the mode service risked
touching already-verified, heavily-tested R2-005 startup logic for no
required benefit this phase; both flags continue to work exactly as before.
This is recorded as a known limitation in the Phase 3 contract, not hidden.

**Why mode changes take effect on next start, not live:** the running
server resolves its mode once at startup; `mode_cli.py` writes to the
durable store but does not signal a running process to reload. This matches
the master program's own framing of mode resolution as a startup-time
concern (Section "STARTUP SAFETY") and avoids the added complexity and risk
of hot-swapping subsystems inside a live server this phase. Verified
directly in the manual rehearsal: each transition required a stop/start
cycle to take visible effect, which is the intended behavior, not a defect.

**How to apply:** Full suite (432 tests, up from 396) passes twice under
`python -B -W error`. Manual loopback rehearsal performed against the real
application on the real port 8765 (not mocks): OFF → RESEARCH →
SYNTHETIC_PAPER → rejected `MT5_DEMO_MANUAL` (`MISSING_MT5_ADAPTER`) →
rejected `MT5_LIVE_AUTOMATED` (`MISSING_MT5_ADAPTER` +
`MISSING_LIVE_ARMING`) → OFF → stopped, port confirmed clear. Nothing
staged, committed, or pushed yet for Phase 3 — awaiting Founder review per
the 2026-07-31-001 approval-gate decision.

## 2026-07-31-007 — Founder correction: removed the legacy-flag authority bypass

**Decision:** The Founder's Phase 3 review found a real architectural
contradiction: the design doc stated `ModeService` is authoritative and
subsystems must be constructed only from the resolved governed mode, but
`app.py` still preserved `--enable-forward-paper-engine` and
`--enable-forward-paper-demo` as direct construction branches that never
consulted or updated `ModeService`. This meant the reported mode
(`/api/mode-status`) and the actually active paper service
(`/api/paper-account`) could disagree, and a CLI flag could activate paper
capability the state machine had not authorized. Correctly flagged as not
acceptable to leave as a "known limitation."

**Root cause:** the original Phase 3 implementation added the mode service
as a new, parallel decision path instead of making it the *only* one — the
old flag-driven `if/elif/else` construction logic in `main()` was left
in place unchanged, so two independent authorities for "is paper active"
existed side by side.

**Fix:** collapsed to exactly one path —
`ModeService` resolved mode → capability check → `_paper_service_for_mode()`.
That single function is now the only paper-service constructor in the
application, used both as `ModeService`'s `subsystem_builder` (so a
transition validates real construction before committing) and again at
startup to build what's actually wired into the server; because both calls
consume the same resolved mode, mode-status and paper-status can no longer
diverge. `--enable-forward-paper-demo` now calls
`ModeService.request_transition("SYNTHETIC_PAPER", actor_channel="LOCAL_OPERATOR")`
— identical to the `mode_cli.py` path — and fails closed if not `ACCEPTED`
(with an idempotency exception: if already `SYNTHETIC_PAPER`, no redundant
transition is attempted, since a same-mode request is otherwise correctly
rejected as `INVALID_TRANSITION` and must not make an already-correct
startup fail). `--enable-forward-paper-engine` now always fails closed with
`LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE` before any other setup work — no
mode is constructed, no file is touched — because none of the seven Phase 3
modes authorizes it, and adding an eighth mode or silently remapping it to
`RESEARCH`/`SYNTHETIC_PAPER` was explicitly out of bounds. A new
`_validate_subsystem_consistency()` check runs immediately before the
server binds and fails closed with `MODE_SUBSYSTEM_CONFIGURATION_MISMATCH`
if the constructed subsystem ever disagrees with the resolved mode's
authoritative capability set — a structural invariant, not just a
convention.

**Why:** a capability gate that can be bypassed by a flag is not a gate.
This needed to be a hard architectural correction, not a documented
limitation, precisely because Phase 5–9 will build real broker execution on
top of the same `ModeService` — any tolerance for a bypass here would
compound into a real safety gap later.

**How to apply:** 15 new tests added (`SingleAuthorityTests` in
`test_operating_mode.py`), covering every item the Founder listed: OFF/
RESEARCH cannot construct an active paper service; SYNTHETIC_PAPER
constructs only the synthetic demonstration service; the demo flag routes
through ModeService, results in `current_mode == SYNTHETIC_PAPER`, creates
normal transition audit events, and cannot bypass a forced rejection; the
engine flag fails closed before server startup with no store/network/
listener/execution side effect; mode-status and paper-status agreement
verified over real HTTP for all three available modes; direct helper calls
rejecting disallowed constructions; a deliberate mismatch raising
`MODE_SUBSYSTEM_CONFIGURATION_MISMATCH`; the existing synthetic
demonstration remaining deterministic; exactly seven modes; no HTTP
mutation route. Full suite: 447 tests (432 + 15), passing twice under
`python -B -W error`. Manual rehearsal repeated end-to-end against the real
application on port 8765, including confirming the failed
`--enable-forward-paper-engine` attempt left the persisted mode file
completely unmutated. Nothing staged, committed, or pushed — awaiting
further Founder review.

## 2026-07-31-008 — Phase 3 tracking closure; Phase 4 (TRL-R2-006 signal intelligence) implemented

Phase 3's operating-mode state machine, previously recorded above as "not
yet committed," is confirmed committed and pushed at
`861e77a6603d8bdb8d4369db442faab2bfadc4f8` (branch
`codex/TRL-R2-full-vision-execution`, local HEAD and
`origin/codex/TRL-R2-full-vision-execution` verified to match exactly
before Phase 4 work began). `TRL_CONTINUATION_STATE.md`/`.json` and
`TRL_FULL_VISION_MASTER_PROGRAM.md` are updated to reflect this; no
tracking-only commit was created, per the governing prompt's instruction
that this closure ride along with the Phase 4 checkpoint commit.

Phase 4 implements the full six-role governed signal-intelligence pipeline
from `TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md`: Data Quality, Market
Regime, Technical Strategy (SMA-001 ported from
`trading_lab_core.strategy.sma`/`sma_cross_signals` unchanged; FIB-001 kept
fully blocked with no fabricated parameters), News/Event Risk, Independent
Risk (structurally separate module, no import of Role 3, no reuse of its
suggested quantity, `SIZE_MISMATCH_BETWEEN_PARTNERS` on disagreement), and
Execution Eligibility. A `BLOCKED` result at any role stops every
downstream role from running (verified by direct test, not just by
convention). The `TRL_SIGNAL_PROPOSAL.v1` schema reuses R2-005's
`paper_data.validate_proposal` for the executable-proposal invariants
rather than forking them.

**Why:** the governing prompt required a completely independent second
risk-sizing implementation (not a second call to the same formula) so a
defect in the shared sizing code cannot silently pass both roles, and
required FIB-001 to remain unimplemented until a dated Founder decision
records its exact numeric parameters — neither of which previously existed
in this codebase.

**How to apply:** one new governed `signal_proposal_generation` capability
was added to `mode_service.py` (denied in `OFF`/MT5 modes, granted in
`RESEARCH`/`SYNTHETIC_PAPER`); `app.py`'s single subsystem-construction
path was extended (not duplicated) with `_signal_service_for_mode` and a
combined `_subsystem_builder_for_mode`, used by both `app.py` and
`mode_cli.py`, so a mode transition validates both the paper service and
the signal service before committing. The wired signal service is
in-memory only in this checkpoint (a documented limitation, not an
oversight — see `TRL_R2_006_SIGNAL_INTELLIGENCE_EVIDENCE.md` Section 10):
`_subsystem_builder_for_mode` is also `ModeService`'s own
`subsystem_builder`, exercised on every transition attempt including from
automated tests, and must therefore never touch the filesystem by default.
63 new tests added (`test_signal_intelligence.py`); one existing test
(`test_forward_paper.py::test_governed_categories_and_schema`) was updated
from an event-category count of 11 to 12 to reflect the new, additive
`SIGNAL_PIPELINE_STEP` timeline category — no existing test was weakened,
skipped, or deleted. Full suite: 510 tests (447 + 63), passing twice under
`python -B -W error`. Manual rehearsal performed end-to-end against the
real application on port 8765: OFF (signal intelligence confirmed
unavailable) -> RESEARCH (SMA-001 BUY proposal generated via
`signal_cli.py`, repeated for determinism, stale evidence BLOCKED, FIB-001
BLOCKED with `STRATEGY_PARAMETERS_NOT_APPROVED`, a controlled Role 5
mismatch fixture BLOCKED with `SIZE_MISMATCH_BETWEEN_PARTNERS`) -> OFF ->
SYNTHETIC_PAPER (availability confirmed, no broker execution) -> OFF, with
port 8765 confirmed clear after every stop. No broker, MT5, external
network, or model API call occurred at any point. Nothing staged,
committed, or pushed — awaiting Founder review and commit approval.

## 2026-08-01-009 — Founder correction pass: durable persistence, SMA-001 geometry removed, performance reporting added, honest confidence status

Founder review of the Phase 4 checkpoint recorded above (2026-07-31-008) found four
contract-level gaps and required them corrected before commit — not treated as
optional known limitations.

**1. Durable persistence, rejected in-memory-only design.** The first pass wired an
in-memory-only signal service for both `RESEARCH` and `SYNTHETIC_PAPER`; proposal and
audit history were lost on every restart. Corrected by separating two previously
conflated concerns in `app.py`: `_signal_service_preflight_for_mode` (side-effect-free,
always `InMemorySignalStore`, used only as part of `ModeService`'s `subsystem_builder`
to check a transition *would* succeed) from `_signal_service_for_mode` (the real
runtime builder, called only after a mode is actually resolved, used by both
application startup and `signal_cli.py`). Both available modes now construct a durable
`LocalSignalStore`-backed service — the earlier draft that kept `SYNTHETIC_PAPER`
in-memory-only because "it matches the existing synthetic-demonstration convention"
was rejected: synthetic evaluations are still real governed evidence worth auditing,
and nothing in the R2-006 contract required losing that history. Both modes share one
durable store file; every persisted proposal's own `operating_mode`/`sample_label`
fields keep RESEARCH and SYNTHETIC_PAPER records distinguishable. Corruption fails
closed with a new stable reason, `SIGNAL_STORE_INTEGRITY_FAILURE` (no R2-006
contract-defined code covers storage corruption, matching `paper_service.py`'s own
precedent of defining implementation-layer codes). `generate_proposal` was also made
idempotent by content (re-submitting identical governed evidence against the same
timeline returns the already-recorded proposal rather than attempting to append
duplicate timeline events) once durability made that case reachable for the first
time.

**2. Invented SMA-001 execution geometry removed.** The first pass invented a 20-bar
swing-stop, 1x/2x/3x/4x-target, 25%-allocation geometry, framed in its own docstring as
a "Phase 4 I/O adaptation" — that framing did not change the fact that no Founder ever
approved those specific numbers, which is exactly the standard already applied to
FIB-001. A repository-wide search of this log, `TRL_BLOCKERS.md`, and every R2-006
document confirmed no such approval exists. The geometry-computing functions
(`_trade_geometry`, `_candidate_quantity`) and their constants were deleted entirely
from `signal_role3_strategy.py`, not merely left unused. SMA-001 now records only the
exact, unmodified R1-kernel crossing *direction* as `candidate_direction` on Role 3's
result and fails closed with a new reason, `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`;
the pipeline's existing short-circuit rule then blocks the proposal before Roles 5/6
ever run. A new blocker row was added to `TRL_BLOCKERS.md` alongside FIB-001's.

**3. Performance/walk-forward reporting implemented.** Not started in the first pass
despite being part of the original Phase 4 scope. New module `signal_reporting.py`
implements `TRL_SIGNAL_PERFORMANCE_REPORT.v1`: one sample label per report (no
blending), walk-forward segments with validated non-overlapping boundaries, a governed
minimum-completed-trades floor (20, matching the contract's own example), and always-
present fee/slippage/spread assumptions. Because no strategy can currently produce a
completed trade (item 2), every report in this checkpoint is honestly
`INSUFFICIENT_SAMPLE` — this is the correct state, not a defect, and the report format
never implies otherwise. `VALIDATION` was added to `signal_data.SAMPLE_LABELS`
(previously only `IN_SAMPLE`/`OUT_OF_SAMPLE`/`WALK_FORWARD`/`SYNTHETIC_PAPER`/
`BROKER_DEMO`/`BROKER_LIVE`) because the reporting requirement separates
IN_SAMPLE/VALIDATION/OUT_OF_SAMPLE as three distinct labels.

**4. Confidence status made explicit.** `compute_confidence()` now returns a
`confidence_status` value (`UNCALIBRATED_HEURISTIC`, the only current member of
`CONFIDENCE_STATUSES`) alongside the numeric score; `signal_data.py` rejects a proposal
whose `confidence_status` doesn't match its resolved `confidence_calibration_source`,
and rejects any calibration source that doesn't resolve to a real registered record.
Every proposal's `explanation` field now carries the full non-promissory disclaimer
text.

**Why:** a numeric confidence score, an invented-but-plausible-looking execution
geometry, and an in-memory-only "durable" store are each individually the kind of gap
that looks like a small implementation detail in isolation but compounds into a real
safety/honesty problem once later phases (execution adapters, live reporting) build on
top of them. Founder review caught all four before commit, which is exactly what this
review gate exists for.

**How to apply:** 45 new tests added
(`SMAGeometryBlockTests` x8, `PerformanceReportingTests` x30, `DurablePersistenceTests`
x18, plus scattered additions/rewrites elsewhere — 122 signal-intelligence tests total,
up from 63). Every existing test that asserted the invented executable-geometry values
was rewritten to test the corrected behavior directly rather than edited to accept
different invented values; no test was weakened, skipped, or deleted merely to pass. A
stray `__pycache__` directory accidentally created by an earlier `py_compile`
diagnostic command (not part of the implementation) was found and removed after it
caused four pre-existing "no generated artifacts" tests to fail; this was a leftover
from a verification command, not a defect in the corrected code. Full suite: 569 tests
(447 + 122), passing twice under `python -B -W error`. Manual rehearsal repeated
end-to-end against the real application on port 8765, plus a real separate-process
`mode_cli.py`/`signal_cli.py` rehearsal sharing one isolated temporary `LOCALAPPDATA`
(never the real one) proving `generate-proposal` in one process is visible to
`proposal-history` in a later, separate process. Neither the SMA-001 nor FIB-001
blocker was marked resolved. Nothing staged, committed, or pushed — awaiting Founder
review and commit approval.

## 2026-08-01-010 — Phase 4 tracking closure; Phase 5 (TRL-R2-007 MT5 execution adapter) implemented

**What:** Phase 4 (TRL-R2-006 governed signal intelligence, including its Founder
correction pass) is complete, committed, and pushed at `5a9570a`; tracking updated
accordingly (`TRL_FULL_VISION_MASTER_PROGRAM.md`, `TRL_CONTINUATION_STATE.md/.json`) per
the Phase 5 kickoff instructions. No tracking-only commit was created; this closure is
recorded for inclusion in the Phase 5 checkpoint commit.

Phase 5 implements the `MT5_DEMO_MANUAL` demo-manual slice of
`TRL_R2_007_MT5_EXECUTION_CONTRACT.md` — see
`TRL_R2_007_MT5_EXECUTION_EVIDENCE.md` for full detail. Three decisions worth recording
here specifically:

**1. Scope resolution: no contract/kickoff conflict.** The R2-007 contract describes the
full multi-phase end state (basket children, live modes, arming tokens, automatic
reconciliation) while the kickoff prompt forbids implementing most of that in this
checkpoint. `TRL_FULL_VISION_MASTER_PROGRAM.md`'s existing phase table already maps each
excluded piece to its own later phase number (baskets → Phase 6, live-automation arming
→ Phase 9, reconciliation → Phase 10), and `mode_service.py`'s own committed Phase 3
description text already framed `MT5_DEMO_MANUAL` as exactly "Phase 5's" deliverable.
This was treated as a clear, well-supported reading — not a genuine contradiction
requiring a stop-and-report — and Phase 5 was scoped to the demo-manual, single-order,
non-basket, non-automated slice accordingly.

**2. Restart-safety fix for `MT5_DEMO_MANUAL`.** The existing Phase 3 startup safe-
downgrade (`_load_startup_state`, `MODE_STARTUP_SAFE_DOWNGRADE`) force-resets any
persisted MT5 mode to `OFF` on every fresh `ModeService` construction — a genuine safety
property for the three automated/live modes (their whole risk is *unattended*
resumption after a crash/restart). Wiring `MT5_DEMO_MANUAL` in naively would have made
it force-reset on every single CLI invocation too, since each `mt5_execution_cli.py`
command constructs a fresh `ModeService` in its own process (mirroring `mode_cli.py`'s
existing, already-relied-upon pattern for `RESEARCH`/`SYNTHETIC_PAPER`) — silently
breaking the entire CLI-driven workflow this checkpoint depends on. Caught by exercising
the actual CLI as separate process invocations during the manual rehearsal, not by the
automated test suite alone (which used a single shared `ModeService` instance per test
and would not have caught a cross-process regression). Fixed by introducing
`AUTOMATED_OR_LIVE_MT5_MODES` (excludes `MT5_DEMO_MANUAL`) as the actual downgrade-check
set — the reasoning: every `order_send` `MT5_DEMO_MANUAL` permits still requires a
fresh, explicit local manual confirmation for that specific order, so persisting the
*mode* across a restart creates no unattended-execution risk, unlike the three modes
still covered by the downgrade. Two existing Phase 3 tests in `test_operating_mode.py`
that asserted a blanket "no MT5 mode ever survives restart" were corrected (not
weakened) to test the now-intentional distinction; the safety property for the three
still-forbidden modes is preserved and re-asserted under its own dedicated test.

**3. SMA-001 defense-in-depth gate.** `signal_strategy_registry.executable_status`
alone does not block SMA-001 (`approval_status` is `EXPERIMENTAL_RESEARCH_ONLY`, not
`APPROVAL_PENDING`) — only Role 3's pipeline-internal crossing-detection logic blocks it
from ever reaching an executable proposal. Because a hand-built, schema-valid proposal
object could claim `strategy_id="SMA-001"` with an executable side without going
through the pipeline, `mt5_execution_service.py` adds its own independent, empty
`EXECUTION_GEOMETRY_APPROVED_STRATEGIES` allowlist, checked before any adapter call,
reusing the identical `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` reason code Role 3
already uses. Neither the SMA-001 nor FIB-001 blocker was resolved, weakened, or worked
around.

**Why:** the restart-safety issue in particular is the kind of gap that a narrowly-scoped
in-process test suite cannot catch by construction (each test constructs one
`ModeService` and keeps using it), which is exactly why the kickoff instructions require
a real, separate-process manual rehearsal in addition to the automated suite.

**How to apply:** 166 new tests across six new test files, plus 3 existing Phase 3/4
assertions corrected (not weakened) to match the now-intentional `MT5_DEMO_MANUAL`
availability/persistence — see `TRL_R2_007_MT5_EXECUTION_EVIDENCE.md` Section 17 for the
full breakdown. Full suite: 737 tests, passing twice under `python -B -W error`. Manual
rehearsal performed against an isolated temporary `LOCALAPPDATA` using the real CLI
entry points as separate process invocations, including one real (fail-closed, no
credential displayed) `RealMT5ExecutionAdapter` dependency/terminal check — the optional
`MetaTrader5` package happens to already be installed in this development environment
(not installed by this work), but no MT5 terminal process was running, so the check
correctly reported `TERMINAL_UNAVAILABLE`. No real broker order was submitted at any
point. Neither SMA-001 nor FIB-001 was marked resolved. Nothing staged, committed, or
pushed — awaiting Founder review and commit approval.

## 2026-08-01-011 — Founder review: cross-process execution-locking race found and corrected

**What:** A Founder-review manual rehearsal, run *after* entry 010's Phase 5 checkpoint, asked for
an explicit audit of the R2-007 contract's execution-intent identity rules against two scenarios:
identical governed input built against two genuinely independent fresh journals, and identical
governed input raced concurrently against *one* shared journal.

**Two-fresh-journal result:** matches the contract exactly, no defect. The contract's Section 5.1
lookup key (no nonce, no price) is deterministic and identical across both independent journals;
the Section 5.3 `execution_intent_id` is explicitly nonce-salted by contract design and legitimately
differs between two journals that have never seen each other's data — the contract never claims
otherwise. See `TRL_R2_007_MT5_EXECUTION_EVIDENCE.md` Section 20.1–20.2.

**Concurrent-single-journal result: a real defect.** `build_order_intent`'s lookup-before-create
sequence and `confirm_and_send`'s duplicate-check-then-reserve sequence had no mutual exclusion
across separate OS processes. Reproduced directly with two genuine `python -B` processes racing
against one initially empty durable journal: both succeeded, both minted a *different*
`order_intent_id`, and the durable file ended up recording only one of them — the other process's
write was silently lost, while that process's own in-memory state still believed its creation had
succeeded and could have gone on to attempt a real send for an intent the journal had no record of.
This is exactly the kind of gap a single-process-oriented test suite cannot catch by construction,
which is why the kickoff instructions require real separate-process rehearsal in addition to the
automated suite — and why it surfaced now rather than during the original implementation.

**Correction:** added `_CrossProcessFileLock` (atomic exclusive-file-creation mutex,
owner-token-verified release, bounded stale-lock recovery) and `_ThreadLock` (in-memory-store
equivalent) to `mt5_execution_journal.py`; `ExecutionJournalWriter.acquire_creation_lock()` wraps
both critical sections, reloading the journal from disk immediately on acquisition so a stale
in-memory snapshot can never defeat the lock. New reason code `EXECUTION_LOCK_UNAVAILABLE` fails
closed on contention rather than proceeding unlocked. A second, independently-caught defect during
this same correction: the lock's original `release()` unconditionally unlinked whatever file
currently existed at the lock path — if a lock was ever broken as stale and re-acquired by a
different owner, the original (late) owner's `release()` would have deleted that new owner's live
lock. Fixed with a unique owner token written into the lock file and checked before unlink. Full
detail: `TRL_R2_007_MT5_EXECUTION_EVIDENCE.md` Section 20.3–20.4.

**Why:** duplicate broker orders and lost audit records are exactly the failure mode the entire
execution-intent identity design (contract Section 5) exists to prevent; a race that defeats it
silently, with no error raised to either caller, is a safety-critical defect, not a minor one.

**How to apply:** 25 new tests (7 `test_mt5_execution_concurrency.py` — genuine separate-process
races for both intent creation and send, synchronized via readiness-marker files rather than a
sleep guess; 14 `test_mt5_execution_journal_lock.py` — acquire/release/exception-safety/timeout/
stale-lock/owner-token-safety/reload-after-acquire; 4 `TwoFreshJournalIdentityTests` formalizing
the two-fresh-journal experiment as a permanent regression). One test-isolation defect found and
fixed during this same pass: `test_mt5_execution_concurrency.py`'s send-race setup monkeypatched
`EXECUTION_GEOMETRY_APPROVED_STRATEGIES` without restoring it, polluting later test files' module
state in a full-suite run — fixed with `addCleanup`. Full suite: 762 tests, passing twice under
`python -B -W error` (up from 737; a stray `__pycache__` from an earlier `py_compile` diagnostic
command was found and removed first, exactly the same class of leftover-artifact issue recorded in
entry 009 — not a defect in the corrected code). The original two-genuine-process race was re-run
five more times after the fix, plus the permanent automated regression, with zero recurrence.
Manual rehearsal repeated for lock timeout and journal-corruption-under-lock, both against isolated
temporary storage with the fake adapter only. Also completed during this pass: a status-command
side-effect audit (found to be intentional, contract-required, bounded Phase 3 behavior — not
redesigned) and a precise LOCALAPPDATA disclosure correcting an earlier overly-broad "untouched"
claim (`TRL_R2_007_MT5_EXECUTION_EVIDENCE.md` Section 20.6–20.7). Neither SMA-001 nor FIB-001 was
touched. Phase 6 was not started. Nothing staged, committed, or pushed — awaiting Founder review
and commit approval.

## 2026-08-01-012 — Phase 5 tracking closure; Phase 6 fail-closed stop; TRL-R2-009 contract-authoring checkpoint

**What:** Phase 5 (TRL-R2-007 MT5 execution adapter, `MT5_DEMO_MANUAL` demo-manual
slice) is complete, committed, and pushed at `49b8f743b2e4db967670df35cbb11d2a4ad7f7fa`;
tracking updated accordingly (`TRL_FULL_VISION_MASTER_PROGRAM.md`,
`TRL_CONTINUATION_STATE.md/.json`). No separate tracking-only commit was created for
this closure; it is recorded here for inclusion in whichever future commit the
Founder next approves.

**1. Phase 6 implementation attempt — correct fail-closed stop.** A Phase 6
implementation kickoff was received. Startup verification (branch, HEAD, upstream,
main SHA, clean tree, port 8765, no running process) passed. A full search of
`TRL_FULL_VISION_MASTER_PROGRAM.md`, `TRL_CONTINUATION_STATE.md/.json`,
`TRL_DECISION_LOG.md`, `TRL_BLOCKERS.md`, `TRL_R2_007_MT5_EXECUTION_CONTRACT.md`
Section 5.6, `TRL_FULL_SYSTEM_THREAT_MODEL.md` Section 3.6, and
`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` found no dedicated Phase 6 controlled-basket
contract — only forward-reference fragments (a `basket_child_id` identity hook, a
threat/mitigation sentence pair, and a capability-matrix placeholder). Unlike every
other phase (5 → R2-007, 8 → R2-008), Phase 6 had never been assigned a `TRL-R2-0XX`
contract number. Per the kickoff instruction's own explicit rule ("If no Phase 6
controlled-basket contract exists, stop and report... Do not invent a contract"), the
correct outcome — `PHASE 6 CONTRACT NOT FOUND` — was reported with no implementation,
no file change, and no repository state change of any kind.

**2. Independent conflict found during the same review.** Separately from the missing
contract, `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`'s committed, approved capability
matrix was found to grant the broad `basket_execution` capability only to the
still-future, still-unavailable `MT5_DEMO_AUTOMATED`/`MT5_LIVE_AUTOMATED` rows —
`MT5_DEMO_MANUAL`'s granted set does not include it. This directly conflicts with any
design that assumes `MT5_DEMO_MANUAL` can perform basket execution without a
capability-matrix change, and was reported alongside the missing-contract finding
rather than resolved unilaterally.

**3. Contract-authoring checkpoint (this entry).** The Founder subsequently issued a
dedicated, implementation-scoped-out "contract-authoring checkpoint" instruction with
explicit authoritative decisions resolving both findings above:
`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` is now authored as the governing
Phase 6 contract. **Numbering:** R2-009, not R2-006 (already implemented, unrelated)
and not R2-008 (`TRL_R2_008_PRIVATE_ONLINE_OPERATIONS_CONTRACT.md` already exists and
governs the unrelated Phase 8 private/online checkpoint) — R2-008 was not renamed,
overwritten, reinterpreted, or substantively modified. **Capability decision:** a new,
narrow capability `manual_basket_execution` is granted only to `MT5_DEMO_MANUAL`
(`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.1); the existing broad
`basket_execution` capability is left unchanged, still reserved for the future
automated/live modes only. Basket order-checking additionally requires
`mt5_order_check`; basket child sending additionally requires `mt5_order_send` and
`manual_broker_execution` — `manual_basket_execution` alone is never sufficient.
**Everything else in the R2-009 contract** (basket/child schemas, deterministic
lookup-before-create identities extending R2-007 Section 5.1/5.6 exactly as already
anticipated, zero-tolerance exact quantity/allocation conservation with no rounding
direction invented, inherited-order-type/no-conversion policy, sequential
single-attempt-per-child send with the existing cross-process lock, truthful
rejection/partial/uncertain-freeze behavior, an explicit no-rollback/no-compensation
statement, reuse of the existing Phase 5 adapter/journal/locking architecture with a
closed additive event/reason-code vocabulary, a local-only CLI, and a strictly
read-only HTTP/dashboard surface) follows directly from the Founder's authoritative
decisions and from the already-committed Phase 5/R2-007/Phase 3 architecture — no
business or safety rule was invented independently. SMA-001
(`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`) and FIB-001
(`STRATEGY_PARAMETERS_NOT_APPROVED`) remain fully blocked and are independently
re-enforced by the new contract for basket construction specifically
(`TRL_BLOCKERS.md`). This checkpoint changed documentation only: one new file
(`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md`) and five narrowly-scoped
tracking/contract edits — no Python, JavaScript, HTML, CSS, or test file was touched;
no Phase 6 source module exists; Phase 7 was not started; nothing was staged,
committed, or pushed.

## 2026-08-01-013 — Founder correction pass on the R2-009 contract: schema compatibility, confirmation lifecycle, check freshness, sequential child authority

**What:** The Founder reviewed the first R2-009 draft (entry 2026-08-01-012) and issued
four corrections, all resolved in this pass. The contract-authoring scope remains
unchanged (7 files: 1 new + 6 modified, 0 staged); only the content of
`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` was rewritten. No Python,
JavaScript, HTML, CSS, or test file was touched; nothing staged, committed, or pushed;
Phase 6 implementation has not started; Phase 7 was not started.

**1. Phase 5 schema-compatibility correction.** The first draft described basket
children as an extension of `TRL_MT5_ORDER_INTENT.v1`/`ORDER_INTENT_FIELDS` (two new
nullable fields, `basket_id`/`basket_child_id`) and described the basket-child lookup
key as extending Phase 5's `execution_intent_lookup_key` function with the
`approved_aggregate_risk_id`/`basket_child_id` fields R2-007 Section 5.1 had reserved
for future use. Both would have required modifying the closed, already-implemented
Phase 5 `v1` schema and its lookup-key function. The Founder ruled `TRL_MT5_ORDER_INTENT.v1`
must remain completely unchanged. The contract now defines six separate,
independently versioned basket schemas (`TRL_BASKET_PLAN.v1`, `TRL_BASKET_CHILD_INTENT.v1`,
`TRL_BASKET_CHECK_RESULT.v1`, `TRL_BASKET_CONFIRMATION.v1`,
`TRL_BASKET_CHILD_EXECUTION_RESULT.v1`, `TRL_BASKET_STATUS.v1` — new Section 1.1,
Sections 9–12/36), each referencing the Phase 5 parent order intent by ID and pinned
content hash without adding any field to it. `TRL_R2_007_MT5_EXECUTION_CONTRACT.md`
Section 5.6's forward-looking `basket_child_id` sketch is explicitly noted as
superseded for Phase 6 purposes by the new Section 17.4 derivation — that file itself
was not touched (out of this checkpoint's authorized scope).

**2. Basket-identity correction: no nonce in the basket ID.** The first draft generated
`basket_id` with a random creation nonce, mirroring Phase 5's `order_intent_id`
pattern. The Founder ruled the basket ID itself must never contain a nonce — it must be
a pure deterministic function of the basket's own immutable identity. Corrected:
`basket_id = "bsk_" + sha256("TRL-BASKET-ID.v1\n" + basket_lookup_key)[:32]` (Section
17.2); `basket_child_id` similarly derived deterministically from `basket_id` +
`canonical_basket_plan_hash` + child index + target/allocation/quantity + inherited
authority fields, with no nonce anywhere in the basket layer (Section 17.4). The only
nonce in the combined Phase 5 + Phase 6 design remains Phase 5's own
`client_intent_nonce` on the parent order intent, untouched.

**3. Confirmation-challenge and lifecycle correction.** The first draft reused Phase
5's 8-hex-character `confirmation_challenge_code` pattern with no defined multi-child
authorization lifecycle, leaving ambiguous whether each `send-basket-child` call needed
to resupply the code. The Founder specified an exact derivation
(`sha256("TRL-BASKET-CONFIRM.v1\n"+basket_id+"\n"+canonical_basket_plan_hash)[:16]`,
lowercase hex), an exact entry syntax (`CONFIRM-BASKET <16-hex-challenge>`, ASCII,
case-sensitive prefix, exactly one space, exactly 16 lowercase hex characters, no
extra content), and a precise lifecycle (Section 13.4/13.4.1): the code is single-use,
but the resulting `ACCEPTED` `TRL_BASKET_CONFIRMATION.v1` record is a durable,
basket-scoped authorization that persists across multiple sequential child sends until
explicitly invalidated (Section 13.6: plan/account mismatch, any required child's check
going stale, basket/confirmation expiry, a child rejection/partial/uncertain result, or
the basket reaching a terminal state) — later child sends never resubmit or re-consume
the code. Confirmation acceptance is cross-process-lock-protected so two concurrent
`confirm-basket` calls produce at most one accepted event.

**4. Check-freshness and next-child-sequencing correction.** The first draft left
check-freshness duration and the interaction between all-child checking, confirmation,
and later sequential sends unspecified, and retained a `send-basket-child <basket_id>
<child_id>` command whose child-ID argument created room for operator error (skip,
resend, reorder). The Founder required an exact, Phase-5-referenced freshness bound
rather than a new invented one: the contract now cites the existing, already-committed
`mt5_execution_service.CHECK_FRESHNESS_SECONDS = 120` and
`CONFIRMATION_LIFETIME_SECONDS = 300` constants unchanged (Section 24.1), revalidated
at exactly three points (confirmation request, confirmation acceptance, and
immediately before each individual child send) — a stale check at any of the three
invalidates the confirmation and returns the basket to `CHECK_REQUIRED` for every
required child, not just the stale one. The CLI's per-child-ID send command is replaced
with an argument-free `send-basket-next <basket_id>` (Section 26/34) — the service
alone computes the next eligible child from durable state, so there is no argument an
operator could use to select the wrong one. The basket state vocabulary was expanded
accordingly (Section 14) to distinguish `REJECTED` (governance/schema rejection, zero
broker sends) from `BLOCKED` (SMA-001/FIB-001 or capability-gate rejection, zero broker
sends) from `FAILED` (the first-ever sent child rejected by the broker with zero prior
fills) from `PARTIALLY_COMPLETED` ("partial success" — one or more children filled
before the basket stopped), with `reconciliation_required` redefined as a derived
boolean flag (true exactly for `PARTIALLY_COMPLETED`/`FROZEN`) rather than a competing
status value. The reason-code and event vocabularies (Sections 15–16) were
deduplicated during the same pass (e.g. `BASKET_CONFIRMATION_ALREADY_ACCEPTED`
replaces "already consumed" phrasing to match the new lifecycle's own terminology;
`BASKET_CHILD_NOT_NEXT_ELIGIBLE` replaces two overlapping sequence-violation codes).

`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.1 was reviewed against all four
corrections and required no change — its only R2-009 cross-references are by section
number (Section 6, Section 13), both of which remain valid after the rewrite; the
capability decision itself (`manual_basket_execution` granted only to `MT5_DEMO_MANUAL`,
`basket_execution` unchanged) is untouched. SMA-001 and FIB-001 remain fully blocked,
independently re-enforced by the corrected contract at basket-construction time.

## 2026-08-01-014 — Founder final lifecycle correction on the R2-009 contract: confirmation cycles, stale checks after partial progress, child-state consistency

**What:** The Founder reviewed the second R2-009 draft (entry 2026-08-01-013) and found
a real contradiction plus two further gaps, all resolved in this pass. The
contract-authoring scope remains unchanged (7 files: 1 new + 6 modified, 0 staged);
only the content of `TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` was rewritten.
No Python, JavaScript, HTML, CSS, or test file was touched; nothing staged, committed,
or pushed; Phase 6 implementation has not started; Phase 7 was not started.

**1. Confirmation-cycle contradiction.** The second draft derived the confirmation
challenge from only `basket_id` + `canonical_basket_plan_hash` — both of which never
change for a basket's lifetime. That formula would silently regenerate the *same*
challenge across two genuinely different confirmation cycles (e.g. before any child was
sent, versus after one child filled and the remaining children's checks were refreshed),
even though the first challenge had already been declared permanently single-use. The
Founder introduced a `confirmation_basis_hash` (Section 13.1) binding basket ID, plan
hash, account fingerprint, the ordered set of already-filled children, the ordered set
of currently-required fresh child checks (by a new deterministic `check_result_id` —
Section 11), the next eligible child, operating mode, and the `CONFIRMATION_LIFETIME_SECONDS`
*value* (not a live timestamp, so the basis stays reproducible for reuse checks). The
challenge formula now includes this basis hash; a deterministic, nonce-free
`confirmation_request_id` is derived from basket ID + plan hash + basis hash (Section
13.1). Re-requesting confirmation with an unchanged basis reuses the existing active
request and challenge (`BASKET_CONFIRMATION_REQUEST_REUSED`); any basis change
invalidates the prior request and produces a genuinely new request ID and challenge
(`BASKET_CONFIRMATION_BASIS_CHANGED`) — this is why a later valid confirmation cycle is
never "reuse" of the earlier single-use acceptance. `TRL_BASKET_CONFIRMATION.v1`
(Section 12) was extended with the new identity fields plus a `canonical_confirmation_record_hash`
(Section 12.1) that, mirroring the plan-hash pattern, covers only the immutable request
identity and excludes the four mutable lifecycle fields (`status`, `accepted_at_utc`,
`invalidated_at_utc`, `invalidated_reason`). HTTP confirmation remains prohibited without
exception.

**2. Stale checks after one or more fills must never reset a filled child.** The prior
draft's stale-check rule returned "every required child" to `CHECK_REQUIRED` without
distinguishing whether any child had already filled — which, read literally, would have
reset an already-`FILLED` child's status. The Founder ruled this must never happen:
Section 24.2 now defines two explicit scenarios. **(A) Zero prior fills:** unchanged from
the prior draft — every currently-required child needs a fresh check again. **(B) One or
more prior fills:** every `FILLED` child's `TRL_BASKET_CHILD_EXECUTION_RESULT.v1` record
and journal history is preserved permanently and is never rechecked, resent, replaced,
rolled back, compensated, or counted as pending (Section 11.1 marks a `FILLED` record
immutable); only the remaining, still-unsent children require fresh checks; the basket
returns to `CHECK_REQUIRED` while `TRL_BASKET_STATUS.v1` (Section 36, new
`filled_child_count`/`completed_quantity` fields) continues truthfully reporting the
preserved progress. **This recoverable state is explicitly not `PARTIALLY_COMPLETED`**
(Section 14.3/14.4) — `PARTIALLY_COMPLETED` is now defined strictly as a *permanent* stop
requiring both a prior fill and a later definitive non-recoverable event (rejection,
expiry-after-fills), never an ordinary recheck cycle. The next-eligible-child rule
(Section 26) was correspondingly tightened to require every lower-indexed child to be
`FILLED` and the target child's check to be one of the confirmation's own bound
`ordered_required_check_ids`.

**3. Child-state vocabulary correction.** The prior draft's child vocabulary included
`CANCELLED` (Phase 6 implements no broker, automatic, rollback, compensation, or
reconciliation cancellation, so no code path can legitimately produce it) and a
child-level `AWAITING_CONFIRMATION` (basket confirmation is authoritative at the basket
level; a duplicated per-child confirmation state could contradict it). Both are removed.
The corrected, Founder-approved minimum vocabulary (Section 14.5) is exactly: `CREATED,
CHECK_REQUIRED, CHECKING, CHECK_PASSED, SEND_RESERVED, FILLED, PARTIALLY_FILLED,
REJECTED, FROZEN_PENDING_RECONCILIATION, EXPIRED, BLOCKED` — with `EXPIRED`/`BLOCKED`
child transitions now precisely defined as flowing from the corresponding basket-level
terminal transition, and `PARTIALLY_FILLED` explicitly terminal for Phase 6 (no
remainder-chasing attempt). The basket-level vocabulary gained an explicit initial
`CREATED` state (distinct from `CHECK_REQUIRED`, which now means "needs a (re)check,
having been touched before") and explicit nonterminal/terminal lists (Section 14.2);
`FROZEN` is confirmed terminal for Phase 6 sending specifically, while remaining
examinable only by a later, separately Founder-approved Phase 10 reconciliation phase.
Reason codes `BASKET_RECHECK_REQUIRED` and `BASKET_CHILD_ALREADY_FILLED` were added, and
`BASKET_LOOKUP_STORE_INTEGRITY_UNCERTAIN`/`BASKET_LOCK_UNAVAILABLE` were renamed to the
Founder's exact final names `BASKET_JOURNAL_INTEGRITY_UNCERTAIN`/
`BASKET_EXECUTION_LOCK_UNAVAILABLE` throughout the contract; event names
`BASKET_PARTIAL_SUCCESS`/`BASKET_COMPLETE` were renamed to `BASKET_PARTIALLY_COMPLETED`/
`BASKET_COMPLETED` so every event name is character-identical to the `basket_status`
value it reports.

`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.1 was reviewed against this
correction and required no change. Phase 5 backward compatibility (Section 1.1) was
reconfirmed unaffected — every new confirmation-cycle field lives only on the Phase-6-
owned `TRL_BASKET_CONFIRMATION.v1`. SMA-001 and FIB-001 remain fully blocked.

## 2026-08-01-015 — Founder final correction on the R2-009 contract: expired-request immutability and unique reconfirmation challenges

**What:** The Founder reviewed the third R2-009 draft (entry 2026-08-01-014) and found
that its own fix still permitted an expired-but-unaccepted confirmation request to be
reissued using the *same* `confirmation_basis_hash`-derived `confirmation_request_id`
and the *same* `challenge_hex`, only replacing its timestamps — meaning an expired
challenge could, under that design, become valid again the moment it was reissued. This
is corrected in this pass. The contract-authoring scope remains unchanged (7 files: 1
new + 6 modified, 0 staged); only the content of
`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` was rewritten. No Python,
JavaScript, HTML, CSS, or test file was touched; nothing staged, committed, or pushed;
Phase 6 implementation has not started; Phase 7 was not started.

**Fix: separate confirmation-basis identity from confirmation-cycle identity.**
`confirmation_basis_hash` (Section 13.1) is retained exactly as the deterministic
snapshot of the current execution authority (basket, account, filled-child set,
required-check set, next eligible child, mode, confirmation-lifetime policy value) —
but it no longer, by itself, identifies one confirmation-request instance, because the
same unchanged basis can legitimately span more than one *cycle* (an expired-and-
reissued attempt at confirming that same basis). A new immutable, durable, monotonic
`confirmation_cycle_number` (Section 13.1a) — starting at `1` per basket, allocated only
when a genuinely new request record is created, under the cross-process lock, by
scanning the journal for the highest existing cycle number for that basket and never
reused, decremented, or reset (a corrupted/unreadable journal fails closed with
`BASKET_JOURNAL_INTEGRITY_UNCERTAIN` rather than restarting numbering at `1`) — is now
folded, together with that cycle's own freshly assigned `requested_at_utc`/
`expires_at_utc`, into both `confirmation_request_id` and `challenge_hex` (Section
13.1b–13.1c). Because a cycle's own fixed timestamps and number are baked into its
request ID and challenge, **every cycle produces a unique challenge, including a
same-basis reissue after expiry** — an expired cycle's record (`TRL_BASKET_CONFIRMATION.v1`,
now with an `expired_at_utc` field distinct from `invalidated_at_utc`) is never rewritten,
its identity fields never change again, and its challenge can never coincide with, or
later be accepted as, any subsequent cycle's challenge. `confirm-basket` now resolves an
entered challenge against basket confirmation-cycle history in explicit precedence order
(Section 13.4): matches the current cycle → full acceptance checks; matches this
basket's own prior **expired** cycle → reject with `BASKET_CONFIRMATION_EXPIRED`
specifically (per the Founder's exact instruction — an old challenge is never accepted
merely because a newer cycle now exists); matches a prior **invalidated** cycle → reject
with `BASKET_CONFIRMATION_INVALIDATED`; matches a different basket's cycle (or this
basket's already-`ACCEPTED` cycle, unreachable in practice) → reject with the renamed
`BASKET_CONFIRMATION_WRONG_REQUEST` (replacing `BASKET_CONFIRMATION_WRONG_BASKET`, since
a wrong challenge can now be wrong-cycle as well as wrong-basket); matches nothing →
`BASKET_CONFIRMATION_MISMATCH`. A new `BASKET_CONFIRMATION_EXPIRED` journal event was
added (distinct from the basket-level `BASKET_EXPIRED`), appended the instant a cycle's
expiry is materialized; every `BASKET_CONFIRMATION_*`/`BASKET_RECHECK_REQUIRED` event's
payload now references the affected cycle's `confirmation_request_id` **and**
`confirmation_cycle_number`. Repeated status inspection or a same-basis re-request while
a cycle remains active still never extends its window (`requested_at_utc`/
`expires_at_utc` immutable once assigned — unchanged behavior from entry 014, now
additionally guaranteed by the cycle's timestamps being baked into its own identity
hash, making an accidental extension structurally impossible rather than merely a
documented rule). `TRL_BASKET_STATUS.v1` gained `active_confirmation_cycle_number`
alongside the existing `active_confirmation_request_id`.

`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.1 was reviewed against this
correction and required no change. Phase 5 backward compatibility (Section 1.1) was
reconfirmed unaffected — `confirmation_cycle_number` exists only on the Phase-6-owned
`TRL_BASKET_CONFIRMATION.v1`; no Phase 5 schema gained a new required field. SMA-001 and
FIB-001 remain fully blocked.

## 2026-08-01-016 — Founder correction on the R2-009 contract: authorization-progression contradiction between one-confirmation sequential sending and a live-recomputed basis

**What:** The Founder found a genuine internal contradiction in the fourth R2-009 draft
(entry 2026-08-01-015) before any implementation began: `confirmation_basis_hash` bound
`ordered_filled_child_ids` and `next_eligible_child_id` as **live** values, and Section
13.4's acceptance check plus Section 26's send-time check both compared the accepted
record's frozen values against a **freshly recomputed** basis/next-child at send time.
Because the same contract also claimed (Section 13.4.1) that one accepted confirmation
authorizes the *entire* sequential run of remaining children, and because an ordinary
successful fill necessarily changes both the live filled-child set and the live
next-eligible child, the send-time check as written (`its next_eligible_child_id equals
the child just computed`) would have failed for every child past the first one sent
under a cycle — silently contradicting the multi-child-authorization design the same
document claimed to implement. This is corrected in this pass, before any implementation
exists. The contract-authoring scope remains unchanged (7 files: 1 new + 6 modified, 0
staged); only the content of `TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` was
rewritten. No Python, JavaScript, HTML, CSS, or test file was touched; nothing staged,
committed, or pushed; Phase 6 implementation has not started; Phase 7 was not started.

**Fix: the confirmation basis is now a fixed authorization checkpoint, not a live
projection.** Three renamed, precisely-defined fields (Section 13.1.1) replace the old
live pair: **(A)** `authorized_prior_filled_child_ids` — the children already `FILLED`
*before* this cycle was requested (normally empty for a first cycle), an immutable
snapshot never updated by this cycle's own later fills; **(B)**
`authorized_remaining_child_ids` — the *complete* ordered set of unsent children this
one accepted cycle may authorize sending, in sequence, not merely "the next one," and a
child stays listed here for the whole cycle even after it fills; **(C)**
`authorized_start_child_id` — the lowest-index member of (B) at request time, purely
informational/display, explicitly not required to keep equaling the *live* next-eligible
child as progression advances. `confirmation_basis_hash` (Section 13.1) is now computed
**once**, at `request-basket-confirmation` time, and is never recomputed against a later,
more-advanced live state during normal progression — Section 13.4's accept-time
recomputation and Section 13.3 step 6's re-request comparison are both explicitly
reframed as defensive checks against otherwise-unexpected drift (since no child of a
cycle can fill before that cycle is accepted, given `request-basket-confirmation` is only
reachable from `CHECK_COMPLETE`/`AWAITING_CONFIRMATION`, before any send), not as
mechanisms that ever fire during ordinary successful multi-child progress. Section 26's
send-time gate is corrected to match: the live next-eligible child (still freshly derived
every time, and now explicitly documented as a *derived service projection*, never a
confirmation-record field) must be a **member** of `authorized_remaining_child_ids` with
every lower-indexed child either in `authorized_prior_filled_child_ids` or durably
`FILLED` during this same cycle — replacing the old, incorrect exact-equality check
against a single frozen `next_eligible_child_id` field. Section 13.4.1 was rewritten to
state explicitly, per the Founder's authoritative list, that a child reaching `FILLED`
never by itself invalidates the authorization, creates a new cycle, requires the
challenge again, changes the basis, or permits parallel execution — and Section 13.6's
invalidation-condition list now carries an explicit "never invalidates" companion list
covering exactly those cases. Section 24.2.B (stale check after prior fills) and the
testing/rehearsal sections (40/41) were updated to reference the renamed fields and to
require an explicit multi-child-under-one-confirmation rehearsal (confirm once, then
`send-basket-next` three separate times for a three-child basket, verifying the
confirmation record's identity fields never change). `TRL_BASKET_STATUS.v1` (Section 36)
gained `authorized_start_child_id`, `authorized_remaining_child_ids`, a separate
`live_next_eligible_child_id`, and `remaining_quantity`, and its `confirmation_status`
vocabulary was corrected to drop an inconsistent `REJECTED` value — a wrong
`confirm-basket` entry is, and always was intended to be, an attempt-level
`BASKET_CONFIRMATION_REJECTED` journal event, never a competing request or a new
request-lifecycle status value (the record's own `status` field remains `REQUESTED`
afterward, per Section 13.4, now stated explicitly to prevent a future implementation
from inventing a contradictory `"REJECTED"` status).

`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.1 was reviewed against this correction
and required no change. Phase 5 backward compatibility (Section 1.1) was reconfirmed
unaffected — every renamed/added field lives only on the Phase-6-owned
`TRL_BASKET_CONFIRMATION.v1`/`TRL_BASKET_STATUS.v1`. SMA-001 and FIB-001 remain fully
blocked.

## 2026-08-01-017 — Founder approval and local commit of the TRL-R2-009 contract-authoring checkpoint

**Decision:** The Founder reviewed the R2-009 contract through all four correction passes
(entries 2026-08-01-013 through -016) and approved:

- `TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md` as the governing Phase 6 —
  Controlled Basket Execution contract.
- The narrow capability amendment `manual_basket_execution`, granted only to
  `MT5_DEMO_MANUAL` (`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` Section 3.1). The broad
  `basket_execution` capability remains unchanged and reserved for the still-future,
  still-unavailable `MT5_DEMO_AUTOMATED`/`MT5_LIVE_AUTOMATED` modes.
- A local commit of exactly the 7 files that make up this contract-authoring checkpoint
  (1 new, 6 modified — the R2-009 contract itself plus the six tracking/governance
  documents kept in sync with it).

**Why:** The original Phase 6 implementation attempt correctly stopped fail-closed with
`PHASE 6 CONTRACT NOT FOUND` because no governing contract existed. Four Founder
correction passes then closed every substantive gap found in successive drafts: Phase 5
backward compatibility (no change to `TRL_MT5_ORDER_INTENT.v1` or any other Phase 5 `v1`
schema/function/persisted document); fully deterministic, nonce-free basket and
basket-child identity; an exact, versioned, single-use-per-cycle confirmation challenge
with permanently immutable expired/invalidated records; and a fixed authorization-
checkpoint confirmation-basis design that correctly allows one accepted confirmation to
govern the sequential sending of an entire basket's remaining children without a normal
successful fill ever forcing reconfirmation. With no further contradictions found, the
Founder authorized finalizing and committing this checkpoint locally.

**How to apply:** This commit records the *contract*, not an *implementation* — Phase 6
source code, tests, CLI, HTTP routes, and dashboard changes remain entirely unbuilt and
are explicitly deferred to a separate, later checkpoint that must itself follow this
contract without inventing business or safety rules. Remote push of this checkpoint's
commit requires a separate, explicit Founder approval, per the standing commit/push
policy (`TRL_DECISION_LOG.md` entry 2026-07-31-001) — this decision authorizes the local
commit only, not the push. Phase 5 remains complete, committed, and pushed at
`49b8f743b2e4db967670df35cbb11d2a4ad7f7fa`. SMA-001
(`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`) and FIB-001
(`STRATEGY_PARAMETERS_NOT_APPROVED`) remain fully blocked and are unaffected by this
approval. Phase 7 was not started and is not referenced as available anywhere in the
approved contract.

## 2026-08-01-018 — Founder approval and verified remote push of the TRL-R2-009 contract-authoring checkpoint

**Decision:** The Founder separately authorized pushing the local commit recorded in
entry 2026-08-01-017 (`d4b8ca5625cceeae403e6cbaf0e6628efc947722`, "Define TRL-R2-009
controlled basket execution contract") to `origin/codex/TRL-R2-full-vision-execution`.
Pre-push verification confirmed the exact expected pre-push state (branch, HEAD, upstream
SHA at the prior Phase 5 commit, one commit ahead, clean working tree and index, no
untracked files, exactly the 7 documentation/governance files in the commit, port 8765
clear, no Trading Lab Python process). The push completed as `49b8f74..d4b8ca5
codex/TRL-R2-full-vision-execution -> codex/TRL-R2-full-vision-execution`. Post-push
verification confirmed local HEAD, `origin/codex/TRL-R2-full-vision-execution`, and the
upstream-tracking ref all equal `d4b8ca5625cceeae403e6cbaf0e6628efc947722` exactly, with
no ahead/behind marker, a clean working tree and index, no untracked files, no additional
commit created, and `main` unchanged at `8ada27f915091b91ddbc421aae06c7c5b36e068f`.

**Why:** This is the standard two-step commit/push approval the program's commit/push
policy requires (`TRL_DECISION_LOG.md` entry 2026-07-31-001) — a separate, explicit
Founder authorization for the push, distinct from the earlier authorization for the local
commit itself (entry 2026-08-01-017).

**How to apply:** `TRL-R2-009` is now the governing Phase 6 contract, committed and
pushed, available to any future session working from this branch without relying on
uncommitted local state. Phase 6 implementation remains entirely unbuilt and is
explicitly deferred to a separate, later checkpoint that must follow this pushed
contract without inventing business or safety rules. A subsequent continuation-state
synchronization pass (this same session) found and corrected stale "push pending"
wording in `TRL_FULL_VISION_MASTER_PROGRAM.md`, `TRL_CONTINUATION_STATE.md`, and
`TRL_CONTINUATION_STATE.json` left over from before this push completed — including a
stale `Current HEAD` field in `TRL_CONTINUATION_STATE.md` that still named the prior
Phase 5 commit rather than this verified checkpoint. That synchronization is itself a
distinct, later governance checkpoint from the R2-009 commit this entry records; its
exact repository status (staged, committed, pushed) is determined by Git at any given
moment, not restated here — Phase 6 controlled-basket implementation requires that
synchronization checkpoint to independently reach the same Founder-approved,
verified-equal commit-and-push status this entry records for `d4b8ca5`. Phase 5 remains
complete, committed, and pushed at
`49b8f743b2e4db967670df35cbb11d2a4ad7f7fa`. SMA-001
(`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`) and FIB-001
(`STRATEGY_PARAMETERS_NOT_APPROVED`) remain fully blocked. Phase 7 was not started.
