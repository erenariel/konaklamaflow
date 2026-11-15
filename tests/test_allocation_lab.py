"""Bounded, source-derived fictional allocation laboratory tests."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.room_allocation_solver import propose_group
from scripts.render_allocation_lab import (
    SCENARIOS, authoritative_scenarios, allocation_lab_html, main,
)
from scripts.stage_demo_site import stage_site
from scripts.verify_release_readiness import verify_staged_site, ReleaseReadinessError


class AllocationLabTests(unittest.TestCase):
    def test_six_auditable_cases_source_derived(self):
        cases = authoritative_scenarios()
        self.assertEqual(len(cases), 6)
        self.assertEqual(len({case["id"] for case in cases}), 6)
        for case in cases:
            with self.subTest(case=case["id"]):
                source = deepcopy(case["source"])
                self.assertEqual(case["report"], propose_group(source))
                self.assertEqual(case["source"], source)
                self.assertEqual(case["report"]["mode"], "DRY_RUN_ONLY")
                self.assertTrue(case["report"]["human_approval_required"])
                self.assertFalse(any(case["report"]["side_effects"].values()))
                self.assertLessEqual(len(case["source"]["stays"]), 4)
                self.assertLessEqual(len(case["source"]["rooms"]), 18)
                for item in case["source"]["stays"]:
                    self.assertFalse(set(item) & {"guest_name", "email", "passport"})

    def test_expected_stay_outcomes(self):
        cases = {case["id"]: case for case in authoritative_scenarios()}
        expected = {
            "twin-scarcity": "proposed", "maintenance": "no_solution",
            "unknown-occupancy": "manual_review_required",
            "cancelled-hold": "manual_review_required",
            "overlap": "no_solution", "checkout": "proposed",
        }
        self.assertEqual({k: v["report"]["status"] for k, v in cases.items()}, expected)
        proposals = cases["twin-scarcity"]["report"]["proposals"]
        self.assertEqual({p["stay_id"]: p["room_id"] for p in proposals},
                         {"A_FLEX": "D102", "B_TWIN": "T101"})
        self.assertEqual(cases["unknown-occupancy"]["report"]["reason_codes"],
                         ["ROOM_READINESS_UNVERIFIED"])
        self.assertEqual(cases["cancelled-hold"]["report"]["reason_codes"],
                         ["HELD_ROOM_RELEASE_NOT_VERIFIED"])
        self.assertEqual(cases["overlap"]["report"]["proposals"], [])
        checkout = cases["checkout"]["report"]["proposals"]
        self.assertEqual(len(checkout), 2)
        self.assertEqual({p["room_id"] for p in checkout}, {"D102"})

    def test_html_is_self_contained_source_derived_and_non_authorizing(self):
        html = allocation_lab_html()
        self.assertIn("window.ALLOCATION_SCENARIOS=", html)
        self.assertIn("connect-src &#39;none&#39;", html)
        self.assertIn("Önerileri göster", html)
        self.assertIn("DRY_RUN_ONLY", html)
        self.assertIn("human_approval_required", html)
        self.assertIn("Kararın nedenlerini göster", html)
        self.assertEqual(html.count("<script>"), 2)
        self.assertNotIn("https://fonts", html)
        self.assertNotIn('fetch(', html)
        for item in SCENARIOS:
            self.assertIn(item["id"], html)

    def test_cli_write_check_and_reject_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "allocation-lab.html"
            self.assertEqual(main(["--output", str(path)]), 0)
            self.assertEqual(main(["--check", str(path)]), 0)
            self.assertEqual(main(["--output", str(path)]), 2)
            path.write_text("<p>not a source derived page</p>", encoding="utf-8")
            self.assertEqual(main(["--check", str(path)]), 2)

    def test_staging_and_preflight_verify_complete_python_output(self):
        with tempfile.TemporaryDirectory() as d:
            stage = Path(d) / "site"
            stage_site(stage)
            self.assertIn("allocation-lab.html", {p.name for p in stage.iterdir()})
            self.assertEqual((stage / "allocation-lab.html").read_text(encoding="utf-8"),
                             allocation_lab_html())
            self.assertGreater(verify_staged_site(stage)["staged_files"], 23)
            (stage / "allocation-lab.html").write_text("tampered", encoding="utf-8")
            with self.assertRaises(ReleaseReadinessError):
                verify_staged_site(stage)


if __name__ == "__main__":
    unittest.main()
