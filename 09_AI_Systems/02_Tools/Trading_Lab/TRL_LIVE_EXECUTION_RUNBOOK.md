# TRL Live Execution Runbook

> **The Founder performs the first real-money activation personally. This runbook is the exact procedure for that activation and every one after it.**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | Full-vision program, Phase 2 (procedure defined ahead of Phase 9 implementation) |
| Status | Design-time runbook — commands below are the target CLI surface from the R2-007 contract; will be verified word-for-word once implemented |

## 1. Before you start

Confirm every item; do not proceed if any is unchecked.

- [ ] MT5 terminal installed, logged into the intended **live** account, and reachable (`connect` / `health` commands both report OK).
- [ ] Account fingerprint (login, broker company, server) matches the value configured for `MT5_LIVE_*` modes.
- [ ] Demo execution parity has been demonstrated: the same strategy has completed a full demo rehearsal (Phase 12.D–H) with no unresolved defects.
- [ ] Current risk policy hash matches what you intend to run (no unreviewed risk-config change since the last demo rehearsal).
- [ ] Recent reconciliation (Phase 10) shows no execution intent stuck in `FROZEN_PENDING_RECONCILIATION` or `MANUAL_REVIEW_REQUIRED` (an unresolved `UNKNOWN_OUTCOME`) and no unprotected-position alerts.
- [ ] No active risk halt.
- [ ] You have read `TRL_EMERGENCY_RUNBOOK.md` and know the emergency-stop command before you arm anything.

## 2. Manual live activation (first time)

**The first live activation targets no more than 0.1% of current governed
equity — never the normal 0.5% default — and the system fails closed rather
than silently sizing above that target.** This is a deliberate one-time
floor to prove the entire live path (preflight, execution intent, fill,
stop confirmation, reconciliation) with the smallest possible real-money
exposure before trading at the normal governed risk percentage. The exact
mechanism is defined in `TRL_R2_007_MT5_EXECUTION_CONTRACT.md` Section 4;
this is how it shows up in the procedure:

1. Run `account-snapshot` against the live account. Verify balance, equity, and open positions match what you expect from the broker's own terminal/app — cross-check independently, not just from this system.
2. Run `validate-symbol` for the instrument you intend to trade. Confirm spread, session, and stop/freeze levels are sane for a live session.
3. Generate a proposal through the normal R2-006 pipeline (or accept a pending one already produced). Review it in full: entry, stop, TP1–4, risk percent, confidence, and its evidence chain. Confirm its risk percent is at or below 0.1%.
4. Run `order-check` (not `execute-live`) first.
   - If the check reports `FIRST_LIVE_MINIMUM_VOLUME_EXCEEDS_TARGET_RISK`,
     the broker's smallest tradeable size already exceeds the 0.1% target
     for this instrument. Read the displayed target percentage, actual
     minimum-volume percentage, monetary risk, entry, and stop. Do not try
     to work around this by resizing — resizing smaller than the broker
     minimum is not possible. Proceeding requires the separate override
     approval in step 4a; if you are not prepared to explicitly accept a
     risk above 0.1% (and never above 0.5%) for this specific proposal,
     stop here and pick a different instrument or wait.
   - 4a. **Override (only if you explicitly choose to proceed above 0.1% for
     this one proposal):** the system will only ever offer this when the
     minimum-volume risk is at or below 0.5% — above that, there is no
     override, the trade is simply prohibited. Confirm you are shown the
     exact percentage and monetary risk, and that the approval you grant is
     scoped to this one proposal, this one account, and this one
     instrument, and expires in minutes. Do not grant it if you have not
     personally read and understood the exact numbers displayed.
   - Otherwise (no block), confirm the check succeeds and the reported margin/cost matches your expectation.
5. Only then run `execute-live` for that single proposal. This is a manual, one-proposal-at-a-time action — automated live execution is a separate, later arming step (Section 3).
6. Immediately run `reconcile`. Confirm the position, deal, and order tickets recorded locally match the broker's own history.
7. Confirm the position shows a broker-confirmed protective stop before you consider the entry complete.

Raise to the normal 0.5% default only after this first activation has been
reconciled clean and you have deliberately decided to do so — the system
never raises it for you, and this first-activation floor stops applying
automatically once your first live fill is reconciled (Section 4 of the
R2-007 contract).

## 3. Arming automated live execution

Automated live execution requires the full arming state machine (Phase 9) to
reach `LIVE_ARMED`. In order:

1. Server mode must already be `MT5_LIVE_AUTOMATED` (a deliberate configuration change, not a default).
2. Account fingerprint re-verified fresh (not cached from a prior session).
3. Current risk policy hash re-confirmed.
4. Broker connection healthy, market data fresh, no active risk halt, no unresolved execution, recent reconciliation clean.
5. Founder reauthenticates (fresh credential, not just an existing session).
6. Founder types the exact confirmation phrase the system displays (this phrase is generated per-arming attempt, not a fixed string, to prevent copy-paste automation of the arming step itself).
7. System issues a short-lived arming token with an explicit expiry.
8. Arming is recorded as an audit event including every fact re-verified above.
9. If the arming token expires before automated execution begins, the system returns to `DISARMED` — it never silently re-arms.

## 4. During a live automated session

- Monitor the dashboard's emergency-state and mode badge continuously during the first sessions; do not treat this as fire-and-forget.
- Any watchdog halt (stale data, disconnect, reconciliation failure, repeated rejection, clock anomaly, storage corruption) moves the system to `HALTED` automatically — this is expected safe behavior, not a bug to bypass.
- A `HALTED` state requires manual Founder review before re-arming; there is no automatic clear.

## 5. Ending a session

- Prefer `disable-new-entries` before stopping the process, so any open position stays intact and future entries stop cleanly.
- Confirm `reconcile` shows a clean state before shutdown.
- Restart always comes up `DISARMED` (or whatever a specific later contract explicitly documents as the exception) — re-arming always requires repeating Section 3 in full, every time.

## 6. What this runbook does not cover

Emergency stop, flatten, and disconnect procedures live in
`TRL_EMERGENCY_RUNBOOK.md` — use that document, not this one, if something is
going wrong right now.
