"""Release-copy, external-link and staging safety checks."""
from pathlib import Path
import tempfile
import unittest

from scripts.stage_demo_site import stage_site
from scripts.verify_release_readiness import (
    ReleaseReadinessError,
    verify_overview_content,
    verify_staged_site,
    main,
)


class ReleaseReadinessTests(unittest.TestCase):
    def test_fully_integrated_staged_site_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder) / "stage"
            stage_site(stage)
            result = verify_staged_site(stage)
            self.assertGreater(result["staged_files"], 15)
            self.assertGreaterEqual(result["internal_links"], 1)
            self.assertGreaterEqual(result["local_images"], 1)
            self.assertEqual(main(["--site", str(stage)]), 0)

    def test_pages_deployment_invokes_same_preflight(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("python -m scripts.verify_release_readiness --site _site", workflow)
        self.assertIn("workflow_run", workflow)
        self.assertIn("branches: [main]", workflow)

    def test_private_or_unexpected_staged_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder) / "stage"
            stage_site(stage)
            (stage / "guest-export.json").write_text("{}")
            with self.assertRaises(ReleaseReadinessError):
                verify_staged_site(stage)
            self.assertEqual(main(["--site", str(stage)]), 2)

    def test_corrupt_generated_scorecard_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder) / "stage"
            stage_site(stage)
            (stage / "synthetic-scorecard.html").write_text("<p>forged</p>")
            with self.assertRaises(ReleaseReadinessError):
                verify_staged_site(stage)

    def test_missing_poster_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder) / "stage"
            stage_site(stage)
            (stage / "ai-command-tour-poster.png").unlink()
            with self.assertRaises(ReleaseReadinessError):
                verify_staged_site(stage)

    def test_symlink_staged_asset_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder) / "stage"
            stage_site(stage)
            target = stage / "project-overview.html"
            target.unlink()
            target.symlink_to(stage / "index.html")
            with self.assertRaises(ReleaseReadinessError):
                verify_staged_site(stage)

    def test_stale_copy_and_offsite_img_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder) / "stage"
            stage_site(stage)
            overview = (stage / "project-overview.html").read_text(encoding="utf-8")
            staged = {p.name for p in stage.iterdir()}
            with self.assertRaises(ReleaseReadinessError):
                verify_overview_content(
                    overview + "henüz ana sürüme birleştirilmediler", staged)
            with self.assertRaises(ReleaseReadinessError):
                verify_overview_content(
                    overview.replace("ai-command-tour-poster.png",
                                     "https://tracker.example.org/pixel.gif"), staged)
            with self.assertRaises(ReleaseReadinessError):
                verify_overview_content(
                    overview.replace("href=\"index.html\"",
                                     "href=\"../../private.html\""), staged)


if __name__ == "__main__":
    unittest.main()
