# TRL-R2-011 Deterministic Market Data Fabric and Replay V0 Contract

> **RESEARCH ONLY — LOCAL ONLY — NO LIVE DATA — NO BROKER CALL EXISTS ANYWHERE IN THIS CONTRACT — NO EXECUTION AUTHORITY IS CREATED, GRANTED, OR IMPLIED**

Product component working name: **TRL CORTEX DATA FABRIC V0**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-011 (contract-authoring checkpoint only; not an implementation checkpoint; not Phase 7) |
| Status | **Contract-only draft, awaiting Founder review, now including one Founder correction pass.** The initial draft transcribed the Founder's fully specified requirements into the repository's governed-contract format. The Founder review pass that followed found seven implementation-readiness gaps — no separate content-addressed dataset store (a journal event would otherwise have to embed up to 250,000 bar records), deferred exact numeric bounds, under-specified hash-input field lists, undefined replay-session-reuse-by-status behavior, unsafe corrupted-journal semantics, unbounded inspection output, and an imprecise replay-bound summary — and this pass corrects all seven in place: a new non-governed `TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1` storage container (Section 10.6) separate from the journal; every previously deferred bound now fixed exactly (Section 18.1); an explicit ordered identity/hash field table per governed schema (Section 11); explicit replay-session-reuse behavior for every projected status (Section 14.4); explicit atomic replay-event-batch and cancellation semantics (Section 15.2); two distinct, safe corruption cases (Section 18.3); and bounded, paginated list/inspection output everywhere (Section 19). Five governed record schemas plus one non-governed storage envelope, non-circular deterministic identities, exact CSV import/grammar and bar-validation rules, exact gap-detection and replay-step formulas, a deterministic step-driven replay model, a separate append-only hash-chained journal, a narrow `market_data_research` capability amendment, an 11-command CLI, six read-only HTTP routes, and precisely scoped blockers. Implementation has not started. This checkpoint's exact staged/committed/pushed state is, per this program's Git-authoritative convention, always read from `git rev-parse HEAD`/`git status` directly rather than restated here as a fixed value. |
| Depends on | `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (`ModeService` authority; narrowly amended by this checkpoint, Section 20), TRL-R2-010 (Market Intelligence V0 / TRL CORTEX V0 — complete, unchanged; this contract's Section 23 defines the exact, currently-empty compatibility boundary between the two) |
| Feeds | No phase. This checkpoint is local-only, research-only, and does not authorize, gate, or advance Phase 7 or any later phase. Any future conversion of a replay window into an R2-010 analysis input, an automatic evidence generator, or any execution artifact requires a separate, explicitly Founder-approved handoff contract (Sections 4, 23, 24). |

---

## 0. Numbering and classification decision

This contract is numbered **TRL-R2-011**. It does not reuse, rename, or
reinterpret any existing `TRL-R2-0XX` document: R2-005 (paper engine),
R2-006 (signal intelligence), R2-007 (MT5 execution), R2-008 (private
online operations, still not started), R2-009 (controlled basket execution,
Phase 6, complete), and R2-010 (Market Intelligence V0 / TRL CORTEX V0,
informational Phase 6A, complete) are all unrelated checkpoints and remain
unchanged.

**This checkpoint is not a Phase in the existing 0–14
`TRL_FULL_VISION_MASTER_PROGRAM.md` phase table**, for the same reason
R2-010 was not: inserting it into that sequence would require renumbering
every phase from 7 onward. It is recorded as a new, independent,
informational row — **Phase 6B — Deterministic Market Data Fabric and
Replay V0 (TRL-R2-011)** — positioned informationally after Phase 6A to
reflect authoring order. It is not a prerequisite for, and does not block,
gate, or reorder, Phases 7 through 14. It is explicitly not Phase 7
(optional TradingView signal intake remains a separate, unrelated,
not-started checkpoint).

## 1. Checkpoint purpose

TRL CORTEX DATA FABRIC V0 creates the governed local historical-data and
deterministic-replay foundation required by future TRL CORTEX intelligence
systems. It governs the future ability to import bounded local historical
or synthetic market-bar data; strictly validate every imported bar;
normalize approved data into canonical immutable records; create a
deterministic dataset manifest; detect duplicates, out-of-order timestamps,
and data gaps; preserve source classification and logical provenance;
create deterministic local replay sessions; advance replay through explicit
governed steps; generate replay snapshots for inspection and future
research; preserve replay state through restart; and expose local CLI and
read-only HTTP/dashboard concepts. This checkpoint does **not** create
automatic evidence, opportunities, signals, orders, or execution
instructions of any kind.

## 2. Checkpoint classification

**Is:** local-only, research-only, deterministic, historical- or
synthetic-data-only, non-live, non-automated, non-executing, append-only
and auditable, restart-stable, compatible with R2-010.

**Is not:** a live market feed, a broker-history connector, a TradingView
connector, an external API client, an automatic evidence generator, a
signal generator, a strategy, an execution system, a portfolio system, a
profitability claim, a data-quality guarantee, a data-vendor certification
system, or Phase 7.

## 3. Scope

In scope for the future implementation this contract authorizes (not this
checkpoint):

- Five governed record schemas plus one non-governed storage envelope
  (Section 10) with non-circular deterministic identities (Section 11).
- Strict local CSV import with exact header, size, row-count, and
  character-grammar rules (Section 7), exact bar-validation rules
  (Section 9), and an exact `Decimal`-only numeric policy with no silent
  correction (Section 8).
- A separate, content-addressed, immutable dataset store, distinct from the
  compact journal (Sections 10.6, 17).
- Deterministic dataset-reuse behavior keyed on content and logical source
  reference (Section 12).
- Exact-multiple-only gap detection with no automatic filling (Section 13).
- A deterministic, step-driven (never wall-clock-driven) replay model with
  explicit session-reuse-by-status behavior (Section 14), atomic
  replay-event batching (Section 15), and a bounded, dataset-order-
  preserving replay window (Section 16).
- A separate, append-only, hash-chained Market Data and Replay journal, with
  a closed event vocabulary, exact bounded limits, cross-process
  owner-token locking, and two distinct, safe corruption cases
  (Section 18).
- Bounded, paginated read-only list and inspection output everywhere
  (Section 19).
- A new, narrow `market_data_research` operating-mode capability, gating
  only the four listed mutations, with read-only operations available in
  every mode (Section 20).
- A local-only CLI (Section 21) and strictly read-only HTTP routes plus a
  dashboard concept (Section 22).
- Six new, precisely scoped blockers with full governed reason-code
  coverage (Section 24).

## 4. Hard safety boundary

The future R2-011 implementation must not, anywhere in its design or
future implementation:

- import `MetaTrader5`,
- connect to MetaTrader5,
- connect to a broker,
- connect to TradingView,
- call an external market-data API,
- call a news or macro API,
- call an AI model,
- use internet or network retrieval,
- request credentials,
- store a broker account identity,
- call `order_check`,
- call `order_send`,
- construct `RealMT5ExecutionAdapter`,
- generate a Phase 5 order intent,
- generate a Phase 6 basket,
- generate an R2-010 Opportunity Card automatically,
- create R2-010 evidence automatically,
- request execution confirmation,
- write to the Phase 5/6 execution journal,
- write to the R2-010 Market Intelligence journal,
- activate a live or automated operating mode,
- fill missing bars automatically,
- silently repair imported market data,
- silently sort out-of-order input,
- silently normalize an unsupported symbol,
- silently normalize an unsupported timeframe.

Any future live-data, evidence-generation, intelligence-handoff, or
execution capability requires another Founder-approved contract. This
contract authorizes none of them.

## 5. Approved V0 data sources

Exactly two V0 source classifications are approved:

1. **`SYNTHETIC_FIXTURE`** — committed or isolated synthetic research data;
   clearly labelled synthetic; no claim that values represent a real
   market; no broker identity; no account identity; no performance claim.
2. **`LOCAL_HISTORICAL_FILE`** — local user-supplied historical data;
   treated as unverified user input; not treated as authoritative market
   truth; no provenance guarantee; no automatic external verification.

No other source classification is approved in V0. A logical source
reference (`source_reference`) must be bounded text containing no
credential, no absolute filesystem path, no URL requiring retrieval, no
account number, no broker server, and no executable content. Maximum
length: **256 Unicode code points**.

## 6. Canonical instruments and timeframes

The same exact canonical V0 allowlists as R2-010, reused verbatim rather
than redefined:

- **Instruments:** `XAUUSD`, `NAS100`, `EURUSD`, `GBPUSD`, `USDJPY`.
- **Timeframes:** `M5`, `M15`, `H1`, `H4`, `D1`.

Stored values use the exact uppercase identifiers above; **no alias is
silently normalized**. Examples that must fail closed unless already
canonical: `XAU/USD`, `GOLD`, `US100`, `USTEC`, `EUR/USD`, `5M`, `60M`,
`1H`. These are research identifiers, not broker-native symbols. Expanding
either allowlist requires a later contract amendment.

## 7. V0 input format (local CSV)

V0 imports exactly one local CSV file per dataset.

**Exact required header, in exact order:**

```
instrument,timeframe,observed_at_utc,open,high,low,close,spread,tick_volume
```

### 7.1 File- and row-level CSV requirements

- strict UTF-8, no BOM, comma delimiter;
- header required, exact header names, exact header order; duplicate or
  additional header names fail closed;
- no unknown column, no missing column;
- no blank data row, no comment row, no executable formula (a
  formula-style value such as `=1+1` is rejected simply because it cannot
  satisfy the field-specific grammar below — no separate formula-detection
  step is needed);
- LF or CRLF line endings are both accepted;
- a quoted CSV field may use standard double-quote escaping; an embedded
  CR or LF, or a NUL byte, inside any parsed field is rejected; leading or
  trailing whitespace inside a field is **rejected, not trimmed**;
- every parsed data row must contain exactly nine fields;
- no archive input, no URL input, no directory input, no device input, no
  UNC/network path, no symlink or reparse-point traversal where detectable;
- regular local file only; input bytes read once; no absolute path
  persisted.
- **Maximum input file size:** 33,554,432 bytes (32 MiB).
- **Maximum physical CSV line length:** 1,024 bytes.
- **Maximum parsed field length:** 128 Unicode code points.
- **Maximum bars per dataset:** 250,000.
- **Minimum bars per dataset:** 2.

All rows in one file must use the same instrument, timeframe, and source
classification — multiple instruments or timeframes must never be silently
combined.

### 7.2 Canonical timestamp grammar

```
YYYY-MM-DDTHH:MM:SS.ffffffZ
```

- exactly six fractional-second digits;
- UTC `Z` suffix only — no numeric offset form;
- no missing fractional seconds;
- must be a valid calendar date/time;
- canonical round-trip equality (re-serializing a parsed timestamp
  reproduces the exact same text).

### 7.3 Exact decimal input grammar (`open`, `high`, `low`, `close`, `spread`)

```
^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$
```

- ASCII digits only; no plus sign; no exponent; no leading decimal point;
  no trailing decimal point; no whitespace;
- no leading zeros except zero itself;
- maximum 24 total digits, excluding the sign and the decimal point;
- maximum 12 fractional digits;
- no rounding, and no quantization that loses value — the parsed `Decimal`
  is canonical exactly as supplied, subject only to: trailing fractional
  zeros may be removed canonically, and negative zero canonicalizes to
  `"0"`;
- `open`, `high`, `low`, `close` must be strictly positive after
  canonicalization; `spread` must be zero or positive after
  canonicalization.

### 7.4 Exact `tick_volume` grammar

```
^(?:0|[1-9][0-9]*)$
```

- ASCII integer only; no sign; no decimal point; no exponent; no
  whitespace;
- valid range: `0` through `9223372036854775807` inclusive.

## 8. Exact numeric policy

`Decimal` is authoritative for every canonical price, spread, and identity
input; binary floating-point is never used for validation, canonical
records, identities, hashes, dataset summaries, replay state, or
comparisons. The exact digit/scale/grammar limits for every numeric field
are fixed in Section 7.3/7.4, not left to implementation discretion.

- No `NaN`, no `Infinity`, no exponent notation in canonical output.
- No JSON/CSV boolean literal is accepted as a numeric value.
- Negative zero canonicalizes to zero.
- `tick_volume` must be a non-negative integer within the exact range
  fixed in Section 7.4.
- No undocumented rounding: imported decimal text remains **lossless**
  within the exact grammar of Section 7.3 — the canonicalized `Decimal`
  value is the canonical value, with no repricing, quantization beyond
  canonical trailing-zero removal, or invented rounding applied anywhere
  in the import path.
- Price and spread fields follow the repository's existing canonical
  finite-decimal text convention (no exponent notation) for storage and
  hashing. This contract does not invent broker precision, lot-step, or
  tick-size authority — none of those concepts exist in V0.

## 9. Bar validation rules

Every imported bar must satisfy all of the following. A single invalid row
fails the **entire** import — no partial dataset import is ever allowed.

1. Instrument is allowlisted (Section 6).
2. Timeframe is allowlisted (Section 6).
3. Timestamp matches the canonical UTC grammar (Section 7.2).
4. Timestamp is finite and parseable.
5. `open > 0`.
6. `high > 0`.
7. `low > 0`.
8. `close > 0`.
9. `spread >= 0`.
10. `tick_volume` matches the exact grammar and range (Section 7.4).
11. `high >= open`.
12. `high >= close`.
13. `high >= low`.
14. `low <= open`.
15. `low <= close`.
16. Input timestamps are strictly increasing in file order.
17. Duplicate timestamps are rejected.
18. Out-of-order timestamps are rejected.
19. Bars are **never** silently sorted.
20. Gaps are permitted but recorded (Section 13) — never filled.
21. Missing bars are **never** synthesized automatically.
22. Imported values are **never** silently corrected.

## 10. Governed record schemas (five, immutable, closed) plus one storage envelope

All five governed schemas are independent, closed (unknown fields
rejected), exactly versioned, and validated the same way Phase 5/6/6A
schemas are validated (`validate_*` functions rejecting non-finite
numbers, wrong types, and out-of-range enums). No credential, raw account
identity, or broker connection detail appears in any field of any schema
below. Section 10.6 additionally defines one non-governed, storage-only
envelope.

### 10.1 `TRL_MARKET_BAR.v1`

One immutable, validated, canonicalized market bar.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_MARKET_BAR.v1"` (closed) |
| `bar_id` | `"bar_" + sha256(...)[:32]` (Section 11.1) |
| `instrument` | canonical instrument allowlist member (Section 6) |
| `timeframe` | canonical timeframe allowlist member (Section 6) |
| `observed_at_utc` | canonical UTC timestamp (Section 7.2) |
| `open`, `high`, `low`, `close` | canonical lossless `Decimal` (Section 7.3), `> 0`, satisfying Section 9's high/low invariants |
| `spread` | canonical lossless `Decimal` (Section 7.3), `>= 0` |
| `tick_volume` | non-negative integer (Section 7.4) |
| `source_classification` | `SYNTHETIC_FIXTURE` or `LOCAL_HISTORICAL_FILE` (Section 5) |
| `canonical_bar_hash` | sha256 over the complete record (Section 11.1) |

