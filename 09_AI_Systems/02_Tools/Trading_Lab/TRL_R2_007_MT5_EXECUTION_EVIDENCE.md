# TRL-R2-007 MT5 Execution Adapter (Phase 5) — Implementation and Evidence

> **DEMO ONLY — LIVE EXECUTION DISABLED — MANUAL CONFIRMATION REQUIRED FOR EVERY ORDER — NO REAL ORDER WAS EVER SUBMITTED**

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-007-MT5-EXECUTION-EVIDENCE-001 |
| Document Type | Implementation and Evidence Record |
| Status | Implemented, tested, manually rehearsed, Founder-corrected (cross-process execution locking, Section 20); awaiting Founder review and commit approval |
| Version | 2.0 (supersedes v1.0's cross-process concurrency claims — see Section 20) |
| Date | 2026-08-01 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | Phase 5 (`TRL_R2_007_MT5_EXECUTION_CONTRACT.md`) |
| Depends on | TRL-R2-006 (signal proposals, unchanged), TRL-R2-003 (`mt5_connector.py` read-only pattern, unchanged), Phase 3 (`ModeService`, extended) |
| Feeds | Phase 6 (basket execution), Phase 9 (live-automation arming), Phase 10 (reconciliation) — none started |

## 1. Scope: the demo-manual slice of R2-007

`TRL_R2_007_MT5_EXECUTION_CONTRACT.md` describes the full multi-phase end state of the MT5
execution adapter, including basket children (Section 5.6), live modes, arming tokens, and
automatic reconciliation. `TRL_FULL_VISION_MASTER_PROGRAM.md`'s phase table maps each of those
pieces to its own later phase (baskets → Phase 6, live-automation arming → Phase 9, operational
reconciliation → Phase 10). Phase 5 implements exactly the `MT5_DEMO_MANUAL` slice: one order per
execution intent, no basket, no automated submission, mandatory local manual confirmation before
every `order_send`, and no automatic reconciliation retry — an uncertain result freezes the intent
and is deferred to the phase that implements reconciliation, matching the Phase 5 kickoff
instructions verbatim.

Two deliberate narrowings versus the full contract, both **more conservative**, not looser:

- **Single-attempt-per-intent.** The full contract's repriced-retry-under-the-same-intent
  machinery (Section 5.4/6, multiple `execution_attempt`s per intent) is not implemented. A
  failed `order_check` makes its intent terminal (`REJECTED`); a materially different situation
  requires a new proposal, which resolves to a new lookup key and a new intent.
- **Entry-zone → order-type mapping.** The kickoff instructions require failing closed rather
  than inventing a general entry-zone-to-price mapping. Phase 5 supports only the one
  unambiguous case: a proposal whose `entry_zone_lower` equals `entry_zone_upper` (a single exact
  price, not a range) maps to a pending `BUY_LIMIT`/`SELL_LIMIT` order at that price. A genuine
  range, or a price the market has already crossed, fails closed with a distinct reason code
  (`ENTRY_ZONE_RANGE_MAPPING_NOT_APPROVED` / `ENTRY_PRICE_ALREADY_CROSSED_MAPPING_NOT_APPROVED`).

## 2. Adapter architecture — `mt5_execution_adapter.py`

Three tiers, mirroring `mt5_connector.py`'s house style (lazy import, allowlisted provider
methods, single serializing lock, strict normalization):

| Tier | Class | Behavior |
|---|---|---|
| Disabled | `DisabledExecutionAdapter` | Default. Never imports `MetaTrader5`. Every operation returns a stable `ADAPTER_DISABLED` failure document. |
| Fake | `FakeExecutionAdapter` | Deterministic, in-memory, scriptable (`queue_check_result`, `queue_send_result`, `set_symbol`). No network, no terminal. Used by every automated test. |
| Real | `RealMT5ExecutionAdapter` | Imports the optional `MetaTrader5` package lazily, only inside a method call — never at import time or construction time. Every method independently `initialize()`s and `shutdown()`s within one process-wide lock (`PROVIDER_METHOD_ALLOWLIST` gates every provider call), so no broker session is ever held open between calls. |

The adapter never makes a governance decision (account/symbol/risk approval) — it only talks to
the broker and returns strictly normalized documents (`terminal_status`, `account_status`,
`symbol_status`, `order_check`, `order_send`). `mt5_execution_service.py` is the sole authority
that decides whether a normalized document satisfies Phase 5's preflight requirements.

`order_send` normalization never treats a non-null response object, or a non-`DONE`-family
retcode, as proof of success (`_normalize_send_response`); a `FILLED` result additionally requires
a present order ticket, deal ticket, and positive fill volume, or it is reclassified `MALFORMED`.

## 3. ModeService integration

`MT5_DEMO_MANUAL` was already represented in `mode_service.py` (added in Phase 3) but marked
unavailable (`MISSING_MT5_ADAPTER`). Phase 5 changes exactly three things in `mode_service.py`:

