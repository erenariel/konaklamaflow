"""Canonical identity/FK, projection, money and conservative review tests."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import unittest

from konaklamaflow.canonical import (CanonicalError, aggregate_reservation_reviews,
    canonical_fingerprint, project_operations, project_review, review_links,
    validate_canonical)
from konaklamaflow.experience_engine import evaluate, validate as validate_review

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=json.loads((ROOT/'examples/canonical-hotel.json').read_text())
LEGACY_REVIEW=json.loads((ROOT/'examples/fictional-hotel.json').read_text())


class CanonicalTests(unittest.TestCase):
    def setUp(self):self.source=deepcopy(FIXTURE)

    def booking(self,identifier='KF1010'):
        return next(row for row in self.source['reservations'] if row['id']==identifier)

    def stay(self,identifier='KF1010'):
        return next(row for row in self.source['room_stays'] if row['reservation_id']==identifier)

    def room(self,identifier='201'):
        return next(row for row in self.source['rooms'] if row['id']==identifier)

    def assert_invalid(self):
        with self.assertRaises(CanonicalError) as caught:validate_canonical(self.source)
        self.assertEqual(str(caught.exception),'Invalid canonical fictional hotel snapshot')

    def make_multiroom(self):
        booking=self.booking('KF1011');other=deepcopy(self.stay('KF1011'))
        other.update(id='STAY-KF1011-B',room_id='402',bed_request='none',requests=[],
                     guest_ids=['GUEST-KF1011-3','GUEST-KF1011-4'],quote_total='200.00')
        other['nightly_rates']=[{'date':'2026-11-13','amount':'100.00'},
                                {'date':'2026-11-14','amount':'100.00'}]
        template=self.source['guests'][0]
        for n,identifier in enumerate(other['guest_ids'],3):
            guest=deepcopy(template);guest.update(id=identifier,surname='DEMO_KF1011_'+str(n),display_label='ÖRNEK KF1011 '+str(n))
            self.source['guests'].append(guest)
        self.source['room_stays'].append(other);booking['room_stay_ids'].append(other['id'])
        booking['guest_ids']+=other['guest_ids']
        return booking,other

    def test_owned_deterministic_source_has_one_parent_set_and_no_old_finance_alias(self):
        before=deepcopy(self.source)
        canonical=validate_canonical(self.source)
        review=project_review(self.source);ops=project_operations(self.source)
        self.assertEqual(self.source,before)
        expected={r['id'] for r in canonical['reservations']}
        self.assertEqual(expected,{r['id'] for r in review['reservations']})
        self.assertEqual(expected,{r['id'] for r in ops['reservations']})
        self.assertEqual(len(expected),12)
        self.assertEqual(ops['as_of'],review['as_of'])
        self.assertEqual(canonical_fingerprint(self.source),canonical_fingerprint(deepcopy(self.source)))
        self.assertNotIn('KFD-2026-',json.dumps(canonical))
        self.assertIs(canonical['provenance']['legacy_financial_records_migrated'],False)

    def test_default_review_preserves_original_engine_facts_and_decisions(self):
        self.assertEqual(project_review(self.source),validate_review(LEGACY_REVIEW))
        self.assertEqual(evaluate(project_review(self.source)),evaluate(LEGACY_REVIEW))

    def test_reordering_cannot_join_guest_folio_or_room_by_position(self):
        original=project_operations(self.source)
        for key in ('reservations','room_stays','guests','agencies','folios','rooms'):
            self.source[key].reverse()
        projected=project_operations(self.source)
        self.assertEqual({r['id']:r for r in original['reservations']},
                         {r['id']:r for r in projected['reservations']})
        self.assertEqual({r['id']:r for r in original['folios']},
                         {r['id']:r for r in projected['folios']})

    def test_projection_preserves_exact_status_including_pending_and_no_show(self):
        for status in ('pending','no_show','cancelled','in_house','checked_out'):
            self.booking()['status']=status
            review=next(r for r in project_review(self.source)['reservations'] if r['id']=='KF1010')
            ops=next(r for r in project_operations(self.source)['reservations'] if r['id']=='KF1010')
            self.assertEqual(review['status'],status)
            self.assertEqual(ops['status'],status)
            self.assertEqual(ops['source_status'],status)

    def test_typed_ref_property_and_type_cannot_cross_namespaces(self):
        original=deepcopy(self.booking()['source_ref'])
        self.booking()['source_ref']['property_id']='OTHER_SYNTHETIC_PROPERTY';self.assert_invalid()
        self.booking()['source_ref']=original
        self.booking()['source_ref']['kind']='pms';self.assert_invalid()

    def test_unknown_reference_fields_are_rejected_without_echo(self):
        self.booking()['source_ref']['api_token']='SYNTHETIC_REJECT_ONLY'
        self.assert_invalid()

    def test_duplicate_ota_reference_is_a_review_fact_and_never_merges_parents(self):
        self.booking('KF1012')['source_ref']=deepcopy(self.booking('KF1003')['source_ref'])
        self.booking('KF1012')['agency_id']='TRIP'
        value=validate_canonical(self.source)
        self.assertEqual(len(value['reservations']),12)
        rows=evaluate(project_review(value))['arrivals']
        for identifier in ('KF1003','KF1012'):
            self.assertIn('DUPLICATE_CHANNEL_REF',next(r for r in rows if r['id']==identifier)['blockers'])

    def test_duplicate_entity_ids_and_projection_identity_collisions_are_rejected(self):
        self.source['reservations'][1]['id']=self.source['reservations'][0]['id']
        self.assert_invalid()

    def test_orphan_and_reverse_room_stay_fk_rejected(self):
        stay=self.stay();stay['reservation_id']='UNKNOWN_BOOKING';self.assert_invalid()
        stay['reservation_id']='KF1001';self.assert_invalid()

    def test_guest_relationships_must_be_explicit_and_consistent(self):
        self.stay()['guest_ids']=['UNKNOWN_GUEST'];self.assert_invalid()

    def test_guest_pii_fields_must_remain_null(self):
        self.source['guests'][0]['email']='synthetic@example.invalid'
        self.assert_invalid()

    def test_invalid_untyped_boolean_metadata_is_rejected(self):
        self.source['provenance']['legacy_financial_records_migrated']=0
        self.assert_invalid()

    def test_folio_parent_stay_room_and_currency_must_match(self):
        original=deepcopy(self.source['folios'][0])
        for field,bad in (('reservation_id','KF1004'),('room_stay_id','STAY-KF1004-A'),
                          ('room_id','104'),('currency','TRY')):
            self.source['folios'][0]=deepcopy(original)
            self.source['folios'][0][field]=bad
            self.assert_invalid()

    def test_folio_payment_does_not_appear_from_a_ready_signal(self):
        value=project_operations(self.source)
        self.assertTrue(all(not f['payments'] for f in value['folios']))
        self.assertEqual({f['reservation_id'] for f in value['folios']},{'KF1001','KF1004','KF1007'})
        self.assertFalse(any(f['reservation_id']=='KF1010' for f in value['folios']))

    def test_missing_rates_and_folios_stay_missing(self):
        self.source['folios']=[]
        for stay in self.source['room_stays']:stay['nightly_rates']=[]
        projected=project_operations(self.source)
        self.assertEqual(projected['folios'],[])
        self.assertTrue(all(not part['nightly_rates'] for b in projected['reservations'] for part in b['rooms']))

    def test_decimal_quotes_reject_float_nonfinite_and_wrong_explicit_totals(self):
        for bad in (89.0,'NaN','Infinity','89.001','-1.00'):
            self.stay()['quote_total']=bad;self.assert_invalid()
        self.stay()['quote_total']='89.00';self.stay()['nightly_rates'][0]['amount']='88.00'
        self.assert_invalid()

    def test_future_postings_and_postings_outside_stay_are_not_recorded_movements(self):
        self.source['folios'][0]['postings'][0]['date']='2026-11-13';self.assert_invalid()
        self.source['folios'][0]['postings'][0]['date']='2026-11-11';self.assert_invalid()

    def test_explicit_advance_payment_allowed_but_not_invented(self):
        self.source['folios'][0]['payments']=[{'id':'PAY-CAN-ADVANCE','date':'2026-11-11',
            'method':'bank_transfer','amount':'20.00','reference':'SYNTHETIC_ADVANCE'}]
        projected=project_operations(self.source)
        self.assertEqual(projected['folios'][0]['payments'][0]['amount'],'20.00')
        self.source['folios'][0]['payments'][0]['date']='2026-11-13';self.assert_invalid()

    def test_operational_overlap_and_incompatible_capacity_are_not_schema_errors(self):
        self.stay()['room_id']='101'
        report=evaluate(project_review(self.source))
        self.assertIn('ROOM_CONFLICT',next(r for r in report['arrivals'] if r['id']=='KF1010')['blockers'])
        self.stay()['room_id']='201';self.stay()['adults']=3
        report=evaluate(project_review(self.source))
        self.assertIn('ROOM_INCOMPATIBLE',next(r for r in report['arrivals'] if r['id']=='KF1010')['blockers'])

    def test_twin_housekeeping_and_technical_constraints_reach_shared_rule_engine(self):
        self.stay('KF1002')['room_id']='402'
        rows=evaluate(project_review(self.source))['arrivals']
        self.assertIn('ROOM_INCOMPATIBLE',next(r for r in rows if r['id']=='KF1002')['blockers'])
        self.room()['housekeeping']='dirty'
        rows=evaluate(project_review(self.source))['arrivals']
        self.assertIn('HOUSEKEEPING_NOT_INSPECTED',next(r for r in rows if r['id']=='KF1010')['blockers'])
        self.room()['housekeeping']='out_of_order'
        rows=evaluate(project_review(self.source))['arrivals']
        self.assertIn('ROOM_INCOMPATIBLE',next(r for r in rows if r['id']=='KF1010')['blockers'])

    def test_cancelled_checked_in_stay_remains_a_physical_review_hold(self):
        self.booking('KF1006')['arrival_state']='checked_in'
        report=evaluate(project_review(self.source))
        room=next(r for r in report['room_plan'] if r['id']=='102')
        self.assertIn('KF1006',room['held_reservation_ids'])
        self.assertIn('CANCELLED_ASSIGNED',next(r for r in report['arrivals'] if r['id']=='KF1006')['blockers'])

    def test_room_blocks_have_real_source_identity_and_do_not_release_ooo(self):
        projected=project_operations(self.source)
        room=next(r for r in projected['rooms'] if r['id']=='401')
        self.assertTrue(room['blocked']);self.assertEqual(room['room_block_ids'],['BLOCK-401-TECH'])
        self.source['room_blocks'][0]['room_id']='UNKNOWN_ROOM';self.assert_invalid()

    def test_multiroom_is_not_collapsed_to_first_room_or_renamed_parent(self):
        booking,other=self.make_multiroom()
        review=project_review(self.source);links=review_links(self.source)
        cases=[r for r in review['reservations'] if links[r['id']]['reservation_id']=='KF1011']
        self.assertEqual(len(review['reservations']),13)
        self.assertEqual({r['id'] for r in cases},{'STAY-KF1011-A','STAY-KF1011-B'})
        self.assertEqual({r['room_id'] for r in cases},{'302','402'})
        self.assertEqual({links[r['id']]['room_stay_id'] for r in cases},set(booking['room_stay_ids']))
        ops=next(r for r in project_operations(self.source)['reservations'] if r['id']=='KF1011')
        self.assertEqual(ops['room_stay_ids'],booking['room_stay_ids']);self.assertEqual(len(ops['rooms']),2)
        grouped=next(r for r in aggregate_reservation_reviews(self.source)['reservations'] if r['reservation_id']=='KF1011')
        self.assertTrue(grouped['requires_multiroom_review'])
        self.assertEqual(grouped['scope_note'],'SHARED_PARENT_REFERENCES_ARE_NOT_PROOF_OF_DUPLICATE_OTA')
        self.assertEqual(len(grouped['room_stay_reviews']),2)
        self.assertFalse(grouped['live_operations_allowed']);self.assertTrue(grouped['human_approval_required'])
        self.assertEqual(grouped['status'],'blocked')

    def test_multiroom_folio_is_tied_to_its_explicit_stay(self):
        _,other=self.make_multiroom();template=deepcopy(self.source['folios'][0])
        template.update(id='FOL-CAN-MULTI',reservation_id='KF1011',room_stay_id=other['id'],room_id='402',postings=[],payments=[])
        self.source['folios'].append(template)
        self.assertEqual(project_operations(self.source)['folios'][-1]['room_stay_id'],other['id'])
        template['room_id']='302';self.assert_invalid()

    def test_multiroom_reservation_tasks_are_projected_to_exact_room_stays(self):
        self.make_multiroom()
        self.source['tasks'].append({'id':'TASK-CAN-MULTI','kind':'frontdesk','room_id':None,
            'reservation_id':'KF1011','status':'open','priority':'normal'})
        projection=project_review(self.source)
        tasks=[t for t in projection['tasks'] if t['reservation_id'] in {'STAY-KF1011-A','STAY-KF1011-B'}]
        self.assertEqual({t['reservation_id'] for t in tasks},{'STAY-KF1011-A','STAY-KF1011-B'})
        self.assertEqual(len({t['id'] for t in tasks}),2)
        self.assertEqual(self.source['tasks'][-1]['id'],'TASK-CAN-MULTI')

    def test_future_business_date_is_deterministic_and_not_a_live_clock(self):
        self.source['as_of']='2026-11-14';self.source['report_versions']['hotel_clock']='2026-11-14'
        first=project_review(self.source);second=project_review(deepcopy(self.source))
        self.assertEqual(first,second);self.assertEqual(first['as_of'],'2026-11-14')
        self.assertEqual(evaluate(first),evaluate(second))

    def test_all_32_registry_entries_required_and_unknown_fields_rejected(self):
        self.source['report_catalog'].pop();self.assert_invalid()
        self.source=deepcopy(FIXTURE);self.source['provider_credentials']='SYNTHETIC_REJECT_ONLY';self.assert_invalid()