The bar must **not** contain `dataset_id`, `replay_session_id`,
`opportunity_id`, `evidence_id`, an account identity, a broker identity, or
any execution authority. **A bar identity must be independent of the
dataset that later references it** — `source_reference` is deliberately
not a bar field (it lives only on the dataset manifest, Section 10.2),
which is exactly what makes identical bar content reusable across distinct
dataset manifests (Section 12).

### 10.2 `TRL_MARKET_DATASET_MANIFEST.v1`

The deterministic, all-or-nothing result of one accepted CSV import.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_MARKET_DATASET_MANIFEST.v1"` (closed) |
| `dataset_id` | `"mds_" + sha256(...)[:32]` (Section 11.2) |
| `instrument`, `timeframe` | inherited from every bar in the dataset (Section 7) |
| `source_classification` | `SYNTHETIC_FIXTURE` or `LOCAL_HISTORICAL_FILE` |
| `source_reference` | bounded logical label, maximum 256 Unicode code points (Section 5) |
| `bar_count` | integer, `2..250000` (Section 7) |
| `first_observed_at_utc`, `last_observed_at_utc` | canonical UTC timestamps, first and last bar in file order |
| `ordered_bar_refs` | ordered list of `(bar_id, canonical_bar_hash)` pairs, one per bar, in file order |
| `expected_interval_seconds` | canonical interval for `timeframe` (Section 13) |
| `gap_count` | non-negative integer count of detected gaps (Section 13) |
| `largest_gap_intervals` | non-negative integer, the largest `missing_intervals` value across all detected gaps; `0` if no gap |
| `duplicate_timestamp_count` | integer; **must equal `0`** for `import_status == ACCEPTED` |
| `out_of_order_count` | integer; **must equal `0`** for `import_status == ACCEPTED` |
| `import_status` | literal `"ACCEPTED"` — a rejected import produces no manifest at all |
| `imported_at_utc` | ISO-8601 UTC timestamp — display-only, excluded from `canonical_dataset_hash`; its integrity is protected by the enclosing `MARKET_DATASET_IMPORTED` journal event's own hash (Section 11.7) |
| `canonical_dataset_hash` | sha256 over the complete record excluding `imported_at_utc` (Section 11.2) |

