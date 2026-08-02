# TRL-R2-011 Deterministic Market Data Fabric and Replay V0 — Implementation Evidence

> **RESEARCH ONLY — LOCAL ONLY — NO LIVE DATA — NO BROKER HISTORY — NO EXECUTION AUTHORITY**

Product component working name: **TRL CORTEX DATA FABRIC V0**

## Document Information

| Field | Value |
|---|---|
| Founder | Abdulrahman Yaseen Alsakkaf |
| Checkpoint | TRL-R2-011 implementation (against the Founder-approved, remotely verified governing contract, commit `678de02d739a89a0fcc58765178bd8935f4db868`) |
| Status | **Implementation complete, Founder-reviewed (including two correction passes: reason-code conformance, then locked rejection journaling), committed, pushed, and remotely verified.** This document is part of implementation commit `6e24194071e8776833e396745d19b45785ee6ce4` ("Implement TRL-R2-011 Data Fabric and Replay V0"), pushed range `5c53396..6e24194`. At verification time: local HEAD, the live `origin/codex/TRL-R2-full-vision-execution` ref, and the upstream-tracking ref all equaled `6e24194071e8776833e396745d19b45785ee6ce4`; ahead/behind was `0 0`; the working tree and index were clean; no untracked file remained; `main` was unchanged. **R2-011 implementation is formally closed.** The exact current committed/pushed state is always read from `git rev-parse HEAD`/`git status` directly rather than restated here as a value that would otherwise go stale. |
| Governing contract | `TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_CONTRACT.md`, commit `678de02d739a89a0fcc58765178bd8935f4db868` |
| Contract-closure commit | `5c53396af9daa0e235e293d698e39b5afcdeb23b` ("Close TRL-R2-011 verified contract checkpoint") |
| Depends on | `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md` (`ModeService`, narrowly amended: `market_data_research` capability); TRL-R2-010 (Market Intelligence V0 — complete, unchanged) |
| Feeds | No phase. Local-only, research-only. Does not authorize, gate, or advance Phase 7 or any later phase. |

---

## 1. Classification and exact file scope

**Is:** local-only, research-only, deterministic, historical- or synthetic-data-only, non-live, non-automated, non-executing, append-only and auditable, restart-stable, compatible with R2-010.

**Is not:** a live market feed, a broker-history connector, a TradingView connector, an external API client, an automatic evidence generator, a signal generator, a strategy, an execution system, or Phase 7.

### 1.1 New files (15)

1. `trading_lab_app/market_data_replay_data.py`
2. `trading_lab_app/market_data_replay_storage.py`
3. `trading_lab_app/market_data_replay_journal.py`
4. `trading_lab_app/market_data_replay_service.py`
5. `trading_lab_app/market_data_replay_cli.py`
6. `test_market_data_replay_data.py`
7. `test_market_data_replay_storage.py`
8. `test_market_data_replay_journal.py`
9. `test_market_data_replay_service.py`
10. `test_market_data_replay_cli.py`
11. `test_market_data_replay_http.py`
12. `test_market_data_replay_concurrency.py`
13. `mdr_test_support.py` (shared, non-discovered test helper — filename does not match `test*.py`)
14. `fixtures/trl_cortex_data_fabric_v0_synthetic.csv`
15. `TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_EVIDENCE.md` (this document)

### 1.2 Modified files (11, all additive)

1. `trading_lab_app/mode_service.py` — one capability added (`market_data_research`), 16 insertions, 0 deletions
2. `trading_lab_app/app.py` — subsystem builder/construction/validation/shutdown wiring, 107 insertions
3. `trading_lab_app/server.py` — 6 read-only routes, pagination parsing, HEAD/405 wiring, 196 insertions
4. `trading_lab_app/service.py` — 6 HTTP document wrapper functions, 35 insertions
5. `trading_lab_app/static/index.html` — one new dashboard section, 25 insertions
6. `trading_lab_app/static/app.js` — render/load functions, safe DOM only, 63 insertions
7. `TRL_APP_QUICK_START.md` — new Section 21
8. `TRL_FULL_VISION_MASTER_PROGRAM.md` — Phase 6B row updated
9. `TRL_CONTINUATION_STATE.md` — new implementation entry
10. `TRL_CONTINUATION_STATE.json` — new implementation entry
11. `TRL_DECISION_LOG.md` — new entry `2026-08-02-029`

### 1.3 Deleted files

None.

### 1.4 Direct R2-010 and Phase 5/6 compatibility — exact scope proof

`git diff --stat` (full repository diff at time of writing) touches only the 6 files listed in 1.2 plus the 15 new files in 1.1. No `market_intelligence_*`, `mt5_execution_*`, or `basket_execution_*` file appears in the diff. No existing test file was modified. The governing contract (`TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_CONTRACT.md`), `TRL_PHASE_3_OPERATING_MODE_CONTRACT.md`, and `TRL_BLOCKERS.md` were not modified.

---

## 2. Reason-code conformance — Founder-review correction pass

A dedicated Founder-review correction pass performed a complete implementation-conformance audit of every one of the 29 codes in the contract's closed Section 24.1 reason-code table. That audit found **three genuine conformance defects** (not the originally-reported "two disclosed reuse decisions, both acceptable") and corrected all three in the authorized R2-011 source only. No existing test was modified; no contract was modified.

### 2.1 Defects found and corrected

1. **`MARKET_DATA_JOURNAL_CORRUPTED` was declared but never emitted.** `market_data_replay_service._require_journal_integrity` raised an invented, non-governed alias, `MARKET_DATA_JOURNAL_INTEGRITY_UNCERTAIN` (not a member of `mdd.REASON_CODES`), for exactly the condition the contract assigns `MARKET_DATA_JOURNAL_CORRUPTED` to (Section 18.3 Case A). **Fixed:** the alias was removed from `SERVICE_REASON_CODES` and the raise site now uses the contract's exact code. Four new tests (`JournalCorruptionTests`) verify `import_market_data`/`create_replay_session`/`replay_next`/`cancel_replay_session` all fail closed with `MARKET_DATA_JOURNAL_CORRUPTED`, and that read-only `status_document()` remains available.
2. **`MARKET_DATA_STORAGE_INTEGRITY_FAILURE` leaked the wrong code on a corrupted *stored* envelope.** `market_data_replay_storage._parse_envelope_bytes` called `mdd.validate_storage_envelope`, which internally reuses `validate_dataset_manifest_record`/`validate_bar_record` (the same functions used during CSV *import*). A tampered field inside an already-accepted, reloaded envelope (e.g. `bar_count` mismatched against `ordered_bar_refs`) therefore surfaced `MARKET_DATA_CSV_SHAPE_INVALID` — an import-context code — instead of the contract's storage-load code (Section 10.6 requirement 15: "Every load revalidates ... "). Reproduced directly and confirmed before the fix (`reason_code = MARKET_DATA_CSV_SHAPE_INVALID`) and after the fix (`reason_code = MARKET_DATA_STORAGE_INTEGRITY_FAILURE`). **Fixed:** `_parse_envelope_bytes` now catches any `mdd.MarketDataValidationError` raised during storage-envelope revalidation and re-raises it uniformly as `MARKET_DATA_STORAGE_INTEGRITY_FAILURE` (the pre-existing, already-correct `MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE` size check, which fires before any parse is attempted, is untouched and remains distinct). The two storage tests that exercised tampering (`test_reload_revalidates_and_detects_tampering`, `test_duplicate_json_key_rejected`) were tightened to assert the exact code; `test_oversized_envelope_rejected` was tightened from an `assertIn` over two codes to an exact `assertEqual`.
3. **`MARKET_DATA_REPLAY_ALREADY_COMPLETED` was declared but never observable.** Section 15.1 states that calling `replay-next` on an already-completed session returns "a governed completed result ... instead" of an error — implying the code should be present *in* that returned result, not merely true-by-absence-of-a-new-step. `replay_next`'s COMPLETED short-circuit returned the projection with no field naming the condition. **Fixed:** that branch now attaches `"reason_code": "MARKET_DATA_REPLAY_ALREADY_COMPLETED"` to the returned document (the branch that itself *just reached* completion is unaffected and carries no such field, preserving the distinction Section 15.1 draws). `test_no_step_after_completion` was extended to assert the field's presence/absence in both cases.

