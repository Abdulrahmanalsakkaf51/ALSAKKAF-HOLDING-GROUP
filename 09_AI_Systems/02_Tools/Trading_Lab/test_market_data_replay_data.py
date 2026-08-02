"""Tests for TRL-R2-011 Market Data Fabric and Replay V0 -- data/validation/
identity module (``market_data_replay_data.py``). Covers contract Section
25 categories A (input/path safety -- CSV grammar), B (decimal/timestamp/
volume grammar), C (bar/dataset validation), and D (identities/hashes).
"""

import unittest

import mdr_test_support as support
from trading_lab_app import market_data_replay_data as mdd


HEADER = mdd.CSV_HEADER + "\n"


def _row(instrument="XAUUSD", timeframe="M5", ts="2026-01-01T00:00:00.000000Z",
         open_="1900.00", high="1901.00", low="1899.00", close="1900.50",
         spread="0.20", volume="100"):
    return ",".join([instrument, timeframe, ts, open_, high, low, close, spread, volume])


class CsvShapeTests(unittest.TestCase):
    def test_exact_header_accepted(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(interval, 300)
        self.assertEqual(gap_count, 0)
        self.assertEqual(largest_gap, 0)

    def test_wrong_header_order_rejected(self):
        bad = "timeframe,instrument,observed_at_utc,open,high,low,close,spread,tick_volume\n"
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(bad.encode("utf-8"))

    def test_missing_column_rejected(self):
        bad = "instrument,timeframe,observed_at_utc,open,high,low,close,spread\n"
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(bad.encode("utf-8"))

    def test_unknown_column_rejected(self):
        bad = HEADER.rstrip("\n") + ",extra\n"
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(bad.encode("utf-8"))

    def test_blank_row_rejected(self):
        raw = (HEADER + _row() + "\n\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_comment_row_rejected(self):
        raw = (HEADER + "# a comment\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_nul_byte_rejected(self):
        raw = (HEADER + _row() + "\n").encode("utf-8") + b"\x00"
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_embedded_newline_in_quoted_field_rejected(self):
        raw = HEADER.encode("utf-8") + b'"XAU\nUSD",M5,2026-01-01T00:00:00.000000Z,1900,1901,1899,1900,0,100\n'
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_bom_rejected(self):
        raw = b"\xef\xbb\xbf" + (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_invalid_utf8_rejected(self):
        raw = HEADER.encode("utf-8") + b"\xff\xfe,M5,2026-01-01T00:00:00.000000Z,1900,1901,1899,1900,0,100\n"
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_byte_limit_enforced(self):
        oversized = b"x" * (mdd.MAX_CSV_BYTES + 1)
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(oversized)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_INPUT_FILE_TOO_LARGE")

    def test_line_length_limit_enforced(self):
        raw = (HEADER + _row() + ("x" * mdd.MAX_PHYSICAL_LINE_BYTES) + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(raw)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_CSV_LINE_TOO_LONG")

    def test_field_length_limit_enforced(self):
        raw = (HEADER + _row(instrument="X" * (mdd.MAX_FIELD_CODEPOINTS + 1)) + "\n"
               + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(raw)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_CSV_FIELD_TOO_LONG")

    def test_minimum_rows_enforced(self):
        raw = (HEADER + _row() + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_maximum_rows_enforced(self):
        rows = [HEADER.rstrip("\n")]
        for index in range(mdd.MAX_DATA_ROWS + 1):
            rows.append(_row(ts="2026-01-01T{:02d}:{:02d}:00.000000Z".format((index * 5) // 60 % 24, (index * 5) % 60)))
        raw = ("\n".join(rows) + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_untrimmed_whitespace_rejected(self):
        raw = (HEADER + _row(instrument=" XAUUSD") + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_instrument_alias_rejected(self):
        raw = (HEADER + _row(instrument="XAU/USD") + "\n" + _row(instrument="XAU/USD", ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_timeframe_alias_rejected(self):
        raw = (HEADER + _row(timeframe="5M") + "\n" + _row(timeframe="5M", ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_mixed_instrument_in_one_file_rejected(self):
        raw = (HEADER + _row() + "\n" + _row(instrument="EURUSD", ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_every_approved_instrument_accepted(self):
        for instrument in mdd.INSTRUMENTS:
            raw = (HEADER + _row(instrument=instrument) + "\n" + _row(instrument=instrument, ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
            rows, _interval, _gap, _largest = mdd.parse_csv_rows(raw)
            self.assertEqual(rows[0]["instrument"], instrument)

    def test_every_approved_timeframe_accepted(self):
        for timeframe in mdd.TIMEFRAMES:
            seconds = mdd.TIMEFRAME_SECONDS[timeframe]
            from datetime import datetime, timedelta, timezone
            t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
            t1 = t0 + timedelta(seconds=seconds)
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            raw = (HEADER + _row(timeframe=timeframe, ts=t0.strftime(fmt)) + "\n"
                   + _row(timeframe=timeframe, ts=t1.strftime(fmt)) + "\n").encode("utf-8")
            rows, interval, _gap, _largest = mdd.parse_csv_rows(raw)
            self.assertEqual(interval, seconds)


class DecimalGrammarTests(unittest.TestCase):
    def test_valid_decimal_canonicalizes_trailing_zeros(self):
        self.assertEqual(mdd.parse_market_decimal("1900.500", "open", positive=True, allow_zero=False), "1900.5")

    def test_negative_zero_canonicalizes(self):
        self.assertEqual(mdd.parse_market_decimal("-0.00", "spread", positive=True, allow_zero=True), "0")

    def test_leading_zero_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal("01900.50", "open", positive=True, allow_zero=False)

    def test_plus_sign_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal("+1900.50", "open", positive=True, allow_zero=False)

    def test_exponent_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal("1.9e3", "open", positive=True, allow_zero=False)

    def test_whitespace_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal(" 1900.50", "open", positive=True, allow_zero=False)

    def test_digit_limit_enforced(self):
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_market_decimal("1" * 25, "open", positive=True, allow_zero=False)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_DECIMAL_DIGIT_LIMIT_EXCEEDED")

    def test_scale_limit_enforced(self):
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_market_decimal("1." + "1" * 13, "open", positive=True, allow_zero=False)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_DECIMAL_SCALE_EXCEEDED")

    def test_zero_open_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal("0", "open", positive=True, allow_zero=False)

    def test_zero_spread_allowed(self):
        self.assertEqual(mdd.parse_market_decimal("0", "spread", positive=True, allow_zero=True), "0")

    def test_negative_spread_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal("-0.01", "spread", positive=True, allow_zero=True)

    def test_boolean_rejected_as_numeric(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_market_decimal(True, "open", positive=True, allow_zero=False)


class TimestampGrammarTests(unittest.TestCase):
    def test_valid_timestamp_round_trips(self):
        mdd.validate_market_timestamp("2026-01-01T00:00:00.000000Z")

    def test_missing_fractional_seconds_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_market_timestamp("2026-01-01T00:00:00Z")

    def test_numeric_offset_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_market_timestamp("2026-01-01T00:00:00.000000+00:00")

    def test_invalid_calendar_date_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_market_timestamp("2026-02-30T00:00:00.000000Z")


class TickVolumeGrammarTests(unittest.TestCase):
    def test_valid_volume(self):
        self.assertEqual(mdd.parse_tick_volume("0"), 0)
        self.assertEqual(mdd.parse_tick_volume(str(mdd.MAX_TICK_VOLUME)), mdd.MAX_TICK_VOLUME)

    def test_leading_zero_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_tick_volume("0100")

    def test_negative_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_tick_volume("-1")

    def test_decimal_point_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_tick_volume("100.0")

    def test_out_of_range_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_tick_volume(str(mdd.MAX_TICK_VOLUME + 1))
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE")

    def test_boolean_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_tick_volume(True)


class BarValidationTests(unittest.TestCase):
    def test_high_below_low_rejected(self):
        raw = (HEADER + _row(high="1800", low="1899") + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(raw)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_DECIMAL_GRAMMAR_INVALID")

    def test_open_above_high_rejected(self):
        raw = (HEADER + _row(open_="1950", high="1901") + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.parse_csv_rows(raw)

    def test_duplicate_timestamp_rejected(self):
        raw = (HEADER + _row() + "\n" + _row() + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(raw)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_DUPLICATE_TIMESTAMP")

    def test_out_of_order_rejected_not_silently_sorted(self):
        raw = (HEADER + _row(ts="2026-01-01T00:05:00.000000Z") + "\n" + _row(ts="2026-01-01T00:00:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(raw)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_TIMESTAMP_OUT_OF_ORDER")

    def test_irregular_interval_rejected(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:07:00.000000Z") + "\n").encode("utf-8")
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.parse_csv_rows(raw)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_IRREGULAR_INTERVAL")

    def test_valid_gap_recorded_not_filled(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:15:00.000000Z") + "\n").encode("utf-8")
        rows, _interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        self.assertEqual(len(rows), 2)
        self.assertEqual(gap_count, 1)
        self.assertEqual(largest_gap, 2)

    def test_largest_gap_tracks_maximum(self):
        raw = (HEADER + _row(ts="2026-01-01T00:00:00.000000Z") + "\n"
               + _row(ts="2026-01-01T00:10:00.000000Z") + "\n"
               + _row(ts="2026-01-01T00:35:00.000000Z") + "\n").encode("utf-8")
        rows, _interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        self.assertEqual(gap_count, 2)
        self.assertEqual(largest_gap, 4)


class IdentityTests(unittest.TestCase):
    def _built(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        bars = [mdd.build_bar_record(row, "SYNTHETIC_FIXTURE") for row in rows]
        manifest = mdd.build_dataset_manifest_record(
            bars, "SYNTHETIC_FIXTURE", "ident-test", interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z",
        )
        return bars, manifest

    def test_bar_id_is_process_and_restart_stable(self):
        bars1, _ = self._built()
        bars2, _ = self._built()
        self.assertEqual(bars1[0]["bar_id"], bars2[0]["bar_id"])
        self.assertEqual(bars1[0]["canonical_bar_hash"], bars2[0]["canonical_bar_hash"])

    def test_bar_id_matches_pattern(self):
        bars, _ = self._built()
        self.assertRegex(bars[0]["bar_id"], r"^bar_[0-9a-f]{32}$")

    def test_bar_id_independent_of_source_reference(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        bars_a = [mdd.build_bar_record(row, "SYNTHETIC_FIXTURE") for row in rows]
        manifest_a = mdd.build_dataset_manifest_record(bars_a, "SYNTHETIC_FIXTURE", "ref-a", interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z")
        manifest_b = mdd.build_dataset_manifest_record(bars_a, "SYNTHETIC_FIXTURE", "ref-b", interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z")
        self.assertEqual(bars_a[0]["bar_id"], bars_a[0]["bar_id"])
        self.assertNotEqual(manifest_a["dataset_id"], manifest_b["dataset_id"])

    def test_dataset_id_stable_and_tamper_detected(self):
        _bars, manifest = self._built()
        clean = mdd.validate_dataset_manifest_record(manifest)
        self.assertEqual(clean["dataset_id"], manifest["dataset_id"])
        tampered = dict(manifest)
        tampered["bar_count"] = manifest["bar_count"] + 1
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_dataset_manifest_record(tampered)

    def test_imported_at_utc_excluded_from_identity(self):
        bars, manifest = self._built()
        other = mdd.build_dataset_manifest_record(
            bars, "SYNTHETIC_FIXTURE", "ident-test",
            manifest["expected_interval_seconds"], manifest["gap_count"], manifest["largest_gap_intervals"],
            "2099-01-01T00:00:00.000000Z",
        )
        self.assertEqual(manifest["dataset_id"], other["dataset_id"])
        self.assertEqual(manifest["canonical_dataset_hash"], other["canonical_dataset_hash"])
        self.assertNotEqual(manifest["imported_at_utc"], other["imported_at_utc"])

    def test_no_cycle_in_identity_sequence(self):
        """A direct acceptance test that no identity formula takes as input
        a hash computed from data including that identity's own value or a
        value computed after it (Section 11.6)."""
        bars, manifest = self._built()
        session = mdd.build_replay_session_record(
            manifest["dataset_id"], manifest["canonical_dataset_hash"], 0, 1, 1, "2026-01-01T01:00:00.000000Z",
        )
        step = mdd.build_replay_step_record(
            session["replay_session_id"], session["canonical_replay_session_hash"], 1, 0, 0,
            [mdd.bar_ref(bars[0])], "RUNNING", "2026-01-01T01:00:01.000000Z",
        )
        snapshot = mdd.build_replay_snapshot_record(
            session["replay_session_id"], session["canonical_replay_session_hash"],
            step["replay_step_id"], step["canonical_replay_step_hash"],
            manifest["dataset_id"], manifest["canonical_dataset_hash"],
            0, bars[0]["bar_id"], bars[0]["canonical_bar_hash"], 0, 0, [mdd.bar_ref(bars[0])],
            "2026-01-01T01:00:01.000000Z",
        )
        # Each identity's material set is exactly the documented upstream
        # fields -- none of bar_id/dataset_id/replay_session_id/
        # replay_step_id/replay_snapshot_id is itself a member of an
        # earlier identity's material.
        self.assertNotIn(bars[0]["bar_id"], mdd.BAR_ID_FIELDS)
        self.assertNotIn("dataset_id", mdd.BAR_ID_FIELDS)
        self.assertIn("dataset_id", mdd.REPLAY_SESSION_ID_FIELDS)
        self.assertIn("replay_session_id", mdd.REPLAY_STEP_ID_FIELDS)
        self.assertIn("replay_step_id", mdd.REPLAY_SNAPSHOT_ID_FIELDS)
        self.assertTrue(snapshot["replay_snapshot_id"].startswith("rsn_"))


class StorageEnvelopeTests(unittest.TestCase):
    def test_envelope_round_trips(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        bars = [mdd.build_bar_record(row, "SYNTHETIC_FIXTURE") for row in rows]
        manifest = mdd.build_dataset_manifest_record(bars, "SYNTHETIC_FIXTURE", "env-test", interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z")
        envelope = mdd.build_storage_envelope(manifest, bars)
        clean = mdd.validate_storage_envelope(envelope)
        self.assertEqual(clean["dataset_id"], manifest["dataset_id"])
        self.assertEqual(len(clean["ordered_bars"]), 2)

    def test_envelope_rejects_bar_count_mismatch(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        bars = [mdd.build_bar_record(row, "SYNTHETIC_FIXTURE") for row in rows]
        manifest = mdd.build_dataset_manifest_record(bars, "SYNTHETIC_FIXTURE", "env-test", interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z")
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.build_storage_envelope(manifest, bars[:1])

    def test_envelope_rejects_unknown_field(self):
        raw = (HEADER + _row() + "\n" + _row(ts="2026-01-01T00:05:00.000000Z") + "\n").encode("utf-8")
        rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
        bars = [mdd.build_bar_record(row, "SYNTHETIC_FIXTURE") for row in rows]
        manifest = mdd.build_dataset_manifest_record(bars, "SYNTHETIC_FIXTURE", "env-test", interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z")
        envelope = mdd.build_storage_envelope(manifest, bars)
        envelope["extra_field"] = True
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_storage_envelope(envelope)


class ReplayBoundsTests(unittest.TestCase):
    def test_valid_bounds_accepted(self):
        mdd.validate_replay_bounds(10, 0, 9, 1)

    def test_start_exceeds_end_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            mdd.validate_replay_bounds(10, 5, 4, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_BOUNDS_INVALID")

    def test_end_exceeds_bar_count_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_replay_bounds(10, 0, 10, 1)

    def test_step_size_out_of_range_rejected(self):
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_replay_bounds(10, 0, 9, 1001)
        with self.assertRaises(mdd.MarketDataValidationError):
            mdd.validate_replay_bounds(10, 0, 9, 0)

    def test_projected_step_count_exact(self):
        self.assertEqual(mdd.projected_step_count(0, 9, 1), 10)
        self.assertEqual(mdd.projected_step_count(0, 9, 3), 4)
        self.assertEqual(mdd.projected_step_count(0, 0, 1), 1)


if __name__ == "__main__":
    unittest.main()
