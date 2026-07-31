# TRL-R2-007 MT5 Execution Adapter Contract

> **DEMO REHEARSAL ONLY UNTIL FOUNDER LIVE ACTIVATION — NO AUTOMATED TEST MAY SUBMIT A REAL ORDER**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-007 |
| Status | Design contract — implementation not yet started. Revised after Founder Phase 2 document review (correction pass, see `TRL_DECISION_LOG.md`) and a final Founder/CTO correction pass adding the first-live-activation risk floor and the deterministic intent lookup key. |
| Depends on | TRL-R2-005 (paper engine), TRL-R2-006 (signal proposals), existing `mt5_service.py` read-only connector |
| Feeds | Phase 9 (live-automation arming and emergency controls) gates every mutation this adapter can perform |

## 1. Boundary

This adapter is the only component permitted to call `MetaTrader5.order_check`
or `order_send`. No other module, no browser request, and no LLM output may
reach the broker directly. The existing read-only `mt5_service.py` connector
(R2-003) is extended, not replaced — market-data and account *reads* keep
their current shape; this contract adds validation, submission, and
reconciliation *on top*.

Every mutation call requires: (a) a proposal that has passed the full R2-006
pipeline, (b) the operating-mode state machine (Phase 3) in a state that
permits it, and (c) for automated paths, an active arming token (Phase 9).
Any one of these being absent fails closed with no partial execution.

No broker credential, terminal secret, account secret, or connection detail
capable of reconstructing a credential ever appears in this adapter's local
logs, exception messages, HTTP responses, or exported reports (Section 12).

## 2. Separate interfaces

| Interface | Allowed calls | Never does |
|---|---|---|
| Market-data access | `symbol_info`, `symbol_info_tick`, `copy_rates_*` | never submits an order |
| Account access | `account_info` | never submits an order |
| Order validation | `order_check` | never commits to a position; a failed check has zero broker-side effect |
| Order submission | `order_send` | only called after a successful, freshly re-checked `order_check` for the same attempt |
| Position reconciliation | `positions_get` | read-only; writes only to local audit records |
| History reconciliation | `orders_get`, `history_deals_get`, `history_orders_get` | read-only |
| Emergency controls | close/cancel calls scoped to governed positions/orders only | never touches a position this system did not open (see Section 11) |

## 3. Preflight validation (all must pass before any order attempt)

### Terminal
- `initialize()` succeeded this session.
- Terminal reports connected.
- Trade API is not disabled at the terminal level.
- Trading is allowed (`terminal_info().trade_allowed`).
- Terminal identity (path, build) recorded in the audit event.
- Terminal path matches the configured expected path (prevents silently talking to the wrong installation).

### Account
- `account_info()` returns a value.
- `login` matches the configured allowlisted fingerprint exactly.
- `company` (broker) matches the configured fingerprint.
- `server` matches the configured fingerprint.
- `currency` recorded in every audit event.
- `trade_mode` (demo/contest/real) matches the current operating mode: `MT5_DEMO_*` modes reject a real account; `MT5_LIVE_*` modes reject a demo account. Mismatch fails closed with `ACCOUNT_MODE_MISMATCH`, never a silent downgrade.
- `trade_allowed` and `trade_expert` (EA trading allowed) both true.
- Margin level and stop-out level within configured acceptable bounds.

