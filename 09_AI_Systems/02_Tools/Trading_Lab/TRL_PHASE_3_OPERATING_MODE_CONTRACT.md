# TRL Phase 3 — Operating-Mode State Machine

> **SEVEN MODES DEFINED — THREE AVAILABLE — NO BROKER EXECUTION IN THIS CHECKPOINT**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | Full-vision program, Phase 3 |
| Status | Implemented, tested, and manually rehearsed |
| Depends on | TRL-R2-005 (paper engine, unchanged), Phase 2 contracts (R2-006/007/008, threat model, runbooks) |
| Feeds | Phase 4 (signal intelligence), Phase 5 (MT5 adapter), Phase 9 (live arming) all consult this service; none of them exist yet |

## 1. Purpose and boundary

This checkpoint implements the governed operating-mode state machine that
will control which Trading Lab capabilities are active as later phases add
real MT5 execution, baskets, TradingView intake, private online access, and
live arming. It defines and enforces **modes and safe transitions only**.

It does **not** implement real MT5 order submission, automated live arming,
remote authentication, or TradingView webhooks. Those remain later-phase
work; this checkpoint only reserves their place in the mode schema and
capability matrix so later phases have a single, already-tested gate to
build against.

## 2. The seven modes

| Mode | Available in Phase 3? | Meaning |
|---|---|---|
| `OFF` | Yes | No strategy loop, no forward-paper execution, no MT5 connection, no broker mutation. Safest default. |
| `RESEARCH` | Yes | Historical research and deterministic strategy analysis/reports only. No forward-paper fills, no broker execution. |
| `SYNTHETIC_PAPER` | Yes | The existing R2-005 synthetic demonstration. Synthetic evidence only; no live data, no broker, no credentials, no external network call. |
| `MT5_DEMO_MANUAL` | **No** | Future manually confirmed MT5 demo execution. Fails closed with `MISSING_MT5_ADAPTER`. |
| `MT5_DEMO_AUTOMATED` | **No** | Future governed automated MT5 demo execution. Fails closed with `MISSING_MT5_ADAPTER` and `MISSING_LIVE_ARMING`. |
| `MT5_LIVE_MANUAL` | **No** | Future Founder-confirmed, one-proposal-at-a-time live execution. Fails closed with `MISSING_MT5_ADAPTER`. No Phase 3 code connects to MT5 or submits an order. |
| `MT5_LIVE_AUTOMATED` | **No** | Future armed automated live execution. Fails closed with `MISSING_MT5_ADAPTER` and `MISSING_LIVE_ARMING`. Never activates merely because a stored value says so — see Section 6. |

**All four MT5 modes are represented in the schema, the capability matrix,
the CLI, and the dashboard — and are unavailable in this checkpoint.** No
software path in this checkpoint can make one of them the current mode.

## 3. Governed capability matrix

Sixteen capabilities are governed: `historical_research`,
`strategy_evaluation`, `synthetic_evidence`, `forward_paper_fills`,
`live_market_data_read`, `mt5_read_only_access`, `mt5_order_check`,
`mt5_order_send`, `manual_broker_execution`, `automated_broker_execution`,
`basket_execution`, `tradingview_proposal_intake`, `private_remote_access`,
`live_arming`, `emergency_controls`, `report_export`.

| Mode | Capabilities granted |
|---|---|
| `OFF` | *(none)* |
| `RESEARCH` | `historical_research`, `strategy_evaluation`, `report_export`, `mt5_read_only_access`, `live_market_data_read` |
| `SYNTHETIC_PAPER` | `synthetic_evidence`, `forward_paper_fills`, `report_export` |
| `MT5_DEMO_MANUAL` (future) | `mt5_read_only_access`, `mt5_order_check`, `mt5_order_send`, `manual_broker_execution`, `emergency_controls`, `report_export` |
| `MT5_DEMO_AUTOMATED` (future) | above + `automated_broker_execution`, `basket_execution` |
| `MT5_LIVE_MANUAL` (future) | same as `MT5_DEMO_MANUAL`'s set |
| `MT5_LIVE_AUTOMATED` (future) | above + `automated_broker_execution`, `basket_execution`, `live_arming` |

