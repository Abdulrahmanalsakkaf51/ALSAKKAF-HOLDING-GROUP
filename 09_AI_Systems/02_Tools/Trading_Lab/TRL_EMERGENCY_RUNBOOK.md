# TRL Emergency Runbook

> **If you are reading this because something is actively wrong right now: go to Section 1 and act. Read the rest afterward.**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | Full-vision program, Phase 2 (procedure defined ahead of Phase 9 implementation) |
| Status | Design-time runbook — commands below are the target CLI/dashboard surface; will be verified word-for-word once implemented |

## 1. Immediate actions (do these first)

| Situation | Action |
|---|---|
| You want everything to stop submitting new trades right now, but existing positions can stay open | Run `disable-new-entries`, or click the equivalent dashboard control. This is the least destructive stop — it never touches an existing position. |
| A specific position is wrong and you want it closed now | Run `close-position <position-id>`, or use the dashboard's governed close control for that position. |
| You want every governed position closed and everything stopped | Run `emergency-flatten`, or the dashboard's global emergency-stop control. This is the global-stop button described in Phase 9 — it moves the system to `EMERGENCY_STOPPED`. |
| You suspect the connection to the broker is compromised, hung, or behaving strangely | Run `disconnect` after flattening/disabling as needed above. Do not leave an ambiguous connection open "to see what happens." |
| The dashboard itself is unreachable, but the host machine is up | Use `STOP_TRADING_LAB.ps1` to stop the local process. This does not touch broker-side positions directly — if positions need closing and the dashboard is unreachable, use the MT5 terminal's own interface on that machine to check/close positions, then investigate why the dashboard was unreachable before restarting it. |
| The host machine itself is unreachable (powered off, network-isolated, or otherwise inaccessible) while a live position may be open | This system cannot act for you in this situation — it isn't running. Check and, if necessary, close the position directly from the broker's own mobile app or web portal on a different device, using your own broker login (not this system). Once you regain access to the host, run `GET_TRADING_LAB_STATUS.ps1`, then `reconcile` before assuming anything about the system's state, and follow Section 4 (Post-incident steps) regardless of what you find. |

## 2. What `emergency-flatten` does and does not do

- Closes every open position and cancels every pending order that this
  system's own governed scheme opened (matched by magic number/comment —
  see the R2-007 contract Section 11). It does not touch a position opened
  manually by the Founder or by any other EA.
- Moves the arming state machine to `EMERGENCY_STOPPED`. Recovery from this
  state always requires a fresh, full re-arming (`TRL_LIVE_EXECUTION_RUNBOOK.md`
  Section 3) — there is no quick "resume" from an emergency stop.
- Records a full audit event including every position/order it acted on and
  the outcome of each individual close/cancel call.
- If a partial failure occurs (some positions close, others don't), the
  system reports exactly which ones failed and why — it never reports
  "flattened" unless every governed position is confirmed closed by
  reconciliation.

## 3. Watchdog-triggered halts (the system stopped itself)

The system moves to `HALTED` automatically, without any human action, when
it detects: stale market data, a broker disconnect, a reconciliation
failure, repeated order rejection, a clock anomaly, or storage corruption.
This is working as intended, not a malfunction to route around.

**Do not attempt to force-clear a `HALTED` state without understanding why it
halted.** Steps:

1. Read the halt reason from the dashboard/audit event.
2. Confirm the underlying condition is actually resolved (data is fresh
   again, connection is back, reconciliation is clean, clock is correct,
   storage validates).
3. Only then re-arm from scratch per `TRL_LIVE_EXECUTION_RUNBOOK.md`.

## 4. Post-incident steps

After any emergency stop or watchdog halt involving a live account:

1. Run `reconcile` and compare the resulting position/order/deal list against
   the broker's own terminal or web portal independently.
2. Export the immutable trade report (Phase 10) covering the incident window.
3. Record what happened and why in a dated entry — use the same style as
   `TRL_DECISION_LOG.md` — before resuming any automated activity.
4. If the cause was a defect in this system (not a market event), fix and
   re-test it under the normal testing gate (Phase 11) before the next live
   session; do not patch live and immediately re-arm in the same breath.

## 5. What this system will never do, even in an emergency

- It will never increase position size to "make back" a loss during or after
  an emergency stop.
- It will never automatically re-arm itself.
- It will never close or modify a position it did not open.
- It will never submit a real order from an automated test run, ever,
  including while diagnosing an incident.
