"""Publish the correct demo without copying private source/history leftovers."""
from pathlib import Path
import tempfile
import unittest
from scripts.stage_demo_site import stage_site, PUBLIC_ASSETS, GENERATED_ASSETS, ROOT


class DemoSiteTests(unittest.TestCase):
    def test_suite_is_entry_point_and_legacy_viewers_remain_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)/'site'
            stage_site(site)
            self.assertEqual((site/'index.html').read_bytes(),(ROOT/'demo/v04-integrated-preview.html').read_bytes())
            overview=(site/'project-overview.html').read_text(encoding='utf-8')
            self.assertEqual(overview,(ROOT/'demo/project-overview.html').read_text(encoding='utf-8'))
            self.assertIn('Geliştirme durumunu açıkça ayırıyoruz',overview)
            self.assertIn('7 / 10',overview)
            self.assertIn('Henüz yapılmayanlar',overview)
            self.assertIn('ai-command-tour-poster.png',overview)
            self.assertIn('id="gercek-gif"', overview)
            self.assertIn('id="vizyon"', overview)
            self.assertIn('Concept art only', overview)
            for name in ('ai-command-tour.gif', 'roomplan-story.gif', 'overview-pulse.gif',
                         'vision-ai-command-core.gif', 'vision-smart-room-grid.gif',
                         'vision-executive-intelligence.gif',
                         'vision-ai-command-core-poster.jpg', 'vision-smart-room-grid-poster.jpg',
                         'vision-executive-intelligence-poster.jpg'):
                self.assertIn(name, overview)
                self.assertTrue((site / name).is_file(), f'Staged showcase asset missing: {name}')
            for number in (51,53,55,58,59):
                self.assertIn(f'pull/{number}',overview)
            self.assertNotIn('<script',overview.lower())

            self.assertEqual((site/'index.html').read_bytes(),(site/'hotel-operations.html').read_bytes())
            self.assertEqual((site/'hotel-suite.html').read_bytes(),(ROOT/'demo/hotel-suite.html').read_bytes())
            self.assertEqual((site/'global-presentation.html').read_bytes(),(ROOT/'demo/global-presentation-concept.html').read_bytes())
            self.assertEqual((site/'reviewer.html').read_bytes(),(ROOT/'demo/viewer.html').read_bytes())
            self.assertEqual((site/'operations.html').read_bytes(),(ROOT/'demo/operations.html').read_bytes())
            self.assertEqual({p.name for p in site.iterdir()},set(PUBLIC_ASSETS)|set(GENERATED_ASSETS)|{'.nojekyll'})
            scorecard = (site/'synthetic-scorecard.html').read_text(encoding='utf-8')
            history = (site/'fictional-trace.html').read_text(encoding='utf-8')
            index = (site/'index.html').read_text(encoding='utf-8')
            self.assertIn('Gerçek otel doğruluğu değildir', scorecard)
            self.assertIn('7 / 10', scorecard)
            self.assertIn('Gerçek personel eylemi', history)
            self.assertIn('href="synthetic-scorecard.html"', index)
            self.assertIn('href="fictional-trace.html"', index)
            self.assertIn('href="project-overview.html"', index)
            self.assertFalse((site/'.git').exists())
            self.assertFalse((site/'examples').exists())

    def test_existing_output_is_rejected_and_left_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            site=Path(directory)/'site';site.mkdir()
            private=site/'synthetic-private-report.json';private.write_text('synthetic private report')
            with self.assertRaises(ValueError):stage_site(site)
            self.assertEqual(private.read_text(),'synthetic private report')
            self.assertEqual([p.name for p in site.iterdir()],[private.name])
