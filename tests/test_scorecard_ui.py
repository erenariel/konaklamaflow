"""Scorecard is rendered from current Python evaluation, not authored percentages."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.render_scorecard import authoritative_report, render_scorecard, scorecard_html, main
from scripts.stage_demo_site import stage_site, PUBLIC_ASSETS, GENERATED_ASSETS


class ScorecardUiTests(unittest.TestCase):
    def test_source_counts_labels_and_exclusions_are_visible(self):
        report=authoritative_report()
        self.assertEqual(report["summary"]["evaluated"],7)
        self.assertEqual(report["summary"]["total_cases"],10)
        page=render_scorecard(report)
        self.assertEqual(page.count('class="card"'),4)
        self.assertIn("70.0%",page)
        self.assertIn("Excluded: unsupported=2; unlabelled=1",page)
        self.assertIn("not_measured",page)
        self.assertIn("Gerçek otel doğruluğu değildir",page)
        for case in report["cases"]:
            self.assertIn(case["id"],page)
        self.assertNotIn("<script",page.lower())
        self.assertEqual(page,scorecard_html())

    def test_forged_reports_are_rejected_even_when_ratios_look_plausible(self):
        report=authoritative_report()
        mutations=[
            ("summary","evaluated",10),
            ("metrics","precision",1.0),
            ("metrics","tp",999),
            ("cases",0,"new_case"),
        ]
        for section,key,value in mutations:
            fake=deepcopy(report)
            if section=="cases":fake["cases"][key]["id"]=value
            else:fake[section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(ValueError):
                render_scorecard(fake)
        self.assertEqual(render_scorecard(report),scorecard_html())

    def test_generator_check_and_staging_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"scorecard.html"
            self.assertEqual(main(["--output",str(path)]),0)
            self.assertEqual(main(["--check",str(path)]),0)
            path.write_text("tampered",encoding="utf-8")
            self.assertEqual(main(["--check",str(path)]),2)
            self.assertEqual(main(["--output",str(path)]),2)
            site=Path(folder)/"site"
            stage_site(site)
            self.assertEqual((site/"synthetic-scorecard.html").read_text(encoding="utf-8"),
                             scorecard_html())
            self.assertEqual({p.name for p in site.iterdir()},
                             set(PUBLIC_ASSETS)|set(GENERATED_ASSETS)|{".nojekyll"})


if __name__=="__main__":
    unittest.main()
