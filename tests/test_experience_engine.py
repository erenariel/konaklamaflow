import copy
import json
from pathlib import Path
import unittest
from konaklamaflow.experience_engine import evaluate, validate, SnapshotError, overlap, propose_room

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=json.loads((ROOT/'examples/fictional-hotel.json').read_text(encoding='utf-8'))

class TestOperations(unittest.TestCase):
    def example(self):return copy.deepcopy(FIXTURE)

    def test_synthetic_fixture_report(self):
        r=evaluate(self.example())
        self.assertEqual(r['summary']['reservations'],12)
        self.assertEqual(r['summary']['blocked'],10)
        self.assertEqual(r['summary']['review_ready'],2)
        self.assertEqual(r['mode'],'DRY_RUN_ONLY')
        self.assertFalse(r['approval_policy']['pms_writes'])

    def test_fingerprint_deterministic(self):
        self.assertEqual(evaluate(self.example()),evaluate(self.example()))

    def test_input_not_modified(self):
        s=self.example();original=copy.deepcopy(s);evaluate(s)
        self.assertEqual(s,original)

    def test_unknown_reservation_field_rejected(self):
        s=self.example();s['reservations'][0]['guest_name']='PSEUDO-GUEST'
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_unstructured_personal_note_rejected(self):
        s=self.example();s['reservations'][0]['requests']=['guest@email.example']
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_unstructured_room_note_rejected(self):
        s=self.example();s['rooms'][0]['amenities']=['PERSONAL_FIELD']
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_unknown_top_level_field_rejected(self):
        s=self.example();s['passport']='NOT_ALLOWED'
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_duplicate_room_rejected(self):
        s=self.example();s['rooms'].append(copy.deepcopy(s['rooms'][0]))
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_duplicate_reservation_rejected(self):
        s=self.example();s['reservations'].append(copy.deepcopy(s['reservations'][0]))
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_bad_stay_rejected(self):
        s=self.example();s['reservations'][0]['departure']=s['reservations'][0]['arrival']
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_dirty_room_blocks(self):
        r=evaluate(self.example())
        row=next(x for x in r['arrivals'] if x['id']=='KF1003')
        self.assertIn('HOUSEKEEPING_NOT_INSPECTED',row['blockers'])

    def test_ooo_room_blocks_proposal(self):
        s=self.example();b=next(x for x in s['reservations'] if x['id']=='KF1002')
        result=evaluate(s)
        row=next(x for x in result['arrivals'] if x['id']==b['id'])
        self.assertNotEqual(row['suggested_room'],'401')

    def test_cancelled_assigned_is_flagged(self):
        r=evaluate(self.example());x=next(x for x in r['arrivals'] if x['id']=='KF1006')
        self.assertIn('CANCELLED_ASSIGNED',x['blockers'])

    def test_no_pms_match_flagged(self):
        r=evaluate(self.example());x=next(x for x in r['arrivals'] if x['id']=='KF1008')
        self.assertIn('UNMAPPED_PMS',x['blockers'])

    def test_identity_pending_blocks(self):
        r=evaluate(self.example());x=next(x for x in r['arrivals'] if x['id']=='KF1002')
        self.assertIn('IDENTITY_STAFF_REVIEW',x['blockers'])

    def test_payment_review_blocks(self):
        r=evaluate(self.example());x=next(x for x in r['arrivals'] if x['id']=='KF1004')
        self.assertIn('PAYMENT_REVIEW',x['blockers'])

    def test_only_staff_verification_allows_readiness(self):
        s=self.example();b=next(x for x in s['reservations'] if x['id']=='KF1001');b['identity_signal']='pending_staff'
        x=next(x for x in evaluate(s)['arrivals'] if x['id']==b['id'])
        self.assertEqual(x['status'],'blocked')

    def test_bed_mismatch_blocks(self):
        s=self.example();b=next(x for x in s['reservations'] if x['id']=='KF1001');b['bed_request']='twin'
        x=next(x for x in evaluate(s)['arrivals'] if x['id']==b['id'])
        self.assertIn('ROOM_INCOMPATIBLE',x['blockers'])

    def test_duplicate_external_channel_ref(self):
        s=self.example();s['reservations'][1]['channel']=s['reservations'][0]['channel'];s['reservations'][1]['external_ref']=s['reservations'][0]['external_ref']
        report=evaluate(s)
        for bid in ('KF1001','KF1002'):
            self.assertIn('DUPLICATE_CHANNEL_REF',next(x for x in report['arrivals'] if x['id']==bid)['blockers'])

    def test_overlapping_room_conflict(self):
        s=self.example();s['reservations'][1]['room_id']='101'
        report=evaluate(s)
        self.assertIn('ROOM_CONFLICT',next(x for x in report['arrivals'] if x['id']=='KF1001')['blockers'])

    def test_half_open_stays_not_overlapping(self):
        self.assertFalse(overlap({'arrival':'2026-11-12','departure':'2026-11-13'}, {'arrival':'2026-11-13','departure':'2026-11-15'}))

    def test_twin_scarcity_preserved(self):
        s=self.example()
        b=next(x for x in s['reservations'] if x['id']=='KF1002');b['bed_request']='twin'
        room=propose_room(b,s['rooms'],s['reservations'])
        self.assertEqual(room,'302' if '302' not in [r['room_id'] for r in s['reservations']] else None)

    def test_no_allocation_to_incompatible_room(self):
        s=self.example()
        b=next(x for x in s['reservations'] if x['id']=='KF1002');b['category']='family'
        room=propose_room(b,s['rooms'],s['reservations'])
        if room:self.assertEqual(next(x for x in s['rooms'] if x['id']==room)['category'],'family')

    def test_task_unknown_sensitive_field_rejected(self):
        s=self.example();s['tasks'][0]['guest_phone']='NO'
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_unknown_room_data_rejected(self):
        s=self.example();s['rooms'][0]['owner']='NOBODY'
        with self.assertRaises(SnapshotError):evaluate(s)

    def test_invalid_json_nonfinite_rejected(self):
        s=self.example();s['reservations'][0]['price_total']=float('nan')
        with self.assertRaises(SnapshotError):evaluate(s)

if __name__=='__main__':unittest.main()
