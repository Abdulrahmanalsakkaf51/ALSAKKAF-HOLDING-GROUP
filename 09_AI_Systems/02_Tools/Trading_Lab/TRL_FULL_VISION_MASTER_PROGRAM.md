## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-FULLVISION-001 |
| Document Type | Master Delivery Program |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-31 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS / Trading Lab (PRJ-017) |
| Related Protocol | OPS-001, CLAUDE-001 |

# TRL Full-Vision Delivery Program — Master Tracker

## Purpose

Tracks the multi-phase delivery of the ALSAKKAF Trading Lab full vision:
governed signal generation, MT5 broker execution (demo and live-capable),
private online/mobile operation, automation with arming controls,
reconciliation, and full documentation — starting from the TRL-R2-005
forward paper timeline work.

## Governance note

This program text requested auto-commit-per-phase and auto-push where a
remote is available. Project instructions in `CLAUDE.md` (which explicitly
override default behavior) require Founder approval before significant
changes, before every commit, and before every push. Where the two conflict,
`CLAUDE.md` wins: commits will be proposed with an exact `git diff`/status
summary and will wait for explicit Founder approval before being created;
pushes will wait for explicit Founder approval separately. See
`TRL_DECISION_LOG.md`.

No automated process in this program will submit a real-money broker order.
Live execution capability is implemented and rehearsed on MT5 demo only;
the Founder performs the first real-money activation personally.

## Phase index

| Phase | Title | Status |
|-------|-------|--------|
| 0 | Verify backup and repository | Complete (2026-07-31) |
| 1 | Independently review and close TRL-R2-005 | Complete and pushed (2026-07-31, commit `49fa62c`) |
| 2 | Create full-vision delivery branch + contracts | Complete and pushed (2026-07-31, commit `ffcdd74`) |
| 3 | Operating-mode state machine | Implemented, corrected after Founder review removed a legacy-flag authority bypass, 447/447 tests passing twice, manually rehearsed twice; not yet committed |
| 4 | Governed signal intelligence (TRL-R2-006) | Not started |
| 5 | MT5 execution adapter (TRL-R2-007) | Not started |
| 6 | Controlled basket execution | Not started |
| 7 | Optional TradingView signal intake | Not started |
| 8 | Private online and mobile application (TRL-R2-008) | Not started |
| 9 | Live-automation arming and emergency controls | Not started |
| 10 | Operational reconciliation and observability | Not started |
| 11 | Testing | Ongoing (baseline: 391 tests passing twice under -B -W error) |
| 12 | Manual rehearsals | Not started |
| 13 | Documentation | Ongoing |
| 14 | Final repository closeout | Not started |

Detail for the active phase lives in `TRL_CONTINUATION_STATE.md`. Decisions
and their reasoning live in `TRL_DECISION_LOG.md`. External prerequisites
and known defects live in `TRL_BLOCKERS.md`.

## Prohibited actions (program-wide)

- `git reset --hard`, `git clean`, broad `git restore`
- Discarding current R2-005 work
- Modifying ASC Operations Hub or any other ALSAKKAF project
- Exposing broker credentials in source, logs, URLs, or browser responses
- Binding a trading mutation interface directly to a public network interface
- Unauthenticated order endpoints; browser calling MT5 `order_send` directly
- Martingale, loss-recovery sizing, averaging down outside one approved basket
- Hiding unrealized losses; treating LLM output as a direct broker order
- Real-money trades during automated testing
- Deriv digit/binary-contract execution (out of scope for this program)
- Claiming production completion when an external prerequisite is missing
