# TRL-R2-003 Local MT5 Read-Only Connector Contract

## Document Information

| Field | Value |
|---|---|
| Document ID | TRL-R2-003-MT5-CONTRACT-001 |
| Document Type | Governed Application Contract |
| Status | Implemented for source validation |
| Version | 1.1 |
| Date | 2026-07-27 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-003 - Local MT5 Read-Only Market-Data Connector |

## Founder Local-Only Decision

PRJ-017 remains a locally installed and locally processing product. The dashboard binds only to literal `127.0.0.1`. The connector communicates only with an operator-owned MetaTrader 5 terminal on the same PC, and all normalization and presentation remain on that PC. There is no cloud, customer account, login, subscription, payment, telemetry, central market-data service, central customer database, remote broker connection, broker credential transfer, financial-state transfer, or Atlas runtime dependency.

Synthetic demonstration mode remains the default. Local MT5 read-only mode requires the explicit `--enable-mt5-read-only` launch control. This checkpoint retrieves data only. It does not use MT5 data for a signal, recommendation, strategy evaluation, paper fill, order proposal, assisted action, or automated action.

## Scope and Exclusions

Implemented scope is a broker-neutral foundation for exact MT5 symbols, bid and ask, raw spread, non-account symbol specifications, and separate broker-provided M1, M5, H4, and D1 bars. It distinguishes closed and forming bars and reports source identity, retrieval time, freshness, validation quality, and fail-closed reasons.

Excluded scope includes news, economic events, strategy selection, ranking, optimization, regime detection, live strategy signals, forward paper trading, broker positions, balances, orders, order proposals, assisted execution, automated execution, packaging, accounts, subscriptions, payments, cloud services, telemetry, and broker certification.

## Module Ownership

| Module | Ownership |
|---|---|
| `market_data.py` | Pure constants, bounds, candidate comparison, strict tick/specification/bar validation, forming-bar classification, UTC formatting, and deterministic snapshot schema |
| `mt5_connector.py` | Lazy optional dependency import, exact provider-method gate, provider lock, initialization/shutdown lifecycle, sanitized failures, symbol lookup, and atomic snapshot retrieval |
| `mt5_service.py` | Immutable local configuration, disabled-default behavior, application service facade, and injected provider/clock seam |
| `service.py` | Application documents for market connection and snapshot routes; no financial evaluation of MT5 data |
| `server.py` | Exact localhost API allowlist, HTTP boundary, deterministic JSON, no-store, and security headers |
| `app.py` | Bounded opt-in command-line controls and local server lifecycle |
| `static/index.html`, `static/styles.css`, `static/app.js` | Accessible, responsive local market-connection presentation with synthetic-dashboard isolation |

Dependencies are acyclic: pure normalization has no application dependency; the connector depends on normalization; the MT5 service depends on both; the existing application service and server depend on the MT5 service.

## Optional Dependency Boundary

The Python standard library remains the application baseline. The official `MetaTrader5` package is optional and is imported lazily inside `LocalMT5ReadOnlyConnector` only after a market snapshot is requested from an explicitly enabled service. Importing the package or starting the ordinary dashboard does not import the optional dependency, initialize MT5, or access a terminal. A missing dependency returns `MT5_DEPENDENCY_MISSING` and no price.

The checkpoint does not install the package, invoke a package manager, vendor a client, use a subprocess to operate MT5, or access the internet.

## Credentials and Provider-Method Boundary

The operator authenticates inside MetaTrader 5. PRJ-017 accepts and stores no MT5 login number, broker username, password, investor password, API key, broker server address, remote host, payment information, account number, or account name. The connector passes only a bounded `timeout` to `initialize`; it never passes a terminal path, login, password, or server.

The complete provider-method allowlist is:

| Method | Narrow purpose |
|---|---|
| `initialize` | Open the local Python integration session with a bounded timeout |
| `shutdown` | Close an initialized Python integration session |
| `last_error` | Retain only an integer error code for sanitized local troubleshooting |
| `symbols_get` | Inspect a bounded prefix only for candidate aliases after exact lookup fails |
| `symbol_info` | Attempt the exact requested broker symbol's non-account specification first |
| `symbol_info_tick` | Read the exact selected broker symbol's current tick |
| `copy_rates_from_pos` | Read bounded broker bars for an allowlisted timeframe |

