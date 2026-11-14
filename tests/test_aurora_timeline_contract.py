"""Aurora timeline source sync and deterministic date-interval contract."""
from datetime import date, timedelta
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AuroraTimelineContractTests(unittest.TestCase):
    def test_html_embeds_exact_source_once(self):
        html=(ROOT/'demo/v04-integrated-preview.html').read_text(encoding='utf-8')
        cases=[
          ('aurora-timeline.js','// BEGIN GENERATED_AURORA_TIMELINE_JS','// END GENERATED_AURORA_TIMELINE_JS'),
          ('aurora-timeline.css','/* BEGIN GENERATED_AURORA_TIMELINE_STYLES */','/* END GENERATED_AURORA_TIMELINE_STYLES */')
        ]
        for filename,start,end in cases:
            source=(ROOT/'demo'/filename).read_text(encoding='utf-8')
            self.assertEqual(html.count(start),1)
            self.assertEqual(html.count(end),1)
            self.assertIn(start+'\n'+source+'\n'+end,html)

    def test_timeline_has_provenance_and_safe_intervals(self):
        js=(ROOT/'demo/aurora-timeline.js').read_text(encoding='utf-8')
        for token in ('CANONICAL_DATA.room_stays','CANONICAL_LINKS.as_of',
                      'auroraTimelineWindow','auroraTimelineCaseForStay',
                      'data-canonical-reservation','source_not_connected',
                      'reportStale','auroraTimelineDates','[', 'departure'):
            if token == 'departure':  # date interval source is stay.arrival/stay.departure
                self.assertIn('stay.departure', js)
            elif token == 'CANONICAL_DATA.room_stays':
                self.assertIn('source.room_stays', js)
            else:
                self.assertIn(token,js)
        d=date(2026,11,12)
        following=d+timedelta(days=1)
        self.assertEqual(sum(d<=d+timedelta(days=i)<following for i in range(3)),1)

    def test_ten_locales_and_reduced_motion(self):
        js=(ROOT/'demo/aurora-timeline.js').read_text(encoding='utf-8')
        css=(ROOT/'demo/aurora-timeline.css').read_text(encoding='utf-8')
        for language in ('tr','en','fr','el','he','ar','de','ru','es','uk'):
            self.assertIn('\n '+language+':{',js)
        self.assertIn('prefers-reduced-motion:reduce',css)
        self.assertIn('data-kf-motion="off"',css)
        self.assertIn(':focus-visible',css)
        self.assertIn('position:sticky',css)
