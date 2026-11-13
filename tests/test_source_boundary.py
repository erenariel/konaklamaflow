"""Read-only mock source envelope fails closed on stale, scope and PII errors."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from konaklamaflow.source_boundary import (
    SourceBoundaryError, verify_mock_source_envelope
)

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = "2026-11-13T00:00:00+00:00"
CHECK = "2026-11-13T00:03:00Z"


class SourceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / "examples/fictional-hotel.json").read_text())
        self.envelope = {
            "source": "SYNTHETIC_READ_ONLY_MOCK",
            "property_id": self.snapshot["property_id"],
            "captured_at_utc": CAPTURE,
            "revision": "sample_revision_007",
            "snapshot": self.snapshot,
        }

    def verify(self, **kwargs):
        args = dict(expected_property_id=self.snapshot["property_id"],
                    checked_at_utc=CHECK)
        args.update(kwargs)
        return verify_mock_source_envelope(self.envelope, **args)

    def test_valid_synthetic_snapshot_is_still_not_authorized_or_live(self):
        before = deepcopy(self.envelope)
        result = self.verify()
        self.assertEqual(self.envelope, before)
        self.assertEqual(result["report"]["mode"], "DRY_RUN_ONLY")
        self.assertEqual(result["source_validity"],
                         "FRESH_SYNTHETIC_ENVELOPE_NOT_LIVE_VERIFICATION")
        self.assertFalse(result["policy"]["live_pms_connected"])
        self.assertFalse(result["policy"]["pms_writes"])
        self.assertFalse(result["policy"]["payments"])
        self.assertFalse(result["policy"]["kbs"])
        self.assertTrue(result["policy"]["human_approval_required"])

    def test_stale_and_future_snapshots_fail_closed(self):
        for checked in ("2026-11-13T00:06:00Z", "2026-11-12T23:59:59Z"):
            with self.subTest(checked=checked), self.assertRaises(SourceBoundaryError):
                self.verify(checked_at_utc=checked)

    def test_wrong_property_scope_and_source_fail(self):
        for mutation in ({"property_id": "OTHER_HOTEL"},
                         {"source": "UNAUTHORIZED_VENDOR"},
                         {"revision": "../guest.csv"}):
            original = deepcopy(self.envelope)
            self.envelope.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(SourceBoundaryError):
                self.verify()
            self.envelope = original
        self.envelope["snapshot"]["property_id"] = "OTHER_PROPERTY"
        with self.assertRaises(SourceBoundaryError):
            self.verify()

    def test_raw_guest_fields_rejected_without_echo(self):
        self.envelope["snapshot"]["reservations"][0]["guest_email"] = "PRIVATE_TEST"
        with self.assertRaises(SourceBoundaryError) as caught:
            self.verify()
        self.assertNotIn("PRIVATE_TEST", str(caught.exception))

    def test_naive_and_non_utc_timestamps_rejected(self):
        for source_time in ("2026-11-13T00:00:00", "2026-11-13T03:00:00+03:00",
                            "2026-11-13T00:00:00+01:00"):
            self.envelope["captured_at_utc"] = source_time
            with self.subTest(source_time=source_time), self.assertRaises(SourceBoundaryError):
                self.verify()

    def test_ttl_limits_and_malformed_metadata_rejected(self):
        for ttl in (0, -1, 901, True, 1.5):
            with self.subTest(ttl=ttl), self.assertRaises(SourceBoundaryError):
                self.verify(max_age_seconds=ttl)
        for key in ("source", "revision", "snapshot", "captured_at_utc"):
            env = deepcopy(self.envelope)
            env.pop(key)
            with self.subTest(key=key), self.assertRaises(SourceBoundaryError):
                verify_mock_source_envelope(env, expected_property_id=self.snapshot["property_id"],
                                            checked_at_utc=CHECK)

    def test_explicit_ttl_can_be_more_conservative(self):
        with self.assertRaises(SourceBoundaryError):
            self.verify(max_age_seconds=60)
        result = self.verify(max_age_seconds=180)
        self.assertEqual(result["revision"], "sample_revision_007")


if __name__ == "__main__":
    unittest.main()
