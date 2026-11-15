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
            self.assertIn('Demo kapsamı:',overview)
            self.assertIn('id="senaryolar"',overview)
            self.assertIn('Henüz yapılmayanlar',overview)
            self.assertIn('ai-command-tour-poster.png',overview)
            self.assertIn('id="gercek-gif"', overview)
            self.assertIn('id="moduller"', overview)
            self.assertNotIn('id="sifreli-kasa"', overview)
            self.assertNotIn('href="privacy-campaign.html"', overview)
            for name in ("privacy-promise.gif", "privacy-promise-poster.jpg", "authorized-device.gif", "authorized-device-poster.jpg", "zero-access-flow.gif", "zero-access-flow-poster.jpg", "future-certification.gif", "future-certification-poster.jpg"):
                self.assertIn(name, PUBLIC_ASSETS)
                self.assertTrue((site/name).is_file(), f"Missing campaign media: {name}")
            campaign=(site/'privacy-campaign.html').read_text(encoding='utf-8')
            self.assertIn('NOT', campaign.upper())
            self.assertIn('Şu anda canlı şifreli otel sistemi değil',campaign)
            self.assertIn('connect-src \'none\'',campaign)
            self.assertIn('Bugün herhangi bir otele KonaklamaFlow güvenlik sertifikası verilmedi',campaign)
            self.assertNotIn('href="privacy-vault-lab.html"',overview)
            vault=(site/'privacy-vault-lab.html').read_text(encoding='utf-8')
            self.assertIn("NOT A PRODUCTION SECURITY FEATURE",vault)
            self.assertIn("connect-src 'none'",vault)
            self.assertIn("crypto.subtle",vault)
            self.assertNotIn('localStorage',vault)
            self.assertNotIn('sessionStorage',vault)
            self.assertIn('FICTIONAL_HOTEL_ONLY',vault)
            self.assertNotIn('id="vizyon"', overview)
            # Real recordings remain visible; unrelated research assets may
            # still be staged, but they must not be promoted by overview.
            for name in ('ai-command-tour.gif', 'roomplan-story.gif',
                         'overview-pulse.gif'):
                self.assertIn(name, overview)
                self.assertTrue((site / name).is_file(), f'Staged demo recording missing: {name}')
            for forbidden in ('otel-degerlendirmesi', 'OPERATOR_FIRST_PARTY_REVIEW',
                              'KonaklamaFlow_Operator_Review', 'imzalı ve kaşeli',
                              'PR #', 'privacy-campaign.html', 'privacy-vault-lab.html'):
                self.assertNotIn(forbidden, overview)
            self.assertIn('id="senaryolar"', overview)
            self.assertIn('id="moduller"', overview)
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
            self.assertIn('href="project-overview.html#senaryolar"', index)
            self.assertNotIn('project-overview.html#otel-degerlendirmesi', index)
            self.assertNotIn('İmzalı ve kaşeli otel değerlendirmesi', index)
            self.assertFalse((site/'.git').exists())
            self.assertFalse((site/'examples').exists())

    def test_existing_output_is_rejected_and_left_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            site=Path(directory)/'site';site.mkdir()
            private=site/'synthetic-private-report.json';private.write_text('synthetic private report')
            with self.assertRaises(ValueError):stage_site(site)
            self.assertEqual(private.read_text(),'synthetic private report')
            self.assertEqual([p.name for p in site.iterdir()],[private.name])
