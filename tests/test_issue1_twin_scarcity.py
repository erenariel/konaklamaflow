"""Regression for Issue #1 — scarce twin room planning is advisory only."""
from copy import deepcopy
import unittest

from konaklamaflow.core import review


def fixture():
    return {
        "property_id": "FICTIONAL_INN",
        "rooms": [
            {"id": "101", "category": "standard", "beds": "twin"},
            {"id": "102", "category": "standard", "beds": "double"},
        ],
        "reservations": [
            {"ref": "A_STD", "source": "SYNTHETIC", "status": "confirmed",
             "checkin": "2026-11-13", "checkout": "2026-11-15",
             "category": "standard"},
            {"ref": "B_TWIN", "source": "SYNTHETIC", "status": "confirmed",
             "checkin": "2026-11-13", "checkout": "2026-11-15",
             "category": "standard", "twin_requested": True},
        ],
    }


class TwinScarcityRegressionTests(unittest.TestCase):
    def test_issue_1_original_repro_preserves_twin_room(self):
        s = fixture()
        before = deepcopy(s)
        result = review(s, "2026-11-12")
        plan = {p["reservation_ref"]: p["room_id"] for p in result["room_proposals"]}
        self.assertEqual(plan, {"B_TWIN": "101", "A_STD": "102"})
        self.assertEqual(result["mode"], "DRY_RUN_ONLY")
        self.assertEqual(s, before)
        self.assertTrue(all(p["kind"] == "MANUAL_APPROVAL_REQUIRED"
                            for p in result["room_proposals"]))

    def test_input_order_is_deterministic(self):
        s = fixture()
        expected = {p["reservation_ref"]: p["room_id"] for p in
                    review(s, "2026-11-12")["room_proposals"]}
        s["rooms"].reverse()
        s["reservations"].reverse()
        actual = {p["reservation_ref"]: p["room_id"] for p in
                  review(s, "2026-11-12")["room_proposals"]}
        self.assertEqual(expected, actual)

    def test_twin_request_never_given_double_room_when_twin_held(self):
        s = fixture()
        s["reservations"].append({
            "ref": "HOLD", "source": "SYNTHETIC", "status": "pending",
            "checkin": "2026-11-12", "checkout": "2026-11-15",
            "category": "standard", "room_id": "101",
        })
        report = review(s, "2026-11-12")
        plan = {p["reservation_ref"]: p["room_id"] for p in report["room_proposals"]}
        self.assertNotIn("B_TWIN", plan)
        self.assertEqual(plan.get("A_STD"), "102")
        self.assertTrue(any(i["code"] == "NO_SAFE_ROOM_PROPOSAL" and
                            i["reservation_ref"] == "B_TWIN"
                            for i in report["issues"]))

    def test_inactive_or_maintenance_twin_room_is_not_promised(self):
        for room_update in ({"active": False}, {
            "maintenance": [{"start": "2026-11-14", "end": "2026-11-16"}]
        }):
            s = fixture()
            s["rooms"][0].update(room_update)
            plan = {p["reservation_ref"]: p["room_id"] for p in
                    review(s, "2026-11-12")["room_proposals"]}
            with self.subTest(room_update=room_update):
                self.assertNotIn("B_TWIN", plan)
                self.assertEqual(plan["A_STD"], "102")

    def test_future_nonoverlapping_stay_may_reuse_room(self):
        s = fixture()
        s["reservations"][0]["checkin"] = "2026-11-16"
        s["reservations"][0]["checkout"] = "2026-11-18"
        report = review(s, "2026-11-12")
        assignments = {p["reservation_ref"]: p["room_id"] for p in
                       report["room_proposals"]}
        self.assertEqual(assignments["B_TWIN"], "101")
        self.assertEqual(assignments["A_STD"], "102")


if __name__ == "__main__":
    unittest.main()