### 10.3 `TRL_REPLAY_SESSION.v1`

One immutable deterministic replay configuration.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_REPLAY_SESSION.v1"` (closed) |
| `replay_session_id` | `"rps_" + sha256(...)[:32]` (Section 11.3) |
| `dataset_id`, `canonical_dataset_hash` | pinned reference to Section 10.2 |
| `start_index` | integer `>= 0` |
| `end_index` | integer, `<= dataset.bar_count - 1`, `>= start_index` |
| `step_size` | integer, `1..1000` |
| `created_at_utc` | ISO-8601 UTC timestamp — display-only, excluded from `canonical_replay_session_hash`; protected by the enclosing `REPLAY_SESSION_CREATED` journal event's own hash (Section 11.7) |
| `canonical_replay_session_hash` | sha256 over the complete record excluding `created_at_utc` (Section 11.3) |

**The immutable session record contains no mutable cursor.** Cursor,
status, and progress are always derived by replaying the session's own
`TRL_REPLAY_STEP.v1` events (Sections 14–15) — never stored as an editable
field on this record.

### 10.4 `TRL_REPLAY_STEP.v1`

One immutable advancement of a replay session.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_REPLAY_STEP.v1"` (closed) |
| `replay_step_id` | `"rst_" + sha256(...)[:32]` (Section 11.4) |
| `replay_session_id`, `canonical_replay_session_hash` | pinned parent reference |
| `sequence_number` | integer `>= 1`, contiguous per session, starting at `1` |
| `from_index`, `to_index` | integers within the session's `[start_index, end_index]` bound (Section 15) |
| `ordered_bar_refs` | ordered list of `(bar_id, canonical_bar_hash)` pairs for `from_index..to_index` |
| `status_after` | `RUNNING` or `COMPLETED` |
| `occurred_at_utc` | ISO-8601 UTC timestamp — display-only, excluded from `canonical_replay_step_hash`; protected by the enclosing `REPLAY_STEP_RECORDED` journal event's own hash (Section 11.7) |
| `canonical_replay_step_hash` | sha256 over the complete record excluding `occurred_at_utc` (Section 11.4) |

Each step is immutable once recorded — a step is never rewritten, only
superseded by the next step's own record.

### 10.5 `TRL_REPLAY_SNAPSHOT.v1`

One immutable, read-only, non-executable inspection point.

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_REPLAY_SNAPSHOT.v1"` (closed) |
| `replay_snapshot_id` | `"rsn_" + sha256(...)[:32]` (Section 11.5) |
| `replay_session_id`, `canonical_replay_session_hash` | pinned reference |
| `replay_step_id`, `canonical_replay_step_hash` | pinned reference to the step that produced this snapshot |
| `dataset_id`, `canonical_dataset_hash` | pinned reference |
| `current_index` | integer, equal to the producing step's `to_index` |
| `current_bar_id`, `canonical_current_bar_hash` | pinned reference to the bar at `current_index` |
| `window_start_index`, `window_end_index` | integers, `window_end_index == current_index`, window bounded to 100 bars (Section 16) |
| `ordered_window_bar_refs` | ordered list of `(bar_id, canonical_bar_hash)` pairs for `window_start_index..window_end_index` |
| `created_at_utc` | ISO-8601 UTC timestamp — display-only, excluded from `canonical_replay_snapshot_hash`; protected by the enclosing `REPLAY_SNAPSHOT_RECORDED` journal event's own hash (Section 11.7) |
| `non_live` | literal `true` (always; schema-enforced) |
| `non_executable` | literal `true` (always; schema-enforced) |
| `canonical_replay_snapshot_hash` | sha256 over the complete record excluding `created_at_utc` (Section 11.5) |

`TRL_REPLAY_SNAPSHOT.v1` is **not** `TRL_MARKET_SNAPSHOT.v1`,
`TRL_OPPORTUNITY_CARD.v1`, `TRL_EVIDENCE_ITEM.v1`, or any execution
document (Section 23). Any future conversion into an R2-010 analysis input
requires a separate, explicitly Founder-approved handoff contract.

### 10.6 `TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1` (non-governed storage container)

**Founder correction:** a normal journal event must not contain hundreds of
thousands of complete bar records. This envelope is the answer — a
separate, immutable, content-addressed local storage container holding the
complete canonicalized bar set and manifest for one accepted dataset. It is
**not** a sixth governed business record: it has no independent business
identity of its own (no dedicated `_id`/canonical-hash field beyond the
`dataset_id`/`canonical_dataset_hash` it carries), it is never accepted by
R2-010, it is never an execution document, and it is never exposed as
external authority in its own right — only the governed manifest
(Section 10.2) it faithfully wraps is authoritative.

Exact closed fields:

| Field | Type / domain |
|---|---|
| `schema_version` | `"TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1"` (closed) |
| `dataset_id` | must equal `manifest.dataset_id` |
| `canonical_dataset_hash` | must equal `manifest.canonical_dataset_hash` |
| `manifest` | one embedded object, must validate as `TRL_MARKET_DATASET_MANIFEST.v1` |
| `ordered_bars` | ordered list of complete embedded objects, each must validate as `TRL_MARKET_BAR.v1` |

Requirements:

1. `manifest` must validate as `TRL_MARKET_DATASET_MANIFEST.v1`.
2. Every `ordered_bars` item must validate as `TRL_MARKET_BAR.v1`.
3. `len(ordered_bars)` must equal `manifest.bar_count`.
4. `ordered_bars` order must match `manifest.ordered_bar_refs` exactly.
5. Every referenced `bar_id`/`canonical_bar_hash` pair in
   `manifest.ordered_bar_refs` must match the corresponding complete bar in
   `ordered_bars` exactly.
6. `instrument`, `timeframe`, and `source_classification` must remain
   consistent across the manifest and every bar.
7. No unknown field is allowed anywhere in the envelope.
8. No absolute path is stored anywhere in the envelope.
9. No source CSV bytes are stored.
10. No executable content is stored.
11. **Maximum canonical storage-envelope size: 268,435,456 bytes (256 MiB).**
12. The storage filename must be derived only from the safe dataset
    identity, equivalent to `<dataset_id>.json` — never from the source
    CSV filename or path.
13. The physical storage path is internal configuration and is **never**
    written into a governed record, a journal payload, a CLI response, or
    an HTTP response.
14. Storage files are **immutable after successful acceptance** — never
    rewritten in place.
15. Every load revalidates: strict UTF-8; strict JSON; no duplicate keys;
    exact closed fields; manifest identity/hash; every bar's identity/hash;
    complete manifest/bar correspondence (requirements 3–6); and the
    maximum size (requirement 11).

## 11. Deterministic identities

Every identity is deterministic, content-derived, canonical, nonce-free
(where content is immutable), restart-stable, process-stable, independent
of absolute file paths, and independent of mutable display state. Every
identity uses the established Phase 5/6/6A pattern:

