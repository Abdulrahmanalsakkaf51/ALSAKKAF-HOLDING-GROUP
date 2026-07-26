# TRL-R2-002 Local Governed Strategy Registry and Vault Contract

> **PAPER/RESEARCH ONLY — LOCAL PROCESSING — NO LIVE DATA — NO BROKER — NO EXECUTION**

## Document Information

| Field | Value |
|---|---|
| Project | PRJ-017 — ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-002 — Local Governed Strategy Registry and Vault |
| Status | Implemented source checkpoint; not approved for customer distribution |
| Date | 2026-07-26 |
| Registry schema | 1.0.0 |
| Backlog schema | 1.0.0 |

## 1. Founder product decision

PRJ-017 is a locally installed and locally processing research product. It has no ALSAKKAF customer account, login, authentication, subscription, payment system, cloud backend, central database, telemetry, analytics, centrally redistributed market data, central signals service, remote broker integration, credential transfer, customer financial-data transfer, or Atlas dependency. An operator may connect an operator-owned broker or data account only in a separately governed future local checkpoint. Strategy calculations, market processing, reports, and any future order proposals remain local.

Release 2 at this checkpoint uses only committed synthetic data and historical paper/research evaluation. No investment approval, profitability, market validity, live trading, or customer distribution approval is claimed.

## 2. Scope and exclusions

TRL-R2-002 adds a deterministic catalog of strategy metadata, immutable packaged definition identities, registry queries, a separate research backlog, a read-only local API document, and dashboard presentation.

The vault is not a password or credential vault, broker-account store, remote service, marketplace, plugin loader, optimizer, ranking engine, profitability selector, or execution system. This checkpoint does not implement MT5, live market data, news, regime selection, forward paper trading, order proposals, assisted execution, automated execution, packaging, accounts, subscriptions, payments, cloud services, or telemetry.

## 3. Module ownership

| Owner | Responsibility |
|---|---|
| `strategy_registry.py` | Exact schemas, enums, status combinations, registry construction, duplicate detection, deterministic ordering and filtering, status interpretation, research eligibility, stable reason codes, isolated returned values |
| `strategy_vault.py` | Exact two-file allowlist, strict UTF-8 JSON loading, duplicate JSON-key rejection, bounded size/depth/nodes/numerics, newline normalization, canonical JSON, SHA-256 identities, ordered manifest, bundle digest, packaged trust anchors, tamper/corruption failure |
| `strategy_catalog/SMA-001.1.0.0.json` | Data-only executable registry record for the existing Release 1 strategy |
| `strategy_catalog/research_backlog.json` | Data-only, non-executable research questions and risks |
| `service.py` | Cross-check against the exact application demo strategy configuration and produce the registry API document without financial evaluation |
| `server.py` | Exact allowlisted `GET /api/strategy-registry` route under existing localhost and security boundaries |
| Static dashboard | Read-only accessible presentation of validated API data |

Dependencies are acyclic: the registry depends on the vault, while the vault has no registry, service, server, or Release 1 dependency. Catalog JSON contains no Python, expression, import, callable, path, or code-loading field.

## 4. Executable record schema

Every executable record is an exact built-in JSON object with exactly these required fields and no others:

`strategy_id`, `strategy_version`, `display_name`, `family`, `description`, `implementation_status`, `approval_status`, `research_eligibility`, `supported_markets`, `supported_instrument_types`, `supported_timeframes`, `required_market_fields`, `required_indicators`, `parameter_schema`, `risk_characteristics`, `known_limitations`, `source_checkpoint`, `kernel_strategy_definition_hash`, and `record_schema_version`.

Identifiers and tokens use restricted uppercase forms; semantic versions use canonical three-part non-negative decimal form without leading zeroes. Hashes are lowercase 64-character hexadecimal SHA-256 values. Required strings are trimmed and non-empty. Set-like lists are non-empty, sorted, unique exact lists. Parameter names use restricted lowercase identifiers. Parameter specifications permit only `type`, `minimum`, `maximum`, `exclusive_minimum`, and `relation`; numeric booleans, subclasses, nonfinite values, inconsistent bounds, and unknown keys are rejected.

