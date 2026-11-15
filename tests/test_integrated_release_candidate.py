"""Cross-feature, fail-closed checks for the offline integration candidate."""
from pathlib import Path
import tempfile
import unittest

from scripts.stage_demo_site import stage_site, ROOT, PUBLIC_ASSETS, GENERATED_ASSETS
from scripts.render_scorecard import authoritative_report
from scripts.render_trace_view import trusted_trace


class IntegratedReleaseCandidateTests(unittest.TestCase):
    def test_source_verified_pages_are_staged_and_linked(self):
        self.assertEqual(set(GENERATED_ASSETS), {
            "synthetic-scorecard.html", "fictional-trace.html"
        })
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"site"
            stage_site(path)
            self.assertEqual({p.name for p in path.iterdir()},
                             set(PUBLIC_ASSETS)|set(GENERATED_ASSETS)|{".nojekyll"})
            index=(path/"index.html").read_text(encoding="utf-8")
            for link in ("synthetic-scorecard.html", "fictional-trace.html",
                         "project-overview.html", "BEGIN GENERATED_DECISION_EVIDENCE_UI"):
                self.assertIn(link,index)
            scorecard=(path/"synthetic-scorecard.html").read_text(encoding="utf-8")
            trace=(path/"fictional-trace.html").read_text(encoding="utf-8")
            self.assertIn("7 / 10",scorecard)
            self.assertIn("Gerçek otel doğruluğu değildir",scorecard)
            self.assertIn("Gerçek personel eylemi",trace)
            for private in ("examples", "evaluation", ".git", "konaklamaflow",
                            "docs", "README.md", "tests"):
                self.assertFalse((path/private).exists())

    def test_original_python_truth_and_human_boundary_remain_intact(self):
        report=authoritative_report()
        self.assertEqual(report["summary"]["total_cases"],10)
        self.assertEqual(report["summary"]["evaluated"],7)
        self.assertEqual(report["human_override_rate"],"not_measured")
        _,_,trace=trusted_trace()
        self.assertEqual(trace["mode"],"DRY_RUN_ONLY")
        self.assertEqual(len(trace["events"]),3)
        self.assertIn("NO_AUTHORIZATION",trace["boundary"])

    def test_sandbox_sources_and_site_paths_are_distinct(self):
        self.assertEqual(PUBLIC_ASSETS["project-overview.html"],"demo/project-overview.html")
        self.assertEqual(PUBLIC_ASSETS["index.html"],"demo/v04-integrated-preview.html")
        body=(ROOT/"demo/v04-integrated-preview.html").read_text(encoding="utf-8")
        self.assertIn("source_bound",body)
        self.assertIn("DRY_RUN_ONLY",body)


if __name__=="__main__":
    unittest.main()