```
"<prefix>_" + sha256("<DOMAIN>.v1\n" + canonical_json(identity_fields))[:32]
```

using the repository's existing `canonical_json` byte-stable encoder.
Every generated identifier matches the closed pattern `<prefix>` followed
by exactly 32 lowercase hexadecimal digest characters — no implementation
may substitute a different length, case, or field order anywhere below.
Computation proceeds strictly in this order — matching the Founder-mandated
sequence exactly (bar → dataset → replay session → replay step → replay
snapshot) — so no formula ever references a hash computed after it.

### 11.1 `TRL_MARKET_BAR.v1`

| Field | Value |
|---|---|
| Identity domain | `TRL-MARKET-BAR-ID.v1` |
| ID prefix | `bar_` |

`bar_id` identity material, in exact order:

1. `instrument`
2. `timeframe`
3. `observed_at_utc`
4. `open`
5. `high`
6. `low`
7. `close`
8. `spread`
9. `tick_volume`
10. `source_classification`

`canonical_bar_hash` material, in exact order:

1. `schema_version`
2. `bar_id`
3. `instrument`
4. `timeframe`
5. `observed_at_utc`
6. `open`
7. `high`
8. `low`
9. `close`
10. `spread`
11. `tick_volume`
12. `source_classification`

`source_reference` is never an input to bar identity — this is what makes
a bar identity independent of the dataset that later references it
(Section 10.1).

### 11.2 `TRL_MARKET_DATASET_MANIFEST.v1`

| Field | Value |
|---|---|
| Identity domain | `TRL-MARKET-DATASET-ID.v1` |
| ID prefix | `mds_` |

`dataset_id` identity material, in exact order:

1. `instrument`
2. `timeframe`
3. `source_classification`
4. `source_reference`
5. `ordered_bar_refs`
6. `expected_interval_seconds`
7. `gap_count`
8. `largest_gap_intervals`

(`expected_interval_seconds`, `gap_count`, and `largest_gap_intervals` are
themselves deterministic functions of `ordered_bar_refs`'s pinned bar
timestamps, so including them introduces no independent input and no
non-determinism — they simply make the identity's tamper-evidence explicit
over gap state as well as bar content.)

`canonical_dataset_hash` material, in exact order:

1. `schema_version`
2. `dataset_id`
3. `instrument`
4. `timeframe`
5. `source_classification`
6. `source_reference`
7. `bar_count`
8. `first_observed_at_utc`
9. `last_observed_at_utc`
10. `ordered_bar_refs`
11. `expected_interval_seconds`
12. `gap_count`
13. `largest_gap_intervals`
14. `duplicate_timestamp_count`
15. `out_of_order_count`
16. `import_status`

`imported_at_utc` is excluded from both the identity and the semantic hash
(Section 11.7).

### 11.3 `TRL_REPLAY_SESSION.v1`

| Field | Value |
|---|---|
| Identity domain | `TRL-REPLAY-SESSION-ID.v1` |
| ID prefix | `rps_` |

`replay_session_id` identity material, in exact order:

1. `dataset_id`
2. `canonical_dataset_hash`
3. `start_index`
4. `end_index`
5. `step_size`

`canonical_replay_session_hash` material, in exact order:

1. `schema_version`
2. `replay_session_id`
3. `dataset_id`
4. `canonical_dataset_hash`
5. `start_index`
6. `end_index`
7. `step_size`

`created_at_utc` is excluded from both the identity and the semantic hash
(Section 11.7).

### 11.4 `TRL_REPLAY_STEP.v1`

| Field | Value |
|---|---|
| Identity domain | `TRL-REPLAY-STEP-ID.v1` |
| ID prefix | `rst_` |

`replay_step_id` identity material, in exact order:

1. `replay_session_id`
2. `canonical_replay_session_hash`
3. `sequence_number`
4. `from_index`
5. `to_index`
6. `ordered_bar_refs`
7. `status_after`

`canonical_replay_step_hash` material, in exact order:

1. `schema_version`
2. `replay_step_id`
3. `replay_session_id`
4. `canonical_replay_session_hash`
5. `sequence_number`
6. `from_index`
7. `to_index`
8. `ordered_bar_refs`
9. `status_after`

`occurred_at_utc` is excluded from both the identity and the semantic hash
(Section 11.7).

### 11.5 `TRL_REPLAY_SNAPSHOT.v1`

| Field | Value |
|---|---|
| Identity domain | `TRL-REPLAY-SNAPSHOT-ID.v1` |
| ID prefix | `rsn_` |

`replay_snapshot_id` identity material, in exact order:

1. `replay_session_id`
2. `canonical_replay_session_hash`
3. `replay_step_id`
4. `canonical_replay_step_hash`
5. `dataset_id`
6. `canonical_dataset_hash`
7. `current_index`
8. `current_bar_id`
9. `canonical_current_bar_hash`
10. `window_start_index`
11. `window_end_index`
12. `ordered_window_bar_refs`
13. `non_live`
14. `non_executable`

`canonical_replay_snapshot_hash` material, in exact order:

1. `schema_version`
2. `replay_snapshot_id`
3. `replay_session_id`
4. `canonical_replay_session_hash`
5. `replay_step_id`
6. `canonical_replay_step_hash`
7. `dataset_id`
8. `canonical_dataset_hash`
9. `current_index`
10. `current_bar_id`
11. `canonical_current_bar_hash`
12. `window_start_index`
13. `window_end_index`
14. `ordered_window_bar_refs`
15. `non_live`
16. `non_executable`

`created_at_utc` is excluded from both the identity and the semantic hash
(Section 11.7).

### 11.6 No cycle

No identity formula above takes as input a hash computed from data that
includes that identity's own value or any value computed after it in the
sequence `bar -> dataset -> replay_session -> replay_step ->
replay_snapshot` — there is no cycle. A direct acceptance test for this
dependency-order property is required (Section 25.C).

### 11.7 Audit-timestamp exclusion and protection policy

Every display-only timestamp field (`imported_at_utc`, `created_at_utc`,
`occurred_at_utc`) is deliberately excluded from both its record's
identity and its record's own semantic hash, so that a mutable-in-name-only
display value can never change a content identity. This does **not** leave
the timestamp unprotected: every governed record is persisted only inside
its own enclosing, hash-chained journal event (Section 17/18); that
event's own `payload_sha256`/`current_event_hash` covers the complete
event payload, including the display timestamp. A tampered display
timestamp therefore still breaks the journal's hash chain even though it
never changes the record's own semantic/business hash. The storage
envelope (Section 10.6) carries the same governed records verbatim and is
itself revalidated on every load (Section 10.6, requirement 15).

## 12. Dataset reuse

**Founder decision: `source_reference` is included in dataset identity
(Section 11.2).** Therefore, deterministically:

- Same bars + same source classification + same source reference = **reuse
  the existing accepted dataset manifest** (identical `dataset_id`,
  identical `canonical_dataset_hash`) rather than create a duplicate
  authoritative record.
- Same bars + different source reference = a **distinct** dataset manifest.
- Individual bar identities remain identical either way — bars are reused
  across distinct dataset manifests because `source_reference` is never a
  bar-identity input (Section 11.1).

## 13. Gap detection

Canonical timeframe intervals, mapped exactly:

| Timeframe | `expected_interval_seconds` |
|---|---|
| `M5` | 300 |
| `M15` | 900 |
| `H1` | 3600 |
| `H4` | 14400 |
| `D1` | 86400 |

For each adjacent pair of bars in file order:

```
actual_interval = current_timestamp - previous_timestamp
```

A gap exists when `actual_interval > expected_interval`. Define:

```
missing_intervals = (actual_interval / expected_interval) - 1
```

A gap is valid **only** where `actual_interval` is an exact positive
multiple of `expected_interval`. If the interval is not an exact multiple,
the import is **rejected as structurally inconsistent**
(`MARKET_DATA_IRREGULAR_INTERVAL`, Section 24.1) — it is never repaired.
`gap_count` and `largest_gap_intervals` (Section 10.2) summarize detected
gaps. **No missing bar is ever automatically created.**