`tradingview_proposal_intake` and `private_remote_access` are Phase 7/8
concepts: **no mode in this checkpoint grants either, under any
circumstance.** A capability not explicitly listed for a mode is denied —
there is no default-allow path anywhere in the matrix.

Because the four MT5 rows can never actually become the current mode in
this checkpoint, their capability grants are never actually exercised —
they exist so Phase 5/6/9 can extend the *same* matrix instead of building
a second one.

### 3.1 Amendment (TRL-R2-009, contract-authoring checkpoint): `manual_basket_execution`

*Added while authoring `TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md`
(Phase 6 contract-authoring checkpoint). This is the one narrow,
Founder-approved capability change that contract requires; every other
rule in this document is unchanged. No code implements this amendment yet
— see the R2-009 contract Section 6 for the full rationale.*

A seventeenth governed capability is added: `manual_basket_execution`.

**The existing, broader `basket_execution` capability is not widened by
this amendment and remains reserved exactly as before** — granted only to
the still-future, still-unavailable `MT5_DEMO_AUTOMATED` and
`MT5_LIVE_AUTOMATED` rows. `manual_basket_execution` is granted **only**
to `MT5_DEMO_MANUAL`:

| Mode | Capabilities granted (amended) |
|---|---|
| `MT5_DEMO_MANUAL` (available) | `mt5_read_only_access`, `mt5_order_check`, `mt5_order_send`, `manual_broker_execution`, `manual_basket_execution`, `emergency_controls`, `report_export` |

No other mode's row changes: `OFF`, `RESEARCH`, `SYNTHETIC_PAPER`,
`MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`, and `MT5_LIVE_AUTOMATED` are not
granted `manual_basket_execution` under any circumstance unless a later,
separately Founder-approved contract changes that decision.

`manual_basket_execution` is, by definition and by every safeguard this
document and `TRL_R2_007_MT5_EXECUTION_CONTRACT.md` already establish for
`MT5_DEMO_MANUAL`: manual (every basket child send still requires its own
fresh local operator confirmation, per the R2-009 contract Section 13),
demo-only (rejects a live account exactly as every other `MT5_DEMO_MANUAL`
action already does), locally confirmed, non-automated, non-live, subject
to every existing Phase 5 MT5 safeguard (Section 3/4/5–8 of R2-007), and
additionally subject to every rule in
`TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md`. Granting this
capability to `MT5_DEMO_MANUAL` does not, by itself, activate, arm, or
otherwise change the availability of `MT5_DEMO_AUTOMATED`,
`MT5_LIVE_MANUAL`, or `MT5_LIVE_AUTOMATED` — Section 2's availability
table, Section 4's transition matrix, and Section 6's startup-safety
downgrade for those three modes are all unchanged by this amendment.

### 3.2 Amendment (TRL-R2-010, contract-authoring checkpoint): `market_intelligence_research`

*Added while authoring `TRL_R2_010_MARKET_INTELLIGENCE_V0_CONTRACT.md`
(Market Intelligence V0, product name "TRL CORTEX V0" — an informational
"Phase 6A" checkpoint, not part of the 0–14 phase sequence and not Phase 7).
This is the one narrow, Founder-approved capability change that contract
requires; every other rule in this document, including the 3.1 amendment
above, is unchanged. No code implements this amendment yet — see the
R2-010 contract Section 5.1/5.2 for the full rationale.*

An eighteenth governed capability is added: `market_intelligence_research`.
It is a read/analysis-only research capability: it grants no
`order_check`, `order_send`, `manual_broker_execution`,
`manual_basket_execution`, `basket_execution`, live execution, automated
execution, or execution handoff of any kind — it gates only Market
Intelligence record creation (snapshot analysis, evidence/opportunity/
decision/lattice generation, basket-preview generation, and outcome-
telemetry recording), never anything Phase 5/6 recognizes as broker
authority.

`market_intelligence_research` is granted to `RESEARCH`, `SYNTHETIC_PAPER`,
and `MT5_DEMO_MANUAL`:

| Mode | `market_intelligence_research` granted? |
|---|---|
| `OFF` | No |
| `RESEARCH` | **Yes** |
| `SYNTHETIC_PAPER` | **Yes** |
| `MT5_DEMO_MANUAL` (available) | **Yes** |
| `MT5_DEMO_AUTOMATED` (future) | No |
| `MT5_LIVE_MANUAL` (future) | No |
| `MT5_LIVE_AUTOMATED` (future) | No |