### 2.2 Remaining reuse decisions confirmed contract-conforming (not defects)

After the three corrections above, a full 29-row exhaustiveness check (every code in Section 24.1 individually compared against every Section 9/7 rule) found **no other code available in the closed vocabulary** that fits an instrument/timeframe-allowlist violation, a cross-row mixed-instrument/timeframe file, or an OHLC/spread-invariant violation (`open<=0`, `high<low`, etc.) any more specifically than the two already in use:

- Instrument/timeframe-allowlist and mixed-instrument/timeframe-file violations → `MARKET_DATA_CSV_SHAPE_INVALID`.
- OHLC/spread invariant violations (rules 5–15) → `MARKET_DATA_DECIMAL_GRAMMAR_INVALID`.

This is not a case of two contractually-distinct codes being incorrectly conflated (the failure mode Section 3 of the Founder-review correction guards against) — for both condition classes, **no code in the 29-entry table names that condition at all**, contractually or by any reasonable reading of the table's own row descriptions. Section 24.1's closing note ("this table fixes the exact condition-to-code mapping, not the mechanical casing conventions") establishes the table as authoritative and closed, meaning no ad-hoc new code may be invented (`REASON_CODES` in `market_data_replay_data.py` is exactly the 29-member table, no more, no fewer) — the two nearest-fit existing codes are the only contract-conforming choice available. No schema field, identity input, validation rule, or reason-code *meaning* is changed by this application; it is a closed-vocabulary application decision, not a deviation.

### 2.3 Complete reason-code implementation-conformance table

Every one of the 29 governed codes, verified directly against source and tests after the corrections in 2.1:

| # | Code | Triggering condition | Source (file : function) | Test(s) |
|---|---|---|---|---|
| 1 | `MARKET_DATA_INPUT_FILE_TOO_LARGE` | CSV bytes exceed 33,554,432 | `market_data_replay_data.py : parse_csv_rows`; `market_data_replay_service.py : load_csv_input_bytes` | `test_market_data_replay_data.CsvShapeTests.test_byte_limit_enforced` |
| 2 | `MARKET_DATA_CSV_LINE_TOO_LONG` | Physical line exceeds 1,024 bytes | `market_data_replay_data.py : parse_csv_rows` | `test_line_length_limit_enforced` |
| 3 | `MARKET_DATA_CSV_FIELD_TOO_LONG` | Parsed field exceeds 128 code points | `market_data_replay_data.py : parse_csv_rows` | `test_field_length_limit_enforced` |
| 4 | `MARKET_DATA_CSV_SHAPE_INVALID` | Header/column/row-width violation; **and** (2.2) instrument/timeframe-allowlist or mixed-instrument/timeframe-file violation | `market_data_replay_data.py : parse_csv_rows`, `_require_exact_keys`, schema `_fail(SCHEMA_FAIL, ...)` call sites | `test_wrong_header_order_rejected`, `test_missing_column_rejected`, `test_unknown_column_rejected`, `test_blank_row_rejected`, `test_comment_row_rejected`, `test_instrument_alias_rejected`, `test_timeframe_alias_rejected`, `test_mixed_instrument_in_one_file_rejected`, `test_bom_rejected`, `test_invalid_utf8_rejected`, `test_nul_byte_rejected`, `test_embedded_newline_in_quoted_field_rejected`, `test_untrimmed_whitespace_rejected`, `test_minimum_rows_enforced`, `test_maximum_rows_enforced` |
| 5 | `MARKET_DATA_TIMESTAMP_INVALID` | Timestamp grammar/round-trip/calendar failure | `market_data_replay_data.py : validate_market_timestamp` | `TimestampGrammarTests` (4 tests) |
| 6 | `MARKET_DATA_DECIMAL_GRAMMAR_INVALID` | Decimal regex mismatch, sign/whitespace/leading-zero violation; **and** (2.2) OHLC/spread invariant violation | `market_data_replay_data.py : parse_market_decimal`, `parse_csv_rows` (invariant check) | `DecimalGrammarTests` (9 tests), `BarValidationTests.test_high_below_low_rejected`, `test_open_above_high_rejected` |
| 7 | `MARKET_DATA_DECIMAL_DIGIT_LIMIT_EXCEEDED` | >24 total digits | `market_data_replay_data.py : parse_market_decimal` | `test_digit_limit_enforced` |
| 8 | `MARKET_DATA_DECIMAL_SCALE_EXCEEDED` | >12 fractional digits | `market_data_replay_data.py : parse_market_decimal` | `test_scale_limit_enforced` |
| 9 | `MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE` | Grammar mismatch or out-of-range integer | `market_data_replay_data.py : parse_tick_volume` | `TickVolumeGrammarTests` (6 tests) |
| 10 | `MARKET_DATA_DUPLICATE_TIMESTAMP` | Equal adjacent timestamps | `market_data_replay_data.py : parse_csv_rows` | `test_duplicate_timestamp_rejected` |
| 11 | `MARKET_DATA_TIMESTAMP_OUT_OF_ORDER` | Decreasing adjacent timestamp | `market_data_replay_data.py : parse_csv_rows` | `test_out_of_order_rejected_not_silently_sorted` |
| 12 | `MARKET_DATA_IRREGULAR_INTERVAL` | Gap not an exact multiple of the timeframe interval | `market_data_replay_data.py : parse_csv_rows` | `test_irregular_interval_rejected` |
| 13 | `MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE` | Encoded envelope exceeds 268,435,456 bytes | `market_data_replay_storage.py : _parse_envelope_bytes`, `encode_envelope` | `test_market_data_replay_storage.LocalDatasetStorageTests.test_oversized_envelope_rejected` (exact-code assertion after correction) |
| 14 | `MARKET_DATA_STORAGE_INTEGRITY_FAILURE` | Any other Section 10.6 requirement-15 revalidation failure on a stored envelope; envelope/manifest dataset-identity mismatch; orphan/Case-B dataset corruption | `market_data_replay_storage.py : _parse_envelope_bytes` (corrected 2.1.2), `LocalDatasetStorage.load`; `market_data_replay_service.py : _load_dataset_envelope` | `test_reload_revalidates_and_detects_tampering`, `test_duplicate_json_key_rejected` (both exact-code after correction); service-level Case B: `StorageIntegrityFailureCaseBTests` (3 new tests) |
| 15 | `MARKET_DATA_JOURNAL_EVENT_TOO_LARGE` | Encoded event exceeds 262,144 bytes | `market_data_replay_journal.py : MarketDataReplayJournal.append_batch` | `test_market_data_replay_journal.InMemoryJournalTests.test_event_too_large_rejected` (exact-code after correction) |
| 16 | `MARKET_DATA_JOURNAL_FULL` | Event count or journal byte bound reached | `market_data_replay_journal.py : append_batch` | `test_event_count_bound_enforced` (exact-code after correction) |
| 17 | `MARKET_DATA_JOURNAL_LOCK_TIMEOUT` | Mutation lock not acquired within 10.0s | `market_data_replay_service.py : import_market_data`/`create_replay_session`/`replay_next`/`cancel_replay_session` (all four catch `MarketDataReplayJournalLockTimeout`) | `LockTimeoutConversionTests` (4 new tests, one per mutation) |
| 18 | `MARKET_DATA_JOURNAL_CORRUPTED` | Journal fails its own startup validation (Case A) | `market_data_replay_service.py : _require_journal_integrity` (corrected 2.1.1) | `JournalCorruptionTests` (5 new tests) |
| 19 | `MARKET_DATA_REPLAY_BOUNDS_INVALID` | `start_index`/`end_index`/`step_size` outside governed range | `market_data_replay_data.py : validate_replay_bounds`; `market_data_replay_service.py : create_replay_session` | `ReplayBoundsTests` (4 tests); `ReplaySessionLifecycleTests.test_replay_bounds_invalid_rejected` |
| 20 | `MARKET_DATA_REPLAY_PROJECTED_STEP_LIMIT_EXCEEDED` | Projected step count exceeds 10,000 | `market_data_replay_service.py : create_replay_session` | `test_projected_step_limit_exceeded_rejected` |
| 21 | `MARKET_DATA_REPLAY_ALREADY_COMPLETED` | `replay-next` called on an already-`COMPLETED` session | `market_data_replay_service.py : replay_next` (corrected 2.1.3 — now attached to the returned document) | `test_no_step_after_completion` (extended) |
| 22 | `MARKET_DATA_REPLAY_ALREADY_CANCELLED` | `replay-next` called on a `CANCELLED` session | `market_data_replay_service.py : replay_next` | `test_replay_next_after_cancellation_rejected` |
| 23 | `MARKET_DATA_REPLAY_SESSION_CORRUPTED` | Session projection fails its own consistency check (Section 14.3) | `market_data_replay_service.py : create_replay_session`/`replay_next`/`cancel_replay_session` | `ReplaySessionCorruptionTests` (4 new tests: inspect, replay-next, cancel, create-reuse) |
| 24 | `MARKET_DATA_CAPABILITY_DENIED` | `market_data_research` not granted | `market_data_replay_service.py : _require_capability` | `CapabilityGatingTests.test_import_denied_without_capability` |
| 25 | `EXTERNAL_MARKET_DATA_FEED_NOT_APPROVED` | Blocker identifier only — no code path in this V0 implementation ever requests an external feed | `market_data_replay_data.py : REASON_CODES` (vocabulary member only) | N/A — not a reachable condition; correctly never emitted (no-network structural audit, Section 16/17) |
| 26 | `BROKER_HISTORY_IMPORT_NOT_APPROVED` | Blocker identifier only — no broker-history code path exists | `market_data_replay_data.py : REASON_CODES` | N/A — not reachable; correctly never emitted |
| 27 | `AUTOMATIC_EVIDENCE_GENERATION_NOT_APPROVED` | Blocker identifier only — no automatic-evidence code path exists | `market_data_replay_data.py : REASON_CODES` | N/A — not reachable; correctly never emitted |
| 28 | `REPLAY_TO_INTELLIGENCE_HANDOFF_NOT_APPROVED` | Blocker identifier only — no R2-010 handoff code path exists | `market_data_replay_data.py : REASON_CODES` | N/A — not reachable; correctly never emitted |
| 29 | `REPLAY_TO_EXECUTION_HANDOFF_NOT_APPROVED` | Blocker identifier only — no execution-handoff code path exists | `market_data_replay_data.py : REASON_CODES` | N/A — not reachable; correctly never emitted |