### Symbol
- Exact broker-native symbol string exists in `symbol_info` (no alias guessing).
- Symbol is visible, or is safely selected via `symbol_select` and re-verified.
- `symbol_info_tick` returns a tick.
- Tick age is within the configured freshness bound (reuses R2-005's staleness concept, applied to live ticks).
- Bid/ask both positive and `ask > bid`.
- Spread (in points) ≤ proposal's `maximum_spread`.
- Requested volume respects `volume_min`, `volume_max`, `volume_step`.
- Price respects `digits` and `point`.
- Stop distance respects `trade_stops_level` and `trade_freeze_level`.
- A permitted filling mode is selected from `filling_mode` flags, never assumed.
- Market session open per `symbol_info.session_deals` / trade session tables.

### Risk (independently re-derived here, not trusted from R2-006)
- Stop loss is present and non-null — an order without one is never sent.
- Stop distance valid (> 0, respects freeze/stop level above).
- Position size derived from allowed account risk, same formula family as R2-005/R2-006.
- Hard ceiling: 1% of equity per proposal; default 0.5% unless explicitly raised (never above the ceiling).
- For a **first live activation** on this account, Section 4's tighter floor applies before this general ceiling.
- Combined basket risk (Phase 6) stays within the *one* proposal's risk budget — baskets do not multiply risk per child order.
- Daily loss and drawdown halts checked against the same governed limits as the paper engine.
- Margin usage and total open risk within configured limits.
- Correlated-exposure limit respected (configured instrument correlation groups).
- Per-instrument position limit respected (default: one open position per instrument, matching R2-005).
- No martingale, no risk increase after a loss, no averaging down outside one predeclared, separately risk-approved basket.
- No duplicate proposal (same `proposal_id` cannot be submitted twice) and no duplicate broker order under the same execution intent (Section 5) — a repriced retry never creates a second logical intent, and a genuinely repeated submission is resolved by lookup (Section 5.1–5.2) before any broker call.

## 4. First live activation risk floor

*Added in the final Founder/CTO correction pass. Applies whenever the
operating mode is `MT5_LIVE_MANUAL` or `MT5_LIVE_AUTOMATED` **and** no prior
execution intent for this account's `account_fingerprint_hash` has ever
reached `FILLED` or `PARTIALLY_FILLED` while in a live mode — i.e. this
would be the account's first live fill. The system determines this
automatically from reconciled history; it is never a manually-set flag that
could be forgotten or skipped.*

1. The target risk for a first live activation is **no more than 0.1% of
   current governed equity** — the proposal's own approved risk percent for
   a first-live proposal must already be at or below this, per
   `TRL_LIVE_EXECUTION_RUNBOOK.md` Section 2.
2. Before proceeding, compute the exact monetary and percentage risk that
   the **broker's minimum permitted volume** for this instrument would
   itself create, using: the validated entry price (Section 3, Symbol),
   the proposal's mandatory stop price, `tick_value`, `tick_size`,
   `contract_size`, an account-currency conversion where the instrument's
   profit currency differs from the account currency, and the broker's
   `volume_min`/`volume_step`. If a required currency conversion rate is
   not available from a governed, freshly quoted source, fail closed with
   `CURRENCY_CONVERSION_UNAVAILABLE` — never approximate or skip the
   conversion.
3. **If the broker minimum-volume risk is at or below 0.1%**, the proposal
   continues through the normal preflight in Section 3, sized at or below
   the 0.1% target as usual.
4. **If the broker minimum-volume risk is above 0.1%**, fail closed with
   `FIRST_LIVE_MINIMUM_VOLUME_EXCEEDS_TARGET_RISK`. The smallest size the
   broker will accept already exceeds the first-activation target — no
   ordinary sizing choice can fix this, so execution stops rather than
   silently sizing above target.
5. The block is displayed with every one of: target risk percentage (0.1%),
   actual minimum-volume risk percentage, the monetary risk amount, the
   instrument, the entry price, the stop price, the minimum volume, and the
   exact reason code above. Nothing about the block is summarized away.
6. The blocked first activation may proceed **only** after a separate,
   proposal-specific Founder approval — `TRL_FIRST_LIVE_OVERRIDE_APPROVAL.v1`
   — that explicitly displays and requires acknowledgement of the exact
   percentage and monetary risk computed in step 2. This is not the same
   confirmation as the general `order-check`/`execute-live` flow; it is a
   distinct, additional step.
7. **Even with that approval, the resulting order must never exceed the
   normal 0.5% hard ceiling (Section 3).** If the broker minimum-volume risk
   itself exceeds 0.5%, the trade is prohibited outright and the override
   approval object cannot even be created — there is no path, overridden or
   otherwise, that permits it.
8. The override approval is:
   - **single-use** — consuming it (by executing the associated attempt)
     immediately invalidates it for any further use;
   - **proposal-specific** — bound to one `proposal_id`;
   - **account-specific** — bound to one `account_fingerprint_hash`;
   - **instrument-specific** — bound to one `broker_native_instrument`;
   - **short-lived** — expires quickly (target: 15 minutes) after creation;
   - **an audit event** on both creation and consumption (or expiry unused).
9. The system never automatically raises the target from 0.1% merely
   because the broker's minimum volume is larger — every occurrence of this
   situation requires a fresh, explicit override approval; none is ever
   reused, inferred, or silently granted from a prior one, even for the same
   instrument.

`TRL_FIRST_LIVE_OVERRIDE_APPROVAL.v1` fields: `proposal_id`,
`account_fingerprint_hash`, `broker_native_instrument`, `target_risk_percent`
(`"0.1"`), `minimum_volume_risk_percent`, `minimum_volume_risk_amount`,
`minimum_volume`, `entry_price`, `stop_price`, `authorization_identity` (the
Founder confirmation event for this specific approval), `approved_at_utc`,
`expires_at_utc`, `consumed` (boolean), `consumed_at_utc` (nullable).
Validation on creation rejects the object outright if
`minimum_volume_risk_percent` exceeds 0.5% (step 7) — that case has no
representable approval object at all.

Once an account's first live activation reaches `FILLED` or
`PARTIALLY_FILLED`, this section no longer applies to that account; the
normal Section 3 risk ceiling governs every activation after it.

## 5. Execution identity: intent vs. attempt

*Revised in the Phase 2 correction pass to close a duplicate-order gap
found in Founder review (the original design keyed duplicate-detection off
values that could legitimately change between attempts), and revised again
in the final correction pass to remove the ambiguity a freshly-generated
`client_intent_nonce` could create before any duplicate-lookup had run.*

An **execution intent** is the immutable identity of one logical order the
system has decided to place. An **execution attempt** is one concrete
`order_check`/`order_send` try under that intent. Repricing, re-quoting, or
retrying after an ambiguous result always creates a new **attempt** under the
*same* intent — it never creates a new intent, and a genuinely repeated
submission of the same logical order resolves to the same intent via the
lookup key below, before any nonce or new intent is ever created.

### 5.1 Execution Intent Lookup Key — deterministic, no nonce

Computed from exactly these fields, in canonical field set
(`TRL_EXECUTION_INTENT_LOOKUP_KEY.v1`), before anything else happens:

| Field | Meaning |
|---|---|
| `proposal_id` | the R2-006 proposal this intent would execute |
| `account_fingerprint_hash` | sha256 of the account's login, company, and server values joined together |
| `broker_native_instrument` | exact broker symbol |
| `side` | `BUY` or `SELL` |
| `approved_quantity` | approved volume for a single order, **or** `null` for a basket child |
| `approved_aggregate_risk_id` | the basket's approved aggregate-risk identity, **or** `null` if not a basket child — exactly one of `approved_quantity` / `approved_aggregate_risk_id` is non-null |
| `basket_child_id` | stable per-child identity (Section 5.6), **or** `null` if this is not a basket child |
| `strategy_id` | from the proposal |
| `strategy_version` | from the proposal |
| `risk_policy_hash` | hash of the governed risk configuration in effect |
| `operating_mode` | e.g. `MT5_LIVE_MANUAL`, `MT5_LIVE_AUTOMATED`, `MT5_DEMO_MANUAL`, `MT5_DEMO_AUTOMATED` |
| `authorization_identity` | the Founder confirmation event ID (manual) or arming token ID (automated), never a secret itself |

`execution_intent_lookup_key = "eik_" + sha256(canonical_json(above fields))[:32]`.
This key contains **no nonce and no price** — it is fully reproducible from
the proposal and its authorized context alone, which is exactly what makes
it safe to compute and search *before* any nonce or intent exists.

### 5.2 Lookup-before-create flow

Runs before any nonce, any `execution_intent_id`, or any broker call:

1. Compute the lookup key (Section 5.1) for the proposal/context at hand.
2. Search the durable audit store (the same append-only, hash-chained
   storage class as R2-005's timeline) for an existing execution intent
   record whose stored lookup key matches.
3. **Match found:** reuse that exact intent — its `execution_intent_id`,
   its already-stored `client_intent_nonce`, and its complete attempt
   history. No new intent is created. If the intent's current state is
   already terminal (`FILLED`, `REJECTED`, `CANCELLED`, or a fully closed
   `PARTIALLY_FILLED`), the repeated submission is answered with that
   existing outcome and **no `order_check` or `order_send` call is made
   merely because the request arrived again**. If the intent's state
   permits a further attempt (`CREATED` with no attempt yet, or
   `NOT_FOUND_SAFE_TO_RETRY`), proceed to create a new execution attempt
   (Section 5.4) under the existing intent.
4. **No match found:** only now is a `client_intent_nonce` generated
   (random, once), and only now is a new `execution_intent_id` computed
   (Section 5.3, using the lookup-key fields plus the fresh nonce). The
   lookup key, the nonce, and the new intent record are persisted
   atomically, in one durable write, before any broker call is made.
5. **Lookup or durable-store integrity uncertain** (a read error, a
   hash-chain validation failure, or any inability to conclusively
   determine whether a matching intent exists): fail closed. A new intent
   is never created as a fallback when the lookup itself cannot be trusted
   — that would silently reintroduce the exact duplication risk this
   mechanism exists to prevent. Route to `MANUAL_REVIEW_REQUIRED` and
   require reconciliation before anything proceeds.
6. A process crash between step 4's persistence and the first `order_send`
   recovers the already-persisted intent on restart via the same lookup key
   (Section 6, restart handling) — it does not create a second one.
7. A browser refresh, an API-level retry, a repeated CLI command, or a
   process restart that all logically describe "submit this proposal"
   resolve, via the lookup key, to the exact same intent every time.

### 5.3 Execution Intent ID — immutable

`TRL_EXECUTION_INTENT_ID.v1` uses the same fields as the lookup key
(Section 5.1) plus `client_intent_nonce` (populated only per the
lookup-before-create flow, Section 5.2):

`execution_intent_id = "exi_" + sha256(canonical_json(lookup key fields + client_intent_nonce))[:32]`
(same deterministic-hash house style as R2-005's stable IDs). None of these
fields change if a quote moves, a spread widens, or a retry is needed —
that is the entire point of this identity, and the nonce itself is fixed
the moment the intent is first created, never regenerated afterward.

### 5.4 Execution Attempt ID — one per try

Computed fresh for every submission try under an intent, from
(`TRL_EXECUTION_ATTEMPT_ID.v1`):

| Field | Meaning |
|---|---|
| `execution_intent_id` | the parent intent |
| `attempt_sequence` | 1, 2, 3, ... strictly increasing per intent |
| `quoted_price` | the bid/ask pair used for *this* attempt's request parameters |
| `request_timestamp_utc` | when this attempt's `order_send` was issued |
| `broker_request_hash` | sha256 of the exact request payload sent to the broker for this attempt |

`execution_attempt_id = "exa_" + sha256(canonical_json(above fields))[:32]`.
A magic number is derived deterministically from `strategy_id` (stable
mapping, recorded in the registry) and is the same across every attempt of
one intent. A bounded, sanitized broker comment is derived from the
`execution_intent_id` (not the attempt), so the broker-side record itself
carries a stable, greppable link back to the intent.

### 5.5 Execution intent state machine

```
CREATED
  --(submit attempt)--> ATTEMPT_PENDING
ATTEMPT_PENDING
  --(confirmed success retcode + reconciled deal, full volume)--> FILLED
  --(confirmed success retcode + reconciled deal, partial volume)--> PARTIALLY_FILLED
  --(confirmed rejection retcode)--> REJECTED
  --(pending order cancelled, e.g. proposal expired)--> CANCELLED
  --(timeout / dropped connection / no confirmed retcode)--> FROZEN_PENDING_RECONCILIATION
FROZEN_PENDING_RECONCILIATION
  --(reconciliation: no matching broker-side record found)--> NOT_FOUND_SAFE_TO_RETRY
  --(reconciliation: matching deal found, full volume)--> FILLED
  --(reconciliation: matching deal found, partial volume)--> PARTIALLY_FILLED
  --(reconciliation: ambiguous or conflicting records)--> MANUAL_REVIEW_REQUIRED
NOT_FOUND_SAFE_TO_RETRY
  --(new attempt created under the SAME intent, full preflight re-run)--> ATTEMPT_PENDING
FILLED / PARTIALLY_FILLED (fully closed) / REJECTED / CANCELLED / MANUAL_REVIEW_REQUIRED
  --terminal for this intent--
```

A `PARTIALLY_FILLED` intent whose remaining approved quantity is still valid
(proposal not expired, preflight still passes) may create a further attempt
under the same intent for the remainder, following the same `ATTEMPT_PENDING`
path. `MANUAL_REVIEW_REQUIRED` is terminal for automation: no further
automated attempt may be created under that intent under any circumstance —
only a Founder, after manual investigation, may close it out (mark it
resolved with the true outcome) or explicitly authorize a fresh proposal
(a new intent, with its own new lookup key) to replace it.

### 5.6 Basket children

Every basket child order carries its own stable `basket_child_id`, assigned
once when the parent basket is approved, derived deterministically (e.g.
`"bc_" + sha256(parent_proposal_id + child_index)[:16]` — never randomly).
The lookup key (Section 5.1) includes `basket_child_id`, so each child has
its own independent lookup identity. A repeated **parent** basket
submission resolves every child, individually, to its already-existing
child intent via Section 5.2 — the basket as a whole is never re-created,
and no child is ever duplicated or silently dropped on a retry.

## 6. Execution flow

1. Resolve or create the execution intent via the lookup-before-create flow (Section 5.2); persist it before any broker call.
2. Compute a new execution attempt (Section 5.4) for this try.
3. Call `order_check` with the exact parameters intended for `order_send` for this attempt.
4. Validate the `order_check` response: retcode must indicate success; reject on any other retcode with the retcode recorded verbatim against this attempt.
5. Call `order_send` only immediately after a successful check with unchanged parameters for this same attempt. If any preflight fact changed between check and send (tick moved beyond tolerance, spread widened, account state changed), do not send — return to step 2 and create a new attempt with freshly re-run preflight, under the same intent.
6. Validate the trade result: a non-`TRADE_RETCODE_DONE`-family result is a rejection, recorded with its retcode; **an order object being non-null is never itself treated as proof of success**.
7. Store the request hash, response hash, and (on success) the broker order ticket, deal ticket, and position ticket against this attempt in the local audit timeline.
8. Reconcile immediately via `positions_get`/`history_deals_get` — do not rely solely on the `order_send` return value for state.
9. If the result is ambiguous or times out, move the intent to `FROZEN_PENDING_RECONCILIATION` (Section 7) — never blindly retry.
10. On process restart, any intent found in `ATTEMPT_PENDING` (its outcome was never confirmed before the process stopped) is treated as `FROZEN_PENDING_RECONCILIATION` and must clear reconciliation before anything resumes. The full intent and attempt history is loaded from the audit timeline before any new attempt is considered, preventing duplicate orders after a crash/restart — and any intent that had only been persisted (Section 5.2 step 4) but never reached `ATTEMPT_PENDING` is recovered as `CREATED`, so a crash between persistence and the first `order_send` resumes from the existing intent rather than creating another.

## 7. `FROZEN_PENDING_RECONCILIATION` handling (formerly "unknown outcome")

The instant an attempt's result cannot be confirmed:

1. **Freeze the intent.** No new attempt may be created under it while frozen.
2. **Do not submit another order merely because a quote changed.** A moved price is not a reason to act; only a reconciled outcome is.
3. **Reconcile first.** Query `orders_get`, `positions_get`, and `history_deals_get`, searching by: the intent's magic number, its bounded broker comment (Section 5.4), the account fingerprint, instrument, side, quantity, and a bounded time window around the attempt's `request_timestamp_utc`.
4. **Classify deterministically** into exactly one of: `FILLED`, `PARTIALLY_FILLED`, `REJECTED`, `CANCELLED`, `NOT_FOUND_SAFE_TO_RETRY`, or `MANUAL_REVIEW_REQUIRED`.
5. **If reconciliation itself is ambiguous** (conflicting records, an unexpected partial match, or the reconciliation call itself fails) — fail closed into `MANUAL_REVIEW_REQUIRED`. Never guess.
6. Only `NOT_FOUND_SAFE_TO_RETRY` permits a new attempt, and only under the same intent, with attempt-sequence incremented and full preflight re-run fresh (not reused from the frozen attempt).
7. `MANUAL_REVIEW_REQUIRED` blocks all further automated submissions for that instrument until a Founder resolves it (Section 11, Emergency Runbook).

## 8. Stops and targets

- Where the broker permits, send the initial protective stop (and, if supported, TP1) together with the entry request.
- If a mandatory protective stop cannot be validated against the broker's stop/freeze level, the entry is rejected — never sent unprotected "to fix later."
- TP2–TP4 and partial closes are managed as governed position-reduction events, mirroring R2-005's `PAPER_TP` model but against real position tickets, and each such reduction is itself its own execution intent (a `CLOSE` side against the open position), following the same lookup/intent/attempt model as an entry.
- Quantity conservation is exact: sum of partial closes + final close equals the original filled volume, accounting for broker volume-step rounding, with any rounding difference recorded explicitly (never silently absorbed).
- A position is never left silently unprotected: if a stop cannot be (re)confirmed present on a live position during reconciliation, that position enters the unprotected-position alert queue (Phase 10) immediately.

## 9. CLI commands

`connect`, `health`, `account-snapshot`, `validate-symbol`, `preview-proposal`,
`order-check`, `execute-demo`, `execute-live`, `cancel-pending`,
`close-position`, `emergency-flatten`, `disable-new-entries`, `reconcile`,
`disconnect`. Every mutating command (`execute-*`, `cancel-pending`,
`close-position`, `emergency-flatten`, `disable-new-entries`) requires
server-side authorization (Phase 8 roles) and writes an audit event
regardless of outcome.

## 10. Testing boundary

Automated tests use mocks/fakes of the `MetaTrader5` module surface — they
never import or call the real module against a live terminal, and therefore
can never submit a live order. A manual rehearsal against a real MT5 **demo**
account is the only sanctioned way to exercise the real `order_send` path
before Founder live activation; live-account rehearsal is preflight-only
(`connect`, `health`, `account-snapshot`, `order-check`) until the Founder
personally performs the first live order, subject to Section 4's floor.

## 11. Emergency controls scope

`emergency-flatten` and `close-position` operate only on positions whose
magic number and comment match this system's own governed scheme (Section
5.4). A position opened manually by the Founder outside this system, or
by any other EA, is never touched by these commands.

## 12. Secret and credential handling

No broker credential, terminal secret, account secret, or value that could
reconstruct a credential is ever:

- written to a local log line, structured or unstructured;
- included in an exception message or stack trace;
- returned in any HTTP response body or header (this adapter's mutations
  are only ever reachable through the authenticated layer defined in
  TRL-R2-008, which itself never forwards broker credentials to a browser);
- written into an exported report (Phase 10).

Account identifiers that are not secrets (login number, broker company name,
server name, currency) may appear in audit events and reports for
traceability, but the fingerprint values used in identity computation
(Section 5.1) are hashed rather than embedded raw, so a leaked
`execution_intent_id`, lookup key, or audit record does not itself reveal
the raw account login.

## 13. Acceptance tests

- Full preflight checklist (Sections 3.1–3.4) as individual unit tests against mocked terminal/account/symbol/risk states, each with a passing and at least one failing case.
- First-live-floor-within-target test: broker minimum-volume risk at or below 0.1% proceeds through normal preflight without requiring an override.
- First-live-floor-blocked test: broker minimum-volume risk above 0.1% fails closed with `FIRST_LIVE_MINIMUM_VOLUME_EXCEEDS_TARGET_RISK` and displays all required fields (Section 4, item 5).
- First-live-override-required-and-single-use test: the blocked case proceeds only after a valid, unconsumed `TRL_FIRST_LIVE_OVERRIDE_APPROVAL.v1`; consuming it invalidates it for further use.
- First-live-override-absolute-prohibition test: minimum-volume risk above 0.5% cannot produce a valid override approval object under any input — creation itself fails.
- First-live-no-auto-raise test: across repeated first-live attempts at the same broker minimum, the system never substitutes a higher target without a fresh override approval each time.
- Currency-conversion-unavailable test: a missing governed conversion rate for a first-live computation fails closed with `CURRENCY_CONVERSION_UNAVAILABLE` rather than approximating.
- Lookup-before-create test: computing the lookup key for an identical proposal/context twice, before any intent is persisted, resolves to the same intent on the second call rather than creating two.
- Repeated-before-submission test: an identical resubmission before any `order_check` call reuses the existing `CREATED` intent and creates only one subsequent attempt.
- Repeated-after-order-check test: an identical resubmission after a successful `order_check` but before `order_send` reuses the existing intent rather than starting a second one.
- Repeated-after-timeout test: an identical resubmission after an `order_send` timeout resolves to the same intent, now `FROZEN_PENDING_RECONCILIATION`, and does not call `order_send` again until reconciliation permits it.
- Crash-after-persistence test: simulating a crash immediately after Section 5.2 step 4's atomic persistence (before any broker call) — restart recovers the existing `CREATED` intent via the lookup key rather than creating a new one.
- Browser/API-retry test: a duplicate HTTP submission of the same proposal resolves, via the lookup key, to the same intent.
- Basket-parent-retry test: resubmitting an entire basket resolves every child to its existing child intent (via `basket_child_id`) with no child duplicated or dropped.
- Durable-store-lookup-failure test: a simulated read/validation failure during lookup fails closed to `MANUAL_REVIEW_REQUIRED` rather than falling back to creating a new intent.
- Nonce-only-for-new-intent test: `client_intent_nonce` is generated exactly once, only on a genuine lookup miss, and is never regenerated for a resolved/reused intent.
- Intent-stability test: an execution intent computed twice for the same proposal, account, and risk-policy hash — but with two different quoted prices — yields the *same* `execution_intent_id` and two different `execution_attempt_id`s.
- Restart-duplicate test: process restart mid-flow moves the in-flight intent to `FROZEN_PENDING_RECONCILIATION` and does not resubmit an already-accepted order.
- Uncertain-result test: a simulated timeout after `order_send` moves the intent to `FROZEN_PENDING_RECONCILIATION`, reconciliation classifies it, and only a `NOT_FOUND_SAFE_TO_RETRY` classification permits a new attempt under the same intent.
- Ambiguous-reconciliation test: a simulated conflicting/partial broker record during reconciliation results in `MANUAL_REVIEW_REQUIRED`, and no further automated attempt is possible for that intent afterward.
- Repricing-is-not-a-new-intent test: a changed quote between the original attempt and a permitted retry produces a new `execution_attempt_id` under the *same* `execution_intent_id`.
- Unprotected-position test: a position missing a confirmed stop on reconciliation raises the unprotected-position alert.
- No-automated-live-order test: static/dynamic check confirming no test module imports the real `MetaTrader5` package in a way that could reach a live terminal.
- Secret-leak test: a scan of every log line, exception message, and HTTP response format string emitted by this adapter confirms no raw credential or fingerprint field appears unhashed outside the account-identifier allowlist (Section 12).
