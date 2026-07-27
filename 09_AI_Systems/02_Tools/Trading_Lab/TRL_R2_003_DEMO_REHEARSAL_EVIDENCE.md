# TRL-R2-003 Local 4T Limited MT5 Demo Rehearsal Evidence

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-003-REHEARSAL-01 |
| Project | PRJ-017 — ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-003 |
| Evidence type | Local manual demo-terminal compatibility rehearsal |
| Status | PASSED — NARROW READ-ONLY DEMO-TERMINAL EVIDENCE |
| Date | 2026-07-27 |
| Owner and Founder Authority | Abdulrahman Yaseen Alsakkaf |
| Product boundary | LOCAL-ONLY — READ-ONLY — DEMO TERMINAL — NO ORDERS |
| Implementation commit tested | `35ef0a6` |
| Tested provider environment | 4T Limited MT5 demo terminal |
| Tested symbol | `XAUUSD` |

## Purpose and Evidence Boundary

This document records evidence reported from the separately authorized local manual rehearsal performed by Founder Abdulrahman Yaseen Alsakkaf on 2026-07-27. It records narrow compatibility evidence for the stated environment only. It does not claim broker certification, production readiness, strategy validity, investment suitability, profitability, live-account compatibility, or execution approval.

The evidence does not authorize another terminal connection, another broker, another symbol, a live account, trading, investment use, execution, or a future checkpoint.

## Founder Authorization

> “I, Abdulrahman Yaseen Alsakkaf, authorize one local read-only TRL-R2-003
> rehearsal using my operator-owned 4t limited MT5 demo terminal for the exact
> symbol XAUUSD. This authorizes market tick, specification, and M1/M5/H4/D1 bar
> retrieval only. It does not authorize account-data access, positions, history,
> orders, or execution.”

This authorization is preserved as given. It is not approval for a live account, trading, investment use, execution, other brokers, other symbols, or future checkpoints.

## Tested Environment

| Item | Recorded value |
|---|---|
| Operating system | Windows 64-bit |
| Python | 3.12.10 |
| MetaTrader5 Python package | 5.0.5735 |
| Terminal process | One running `terminal64` process |
| Terminal | Operator-owned 4T Limited MT5 demo terminal |
| Application | ALSAKKAF Trading Research Lab 2.0.0-r2.003 |
| Local dashboard | `127.0.0.1:8765` |
| Connector mode | `READ_ONLY` |
| Requested symbol | `XAUUSD` |
| Resolved symbol | `XAUUSD` |
| Requested timeframes | M1, M5, H4 and D1 |
| Requested bars | 500 per timeframe |

No account number, login, password, server credential, terminal credential, or personal account identifier is recorded.

## First Closed-Market Rehearsal

The first request was a successful fail-closed freshness observation:

| Item | Recorded result |
|---|---|
| Retrieval timestamp | `2026-07-26T21:26:36.718Z` |
| Connection status | `MT5_CONNECTED` |
| Freshness | `STALE_BY_THRESHOLD` |
| Reason | `MT5_STALE` |
| Diagnostic | The quote was stale by threshold; market-session state was unknown, so it was not treated as a broker failure. |
| Exact symbol resolution | Succeeded |
| Credential input accepted | `false` |
| Order capability | `false` |
| Candidate substitution | None |

This observation occurred during the provider's XAUUSD closed/daily break period and demonstrated the intended freshness fail-closed behavior. The application did not independently determine the market session: the recorded application status remained `MARKET_SESSION_UNKNOWN`.

No account, position, history, order, or execution operation was authorized.

## Fresh-Market Rehearsal

The successful fresh API request recorded:

| Item | Recorded result |
|---|---|
| API retrieval timestamp | `2026-07-27T14:38:56.746Z` |
| Connection status | `MT5_CONNECTED` |
| Connector mode | `READ_ONLY` |
| Freshness | `FRESH` |
| Reason | `MT5_READ_ONLY_SNAPSHOT_VALID` |
| Diagnostic | The read-only local MT5 snapshot passed validation. |
| Source type | `LOCAL_MT5_TERMINAL` |
| Local only | `true` |
| Requested symbol | `XAUUSD` |
| Resolved symbol | `XAUUSD` |
| Candidate symbols | None |
| Credential input accepted | `false` |
| Order capability | `false` |
| Market-session status | `MARKET_SESSION_UNKNOWN` |