Forbidden operations include `account_info`, `positions_get`, `positions_total`, `orders_get`, `orders_total`, `order_check`, `order_send`, `history_orders_get`, `history_orders_total`, `history_deals_get`, and `history_deals_total`. `symbol_select` is also forbidden because it changes Market Watch state. There is no request-building wrapper, order model, order endpoint, or dormant execution function.

Provider constant access has a separate fixed allowlist containing only `TIMEFRAME_M1`, `TIMEFRAME_M5`, `TIMEFRAME_H4`, and `TIMEFRAME_D1`. The connector accepts no caller-supplied attribute name. All four identifiers must be positive, distinct, non-boolean integers no greater than 2,147,483,647. Invalid or missing constants return `MT5_PROVIDER_INCOMPATIBLE` before any bar request. Human interval durations remain separately defined and are not provider identifiers.

## Connection Lifecycle

1. Validate the exact symbol, unique timeframe list, bar count, timeout, and stale threshold before provider access.
2. Lazily resolve the injected fake or optional official provider.
3. Acquire the connector lock and retain it through the complete provider session.
4. Call `initialize(timeout=...)` without credentials, path, remote host, or broker server.
5. Fail closed on initialization failure and retain only a numeric `last_error` code when safely available.
6. Call `symbol_info(requested_symbol)` before any bounded candidate inventory read.
7. Validate the exact specification and tick, resolve all four allowlisted provider timeframe constants, and capture every requested timeframe directly.
8. Capture one timezone-aware UTC completion reference immediately after the final market-data read and use it for every bar and freshness calculation.
9. Call `shutdown` in `finally` after every successfully initialized session, including validation and provider failures.
10. If shutdown fails, withhold the otherwise obtained snapshot and return `MT5_PROVIDER_ERROR`.

The initialization timeout is bounded from 1,000 through 30,000 milliseconds and defaults to 5,000 milliseconds. Provider sessions cannot overlap across connector instances in the local application process.

## Symbol-Resolution Policy

The requested symbol must be 1 through 64 ASCII characters and may contain only letters, digits, dot, underscore, number sign, plus, or hyphen. Resolution first calls `symbol_info(requested_symbol)`. A result is exact only when its broker-reported name equals the requested string case-sensitively. A valid visible exact result is used directly, its original spelling is preserved, and `symbols_get` is not called merely to reconfirm it.

If exact information is absent or reports a different name, only then may bounded `symbols_get` candidate discovery compare uppercase alphanumeric forms. Prefix comparison finds suffix forms such as `XAUUSD.a`; `GOLD` and `XAUUSD` may be cross-listed only as candidate hints. A candidate is never selected, resolved, or claimed financially equivalent. One candidate remains `MT5_SYMBOL_NOT_FOUND`; multiple candidates are `MT5_SYMBOL_AMBIGUOUS`. The operator must choose one exact broker symbol on a later launch. At most 5,000 inventory entries are inspected and at most 20 sorted candidates are returned.

An exact symbol that is unavailable or not visible returns `MT5_SYMBOL_NOT_VISIBLE`. The operator must make it visible in MT5 Market Watch; PRJ-017 does not call `symbol_select`.

## Normalized Market Snapshot Schema

`TRL-MARKET-SNAPSHOT-1.0` has an exact top-level shape:

| Field | Meaning |
|---|---|
| `schema_version` | Stable schema identity |
| `source_type` | Local MT5 terminal, or the disabled synthetic-default boundary |
| `connector_mode` | Read-only MT5 or synthetic-default/MT5-disabled mode |
| `connection_status` | Stable connector state |
| `reason_code` | Stable success, quality, or failure reason |
| `requested_symbol` | Exact operator request, or null while disabled |
| `resolved_symbol` | Exact broker identity only after exact resolution |
| `candidate_symbols` | Bounded original broker names; never substitutions |
| `retrieval_timestamp_utc` | One timezone-aware UTC reference captured after the final market-data read |
| `tick` | Validated broker tick or null |
| `symbol_specification` | Allowlisted non-account fields or null |
| `timeframe_series` | Requested timeframe documents with status, counts, and bars |
| `data_quality` | Validity, freshness, future-tick skew, session knowledge, threshold, sanitized code, and diagnostic |
| `limitations` | Fixed boundary statements |