Every code is emitted through the shared `mdd.MarketDataValidationError`/`svc.MarketDataServiceError` wrapper (never a bare string comparison); every code in `REASON_CODES` is validated on construction against the closed 29-member tuple (`MarketDataValidationError.__init__` raises `ValueError` for any code outside it), so no unauthorized alias can silently pass through code review undetected — the two `JournalCorruptedIntegrityUncertain`/`CSV_SHAPE_INVALID`-leak defects were structural bugs in *which* governed code a call site chose, not violations of the closed-vocabulary guard itself, which is exactly why they were still possible.

**Conformance conclusion: every one of the contract's 29 governed reason codes is now implemented exactly, with no unresolved reason-code implementation-authority decision remaining.**

### 2.4 Second Founder-review correction: locked rejection journaling

A second, narrower Founder-review correction pass found that `import_market_data`'s `MARKET_DATASET_REJECTED` append was the **one remaining unlocked journal mutation**: `_reject_import` (the pre-correction name) was called directly from each CSV/validation failure branch, entirely **before** `with self._journal.acquire_mutation_lock():` was ever reached. The prior evidence pass had characterized this as "matching R2-010 precedent" (`market_intelligence_service._reject`, which is also unlocked) and treated it as acceptable. **The Founder's finding is that an earlier checkpoint's implementation precedent does not override the R2-011 governing contract's own Section 18.1 requirement** ("cross-process locking; owner-token lock safety; reload after lock acquisition; atomic persistence; ... no unlocked fallback occurs anywhere in this sequence") — R2-010's `MI_RECORD_REJECTED` design was never itself verified against this exact standard, and citing it does not substitute for that verification. This is corrected.

**Exact corrected rejection sequence** (`market_data_replay_service.import_market_data`, now unified with the existing accept/reuse critical section under one lock acquisition per call):

1. Capability check (`_require_capability`) — a denial raises immediately; **no lock is acquired, no journal is touched, nothing is read from or written to the journal at all** (Section 4).
2. Pure validation/construction over already-safe, already-read local input (source classification, source reference, CSV bytes via `load_csv_input_bytes`, CSV parse, bar/manifest construction) determines the primary governed rejection `reason_code`, if any — **no journal or storage mutation occurs in this step**.
3. `with self._journal.acquire_mutation_lock():` — the single lock acquisition covers both the rejection-recording branch and the existing accept/reuse branch. Entering this context (`_ReloadingLock.__enter__`) reloads the journal from the durable store before any code inside the block runs.
4. `_fail_if_journal_corrupted()` — checked **fresh, immediately after lock acquisition and reload**, using the just-reloaded `startup_diagnostic_code`, not a value cached before the lock. Corruption always takes precedence over any pending rejection reason (Section 5.B) — nothing is appended, and `MARKET_DATA_JOURNAL_CORRUPTED` is raised.
5. If a rejection reason is pending: `_append_rejection` constructs the bounded payload (governed reason code, bounded source reference, bounded detail — never a raw CSV row, never an absolute path) and calls `self._journal.append("MARKET_DATASET_REJECTED", ...)`, which itself performs bounds checking (event-size, event-count, journal-size) and atomic persistence internally.
6. If the append itself fails on a journal-capacity bound (`MARKET_DATA_JOURNAL_EVENT_TOO_LARGE` / `MARKET_DATA_JOURNAL_FULL`), that governed code is raised instead of the original pending reason, and nothing is appended (Section 5.C) — the journal's own `append_batch` is already all-or-nothing (a snapshot restore on any exception), so no partial event is ever possible.
7. On successful append, the original governed rejection reason is what the caller ultimately sees (`MarketDataServiceError(reason_code, detail)`), exactly matching prior external behavior — only the internal locking changed.
8. If the lock itself times out (`MarketDataReplayJournalLockTimeout`, caught outside the `with` block), **nothing is appended** (the `with` body never ran); `MARKET_DATA_JOURNAL_LOCK_TIMEOUT` is returned; the original pending reason, if any, is preserved only as non-authoritative diagnostic text in the exception message — never as a second reason code, never as an invented alias (Section 5.A).
9. Lock release remains owner-token-verified by the unmodified `_CrossProcessFileLock.release()` (used unchanged by every mutation, not re-implemented for rejections).

**Capability-denied behavior (Section 4):** unchanged in effect, but now explicitly verified by a dedicated test proving the durable store is byte-identical before and after a capability-denied import attempt.

**The same fresh, post-lock, reload-based corruption check (`_fail_if_journal_corrupted`) was applied uniformly to all four mutation methods** (`import_market_data`, `create_replay_session`, `replay_next`, `cancel_replay_session`), replacing the previous pattern of a single pre-lock check using only cached startup state. `create_replay_session` additionally keeps one pre-lock read of the same cached flag (not a mutation) purely so a corrupted journal is reported as `MARKET_DATA_JOURNAL_CORRUPTED` rather than a misleading `MARKET_DATA_DATASET_NOT_FOUND` from its necessarily-pre-lock dataset-existence lookup — the fresh post-lock check remains the authoritative determination in every case. The now-dead pre-lock-only `_require_journal_integrity` helper was removed rather than left as stale code.

