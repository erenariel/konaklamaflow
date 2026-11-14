import copy
import json
from pathlib import Path
import unittest
from konaklamaflow.core import InputError, review
from konaklamaflow.operations import plan_operations
from konaklamaflow.agent_protocol import make_handoff, verify_suggestion, ProtocolError

ROOT = Path(__file__).resolve().parents[1]
DEMO = json.loads((ROOT / 'examples' / 'operations-demo.json').read_text())


def run(d=None, day='2026-11-12', at='14:01'):
    return plan_operations(copy.deepcopy(DEMO if d is None else d), day, at)


class OperationsTests(unittest.TestCase):
    def test_demo_readiness_counts(self):
        report = run()
        self.assertEqual(report['mode'], 'DRY_RUN_ONLY')
        self.assertEqual(report['summary']['ready_for_review'], 0)
        self.assertEqual(report['summary']['blocked'], 4)
        pending = next(t for t in report['tasks'] if t['reservation_ref'] == 'DEMO_A01')
        self.assertEqual(pending['state'], 'BLOCKED_FOR_HUMAN_REVIEW')
        self.assertIn('pms_registration_not_confirmed', pending['reasons'])
        self.assertFalse(pending['checklist']['registration_confirmed_by_authorized_system'])
        self.assertEqual(pending['required_action'], 'MANUAL_APPROVAL_IN_AUTHORIZED_PMS_ONLY')
        self.assertIn('KBS', report['disclaimer'])

    def test_dirty_room_blocks(self):
        self.assertIn('room_not_clean', next(t for t in run()['tasks'] if t['reservation_ref']=='DEMO_A03')['reasons'])

    def test_unassigned_blocks(self):
        self.assertIn('room_unassigned', next(t for t in run()['tasks'] if t['reservation_ref']=='DEMO_A04')['reasons'])

    def test_before_checkin_time_blocks(self):
        self.assertIn('before_checkin_time', run(at='10:00')['tasks'][0]['reasons'])

    def test_early_authorization_only_exempts_time(self):
        d=copy.deepcopy(DEMO); d['arrival_checks'][0]['early_checkin_authorized']=True
        t=next(t for t in run(d,at='10:00')['tasks'] if t['reservation_ref']=='DEMO_A01')
        self.assertNotIn('before_checkin_time',t['reasons'])

    def test_identity_not_authorized_blocks(self):
        d=copy.deepcopy(DEMO);d['arrival_checks'][0]['identity_status']='pending'
        self.assertIn('identity_needs_authorized_verification',run(d)['tasks'][0]['reasons'])

    def test_payment_review_blocks(self):
        d=copy.deepcopy(DEMO);d['arrival_checks'][0]['payment_review']='review'
        self.assertIn('payment_review_needed',run(d)['tasks'][0]['reasons'])

    def test_unknown_personal_data_rejected_without_echo(self):
        d=copy.deepcopy(DEMO);d['arrival_checks'][0]['guest_email']='someone@example.com'
        with self.assertRaises(InputError) as caught: run(d)
        self.assertNotIn('someone@example.com',str(caught.exception))

    def test_duplicate_room_status_rejected(self):
        d=copy.deepcopy(DEMO);d['room_operations'].append(copy.deepcopy(d['room_operations'][0]))
        with self.assertRaises(InputError): run(d)

    def test_unknown_status_rejected(self):
        d=copy.deepcopy(DEMO);d['arrival_checks'][0]['identity_status']='verified_by_ai'
        with self.assertRaises(InputError): run(d)

    def test_unknown_reservation_ref_rejected(self):
        d=copy.deepcopy(DEMO);d['arrival_checks'][0]['ref']='MISSING'
        with self.assertRaises(InputError): run(d)

    def test_stable_hash_when_dict_key_order_changes(self):
        x=run(); d=copy.deepcopy(DEMO); d=dict(reversed(list(d.items())))
        self.assertEqual(x['snapshot_sha256'],run(d)['snapshot_sha256'])

    def test_no_guest_data_in_output(self):
        out=json.dumps(run())
        self.assertNotIn('guest_name',out)
        self.assertNotIn('passport',out.lower())

    def test_hand_off_expires_and_blocks_write(self):
        rep=run();h=make_handoff(rep,'2026-11-12T11:00:00Z')
        self.assertEqual(h['mode'],'NO_EXECUTION_READ_ONLY')
        task=h['tasks'][0]; p={'task_id':task['task_id'],'intent':'SUGGEST_RECEPTION_REVIEW','snapshot_sha256':h['snapshot_sha256'],'report_sha256':h['report_sha256']}
        self.assertTrue(verify_suggestion(h,p,'2026-11-12T11:03:00Z',current_review=rep))
        with self.assertRaises(ProtocolError): verify_suggestion(h,p,'2026-11-12T11:05:00Z',current_review=rep)
        p['intent']='write_pms'
        with self.assertRaises(ProtocolError):verify_suggestion(h,p,'2026-11-12T11:03:00Z',current_review=rep)

    def test_stale_source_checksum_blocked(self):
        h=make_handoff(run(),'2026-11-12T11:00:00+00:00')
        p={'task_id':h['tasks'][0]['task_id'],'intent':'SUGGEST_RECEPTION_REVIEW','snapshot_sha256':'0'*64,'report_sha256':h['report_sha256']}
        with self.assertRaises(ProtocolError):verify_suggestion(h,p,'2026-11-12T11:02:00Z',current_review=run())

    def test_duplicated_reservation_blocks_all_instances(self):
        d=copy.deepcopy(DEMO);d['reservations'].append(copy.deepcopy(d['reservations'][0]))
        items=[t for t in run(d)['tasks'] if t['reservation_ref']=='DEMO_A01']
        self.assertEqual(len(items),2)
        self.assertTrue(all('duplicate_reservation' in t['reasons'] for t in items))
        self.assertEqual(len({t['task_id'] for t in items}), 2)
        make_handoff(run(d), '2026-11-12T11:00:00Z')

    def test_never_performs_checkin(self):
        out=run()
        self.assertTrue(all(t['state'] != 'CHECKED_IN' for t in out['tasks']))

    def test_twin_scarcity_heuristic(self):
        inp={'rooms':[{'id':'101','category':'standard','beds':'twin'}, {'id':'102','category':'standard','beds':'double'}],
             'reservations':[{'ref':'A','source':'S','status':'confirmed','checkin':'2026-11-13','checkout':'2026-11-15','category':'standard'},
                             {'ref':'B','source':'S','status':'confirmed','checkin':'2026-11-13','checkout':'2026-11-15','category':'standard','twin_requested':True}]}
        result=review(inp,'2026-11-12')
        assignments={a['reservation_ref']:a['room_id'] for a in result['room_proposals']}
        self.assertEqual(assignments,{'B':'101','A':'102'})

if __name__ == '__main__':unittest.main()