The independent dashboard observation recorded:

| Item | Recorded result |
|---|---|
| Latest source tick time | `2026-07-27T14:41:15.000Z` |
| Dashboard retrieval time | `2026-07-27T14:41:16.651Z` |
| Visual observation | The Founder visually confirmed that the XAUUSD bid and ask were updating. |
| Local rendering | Broker-native tick and specification information rendered locally. |
| Commission | `UNKNOWN` because no governed commission source exists. |
| Strategy use | No strategy was applied to the local MT5 data. |
| Dashboard boundary | The dashboard explicitly displayed `DATA ONLY` and stated that no order capability exists. |

Observed bid, ask, price history, raw 500-bar arrays, copied market data, and screenshots are intentionally not included in the repository.

## Timeframe Evidence

| Timeframe | Status | Bars | Closed | Forming | Latest source time |
|---|---|---:|---:|---:|---|
| M1 | AVAILABLE | 500 | 499 | 1 | 2026-07-27T14:41:00.000Z |
| M5 | AVAILABLE | 500 | 499 | 1 | 2026-07-27T14:40:00.000Z |
| H4 | AVAILABLE | 500 | 499 | 1 | 2026-07-27T12:00:00.000Z |
| D1 | AVAILABLE | 500 | 499 | 1 | 2026-07-27T00:00:00.000Z |

Only the newest bar in each timeframe was marked `FORMING`; the preceding 499 bars in each timeframe were marked `CLOSED`. No missing bar was invented, filled, interpolated, or aggregated.

## Demonstrated Read-Only Boundary

Under the recorded conditions, the rehearsal demonstrated:

- Lazy installation/import compatibility with MetaTrader5 5.0.5735.
- Local terminal initialization.
- Exact case-sensitive symbol resolution.
- Freshness validation.
- Broker-native tick validation.
- Broker-native specification validation.
- M1, M5, H4 and D1 bar retrieval and validation.
- Closed/forming-bar separation.
- Localhost dashboard/API presentation.
- Stable fail-closed behavior during stale data.
- Credential-input rejection.
- Absence of order capability.

## Not Demonstrated or Authorized

The rehearsal did not demonstrate or authorize:

- Account information access.
- Balance or equity access.
- Position access.
- Pending-order access.
- Order or deal history.
- Order checking or calculation.
- Order submission, modification or cancellation.
- Live-account compatibility.
- Customer distribution.
- Broker certification.
- IC Markets or Equiti compatibility.
- Other MT5 brokers, terminals, symbols, computers or operating systems.
- Strategy selection, ranking, signals or advice.
- Stop-loss, take-profit or position-size recommendations.
- Paper fills joined to live MT5 data.
- Assisted or automated execution.
- Profitability, performance or market correctness.
- Regulatory, legal or security approval.

## Privacy and Data Retention

- Credentials were entered only by the operator inside MT5.
- No credentials were supplied to the Trading Lab or recorded in evidence.
- No account identifier is recorded.
- No raw broker bar dataset is retained.
- No screenshot is committed.
- No cloud service, telemetry or ALSAKKAF account was involved.
- No centralized customer-data custody exists.
- The Python package was installed locally outside Git and produced no repository change.
- The local server was stopped with `Ctrl+C`.
- Port 8765 had no listener after shutdown.
- Final Git status after the rehearsal was clean.

## Acceptance Conclusion

“TRL-R2-003-REHEARSAL-01 passed as narrow manual compatibility evidence for one
operator-owned 4T Limited MT5 demo terminal, one Windows environment and the
exact symbol XAUUSD. It confirms that the committed TRL-R2-003 connector can
retrieve and validate the authorized read-only market-data surface under the
recorded conditions. It is not broker certification, investment validation,
live-account approval, strategy approval or execution authorization.”

## Next-Checkpoint Boundary

The exact proposed next checkpoint is TRL-R2-004 — LOCAL GOVERNED NEWS AND ECONOMIC-EVENT COLLECTION. It remains unimplemented and unauthorized. This evidence document does not begin or authorize it.
