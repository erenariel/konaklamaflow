"""Publish the correct demo without copying private source/history leftovers."""
from pathlib import Path
import tempfile
import unittest
from scripts.stage_demo_site import stage_site, PUBLIC_ASSETS, ROOT


class DemoSiteTests(unittest.TestCase):
    def test_suite_is_entry_point_and_legacy_viewers_remain_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)/'site'
            stage_site(site)
            self.assertEqual((site/'index.html').read_bytes(),(ROOT/'demo/v04-integrated-preview.html').read_bytes())
            self.assertEqual((site/'index.html').read_bytes(),(site/'hotel-operations.html').read_bytes())
            self.assertEqual((site/'hotel-suite.html').read_bytes(),(ROOT/'demo/hotel-suite.html').read_bytes())
            self.assertEqual((site/'reviewer.html').read_bytes(),(ROOT/'demo/viewer.html').read_bytes())
            self.assertEqual((site/'operations.html').read_bytes(),(ROOT/'demo/operations.html').read_bytes())
            self.assertEqual({p.name for p in site.iterdir()},set(PUBLIC_ASSETS)|{'.nojekyll'})
            self.assertFalse((site/'.git').exists())
            self.assertFalse((site/'examples').exists())

    def test_existing_output_is_rejected_and_left_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            site=Path(directory)/'site';site.mkdir()
            private=site/'synthetic-private-report.json';private.write_text('synthetic private report')
            with self.assertRaises(ValueError):stage_site(site)
            self.assertEqual(private.read_text(),'synthetic private report')
            self.assertEqual([p.name for p in site.iterdir()],[private.name])