## 14. Deterministic replay model

Replay is **step-driven, not wall-clock-driven**. No timer, sleep, delayed
execution, or real-time synchronization is required or permitted.

### 14.1 Exact session bounds (corrected)

Replay session configuration (`TRL_REPLAY_SESSION.v1`, Section 10.3):

- `start_index` inclusive, `end_index` inclusive, `step_size` = bars per
  step.
- `start_index` minimum: `0`.
- `end_index` maximum: `dataset.bar_count - 1`.
- `start_index` must not exceed `end_index`.
- `step_size` range: `1` through `1000` inclusive.

### 14.2 Projected-step-count cap

```
projected_step_count = ceil(
    (end_index - start_index + 1) / step_size
)
```

**Maximum projected replay steps per session: 10,000.** A
`create-replay-session` request must fail closed with
`MARKET_DATA_REPLAY_PROJECTED_STEP_LIMIT_EXCEEDED` (Section 24.1) when
`projected_step_count > 10000`. `step_size` is never silently increased and
the requested range is never silently truncated to make a request fit.

### 14.3 Projected status derivation

Status is always derived from the session's own replay-event history
(Section 15), never a stored mutable field:

| Status | Meaning |
|---|---|
| `READY` | Session created; no step yet recorded. |
| `RUNNING` | At least one step recorded; `end_index` not yet reached. |
| `COMPLETED` | A step reached `to_index == end_index`. |
| `CANCELLED` | An explicit `cancel-replay-session` mutation was recorded against a `READY` or `RUNNING` session. |
| `CORRUPTED` | The session's own recorded event sequence fails an internal consistency check on projection (e.g., a non-contiguous `sequence_number`, a step referencing a mismatched `canonical_replay_session_hash`, or a missing referenced snapshot) — distinct from whole-journal hash-chain corruption, which is Section 18.3 Case A and fails the entire journal closed, not just one session. |

### 14.4 Replay-session reuse, by status (explicit, not implementation discretion)

V0 mutation behavior is exactly: **create replay session, advance replay,
cancel replay.** V0 does **not** support reverse replay, arbitrary seek
after creation, editing an existing session, changing dataset, changing
range, or changing step size. When an identical `(dataset_id,
canonical_dataset_hash, start_index, end_index, step_size)` is requested
again, behavior is fixed exactly by the existing session's projected
status:

- **`READY`:** return the existing session; append no duplicate
  `REPLAY_SESSION_CREATED` event; a bounded `REPLAY_SESSION_REUSED` event
  may be appended only where its own event identity remains unique under
  the journal's closed-vocabulary/hash-chain rules; the projection is not
  reset.
- **`RUNNING`:** return the existing session and its current projection;
  do not create a second session; do not reset or seek; do not duplicate
  any prior step.
- **`COMPLETED`:** return the existing completed session; do not reopen
  it; do not create a fresh run; do not append another step.
- **`CANCELLED`:** return the existing cancelled session; do not reopen
  it; do not create a fresh run.
- **`CORRUPTED`:** fail closed; do not create a replacement session with
  the same deterministic identity; require a later governed recovery or
  maintenance checkpoint (Section 18.3).

**V0 does not support rerunning an identical completed or cancelled replay
configuration as a fresh session.** A future contract may add a governed
logical run reference if distinct reruns are required — this contract does
not.

## 15. Replay-step behavior

### 15.1 Exact `replay-next` sequence

For each `replay-next` action:

1. Acquire the authoritative replay mutation lock.
2. Reload the journal after lock acquisition.
3. Reconstruct the current session projection.
4. Confirm the session is `READY` or `RUNNING`.
5. Determine `from_index` = next unconsumed index.
6. Determine `to_index = min(from_index + step_size - 1, end_index)`.
7. Create exactly one immutable `TRL_REPLAY_STEP.v1`.
8. Create exactly one immutable `TRL_REPLAY_SNAPSHOT.v1`.
9. Append events atomically (Section 15.2).
10. Update the derived projection.
11. Release the lock safely.

If the session has already completed, no new step is created, no duplicate
event is appended, and a governed completed result is returned instead.
Replay must never create an R2-010 evidence item, an R2-010 opportunity, a
Phase 5 order, a Phase 6 basket, or a broker action of any kind.

### 15.2 Atomic replay-event batches

One `replay-next` mutation persists its authoritative results as exactly
one atomic journal batch:

- **Non-terminal batch** (`to_index < end_index` after this step) contains
  exactly: `REPLAY_STEP_RECORDED`, `REPLAY_SNAPSHOT_RECORDED`.
- **Terminal batch** (`to_index == end_index`) contains exactly:
  `REPLAY_STEP_RECORDED`, `REPLAY_SNAPSHOT_RECORDED`,
  `REPLAY_SESSION_COMPLETED`.

Requirements:

- All events in the batch succeed or none become visible.
- Sequence numbers are consecutive; hash-chain links are consecutive.
- No snapshot exists without its step; no completion event exists without
  its terminal step and snapshot.
- A retry after a failed batch re-derives strictly from the last valid
  journal state and never duplicates an already-committed step.
- No rollback or compensation event is ever used — a batch either commits
  completely under the lock or leaves the journal exactly as it was.
- No unlocked fallback occurs anywhere in this sequence.

### 15.3 Cancellation

Cancellation is one atomic `REPLAY_SESSION_CANCELLED` event, appended only
after the same lock/reload/projection-validation sequence as Section 15.1
steps 1–4.

- Cancelling an already-`CANCELLED` session is **idempotent** — it returns
  the existing cancelled projection and appends no duplicate event.
- **Founder decision:** cancelling a `COMPLETED` session returns the
  existing `COMPLETED` projection and appends **no** event — a completed
  session is a permanent terminal state that cancellation cannot revisit.

## 16. Replay window model

The replay snapshot window contains all bars from
`max(start_index, current_index - window_size + 1)` through
`current_index`. **Founder-approved V0 replay window size: 100 bars
maximum.** If fewer than 100 bars have been replayed, the window contains
only the bars actually available.

The window must preserve dataset order, contain no hidden bar, contain no
future bar, contain no bar after `current_index`, and reference exact
immutable bar IDs and hashes. **No indicator, strategy, evidence, or signal
is calculated by R2-011** — the window is a read-only, ordered slice of
already-canonicalized bars, nothing more.

## 17. Dataset storage architecture and import atomicity

### 17.1 Two-tier persistence

Persistence for R2-011 is split into two components with distinct
responsibilities, addressing the Founder's finding that a normal journal
event must never embed hundreds of thousands of complete bar records:

- **Dataset store** (`TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1`,
  Section 10.6) — persists the complete canonical bars and the complete
  manifest for one accepted dataset; immutable after acceptance;
  content-addressed by `dataset_id`; strictly revalidated on every load;
  local-only; contains no credential or absolute user path.
- **Journal** (Section 18) — records acceptance, reuse, rejection, and
  replay events using compact dataset identifiers and hashes only; never
  duplicates all complete bars; remains bounded and efficiently
  replayable.

### 17.2 Exact import sequence

The authoritative import sequence, exactly:

1. Validate capability (`market_data_research`, Section 20).
2. Validate the local input path and file bounds (Section 7.1).
3. Read the input bytes once.
4. Strictly parse the entire CSV (Sections 7.1–7.4).
5. Validate every row (Section 9).
6. Construct every canonical bar (Section 10.1).
7. Construct the complete dataset manifest (Section 10.2).
8. Construct the storage-only dataset envelope (Section 10.6).
9. Acquire the dataset mutation lock (Section 18.1).
10. Reload the journal after lock acquisition.
11. Check for an already-accepted dataset with the same deterministic
    dataset identity and hash.
12. **If the accepted dataset already exists:**
    - fully verify its stored envelope (Section 10.6, requirement 15);
    - do **not** rewrite it;
    - do **not** create a duplicate authoritative record;
    - append or reuse the exact governed reuse result per Section 12's
      idempotency rule (`MARKET_DATASET_REUSED`);
    - return the existing manifest.
