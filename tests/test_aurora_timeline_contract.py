"""Aurora timeline source and embedded demo remain exactly synchronized."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AuroraTimelineContractTests(unittest.TestCase):
    def test_ui_and_css_are_embedded_once_in_offline_html(self):
        html = (ROOT / 'demo/v04-integrated-preview.html').read_text(encoding='utf-8')
        for file, left, right in (
            ('aurora-timeline.js', '// BEGIN GENERATED_AURORA_TIMELINE_UI',
             '// END GENERATED_AURORA_TIMELINE_UI'),
            ('aurora-timeline.css', '/* BEGIN GENERATED_AURORA_TIMELINE_STYLES */',
             '/* END GENERATED_AURORA_TIMELINE_STYLES */'),
        ):
            raw = (ROOT / 'demo' / file).read_text(encoding='utf-8')
            self.assertEqual(html.count(left), 1)
            self.assertEqual(html.count(right), 1)
            self.assertIn(left+'\n'+raw+'\n'+right, html)

    def test_ui_uses_single_canonical_source_with_no_live_writes(self):
        js = (ROOT / 'demo/aurora-timeline.js').read_text(encoding='utf-8')
        self.assertIn('CANONICAL_DATA.reservations', js)
        self.assertIn('window.canonicalReservationId', js)
        self.assertIn('auroraRoomSource()', js)
        self.assertNotIn('fetch(', js)
        self.assertNotIn('localStorage', js)
        self.assertNotIn('XMLHttpRequest', js)
        self.assertNotIn('navigator.sendBeacon', js)
        self.assertIn('auroraTimelineFilterState', js)
        self.assertEqual(js.count('const auroraTimelineTranslations'), 1)

if __name__ == '__main__':
    unittest.main()