It is granted to `MT5_DEMO_MANUAL` because research-only analysis running
alongside a demo-manual execution mode creates no execution risk by
itself — the capability grants no order/basket authority of any kind, so
there is no reason to withhold it there the way the three still-unavailable
MT5 rows are withheld from every other capability by virtue of remaining
unavailable. It is not granted to `OFF` (which grants nothing, by design)
or to `MT5_DEMO_AUTOMATED`/`MT5_LIVE_MANUAL`/`MT5_LIVE_AUTOMATED` (which
remain fully unavailable, unchanged by this amendment). Granting this
capability to `MT5_DEMO_MANUAL` does not, by itself, activate, arm, or
otherwise change the availability of any of the three still-unavailable
modes — Section 2's availability table, Section 4's transition matrix, and
Section 6's startup-safety downgrade for those three modes are all
unchanged by this amendment, exactly as the 3.1 amendment already
established for `manual_basket_execution`.

Read-only Market Intelligence operations (status, list, inspect, journal
inspection, and every read-only HTTP route defined in the R2-010 contract)
require no capability grant and remain available in every mode, including
`OFF` — matching this document's own existing convention that pure-read
commands like `show-mode`/`list-modes` never require a capability.

## 4. Exact transition matrix

```
OFF              -> RESEARCH, SYNTHETIC_PAPER
RESEARCH         -> OFF, SYNTHETIC_PAPER
SYNTHETIC_PAPER  -> OFF, RESEARCH
MT5_DEMO_MANUAL, MT5_DEMO_AUTOMATED,
MT5_LIVE_MANUAL, MT5_LIVE_AUTOMATED  -> (no transitions defined; unreachable)
```

`OFF` is always reachable from every mode this checkpoint can actually be
in. A request for an MT5 mode is rejected during the *availability* check,
before the transition matrix is even consulted — the matrix has no rows
for MT5 modes at all, source or destination.

## 5. Transition rules (fail-closed)