13. **If no accepted dataset exists:**
    - write the complete envelope to a same-directory temporary file;
    - flush and close it;
    - atomically replace/create the final content-addressed dataset file
      (temp-file + `os.replace`);
    - reload and revalidate the final file;
    - append `MARKET_DATASET_IMPORTED` to the valid journal;
    - only then expose the manifest as accepted.
14. Release the lock using owner-token safety.

### 17.3 Failure behavior

- Invalid input produces no manifest.
- Invalid input produces no accepted storage envelope.
- No partial bar set is ever authoritative.
- No partial manifest is ever authoritative.
- No partially written final file is ever accepted.
- No unlocked fallback ever occurs.

### 17.4 Orphan-file behavior

If an atomic dataset storage file exists on disk but no valid journal
acceptance event exists for it, the file is **non-authoritative**:

- it remains invisible to every list/inspect/replay operation;
- it is never treated as accepted merely because it exists on disk;
- it may only be safely verified and adopted during a later, identical
  import — and only after that import's own valid acceptance event is
  appended under lock (Section 17.2, step 13);
- otherwise it remains ignored until a later governed maintenance
  checkpoint (not authorized by this contract).

Loading the service must **never** delete or adopt an orphan file
automatically.

## 18. Storage, journal, and corruption semantics

### 18.1 Exact V0 resource limits (Founder-approved, no longer deferred)

**Input CSV:**

| Constant | Value |
|---|---|
| Maximum input bytes | 33,554,432 |
| Minimum data rows | 2 |
| Maximum data rows | 250,000 |
| Maximum physical CSV line length | 1,024 bytes |
| Maximum parsed field length | 128 Unicode code points |

**Dataset storage envelope:**

| Constant | Value |
|---|---|
| Maximum canonical bytes | 268,435,456 |

**Journal:**

| Constant | Value |
|---|---|
| Maximum event count | 100,000 |
| Maximum encoded event size | 262,144 bytes |
| Maximum encoded journal size | 268,435,456 bytes |
| Lock-acquisition timeout | 10.0 seconds |
| Lock polling interval | 0.02 seconds |
| Unlocked fallback | never permitted |

**Replay:**

| Constant | Value |
|---|---|
| `step_size` minimum | 1 |
| `step_size` maximum | 1000 |
| Replay-window size | fixed maximum of 100 bars |
| Maximum projected replay steps per session | 10,000 (Section 14.2) |

A separate Market Data and Replay journal (working name
`TRL_MARKET_DATA_REPLAY_JOURNAL.v1`, embedded in a
`TRL_MARKET_DATA_REPLAY_STORE.v1` storage document, mirroring the existing
`mt5_execution_journal.py`/`market_intelligence_journal.py` architecture).
It must **not** reuse the Phase 5/6 execution journal or the R2-010 Market
Intelligence journal.

Required safety principles: append-only events; closed event vocabulary;
canonical event records; deterministic event IDs where applicable; hash
chaining (`previous_event_hash`/`current_event_hash`); the bounded limits
above; strict validation; corruption fails closed (Section 18.3); atomic
persistence (temp-file + `os.replace`); cross-process locking; owner-token
lock safety; the exact bounded lock timeout/poll interval above; no
unlocked fallback; reload after lock acquisition; restart-safe projection.

Loading the data/replay journal must **never** import data automatically,
advance replay automatically, access a network, connect to a broker,
construct an adapter, create evidence, generate a signal, or generate an
order.

**Closed event vocabulary (ten governed types):**

`MARKET_DATASET_IMPORTED`, `MARKET_DATASET_REUSED`,
`MARKET_DATASET_REJECTED`, `REPLAY_SESSION_CREATED`,
`REPLAY_SESSION_REUSED`, `REPLAY_STEP_RECORDED`,
`REPLAY_SNAPSHOT_RECORDED`, `REPLAY_SESSION_COMPLETED`,
`REPLAY_SESSION_CANCELLED`, `JOURNAL_INTEGRITY_FAILURE`.

### 18.2 Exact event payload boundaries

Journal payloads stay compact by design — they carry references and
summaries, never a full bar set:

- **`MARKET_DATASET_IMPORTED`** contains only: `dataset_id`,
  `canonical_dataset_hash`, `instrument`, `timeframe`,
  `source_classification`, `source_reference`, `bar_count`,
  `first_observed_at_utc`, `last_observed_at_utc`, `gap_count`,
  `largest_gap_intervals`, `storage_envelope_size`,
  `storage_envelope_hash`. It must **not** embed any complete bar or the
  complete `ordered_bar_refs` list.
- **`MARKET_DATASET_REUSED`** contains only: `dataset_id`,
  `canonical_dataset_hash`, a bounded reuse reason, and a safe source
  classification/reference summary.
- **`MARKET_DATASET_REJECTED`** contains only: a governed reason code, a
  safe logical source reference, a bounded row number where applicable, a
  bounded field name where applicable — never a raw CSV row, never an
  absolute path.
- Replay events (`REPLAY_STEP_RECORDED`, `REPLAY_SNAPSHOT_RECORDED`, etc.)
  may contain the complete governed replay step or snapshot record only
  where the encoded event remains within the 262,144-byte limit
  (Section 18.1). Any event that would exceed this limit fails closed
  before any journal mutation occurs.

### 18.3 Corruption semantics — two distinct, safe cases

**Case A — journal hash-chain or journal schema corruption** (the journal
itself cannot be trusted):

- fail closed immediately;
- project a read-only service status of `CORRUPTED` only where a safe
  projection can be formed without trusting the corrupted region;
- do **not** append `JOURNAL_INTEGRITY_FAILURE` to a journal whose own
  integrity cannot be established — a journal that fails its own
  hash-chain validation cannot safely receive a new event;
- do not import;
- do not create or advance any replay;
- do not create a replacement journal automatically;
- require a later, separate, governed recovery checkpoint.

**Case B — the journal itself remains valid, but a referenced dataset
storage envelope fails its own revalidation** (Section 10.6, requirement
15):

- the journal itself remains appendable;
- append exactly one bounded `JOURNAL_INTEGRITY_FAILURE` event under lock;
- that event includes only safe IDs, hashes, and a governed reason code —
  never a physical path;
- mark the affected dataset's/replay session's projection `unavailable`
  or `CORRUPTED` (Section 14.3) as applicable;
- do not import automatically;
- do not advance replay automatically;
- do not rewrite the dataset storage file.

`JOURNAL_INTEGRITY_FAILURE` belongs to the event vocabulary for Case B and
any other failure where the journal itself remains valid — it is never
appended to a journal whose own integrity cannot first be established
(Case A).

## 19. Bounded read-only inspection and pagination

No CLI command or HTTP route may ever return an unbounded response. A
dataset manifest can reference up to 250,000 bars — list and inspection
output is paginated everywhere:

**Dataset and replay-session lists:**

- default limit: 100; maximum limit: 1000;
- default offset: 0; offset must be a non-negative integer;
- **datasets** ordered by `imported_at_utc` descending, then `dataset_id`
  ascending;
- **replay sessions** ordered by `created_at_utc` descending, then
  `replay_session_id` ascending.

**Dataset bar references (`inspect-market-dataset`):**

- default limit: 100; maximum limit: 1000; offset must be a non-negative
  integer; preserves manifest order;
- the response reports: `total_bar_count`, `offset`, `limit`,
  `returned_count`, `has_more`, and the `ordered_bar_refs` page itself.

**Journal inspection (`market-data-journal`):**

- default tail count: 100; maximum tail count: 1000; preserves journal
  sequence order in the returned page.

**Replay snapshot inspection:**

- the window itself remains capped at 100 bars (Section 16); no
  additional pagination is required.

The CLI may expose read-only `--offset`, `--limit`, and `--tail` flags
where applicable (Section 21). HTTP routes may accept strictly validated
read-only pagination query parameters (Section 22). Pagination parameters
must never mutate state; invalid pagination input returns a governed
validation error. No endpoint or CLI command may return all 250,000 bar
references, or an unbounded event tail, by default.

## 20. Operating-mode capability

### 20.1 Amendment (TRL-R2-011, contract-authoring checkpoint): `market_data_research`

