## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-BLOCK-001 |
| Document Type | Blockers and External Prerequisites |
| Status | Active |
| Version | 1.1 |
| Date | 2026-08-01 |
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
| MT5 demo account fingerprint (login, broker company, server) | Phase 5 real `order_check`/`order_send` rehearsal, Phase 12.D–H | Not confirmed available | `mt5_execution_service.AccountFingerprintConfiguration` is unset by default; `build_order_intent` fails closed with `ACCOUNT_UNAVAILABLE` until a Founder-approved fingerprint is set via `TRL_MT5_DEMO_LOGIN`/`TRL_MT5_DEMO_COMPANY`/`TRL_MT5_DEMO_SERVER` environment variables. Automated tests use the fake adapter and are not blocked. The optional `MetaTrader5` Python package happens to already be installed in the current development environment (not installed by Phase 5 work), but no MT5 terminal process was running during the Phase 5 manual rehearsal, so the real adapter's connection check correctly failed closed with `TERMINAL_UNAVAILABLE` — a genuine order_check/order_send round trip has not been rehearsed |
| MT5 live account fingerprint (login, broker company, server) | Phase 5 live-mode allowlist config, Phase 9 live arming | Not provided | Software/tests/docs can be built without it; live arming cannot be rehearsed for real without it |
| Private authenticated HTTPS tunnel (e.g., Tailscale) or equivalent | Phase 8 private online deployment, Phase 12.K | Not confirmed installed | App will be built deployment-ready; cannot claim "online" until independently reachable over authenticated HTTPS |
| TradingView webhook signing secret / source allowlist | Phase 7 | Not provided | Contract and adapter can be built with a placeholder scheme; live intake needs a real secret before use |
| Founder decision on VIEWER/FOUNDER_OPERATOR credentials | Phase 8 authentication | Not provided | Password hash must be set by Founder, never generated/stored by Claude in the repo |
| FIB-001 exact numeric parameters (retracement/extension ratios, swing-detection rule, invalidation distance) | Phase 4 (R2-006 FIB-001 implementation), Phase 5 (MT5 execution) | Not provided | Correction pass (2026-07-31-004) removed a fabricated "previously approved" citation; a dated Decision Log entry with the real parameters is required before FIB-001 is implemented. Phase 5 (2026-08-01) independently re-checks `signal_strategy_registry.executable_status("FIB-001")` before ever reaching the MT5 adapter, so this blocker gates execution too, not just proposal generation |
| SMA-001 exact executable-geometry parameters (entry-zone rule, stop-placement rule, TP1-TP4 formula, target allocations, lookback window, rounding/tolerance behavior) | Phase 4 (R2-006 SMA-001 executable BUY/SELL proposals), Phase 5 (MT5 execution) | Not provided | Correction pass (2026-08-01) found the first Phase 4 implementation had invented a 20-bar swing-stop/1x-2x-3x-4x-target/25%-allocation geometry with no citable approval and removed it from the executable path; SMA-001's crossing *direction* remains exact R1-kernel parity and is recorded for research only (`STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`) until a dated Decision Log entry records an approved geometry. Phase 5 (2026-08-01) adds its own independent, defense-in-depth gate (`mt5_execution_service.EXECUTION_GEOMETRY_APPROVED_STRATEGIES`, currently empty) since the strategy registry alone does not block SMA-001 execution — only Role 3's pipeline-internal logic does, and a hand-built proposal object could otherwise bypass it |
| Tunnel technology confirmation (Tailscale vs. an equivalent authenticated tunnel) | Phase 8 deployment | Not confirmed | R2-008 contract names Tailscale only as an example; Founder should confirm the actual choice before implementation |

## Update rule

Add a row/entry the moment a phase discovers it cannot proceed further
without something only the Founder or an external system can provide. Do not
stop other phases because of one blocked item — record it here and continue
elsewhere.
