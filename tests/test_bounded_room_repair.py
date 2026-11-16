"""Regression tests for bounded recovery of feasible fictional room proposals."""
from copy import deepcopy
import unittest

from konaklamaflow.core import review


def recoverable_snapshot():
    # Greedy chooses D102 for A, then T101 for C, stranding B.
    # A(T101) + C(D102) + B(T101) is feasible because A checks out on B's arrival.
    return {
        "property_id": "FICTIONAL_INN",
        "rooms": [
            {"id": "101", "category": "standard", "beds": "twin"},
            {"id": "102", "category": "standard", "beds": "double"},
        ],
        "reservations": [
            {"ref": "A_EARLY", "source": "SYNTHETIC", "status": "confirmed",
             "checkin": "2026-11-13", "checkout": "2026-11-16",
             "category": "standard"},
            {"ref": "B_TWIN", "source": "SYNTHETIC", "status": "confirmed",
             "checkin": "2026-11-16", "checkout": "2026-11-19",
             "category": "standard", "twin_requested": True},
            {"ref": "C_OVERLAP", "source": "SYNTHETIC", "status": "confirmed",
             "checkin": "2026-11-14", "checkout": "2026-11-17",
             "category": "standard"},
        ],
    }


def proposals(snapshot):
    return review(snapshot, "2026-11-12")


class BoundedRoomRepairTests(unittest.TestCase):
    def test_recovers_feasible_temporal_plan_without_room_collision(self):
        data = recoverable_snapshot()
        before = deepcopy(data)
        report = proposals(data)
        by_ref = {p["reservation_ref"]: p["room_id"] for p in report["room_proposals"]}
        self.assertEqual(by_ref, {"A_EARLY": "101", "C_OVERLAP": "102",
                                  "B_TWIN": "101"})
        self.assertEqual(report["summary"]["room_proposals"], 3)
        self.assertFalse(any(i["code"] == "NO_SAFE_ROOM_PROPOSAL"
                             for i in report["issues"]))
        self.assertTrue(all(p["kind"] == "MANUAL_APPROVAL_REQUIRED"
                            for p in report["room_proposals"]))
        self.assertEqual(report["mode"], "DRY_RUN_ONLY")
        self.assertEqual(data, before)

    def test_repair_is_stable_under_input_reordering(self):
        data = recoverable_snapshot()
        expected = proposals(data)
        data["rooms"].reverse()
        data["reservations"].reverse()
        self.assertEqual(proposals(data), expected)

    def test_unavailable_twin_does_not_get_invented(self):
        data = recoverable_snapshot()
        data["rooms"][0]["maintenance"] = [
            {"start": "2026-11-16", "end": "2026-11-18"}
        ]
        report = proposals(data)
        by_ref = {p["reservation_ref"]: p["room_id"] for p in report["room_proposals"]}
        self.assertNotIn("B_TWIN", by_ref)
        self.assertTrue(any(i["code"] == "NO_SAFE_ROOM_PROPOSAL"
                            and i["reservation_ref"] == "B_TWIN"
                            for i in report["issues"]))

    def test_existing_hold_is_never_reallocated(self):
        data = recoverable_snapshot()
        data["reservations"].append({
            "ref": "REAL_HOLD", "source": "SYNTHETIC", "status": "pending",
            "checkin": "2026-11-15", "checkout": "2026-11-18",
            "category": "standard", "room_id": "101",
        })
        report = proposals(data)
        plan = {p["reservation_ref"]: p["room_id"] for p in report["room_proposals"]}
        self.assertNotIn("B_TWIN", plan)
        self.assertTrue(any(i["reservation_ref"] == "B_TWIN"
                            and i["code"] == "NO_SAFE_ROOM_PROPOSAL"
                            for i in report["issues"]))

    def test_large_snapshot_remains_bounded_and_advisory(self):
        data = recoverable_snapshot()
        data["reservations"] = [
            {"ref": f"R{i}", "source": "SYNTHETIC", "status": "confirmed",
             "checkin": "2026-11-13", "checkout": "2026-11-16",
             "category": "standard"} for i in range(9)
        ]
        report = proposals(data)
        self.assertEqual(report["summary"]["room_proposals"], 2)
        self.assertEqual(sum(i["code"] == "NO_SAFE_ROOM_PROPOSAL"
                             for i in report["issues"]), 7)
        self.assertTrue(all(p["kind"] == "MANUAL_APPROVAL_REQUIRED"
                            for p in report["room_proposals"]))


if __name__ == "__main__":
    unittest.main()