1. `_AVAILABLE_MODES` now includes `MT5_DEMO_MANUAL`; its `_UNAVAILABLE_REASONS` entry is removed.
2. `_ALLOWED_TRANSITIONS["OFF"]` gains `MT5_DEMO_MANUAL`, and `MT5_DEMO_MANUAL` is reachable only
   back to `OFF` — entering or leaving it is always one deliberate, local-operator step.
3. A new `AUTOMATED_OR_LIVE_MT5_MODES` tuple (`MT5_DEMO_AUTOMATED`, `MT5_LIVE_MANUAL`,
   `MT5_LIVE_AUTOMATED`) replaces `MT5_MODES` in the startup safe-downgrade check. Unlike those
   three, `MT5_DEMO_MANUAL` legitimately survives a process restart: every `order_send` it permits
   still requires a fresh, explicit local confirmation for that specific order, so persisting the
   *mode* across a restart carries no unattended-execution risk, and the CLI-driven workflow
   (every command is its own process) depends on it. The capability matrix, the mode's
   description text, and every other Phase 3 mechanism are unchanged.

No capability was added or renamed: `MT5_DEMO_MANUAL`'s capability grant
(`mt5_read_only_access`, `mt5_order_check`, `mt5_order_send`, `manual_broker_execution`,
`emergency_controls`, `report_export`) was already defined in Phase 3's `_CAPABILITY_MATRIX` and
is unchanged. `mt5_execution_service.py` calls `ModeService.has_capability(...)` and
`ModeService.current_mode` before every action; it never re-derives authorization.

`app.py` gained `_execution_adapter_for_mode` / `_execution_service_preflight_for_mode` /
`_execution_service_for_mode` / `_validate_execution_subsystem_consistency`, following the exact
pattern `_paper_service_for_mode` / `_signal_service_for_mode` already established: a
side-effect-free preflight variant (used as part of `ModeService`'s `subsystem_builder`, so a
transition validates construction before committing) and a real runtime variant (constructed only
after a mode is resolved). Constructing `RealMT5ExecutionAdapter` is itself safe and
side-effect-free — mirroring `MarketDataService`'s `LocalMT5ReadOnlyConnector` — so it is
constructed whenever the resolved mode is `MT5_DEMO_MANUAL`; every other mode gets the disabled
tier. `signal_proposal_generation` is not part of `MT5_DEMO_MANUAL`'s capability grant, so the
signal service resolves to `DisabledSignalService` in that mode — an operator supplies an
already-generated governed proposal (from a prior `RESEARCH`/`SYNTHETIC_PAPER` session) rather
than generating one while execution capabilities are active.

## 4. Dependency/import boundary

`MetaTrader5` is never imported from `mode_service.py`, `app.py`, `server.py`, `service.py`,
dashboard modules, or any Phase 4 signal module. It is imported (via `importlib.import_module`,
never a top-level `import` statement) only inside `RealMT5ExecutionAdapter`'s methods, and only
when a real broker-facing call is actually being made — never at module import or object
construction time. `test_mt5_execution_adapter.py::ImportBoundaryTests` asserts the source file
contains no `import MetaTrader5` statement and that constructing the real adapter never calls
`importlib.import_module`.

## 5. Order-intent schema and identity — `mt5_execution_data.py`

