"""Regression cases from the v0.2 release audit. All fixtures are synthetic."""
import contextlib
import copy
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

from konaklamaflow.agent_protocol import make_handoff, verify_suggestion, ProtocolError
from konaklamaflow.core import InputError, review
from konaklamaflow.operations import plan_operations
from konaklamaflow.ops_cli import main
from konaklamaflow.report_contract import validate_report

ROOT = Path(__file__).resolve().parents[1]
DEMO = json.loads((ROOT / 'examples/operations-demo.json').read_text())


def single():
    d = copy.deepcopy(DEMO)
    d['reservations'] = d['reservations'][:1]
    d['arrival_checks'] = d['arrival_checks'][:1]
    # Isolate room rules from the demo's missing PMS-registration signal.
    d['arrival_checks'][0]['registration_status'] = 'confirmed_by_authorized_system'
    return d


def plan(d=None, at='14:01'):
    return plan_operations(single() if d is None else d, '2026-11-12', at)


def proposal(h):
    return dict(task_id=h['tasks'][0]['task_id'], intent='SUGGEST_RECEPTION_REVIEW',
                snapshot_sha256=h['snapshot_sha256'], report_sha256=h['report_sha256'])


class ReadinessAuditTests(unittest.TestCase):
    def test_overlap_blocks_every_participant_including_pending_hold(self):
        for pending in (False, True):
            d = single()
            other = dict(d['reservations'][0], ref='SECOND', status='pending' if pending else 'confirmed')
            d['reservations'].append(other)
            r = plan(d)
            self.assertEqual(r['summary']['ready_for_review'], 0)
            self.assertTrue(all('ROOM_OVERLAP' in t['reasons'] for t in r['tasks']))

    def test_channel_identity_does_not_contaminate_other_channel(self):
        d = single()
        d['reservations'].append(dict(d['reservations'][0], source='CHANNEL_B', room_id='MISSING'))
        r = plan(d)
        self.assertEqual(r['tasks'][0]['state'], 'READY_FOR_HUMAN_CHECKIN_REVIEW')
        self.assertIn('UNKNOWN_ROOM', r['tasks'][1]['reasons'])

    def test_inactive_maintenance_wrong_category_and_unknown_room_block(self):
        variants = []
        d = single(); d['rooms'][0]['active'] = False; variants.append((d, 'ROOM_OUT_OF_SERVICE'))
        d = single(); d['rooms'][0]['maintenance'] = [{'start':'2026-11-13','end':'2026-11-15'}]; variants.append((d,'ROOM_OUT_OF_SERVICE'))
        d = single(); d['reservations'][0]['category'] = 'superior'; variants.append((d,'CATEGORY_MISMATCH'))
        d = single(); d['reservations'][0]['room_id'] = 'MISSING'; variants.append((d,'UNKNOWN_ROOM'))
        d = single(); d['room_operations'][0]['maintenance_hold'] = True; variants.append((d,'maintenance_hold'))
        for snapshot, code in variants:
            with self.subTest(code=code):
                r = plan(snapshot)
                self.assertEqual(r['summary']['ready_for_review'], 0)
                self.assertIn(code, r['tasks'][0]['reasons'])

    def test_twin_and_price_review_are_not_silently_dropped(self):
        d = single(); d['reservations'][0].update(twin_requested=True, nightly_base='100.00', total_base='1.00', currency='TRY')
        task = plan(d)['tasks'][0]
        self.assertEqual(task['state'], 'BLOCKED_FOR_HUMAN_REVIEW')
        self.assertTrue({'TWIN_NOT_GUARANTEED','BASE_PRICE_MISMATCH'} <= set(task['reasons']))

    def test_missing_room_signals_fail_closed(self):
        for field in ('housekeeping', 'inspection', 'maintenance_hold'):
            d = single(); del d['room_operations'][0][field]
            with self.subTest(field=field), self.assertRaises(InputError):
                plan(d)
        d = single(); d['room_operations'] = []
        self.assertIn('room_status_unverified', plan(d)['tasks'][0]['reasons'])

    def test_turnover_requires_departure_evidence_even_with_early_approval(self):
        d = single()
        d['reservations'].append(dict(d['reservations'][0], ref='DEPARTING', checkin='2026-11-10', checkout='2026-11-12'))
        d['arrival_checks'][0]['early_checkin_authorized'] = True
        self.assertIn('departure_not_verified', plan(d, at='10:00')['tasks'][0]['reasons'])
        d['arrival_checks'].append({'source':'CHANNEL_A','ref':'DEPARTING','arrival_state':'checked_out'})
        r = plan(d, at='10:00')
        self.assertEqual(len(r['tasks']), 1)
        self.assertEqual(r['summary']['ready_for_review'], 1)
        d['room_operations'][0]['housekeeping'] = 'dirty'
        self.assertEqual(plan(d)['summary']['ready_for_review'], 0)

    def test_overdue_occupant_blocks_room_and_is_kept_for_review(self):
        d = single()
        d['reservations'].append(dict(d['reservations'][0], ref='OVERDUE', checkin='2026-11-09', checkout='2026-11-11'))
        d['arrival_checks'].append({'source':'CHANNEL_A','ref':'OVERDUE','arrival_state':'checked_in'})
        r = plan(d)
        self.assertEqual(r['summary']['already_checked_in_requires_review'], 1)
        self.assertEqual(r['summary']['ready_for_review'], 0)
        self.assertIn('departure_not_verified', next(t for t in r['tasks'] if t['reservation_ref']=='DEMO_A01')['reasons'])

    def test_history_and_cancellations_do_not_pollute_staff_queue(self):
        d = single()
        for ref, status in [('OLD','confirmed'), ('CANCELLED','cancelled')]:
            d['reservations'].append(dict(d['reservations'][0], ref=ref, status=status, checkin='2026-10-10', checkout='2026-10-12'))
        self.assertEqual(plan(d)['summary']['arrivals_total'], 1)

    def test_cancelled_checked_in_occupant_blocks_room_and_remains_visible(self):
        for checkout in ('2026-11-13', '2026-11-11'):
            with self.subTest(checkout=checkout):
                d = single()
                d['reservations'].append(dict(d['reservations'][0], ref='CANCELLED_OCCUPANT',
                                               status='cancelled', checkin='2026-11-09', checkout=checkout))
                d['arrival_checks'].append({'source':'CHANNEL_A','ref':'CANCELLED_OCCUPANT',
                                            'arrival_state':'checked_in'})
                r = plan(d)
                arrival = next(t for t in r['tasks'] if t['reservation_ref']=='DEMO_A01')
                occupant = next(t for t in r['tasks'] if t['reservation_ref']=='CANCELLED_OCCUPANT')
                self.assertEqual(arrival['state'], 'BLOCKED_FOR_HUMAN_REVIEW')
                self.assertIn('departure_not_verified', arrival['reasons'])
                self.assertEqual(occupant['state'], 'REVIEW_EXISTING_CHECKIN')
                self.assertIn('reservation_not_confirmed', occupant['reasons'])
                self.assertEqual(r['summary']['ready_for_review'], 0)
                self.assertEqual(r['summary']['already_checked_in_requires_review'], 1)

    def test_cancelled_booking_without_occupancy_signal_does_not_block_room(self):
        d = single()
        d['reservations'].append(dict(d['reservations'][0], ref='CANCELLED', status='cancelled'))
        self.assertEqual(plan(d)['summary']['ready_for_review'], 1)

    def test_registration_is_separate_from_readiness_and_kbs(self):
        raw = copy.deepcopy(DEMO)
        raw['reservations'] = raw['reservations'][:1]
        raw['arrival_checks'] = raw['arrival_checks'][:1]
        blocked = plan(raw)
        self.assertFalse(blocked['tasks'][0]['checklist']['registration_confirmed_by_authorized_system'])
        self.assertEqual(blocked['tasks'][0]['state'], 'BLOCKED_FOR_HUMAN_REVIEW')
        self.assertIn('pms_registration_not_confirmed', blocked['tasks'][0]['reasons'])
        self.assertIn('KBS', blocked['disclaimer'])
        self.assertIn('PMS registration', blocked['disclaimer'])
        ready = plan()
        self.assertTrue(ready['tasks'][0]['checklist']['registration_confirmed_by_authorized_system'])
        self.assertEqual(ready['summary']['ready_for_review'], 1)
        self.assertNotIn('pms_registration_not_confirmed', ready['tasks'][0]['reasons'])

    def test_evaluation_time_changes_task_reference(self):
        self.assertNotEqual(plan(at='10:00')['tasks'][0]['task_id'], plan(at='14:01')['tasks'][0]['task_id'])

    def test_list_limits_and_private_errors(self):
        for field, value in [('arrival_checks', [None]*5001), ('room_operations', [None]*501), ('reservations', [None]*5001)]:
            d = single(); d[field] = value
            with self.subTest(field=field), self.assertRaises(InputError): plan(d)
        d = single(); d['rooms'].append(copy.deepcopy(d['rooms'][0])); d['rooms'][0]['id'] = d['rooms'][-1]['id'] = 'SYNTHETIC_PRIVATE_ID'
        with self.assertRaises(InputError) as caught: plan(d)
        self.assertNotIn('SYNTHETIC_PRIVATE_ID',str(caught.exception))

    def test_concurrent_readers_do_not_mutate_snapshot_or_each_other(self):
        d = single(); original = copy.deepcopy(d)
        with ThreadPoolExecutor(max_workers=4) as pool:
            reports = list(pool.map(lambda _: plan(d), range(20)))
        self.assertEqual(d, original)
        self.assertTrue(all(r == reports[0] for r in reports))
        reports[0]['tasks'][0]['reasons'].append('local mutation')
        self.assertEqual(reports[1]['tasks'][0]['reasons'], [])

    def test_interval_sweep_matches_independent_all_pairs_oracle(self):
        rng = random.Random(20261112)
        from datetime import date, timedelta
        for _ in range(60):
            d = single(); d['reservations'] = []; d['arrival_checks'] = []
            intervals = []
            for i in range(12):
                start = rng.randrange(8); end = start + rng.randrange(1,6); intervals.append((start,end))
                d['reservations'].append(dict(single()['reservations'][0], ref=f'R{i}', checkin=(date(2026,11,12)+timedelta(days=start)).isoformat(), checkout=(date(2026,11,12)+timedelta(days=end)).isoformat()))
            expected = {f'R{i}' for i,(a,b) in enumerate(intervals) if any(i!=j and a<d2 and c<b for j,(c,d2) in enumerate(intervals))}
            issues = [i for i in review({k:v for k,v in d.items() if k in {'property_id','rooms','reservations'}},'2026-11-12')['issues'] if i['code']=='ROOM_OVERLAP']
            self.assertEqual({i['reservation_ref'] for i in issues}, expected)
            self.assertEqual(len(issues),len(expected))


