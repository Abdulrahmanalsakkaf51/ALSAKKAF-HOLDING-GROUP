"""Tests for TRL-R2-011 Market Data Fabric and Replay V0 -- dataset storage
module (``market_data_replay_storage.py``). Covers contract Section 25
category E (storage envelope: schema, correspondence, order, size bound,
atomic write, reload validation, immutable reuse, tampering detection).
"""

import tempfile
import unittest
from pathlib import Path

import mdr_test_support as support
from trading_lab_app import market_data_replay_data as mdd
from trading_lab_app import market_data_replay_storage as mds


def _envelope(source_reference="storage-test"):
    raw = support.build_csv_bytes(bar_count=3)
    rows, interval, gap_count, largest_gap = mdd.parse_csv_rows(raw)
    bars = [mdd.build_bar_record(row, "SYNTHETIC_FIXTURE") for row in rows]
    manifest = mdd.build_dataset_manifest_record(
        bars, "SYNTHETIC_FIXTURE", source_reference, interval, gap_count, largest_gap, "2026-01-01T01:00:00.000000Z",
    )
    return mdd.build_storage_envelope(manifest, bars)


class LocalDatasetStorageTests(unittest.TestCase):
    def test_missing_dataset_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            self.assertIsNone(store.load("mds_" + "0" * 32))

    def test_save_then_load_round_trips(self):
        envelope = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            saved = store.save_new(envelope["dataset_id"], envelope)
            loaded = store.load(envelope["dataset_id"])
            self.assertEqual(saved, loaded)
            self.assertEqual(loaded["dataset_id"], envelope["dataset_id"])

    def test_filename_derived_only_from_dataset_id(self):
        envelope = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            store.save_new(envelope["dataset_id"], envelope)
            files = list(Path(tmp).glob("*.json"))
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, envelope["dataset_id"] + ".json")

    def test_immutable_after_acceptance_refuses_overwrite(self):
        envelope = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            store.save_new(envelope["dataset_id"], envelope)
            with self.assertRaises(mds.DatasetStorageError):
                store.save_new(envelope["dataset_id"], envelope)

    def test_atomic_write_leaves_no_temp_file(self):
        envelope = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            store.save_new(envelope["dataset_id"], envelope)
            leftovers = [p for p in Path(tmp).iterdir() if p.suffix == ".tmp"]
            self.assertEqual(leftovers, [])

    def test_reload_revalidates_and_detects_tampering(self):
        envelope = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            store.save_new(envelope["dataset_id"], envelope)
            path = Path(tmp) / (envelope["dataset_id"] + ".json")
            raw = path.read_text(encoding="utf-8")
            tampered = raw.replace('"bar_count":3', '"bar_count":4')
            path.write_text(tampered, encoding="utf-8")
            with self.assertRaises(mdd.MarketDataValidationError) as ctx:
                store.load(envelope["dataset_id"])
            self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_STORAGE_INTEGRITY_FAILURE")

    def test_duplicate_json_key_rejected(self):
        envelope = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            store.save_new(envelope["dataset_id"], envelope)
            path = Path(tmp) / (envelope["dataset_id"] + ".json")
            raw = path.read_bytes()
            duplicated = raw[:-1] + b',"dataset_id":"' + envelope["dataset_id"].encode() + b'"}'
            path.write_bytes(duplicated)
            with self.assertRaises(mdd.MarketDataValidationError) as ctx:
                store.load(envelope["dataset_id"])
            self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_STORAGE_INTEGRITY_FAILURE")

    def test_oversized_envelope_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            path = Path(tmp) / ("mds_" + "1" * 32 + ".json")
            path.write_bytes(b"{}" + b" " * (mdd.MAX_STORAGE_ENVELOPE_BYTES + 1))
            with self.assertRaises(mdd.MarketDataValidationError) as ctx:
                store.load("mds_" + "1" * 32)
            self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE")

    def test_unsafe_dataset_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = mds.LocalDatasetStorage(root=tmp)
            with self.assertRaises(mds.DatasetStorageError):
                store.load("../etc/passwd")

    def test_no_absolute_path_in_envelope(self):
        envelope = _envelope()
        encoded = mds.encode_envelope(envelope).decode("utf-8")
        self.assertNotIn(":\\", encoded)
        self.assertNotIn("/home/", encoded)

    def test_no_source_csv_bytes_stored(self):
        envelope = _envelope()
        for bar in envelope["ordered_bars"]:
            self.assertNotIn("source_csv", bar)
        self.assertEqual(set(envelope), set(mdd.STORAGE_ENVELOPE_FIELDS))


class InMemoryDatasetStorageTests(unittest.TestCase):
    def test_round_trip(self):
        envelope = _envelope()
        store = mds.InMemoryDatasetStorage()
        store.save_new(envelope["dataset_id"], envelope)
        self.assertEqual(store.load(envelope["dataset_id"])["dataset_id"], envelope["dataset_id"])

    def test_refuses_duplicate_save(self):
        envelope = _envelope()
        store = mds.InMemoryDatasetStorage()
        store.save_new(envelope["dataset_id"], envelope)
        with self.assertRaises(mds.DatasetStorageError):
            store.save_new(envelope["dataset_id"], envelope)

    def test_fail_writes_flag(self):
        envelope = _envelope()
        store = mds.InMemoryDatasetStorage()
        store.fail_writes = True
        with self.assertRaises(mds.DatasetStorageError):
            store.save_new(envelope["dataset_id"], envelope)


if __name__ == "__main__":
    unittest.main()
