# TRL MT5 Local Read-Only Setup Guide

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-003-MT5-SETUP-001 |
| Document Type | Local Operator Setup Guide |
| Status | Active for separately authorized manual rehearsal |
| Version | 1.1 |
| Date | 2026-07-27 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-003 - Local MT5 Read-Only Market-Data Connector |

## Safety Boundary

This checkpoint reads market data only from MetaTrader 5 installed on the same PC. It cannot inspect accounts, balances, positions, or orders, and it cannot propose, check, send, modify, or cancel an order. It does not apply a strategy to MT5 data.

PRJ-017 never requests a broker password, investor password, login number, broker server address, or API key. Authenticate directly inside MetaTrader 5. Never enter broker credentials into PRJ-017 or its command line.

## Local Prerequisites

For a later separately authorized manual integration rehearsal:

1. Install the broker-supported MetaTrader 5 terminal locally.
2. Open MetaTrader 5 and log into the intended operator-owned demo account directly in the terminal.
3. Confirm that the intended exact symbol is visible in Market Watch. Use the broker's spelling and suffix exactly.
4. Keep the PC and MetaTrader 5 running while the local dashboard reads data.
5. Install the official optional `MetaTrader5` Python package only under a separate authorization and local dependency procedure. This checkpoint does not install it.

Broker feeds, symbol names, suffixes, specifications, market sessions, timestamps, tick availability, and spreads differ. A synthetic connector test is not broker certification.

Offline tests model official-package object shapes, but compatibility with an installed official package and real terminal remains unverified until the separately authorized manual rehearsal.

## Start Ordinary Synthetic Mode

From the repository root in Windows PowerShell:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app
```

This is the default. It does not import the optional MT5 dependency or initialize a terminal. The Market connection area reports `MT5_DISABLED`, while the committed synthetic dashboard remains available.

## Start Explicit MT5 Read-Only Mode

After the separate manual-rehearsal authorization and prerequisites, launch with an exact broker symbol:

```powershell
python -B -W error 09_AI_Systems\02_Tools\Trading_Lab\trading_lab_app --enable-mt5-read-only --mt5-symbol XAUUSD --mt5-timeframes M1,M5,H4,D1 --mt5-bars 500
```

Replace `XAUUSD` only with the exact symbol visible in that terminal, such as an exact broker-suffixed name. Do not guess or remove a suffix. The application requests that exact symbol first and scans a bounded inventory only for candidate hints when exact information is unavailable or mismatched; it never silently chooses another symbol. Bar count must be from 1 through 2,000. Only M1, M5, H4, and D1 are accepted.

The dashboard continues to bind only to:

```text
http://127.0.0.1:8765/
```

## Interpret Connection States

| State | Operator interpretation |
|---|---|
| `MT5_DISABLED` | Ordinary synthetic mode; no MT5 attempt occurred |
| `MT5_DEPENDENCY_MISSING` | The official optional local package is not present |
| `MT5_INITIALIZATION_FAILED` | Confirm MT5 is running and authenticated directly in MT5 |
| `MT5_SYMBOL_NOT_FOUND` | No exact match; inspect any candidate hints, then relaunch with one exact chosen name |
| `MT5_SYMBOL_AMBIGUOUS` | Several hints exist; inspect Market Watch and choose explicitly |
| `MT5_SYMBOL_NOT_VISIBLE` | Make the exact symbol visible in Market Watch and relaunch |
| `MT5_TICK_UNAVAILABLE` | No broker tick was returned; no live value is displayed |
| `MT5_TICK_CLOCK_SKEW` | Tick time is more than 5 seconds after retrieval completion; the snapshot is withheld |
| `MT5_BAR_DATA_UNAVAILABLE` | One or more requested broker timeframes returned no bars |
| `MT5_STALE` | Quote age exceeds the local threshold; the market session is unknown, so closure or feed failure is not inferred |
| `MT5_PROVIDER_INCOMPATIBLE` | One or more required MT5 timeframe constants are missing or invalid; no bars are read |
| `MT5_PROVIDER_ERROR` | A local provider operation failed; sensitive provider text is withheld |
| `MT5_READ_ONLY_SNAPSHOT_VALID` | The complete read-only snapshot passed strict validation |

Candidate aliases are discovery hints only. `GOLD`, `XAUUSD`, and suffixed names are never assumed financially identical.

## Interpret Tick, Spread, and Bars

Bid and ask are broker-native values. Raw spread price is checked ask minus bid; spread points use the broker's valid positive point. The separate broker-reported spread is displayed when available. Commission remains unknown. PRJ-017 does not add Release 1 costs, estimate profitability, or claim executable pricing.

`retrieval_timestamp_utc` is captured once after the final requested market-data read. A tick up to 5 seconds ahead reports `CLOCK_SKEW_WITHIN_TOLERANCE`, a zero nonnegative age, and its separate future-skew magnitude. A tick farther ahead fails closed as `MT5_TICK_CLOCK_SKEW`; PRJ-017 never labels a negative age ordinarily fresh.

Each broker-provided timeframe remains separate. `CLOSED` means the bar belongs to a completed interval. Only the newest bar can be `FORMING`, and only while its interval is still open. PRJ-017 does not invent, fill, interpolate, or aggregate missing bars.

## Stop the Local Session

Press `Ctrl+C` in the PowerShell window. The dashboard closes its localhost socket. Each connector request also closes its initialized Python integration session; it does not log the operator out of MetaTrader 5.

## Troubleshooting Without Credentials

- Verify the MT5 terminal and PC remain running.
- Verify authentication and connection state inside MT5, not inside PRJ-017.
- Verify the exact symbol is visible in Market Watch.
- Relaunch with the exact displayed symbol and only supported timeframes.
- Reduce the bounded bar count if the terminal has limited local history.
- Treat stale data as a freshness observation while session state remains unknown.
- Do not paste terminal paths, usernames, account numbers, or credentials into issue notes or browser fields.

This checkpoint cannot place an order under any setup state.