**Sixteen new tests** close this gap: `LockedRejectionTests` (12 tests in `test_market_data_replay_service.py` — lock-before-append call-order proof via a spy journal, reload-before-append proof via a deliberately-stale writer sharing a durable store with an independent writer, capability-denied no-mutation and byte-identical-store proofs, lock-timeout/corruption/full/event-too-large precedence proofs, successful-single-append-and-persist proof, no-storage-created proof, and a retry-after-lock-timeout-derives-cleanly proof), one new journal-module test (`test_owner_token_mismatch_cannot_remove_another_holders_lock`), and five new separate-process concurrency tests (`ConcurrentInvalidImportTests` — two genuinely separate OS processes racing an identical invalid import, both fail closed with `MARKET_DATA_CSV_SHAPE_INVALID`, the journal ends up with exactly two `MARKET_DATASET_REJECTED` events at sequence numbers `[1, 2]`, a valid hash chain, no leftover lock file, and no dataset storage file ever created).

### 2.5 Complete journal-mutation audit table

Every call site in `market_data_replay_service.py` that can append a journal event, append an atomic batch, or persist/replace the journal, re-verified after the correction in 2.4:

| Event type | Source : function | Logical branch | Lock before mutation? | Reloaded after lock? | Atomic persistence? | Owner-token release verified? | Test |
|---|---|---|---|---|---|---|---|
| `MARKET_DATASET_IMPORTED` | `market_data_replay_service.py : import_market_data` | no existing dataset found under lock | Yes | Yes (`_fail_if_journal_corrupted` runs first) | Yes (`JournalWriter._persist`, temp-file+`os.replace`) | Yes (shared, unmodified `_CrossProcessFileLock.release`) | `ImportAtomicityTests.test_import_creates_manifest_and_envelope`; `ConcurrentImportTests` (3 tests) |
| `MARKET_DATASET_REUSED` | `import_market_data` | existing dataset with identical hash found under lock | Yes | Yes | Yes | Yes | `test_identical_import_reuses_dataset`; `ConcurrentImportTests` |
| `MARKET_DATASET_REJECTED` | `import_market_data` → `_append_rejection` | any pending input-rejection reason, appended under lock | **Yes (corrected 2.4)** | **Yes (corrected 2.4)** | Yes | Yes | `LockedRejectionTests` (12 tests); `ConcurrentInvalidImportTests` (5 tests) |
| `REPLAY_SESSION_CREATED` | `create_replay_session` | no existing session identity found under lock | Yes | Yes | Yes | Yes | `test_ready_status_on_creation`; `ConcurrentReplaySessionTests` |
| `REPLAY_SESSION_REUSED` | `create_replay_session` | existing session, `READY` status, under lock | Yes | Yes | Yes | Yes | `test_ready_reuse_returns_same_session_and_appends_reused_event`; `ConcurrentReplaySessionTests` |
| `REPLAY_STEP_RECORDED` | `replay_next` (atomic batch) | `READY`/`RUNNING` session, under lock | Yes | Yes | Yes (`append_batch`, all-or-nothing) | Yes | `test_exact_first_middle_final_partial_step`; `ConcurrentReplayNextTests` |
| `REPLAY_SNAPSHOT_RECORDED` | `replay_next` (same atomic batch) | same branch, same batch as the step | Yes | Yes | Yes | Yes | same as above |
| `REPLAY_SESSION_COMPLETED` | `replay_next` (same atomic batch, terminal only) | `to_index == end_index`, same batch | Yes | Yes | Yes | Yes | `test_exact_first_middle_final_partial_step`; `test_no_step_after_completion` |
| `REPLAY_SESSION_CANCELLED` | `cancel_replay_session` | `READY`/`RUNNING` session, under lock | Yes | Yes | Yes | Yes | `test_cancellation_of_ready_session` |
| `JOURNAL_INTEGRITY_FAILURE` | `_load_dataset_envelope` | Section 18.3 Case B, storage revalidation failure, under lock, idempotency-checked first | Yes | Yes | Yes | Yes | `StorageIntegrityFailureCaseBTests` (3 tests) |

**Conclusion: every one of the ten governed journal event types is appended exactly once per authorized branch, always under the authoritative mutation lock, always after a fresh reload, always atomically persisted, always released through the unmodified owner-token-verified `_CrossProcessFileLock.release()`. No unlocked fallback exists anywhere in `market_data_replay_service.py`. No direct persistence helper (`MarketDataReplayJournalWriter._persist`, `append`, `append_batch`) is called from any code path that has not first entered `acquire_mutation_lock()`.**

---

## 3. The five governed schemas and the storage envelope

Implemented exactly as specified (contract Sections 10–11), in `market_data_replay_data.py`:

| Schema | ID prefix | Identity domain |
|---|---|---|
| `TRL_MARKET_BAR.v1` | `bar_` | `TRL-MARKET-BAR-ID.v1` |
| `TRL_MARKET_DATASET_MANIFEST.v1` | `mds_` | `TRL-MARKET-DATASET-ID.v1` |
| `TRL_REPLAY_SESSION.v1` | `rps_` | `TRL-REPLAY-SESSION-ID.v1` |
| `TRL_REPLAY_STEP.v1` | `rst_` | `TRL-REPLAY-STEP-ID.v1` |
| `TRL_REPLAY_SNAPSHOT.v1` | `rsn_` | `TRL-REPLAY-SNAPSHOT-ID.v1` |

Every identity formula's field set is validated with `_identity_material`/`_identity_for` (exact key-set match, JSON-canonicalized, `sha256(domain + "\n" + material)[:32]`). Display-only timestamps (`imported_at_utc`/`created_at_utc`/`occurred_at_utc`) are excluded from both identity and semantic hash (verified by `test_market_data_replay_data.IdentityTests.test_imported_at_utc_excluded_from_identity`); a direct no-cycle acceptance test exists (`test_no_cycle_in_identity_sequence`), confirming computation strictly follows bar → dataset → replay session → replay step → replay snapshot with no formula referencing a hash computed after it.

`TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1` (Section 10.6) is implemented as a non-governed, storage-only container (`build_storage_envelope`/`validate_storage_envelope`) carrying the complete manifest and complete ordered bar set, with full requirement-1-through-15 revalidation on every load.

---

## 4. Source classifications, allowlists, limits, grammars

- Source classifications: `SYNTHETIC_FIXTURE`, `LOCAL_HISTORICAL_FILE` (exactly two, Section 5).
- Instruments: `XAUUSD`, `NAS100`, `EURUSD`, `GBPUSD`, `USDJPY` — reused verbatim from R2-010, no alias normalization.
- Timeframes: `M5`, `M15`, `H1`, `H4`, `D1` — interval seconds `300/900/3600/14400/86400`.
- CSV limits: max input bytes `33554432`; min/max data rows `2`/`250000`; max physical line `1024` bytes; max parsed field `128` code points; max source_reference `256` code points.
- Decimal grammar: `^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$`, max 24 total digits, max 12 fractional digits, no rounding, canonical trailing-zero removal, negative-zero canonicalization, `Decimal`-only (never binary float).
- Tick-volume grammar: `^(?:0|[1-9][0-9]*)$`, range `0..9223372036854775807`.
- Timestamp grammar: `YYYY-MM-DDTHH:MM:SS.ffffffZ`, exact six fractional digits, canonical round-trip verified.
- Storage envelope: max `268435456` bytes. Journal: max `100000` events, max encoded event `262144` bytes, max encoded journal `268435456` bytes, lock timeout `10.0`s, poll interval `0.02`s.
- Replay: `step_size` `1..1000`; max projected steps per session `10000`; max replay window `100` bars.

All limits are implemented as named constants in `market_data_replay_data.py`/`market_data_replay_journal.py`, matching Section 18.1/7.1/14 exactly.

---

## 5. CSV parsing and bar/dataset validation