`TRL_MT5_ORDER_INTENT.v1` (28 fields: schema version, order-intent ID, proposal linkage,
timestamps, operating mode, hashed account fingerprint, instrument, side, order type, quantity,
entry price, stop, targets/allocations (informational only — Phase 5 sends only the initial order
with its protective stop; TP2–TP4 position-reduction chains are out of scope, matching the
kickoff's "implement only [a single governed initial order]" instruction), spread/deviation
limits, time-in-force, fill policy, strategy linkage, risk-policy hash, idempotency key, manual
confirmation flag, execution status, rejection reasons, and a canonical content hash). No
credential-shaped field exists anywhere in the schema (`test_mt5_execution_data.py` asserts this
directly).

Execution intent identity is a Phase 5 slice of contract Section 5.1/5.3 (basket/live fields
dropped): a deterministic **lookup key** (`proposal_id`, hashed account fingerprint,
broker-native instrument, side, quantity, strategy linkage, risk-policy hash, operating mode, and
a stable `"LOCAL_OPERATOR"` authorization identity — no nonce, no price) is computed first and
searched in the durable journal; only a genuine miss generates a fresh nonce and a new
`order_intent_id`. A match reuses the existing intent unchanged, including its already-terminal
outcome if it has one — no `order_check`/`order_send` call is made merely because a build request
arrived again. The intent's canonical hash is computed over its immutable identity fields only
(excluding `execution_status`/`rejection_reasons`), so the hash stays valid across the intent's
whole lifecycle as its status changes.

## 6. Proposal revalidation chain

Before any order intent is created, `ExecutionService.build_order_intent` independently
re-validates, in order: full schema/hash (`signal_data.validate_signal_proposal`, with a
dedicated check distinguishing a hash mismatch from a general schema defect), executable side
(rejects `BLOCKED`/`HOLD`/`WAIT`), expiry, strategy registration/approval state
(`signal_strategy_registry.executable_status`, id-only — the proposal's declared version is
compared against the registry's current version as its own separate `STRATEGY_VERSION_MISMATCH`
gate, so a version mismatch is never folded into a generic "not registered" code), the Phase 5
execution-geometry allowlist (Section 7), an optional configured risk-policy-hash match, Role
3/Role 5 quantity agreement, instrument allowlist membership, and the entry-zone mapping rule
(Section 1). Every rejection is journaled (`PROPOSAL_REJECTED`) before raising; nothing reaches the
adapter until every check passes.

## 7. SMA-001 and FIB-001 blockers — both independently enforced here

- **FIB-001**: `signal_strategy_registry.executable_status("FIB-001")` already returns
  `(False, "STRATEGY_PARAMETERS_NOT_APPROVED")` — its registry record's `approval_status` is
  `APPROVAL_PENDING`. Phase 5 relies on this directly.
- **SMA-001**: the registry alone does **not** block SMA-001 (`approval_status` is
  `EXPERIMENTAL_RESEARCH_ONLY`, `enabled=True`) — the pipeline blocks it only inside Role 3's
  crossing-detection logic (`signal_role3_strategy.REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`),
  which never lets an executable BUY/SELL SMA-001 proposal leave the pipeline. Because a
  hand-built, schema-valid proposal object could still claim `strategy_id="SMA-001"` with an
  executable side without going through the pipeline, `mt5_execution_service.py` adds its own
  explicit, independent gate: `EXECUTION_GEOMETRY_APPROVED_STRATEGIES` — a local, empty
  `frozenset()` — with a `strategy_id not in EXECUTION_GEOMETRY_APPROVED_STRATEGIES` check that
  raises the identical `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED` reason code independently of
  Role 3. Neither blocker was touched, resolved, or bypassed; both are still enforced *before*
  Section 6's proposal chain reaches the adapter, verified directly by both the automated test
  suite (`SmaFibBlockerTests`) and the manual CLI rehearsal (Section 15).

## 8. Account fingerprint and terminal validation

`AccountFingerprintConfiguration` holds the Founder-approved demo login/company/server (and
optional expected terminal path); `account_fingerprint_from_environment()` reads it from
`TRL_MT5_DEMO_LOGIN` / `TRL_MT5_DEMO_COMPANY` / `TRL_MT5_DEMO_SERVER` /
`TRL_MT5_TERMINAL_PATH` environment variables only — never a committed file, never an HTTP
request — and treats any partial configuration as fully unconfigured (fail closed, never a
partially-trusted fingerprint). No Founder-approved fingerprint has been supplied; this remains an
explicit, reported external blocker (`ACCOUNT_UNAVAILABLE`) rather than something silently
bypassed. `order_check` and `confirm_and_send` each independently re-query the adapter's live
`account_status`/`terminal_status`/`symbol_status`, hash the live login/company/server the same
way (`mt5_execution_data.account_fingerprint_hash` — sha256, raw values never appear in identity
material or in any status document), and compare against the intent's stored hash
(`ACCOUNT_FINGERPRINT_MISMATCH`), the demo/live classification (`ACCOUNT_MODE_MISMATCH`), and
trade-permission flags (`ACCOUNT_TRADE_NOT_ALLOWED`). `account_status_document()` (used by both
the CLI and the read-only HTTP route) strips the raw `login` field entirely, replacing it with a
`login_redacted` value showing only the last two digits.

## 9. Symbol validation and preflight

`order_check` (and, more narrowly, `confirm_and_send`'s repeated pre-send check) independently
re-validates, using only the adapter's live `symbol_status`: availability, visibility, tradeability
(surfacing the adapter's own reason code, e.g. a broker-reported closed market session), mapping
consistency, tick presence and freshness (30s bound), bid/ask validity (`ask > bid > 0`), spread
versus the intent's `maximum_spread`, the entry-zone-already-crossed rule (Section 1), quantity
bounds and step alignment, stop distance versus the broker's stop/freeze level, and fill-policy
availability against the symbol's reported filling modes. Every one of these has a dedicated,
independently exercised failure-path test (`test_mt5_execution_service.py::OrderCheckTests`).

## 10. `order_check` gate

Requires the `mt5_order_check` capability; independently re-validates the whole chain above
before ever calling the adapter; calls `self._adapter.order_check(request)` exactly once
(the request is built entirely from already-validated intent fields — no browser/CLI-supplied
value is trusted); persists `ORDER_CHECK_REQUESTED` before the call and `ORDER_CHECK_RESULT`
after; a `PASSED` outcome moves the intent to `CHECK_PASSED` and never calls `order_send`; any
other outcome (including a malformed response) makes the intent terminally `REJECTED`.

## 11. Manual confirmation gate

`request_confirmation` requires a fresh (≤120s) `CHECK_PASSED` result and computes a
**deterministic** challenge code — `sha256(order_intent_id + ":" + canonical_order_intent_hash)`,
truncated to 8 hex characters — rather than a random one. Because it is a pure function of the
intent's own identity, it needs no separate durable secret store to survive a restart or a
separate CLI process invocation (each CLI command is its own process): any later process can
recompute the exact same code from the same intent. What *is* persisted (in the journal) is the
confirmation *window* (`issued_at_utc`/`expires_at_utc`, 300s) and the intent's
`AWAITING_CONFIRMATION` state. `confirm_and_send` recomputes the expected code, rejects an exact
mismatch (`CONFIRMATION_MISMATCH`), specifically detects and reports a code that matches a
*different* pending intent (`CONFIRMATION_WRONG_INTENT`), rejects an expired window
(`CONFIRMATION_EXPIRED`), and rejects any actor channel other than the literal string
`"LOCAL_OPERATOR"` (`CONFIRMATION_CHANNEL_NOT_LOCAL`) — the HTTP layer has no route that could
even attempt this, but the service itself refuses the channel as defense in depth. No vague
"yes"/"confirm" syntax is accepted anywhere.

## 12. `order_send` gate, idempotency and duplicate protection

Immediately before calling `order_send`, `confirm_and_send` re-checks: no prior send attempt for
this `order_intent_id` exists in the durable journal (`DUPLICATE_SEND_BLOCKED` — this scan, not
any in-memory flag, is the actual duplicate-protection mechanism, so it survives a process
restart), the proposal is still unexpired, the account fingerprint is unchanged, and the symbol
spread is still within limit. `ORDER_SEND_REQUESTED` is persisted *before* the adapter call, so
even a crash immediately afterward leaves a durable record that blocks any further attempt.
`order_send` is called at most once per intent. A `FILLED` result is additionally cross-checked:
the broker's reported filled volume must be positive and not exceed the requested quantity, or the
result is reclassified `FROZEN_PENDING_RECONCILIATION` (`BROKER_RESULT_MISMATCH`) rather than
trusted at face value.

## 13. Uncertain-result handling — no automatic reconciliation

Per the kickoff instructions, Phase 5 does **not** implement Section 7's reconciliation
classification (querying `positions_get`/`history_deals_get` to resolve an uncertain outcome) —
that is explicitly deferred to a later phase. An `UNCERTAIN` or `MALFORMED` `order_send` result
here moves the intent straight to the terminal state `FROZEN_PENDING_RECONCILIATION`, records a
dedicated `UNCERTAIN_RESULT` journal event, and permanently blocks any further attempt for that
idempotency key (the same durable duplicate-protection scan from Section 12 already prevents a
retry, since one send attempt is already on record) — there is no retry path, automatic or
otherwise, anywhere in this checkpoint.

## 14. Execution journal — `mt5_execution_journal.py`

Structurally parallel to `mode_service.py`'s `ModeTransitionLog`/`LocalModeStateStore` pair (own
schema constants, own governed event-type vocabulary): append-only, hash-chained
(`previous_event_hash`/`current_event_hash`, contiguous `append_sequence`, deterministic
`event_id`), atomically persisted (temp-file-plus-`os.replace`, matching `paper_store.py`'s
pattern), bounded (20,000 events / 4 MiB), and corruption-detecting — any hash-chain break,
sequence gap, payload-hash mismatch, or duplicate ID resets the in-memory journal to empty and
sets a `JOURNAL_STORAGE_INVALID` diagnostic rather than trusting a partial or tampered file.
Loading the journal never calls the adapter, never retries an action, and never generates a
proposal — it is pure replay (the class has no adapter reference at all).

The journal doubles as the durable **intent store**: every event that touches one order intent
carries that intent's complete current snapshot in its payload, so `ExecutionService` reconstructs
an intent's live state by scanning for the most recent event that references its
`order_intent_id` — no separate intent-storage system exists. `ExecutionService` refuses to act
(`LOOKUP_STORE_INTEGRITY_UNCERTAIN`) whenever the journal's own startup diagnostic is not `OK`,
rather than silently falling back to creating a new intent when the lookup itself cannot be
trusted.

## 15. CLI — `mt5_execution_cli.py`

`mt5-status`, `mt5-dependency-status`, `mt5-terminal-status`, `mt5-account-status`,
`mt5-symbol-status <symbol>`, `execution-capabilities`, `execution-journal [--limit N]`,
`inspect-proposal <file-or-inline-JSON>`, `build-order-intent <file-or-inline-JSON>`,
`check-order <order_intent_id>`, `send-demo-order <order_intent_id> [--confirm CODE]`,
`inspect-execution <order_intent_id>`. Every command constructs a real `ModeService` bound to the
durable mode store and a real `ExecutionService` for whatever mode is currently persisted
(mirroring `mode_cli.py`'s `_build_service`) — there is no CLI flag, environment variable, or
direct helper call that can construct or authorize an adapter action outside `ModeService`.
`send-demo-order` without `--confirm` requests confirmation and prints the challenge code and its
expiry for the local operator to read and retype; with `--confirm CODE` it calls
`confirm_and_send`. Every rejection prints a stable `{"outcome": "REJECTED", "reason_code": ...}`
document and returns a nonzero exit code; no command ever prints a password or raw account login.

## 16. Read-only HTTP and dashboard

`server.py` gained `EXECUTION_API_ROUTES` (`/api/mt5-execution-status`, `/api/mt5-account-status`,
`/api/mt5-terminal-status`, `/api/execution-journal`), wired into the existing GET-only dispatch
chain (`do_GET`/`do_HEAD`) alongside the existing route groups; POST/PUT/PATCH/DELETE were already
globally `405` for every path (`do_POST = _method_not_allowed`, etc.) before Phase 5 and needed no
change — the new routes inherit that automatically. No route can connect, check, confirm, send,
cancel, or modify execution state. The dashboard (`static/index.html`/`app.js`) gained an "MT5
execution" panel showing operating mode, adapter tier, dependency availability, redacted
terminal/account status, and the latest journal event, plus `LIVE EXECUTION DISABLED`,
`MANUAL CONFIRMATION REQUIRED`, `DEMO ONLY`, and `SMA-001`/`FIB-001 BLOCKED` banners; it uses only
`textContent`/`createElement` (no `innerHTML`) and follows the existing `renderSignalIntelligence`
pattern exactly. The pre-existing "no MT5 execution adapter... exists yet" notice in the
`operating-mode` section was corrected, since it is no longer accurate for `MT5_DEMO_MANUAL`.

## 17. Test evidence

New files: `test_mt5_execution_data.py` (24), `test_mt5_execution_adapter.py` (27),
`test_mt5_execution_journal.py` (13), `test_mt5_execution_service.py` (76),
`test_mt5_execution_cli.py` (13), `test_mt5_execution_http.py` (13) — **166 new tests**, all using
the fake adapter and isolated in-memory/temp-directory storage; none touch real `LOCALAPPDATA`,
make a network call, or import the real `MetaTrader5` package. They cover, among the kickoff's
enumerated items: mode gating (only `MT5_DEMO_MANUAL` constructs the real adapter tier; OFF/
RESEARCH/SYNTHETIC_PAPER never do), the full proposal-revalidation chain, both strategy blockers,
order-intent determinism (same proposal → same intent ID; changed proposal → different ID;
lookup-before-create reuse before/after `order_check`; crash-after-persistence recovery),
`order_check`'s full preflight matrix (terminal/account/symbol/spread/quantity/stop/freeze-level/
filling-mode, each with its own failure test), the manual-confirmation gate (wrong code, wrong
intent, expired, already-consumed, non-local channel), `order_send` (single call, duplicate
blocked including after a simulated restart, uncertain result never retried, broker-response
cross-validation), and journal integrity (hash-chain tampering, corruption, bounds). Three
existing Phase 3 tests in `test_operating_mode.py` and one in `test_signal_intelligence.py`
were updated (not weakened) because they asserted `MT5_DEMO_MANUAL` was permanently unavailable —
a blanket Phase 3 placeholder now superseded by this checkpoint's intentional, documented change;
the corresponding safety property for the three still-unavailable/still-forbidden-on-restart MT5
modes is preserved and re-asserted under its own dedicated test.

The Founder-review correction pass (Section 20) added three further files/additions: 7 tests in
`test_mt5_execution_concurrency.py` (two genuinely separate `python -B` worker processes racing
`build_order_intent`/`confirm_and_send` against one shared durable journal, synchronized via
readiness-marker files rather than a sleep guess), 14 tests in `test_mt5_execution_journal_lock.py`
(cross-process file-lock acquire/release/timeout/exception-safety/stale-lock/owner-token-safety,
in-process thread-lock, and journal-reload-after-lock-acquisition coverage), and 4 tests in a new
`TwoFreshJournalIdentityTests` class in `test_mt5_execution_service.py` (Section 20.2). Total new
Phase 5 tests: 166 + 25 = 191.

Full-suite results (`python -B -W error -m unittest discover -s . -p "test_*.py"`, run twice, after
the correction pass):

| Run | Tests | Failures | Errors | Skipped |
|---|---|---|---|---|
| 1 | 762 | 0 | 0 | 0 |
| 2 | 762 | 0 | 0 | 0 |

(569 pre-existing + 191 new Phase 5 tests + 2 net-new Phase 3 tests added while correcting the
three affected `MT5_DEMO_MANUAL`-availability assertions = 762.)

## 18. Manual rehearsal evidence

Performed against an isolated `LOCALAPPDATA` (never the Founder's real state), using the real
`mode_cli`/`mt5_execution_cli` entry points as separate process invocations:

1. Fresh isolated store → `mode_cli show-mode` → `current_mode: OFF`. Confirmed.
2. `mt5_execution_cli mt5-status` at OFF → `adapter_tier: DISABLED`, `enabled: false`.
   `build-order-intent` at OFF → `{"outcome": "REJECTED", "reason_code": "ADAPTER_DISABLED"}`,
   exit code 1. Confirmed.
3. Transitioned to `RESEARCH` → MT5 status still `DISABLED`/denied; `signal_cli signal-status`
   confirmed Phase 4 research (`enabled: true`, `operating_mode: RESEARCH`) is unaffected.
4. Transitioned to `SYNTHETIC_PAPER` → MT5 status still denied.
5. Returned to `OFF`, then transitioned to `MT5_DEMO_MANUAL` (no configured account fingerprint) →
   transition `ACCEPTED`. A **separate** CLI process invocation confirmed the mode persists
   (`operating_mode: MT5_DEMO_MANUAL`, `adapter_tier: REAL`) — validating the Section 3 restart
   fix. `mt5-account-status` showed no raw login field, only `login_redacted: null` and
   `fingerprint_configured: false`.
6. **Unplanned but informative discovery:** the real `MetaTrader5` Python package happens to
   already be installed in this development environment (not installed by this work — Phase 5
   never runs `pip install`). `mt5-dependency-status` correctly reported `available: true`.
   `mt5-terminal-status`/`mt5-account-status` correctly reported `TERMINAL_UNAVAILABLE` — no MT5
   terminal process is running on this machine, so `MetaTrader5.initialize()` itself returned
   `False`. This is exactly the sanctioned "demonstrate the real adapter's fail-closed connection
   boundary without sending an order" rehearsal path: no credential was ever displayed, and no
   broker session was ever established.
7. Built two hand-constructed, schema-valid, hypothetical proposal fixtures (SMA-001 and FIB-001,
   both otherwise fully valid) and ran `build-order-intent` against each through the **real**
   adapter tier (safe, since both blockers trigger before any adapter call is reached):
   SMA-001 → `STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`; FIB-001 →
   `STRATEGY_PARAMETERS_NOT_APPROVED`. Both confirmed, exit code 1 each.
8. `execution-journal` after the above showed exactly 3 `PROPOSAL_REJECTED` events and zero
   `ORDER_SEND_REQUESTED` events — no order was ever attempted.
9. The full fake-adapter demonstration (deterministic order-intent creation, successful fake
   `order_check`, mandatory manual-confirmation challenge, wrong confirmation rejected, correct
   local confirmation accepted, one fake `order_send`, duplicate send blocked, restart-duplicate
   protection, uncertain-result-not-retried, journal-corruption-fails-closed) is exercised by
   `test_mt5_execution_service.py` (`OrderIntentDeterminismTests`, `OrderCheckTests`,
   `ManualConfirmationTests`, `OrderSendTests`) and `test_mt5_execution_journal.py`
   (`HashChainValidationTests`) — per the kickoff instructions, this automated suite *is* the
   sanctioned "using the fake adapter... demonstrate" rehearsal vehicle, and it passed twice
   (Section 17).
10. Returned operating mode to `OFF`; confirmed via a fresh `show-mode` call.
11. Confirmed port 8765 had no listener and no Trading Lab Python process remained, before and
    after the rehearsal.
12. Deleted the isolated rehearsal directory; the Founder's real `LOCALAPPDATA` state was never
    touched (see Section 20.7 for a precise disclosure of what *did* touch the real default store
    earlier in development, before this isolation discipline was established).

A follow-up Founder-review correction pass added a second manual rehearsal round covering
concurrent first-creation, concurrent send, lock timeout, and journal corruption under the new
locking architecture — see Section 20.5 for the exact results, all against isolated temporary
storage with the fake adapter only.

## 19. Limitations and external prerequisites

- No Founder-approved MT5 demo account fingerprint has been supplied (`TRL_BLOCKERS.md`).
  `ACCOUNT_UNAVAILABLE` is the correct, reportable, external-blocker outcome until one is
  configured via `TRL_MT5_DEMO_LOGIN`/`TRL_MT5_DEMO_COMPANY`/`TRL_MT5_DEMO_SERVER`.
- No MT5 terminal process was running during this rehearsal; the real adapter's connection
  boundary was exercised and failed closed correctly, but a genuine `order_check`/`order_send`
  round trip against a live terminal was not performed.
- SMA-001 execution geometry and FIB-001 numeric parameters remain unapproved and unresolved —
  Phase 5 did not touch, weaken, or work around either blocker.
- Multi-attempt repriced retry (contract Section 5.4/6), TP2–TP4 position-reduction chains, basket
  execution, live modes, automated submission, and reconciliation are all explicitly out of scope
  for this checkpoint (Section 1).
- Phase 6 (basket execution) was not started.

## 20. Founder-review correction — cross-process execution locking

A Founder manual-rehearsal review after the initial Phase 5 implementation asked for an explicit
identity/concurrency audit against the exact contract text. This section records what was found
and corrected, in full, before commit — the race below was a real defect, not a hypothetical one,
and is recorded here rather than omitted.

### 20.1 Contract identity rules, quoted exactly

`TRL_R2_007_MT5_EXECUTION_CONTRACT.md` Section 5 distinguishes three identities, and only one of
them is claimed to be deterministic across independent stores:

- **Execution intent lookup key** (Section 5.1): `"eik_" + sha256(canonical_json(fields))[:32]`
  over proposal/account/instrument/side/quantity/strategy/risk-policy/mode/authorization fields.
  *"This key contains no nonce and no price — it is fully reproducible from the proposal and its
  authorized context alone."* This is the contract's sole deterministic, cross-store identity.
- **Execution intent ID** (Section 5.3): `"exi_" + sha256(canonical_json(lookup key fields +
  client_intent_nonce))[:32]`. The nonce is generated only on a genuine lookup miss (Section 5.2
  step 4) and *"is fixed the moment the intent is first created, never regenerated afterward"* —
  a stability guarantee scoped to one continuous durable store's lifetime, not a claim that two
  independent stores produce the same ID.
- **Idempotency key**: a Phase 5 schema field (not a separate R2-007 concept), implemented as
  `= order_intent_id` — durable, restart-safe duplicate protection *within* the one production
  journal, which is the only journal that actually exists in a real deployment.

### 20.2 Two-fresh-journal experiment — result

Building the identical hypothetical governed proposal against two genuinely independent, initially
empty durable journals (`TwoFreshJournalIdentityTests` in `test_mt5_execution_service.py`):

| Field | Journal A vs. Journal B |
|---|---|
| `proposal_id` | **identical** |
| `canonical_proposal_hash` | **identical** |
| execution intent lookup key (`eik_...`) | **identical** — recomputes independently from context alone |
| immutable broker instruction fields (instrument/side/type/quantity/price/stop/targets) | **identical** |
| `order_intent_id` (`exi_...`) | **different** — each journal's genuine first creation mints its own nonce |
| `canonical_order_intent_hash` | **different** (nonce-salted, via `order_intent_id`) |
| `idempotency_key` | **different** (= `order_intent_id`) |

This matches the contract's design exactly (Section 20.1) — it is not an identity defect. Within
one continuous journal, a second `build_order_intent` call for the identical proposal reuses the
existing `order_intent_id` unchanged (`test_lookup_before_create_within_one_journal_reuses_not_recreates`).
A missing or corrupted journal is never treated as permission to execute again — journal-integrity
uncertainty fails closed (`LOOKUP_STORE_INTEGRITY_UNCERTAIN`, Section 14) rather than falling back
to a fresh empty store.

### 20.3 The real defect: no cross-process mutual exclusion

`build_order_intent`'s lookup-before-create sequence (search the journal, then decide, then
persist) and `confirm_and_send`'s duplicate-check-then-reserve sequence had no mutual exclusion
across separate OS processes — only implicit safety from being read/written within one Python
object's lifetime. Reproduced directly: two genuinely separate `python -B` processes launched
against one initially empty durable journal, both racing `build_order_intent` for the identical
governed proposal. Both succeeded. Both produced a **different** `order_intent_id`. The durable
journal file ended up containing only **one** `ORDER_INTENT_CREATED` event — the other process's
write was silently lost (the later `os.replace()` completely overwrote the earlier one, since
each process's `ExecutionJournalWriter` held its own independently-loaded, unsynchronized
in-memory copy). The "losing" process's in-memory state still believed its own intent had been
created successfully, with `error: null` — meaning it could have gone on to run `order_check` /
`confirm_and_send` / a real `order_send` for an intent the durable journal had **no record of at
all**, defeating audit integrity and duplicate protection. This violates contract Section 5.2
("a genuinely repeated submission... resolves to the same intent... before any nonce or new
intent is ever created") and Section 11 ("no duplicate broker order under the same execution
intent"). The CLI-driven workflow (each command is its own OS process) makes this a realistic,
not merely theoretical, scenario — an in-process `threading.Lock` could never have caught it.

### 20.4 Correction — cross-process locking architecture

`mt5_execution_journal.py` gained:

- **`_CrossProcessFileLock`** — a bounded-wait (default 10s, `LOCK_ACQUIRE_TIMEOUT_SECONDS`)
  mutual-exclusion lock backed by atomic exclusive file creation (`O_CREAT | O_EXCL`, atomic on
  both POSIX and Windows) at `<journal-path>.lock`. Each acquisition writes a unique owner token
  (`pid:random-hex`) into the lock file; `release()` only unlinks the file if it still contains
  *this* acquisition's own token — a holder whose lock was broken as stale and re-acquired by a
  different owner can never delete that owner's live lock by releasing late (this exact bug class
  was caught and fixed during this correction pass — see `test_mt5_execution_journal_lock.py`).
  A lock file older than `LOCK_STALE_SECONDS` (60s) is treated as abandoned by a genuinely
  crashed/killed owner and broken; on Windows specifically, a file cannot be unlinked while any
  handle to it remains open even from the same process, so this recovery path only actually
  succeeds once the OS has reclaimed a truly-terminated owner's handle — a merely slow-but-alive
  owner's lock cannot be stolen, which is the intended behavior.
- **`_ThreadLock`** — the in-memory-store equivalent (an in-memory journal can never actually be
  shared across separate OS processes in the first place, so a `threading.Lock` suffices there).
- **`ExecutionJournalWriter.acquire_creation_lock()`** — a context manager that acquires the
  store's lock *and immediately reloads the journal from disk* before yielding, so the caller's
  search always sees the freshest state any other process may have persisted while this caller
  was waiting; a stale in-memory snapshot loaded only at construction time would otherwise defeat
  the lock entirely regardless of how correct the lock primitive itself is.
- **`EXECUTION_LOCK_UNAVAILABLE`** — the new closed-vocabulary reason code `build_order_intent`
  and `confirm_and_send` raise if the lock cannot be acquired in time; the operation is never
  allowed to proceed unlocked as a fallback.

`mt5_execution_service.py`: `build_order_intent`'s entire lookup-then-create sequence, and
`confirm_and_send`'s entire confirmation-consumption-check-through-`ORDER_SEND_REQUESTED`-persist
sequence, now run inside `with self._journal.acquire_creation_lock():`. The lock is released again
immediately after `ORDER_SEND_REQUESTED` is durably persisted, *before* `order_send` is ever
called — the durable reservation itself is what makes every concurrent caller fail closed
afterward, so the (potentially slow, real-world) broker call never happens while holding the lock.

### 20.5 Corrected behavior — verified

Same two-genuinely-separate-process race, re-run after the fix, five independent times plus the
permanent automated regression (`test_mt5_execution_concurrency.py`, 7 tests): both processes now
converge on the **same** `order_intent_id`; the journal contains exactly one `ORDER_INTENT_CREATED`
and one `ORDER_INTENT_REUSED` event; zero adapter calls from either process; the lock file is
removed after use every time. The equivalent send-side race (`ConcurrentSendTests`) confirms
exactly one process reserves `ORDER_SEND_REQUESTED` and calls the adapter's `order_send` (verified
via each worker's own private fake-adapter call count, summed to exactly 1 across both processes);
the losing process fails closed with `CONFIRMATION_ALREADY_CONSUMED` (deterministic, since
`MANUAL_CONFIRMATION_ACCEPTED` is always persisted, under the same lock, immediately before
`ORDER_SEND_REQUESTED`) without ever calling the adapter; restarting afterward still blocks any
further submission. Lock-timeout behavior (manually rehearsed and unit-tested): a contended lock
fails closed with `EXECUTION_LOCK_UNAVAILABLE` after the bound elapses, with zero adapter calls
and zero journal writes from the timed-out caller; normal operation resumes immediately once the
lock is free. Journal corruption interacting with the lock (manually rehearsed and unit-tested):
acquiring the lock over a corrupted journal does not bypass validation — the mandatory reload
inside the lock re-detects the corruption and fails closed with `LOOKUP_STORE_INTEGRITY_UNCERTAIN`,
with zero adapter calls and no silent empty-store replacement written to disk.

### 20.6 Status-command side-effect audit

Reviewed whether constructing `ModeService` for a read-only status command (`mt5-status`,
`mt5-symbol-status`, dependency inspection) appending one `MODE_STATE_LOADED` audit event is safe:
it is **contract-required**, **inherited Phase 3 behavior** (`TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`
item 9: *"Record the startup resolution as an audit event"*) that predates and is untouched by
Phase 5. It is bounded (`MAX_MODE_EVENTS = 2000`, `MAX_MODE_STORE_BYTES = 512 KiB`), never changes
the operating mode, never touches the execution journal, and never constructs a real adapter or
queries a broker while mode is `OFF` (a bare status command at `OFF` resolves to
`DisabledExecutionService`, whose methods return static denial documents without touching any
adapter at all). This was not redesigned, per the review instructions, since it is intentional
Phase 3 behavior outside Phase 5's scope.

### 20.7 LOCALAPPDATA disclosure (development-session transparency)

Before the isolated Founder rehearsal was established as practice, two development-session
sanity/status CLI invocations (`mt5-status`, `mt5-symbol-status`) were run against the real,
default `%LOCALAPPDATA%` mode store, each appending one benign, load-only `MODE_STATE_LOADED`/`OFF`
audit event. One later ad-hoc verification `ModeService()` construction (checking the real store's
final state) appended one further such event. In every case: the operating mode remained `OFF`
throughout; no execution journal was created, read, or modified; no credential was used, computed,
or displayed; no order intent was created; no `order_check` or `order_send` occurred; no broker
connection occurred; the append-only mode-transition log was never truncated, rewritten, or
manually repaired — it was only ever appended to by the code's own normal, governed startup path.
Every Founder manual-rehearsal script (both the original rehearsal and this correction pass) and
every automated identity/concurrency test used isolated temporary storage exclusively. This is
disclosed here as a transparent record of development-session discipline, not concealed; it is not
a claim that production `LOCALAPPDATA` was completely untouched throughout all of Phase 5's
development — only that the governed rehearsal and test evidence itself is fully isolated.

## 21. Explicit statement

No real broker order was submitted at any point during this checkpoint's implementation, testing,
or manual rehearsal. No automated test imports or calls the real `MetaTrader5` package against a
live terminal. No real broker connection occurred during the automated test suite. The one real
adapter interaction performed during the manual rehearsal was a read-only status/dependency check
that failed closed with no terminal running and no credential displayed.
