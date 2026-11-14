"""Source-bound room status, independent axes and interval regressions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from konaklamaflow.canonical import (CanonicalError, canonical_fingerprint,
                                    project_review, review_links)
from konaklamaflow.experience_engine import evaluate
from konaklamaflow.room_graph import build_room_graph


SOURCE = json.loads((Path(__file__).resolve().parents[1] /
                     'examples/canonical-hotel.json').read_text(encoding='utf-8'))


class RoomGraphTests(unittest.TestCase):
    def setUp(self):
        self.source = deepcopy(SOURCE)

    def booking(self, identifier='KF1010'):
        return next(row for row in self.source['reservations'] if row['id'] == identifier)

    def stay(self, identifier='KF1010'):
        return next(row for row in self.source['room_stays'] if row['reservation_id'] == identifier)

    def room(self, identifier='201'):
        return next(row for row in self.source['rooms'] if row['id'] == identifier)

    def shown(self, identifier='201'):
        return next(row for row in build_room_graph(self.source)['rooms'] if row['id'] == identifier)

    def move(self, identifier, room):
        self.stay(identifier)['room_id'] = room
        for task in self.source['tasks']:
            if task['reservation_id'] == identifier and task['room_id'] is not None:
                task['room_id'] = room

    def test_default_snapshot_has_no_invented_physical_vacancy_or_checkin(self):
        graph = build_room_graph(self.source)
        self.assertEqual(graph['canonical_sha256'], canonical_fingerprint(self.source))
        self.assertEqual(graph['source_state'], 'synthetic_snapshot')
        self.assertEqual(graph['physical_occupancy_source'], 'source_not_connected')
        self.assertEqual(graph['as_of'], self.source['as_of'])
        self.assertEqual(graph['summary']['rooms'], 18)
        self.assertEqual(graph['summary']['floors'], 5)
        self.assertEqual(graph['summary']['assigned_rooms'], 8)
        self.assertEqual(graph['summary']['physical_occupied_signals'], 0)
        self.assertEqual(graph['summary']['physical_unknown_rooms'], 18)
        self.assertTrue(all(room['occupancy_state'] == 'unknown' for room in graph['rooms']))
        self.assertNotIn('vacant', {room['occupancy_state'] for room in graph['rooms']})
        self.assertEqual(self.shown('103')['assignment_state'], 'unassigned')
        self.assertIn('vacant_unverified', self.shown('103')['state_codes'])

    def test_housekeeping_changes_do_not_create_physical_occupancy(self):
        self.booking()['arrival_state'] = 'checked_in'
        for housekeeping in ('dirty', 'clean', 'inspected', 'in_progress'):
            with self.subTest(housekeeping=housekeeping):
                self.room()['housekeeping'] = housekeeping
                room = self.shown()
                self.assertEqual(room['housekeeping'], housekeeping)
                self.assertEqual(room['housekeeping_cleanliness'], housekeeping)
                self.assertEqual(room['occupancy_state'], 'occupied')
                self.assertEqual(room['occupancy_source'], 'synthetic_checked_in_signal')
                self.assertEqual(room['physical_reservation_ids'], ['KF1010'])

    def test_in_house_status_is_an_explicit_signal_not_proof_of_room_readiness(self):
        self.booking()['status'] = 'in_house'
        self.room()['housekeeping'] = 'dirty'
        room = self.shown()
        self.assertEqual(room['occupancy_state'], 'occupied')
        self.assertIn('HOUSEKEEPING_NOT_INSPECTED', room['reason_codes'])
        self.assertEqual(room['review_status'], 'blocked')

    def test_ooo_and_oos_do_not_masquerade_as_cleanliness_or_occupancy(self):
        for state in ('out_of_order', 'out_of_service'):
            with self.subTest(state=state):
                self.room()['housekeeping'] = state
                room = self.shown()
                self.assertEqual(room['housekeeping'], state)
                self.assertEqual(room['housekeeping_cleanliness'], 'unknown')
                self.assertEqual(room['occupancy_state'], 'unknown')
                self.assertIn(state, room['state_codes'])
                self.assertIn('blocked', room['state_codes'])

    def test_checkout_night_excluded_but_unreleased_departure_hold_retained(self):
        stay = self.stay()
        stay.update(arrival='2026-11-11', departure='2026-11-12', nightly_rates=[])
        room = self.shown()
        self.assertEqual(room['active_reservation_ids'], [])
        self.assertEqual(room['assigned_people'], 0)
        self.assertEqual(room['assignment_state'], 'unassigned')
        self.assertEqual(room['departures'], ['KF1010'])
        self.assertEqual(room['held_reservation_ids'], ['KF1010'])
        self.assertIn('expected_departure', room['state_codes'])
        self.assertEqual(room['occupancy_state'], 'unknown')

    def test_same_day_confirmed_checkout_and_checkin_are_not_overlapping_nights(self):
        self.stay().update(arrival='2026-11-11', departure='2026-11-12', nightly_rates=[])
        self.booking().update(status='checked_out', arrival_state='checked_out')
        self.move('KF1003', '201')
        room = self.shown()
        self.assertEqual(room['active_reservation_ids'], ['KF1003'])
        self.assertEqual(room['arrivals'], ['KF1003'])
        self.assertEqual(room['departures'], [])
        self.assertNotIn('ROOM_CONFLICT', room['reason_codes'])
        self.assertNotIn('conflict', room['state_codes'])
        self.assertEqual(room['held_reservation_ids'], ['KF1003'])
        self.assertEqual(set(room['reservation_ids']), {'KF1003', 'KF1010'})

    def test_true_overlap_comes_from_the_existing_python_rule_report(self):
        self.move('KF1003', '201')
        room = self.shown()
        engine = evaluate(project_review(self.source))
        for identifier in ('KF1003', 'KF1010'):
            row = next(row for row in engine['arrivals'] if row['id'] == identifier)
            self.assertIn('ROOM_CONFLICT', row['blockers'])
        self.assertIn('ROOM_CONFLICT', room['reason_codes'])
        self.assertIn('conflict', room['state_codes'])
        self.assertEqual(set(room['active_reservation_ids']), {'KF1003', 'KF1010'})

    def test_cancelled_physical_signal_remains_occupied_and_blocked(self):
        self.booking('KF1006')['arrival_state'] = 'checked_in'
        room = self.shown('102')
        self.assertEqual(room['active_reservation_ids'], [])
        self.assertEqual(room['physical_reservation_ids'], ['KF1006'])
        self.assertEqual(room['held_reservation_ids'], ['KF1006'])
        self.assertEqual(room['occupancy_state'], 'occupied')
        self.assertIn('blocked', room['state_codes'])
        self.assertIn('CANCELLED_ASSIGNED', room['reason_codes'])

    def test_pending_and_no_show_remain_distinct_and_never_become_checkins(self):
        self.booking()['status'] = 'pending'
        room = self.shown()
        self.assertEqual(room['active_reservation_ids'], ['KF1010'])
        self.assertEqual(room['occupancy_state'], 'unknown')
        self.assertIn('NOT_CONFIRMED', room['reason_codes'])
        self.booking()['status'] = 'no_show'
        room = self.shown()
        self.assertEqual(room['active_reservation_ids'], [])
        self.assertEqual(room['arrivals'], [])
        self.assertEqual(room['held_reservation_ids'], ['KF1010'])
        self.assertEqual(room['occupancy_state'], 'unknown')
        self.assertIn('no_show_hold', room['state_codes'])
        self.assertNotIn('occupied', room['state_codes'])

    def test_explicit_block_dates_are_half_open_and_keep_original_housekeeping(self):
        block = {'id': 'BLOCK-TEST-201', 'room_id': '201', 'start': '2026-11-12',
                 'end': '2026-11-13', 'kind': 'out_of_service', 'status': 'active'}
        self.source['room_blocks'].append(block)
        room = self.shown()
        self.assertEqual(room['block_ids'], ['BLOCK-TEST-201'])
        self.assertIn('out_of_service', room['state_codes'])
        self.assertIn('blocked', room['state_codes'])
        self.assertEqual(room['housekeeping_cleanliness'], 'inspected')
        block.update(start='2026-11-11', end='2026-11-12')
        room = self.shown()
        self.assertEqual(room['block_ids'], [])
        self.assertNotIn('out_of_service', room['state_codes'])
        block.update(start='2026-11-13', end='2026-11-14')
        self.assertEqual(self.shown()['block_ids'], [])

    def test_legacy_maintenance_has_source_window_without_invented_block_id(self):
        self.room()['maintenance'] = [{'start': '2026-11-12', 'end': '2026-11-13'}]
        room = self.shown()
        self.assertTrue(room['maintenance_active'])
        self.assertIn('blocked', room['state_codes'])
        self.assertEqual(room['block_ids'], [])
        self.assertIn('OUT_OF_SERVICE_OR_MAINTENANCE', room['reason_codes'])

    def test_multiroom_parent_and_stay_ids_survive_projection_without_first_room_collapse(self):
        parent = self.booking('KF1011')
        second = deepcopy(self.stay('KF1011'))
        guest = deepcopy(self.source['guests'][0])
        guest.update(id='GUEST-MULTI-TEST', surname='DEMO_MULTI_TEST', display_label='ÖRNEK MULTI TEST')
        self.source['guests'].append(guest)
        second.update(id='STAY-MULTI-TEST', room_id='402', adults=1,
                      guest_ids=[guest['id']], bed_request='none', requests=[])
        self.source['room_stays'].append(second)
        parent['room_stay_ids'].append(second['id'])
        parent['guest_ids'].append(guest['id'])
        graph = build_room_graph(self.source)
        for room_id, stay_id in (('302', 'STAY-KF1011-A'), ('402', 'STAY-MULTI-TEST')):
            with self.subTest(room=room_id):
                room = next(row for row in graph['rooms'] if row['id'] == room_id)
                self.assertIn('KF1011', room['reservation_ids'])
                self.assertIn(stay_id, room['room_stay_ids'])
        self.assertEqual({link['reservation_id'] for link in review_links(self.source).values()
                          if link['room_stay_id'] in parent['room_stay_ids']}, {'KF1011'})

    def test_source_reordering_does_not_change_room_relationships_or_mutate_source(self):
        before = deepcopy(self.source)
        original = build_room_graph(self.source)
        self.assertEqual(self.source, before)
        for key in ('rooms', 'reservations', 'room_stays', 'guests', 'room_blocks'):
            self.source[key].reverse()
        self.assertEqual(build_room_graph(self.source)['rooms'], original['rooms'])

    def test_missing_or_invalid_source_fails_closed_and_all_side_effects_stay_disabled(self):
        with self.assertRaises(CanonicalError):
            build_room_graph(None)
        with self.assertRaises(CanonicalError):
            build_room_graph({'schema_version': 'untrusted'})
        safety = build_room_graph(self.source)['safety']
        self.assertTrue(safety['read_only'])
        self.assertTrue(safety['human_approval_required'])
        for flag in ('pms_writes', 'payments', 'kbs', 'guest_messages', 'live_ai_calls'):
            self.assertFalse(safety[flag])