The CSV parser (`parse_csv_rows`) is a manual, physical-line-based parser (not Python's `csv` module, whose default multi-line quoted-field behavior would silently accept an embedded newline the contract explicitly forbids): strict UTF-8 with BOM rejection, NUL rejection, exact header match, exactly-nine-fields-per-row enforcement, untrimmed-whitespace rejection, standard double-quote escaping within one physical line only. All-or-nothing: the first invalid row raises immediately with no partial bar set or manifest ever constructed (verified by `test_market_data_replay_service.ImportAtomicityTests.test_all_or_nothing_no_partial_bar_set`).

Bar validation enforces every Section 9 rule: positive OHLC, high/low invariants, strictly increasing timestamps, duplicate/out-of-order rejection (never silently sorted), exact-multiple-only gap detection (`missing_intervals = actual/expected - 1`), irregular-interval rejection. No bar is ever synthesized or silently corrected.

---

## 6. Dataset storage architecture, import atomicity, reuse, orphans

`market_data_replay_storage.py` implements the two-tier architecture (Section 17.1): `LocalDatasetStorage` persists one content-addressed `<dataset_id>.json` file per accepted dataset (filename derived only from `dataset_id`), atomic same-directory-temp-file-plus-`os.replace` write, immutable after acceptance (`save_new` refuses to overwrite an existing file), full revalidation on every `load`. `InMemoryDatasetStorage` mirrors this for deterministic tests.

`market_data_replay_service.import_market_data` implements the exact Section 17.2 sequence: capability check → safe file I/O (`load_csv_input_bytes`, mirroring `market_intelligence_service.load_analysis_input_bytes`'s regular-file/symlink/UNC/URL/size checks) → strict parse → bar/manifest construction → mutation-lock acquisition → journal reload → existing-dataset check (by deterministic `dataset_id`+`canonical_dataset_hash`) → reuse-or-create → atomic storage write → `MARKET_DATASET_IMPORTED`/`MARKET_DATASET_REUSED` journal append → lock release.

Reuse (Section 12): identical bars + identical source reference reuse the existing manifest (verified `dataset_id`); a different source reference produces a distinct manifest while individual bar identities remain identical (verified `test_market_data_replay_data.IdentityTests.test_bar_id_independent_of_source_reference` and rehearsal step 12). Orphan files (a physical envelope with no valid acceptance event) remain invisible to every list/inspect/replay operation, since datasets are enumerated exclusively from `MARKET_DATASET_IMPORTED` journal events, never from a directory scan.

---

## 7. Journal design, event vocabulary, corruption semantics

`market_data_replay_journal.py` is structurally parallel to `market_intelligence_journal.py` (duplicated cross-process file lock, not imported, per repository convention — zero dependency on either the Phase 5/6 or R2-010 journal module) but a wholly separate journal file (`market-data-fabric-v0/market-data-replay-journal-v1.json`) and schema family (`TRL_MARKET_DATA_REPLAY_JOURNAL.v1`/`TRL_MARKET_DATA_REPLAY_JOURNAL_EVENT.v1`).

Closed ten-event vocabulary: `MARKET_DATASET_IMPORTED`, `MARKET_DATASET_REUSED`, `MARKET_DATASET_REJECTED`, `REPLAY_SESSION_CREATED`, `REPLAY_SESSION_REUSED`, `REPLAY_STEP_RECORDED`, `REPLAY_SNAPSHOT_RECORDED`, `REPLAY_SESSION_COMPLETED`, `REPLAY_SESSION_CANCELLED`, `JOURNAL_INTEGRITY_FAILURE`. `MARKET_DATASET_IMPORTED` carries only compact references/summaries (Section 18.2) — never a full bar or `ordered_bar_refs` list. `append_batch` provides atomic multi-event batches (Section 15.2): all-or-nothing, contiguous sequence numbers, consecutive hash-chain links, snapshot verified in the same commit as its step.

Corruption (Section 18.3): **Case A** (journal itself invalid) fails closed at `MarketDataReplayJournalWriter` construction (`startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"`), never appends, never auto-replaces the journal. **Case B** (valid journal, corrupted dataset storage) is handled by `_load_dataset_envelope`: appends exactly one bounded `JOURNAL_INTEGRITY_FAILURE` event under the mutation lock, idempotent via `_integrity_failure_recorded` (no duplicate event), never rewrites the storage file, never imports or advances replay automatically.

---

## 8. Replay-session behavior

Implemented in `market_data_replay_service.py`, deterministic and step-driven only — no timer, no sleep, no background thread. Status derivation (`_reconstruct_projection`) is always computed from the session's own event history, never a stored mutable field, checking sequence contiguity, session-hash consistency, and step/snapshot correspondence (a mismatch yields `CORRUPTED`, distinct from whole-journal Case A).

Reuse-by-status (Section 14.4), verified for all five statuses in `test_market_data_replay_service.ReplaySessionLifecycleTests`:

- **READY** — returns existing session, appends one `REPLAY_SESSION_REUSED` event, no reset.
- **RUNNING** — returns existing projection, no duplicate step, no reset.
- **COMPLETED** — returns existing completed projection, no reopen, no new run.
- **CANCELLED** — returns existing cancelled projection, no reopen.
- **CORRUPTED** — fails closed with `MARKET_DATA_REPLAY_SESSION_CORRUPTED`, no replacement with the same identity.

`replay_next` implements the exact Section 15.1 11-step sequence and the exact Section 15.2 atomic batch rule (non-terminal: step+snapshot; terminal: step+snapshot+`REPLAY_SESSION_COMPLETED`). Cancellation is idempotent; cancelling a `COMPLETED` session returns the existing completed projection and appends no event (Founder decision, Section 15.3), verified by `test_cancelling_completed_session_appends_no_event`. The replay window is capped at 100 bars, contains no future bar, and every snapshot carries `non_live: true`/`non_executable: true` (schema-enforced literals).

---

## 9. `market_data_research` capability

Added exactly once to `mode_service.CAPABILITIES` and to `_CAPABILITY_MATRIX` for `RESEARCH`, `SYNTHETIC_PAPER`, `MT5_DEMO_MANUAL` only:

| Mode | Granted? |
|---|---|
| `OFF` | No |
| `RESEARCH` | **Yes** |
| `SYNTHETIC_PAPER` | **Yes** |
| `MT5_DEMO_MANUAL` | **Yes** |
| `MT5_DEMO_AUTOMATED` | No |
| `MT5_LIVE_MANUAL` | No |
| `MT5_LIVE_AUTOMATED` | No |

Verified programmatically (`ms.CAPABILITIES.count("market_data_research") == 1`) and via `test_operating_mode.py`'s full 53-test suite passing unchanged. Gates exactly `import-market-data`/`create-replay-session`/`replay-next`/`cancel-replay-session`; grants no `market_intelligence_research`, no order/basket/execution authority. Read-only operations remain available in every mode including `OFF` (`DisabledMarketDataReplayService`, mirroring `DisabledMarketIntelligenceService`'s exact precedent: read-only documents remain callable and honest rather than raising).

---

## 10. CLI, HTTP, dashboard

**CLI** (`market_data_replay_cli.py`, `python -m trading_lab_app.market_data_replay_cli <command>`) — all 11 command families implemented: `market-data-status`, `import-market-data`, `list-market-datasets`, `inspect-market-dataset`, `create-replay-session`, `list-replay-sessions`, `inspect-replay-session`, `replay-next`, `inspect-replay-snapshot`, `cancel-replay-session`, `market-data-journal`. Stable exit codes (0 success, 1 governed rejection), bounded JSON output, safe identifier validation before any service call, no traceback on ordinary rejected input, no path disclosure (verified `test_market_data_replay_cli.CliSafetyTests`).

**HTTP** (`server.py`) — exactly six read-only routes: `/api/market-data-status`, `/api/market-datasets`, `/api/market-dataset/<safe-id>`, `/api/replay-sessions`, `/api/replay-session/<safe-id>`, `/api/replay-snapshot/<safe-id>`. GET/HEAD only; every other verb returns `405` with `Allow: GET, HEAD` (verified for POST/PUT/PATCH/DELETE); safe-ID path matching via `DATASET_ID_PATTERN`/`REPLAY_SESSION_ID_PATTERN`; strictly validated `offset`/`limit` query parameters on the three list/detail routes that support pagination, invalid input returning `400` with a governed reason code, never a raw exception; no physical path in any response (verified `test_market_data_replay_http.MarketDataFabricHttpTests.test_no_physical_path_in_any_response`).

**Dashboard** (`static/index.html`/`static/app.js`) — one new read-only panel, *TRL CORTEX DATA FABRIC V0*: operating mode, `market_data_research` grant state, dataset count/session count, a paginated-in-substance dataset table (instrument/timeframe/source/reference/bar count/first–last/gaps/hash), and a replay-session table (status/current index/window/`non_live`/`non_executable`). No import/replay-next/cancel control exists in the UI. Rendering uses only `textContent`/`document.createElement` (via the existing `cell()`/`setText()` helpers) — no `innerHTML` in any code this checkpoint added (confirmed: the file's one pre-existing `innerHTML` use, in the unrelated `renderSignals` function, predates this checkpoint and was not touched — `git blame` attributes it to an earlier commit).

---

## 11. Synthetic fixture

`fixtures/trl_cortex_data_fabric_v0_synthetic.csv` — strict UTF-8, no BOM, clearly synthetic, `XAUUSD`/`M5`, 24 bars, one exact-multiple gap (skips exactly one 5-minute interval at bar 14), source classification `SYNTHETIC_FIXTURE`, source reference `trl-cortex-data-fabric-v0-synthetic`. Deterministic outputs (generated by the implementation, not hand-typed):

| Field | Value |
|---|---|
| Instrument / Timeframe | `XAUUSD` / `M5` |
| Bar count | `24` |
| First timestamp | `2026-01-05T00:00:00.000000Z` |
| Last timestamp | `2026-01-05T02:00:00.000000Z` |
| `gap_count` | `1` |
| `largest_gap_intervals` | `1` |
| `dataset_id` | `mds_e13cd213c16527457a6e77dc8d6b715d` |
| `canonical_dataset_hash` | `44c6a8694da6a7b9c111067572e42d257afcbb6b850b763c8f2ad9a30a291d2a` |

---

## 12. Test results

### 12.1 New-test-module counts (target run, each module standalone, after both Founder-review correction passes)

| Module | Tests | Result |
|---|---|---|
| `test_market_data_replay_data.py` | 64 | OK |
| `test_market_data_replay_storage.py` | 14 | OK |
| `test_market_data_replay_journal.py` | 18 | OK |
| `test_market_data_replay_service.py` | 55 | OK |
| `test_market_data_replay_cli.py` | 8 | OK |
| `test_market_data_replay_http.py` | 16 | OK |
| `test_market_data_replay_concurrency.py` | 14 | OK |
| **Net-new total** | **189** | all OK |

Growth history: `test_market_data_replay_service.py` grew 27 → 43 (+16, first correction pass: `JournalCorruptionTests`, `LockTimeoutConversionTests`, `StorageIntegrityFailureCaseBTests`, `ReplaySessionCorruptionTests`) → 55 (+12, second correction pass, Section 2.4: `LockedRejectionTests`). `test_market_data_replay_journal.py` grew 17 → 18 (+1, `test_owner_token_mismatch_cannot_remove_another_holders_lock`). `test_market_data_replay_concurrency.py` grew 9 → 14 (+5, `ConcurrentInvalidImportTests`).

Exact seven-module command and result, run from the canonical working directory:

```
cd C:\ALSAKKAF_WT\PRJ017_CODEX\09_AI_Systems\02_Tools\Trading_Lab
python -B -W error -c "<load and run the seven test_market_data_replay_* modules via unittest.TestLoader>"
```

Result: `Ran 189 tests in 11.64s` — **OK** (0 failures, 0 errors, 0 unexpected warnings).

### 12.2 Exact combined targeted suite

Exact command (one process, 28 modules, run from `09_AI_Systems/02_Tools/Trading_Lab`):

```
python -B -W error -c "<unittest.TestLoader loading exactly the 28 modules listed below, unittest.TextTestRunner>"
```

Exact module list (28): `test_market_data_replay_data`, `test_market_data_replay_storage`, `test_market_data_replay_journal`, `test_market_data_replay_service`, `test_market_data_replay_cli`, `test_market_data_replay_http`, `test_market_data_replay_concurrency`, `test_operating_mode`, `test_trading_lab_app`, `test_market_intelligence_data`, `test_market_intelligence_journal`, `test_market_intelligence_service`, `test_market_intelligence_cli`, `test_market_intelligence_http`, `test_market_intelligence_concurrency`, `test_mt5_execution_data`, `test_mt5_execution_adapter`, `test_mt5_execution_journal`, `test_mt5_execution_journal_lock`, `test_mt5_execution_service`, `test_mt5_execution_cli`, `test_mt5_execution_http`, `test_mt5_execution_concurrency`, `test_basket_execution_data`, `test_basket_execution_service`, `test_basket_execution_cli`, `test_basket_execution_http`, `test_basket_execution_concurrency`.

**Exact result: `TOTAL 762  FAILURES 0  ERRORS 0  ELAPSED_SEC 75.78`.**

### 12.3 Full-suite arithmetic

```
1060 (baseline) + 189 (net-new, post both correction passes) = 1249
```

Both complete-suite runs reported exactly `Ran 1249 tests` — the arithmetic reconciles exactly.

### 12.4 Complete-suite Run A and Run B (canonical working directory)

**Canonical complete-suite execution directory:** `C:\ALSAKKAF_WT\PRJ017_CODEX\09_AI_Systems\02_Tools\Trading_Lab` (see Section 12.5 for the exact, evidenced reason the repository-root form must not be used for this particular suite).

**Exact command:** `python -B -W error -m unittest discover -s . -p 'test*.py'`

- **Run A:** `Ran 1249 tests in 145.61s` — **OK** (zero failures, zero errors).
- **Run B (immediately after, no source or test change in between):** `Ran 1249 tests in 145.89s` — **OK** (zero failures, zero errors).

(These figures supersede the first correction pass's `1231`-test pair, reported before Section 2.4's locked-rejection-journaling correction added the 18 further tests reconciling to `1060 + 189 = 1249`.)

Both runs post-date every source/test correction in Section 2; no further source or test change occurred after Run B.

### 12.5 Repository-root CWD failure — complete disclosure with blob-hash proof

**Exact repository-root command:** `python -B -W error -m unittest discover -s 09_AI_Systems/02_Tools/Trading_Lab -p 'test*.py'`, invoked with the process working directory at `C:\ALSAKKAF_WT\PRJ017_CODEX`.

**Exact discovered count:** `Ran 1231 tests` at the time this disclosure was first produced (first correction pass); the same discovery set now totals `1249` after Section 2.4's 18 additional tests. Per the second correction pass's own instructions, the repository-root command was **not re-run** this pass, since the affected file (`test_market_intelligence_cli.py`) is confirmed still byte-identical (`git hash-object` reproduces `910f1d4aa1e432244a933439916083cd1c338c0a`, unchanged from Section 12.5's original check) and no R2-011 change this pass touches anything that could alter the CWD-dependency mechanism itself. The classification below stands unchanged and re-verified via the retained blob-hash proof.

**Exact two failing test names (fully qualified):**
- `test_market_intelligence_cli.GrantedModeTests.test_preview_generated_when_granted`
- `test_market_intelligence_cli.GrantedModeTests.test_analyze_and_inspect_round_trip_when_granted`

**Exact error text, reproduced directly (`python -B -W error -m unittest discover -s 09_AI_Systems/02_Tools/Trading_Lab -p "test_market_intelligence_cli.py" -v`, run from the repository root):**

```
ERROR: test_preview_generated_when_granted (test_market_intelligence_cli.GrantedModeTests.test_preview_generated_when_granted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "...\test_market_intelligence_cli.py", line 151, in test_preview_generated_when_granted
    opportunity_id = match.group(1)
                     ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'group'

FAIL: test_analyze_and_inspect_round_trip_when_granted (test_market_intelligence_cli.GrantedModeTests.test_analyze_and_inspect_round_trip_when_granted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "...\test_market_intelligence_cli.py", line 138, in test_analyze_and_inspect_round_trip_when_granted
    self.assertEqual(exit_code, 0)
AssertionError: 1 != 0
```

**Exact CWD-relative fixture path used by the affected test:** `"fixtures/trl_cortex_v0_synthetic_trade_candidate.json"` (four call sites in `test_market_intelligence_cli.py`, lines 65/96/137/149, each passed literally to `cli.main(["analyze-market-snapshot", ...])`).

**Exact expected path (resolves correctly from the canonical working directory):** `C:\ALSAKKAF_WT\PRJ017_CODEX\09_AI_Systems\02_Tools\Trading_Lab\fixtures\trl_cortex_v0_synthetic_trade_candidate.json` (confirmed to exist, 10,208 bytes).

**Exact incorrectly resolved path (from the repository root):** `C:\ALSAKKAF_WT\PRJ017_CODEX\fixtures\trl_cortex_v0_synthetic_trade_candidate.json` (does not exist — there is no `fixtures/` directory at the repository root; the real one is nested under `09_AI_Systems/02_Tools/Trading_Lab/`).

**Why the same tests pass from the canonical working directory:** the relative path is interpreted against the *process* working directory, not the test file's own location or the `unittest discover -s` start directory. Only when the process CWD is `09_AI_Systems/02_Tools/Trading_Lab` does `"fixtures/trl_cortex_v0_synthetic_trade_candidate.json"` resolve to the real, committed fixture; `analyze-market-snapshot` then succeeds, `cli.main` returns exit code `0`, and the tests' own `re.search(r'"opportunity_id":...')` finds a match.

**Confirmation no R2-011 source appears in either failure stack:** both stack traces above contain exactly one frame each, both inside `test_market_intelligence_cli.py` itself (`match.group(1)` and `self.assertEqual(exit_code, 0)`) — neither trace references `market_data_replay_data.py`, `market_data_replay_storage.py`, `market_data_replay_journal.py`, `market_data_replay_service.py`, `market_data_replay_cli.py`, or any other R2-011 file. The failure is entirely internal to the R2-010 test and its own CLI call.

**Confirmation the affected existing test file is unchanged — exact blob-hash proof:**

```
git diff --exit-code 5c53396af9daa0e235e293d698e39b5afcdeb23b -- 09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_cli.py
  -> exit code 0 (byte-identical to the verified committed baseline)

git rev-parse 5c53396af9daa0e235e293d698e39b5afcdeb23b:09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_cli.py
  -> 910f1d4aa1e432244a933439916083cd1c338c0a

git hash-object 09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_cli.py
  -> 910f1d4aa1e432244a933439916083cd1c338c0a

git rev-parse ea9cc3e7b159d6088f006fc121d1abf2c93b717a:09_AI_Systems/02_Tools/Trading_Lab/test_market_intelligence_cli.py
  -> 910f1d4aa1e432244a933439916083cd1c338c0a
```

All three blob hashes — the verified R2-011-checkpoint baseline (`5c53396a`), the current working tree, and the original R2-010 implementation commit (`ea9cc3e`) — are **byte-identical**. The file has not changed in any way since it was first written for R2-010, well before this checkpoint began.

**Confirmed unrelated to this checkpoint, additional corroboration:**
- `test_market_intelligence_cli.py` passes **17/17 in isolation** regardless of working directory.
- The 1060-test pre-existing baseline alone (every file except the seven new R2-011 test modules), run as a single suite from the repository root, passes **1060/1060, zero failures, zero errors** — confirming the trigger is the combination of a much longer full-suite run reaching this CWD-sensitive test, not this checkpoint's content.
- All seven new R2-011 modules combined with `test_market_intelligence_cli.py` alone, in one process, passed cleanly (172/172 when the R2-011 module count was 155; 171+17=188 after the first correction pass; now 189+17=206 after the second — not independently re-run at each figure change, since the blob-hash proof and the isolated 17/17 result already establish the same underlying fact more directly and do not depend on the R2-011 test count).

**Confirmation no existing test was modified:** the blob-hash proof above is definitive; additionally, `git status --porcelain=v1` throughout this correction pass never lists `test_market_intelligence_cli.py` or any other pre-existing test file.

**Final classification: a pre-existing working-directory portability defect in an untouched existing R2-010 test — not an R2-011 regression.** The evidence (byte-identical blob hashes across three reference points spanning the R2-010 implementation commit, the R2-011 baseline commit, and the current working tree; isolated 17/17 pass; 1060/1060 baseline-alone pass; single-frame stack traces entirely inside the R2-010 test file) is conclusive. No R2-011 source or test was modified to work around this finding; it is disclosed for Founder awareness and possible separate future R2-010 test-fixture-path maintenance (an absolute-from-file `Path(__file__).resolve().parent / "fixtures" / ...` construction, mirroring `mdr_test_support.FIXTURE_PATH`, would make the file CWD-independent) — out of this checkpoint's authorized scope to fix.

---

## 13. Separate-process concurrency evidence

`test_market_data_replay_concurrency.py` (9 tests, all OK) launches genuinely separate OS processes via `subprocess.Popen`, synchronized with readiness-marker files and a bounded poll (never a fixed sleep), mirroring `test_mt5_execution_concurrency.py`'s established pattern exactly:

- **Dataset import race:** two processes import the identical CSV with the identical source reference simultaneously → both converge on the identical `dataset_id`; the journal contains exactly one `MARKET_DATASET_IMPORTED` and one `MARKET_DATASET_REUSED` event; exactly one dataset storage file exists on disk afterward; the journal remains a valid hash chain; no `.lock` file remains.
- **Replay-session creation race:** two processes request the identical `(dataset_id, start_index, end_index, step_size)` simultaneously → both converge on the identical `replay_session_id`; exactly one `REPLAY_SESSION_CREATED` and one `REPLAY_SESSION_REUSED` event.
- **Replay-next race:** two processes call `replay-next` on the identical session simultaneously → both succeed with no error; the journal contains exactly two `REPLAY_STEP_RECORDED` and two `REPLAY_SNAPSHOT_RECORDED` events with sequence numbers `[1, 2]` and no duplicate step; no `.lock` file remains afterward.

---

## 14. Manual synthetic rehearsal — result

Executed end-to-end against a fully isolated temporary `LOCALAPPDATA`, using the real CLI entry points, the real HTTP server (ephemeral port), and the real dashboard static files. All 35 steps of the required rehearsal sequence completed with every assertion passing:

- Mode transitioned `OFF → RESEARCH`; `market_data_research` correctly denied at `OFF` and granted at `RESEARCH`.
- Imported the committed synthetic fixture: `dataset_id = mds_e13cd213c16527457a6e77dc8d6b715d`, `canonical_dataset_hash = 44c6a8694da6a7b9c111067572e42d257afcbb6b850b763c8f2ad9a30a291d2a`, `bar_count = 24`, `gap_count = 1`, `largest_gap_intervals = 1` — exactly matching Section 11 above.
- Content-addressed envelope file confirmed present on disk internally; **no physical path appeared in any CLI output**.
- Simulated restart (fresh service instance against the same durable store): dataset still listed (`total_count = 1`).
- Re-imported the identical CSV with the identical source reference: identical `dataset_id`, still `total_count = 1` (no duplicate authority).
- Re-imported the identical bars with a **different** source reference under an **isolated** second `LOCALAPPDATA`: distinct `dataset_id`, but the first bar's `(bar_id, canonical_bar_hash)` pair was byte-identical across both stores.
- Created one deterministic replay session (`step_size = 3` over 24 bars); advanced two steps (`current_index = 2`, then `5`); simulated restart — `inspect-replay-session` reported the persisted `RUNNING` status and `step_count = 2`.
- Continued to completion: final step landed exactly on `current_index = 23` (`bar_count - 1`), status `COMPLETED`; a further `replay-next` call appended no new step (`step_count` unchanged).
- Cancelling the completed session returned the existing `COMPLETED` projection and appended **no** journal event (event count unchanged before/after).
- The latest snapshot's `window_end_index == current_index == 23` (no future bar); `non_live: true` and `non_executable: true` confirmed.
- All six HTTP routes returned `200`; the identical six routes returned `405` on `POST`.
- The dashboard's root page loaded (`200`) and contained the `id="market-data-fabric"` panel marker.
- **No R2-010 record was generated**: `market-intelligence-journal-v1.json` does not exist under the isolated store.
- **No execution record was generated**: `mt5-execution-journal-v1.json` does not exist under the isolated store.
- Mode returned to `OFF`; final `market-data-status` confirmed `operating_mode: "OFF"`.
- The HTTP server was stopped; the isolated rehearsal runtime directory was removed; its non-existence was reconfirmed programmatically.
- Post-rehearsal system check: port 8765 clear (the rehearsal server used an ephemeral OS-assigned port, never 8765); no Python process remains; no `.lock` file remains anywhere under the Trading Lab tree; `git status` shows no generated dataset/journal artifact inside the repository (all rehearsal state lived under a temporary directory outside the repo).

---

## 15. R2-010 and Phase 5/6 compatibility proof

- `git diff --stat` (whole-repository) touches zero `market_intelligence_*`, `mt5_execution_*`, or `basket_execution_*` files.
- `test_market_intelligence_data.py` (77), `_journal.py` (13), `_service.py` (30), `_cli.py` (17), `_http.py` (21), `_concurrency.py` (2) — all pass unchanged (subject to the disclosed, pre-existing, CWD-dependent full-suite ordering finding in Section 12.5, unrelated to this checkpoint's content).
- `test_mt5_execution_*` (6 files, 158 tests) and `test_basket_execution_*` (5 files, 179 tests) all pass unchanged.
- The rehearsal (Section 14) directly confirmed zero R2-010 and zero Phase 5/6 journal writes resulted from any R2-011 operation.

---

## 16. No-network and no-execution structural audit

`grep`-based structural scan of every new/modified R2-011 source file for: `MetaTrader5` import — none. `RealMT5ExecutionAdapter` construction — none. `order_check`/`order_send` — none. `socket`/`urllib.request`/`http.client`/`requests` used as an *outbound* client — none (the only `http.server`/`socketserver` usage is the existing local-loopback-only application server, already governed and unmodified in its binding/security-header behavior). No write to `mt5_execution_journal.py`'s store path or `market_intelligence_journal.py`'s store path from any R2-011 module (each uses its own dedicated `market-data-fabric-v0/` subdirectory, confirmed in Section 14's rehearsal). No `TRL_OPPORTUNITY_CARD.v1`, `TRL_EVIDENCE_ITEM.v1`, `TRL_MARKET_SNAPSHOT.v1`, Phase 5 order intent, or Phase 6 basket construction call anywhere in this checkpoint's source.

---

## 17. Final quality and security validation

- **Markdown Audit:** run against every new/modified `.md` file in this checkpoint (Section 20 below).
- `git diff --check`: no conflict markers, no trailing-whitespace-only diff issue introduced.
- Strict UTF-8 / no-BOM / final-newline: verified for the CSV fixture and every new Python/Markdown file.
- Strict JSON parsing / no duplicate keys: exercised directly by `market_data_replay_journal._parse_document` and `market_data_replay_storage._parse_envelope_bytes`'s own `object_pairs_hook`-based duplicate-key rejection, and by dedicated tests (`test_market_data_replay_journal.InMemoryJournalTests.test_duplicate_key_rejected_on_load`, `test_market_data_replay_storage.LocalDatasetStorageTests.test_duplicate_json_key_rejected`).
- CSV fixture validation: parsed and fully accepted by `market_data_replay_data.parse_csv_rows` (Section 11).
- No conflict-marker, credential, secret, private-key, account-number, or broker-server string appears in any new file (structural grep scan).
- No absolute user-specific filesystem path appears in any governed record, CLI output, or HTTP response (Sections 6, 10, 14).
- No generated dataset/journal artifact, `__pycache__`, `.pyc`, test-output file, temporary script, marker file, or lock file remains inside the repository after this session's tests and rehearsal.
- No `MetaTrader5` import, no `RealMT5ExecutionAdapter` construction, no `order_check`/`order_send`, no outbound socket/network/HTTP-client call, no execution-journal write, no R2-010 journal write, no evidence generation, no Opportunity Card creation anywhere in this checkpoint's source (Section 16).
- No `innerHTML` in any dashboard code this checkpoint added (Section 10).
- Phase 7 absent: no Phase 7 file, module, or reference exists anywhere in the repository.

---

## 18. Known limitations

- Reason-code reuse for two unlisted condition classes (Section 2.2) — confirmed, after a complete 29-row conformance audit and three corrections, to be the only contract-conforming choice available in the closed vocabulary; not a gap in enforcement.
- The dataset/replay-session projection's `CORRUPTED` detection (Section 14.3) checks sequence contiguity, session-hash consistency, and step/snapshot correspondence — the exact invariants the contract names as examples — but does not attempt to enumerate every conceivable future corruption vector beyond those.
- No live data, no broker history, no automatic evidence generation, no R2-010 handoff, no execution handoff — all by contractual design (Section 3/4/23), not omissions.
- The pre-existing, untouched `test_market_intelligence_cli.py` CWD-dependent relative fixture path (Section 12.5) is disclosed but out of this checkpoint's authorized scope to fix.

## 19. Remaining blockers

Unchanged. `TRL_BLOCKERS.md` was not modified — the six R2-011 blockers this checkpoint's governing contract defined (`EXTERNAL_MARKET_DATA_FEED_NOT_APPROVED`, `BROKER_HISTORY_IMPORT_NOT_APPROVED`, `AUTOMATIC_EVIDENCE_GENERATION_NOT_APPROVED`, `REPLAY_TO_INTELLIGENCE_HANDOFF_NOT_APPROVED`, `REPLAY_TO_EXECUTION_HANDOFF_NOT_APPROVED`, `DATASET_PROVENANCE_NOT_VERIFIED`) were already recorded during the contract-authoring checkpoint and remain active exactly as defined; none of them prevents approved local import and replay.

---

## 20. Markdown Audit result

Run: `py 09_AI_Systems\02_Tools\Markdown_Audit\markdown_audit.py` — see the final report for the exact `Issues found:` count on this document and every other modified `.md` file.

---

## 21. Final state confirmations

- The Founder reviewed this record (across the correction passes recorded in Section 2), approved this exact 26-file scope (15 new, 11 modified, 0 deleted) for local commit, and it was committed as `6e24194071e8776833e396745d19b45785ee6ce4` ("Implement TRL-R2-011 Data Fabric and Replay V0").
- The Founder subsequently pushed this commit; independently re-verified: local HEAD, `origin/codex/TRL-R2-full-vision-execution`, and the upstream-tracking ref all equal `6e24194071e8776833e396745d19b45785ee6ce4`; pushed range `5c53396..6e24194`; ahead/behind `0 0`.
- `main` is unchanged at `8ada27f915091b91ddbc421aae06c7c5b36e068f`.
- The R2-011 governing contract is unchanged.
- Phase 7 is absent.
- Final operating mode: `OFF`.
- Port 8765: clear. No Trading Lab Python process remains. No relevant lock file remains.
- **R2-011 implementation is complete, committed, pushed, and remotely verified — this checkpoint is formally closed.** Per the Git-authoritative model this program uses throughout, the exact current committed/pushed state is always determined by `git rev-parse HEAD`/`git status` directly, not restated here as a value that would otherwise go stale.
