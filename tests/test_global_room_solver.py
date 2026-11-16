"""Synthetic 18/60/200-room safety and bounded search regressions."""
from copy import deepcopy
from random import Random
import unittest

from konaklamaflow.global_room_solver import (
    MAX_GLOBAL_ROOMS, MAX_GLOBAL_STAYS, propose_global_room_plan,
)
from konaklamaflow.room_allocation_solver import (
    AllocationInputError, MAX_ROOMS, MAX_STAYS, SCHEMA, propose_group,
)


def room(index, bed="double", *, readiness="inspected",
         occupancy="verified_vacant", maintenance=None):
    return {"id": f"R{index:03d}", "category": "standard",
            "capacity": 2, "bed": bed, "readiness": readiness,
            "occupancy": occupancy,
            "maintenance": [] if maintenance is None else maintenance}


def stay(index, bed="none", *, arrival="2026-11-16",
         departure="2026-11-18", status="confirmed"):
    return {"id": f"S{index:03d}", "arrival": arrival, "departure": departure,
            "category": "standard", "persons": 2, "bed_request": bed,
            "status": status}


def fixture(count):
    # Include both scarce twins and flexible stays. All stays overlap.
    twins = max(1, count // 5)
    return {
        "schema_version": SCHEMA, "source_kind": "fictional",
        "rooms": [room(i, "twin" if i < twins else "double")
                  for i in range(count)],
        "stays": [stay(i, "twin" if i < twins else "none")
                  for i in range(count)],
        "holds": [],
    }


def mapping(report):
    return {row["stay_id"]: row["room_id"] for row in report["proposals"]}


class BoundedGlobalRoomResearchTests(unittest.TestCase):
    def test_18_60_200_room_synthetic_scales_are_complete_and_read_only(self):
        for size in (18, 60, 200):
            with self.subTest(rooms=size):
                source = fixture(size)
                original = deepcopy(source)
                result = propose_global_room_plan(source, max_seconds=30)
                self.assertEqual(result["status"], "proposed")
                self.assertEqual(len(result["proposals"]), size)
                self.assertEqual(len(set(mapping(result).values())), size)
                self.assertEqual(result["search"]["candidate_rooms"], size)
                self.assertEqual(result["search"]["requested_stays"], size)
                self.assertEqual(result["mode"], "DRY_RUN_ONLY")
                self.assertTrue(result["human_approval_required"])
                self.assertFalse(any(result["side_effects"].values()))
                self.assertTrue(all(p["human_approval_required"]
                                    for p in result["proposals"]))
                self.assertEqual(source, original)

    def test_twin_is_a_hard_constraint_and_flexible_stay_preserves_it(self):
        source = fixture(2)
        source["rooms"] = [room(0, "twin"), room(1, "double")]
        source["stays"] = [stay(0), stay(1, "twin")]
        result = propose_global_room_plan(source)
        self.assertEqual(mapping(result), {"S000": "R001", "S001": "R000"})

    def test_same_day_checkout_allows_reuse_but_overlap_never_does(self):
        source = fixture(1)
        source["stays"] = [stay(0, departure="2026-11-18"),
                           stay(1, arrival="2026-11-18",
                                departure="2026-11-20")]
        self.assertEqual(mapping(propose_global_room_plan(source)),
                         {"S000": "R000", "S001": "R000"})
        source["stays"][1]["arrival"] = "2026-11-17"
        result = propose_global_room_plan(source)
        self.assertEqual(result["status"], "no_solution")
        self.assertEqual(result["proposals"], [])

    def test_maintenance_unknown_occupancy_and_unreleased_holds_fail_closed(self):
        source = fixture(1)
        source["rooms"][0]["maintenance"] = [
            {"start": "2026-11-16", "end": "2026-11-17"}
        ]
        self.assertEqual(propose_global_room_plan(source)["status"], "no_solution")
        source["rooms"][0]["maintenance"] = []
        source["rooms"][0]["occupancy"] = "unknown"
        result = propose_global_room_plan(source)
        self.assertEqual(result["status"], "manual_review_required")
        self.assertEqual(result["proposals"], [])
        source["rooms"][0]["occupancy"] = "verified_vacant"
        source["holds"] = [
            {"id": "H000", "room_id": "R000",
             "arrival": "2026-11-16", "departure": "2026-11-18",
             "status": "cancelled", "release_confirmed": False}
        ]
        result = propose_global_room_plan(source)
        self.assertEqual(result["status"], "manual_review_required")
        self.assertEqual(result["reason_codes"], ["HELD_ROOM_RELEASE_NOT_VERIFIED"])
        source["holds"][0]["release_confirmed"] = True
        self.assertEqual(propose_global_room_plan(source)["status"], "proposed")

    def test_search_limit_never_returns_partial_assignments(self):
        source = fixture(3)
        result = propose_global_room_plan(source, max_states=1)
        self.assertEqual(result["status"], "manual_review_required")
        self.assertEqual(result["reason_codes"], ["SEARCH_LIMIT_REACHED"])
        self.assertEqual(result["proposals"], [])

    def test_invalid_stay_status_or_big_scope_never_proposes(self):
        source = fixture(3)
        source["stays"][0]["status"] = "pending"
        self.assertEqual(propose_global_room_plan(source)["status"],
                         "manual_review_required")
        source = fixture(MAX_GLOBAL_ROOMS + 1)
        self.assertEqual(propose_global_room_plan(source)["reason_codes"],
                         ["SEARCH_SCOPE_EXCEEDED"])
        self.assertEqual(MAX_GLOBAL_ROOMS, 200)
        self.assertEqual(MAX_GLOBAL_STAYS, 200)

    def test_source_reordering_is_deterministic(self):
        source = fixture(18)
        baseline = propose_global_room_plan(source)
        Random(12).shuffle(source["rooms"])
        Random(34).shuffle(source["stays"])
        self.assertEqual(propose_global_room_plan(source), baseline)

    def test_strict_pii_rejection_and_budget_contract(self):
        source = fixture(2)
        source["stays"][0]["passport"] = "PRIVATE"
        with self.assertRaises(AllocationInputError):
            propose_global_room_plan(source)
        for bad in (0, -1, 30.01, True, "1", float("nan"), float("inf")):
            with self.subTest(value=str(bad)), self.assertRaises(AllocationInputError):
                propose_global_room_plan(fixture(2), max_seconds=bad)

    def test_current_small_solver_api_and_limits_are_untouched(self):
        source = fixture(5)
        self.assertEqual(MAX_STAYS, 4)
        self.assertEqual(MAX_ROOMS, 18)
        self.assertEqual(propose_group(source)["reason_codes"],
                         ["SEARCH_SCOPE_EXCEEDED"])
        self.assertEqual(propose_global_room_plan(source)["status"], "proposed")


if __name__ == "__main__":
    unittest.main()