Only exact JSON-compatible built-ins are accepted. Files are limited to 131,072 bytes, 12 JSON levels, 4,096 nodes, 512-bit integers, and finite floating material no greater than `1e150` in magnitude. Duplicate JSON keys and duplicate strategy ID/version pairs fail closed. Path-like or executable text is rejected.

## 5. Status and approval model

Implementation status is exactly one of `IMPLEMENTED`, `PLANNED_NOT_IMPLEMENTED`, or `RETIRED`. Approval status is exactly one of `EXPERIMENTAL_RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `FOUNDER_REJECTED`, or `RETIRED`.

Supported combinations are explicitly closed. An implemented experimental or paper-eligible record may declare research eligibility; Founder-rejected, planned, and retired records cannot. Retirement requires both statuses to be `RETIRED`. No `INVESTMENT_APPROVED`, `LIVE_APPROVED`, or `PROFITABLE` state exists. Research eligibility authorizes only this local research engine boundary; it is not investment approval.

## 6. Deterministic identity model

Three identities remain distinct:

- **Release 1 kernel strategy-definition hash:** `e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955`. This belongs to the Release 1 executable definition and is neither replaced nor relabelled.
- **Registry-record digest:** SHA-256 over canonical sorted-key compact UTF-8 JSON plus one terminal LF. SMA-001 is `3cc2c876ad7c11d2244f9f71ab9a62cdc7f8baac0f5d3964173faa4d9e7e4878`.
- **Vault bundle digest:** SHA-256 over an ordered manifest stream containing explicitly bounded normalized repository-relative path, normalized byte length, normalized bytes, and end boundaries. It is `62a549288ab65fd543f7550416c96f01d65a3ecf3f128aa7b31b2de1ddc21d7b`.

CRLF and bare CR normalize to LF before packaged-byte and bundle identities. UTF-8 decoding is strict. The backlog canonical digest is `5029263efdb47563852ba93733f6d84a2cb4c757d32e57a29a604b952ec75a63`. The ordered manifest exposes normalized byte length, normalized file digest, and canonical JSON digest without exposing an absolute filesystem path.

## 7. SMA-001 installed record

The executable registry contains exactly `SMA-001` version `1.0.0`, family `SMA_CROSS_LONG_ONLY`: **SMA Close Crossing Long-Only Research Rule**. It uses completed-bar closes. Entry occurs only on a fast-SMA transition from at-or-below to above the slow SMA; exit occurs only on the inverse transition. Any hypothetical fill is deferred to the next validated bar open.

The record declares the committed daily synthetic equity research fixture, required OHLCV fields, the simple moving average indicator, `fast >= 1`, `slow >= 2`, `fast < slow`, and `0 < paper_size_pct <= 5`. It records long-only, one-instrument, daily-fixture, and no-validity/no-profit limitations. Its status is `IMPLEMENTED` / `EXPERIMENTAL_RESEARCH_ONLY`, and it is eligible only for local research execution. The service cross-checks its ID, version, family, constraints, Release 1 checkpoint, and kernel definition hash against the existing demo configuration before exposure.

## 8. Research backlog boundary

The backlog contains nine planned families: M1/M5 short-horizon trend; bullish/bearish candle rejection; support/resistance rejection; H4 swing; D1 position; market-session opening; Fibonacci retracement/extension; news and macro events; and regime detection/strategy selection.

Every entry uses the separate `BACKLOG-...` namespace, has status exactly `PLANNED_NOT_IMPLEMENTED`, and has `execution_eligible` exactly `false`. It contains questions, future data needs, and principal risks—no invented trading formula or profitable parameter. Backlog entries are never included by executable registry queries and cannot pass eligibility.

## 9. Fail-closed contract

The stable reason codes are:

- `REGISTRY_VALID`
- `REGISTRY_FILE_MISSING`
- `REGISTRY_UNEXPECTED_FILE`
- `REGISTRY_INVALID_UTF8`
- `REGISTRY_INVALID_JSON`
- `REGISTRY_SCHEMA_INVALID`
- `REGISTRY_DUPLICATE_STRATEGY`
- `REGISTRY_STATUS_COMBINATION_INVALID`
- `REGISTRY_IDENTITY_MISMATCH`
- `REGISTRY_BUNDLE_DIGEST_MISMATCH`
- `REGISTRY_RESEARCH_ELIGIBLE`
- `REGISTRY_NOT_RESEARCH_ELIGIBLE`
- `REGISTRY_STRATEGY_NOT_FOUND`

Any load failure discards the entire snapshot, exposes zero executable strategies and no partial backlog or manifest, does not run financial evaluation, and does not fall back to a default. Unknown ID/version queries return a not-found value rather than leaking an exception.

## 10. API and dashboard

`GET /api/strategy-registry` returns health, schema version, counts, the installed strategy envelope and identities, vault provenance, the separate backlog, closed capability boundaries, and stable reason codes. Output uses the server's deterministic JSON. It exposes only normalized catalog-relative paths.

The existing literal `127.0.0.1` bind, Host-header validation, decoded-path traversal rejection, exact route allowlists, GET-only method boundary, no-store behavior, CSP, frame protection, referrer policy, permissions policy, and content-type controls remain unchanged. No write API exists.

The dashboard shows health, counts, bundle identity, SMA metadata, declarations, parameters, limitations, both strategy hashes, and clearly labelled backlog cards plus an accessible table. It states that the registry does not choose the best strategy, no strategy is investment-approved, and live data, broker, and execution capabilities do not exist. Assets remain local; keyboard focus, semantic landmarks, and reduced motion are preserved.

## 11. Tests and acceptance evidence

`test_strategy_registry.py` covers exact schemas and types, identifiers and semantic versions, duplicates and ordering, unsafe content, statuses, Release 1 identity matching, deterministic canonical and bundle identities, newline parity, missing/unexpected/corrupt/tampered files, zero-partial-state failure, query/filter/eligibility behavior, output isolation, backlog separation, API methods and traversal, dashboard accessibility, capabilities, prohibited dynamic/network surfaces, two-run Release 1 semantic parity, input immutability, and artifact absence.

Acceptance commands run with `PYTHONDONTWRITEBYTECODE=1`, `-B`, and `-W error`. Direct acceptance evidence is 132/132 Release 1 tests, 23/23 application tests, and 32/32 registry tests; combined discovery is 187/187. Required evidence also includes exact semantic hashes and outcomes, `git diff --check`, untracked-file whitespace/final-newline checks, and an empty bytecode/cache/generated-report scan.

## 12. Release 1 compatibility

No Release 1 facade, core module, test, sample, generated evidence, contract, architecture record, engine manifest, or engine source is changed. The registry is metadata over the existing strategy and does not replace it. The committed input hash, configuration hash, strategy-definition hash, engine digest, run ID, outcome, accounting semantics, cash, equity, and semantic digest remain Release 1 acceptance invariants.

## 13. Next-checkpoint boundary

TRL-R2-003 may be proposed only as a **local MT5 read-only market-data connector**: operator-owned local terminal/account access, explicit allowlisted symbols and timeframes, read-only historical/current quote acquisition, deterministic local normalization and provenance, bounded freshness/error states, and no credential export. It must not submit, modify, cancel, propose, or simulate orders; access positions, balances, or reports beyond any separately approved minimum; collect news; select or optimize strategies; start forward paper trading; add cloud/accounts/telemetry; or alter Release 1 semantics. No part of that connector is implemented by TRL-R2-002.