The result never copies arbitrary provider attributes. It excludes installation paths, Windows usernames, account names and numbers, credentials, balance, equity, margin, positions, orders, and machine identifiers.

## Tick and Spread Policy

Tick fields are source UTC timestamp, source timestamp milliseconds when available, bid, ask, last when available, volume when available, raw `spread_price`, and computed `spread_points`. Bid and ask must be finite, non-boolean numbers and ask must be greater than or equal to bid. Last must be finite when present; volume must be finite and nonnegative when present.

The fixed maximum future-tick tolerance is 5 seconds and is not configurable. A source `time` or `time_msc` more than 5 seconds after retrieval completion fails closed as `MT5_TICK_CLOCK_SKEW`. A future tick within 5 seconds preserves its source timestamp, reports zero nonnegative age, records the positive magnitude in `future_tick_skew_seconds`, and reports `CLOCK_SKEW_WITHIN_TOLERANCE` rather than ordinary `FRESH`. No negative age is exposed as fresh.

`spread_price` is checked `ask - bid`. Points are calculated only with a finite positive broker point. The broker-reported symbol spread remains separate as `broker_reported_spread_points`. Values are not clamped. Release 1 slippage and commission assumptions are not applied. Commission is null with `UNKNOWN_NO_GOVERNED_SOURCE`; profitability is not estimated.

The symbol specification contains only the exact symbol; safe bounded description and base/profit/margin currencies; digits; point; trade contract size; volume minimum, maximum, and step; stops and freeze levels; trade mode; and broker-reported spread points. Invalid digits, point, contract size, volume bounds, levels, mode, or spread fail closed as `MT5_INVALID_SYMBOL_SPECIFICATION`.

## Bar, Timeframe, and Forming-Bar Policy

Only M1, M5, H4, and D1 are supported. Their request identifiers come from the four fixed provider constant names; numeric identifiers are not duplicated in production. Each timeframe is requested directly and separately from the broker. There is no aggregation between timeframes. Each bar contains UTC timestamp, open, high, low, close, tick volume, spread, real volume, and `CLOSED` or `FORMING` state.

Numbers must be finite and non-boolean. High must be at least open, low, and close; low must be at most open, high, and close. Volumes and spread must be nonnegative. Timestamps must be strictly increasing and unique in provider order. Invalid data empties the entire returned bar surface and reports `MT5_INVALID_BAR_DATA`; it is never partially labelled valid.

Only the newest bar can be `FORMING`, and only when the single retrieval-completion reference is within the interval beginning at that broker bar timestamp. A historical newest bar is `CLOSED`. Missing bars are not invented, forward-filled, interpolated, or aggregated. Empty data returns `MT5_BAR_DATA_UNAVAILABLE`. The per-timeframe maximum is 2,000 bars, and CLI/API response volume is bounded by that request limit.

## Data Quality and Fail-Closed Reasons

Stable connector and quality states are:

| Status or reason | Meaning |
|---|---|
| `MT5_DISABLED` | Synthetic default; the connector was not enabled |
| `MT5_DEPENDENCY_MISSING` | Optional local package unavailable |
| `MT5_INITIALIZATION_FAILED` | Local terminal integration did not initialize |
| `MT5_CONNECTED` | Provider session connected and returned a validated or quality-qualified snapshot |
| `MT5_SYMBOL_NOT_FOUND` | No exact request was resolved; zero or one candidate may be shown |
| `MT5_SYMBOL_AMBIGUOUS` | Multiple candidate hints require an operator choice |
| `MT5_SYMBOL_NOT_VISIBLE` | Exact symbol must be made visible in Market Watch |
| `MT5_TICK_UNAVAILABLE` | No tick; no price is fabricated |
| `MT5_BAR_DATA_UNAVAILABLE` | One or more requested timeframe series are empty |
| `MT5_INVALID_TICK` | Tick validation failed |
| `MT5_TICK_CLOCK_SKEW` | Tick seconds or milliseconds exceed the fixed future tolerance; snapshot withheld |
| `MT5_INVALID_SYMBOL_SPECIFICATION` | Specification validation failed |
| `MT5_INVALID_BAR_DATA` | Bar validation failed and all bar data was withheld |
| `MT5_STALE` | Valid quote exceeds the injected threshold; not itself a broker failure |
| `MT5_PROVIDER_INCOMPATIBLE` | Required provider timeframe constants are missing or invalid; no bars requested |
| `MT5_PROVIDER_ERROR` | Provider or shutdown exception; details sanitized |
| `MT5_READ_ONLY_SNAPSHOT_VALID` | Complete read-only snapshot passed validation |