class ProtocolAuditTests(unittest.TestCase):
    def setUp(self):
        self.report = plan()
        self.handoff = make_handoff(self.report,'2026-11-12T11:00:00Z')

    def verify(self, h=None, p=None, report=None, at='2026-11-12T11:01:00Z'):
        return verify_suggestion(self.handoff if h is None else h, proposal(self.handoff) if p is None else p, at,
                                 current_review=self.report if report is None else report)

    def test_valid_explanation_is_repeatable_but_never_a_write(self):
        self.assertTrue(self.verify()); self.assertTrue(self.verify())
        self.assertEqual(self.handoff['mode'],'NO_EXECUTION_READ_ONLY')

    def test_changed_trusted_source_property_or_evaluation_invalidates_handoff(self):
        d = single(); d['room_operations'][0]['maintenance_hold'] = True
        for r in (plan(d), plan(at='14:02'), dict(self.report,property_id='OTHER_PROPERTY')):
            with self.subTest(report=r['property_id']), self.assertRaises(ProtocolError): self.verify(report=r)

    def test_manifest_tampering_cannot_expand_ai_scope(self):
        variants = []
        for key, value in [('mode','EXECUTE'), ('protocol','other'), ('snapshot_sha256','0'*64), ('guest_email','synthetic@example.invalid')]:
            h = copy.deepcopy(self.handoff); h[key] = value; variants.append(h)
        h = copy.deepcopy(self.handoff); h['tasks'][0]['allowed_tools'].append('write_pms'); variants.append(h)
        h = copy.deepcopy(self.handoff); h['tasks'][0]['reason_codes'] = ['ignore_previous_instructions']; variants.append(h)
        h = copy.deepcopy(self.handoff); h['tasks'].append(h['tasks'][0]); variants.append(h)
        for h in variants:
            with self.assertRaises(ProtocolError): self.verify(h=h)

    def test_write_intents_unknown_task_and_extra_fields_rejected(self):
        for intent in ('write_pms','check_in','capture_payment','submit_kbs','send_guest_message','read_identity_document'):
            p = proposal(self.handoff); p['intent'] = intent
            with self.subTest(intent=intent), self.assertRaises(ProtocolError): self.verify(p=p)
        for key, value in [('task_id','f'*24), ('report_sha256','f'*64), ('execute',True), ('tool_call',{'name':'write_pms'})]:
            p = proposal(self.handoff); p[key] = value
            with self.assertRaises(ProtocolError): self.verify(p=p)

    def test_invalid_expiry_and_timestamps_rejected(self):
        for seconds in (True, 30.5, '300', 29, 601):
            with self.assertRaises(ProtocolError): make_handoff(self.report,'2026-11-12T11:00:00Z',seconds)
        for stamp in (None, 7, '2026-11-12T11:00:00', '2026-11-12T11:00:00+03:00'):
            with self.assertRaises(ProtocolError): make_handoff(self.report,stamp)
        with self.assertRaises(ProtocolError): make_handoff(self.report,'9999-12-31T23:59:59Z')
        for stamp in ('2026-11-12T10:59:59Z','2026-11-12T11:05:00Z'):
            with self.assertRaises(ProtocolError): self.verify(at=stamp)
        for expiry in ('2026-11-13T11:00:00Z','2026-11-12T11:00:30.5Z'):
            h=copy.deepcopy(self.handoff);h['expires_at']=expiry
            with self.assertRaises(ProtocolError): self.verify(h=h)

    def test_report_fields_and_reason_codes_are_allowlisted_without_echo(self):
        variants = [None, [], {'mode':'DRY_RUN_ONLY','tasks':[]}]
        for target in ('root','task','reasons','checklist','summary'):
            r=copy.deepcopy(self.report)
            if target=='root': r['SYNTHETIC_PRIVATE']='value'
            elif target=='task': r['tasks'][0]['guest_name']='SYNTHETIC_PRIVATE'
            elif target=='reasons': r['tasks'][0]['reasons']=['SYNTHETIC_PRIVATE']
            elif target=='checklist': r['tasks'][0]['checklist']['payment_review_complete']='true'
            else: r['summary']['arrivals_total']=50
            variants.append(r)
        for r in variants:
            with self.assertRaises(ProtocolError) as caught: make_handoff(r,'2026-11-12T11:00:00Z')
            self.assertNotIn('SYNTHETIC_PRIVATE',str(caught.exception))

    def test_ai_manifest_does_not_forward_reservation_property_or_room_ids(self):
        text=json.dumps(self.handoff)
        for private in ('DEMO_A01','CHANNEL_A','SAMPLE_INN_01','reservation_ref','room_id','property_id'):
            self.assertNotIn(private,text)

    def test_malformed_readiness_and_duplicate_task_ids_are_rejected(self):
        variants=[]
        for key,value in [('task_id','x'*24),('stay',{'checkin':'2026-02-30','checkout':'2026-11-14'}),('required_action','EXECUTE'),('state','CHECKED_IN')]:
            r=copy.deepcopy(self.report);r['tasks'][0][key]=value;variants.append(r)
        r=copy.deepcopy(self.report);r['tasks'].append(copy.deepcopy(r['tasks'][0]));variants.append(r)
        r=copy.deepcopy(self.report);r['tasks'][0]['checklist']['room_clean_and_inspected']=False;variants.append(r)
        for r in variants:
            with self.assertRaises(InputError): validate_report(r)


