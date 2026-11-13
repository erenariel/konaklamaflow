"""Independent cross-projection regressions for canonical identity and holds."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from konaklamaflow.canonical import CanonicalError, project_review, validate_canonical
from konaklamaflow.canonical_presentation import build_presentation
from konaklamaflow.experience_engine import evaluate


SOURCE = json.loads((Path(__file__).resolve().parents[1] /
                     'examples/canonical-hotel.json').read_text(encoding='utf-8'))


class CanonicalIntegrityReviewTests(unittest.TestCase):
    def setUp(self):
        self.source = deepcopy(SOURCE)

    def test_unassigned_booking_cannot_silently_lose_a_room_scoped_task(self):
        booking = next(row for row in self.source['reservations'] if row['id'] == 'KF1002')
        stay = next(row for row in self.source['room_stays']
                    if row['id'] == booking['room_stay_ids'][0])
        self.assertIsNone(stay['room_id'])
        self.source['tasks'].append({'id': 'TASK-EXPLICIT-UNASSIGNED', 'kind': 'frontdesk',
            'room_id': '202', 'reservation_id': booking['id'],
            'status': 'open', 'priority': 'normal'})
        # Both FKs would assert a relationship that the source never assigned.
        # Reject it, rather than retaining it in PMS but dropping it from review.
        with self.assertRaises(CanonicalError):
            validate_canonical(self.source)

    def test_unassigned_booking_task_and_independent_room_task_are_both_retained(self):
        tasks = [
            {'id': 'TASK-UNASSIGNED-BOOKING', 'kind': 'frontdesk', 'room_id': None,
             'reservation_id': 'KF1002', 'status': 'open', 'priority': 'normal'},
            {'id': 'TASK-INDEPENDENT-ROOM', 'kind': 'housekeeping', 'room_id': '202',
             'reservation_id': None, 'status': 'open', 'priority': 'normal'},
        ]
        self.source['tasks'].extend(tasks)
        projected = {row['id']: row for row in project_review(self.source)['tasks']}
        for task in tasks:
            self.assertEqual(projected[task['id']], task)

    def test_explicit_source_block_is_not_ignored_when_base_room_is_inspected(self):
        room = next(row for row in self.source['rooms'] if row['id'] == '201')
        self.assertEqual(room['housekeeping'], 'inspected')
        self.source['room_blocks'].append({'id': 'BLOCK-REVIEW-201', 'room_id': '201',
            'start': self.source['as_of'], 'end': None, 'kind': 'hold', 'status': 'active'})
        report = evaluate(project_review(self.source))
        arrival = next(row for row in report['arrivals'] if row['id'] == 'KF1010')
        self.assertEqual(arrival['status'], 'blocked')
        self.assertIn('ROOM_INCOMPATIBLE', arrival['blockers'])
        self.assertNotEqual(arrival['suggested_room'], '201')
        bundle = build_presentation(self.source)
        blockage = next(row for row in bundle['operations_report']['reports']['blockage_report']['rows']
                        if row['room'] == '201')
        self.assertIn('BLOCK-REVIEW-201', blockage['room_block_ids'])
        timeline = next(row for row in bundle['concept']['timeline']['rows'] if row['room_id'] == '201')
        current = next(cell for cell in timeline['cells'] if cell['date'] == self.source['as_of'])
        self.assertTrue(current['technical'])

    def test_building_every_view_preserves_source_and_all_explicit_folio_links(self):
        for key in ('reservations', 'room_stays', 'rooms', 'folios', 'guests', 'agencies'):
            self.source[key].reverse()
        before = deepcopy(self.source)
        bundle = build_presentation(self.source)
        self.assertEqual(self.source, before)
        source_folios = {row['id']: row for row in self.source['folios']}
        stays = {row['id']: row for row in self.source['room_stays']}
        for row in bundle['operations_report']['folios']:
            source = source_folios[row['folio_id']]
            self.assertEqual(row['reservation_id'], source['reservation_id'])
            self.assertEqual(row['room_stay_id'], source['room_stay_id'])
            self.assertEqual(row['room_id'], stays[source['room_stay_id']]['room_id'])
        for identifier, link in bundle['canonical_links']['reservations'].items():
            self.assertEqual(set(link['folio_ids']), {row['id'] for row in source_folios.values()
                                                     if row['reservation_id'] == identifier})


if __name__ == '__main__':
    unittest.main()
