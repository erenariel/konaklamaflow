"""The public motion preview must represent the current reviewed app/data."""
from hashlib import sha256
import json
from pathlib import Path
import unittest
from konaklamaflow.demo_stories import build_demo_stories

ROOT=Path(__file__).resolve().parents[1]


class DemoRecordingTests(unittest.TestCase):
    def test_recorded_preview_is_current_complete_fictional_and_offline(self):
        metadata=json.loads((ROOT/'docs/images/operations-tour.json').read_text())
        gif=(ROOT/'docs/images/operations-tour.gif').read_bytes()
        self.assertIn(gif[:6],(b'GIF87a',b'GIF89a'))
        self.assertLess(len(gif),5_000_000)
        self.assertEqual(metadata['html_sha256'],sha256((ROOT/'demo/hotel-suite.html').read_text(encoding='utf-8').encode()).hexdigest())
        self.assertEqual(metadata['gif_sha256'],sha256(gif).hexdigest())
        stories=build_demo_stories(json.loads((ROOT/'examples/fictional-hotel.json').read_text()))
        self.assertEqual(metadata['snapshot_sha256'],stories['snapshot_sha256'])
        self.assertEqual(metadata['report_sha256'],stories['report_sha256'])
        story=next(s for s in stories['stories'] if s['id']==metadata['story_id'])
        self.assertEqual(metadata['observed_steps'],[str(i) for i in range(len(story['steps']))])
        self.assertEqual(metadata['external_requests'],0)
        self.assertEqual(metadata['browser_errors'],0)
        self.assertGreater(metadata['frames'],5)
        self.assertEqual(metadata['kind'],'ACTUAL_FICTIONAL_BROWSER_TOUR')
        self.assertTrue(all(metadata[key] is False for key in ('live_ai_calls','pms_writes','payments','kbs')))
