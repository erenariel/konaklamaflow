"""Synthetic hard-constraint and fail-closed regression checks for Issue #62."""
from copy import deepcopy
import unittest

from konaklamaflow.room_allocation_solver import (
    SCHEMA, AllocationInputError, propose_group,
)


def room(ident, bed="double", *, category="standard", persons=2,
         readiness="inspected", occupancy="verified_vacant", maintenance=None):
    return {"id": ident, "category": category, "capacity": persons,
            "bed": bed, "readiness": readiness, "occupancy": occupancy,
            "maintenance": [] if maintenance is None else maintenance}


def stay(ident, bed="none", *, arrival="2026-11-16", departure="2026-11-18",
         category="standard", persons=2, status="confirmed"):
    return {"id": ident, "arrival": arrival, "departure": departure,
            "category": category, "persons": persons, "bed_request": bed, "status": status}


def fixture():
    return {"schema_version": SCHEMA, "source_kind": "fictional",
            "rooms": [room("T101", "twin"), room("D102")],
            "stays": [stay("A_FLEX"), stay("B_TWIN", "twin")], "holds": []}


def mapped(report):
    return {r["stay_id"]: r["room_id"] for r in report["proposals"]}


class RoomAllocationSolverTests(unittest.TestCase):
    def test_twin_scarcity_counterexample_global_not_greedy(self):
        src = fixture()
        before = deepcopy(src)
        out = propose_group(src)
        self.assertEqual(out["status"], "proposed")
        self.assertEqual(mapped(out), {"A_FLEX": "D102", "B_TWIN": "T101"})
        self.assertEqual(src, before)
        self.assertTrue(out["human_approval_required"])
        self.assertEqual(out["mode"], "DRY_RUN_ONLY")
        self.assertTrue(all(not flag for flag in out["side_effects"].values()))
        self.assertTrue(all(p["human_approval_required"] for p in out["proposals"]))

    def test_deterministic_under_source_reordering(self):
        src = fixture()
        canonical = propose_group(src)
        src["stays"].reverse()
        src["rooms"].reverse()
        self.assertEqual(propose_group(src), canonical)

    def test_nonoverlap_allows_reuse_of_one_room(self):
        src = fixture()
        src["rooms"] = [room("ONLY1")]
        src["stays"] = [stay("A1", departure="2026-11-18"),
                        stay("B1", arrival="2026-11-18", departure="2026-11-21")]
        self.assertEqual(mapped(propose_group(src)), {"A1": "ONLY1", "B1": "ONLY1"})

    def test_overlapping_stays_never_share_a_room(self):
        src = fixture()
        src["rooms"] = [room("ONLY1")]
        src["stays"] = [stay("A1"), stay("B1")]
        out = propose_group(src)
        self.assertEqual(out["status"], "no_solution")
        self.assertFalse(out["proposals"])
        self.assertIn("NO_FEASIBLE_PROPOSAL", out["reason_codes"])

    def test_explicit_hard_bed_requests_are_not_soft_preferences(self):
        for bed in ("twin", "double", "single"):
            with self.subTest(bed=bed):
                src = fixture()
                src["stays"] = [stay("STRICT", bed)]
                result = propose_group(src)
                if bed == "single":
                    self.assertEqual(result["status"], "no_solution")
                else:
                    self.assertEqual(result["proposals"][0]["room_id"],
                                     "T101" if bed == "twin" else "D102")

    def test_flex_room_does_not_promise_twin_configuration(self):
        src = fixture()
        src["rooms"] = [room("FLEX1", "flex")]
        src["stays"] = [stay("STRICT", "twin")]
        self.assertEqual(propose_group(src)["status"], "no_solution")

    def test_capacity_and_category_must_match_exactly(self):
        src = fixture()
        src["stays"] = [stay("FAMILY", persons=4)]
        self.assertEqual(propose_group(src)["status"], "no_solution")
        src["stays"] = [stay("SUPER", category="superior")]
        self.assertEqual(propose_group(src)["status"], "no_solution")

    def test_maintenance_overlapping_stay_blocks_room(self):
        src = fixture()
        src["rooms"][0]["maintenance"] = [{"start": "2026-11-17", "end": "2026-11-20"}]
        src["stays"] = [stay("STRICT", "twin")]
        self.assertEqual(propose_group(src)["status"], "no_solution")

    def test_maintenance_checkout_boundary_allows_room(self):
        src = fixture()
        src["rooms"][0]["maintenance"] = [{"start": "2026-11-18", "end": "2026-11-20"}]
        src["stays"] = [stay("STRICT", "twin")]
        self.assertEqual(mapped(propose_group(src)), {"STRICT": "T101"})

    def test_active_held_room_blocks_overlap(self):
        src = fixture()
        src["stays"] = [stay("STRICT", "twin")]
        src["holds"] = [{"id": "HOLD1", "room_id": "T101",
                         "arrival": "2026-11-16", "departure": "2026-11-20",
                         "status": "active", "release_confirmed": False}]
        self.assertEqual(propose_group(src)["status"], "no_solution")

    def test_cancelled_hold_not_released_without_explicit_confirmation(self):
        src = fixture()
        src["stays"] = [stay("STRICT", "twin")]
        src["holds"] = [{"id": "HOLD1", "room_id": "T101",
                         "arrival": "2026-11-16", "departure": "2026-11-20",
                         "status": "cancelled", "release_confirmed": False}]
        result = propose_group(src)
        self.assertEqual(result["status"], "manual_review_required")
        self.assertEqual(result["reason_codes"], ["HELD_ROOM_RELEASE_NOT_VERIFIED"])
        src["holds"][0]["release_confirmed"] = True
        self.assertEqual(mapped(propose_group(src)), {"STRICT": "T101"})

    def test_no_show_hold_is_not_implicitly_freed(self):
        src = fixture()
        src["stays"] = [stay("STRICT", "twin")]
        src["holds"] = [{"id": "HOLD1", "room_id": "T101",
                         "arrival": "2026-11-16", "departure": "2026-11-20",
                         "status": "no_show", "release_confirmed": False}]
        self.assertEqual(propose_group(src)["status"], "manual_review_required")

    def test_cancelled_stay_is_not_allocated(self):
        src = fixture()
        src["stays"][0]["status"] = "cancelled"
        result = propose_group(src)
        self.assertEqual(result["status"], "manual_review_required")
        self.assertEqual(result["proposals"], [])

    def test_unknown_occupancy_is_never_declared_available(self):
        src = fixture()
        src["stays"] = [stay("STRICT", "twin")]
        src["rooms"][0]["occupancy"] = "unknown"
        result = propose_group(src)
        self.assertEqual(result["status"], "manual_review_required")
        self.assertEqual(result["reason_codes"], ["ROOM_READINESS_UNVERIFIED"])
        self.assertFalse(result["proposals"])

    def test_dirty_out_of_order_and_occupied_are_not_ready(self):
        for field, value in (("readiness", "dirty"), ("readiness", "out_of_order"),
                             ("readiness", "out_of_service"), ("occupancy", "occupied")):
            with self.subTest(field=field, value=value):
                src = fixture()
                src["stays"] = [stay("STRICT", "twin")]
                src["rooms"][0][field] = value
                self.assertEqual(propose_group(src)["status"], "no_solution")

    def test_search_limit_returns_no_partial_plan(self):
        src = fixture()
        out = propose_group(src, max_states=1)
        self.assertEqual(out["status"], "manual_review_required")
        self.assertEqual(out["reason_codes"], ["SEARCH_LIMIT_REACHED"])
        self.assertEqual(out["proposals"], [])

    def test_scope_rejected_before_deep_search(self):
        src = fixture()
        src["stays"] *= 3
        self.assertEqual(propose_group(src)["reason_codes"], ["SEARCH_SCOPE_EXCEEDED"])
        src = fixture()
        src["rooms"] *= 10
        self.assertEqual(propose_group(src)["status"], "manual_review_required")

    def test_strict_validation_rejects_unrecognized_personal_fields(self):
        for collection, field in (("rooms", "guest_email"), ("stays", "passport"),
                                  ("holds", "guest_name")):
            src = fixture()
            if collection == "holds":
                src["holds"] = [{"id": "H1", "room_id": "T101",
                                 "arrival": "2026-11-16", "departure": "2026-11-17",
                                 "status": "active", "release_confirmed": False}]
            src[collection][0][field] = "PRIVATE"
            with self.subTest(collection=collection), self.assertRaises(AllocationInputError):
                propose_group(src)

    def test_invalid_ids_dates_and_bools_rejected(self):
        variations = [
            ("rooms", 0, "id", "person@example.org"),
            ("stays", 0, "arrival", "2026-02-30"),
            ("stays", 0, "departure", "2026-11-16"),
            ("rooms", 0, "capacity", True),
            ("rooms", 0, "bed", "triple"),
        ]
        for key, idx, field, value in variations:
            src = fixture()
            src[key][idx][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AllocationInputError):
                propose_group(src)

    def test_active_hold_cannot_be_claimed_released(self):
        src = fixture()
        src["holds"] = [{"id": "H1", "room_id": "T101", "arrival": "2026-11-16",
                         "departure": "2026-11-18", "status": "active",
                         "release_confirmed": True}]
        with self.assertRaises(AllocationInputError):
            propose_group(src)

    def test_allows_only_fictional_schema_and_valid_budgets(self):
        src = fixture()
        src["source_kind"] = "live"
        with self.assertRaises(AllocationInputError):
            propose_group(src)
        src = fixture()
        src["rooms"][0]["private_address"] = "nope"
        with self.assertRaises(AllocationInputError):
            propose_group(src)
        for limit in (0, -1, 20001, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(AllocationInputError):
                propose_group(fixture(), max_states=limit)

    def test_no_requests_returns_review_not_proposed(self):
        src = fixture()
        src["stays"] = []
        self.assertEqual(propose_group(src)["status"], "manual_review_required")


if __name__ == "__main__":
    unittest.main()
