"""v0.3 safety regressions. Every record and identifier is fictional."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.experience_cli import main
from konaklamaflow.experience_engine import BLOCKER_CODES, SnapshotError, evaluate, validate, propose_room

ROOT = Path(__file__).resolve().parents[1]


def booking(bid='A', **changes):
    b = dict(id=bid, channel='direct', external_ref='EXT_' + bid, pms_ref='PMS_' + bid,
             arrival='2026-11-12', departure='2026-11-14', category='standard', persons=2,
             bed_request='none', status='confirmed', room_id='R1', identity_signal='staff_verified',
             payment_signal='ready', pms_registration='recorded_by_authorized_staff',
             requests=[], price_total='100.00', currency='TRY', arrival_state='arrived')
    b.update(changes)
    return b


def room(rid='R1', **changes):
    r = dict(id=rid, category='standard', capacity=2, bed='double', housekeeping='inspected', floor=1, amenities=[])
    r.update(changes)
    return r


def snapshot():
    return dict(schema_version='0.3', property_id='SYNTHETIC_HOTEL', as_of='2026-11-12', at_time='14:01',
                rooms=[room()], reservations=[booking()], channel_events=[], tasks=[])


def row(source, bid='A'):
    return next(r for r in evaluate(source)['arrivals'] if r['id'] == bid)


class SuiteSafetyTests(unittest.TestCase):
    def test_legacy_proposal_helper_respects_physical_holds_like_final_evaluation(self):
        for status in ('cancelled', 'no_show', 'checked_out'):
            for departure in ('2026-11-11', '2026-11-14'):
                s = snapshot()
                s['reservations'] = [booking('NEW', room_id=None), booking('OLD', status=status,
                    arrival='2026-11-09', departure=departure, arrival_state='checked_in')]
                with self.subTest(status=status, departure=departure):
                    self.assertIsNone(row(s, 'NEW')['suggested_room'])
                    self.assertIsNone(propose_room(s['reservations'][0], s['rooms'], s['reservations']))

    def test_missing_arrival_signal_never_infers_arrival(self):
        s = snapshot(); del s['reservations'][0]['arrival_state']
        self.assertIn('GUEST_NOT_ARRIVED', row(s)['blockers'])
        self.assertIn('guest_not_arrived', row(s)['core_reasons'])
        self.assertEqual(evaluate(s)['summary']['review_ready'], 0)

    def test_future_past_and_early_arrivals_remain_blocked(self):
        for arrival, clock, reason in [('2026-11-13','14:01','ARRIVAL_NOT_TODAY'), ('2026-11-11','14:01','ARRIVAL_NOT_TODAY'), ('2026-11-12','10:00','BEFORE_CHECKIN_TIME')]:
            s = snapshot(); s['reservations'][0]['arrival'] = arrival; s['at_time'] = clock
            with self.subTest(arrival=arrival,clock=clock):
                self.assertIn(reason, row(s)['blockers'])
                self.assertEqual(row(s)['status'], 'blocked')

    def test_pending_holds_block_proposals_and_both_assigned_conflicts(self):
        s = snapshot(); s['reservations'].append(booking('HOLD', status='pending'))
        self.assertIn('ROOM_CONFLICT', row(s)['blockers'])
        self.assertIn('ROOM_CONFLICT', row(s,'HOLD')['blockers'])
        s['reservations'][0]['room_id'] = None
        self.assertIsNone(row(s)['suggested_room'])

    def test_planned_proposals_never_reuse_a_room_on_overlapping_stays(self):
        s = snapshot(); s['rooms'].append(room('R2'))
        s['reservations'] = [booking('A',room_id=None),booking('B',room_id=None),booking('C',room_id=None)]
        report = evaluate(s); proposed = [r['suggested_room'] for r in report['arrivals'] if r['suggested_room']]
        self.assertEqual(len(proposed),2)
        self.assertEqual(set(proposed),{'R1','R2'})
        self.assertTrue(all(r['status']=='blocked' for r in report['arrivals']))

    def test_bed_request_flags_are_real_proposal_constraints(self):
        s = snapshot(); s['rooms'].append(room('R2',bed='twin'))
        s['reservations'][0].update(room_id=None,requests=['twin'])
        self.assertEqual(row(s)['suggested_room'],'R2')
        s['reservations'][0]['requests'] = ['twin','double']
        self.assertIsNone(row(s)['suggested_room'])
        self.assertIn('CONFLICTING_BED_REQUEST',row(s)['blockers'])
        s['reservations'][0].update(room_id='R1',requests=['twin'])
        self.assertIn('ROOM_INCOMPATIBLE',row(s)['blockers'])

    def test_capacity_single_bed_and_required_amenities_are_not_silently_dropped(self):
        for changes in ({'capacity':1},{'bed':'single'}):
            s = snapshot(); s['rooms'][0].update(changes); s['reservations'][0]['bed_request']='double'
            self.assertIn('ROOM_INCOMPATIBLE',row(s)['blockers'])
            s['reservations'][0]['room_id']=None
            self.assertIsNone(row(s)['suggested_room'])
        s=snapshot();s['rooms'][0]['bed']='single'
        self.assertIn('ROOM_INCOMPATIBLE',row(s)['blockers'])
        s['reservations'][0]['persons']=1
        self.assertEqual(row(s)['status'],'review_ready')
        s=snapshot();s['reservations'][0]['requests']=['accessible']
        self.assertIn('REQUEST_AMENITY_UNAVAILABLE',row(s)['blockers'])
        s['reservations'][0]['room_id']=None
        self.assertIsNone(row(s)['suggested_room'])

    def test_special_requests_require_staff_review_even_if_room_has_amenity(self):
        s=snapshot();s['rooms'][0]['amenities']=['quiet'];s['reservations'][0]['requests']=['quiet']
        self.assertIn('SPECIAL_REQUEST_REVIEW',row(s)['blockers'])
        self.assertFalse(row(s)['status']=='review_ready')

    def test_scheduled_maintenance_spans_entire_stay_and_uses_exclusive_end(self):
        s=snapshot();s['rooms'][0]['maintenance']=[{'start':'2026-11-13','end':'2026-11-15'}]
        self.assertIn('ROOM_INCOMPATIBLE',row(s)['blockers'])
        self.assertFalse(row(s)['checklist']['room_compatible'])
        s['reservations'][0]['room_id']=None
        self.assertIsNone(row(s)['suggested_room'])
        s['rooms'][0]['maintenance']=[{'start':'2026-11-10','end':'2026-11-12'}]
        self.assertEqual(row(s)['suggested_room'],'R1')

    def test_cancelled_no_show_or_overdue_physical_occupant_cannot_release_room(self):
        for status in ('cancelled','no_show','checked_out','in_house'):
            s=snapshot();s['reservations'].append(booking('OLD',status=status,arrival='2026-11-09',departure='2026-11-11',arrival_state='checked_in'))
            with self.subTest(status=status):
                self.assertIn('DEPARTURE_NOT_VERIFIED',row(s)['blockers'])
                self.assertIn('ALREADY_IN_HOUSE',row(s,'OLD')['blockers'])
                s['reservations'][0]['room_id']=None
                self.assertIsNone(row(s)['suggested_room'])

    def test_no_show_room_is_not_proposed_without_staff_release(self):
        s = snapshot()
        s['reservations'] = [booking('NEW', room_id=None),
                             booking('OLD', status='no_show', arrival_state='expected')]
        report = evaluate(s)
        self.assertIsNone(row(s, 'NEW')['suggested_room'])
        self.assertIn('NO_SHOW_RELEASE_REVIEW', row(s, 'OLD')['blockers'])
        plan = next(room for room in report['room_plan'] if room['id'] == 'R1')
        self.assertEqual(plan['availability'], 'BLOCKED_FOR_REVIEW')
        self.assertIn('NO_SHOW_HOLD', plan['reason_codes'])
        self.assertNotIn('REQUIRES_LIVE_REVALIDATION', plan['availability'])

    def test_missing_pms_registration_is_not_operational_approval_or_kbs(self):
        s = snapshot()
        del s['reservations'][0]['pms_registration']
        blocked = row(s)
        self.assertIn('PMS_REGISTRATION_NOT_CONFIRMED', blocked['blockers'])
        self.assertEqual(blocked['status'], 'blocked')
        self.assertFalse(evaluate(s)['approval_policy']['kbs'])
        self.assertFalse(evaluate(s)['approval_policy']['pms_writes'])
        s['reservations'][0]['pms_registration'] = 'recorded_by_authorized_staff'
        self.assertEqual(row(s)['status'], 'review_ready')

    def test_same_day_departure_requires_release_evidence_for_new_proposal(self):
        s=snapshot();s['reservations'].append(booking('OLD',arrival='2026-11-10',departure='2026-11-12',arrival_state='expected'))
        self.assertIn('DEPARTURE_NOT_VERIFIED',row(s)['blockers'])
        s['reservations'][0]['room_id']=None
        self.assertIsNone(row(s)['suggested_room'])
        s['reservations'][1]['arrival_state']='checked_out'
        self.assertEqual(row(s)['suggested_room'],'R1')

    def test_duplicate_channel_or_pms_keys_do_not_get_room_proposals(self):
        for key in ('external_ref','pms_ref'):
            s=snapshot();s['rooms'].append(room('R2'))
            s['reservations']=[booking('A',room_id=None),booking('B',room_id=None)]
            s['reservations'][1][key]=s['reservations'][0][key]
            report=evaluate(s)
            with self.subTest(key=key):
                self.assertTrue(all(r['suggested_room'] is None for r in report['arrivals']))
                expected='DUPLICATE_CHANNEL_REF' if key=='external_ref' else 'DUPLICATE_PMS_REF'
                self.assertTrue(all(expected in r['blockers'] for r in report['arrivals']))

    def test_ota_pms_reference_alone_does_not_prove_mapping(self):
        for channel in ('booking','expedia','trip','ctrip','hotelbeds','channel_manager'):
            s=snapshot();s['reservations'][0]['channel']=channel
            with self.subTest(channel=channel):
                self.assertIn('UNMAPPED_PMS',row(s)['blockers'])
                s['channel_events']=[dict(id='EVENT',channel=channel,external_ref='EXT_A',status='mapped',reservation_id='A')]
                self.assertEqual(row(s)['status'],'review_ready')

    def test_mismatched_cancelled_and_review_channel_events_block_affected_booking(self):
        for status,reference in [('mapped','OTHER'),('cancelled','EXT_A'),('needs_review','EXT_A')]:
            s=snapshot();s['reservations'][0]['channel']='booking'
            s['channel_events']=[dict(id='EVENT',channel='booking',external_ref=reference,status=status,reservation_id='A')]
            r=evaluate(s)
            with self.subTest(status=status):
                self.assertEqual(r['summary']['review_ready'],0)
                self.assertEqual(r['summary']['pending_channel_events'],1)
        s['channel_events'][0]['reservation_id']='UNKNOWN'
        self.assertEqual(evaluate(s)['unmatched_channel_events'],['EVENT'])

    def test_ctrip_trip_alias_deduplicates_only_with_matching_source_key(self):
        s=snapshot();s['reservations']=[booking('A',channel='trip'),booking('B',channel='ctrip',external_ref='EXT_A',room_id=None)]
        self.assertTrue(all('DUPLICATE_CHANNEL_REF' in r['blockers'] for r in evaluate(s)['arrivals']))
        s['reservations'][1]['channel']='expedia'
        self.assertTrue(all('DUPLICATE_CHANNEL_REF' not in r['blockers'] for r in evaluate(s)['arrivals']))

    def test_open_housekeeping_or_technical_task_blocks_readiness_and_proposal(self):
        for kind in ('maintenance','housekeeping'):
            s=snapshot();s['tasks']=[dict(id='TASK',kind=kind,room_id='R1',reservation_id=None,status='open',priority='high')]
            with self.subTest(kind=kind):
                self.assertEqual(row(s)['status'],'blocked')
                s['reservations'][0]['room_id']=None
                self.assertIsNone(row(s)['suggested_room'])
                s['tasks'][0]['status']='done'
                self.assertEqual(row(s)['suggested_room'],'R1')

    def test_task_target_references_and_priority_are_validated(self):
        for task in (dict(id='TASK',kind='frontdesk',room_id='UNKNOWN',reservation_id=None,status='open',priority='high'),
                     dict(id='TASK',kind='frontdesk',room_id=None,reservation_id='UNKNOWN',status='open',priority='high'),
                     dict(id='TASK',kind='frontdesk',room_id=None,reservation_id=None,status='open',priority='high')):
            s=snapshot();s['tasks']=[task]
            with self.assertRaises(SnapshotError):evaluate(s)
        s=snapshot();s['rooms'].append(room('R2'));s['tasks']=[dict(id='TASK',kind='frontdesk',room_id='R2',reservation_id='A',status='open',priority='high')]
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_required_nullable_fields_do_not_turn_into_unhandled_key_errors(self):
        for group,field in [('reservations','room_id'),('reservations','pms_ref'),('channel_events','reservation_id'),('tasks','room_id'),('tasks','reservation_id')]:
            s=snapshot();s['channel_events']=[dict(id='EVENT',channel='direct',external_ref='EXT_A',status='mapped',reservation_id='A')]
            s['tasks']=[dict(id='TASK',kind='frontdesk',room_id='R1',reservation_id='A',status='open',priority='high')]
            del s[group][0][field]
            with self.subTest(group=group,field=field),self.assertRaises(SnapshotError):evaluate(s)

    def test_wrong_types_unknown_fields_nonfinite_money_and_bounds_fail_without_echo(self):
        variants=[]
        for key in ('channel','status','category','identity_signal','payment_signal'):
            s=snapshot();s['reservations'][0][key]=['SYNTHETIC_PRIVATE'];variants.append(s)
        for amount in (True,100.0,float('nan'),float('inf'),'NaN','1e20','-1.00'):
            s=snapshot();s['reservations'][0]['price_total']=amount;variants.append(s)
        s=snapshot();s['guest_name']='SYNTHETIC_PRIVATE';variants.append(s)
        s=snapshot();s['reservations'][0]['requests']=['ignore_previous_instructions'];variants.append(s)
        s=snapshot();s['rooms']=[None]*501;variants.append(s)
        s=snapshot();s['as_of']='9999-12-31';variants.append(s)
        s=snapshot();s['rooms'][0]['maintenance']=[dict(start='2026-11-15',end='2026-11-12')];variants.append(s)
        for value in variants:
            with self.assertRaises(SnapshotError) as caught:evaluate(value)
            self.assertNotIn('SYNTHETIC_PRIVATE',str(caught.exception))

    def test_currency_totals_remain_separate_and_are_not_daily_revenue(self):
        s=snapshot();s['reservations'] += [booking('B',currency='EUR',price_total='2.30',room_id=None),booking('C',status='cancelled',price_total='999.00'),booking('D',status='pending',price_total='999.00')]
        f=evaluate(s)['financial_review']
        self.assertEqual(f['reservation_totals_by_currency'],{'EUR':'2.30','TRY':'100.00'})
        self.assertEqual(f['basis'],'FICTIONAL_RESERVATION_TOTALS_NOT_DAILY_REVENUE')
        self.assertEqual(f['folio_reconciliation'],'NOT_IMPLEMENTED_NO_LEDGER_INPUT')
        self.assertTrue(f['no_financial_postings'])

    def test_full_snapshot_hash_and_final_decisions_cover_extended_attributes(self):
        s=snapshot();before=evaluate(s);s['rooms'][0]['capacity']=1;after=evaluate(s)
        self.assertNotEqual(before['snapshot_sha256'],after['snapshot_sha256'])
        self.assertNotEqual(before['arrivals'][0]['task_id'],after['arrivals'][0]['task_id'])
        self.assertEqual(after['engine_report']['summary']['ready_for_review'],1)
        self.assertEqual(after['summary']['review_ready'],0)
        self.assertTrue(set(after['arrivals'][0]['blockers'])<=BLOCKER_CODES)

    def test_generated_fixture_matches_engine_and_input_is_unchanged(self):
        s=json.loads((ROOT/'examples/fictional-hotel.json').read_text())
        previous=copy.deepcopy(s);report=evaluate(s)
        self.assertEqual(s,previous)
        self.assertEqual(report,json.loads((ROOT/'examples/operations-evaluation.json').read_text()))
        self.assertEqual(report,evaluate(copy.deepcopy(s)))


class SuiteCliSafetyTests(unittest.TestCase):
    def test_invalid_inputs_keep_existing_output_and_never_echo_content_or_path(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'SYNTHETIC_PRIVATE.json';target=Path(directory)/'report.json';target.write_text('previous')
            for raw in (b'\xff',b'SYNTHETIC_PRIVATE',b'{"schema_version":"0.3","schema_version":"0.2"}',b'['*1100,b' '*2_000_001):
                source.write_bytes(raw);error=io.StringIO()
                with contextlib.redirect_stderr(error):self.assertEqual(main([str(source),str(target)]),2)
                self.assertNotIn('SYNTHETIC_PRIVATE',error.getvalue());self.assertEqual(target.read_text(),'previous')

    def test_valid_output_matches_engine_and_has_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'input.json';target=Path(directory)/'report.json';source.write_text(json.dumps(snapshot()))
            self.assertEqual(main([str(source),str(source)]),2)
            self.assertIn('"reservations"', source.read_text())
            self.assertEqual(main([str(source),str(target)]),0)
            self.assertEqual(json.loads(target.read_text()),evaluate(snapshot()))
            if os.name!='nt':self.assertEqual(target.stat().st_mode&0o077,0)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()),['input.json','report.json'])


class SuiteRoomPlanTests(unittest.TestCase):
    def test_room_plan_distinguishes_current_holds_future_holds_and_cancellations(self):
        s=snapshot();s['reservations']=[booking('FUTURE',arrival='2026-11-13'),booking('CANCELLED',status='cancelled')]
        plan=evaluate(s)['room_plan'][0]
        self.assertEqual(plan['held_reservation_ids'],[])
        self.assertEqual(plan['reservation_ids_all_holds'],['FUTURE'])
        self.assertEqual(plan['availability'],'REQUIRES_LIVE_REVALIDATION')
        s['reservations'].append(booking('PENDING',status='pending'))
        self.assertEqual(evaluate(s)['room_plan'][0]['held_reservation_ids'],['PENDING'])

    def test_room_plan_keeps_cancelled_physical_occupant_and_unreleased_departure(self):
        s=snapshot();s['reservations']=[booking('OCCUPANT',status='cancelled',arrival='2026-11-09',departure='2026-11-11',arrival_state='checked_in')]
        self.assertEqual(evaluate(s)['room_plan'][0]['held_reservation_ids'],['OCCUPANT'])
        s['reservations']=[booking('DEPARTURE',arrival='2026-11-10',departure='2026-11-12',arrival_state='expected')]
        self.assertEqual(evaluate(s)['room_plan'][0]['held_reservation_ids'],['DEPARTURE'])
        s['reservations'][0]['arrival_state']='checked_out'
        self.assertEqual(evaluate(s)['room_plan'][0]['held_reservation_ids'],[])

    def test_ordinary_cancelled_departure_does_not_block_a_new_room_proposal(self):
        s=snapshot();s['reservations']=[booking('A',room_id=None),booking('CANCELLED',status='cancelled',arrival='2026-11-10',departure='2026-11-12',arrival_state='expected')]
        self.assertEqual(row(s)['suggested_room'],'R1')
        self.assertEqual(evaluate(s)['room_plan'][0]['held_reservation_ids'],[])

    def test_room_plan_preserves_maintenance_and_housekeeping_blocks(self):
        s=snapshot();s['reservations']=[];s['rooms'][0]['maintenance']=[dict(start='2026-11-12',end='2026-11-13')]
        plan=evaluate(s)['room_plan'][0]
        self.assertEqual(plan['availability'],'BLOCKED_FOR_REVIEW')
        self.assertIn('OUT_OF_SERVICE_OR_MAINTENANCE',plan['reason_codes'])
