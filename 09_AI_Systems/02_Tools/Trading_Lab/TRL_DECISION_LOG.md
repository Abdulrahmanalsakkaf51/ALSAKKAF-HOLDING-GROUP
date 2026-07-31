## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-DECLOG-001 |
| Document Type | Decision Log |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-31 |
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