*Added while authoring `TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_CONTRACT.md`
(TRL CORTEX DATA FABRIC V0, an informational "Phase 6B" checkpoint, not
part of the 0–14 phase sequence and not Phase 7). This is the one narrow,
Founder-approved capability change this contract requires; every other rule
in `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`, including the 3.1 and 3.2
amendments, is unchanged. No code implements this amendment yet — see this
contract's Sections 4/17/18/21/22 for the full boundary. This
contract-authoring checkpoint does not modify `mode_service.py`.*

A **nineteenth** governed capability is added: `market_data_research`. It
is a read/import/replay research capability: it grants no
`order_check`, `order_send`, `manual_broker_execution`,
`manual_basket_execution`, `basket_execution`,
`market_intelligence_research`, live execution, automated execution, or
execution handoff of any kind — it gates only local CSV import and
deterministic replay mutation (Section 4).

`market_data_research` is granted **only** to `RESEARCH`,
`SYNTHETIC_PAPER`, and `MT5_DEMO_MANUAL`:

| Mode | `market_data_research` granted? |
|---|---|
| `OFF` | No |
| `RESEARCH` | **Yes** |
| `SYNTHETIC_PAPER` | **Yes** |
| `MT5_DEMO_MANUAL` (available) | **Yes** |
| `MT5_DEMO_AUTOMATED` (future) | No |
| `MT5_LIVE_MANUAL` (future) | No |
| `MT5_LIVE_AUTOMATED` (future) | No |

Granted to `MT5_DEMO_MANUAL` for the same reason `market_intelligence_research`
was: local research alongside a demo-manual execution mode creates no
execution risk by itself, since the capability grants no order/basket
authority of any kind. Granting this capability does not, by itself,
activate, arm, or otherwise change the availability of any of the three
still-unavailable MT5 modes.

**Capability-gated future mutations:** `import-market-data`,
`create-replay-session`, `replay-next`, `cancel-replay-session`.

**Read-only operations remain available in every mode, including `OFF`**,
matching the existing repository convention: `market-data-status`,
`list-market-datasets`, `inspect-market-dataset`, `list-replay-sessions`,
`inspect-replay-session`, `inspect-replay-snapshot`,
`market-data-journal`, and every read-only HTTP route (Section 22).

`market_data_research` grants none of: `market_intelligence_research`,
`signal_proposal_generation`, `manual_broker_execution`,
`manual_basket_execution`, `mt5_order_check`, `mt5_order_send`, live-market-data
authority, or automated-execution authority.

## 21. CLI contract

Future CLI commands, local-operator-only, with stable exit codes, safe
identifiers, bounded output (Section 19), governed validation errors, no
traceback for ordinary rejected input, research-only warnings, no broker
command, no execution command, no network retrieval, and no automatic
evidence generation:

1. `market-data-status`
2. `import-market-data <csv-path> --source-classification
   <SYNTHETIC_FIXTURE|LOCAL_HISTORICAL_FILE> --source-reference
   <bounded-logical-label>`
3. `list-market-datasets [--offset N] [--limit N]`
4. `inspect-market-dataset <dataset-id> [--offset N] [--limit N]`
5. `create-replay-session <dataset-id> --start-index <integer> --end-index
   <integer> --step-size <integer>`
6. `list-replay-sessions [--offset N] [--limit N]`
7. `inspect-replay-session <replay-session-id>`
8. `replay-next <replay-session-id>`
9. `inspect-replay-snapshot <replay-session-id>`
10. `cancel-replay-session <replay-session-id>`
11. `market-data-journal [--tail N]`

## 22. HTTP and dashboard contract

Future read-only routes:

- `/api/market-data-status`
- `/api/market-datasets` (accepts validated `offset`/`limit` query
  parameters, Section 19)
- `/api/market-dataset/<safe-id>` (accepts validated `offset`/`limit` query
  parameters for its bar-reference page, Section 19)
- `/api/replay-sessions` (accepts validated `offset`/`limit` query
  parameters, Section 19)
- `/api/replay-session/<safe-id>`
- `/api/replay-snapshot/<safe-id>`

Requirements: GET and HEAD only; mutation methods return `405` with a
correct `Allow` header; bounded responses (Section 19); safe identifier
validation; no path disclosure; no raw exception disclosure; no import
through HTTP; no replay advancement through HTTP; no mutation through any
query parameter (pagination parameters are read-only filters, never
mutations); no external network action; no analysis triggered by GET;
invalid pagination input returns a governed validation error, never a raw
exception.

**Dashboard panel concept:** *TRL CORTEX DATA FABRIC V0* — RESEARCH ONLY,
LOCAL DATA ONLY, LIVE DATA DISABLED, EXECUTION DISABLED — showing current
operating mode; imported datasets (source classification, source
reference, instrument, timeframe, bar count, first/last timestamps, gap
count, largest gap, dataset hash), paginated; replay sessions (status,
current cursor, current replay window, current bar, `non_live = true`,
`non_executable = true`), paginated; and remaining blockers. No browser
value is authoritative. No `innerHTML` for new rendering.

## 23. R2-010 compatibility boundary

R2-011 remains separate from R2-010. It may create canonical bars, dataset
manifests, replay sessions, replay steps, and replay snapshots. It must
**not** create `TRL_MARKET_SNAPSHOT.v1`, `TRL_EVIDENCE_ITEM.v1`,
`TRL_OPPORTUNITY_CARD.v1`, `TRL_VIRTUAL_OPPORTUNITY.v1`,
`TRL_OPPORTUNITY_DECISION.v1`,
`TRL_MARKET_INTELLIGENCE_BASKET_PREVIEW.v1`, or
`TRL_LEARNING_TELEMETRY.v1`. No R2-010 service or journal mutation is
authorized. The future evidence-generator checkpoint may consume R2-011
replay windows, but only under a new, separate, Founder-approved contract.
R2-010 remains complete and unchanged by this checkpoint.

## 24. Blockers and reason-code completeness

Six new, precisely scoped blockers (added to `TRL_BLOCKERS.md`):

1. **`EXTERNAL_MARKET_DATA_FEED_NOT_APPROVED`** — blocks external
   market-data APIs, websocket feeds, network polling, and vendor SDKs.
2. **`BROKER_HISTORY_IMPORT_NOT_APPROVED`** — blocks direct MT5 history
   import, broker-terminal history extraction, and authenticated broker
   downloads.
3. **`AUTOMATIC_EVIDENCE_GENERATION_NOT_APPROVED`** — blocks converting
   replay bars into evidence automatically, including technical-indicator
   evidence, regime evidence, liquidity evidence, or signal generation.
4. **`REPLAY_TO_INTELLIGENCE_HANDOFF_NOT_APPROVED`** — blocks automatic
   creation of R2-010 input bundles, automatic R2-010 analysis calls, and
   automatic Opportunity Cards.
5. **`REPLAY_TO_EXECUTION_HANDOFF_NOT_APPROVED`** — blocks Phase 5 order
   intents, Phase 6 baskets, confirmations, and broker instructions
   derived from replay.
6. **`DATASET_PROVENANCE_NOT_VERIFIED`** — local user-supplied historical
   data is unverified; imported data must not be marketed as
   institutionally verified; replay results inherit the source limitation.

None of these blockers prevent approved local import and replay — each is
scoped narrowly, exactly as R2-010's blockers were.

### 24.1 Exact governed reason codes (implementation-facing, closed vocabulary)

