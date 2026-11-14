"""Published motion assets must depict the current real, fictional UI."""
from hashlib import sha256
import json
from pathlib import Path
import struct
import unittest

from konaklamaflow.demo_stories import report_fingerprint

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / 'docs/images'
PROFILES = ('ai-command-tour', 'roomplan-story', 'overview-pulse')


def gif_frames(data):
    """Count encoded image frames, without assuming a manifest is truthful."""
    if data[:6] not in (b'GIF87a', b'GIF89a'):
        raise ValueError('Invalid GIF')
    packed = data[10]
    offset = 13 + (3 * (2 ** ((packed & 7) + 1)) if packed & 128 else 0)
    count = 0

    def subblocks(position):
        while True:
            size = data[position]
            position += 1
            if size == 0:
                return position
            position += size

    while offset < len(data):
        tag = data[offset]
        offset += 1
        if tag == 0x3B:
            return count
        if tag == 0x21:
            offset = subblocks(offset + 1)
        elif tag == 0x2C:
            packed = data[offset + 8]
            offset += 9 + (3 * (2 ** ((packed & 7) + 1)) if packed & 128 else 0)
            offset = subblocks(offset + 1)
            count += 1
        else:
            raise ValueError('Unexpected GIF block')
    raise ValueError('Missing GIF trailer')


class ShowcaseMediaTests(unittest.TestCase):
    def test_all_three_recordings_match_current_integrated_source_and_real_frames(self):
        source_hash = sha256((ROOT / 'demo/v04-integrated-preview.html').read_bytes()).hexdigest()
        report = json.loads((ROOT / 'examples/operations-evaluation.json').read_text())
        for name in PROFILES:
            with self.subTest(profile=name):
                metadata = json.loads((IMAGES / (name + '.json')).read_text())
                gif = (IMAGES / (name + '.gif')).read_bytes()
                poster = (IMAGES / (name + '-poster.png')).read_bytes()
                self.assertEqual(metadata['kind'], 'ACTUAL_INTEGRATED_FICTIONAL_BROWSER_SHOWCASE')
                self.assertEqual(metadata['profile'], name)
                self.assertEqual(metadata['html_sha256'], source_hash)
                self.assertEqual(metadata['gif_sha256'], sha256(gif).hexdigest())
                self.assertEqual(metadata['poster_sha256'], sha256(poster).hexdigest())
                self.assertEqual(metadata['frames'], gif_frames(gif))
                self.assertGreaterEqual(metadata['frames'], 26)
                self.assertLess(len(gif), 5_000_000)
                self.assertEqual(metadata['snapshot_sha256'], report['snapshot_sha256'])
                self.assertEqual(metadata['report_sha256'], report_fingerprint(report))
                self.assertEqual(metadata['external_requests'], 0)
                self.assertEqual(metadata['browser_errors'], 0)
                self.assertTrue(metadata['canonical_source_unchanged'])
                self.assertTrue(metadata['canonical_report_unchanged'])
                for flag in ('live_ai_calls', 'pms_writes', 'payments', 'kbs'):
                    self.assertIs(metadata[flag], False)

    def test_recorded_tour_covers_all_engine_story_phases_and_room_plan_actions(self):
        tour = json.loads((IMAGES / 'ai-command-tour.json').read_text())
        self.assertTrue({'0', '1', '2', '3', '4'} <= set(tour['observed_story_steps']))
        self.assertIn('play_actual_scripted_tour', tour['interactions'])
        room = json.loads((IMAGES / 'roomplan-story.json').read_text())
        self.assertTrue({'open_room_plan', 'inspect_fictional_room_303',
                         'inspect_technical_hold', 'return_to_snapshot_week',
                         'inspect_canonical_room_101'} <= set(room['interactions']))

    def test_preview_manifest_binds_all_sources_and_required_desktop_dimensions(self):
        manifest = json.loads((IMAGES / 'v052-previews.json').read_text())
        self.assertEqual(manifest['requests'], [])
        self.assertEqual(manifest['errors'], [])
        self.assertTrue(manifest['fictional'])
        self.assertTrue({'aurora-room-plan-desktop.png', 'aurora-room-plan-mobile.png',
                         'aurora-room-plan-night.png', 'aurora-room-plan-rtl.png'}
                        <= {row['file'] for row in manifest['captures']})
        for name, checksum in manifest['source_files'].items():
            self.assertEqual(sha256((ROOT / 'demo' / name).read_bytes()).hexdigest(), checksum)
        dimensions = set()
        for row in manifest['captures']:
            data = (IMAGES / row['file']).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', data[16:24]), (row['width'], row['height']))
            self.assertEqual(sha256(data).hexdigest(), row['sha256'])
            self.assertTrue(row['body_within_viewport'])
            dimensions.add((row['width'], row['height']))
        self.assertTrue({(1366, 768), (1440, 900), (1600, 900)} <= dimensions)