Freshness is calculated from the retrieval-completion reference and tick source times. `FRESH` and `STALE_BY_THRESHOLD` are reported with the numeric age and threshold. `CLOCK_SKEW_WITHIN_TOLERANCE` is explicit and includes the positive future skew separately while age remains zero. Session state is always `MARKET_SESSION_UNKNOWN` in this checkpoint; stale data therefore does not claim that the market or broker failed.

## API and Dashboard Integration

Exact new routes are `GET`/`HEAD /api/market-connection` and `GET`/`HEAD /api/market-snapshot`. Disabled mode returns a valid `MT5_DISABLED` document. Existing synthetic and registry APIs remain compatible. Other methods receive HTTP 405; paths remain exact and traversal-protected. JSON is deterministic sorted-key compact UTF-8 with a final LF.

The dashboard shows local mode/status, requested and resolved symbols, candidates, source boundary, bid, ask, raw spread, point, digits, contract and volume limits, stops/freeze levels, broker spread, M1/M5/H4/D1 counts and availability, source and retrieval times, freshness, forming/closed explanation, and unknown commission. It states that no strategy is applied to MT5 data and no order capability exists. MT5 failure does not hide or relabel the existing synthetic dashboard.

## Security and Privacy

The server binds only to literal `127.0.0.1`, validates local Host headers, uses an exact static/API path allowlist, rejects traversal, exposes GET/HEAD only on market routes, sends no-store and security headers, and uses no external resource. There is no outbound HTTP client, telemetry, remote host control, credential argument, or broker server argument.

Provider exception text is never returned. Only a fixed diagnostic and integer error code may be shown. Input provider objects are read and copied without mutation; only explicitly normalized fields enter the response.

## Tests and Evidence

`test_mt5_connector.py` uses an injected data-source fake and controlled clocks. It covers default disablement, missing dependency, initialization failure and timeout, exact method and constant access, forbidden nonuse, shutdown, sanitized exceptions, source nonmutation, thread serialization, exact-first and bounded candidate resolution, clock-skew tolerance, completion-time boundary crossing, provider-specific and invalid timeframe identifiers, tick/specification/spread validation, namedtuple symbol/tick shapes, structured-array-like bars, numeric scalar subclasses, zero optional FX fields, unknown commission, bar counts and states, invalid/empty/partial bars, freshness and staleness, deterministic schema, APIs, HTTP methods, traversal, dashboard language, capabilities, Release 1 parity, registry/vault parity, and artifact absence.

Automated validation neither imports the real optional package nor connects to a real terminal, broker, live feed, news service, or network. Compatibility with an installed official package and real terminal remains unverified until a separately authorized manual rehearsal; no broker is certified by these tests.

## Release 1 and TRL-R2-002 Compatibility

Release 1 facade, core, tests, samples, contracts, financial semantics, source manifest, hashes, engine digest, run ID, and synthetic result remain unchanged. MT5 snapshots never call Release 1 evaluation. The TRL-R2-002 strategy registry, immutable catalog, backlog, trust anchors, registry record digest, research backlog digest, vault bundle digest, installed count, and executable count remain unchanged.

## No Broker Certification Claim

Synthetic inventories resembling exact, suffixed, alternative, ambiguous, missing, and unavailable symbols prove connector logic only. They do not certify IC Markets, Equiti, any account type, any terminal build, or every MetaTrader 5 broker. Broker symbols, feeds, sessions, spreads, specifications, and availability differ.

## Next-Checkpoint Boundary

TRL-R2-004 may be proposed only as a local official news and economic-event collector with explicit official sources, licensing/provenance review, point-in-time UTC normalization, revision awareness, bounded local storage, freshness/quality states, no credentials beyond separately approved public-source needs, no cloud redistribution, and no link to strategies, signals, paper fills, proposals, or orders. TRL-R2-003 does not begin that work.