| Condition | Reason code |
|---|---|
| Input file too large | `MARKET_DATA_INPUT_FILE_TOO_LARGE` |
| Physical CSV line too long | `MARKET_DATA_CSV_LINE_TOO_LONG` |
| Parsed field too long | `MARKET_DATA_CSV_FIELD_TOO_LONG` |
| Invalid CSV shape (header/columns/row width) | `MARKET_DATA_CSV_SHAPE_INVALID` |
| Invalid timestamp grammar | `MARKET_DATA_TIMESTAMP_INVALID` |
| Invalid decimal grammar | `MARKET_DATA_DECIMAL_GRAMMAR_INVALID` |
| Decimal total-digit limit exceeded | `MARKET_DATA_DECIMAL_DIGIT_LIMIT_EXCEEDED` |
| Decimal fractional-scale limit exceeded | `MARKET_DATA_DECIMAL_SCALE_EXCEEDED` |
| `tick_volume` out of range/grammar | `MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE` |
| Duplicate timestamp | `MARKET_DATA_DUPLICATE_TIMESTAMP` |
| Out-of-order timestamp | `MARKET_DATA_TIMESTAMP_OUT_OF_ORDER` |
| Irregular, non-multiple interval | `MARKET_DATA_IRREGULAR_INTERVAL` |
| Dataset storage envelope too large | `MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE` |
| Dataset storage integrity failure | `MARKET_DATA_STORAGE_INTEGRITY_FAILURE` |
| Journal event too large | `MARKET_DATA_JOURNAL_EVENT_TOO_LARGE` |
| Journal full (event count or byte bound reached) | `MARKET_DATA_JOURNAL_FULL` |
| Journal lock-acquisition timeout | `MARKET_DATA_JOURNAL_LOCK_TIMEOUT` |
| Journal corrupted (Section 18.3 Case A) | `MARKET_DATA_JOURNAL_CORRUPTED` |
| Replay bounds invalid (Section 14.1) | `MARKET_DATA_REPLAY_BOUNDS_INVALID` |
| Replay projected-step limit exceeded (Section 14.2) | `MARKET_DATA_REPLAY_PROJECTED_STEP_LIMIT_EXCEEDED` |
| Replay session already completed | `MARKET_DATA_REPLAY_ALREADY_COMPLETED` |
| Replay session already cancelled | `MARKET_DATA_REPLAY_ALREADY_CANCELLED` |
| Replay session corrupted (Section 14.3) | `MARKET_DATA_REPLAY_SESSION_CORRUPTED` |
| Capability denied | `MARKET_DATA_CAPABILITY_DENIED` |
| External market-data feed requested | `EXTERNAL_MARKET_DATA_FEED_NOT_APPROVED` (Section 24, item 1) |
| Broker history import requested | `BROKER_HISTORY_IMPORT_NOT_APPROVED` (Section 24, item 2) |
| Automatic evidence generation requested | `AUTOMATIC_EVIDENCE_GENERATION_NOT_APPROVED` (Section 24, item 3) |
| Replay-to-intelligence handoff requested | `REPLAY_TO_INTELLIGENCE_HANDOFF_NOT_APPROVED` (Section 24, item 4) |
| Replay-to-execution handoff requested | `REPLAY_TO_EXECUTION_HANDOFF_NOT_APPROVED` (Section 24, item 5) |

Use final repository naming conventions consistently at implementation
time; this table fixes the exact condition-to-code mapping, not the
mechanical casing conventions already established elsewhere in the
repository.

## 25. Future implementation acceptance requirements

The future implementation requires comprehensive tests covering at least:

**A. Input and files** — exact CSV header; wrong header order; missing
header; unknown column; duplicate header; blank row; UTF-8; BOM rejection;
file-size limit; physical-line-length limit; field-length limit; row-count
limit; minimum row count; regular-file requirement; directory rejection;
device-path rejection; UNC rejection; URL rejection; archive rejection;
symlink/reparse rejection where detectable; embedded CR/LF/NUL rejection
inside a field; untrimmed-whitespace rejection; no absolute-path
persistence.

**B. Bar validation** — all approved instruments; all approved timeframes;
unsupported aliases; positive OHLC; high/low invariants; non-negative
spread; non-negative integer volume within exact range; booleans rejected
as numeric; non-finite values; exponent policy; exact decimal grammar
(digit/scale limits); exact tick-volume grammar; canonical timestamp
grammar; duplicate-timestamp rejection; out-of-order rejection; no silent
sorting; no silent correction.

**C. Identities** — deterministic bar ID/hash exactly matching Section
11.1's field order; deterministic dataset ID/hash exactly matching Section
11.2; deterministic session/step/snapshot ID/hash exactly matching Sections
11.3–11.5; restart stability; process stability; no nonce; no circular
dependency; no absolute-path dependency; audit-timestamp exclusion
verified for every schema.

**D. Dataset behavior** — accepted dataset; all-or-nothing import; exact
bar count; ordered bar references; identical-import reuse; different
source reference creates a distinct manifest; individual bars remain
reused; gap detection; largest gap; irregular non-multiple interval
rejection; no gap filling.

**E. Storage envelope** — envelope validates manifest and every bar; bar
count matches manifest; bar order matches `ordered_bar_refs`; every
referenced ID/hash matches; instrument/timeframe/source-classification
consistency; unknown-field rejection; no absolute path; no source CSV
bytes; no executable content; maximum-size enforcement; immutability after
acceptance; full revalidation on every load; orphan-file invisibility and
safe later adoption (Section 17.4).

**F. Replay behavior** — `READY`; `RUNNING`; `COMPLETED`; `CANCELLED`;
`CORRUPTED`; reuse behavior for every one of the five statuses
(Section 14.4); valid start/end bounds; valid step-size bounds; projected-
step-count cap enforcement; exact first step; exact middle step; exact
final partial step; no step after completion; no duplicate event after
completion; atomic non-terminal and terminal event batches; window maximum
100; no future bar; exact cursor projection; restart persistence;
deterministic replay; no wall-clock-timing dependency; cancellation
idempotency; cancellation-of-`COMPLETED` behavior.

**G. Journal, storage, and concurrency** — separate journal; closed event
vocabulary; compact event payloads (Section 18.2); hash chain; Case A
journal-corruption fail-closed behavior; Case B dataset-storage-corruption
behavior with a bounded `JOURNAL_INTEGRITY_FAILURE` event; atomic
persistence; exact lock timeout/poll interval; owner-token safety; no
unlocked fallback; reload after lock; true separate-process dataset
import/reuse; true separate-process replay-session creation/reuse; true
separate-process replay advancement; no duplicate step; no remaining lock.

**H. Pagination** — default/maximum limits for dataset lists, replay-
session lists, dataset bar references, and journal tail; deterministic
ordering; non-negative offset validation; `has_more`/`total_bar_count`
correctness; invalid-pagination governed error; no unbounded default
response anywhere.

**I. Capability** — `market_data_research` exists; exact approved-mode
matrix; denied modes; OFF read-only behavior; no implied intelligence
capability; no implied execution capability.

**J. CLI, HTTP and dashboard** — all 11 CLI commands including pagination
flags; stable exit codes; six read-only HTTP routes including pagination
query parameters; HEAD support; mutation 405; Allow headers; safe IDs; no
filesystem-path disclosure; no raw exceptions; no HTTP mutation; no
`innerHTML` in new rendering.

**K. Safety and compatibility** — no `MetaTrader5` import; no adapter
construction; no `order_check`; no `order_send`; no external network; no
broker connection; no Phase 5/6 journal write; no R2-010 journal write; no
evidence generation; no Opportunity Card; no execution record; R2-010
tests unchanged; complete existing suite unchanged; Phase 7 absent.

## 26. Tonight-ready future implementation boundary

The first R2-011 implementation may demonstrate: (1) importing one
committed synthetic CSV dataset; (2) validating and canonicalizing its
bars; (3) creating one dataset manifest and its storage envelope; (4)
showing gap statistics; (5) creating one deterministic replay session; (6)
advancing through several replay steps; (7) producing replay snapshots;
(8) persisting state through restart; (9) displaying dataset and replay
state, paginated, in the local dashboard.

It does **not** need: live data, broker history, TradingView, external
APIs, automatic indicators, automatic evidence, R2-010 handoff, signals,
strategies, or execution. This limitation is intentional.

## 27. Remaining unresolved decisions

None. The Founder review pass (see Document Information Status field)
resolved every previously deferred bound: the replay-mutation lock timeout
and poll interval, and every journal/storage/CSV size and count bound, are
now fixed exactly in Section 18.1. No schema, identity, import rule,
validation rule, replay semantic, capability-matrix decision, blocker, or
safety-boundary question is left open. No V0 implementation-authority
decision remains unresolved.