- **Unknown mode name** → rejected with `UNKNOWN_MODE`; current mode unchanged.
- **Unavailable destination** → rejected with `MISSING_MT5_ADAPTER` and/or `MISSING_LIVE_ARMING` (or `MODE_UNAVAILABLE`); current mode unchanged. The full prerequisite-check list is returned, not just the primary reason.
- **Not in the transition matrix for the current mode** → rejected with `INVALID_TRANSITION` (this also makes a same-mode "transition" to the mode you're already in deterministically rejected, rather than a silent no-op).
- **Subsystem activation raises** → rolled back with `SUBSYSTEM_ACTIVATION_FAILED`; current mode unchanged; no partial activation.
- **Persistence of the completed transition fails** → rolled back with `PERSISTENCE_FAILED`; current mode unchanged. This is a harder gate than ordinary audit logging (Section 7): a mode change is only considered real once it is durably persisted.
- **Non-local-operator channel** (anything other than `LOCAL_OPERATOR`, `STARTUP`, or `SYSTEM`) → rejected immediately with `MODE_CHANGE_REQUIRES_LOCAL_OPERATOR`, before any other check runs. There is no HTTP route that could supply an unpermitted channel — this is defense in depth.
- Every request — accepted or rejected — is atomic from the caller's perspective: `request_transition()` returns a single `TransitionResult` with the exact outcome; there is no intermediate state a concurrent reader could observe.

## 6. Startup safety

Startup resolves the mode in this order, matching the mandated sequence:

1. Load and validate configuration (existing CLI argument parsing, unchanged).
2. Load and validate the persisted mode-state document.
3. Resolve corruption or an unsupported/unsafe state to `OFF`.
4. Load capability availability (static per this checkpoint).
5. Refuse unavailable modes (enforced the same way at startup and at runtime — Section 5's rules apply uniformly).
6. Construct only the subsystems the resolved safe mode allows (Section 8).
7. Start the loopback server.
8. Expose mode status read-only through `/api/mode-status` and the dashboard.
9. Record the startup resolution as an audit event (`MODE_STATE_LOADED`, `MODE_STATE_DEFAULTED`, `MODE_STATE_CORRUPTION_RECOVERED`, or `MODE_STARTUP_SAFE_DOWNGRADE`).

**The specific guarantee the program asked for:** if the persisted document
somehow claims the last completed mode was any of the four MT5 modes
(corrupted, hand-edited, or produced by a future bug), startup replays the
event chain, notices the resolved mode is an MT5 mode, and forces `OFF`
instead — recording a `MODE_STARTUP_SAFE_DOWNGRADE` audit event with reason
`STARTUP_LIVE_AUTOMATION_FORBIDDEN`. This was exercised directly in testing
(a forged `MODE_TRANSITION_COMPLETED` event targeting
`MT5_LIVE_AUTOMATED` was persisted, then a fresh `ModeService` loaded it and
came up in `OFF`) — see Section 11.

No external network connection occurs merely from loading mode state; the
store is a local JSON file only.

## 7. Persistence and audit design

One authoritative service (`trading_lab_app/mode_service.py`) owns every
mode decision — no other module infers permission from a mode-name string
or duplicates transition logic. It is event-sourced, mirroring R2-005's
proven paper-timeline architecture:

- Every decision is a `TRL_MODE_TRANSITION_EVENT.v1` event in an
  append-only, hash-chained log (`TRL_MODE_TRANSITION_LOG.v1`),
  each event carrying `schema_version`, a content-derived `event_id`,
  `event_type` (one of the ten governed types below), `occurred_at_utc`,
  a contiguous `append_sequence`, a bounded sanitized `payload`,
  `payload_sha256`, `previous_event_hash`, and `current_event_hash`.
- **`current_mode` is never stored as an independently editable field.** It
  is always derived by replaying the validated event chain and taking the
  `resulting_mode` of the last `MODE_TRANSITION_COMPLETED` or
  `MODE_STARTUP_SAFE_DOWNGRADE` event. A hand-edit of a raw mode value in
  the file does nothing; only a fully valid, hash-chained event sequence
  can move the derived mode, and even that is subject to the Section 6
  MT5-downgrade check on every load.
- Storage document: `TRL_OPERATING_MODE_STORE.v1`, containing
  `schema_version`, `storage_id`, `session_started_at_utc`, and the
  embedded event log — atomic temp-file-plus-`os.replace` write (identical
  technique to the paper store), strict UTF-8, no BOM, bounded byte/event
  counts, corruption fails closed.
- Ten governed audit event types: `MODE_STATE_LOADED`, `MODE_STATE_DEFAULTED`,
  `MODE_STATE_CORRUPTION_RECOVERED`, `MODE_TRANSITION_REQUESTED`,
  `MODE_TRANSITION_ACCEPTED`, `MODE_TRANSITION_REJECTED`,
  `MODE_TRANSITION_COMPLETED`, `MODE_TRANSITION_ROLLED_BACK`,
  `MODE_CAPABILITY_UNAVAILABLE`, `MODE_STARTUP_SAFE_DOWNGRADE`.
- Twelve governed rejection reason codes: `UNKNOWN_MODE`, `MODE_UNAVAILABLE`,
  `MISSING_MT5_ADAPTER`, `MISSING_LIVE_ARMING`, `MISSING_PRIVATE_AUTH`,
  `INVALID_TRANSITION`, `PERSISTED_STATE_INVALID`, `PERSISTENCE_FAILED`,
  `SUBSYSTEM_ACTIVATION_FAILED`, `STARTUP_LIVE_AUTOMATION_FORBIDDEN`,
  `CAPABILITY_DENIED`, `MODE_CHANGE_REQUIRES_LOCAL_OPERATOR`.
- No credential, secret, or connection detail is ever a governed payload
  field; every event's payload is bounded and sanitized before hashing.
- Default location: `%LOCALAPPDATA%\ALSAKKAF\TradingLab\operating-mode-state-v1.json`.
  A caller that does not explicitly supply a store gets a **side-effect-free
  in-memory store instead** (`in_memory_mode_service()`), mirroring
  `DisabledPaperService`'s no-filesystem-by-default philosophy — this keeps
  every existing test that constructs a server without explicitly wiring a
  mode service from touching the real filesystem.

## 8. Integration with the existing paper engine — single authority path

*Revised after a Founder correction: the first implementation preserved
`--enable-forward-paper-engine`/`--enable-forward-paper-demo` as direct
construction branches that never consulted `ModeService`, so the reported
mode and the actually active paper service could disagree, and a CLI flag
could bypass the authoritative capability state machine entirely. That
design is removed. There is now exactly one decision path, with no
exception:*

```
ModeService resolved mode -> capability check -> paper-service construction
```

`app.py`'s `_paper_service_for_mode(current_mode)` is the **only** function
in the application that constructs a paper service, and it is called from
exactly two places, both consuming a `ModeService`-resolved mode: once as
`ModeService`'s own `subsystem_builder` (so a transition validates that
construction succeeds *before* it is allowed to commit — Section 5), and
once more at startup, after the mode is resolved, to build the object
actually wired into the running server. Required mappings:

- `OFF` → `DisabledPaperService` (no store constructed, matching R2-005).
- `RESEARCH` → `DisabledPaperService` (research capabilities do not include forward-paper fills in this checkpoint).
- `SYNTHETIC_PAPER` → `build_synthetic_demonstration_service()`, the existing R2-005 in-memory synthetic fixture — same function, same behavior, same visible `SYNTHETIC DEMONSTRATION` labeling.
- Any MT5 mode → `_paper_service_for_mode` raises `ModeSubsystemConfigurationError` (defensive; unreachable in practice because `is_available()` rejects an MT5-mode request before the subsystem builder is ever called).

### 8.1 Consistency invariant

**The actual constructed subsystem set must exactly equal the authoritative
capability set of the resolved current mode.** `_validate_subsystem_consistency(mode, paper_service)`
enforces this immediately before the server binds: `OFF`/`RESEARCH` must have
a disabled, non-enabled `DisabledPaperService`; `SYNTHETIC_PAPER` must have
an enabled `ForwardPaperService` with `is_synthetic_demonstration = True`;
anything else fails closed with reason code
`MODE_SUBSYSTEM_CONFIGURATION_MISMATCH` and the server does not start. Because
both call sites for `_paper_service_for_mode` are the same function fed the
same resolved mode, `/api/mode-status` and `/api/paper-account` can never
disagree about whether synthetic paper is active — this is enforced by
construction, not by a separate reconciliation check.

### 8.2 `--enable-forward-paper-demo` (deprecated, routes through ModeService)

Requests a transition to `SYNTHETIC_PAPER` through
`ModeService.request_transition(..., actor_channel="LOCAL_OPERATOR")` —
the identical path `mode_cli.py request-mode SYNTHETIC_PAPER` uses. It
creates the normal `MODE_TRANSITION_REQUESTED`/`ACCEPTED`/`COMPLETED` audit
events (actor recorded as `LEGACY_CLI_FLAG:--enable-forward-paper-demo`),
passes the same transition and capability validation, persists atomically,
and fails closed (exits with status `2`, server never starts) if the
transition does not return `ACCEPTED`. The synthetic demonstration service
is constructed only *after* `ModeService` confirms the resolved mode is
`SYNTHETIC_PAPER`. If the persisted mode is already `SYNTHETIC_PAPER`, no
transition is requested (a same-mode request would otherwise be rejected as
`INVALID_TRANSITION`, which must not make an already-correct startup fail);
the flag prints a deprecation notice pointing at `mode_cli.py` either way.
**It can never activate synthetic paper while the authoritative mode remains
`OFF` or `RESEARCH`** — there is no code path left that skips the transition.

### 8.3 `--enable-forward-paper-engine` (deprecated, fails closed)

None of the seven Phase 3 modes authorizes the old unrestricted
forward-paper engine. The flag is retained only as a recognized argument
that fails closed **before any other setup work** — before
`MT5ReadOnlyConfiguration`, before `ModeService` is even constructed —
printing reason code `LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE` and exiting
with status `2`. No mode-state file is touched, no paper store is
constructed, no server binds, and no external connection occurs. This flag
is never mapped to `RESEARCH` or `SYNTHETIC_PAPER`, and it does not add an
eighth mode — both are explicitly prohibited without separate Founder
approval.

## 9. CLI (local operator only)

`python -B -W error -m trading_lab_app.mode_cli <command>`:

| Command | Effect |
|---|---|
| `show-mode` | Full `mode_status_document()` — current/previous mode, available/unavailable modes with reasons, capability matrix, last transition, diagnostics. |
| `list-modes` | All seven modes plus availability. |
| `explain-mode <mode>` | Description, availability, granted capabilities, prerequisite results, reachable-from/reachable-to. |
| `request-mode <mode> [--reason TEXT]` | The only mutation path. Always uses `actor_channel="LOCAL_OPERATOR"`. |
| `transition-history [--limit N]` | The raw audit event log. |

There is **no** HTTP mutation route for mode — `/api/mode-status` is
GET/HEAD only, returning `405 Allow: GET, HEAD` for every other method,
exactly like every other route in this application. The mode service's own
`actor_channel` gate additionally refuses any channel other than
`LOCAL_OPERATOR`/`STARTUP`/`SYSTEM` regardless of caller, as defense in
depth against a future wiring mistake.

## 10. Dashboard behavior

A new "Operating mode" section (`#operating-mode`) sits directly after
Overview. It shows: the current mode as a badge (also mirrored in the top
bar), whether broker execution / automated trading / live arming / private
remote access are available (always `UNAVAILABLE` in this checkpoint), the
list of currently available modes, the list of unavailable modes with their
exact reasons, the full capability matrix for the current mode, the last
transition event, and a startup-recovery warning banner when
`startup_diagnostic_code` is not `OK`.

Wording is deliberately literal: *"MT5_DEMO_MANUAL, MT5_DEMO_AUTOMATED,
MT5_LIVE_MANUAL and MT5_LIVE_AUTOMATED are represented in this schema but
cannot be entered — no MT5 execution adapter or live-arming capability
exists yet."* Nothing on the page implies unavailable broker execution
exists. In `SYNTHETIC_PAPER`, the existing `SYNTHETIC DEMONSTRATION` warning
(R2-005) remains exactly as before — this checkpoint did not touch that
fixture or its labeling. In `OFF`/`RESEARCH`, the paper desk continues to
show its existing disabled-state message, because the paper service
constructed for those modes is `DisabledPaperService` (Section 8) — no new
code path was needed to keep synthetic values from appearing "active."

## 11. Test and rehearsal evidence

**Automated:** `test_operating_mode.py` (51 tests: 36 original + 15 added for
the single-authority correction) plus regression coverage via the full
suite. Both discovery runs under `python -B -W error`:

| Run | Tests | Result |
|---|---|---|
| 1 | 447 | 0 failures, 0 errors |
| 2 | 447 | 0 failures, 0 errors |

(396 pre-existing R2-005/R2-001–004 tests, unchanged and unweakened, plus 51
operating-mode tests.) The 15-test `SingleAuthorityTests` class specifically
covers: `OFF`/`RESEARCH` cannot construct an active paper service;
`SYNTHETIC_PAPER` constructs only the synthetic demonstration service; the
deprecated demo flag routes through `ModeService`, results in
`current_mode == SYNTHETIC_PAPER`, creates the normal transition audit
events, and cannot bypass a rejected transition (verified by forcing
`request_transition` to return `REJECTED` and confirming `create_server` is
never called); the deprecated engine flag fails closed before any setup
work and leaves no mode-state file; `/api/mode-status` and
`/api/paper-account` agreeing across all three available modes over real
HTTP; direct helper calls rejecting disallowed constructions; a deliberate
mismatch raising `MODE_SUBSYSTEM_CONFIGURATION_MISMATCH`; the existing
synthetic-demonstration fixture remaining deterministic; exactly seven modes
existing; and no HTTP mode-mutation route existing.

Original 36-test coverage (unchanged) includes: all seven modes validating,
unknown-mode rejection, default-startup-is-`OFF`, corrupted-state recovery,
per-mode capability grants (including that `OFF` grants nothing and the two
Phase 7/8 capabilities are never granted anywhere), all four MT5 modes
confirmed represented-but-unavailable with their exact reason codes,
restart-cannot-restore-live-automated (tested by forging a persisted
`MT5_LIVE_AUTOMATED` completion and confirming a fresh load resolves to
`OFF`) for all four MT5 modes individually, unavailable/failed-persistence/
failed-subsystem-activation all leaving the mode unchanged, the exact
transition matrix, repeated-identical-request determinism, the
actor-channel gate, JSON-serializable deterministic audit events, no secret
fields in the persisted state, HTTP read-only status reflecting server
authority, the absence of any HTTP mutation route, the synthetic-mode
warning and non-active-values-in-OFF/RESEARCH dashboard guarantees, no
`MetaTrader5` import anywhere in the new modules, and no outbound-network
import surface.

**Manual loopback rehearsal**, performed against the real application and
real port 8765 (not mocks):

| Step | Action | Result |
|---|---|---|
| 1–2 | Start in `OFF`; check `/api/mode-status` | `current_mode: OFF`, `broker_execution_available: false` |
| 3–4 | `mode_cli.py request-mode RESEARCH`; restart; check status + paper API | `current_mode: RESEARCH`; `/api/paper-account` → `enabled: false` |
| 5–6 | `mode_cli.py request-mode SYNTHETIC_PAPER`; restart; check status + paper API | `current_mode: SYNTHETIC_PAPER`; paper `enabled: true`, `synthetic_demonstration_values: true`, `completed_paper_trade_count: 2` |
| 7–8 | `mode_cli.py request-mode MT5_DEMO_MANUAL` | Rejected: `MISSING_MT5_ADAPTER`; mode unchanged |
| 9–10 | `mode_cli.py request-mode MT5_LIVE_AUTOMATED` | Rejected: both `MISSING_MT5_ADAPTER` and `MISSING_LIVE_ARMING` listed; mode unchanged |
| 11 | `mode_cli.py request-mode OFF` | Accepted; `current_mode: OFF` |
| 12–14 | `STOP_TRADING_LAB.ps1`; port/process check | No listener on 8765 (only `TimeWait` remnants); no `python.exe` process |

**Second rehearsal, after the single-authority correction**, again against
the real application on real port 8765:

| Step | Action | Result |
|---|---|---|
| 1 | Start normally (`START_TRADING_LAB_DISABLED.ps1`) | `current_mode: OFF`, paper `enabled: false` |
| 2 | Stop | Clean |
| 3–6 | Launch with `--enable-forward-paper-demo` | `current_mode: SYNTHETIC_PAPER`; paper `enabled: true`, `synthetic_demonstration_values: true`; mode/paper agreement confirmed directly |
| 7 | Stop | Port confirmed clear (`TimeWait` only) |
| 8–9 | Launch with `--enable-forward-paper-engine` | Failed closed synchronously with `LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE`, exit status `2` |
| 10 | Port/process check | No listener, no `python.exe` process; persisted mode confirmed unchanged (still `SYNTHETIC_PAPER` from step 6, not mutated by the failed attempt) |
| 11 | `mode_cli.py request-mode OFF` | Accepted; `current_mode: OFF` |
| 12 | Final port/process check | No listener (`TimeWait` only), no `python.exe` process |

## 12. Known limitations

- **Mode changes take effect on next start, not live.** The running server
  resolves its mode once at startup and does not poll the mode-state file.
  A `mode_cli.py request-mode` call while the dashboard is already running
  updates the durable file; the running process's `/api/mode-status` keeps
  reporting the mode it started with until restarted. This matches the
  program's own startup-safety framing (mode resolution is a startup-time
  concern) and avoids the complexity/risk of hot-swapping subsystems inside
  a live server for this checkpoint.
- **Legacy paper flags no longer bypass the mode service** (this was
  flagged as unacceptable in Founder review and corrected — see Section 8).
  `--enable-forward-paper-demo` now routes through `ModeService` and
  `--enable-forward-paper-engine` always fails closed; there is no longer a
  known limitation here.
- **No live-polling, multi-process coordination.** If two processes both
  hold a `LocalModeStateStore` open and both attempt a transition
  concurrently, the second writer's atomic replace wins; there is no
  cross-process lock. This is acceptable for a single local operator tool
  and is the same concurrency model R2-005's paper store already uses.
- Phases 4–10 (signal intelligence, MT5 execution, baskets, TradingView
  intake, private online access, live arming, reconciliation) are not
  implemented. This checkpoint only reserves their place in the capability
  matrix and mode schema.

## 13. Explicit statement

**MT5_DEMO_MANUAL, MT5_DEMO_AUTOMATED, MT5_LIVE_MANUAL, and
MT5_LIVE_AUTOMATED are fully represented in the mode schema, capability
matrix, CLI, and dashboard of this checkpoint, and are unavailable.** No
code path in Phase 3 can make any of them the current mode, connect to
MT5, or submit a broker order.
