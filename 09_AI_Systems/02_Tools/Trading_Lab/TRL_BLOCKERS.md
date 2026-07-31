## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-BLOCK-001 |
| Document Type | Blockers and External Prerequisites |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-31 |
| Owner | Abdulrahman Alsakkaf |

# TRL Full-Vision Program — Blockers and External Prerequisites

Tracks known defects (from independent review) and external prerequisites
that gate specific phases. A missing external prerequisite blocks only the
phase(s) listed — all other independent work continues.

## Known defects

None outstanding. Phase 1 independent review found one defect (`paper_service.py`
`_process_open_positions` zero-quantity TP target incorrectly aborted TP4
closure) and fixed it with a regression test. See `TRL_DECISION_LOG.md`
entry 2026-07-31-003.

## External prerequisites

| Prerequisite | Blocks | Status | Notes |
|---|---|---|---|
| MT5 demo account credentials | Phase 5 manual rehearsal, Phase 12.D–H | Not confirmed available | Needed only for manual rehearsal; automated tests use mocks/fakes and are not blocked |
| MT5 live account fingerprint (login, broker company, server) | Phase 5 live-mode allowlist config, Phase 9 live arming | Not provided | Software/tests/docs can be built without it; live arming cannot be rehearsed for real without it |
| Private authenticated HTTPS tunnel (e.g., Tailscale) or equivalent | Phase 8 private online deployment, Phase 12.K | Not confirmed installed | App will be built deployment-ready; cannot claim "online" until independently reachable over authenticated HTTPS |
| TradingView webhook signing secret / source allowlist | Phase 7 | Not provided | Contract and adapter can be built with a placeholder scheme; live intake needs a real secret before use |
| Founder decision on VIEWER/FOUNDER_OPERATOR credentials | Phase 8 authentication | Not provided | Password hash must be set by Founder, never generated/stored by Claude in the repo |

## Update rule

Add a row/entry the moment a phase discovers it cannot proceed further
without something only the Founder or an external system can provide. Do not
stop other phases because of one blocked item — record it here and continue
elsewhere.
