"""Catch stale or split sources across the shipped offline entry points."""
import json
from pathlib import Path
import re
import unittest

from konaklamaflow.canonical_presentation import build_presentation
from scripts.generate_canonical_demo import generate

ROOT = Path(__file__).resolve().parents[1]


def embedded(filename, name):
    document = (ROOT / 'demo' / filename).read_text(encoding='utf-8')
    match = re.search(r'\bconst\s+' + re.escape(name) + r'\s*=\s*', document)
    if match is None:
        raise AssertionError('Missing generated source: ' + name)
    return json.JSONDecoder().raw_decode(document[match.end():])[0]


class CanonicalGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT / 'examples/canonical-hotel.json').read_text())
        cls.bundle = build_presentation(cls.source)

    def test_generated_artifacts_are_current_without_mutation(self):
        # The check path must reject stale output, never repair it silently.
        generate(check=True)

    def test_review_and_operations_entry_points_have_exact_same_parent_source(self):
        for filename in ('hotel-suite.html', 'v04-integrated-preview.html'):
            with self.subTest(filename=filename):
                self.assertEqual(embedded(filename, 'CANONICAL_DATA'), self.source)
                self.assertEqual(embedded(filename, 'INITIAL_DATA'), self.bundle['review_data'])
                self.assertEqual(embedded(filename, 'INITIAL_EVALUATION'), self.bundle['review_report'])
                self.assertEqual(embedded(filename, 'CANONICAL_LINKS'), self.bundle['canonical_links'])
        self.assertEqual(embedded('v04-integrated-preview.html', 'HOTEL_OPS_DATA'),
                         self.bundle['operations_data'])
        self.assertEqual(embedded('v04-integrated-preview.html', 'HOTEL_OPS_REPORT'),
                         self.bundle['operations_report'])

    def test_catalog_and_global_tour_are_bound_to_their_correct_source_hashes(self):
        catalog = embedded('v04-integrated-preview.html', 'V04_CATALOG')
        self.assertEqual(catalog['sourceSha'], self.bundle['review_report']['snapshot_sha256'])
        concept = embedded('global-presentation-concept.html', 'CANONICAL_CONCEPT')
        self.assertEqual(concept, self.bundle['concept'])
        self.assertEqual(concept['canonical_sha256'],
                         self.bundle['operations_report']['canonical_sha256'])

    def test_every_ai_story_booking_and_room_resolves_to_explicit_stay(self):
        links = self.bundle['canonical_links']
        stays = {row['id']: row for row in self.source['room_stays']}
        self.assertEqual(len(self.bundle['stories']['stories']), 4)
        for story in self.bundle['stories']['stories']:
            relation = links['review_links'][story['booking_id']]
            stay = stays[relation['room_stay_id']]
            self.assertEqual(stay['reservation_id'], relation['reservation_id'])
            self.assertIn(stay['id'], links['reservations'][stay['reservation_id']]['room_stay_ids'])

    def test_source_json_outputs_are_reproducible_and_not_historical_kfd_aliases(self):
        for filename, key in (('canonical-review.json', 'review_data'),
                              ('canonical-review-report.json', 'review_report'),
                              ('canonical-operations.json', 'operations_data'),
                              ('canonical-operations-report.json', 'operations_report')):
            with self.subTest(filename=filename):
                actual = json.loads((ROOT / 'examples' / filename).read_text())
                self.assertEqual(actual, self.bundle[key])
                self.assertNotIn('KFD-2026-', json.dumps(actual))