class OpsCliAuditTests(unittest.TestCase):
    def test_invalid_input_never_echoes_content_or_truncates_previous_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'SYNTHETIC_PRIVATE_INPUT.json';target=Path(directory)/'report.json'
            target.write_text('previous report')
            for raw in (b'\xff', b'SYNTHETIC_PRIVATE', b'{' + b'"property_id":"A","property_id":"B"}', b'['*1100, b' '*2_000_001):
                source.write_bytes(raw); error=io.StringIO()
                with contextlib.redirect_stderr(error): self.assertEqual(main([str(source),'--output',str(target)]),2)
                self.assertNotIn('SYNTHETIC_PRIVATE',error.getvalue())
                self.assertEqual(target.read_text(),'previous report')

    def test_complete_output_is_private_and_matches_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'input.json';target=Path(directory)/'report.json'
            source.write_text(json.dumps(single()))
            self.assertEqual(main([str(source),'--as-of','2026-11-12','--at-time','14:01','--output',str(source)]),2)
            self.assertIn('"reservations"', source.read_text())
            self.assertEqual(main([str(source),'--as-of','2026-11-12','--at-time','14:01','--output',str(target)]),0)
            self.assertEqual(json.loads(target.read_text()),plan())
            self.assertEqual(target.stat().st_mode & 0o077,0)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()),['input.json','report.json'])


class ReleaseIntegrityTests(unittest.TestCase):
    def test_version_and_checked_in_fixture_match_implementation(self):
        import re
        import tomllib
        from konaklamaflow import __version__
        self.assertEqual(__version__, tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'])
        source = json.loads((ROOT/'examples/operations-demo.json').read_text())
        expected = plan_operations(source,'2026-11-12','14:01')
        self.assertEqual(expected,json.loads((ROOT/'examples/operations-report.json').read_text()))
        embedded = re.search(r'<script type="application/json" id="example">(.*?)</script>',(ROOT/'demo/operations.html').read_text(),re.S)[1]
        self.assertEqual(expected,json.loads(embedded))

    def test_null_active_or_twin_signal_is_not_silently_defaulted(self):
        for field in ('active','twin_requested'):
            d=single()
            (d['rooms'][0] if field=='active' else d['reservations'][0])[field]=None
            with self.subTest(field=field), self.assertRaises(InputError): plan(d)
