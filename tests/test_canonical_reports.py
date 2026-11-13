"""Canonical report provenance, cross-reference and explicit-source regressions."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
import re
import unittest

from konaklamaflow.canonical_reporting import (
    FOLIO_REPORTS, MISSING_REPORT_SOURCES, REPORT_IDS,
    build_canonical_operations_report,
)
from konaklamaflow.experience_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'examples/canonical-hotel.json').read_text())


class CanonicalReportTests(unittest.TestCase):
    def setUp(self):
        self.source = deepcopy(FIXTURE)

    def report(self):
        return build_canonical_operations_report(self.source)

    def test_registry_has_32_stable_ids_and_one_snapshot_identity(self):
        from konaklamaflow.canonical import canonical_fingerprint
        before = deepcopy(self.source)
        report = self.report()
        self.assertEqual(report, self.report())
        self.assertEqual(self.source, before)
        self.assertEqual(report['report_count'], 32)
        self.assertEqual(set(report['reports']), REPORT_IDS)
        self.assertEqual(report['property_id'], self.source['property_id'])
        self.assertEqual(report['as_of'], self.source['as_of'])
        self.assertEqual(report['canonical_sha256'], canonical_fingerprint(self.source))
        for entry in report['reports'].values():
            self.assertEqual(entry['canonical_sha256'], report['canonical_sha256'])
            self.assertTrue(entry['scope'])

    def test_bookings_are_twelve_real_canonical_ids_not_old_positional_aliases(self):
        report = self.report()
        original = {booking['id']: booking for booking in self.source['reservations']}
        rows = report['reports']['reservation_list']['rows']
        self.assertEqual(len(rows), 12)
        self.assertEqual({row['id'] for row in rows}, set(original))
        self.assertEqual(set(report['reservation_links']), set(original))
        for row in rows:
            self.assertEqual(row['status'], original[row['id']]['status'])
            self.assertEqual(row['arrival_state'], original[row['id']]['arrival_state'])
            self.assertEqual(row['room_stay_ids'], original[row['id']]['room_stay_ids'])
            self.assertFalse(row['id'].startswith('KFD-'))

    def test_folio_math_is_only_explicit_ledger_movements_with_source_record_ids(self):
        report = self.report()
        expected = {folio['id']: folio for folio in self.source['folios']}
        self.assertEqual({row['folio_id'] for row in report['folios']}, set(expected))
        for row in report['folios']:
            source = expected[row['folio_id']]
            debit = sum((Decimal(p['amount']) for p in source['postings']), Decimal('0.00'))
            credit = sum((Decimal(p['amount']) for p in source['payments']), Decimal('0.00'))
            self.assertEqual(row['postings'], f'{debit:.2f}')
            self.assertEqual(row['payments'], f'{credit:.2f}')
            self.assertEqual(row['balance'], f'{debit-credit:.2f}')
            self.assertEqual(row['reservation_id'], source['reservation_id'])
            self.assertEqual(row['room_stay_id'], source['room_stay_id'])
            self.assertEqual(row['source_record_id'], source['id'])
        transactions = report['reports']['transactions']['rows']
        self.assertEqual({row['posting_id'] for row in transactions},
                         {row['id'] for folio in expected.values() for row in folio['postings']})
        self.assertFalse(any('payment_id' in row for row in transactions))
        self.assertEqual(report['reports']['daily_balance']['rows'], [{
            'date': self.source['as_of'], 'currency': 'EUR',
            'postings': '316.50', 'payments': '0.00', 'net': '316.50'}])

    def test_no_folio_means_not_applicable_never_an_invented_zero_balance(self):
        report = self.report()
        without = {r['id'] for r in self.source['reservations']} - {
            f['reservation_id'] for f in self.source['folios']}
        self.assertEqual(len(without), 9)
        for identifier in without:
            link = report['reservation_links'][identifier]
            self.assertEqual(link['finance_status'], 'not_applicable')
            self.assertEqual(link['folio_ids'], [])
            self.assertNotIn('folio_analysis', link['report_ids'])
            self.assertFalse(any(row['reservation_id'] == identifier for row in report['folios']))
        for key in FOLIO_REPORTS:
            coverage = report['reports'][key]['coverage']
            self.assertEqual(set(coverage['missing_reservation_ids']), without)

    def test_currency_totals_are_separate_without_implicit_fx_conversion(self):
        booking = next(row for row in self.source['reservations'] if row['id'] == 'KF1004')
        booking['currency'] = 'TRY'
        folio = next(row for row in self.source['folios'] if row['reservation_id'] == booking['id'])
        folio['currency'] = 'TRY'
        rows = self.report()['reports']['daily_balance']['rows']
        self.assertEqual(rows, [
            {'date': self.source['as_of'], 'currency': 'EUR',
             'postings': '217.50', 'payments': '0.00', 'net': '217.50'},
            {'date': self.source['as_of'], 'currency': 'TRY',
             'postings': '99.00', 'payments': '0.00', 'net': '99.00'},
        ])

    def test_explicit_advance_payment_is_a_credit_with_exact_parent_and_stay(self):
        folio = next(row for row in self.source['folios'] if row['reservation_id'] == 'KF1007')
        folio['payments'].append({'id': 'PAY-CAN-EXPLICIT', 'date': '2026-11-11',
            'method': 'bank_transfer', 'amount': '20.00', 'reference': 'DEMO_ADVANCE'})
        report = self.report()
        advance = report['reports']['advance_payment']['rows']
        self.assertEqual(len(advance), 1)
        self.assertEqual(advance[0]['payment_id'], 'PAY-CAN-EXPLICIT')
        self.assertEqual(advance[0]['reservation_id'], 'KF1007')
        self.assertEqual(advance[0]['room_stay_id'], 'STAY-KF1007-A')
        ledger = next(row for row in report['city_ledger'] if row['reservation_id'] == 'KF1007')
        self.assertEqual((ledger['postings'], ledger['payments'], ledger['balance']),
                         ('127.50', '20.00', '107.50'))
        # The advance is before the declared business date; it is not a new
        # credit movement of the daily source ledger on 12 November.
        self.assertEqual(report['reports']['daily_balance']['rows'][0]['payments'], '0.00')

    def test_removing_all_folios_makes_finance_unavailable_without_creating_rows(self):
        self.source['folios'] = []
        report = self.report()
        self.assertEqual(report['folios'], [])
        self.assertEqual(report['city_ledger'], [])
        for key in FOLIO_REPORTS:
            entry = report['reports'][key]
            self.assertEqual(entry['status'], 'not_implemented')
            self.assertEqual(entry['source_state'], 'missing_source')
            self.assertEqual(entry['missing_sources'], ['explicit_folios'])
            self.assertEqual(entry['rows'], [])
        self.assertTrue(all(row['finance_status'] == 'not_applicable'
                            for row in report['reservation_links'].values()))

    def test_quote_amount_is_not_fabricated_into_nightly_rates_or_folio(self):
        for stay in self.source['room_stays']:
            stay['nightly_rates'] = []
        self.source['folios'] = []
        report = self.report()
        rates = report['reports']['room_rate_control']
        self.assertEqual(rates['status'], 'not_implemented')
        self.assertEqual(rates['rows'], [])
        self.assertEqual(rates['missing_sources'], ['explicit_nightly_rates'])
        self.assertEqual(report['reports']['transactions']['rows'], [])
        self.assertTrue(all('room_rate_control' not in link['report_ids']
                            for link in report['reservation_links'].values()))

    def test_unsupported_sources_and_all_live_integrations_are_explicitly_disconnected(self):
        report = self.report()
        self.assertTrue(report['integrations'])
        self.assertTrue(all(value == 'source_not_connected'
                            for value in report['integrations'].values()))
        for key, source in MISSING_REPORT_SOURCES.items():
            entry = report['reports'][key]
            self.assertEqual(entry['status'], 'not_implemented')
            self.assertEqual(entry['rows'], [])
            self.assertIn(source, entry['missing_sources'])
        self.assertFalse(any(value for key, value in report['safety'].items()
                             if key != 'human_approval_required'))
        self.assertTrue(report['safety']['human_approval_required'])

    def test_missing_fx_is_not_a_live_rate_or_a_one_to_one_conversion(self):
        self.source['fx_rates'] = []
        entry = self.report()['reports']['exchange_rates']
        self.assertEqual(entry['status'], 'not_implemented')
        self.assertEqual(entry['source_state'], 'source_not_connected')
        self.assertEqual(entry['rows'], [])

    def test_room_holds_match_authoritative_engine_not_a_second_occupancy_rule(self):
        from konaklamaflow.canonical import project_review, review_links
        report = self.report()
        review = evaluate(project_review(self.source))
        links = review_links(self.source)
        actual = {row['room']: row for row in report['reports']['occupancy']['rows']}
        self.assertEqual(set(actual), {room['id'] for room in self.source['rooms']})
        self.assertEqual(report['review_snapshot_sha256'], review['snapshot_sha256'])
        for row in review['room_plan']:
            self.assertEqual(actual[row['id']]['held_in_review_snapshot'],
                             bool(row['held_reservation_ids']))
            self.assertEqual(set(actual[row['id']]['reservation_ids']), {
                links[identifier]['reservation_id'] for identifier in row['held_reservation_ids']})
            self.assertEqual(set(actual[row['id']]['room_stay_ids']), {
                links[identifier]['room_stay_id'] for identifier in row['held_reservation_ids']})
        technical = next(row for row in report['reports']['blockage_report']['rows']
                         if row['room'] == '401')
        self.assertIn('BLOCK-401-TECH', technical['room_block_ids'])

    def test_cancelled_physically_occupied_reservation_is_not_released_by_financial_view(self):
        booking = next(row for row in self.source['reservations'] if row['id'] == 'KF1006')
        booking['arrival_state'] = 'checked_in'
        report = self.report()
        room = next(row for row in report['reports']['occupancy']['rows'] if row['room'] == '102')
        self.assertIn('KF1006', room['reservation_ids'])
        self.assertTrue(any(row['reservation_id'] == 'KF1006'
                            and row['status'] == 'cancelled' and row['arrival_state'] == 'checked_in'
                            for row in room['source_physical_signals']))
        link = report['reservation_links']['KF1006']
        self.assertEqual(link['folio_ids'], [])
        self.assertEqual(link['finance_status'], 'not_applicable')

    def test_pending_status_and_distinct_duplicate_source_records_are_not_coerced_or_merged(self):
        from konaklamaflow.canonical import project_review
        pending = next(row for row in self.source['reservations'] if row['id'] == 'KF1005')
        pending['status'] = 'pending'
        same = next(row for row in self.source['reservations'] if row['id'] == 'KF1003')
        duplicate = next(row for row in self.source['reservations'] if row['id'] == 'KF1012')
        duplicate['source_ref'] = deepcopy(same['source_ref'])
        report = self.report()
        rows = {row['id']: row for row in report['reports']['reservation_list']['rows']}
        self.assertEqual(rows['KF1005']['status'], 'pending')
        self.assertEqual(len(rows), 12)
        self.assertIn('KF1003', rows)
        self.assertIn('KF1012', rows)
        review = evaluate(project_review(self.source))
        for row in review['arrivals']:
            if row['id'] in {'KF1003', 'KF1012'}:
                self.assertIn('DUPLICATE_CHANNEL_REF', row['blockers'])

    def test_two_room_stays_remain_one_parent_and_folio_remains_exactly_on_its_source_stay(self):
        booking = next(row for row in self.source['reservations'] if row['id'] == 'KF1004')
        primary = next(row for row in self.source['room_stays']
                       if row['id'] == booking['room_stay_ids'][0])
        extra = deepcopy(primary)
        extra.update(id='STAY-KF1004-B', room_id='202', quote_total='50.00', guest_ids=[])
        extra['nightly_rates'] = [{'date': primary['arrival'], 'amount': '50.00'}]
        for index in (1, 2):
            guest = deepcopy(next(row for row in self.source['guests']
                                  if row['id'] == primary['guest_ids'][0]))
            guest.update(id=f'GUEST-KF1004-B{index}', surname=f'DEMO_KF1004_B{index}',
                         display_label=f'ÖRNEK KF1004 B{index}')
            self.source['guests'].append(guest)
            extra['guest_ids'].append(guest['id'])
            booking['guest_ids'].append(guest['id'])
        booking['room_stay_ids'].append(extra['id'])
        self.source['room_stays'].append(extra)
        report = self.report()
        rows = report['reports']['reservation_list']['rows']
        row = next(row for row in rows if row['id'] == 'KF1004')
        self.assertEqual(len(rows), 12)
        self.assertEqual({part['room_stay_id'] for part in row['rooms']},
                         {'STAY-KF1004-A', 'STAY-KF1004-B'})
        self.assertEqual(report['reservation_links']['KF1004']['folio_ids'], ['FOL-CAN-KF1004'])
        folio = next(row for row in report['folios'] if row['reservation_id'] == 'KF1004')
        self.assertEqual(folio['room_stay_id'], 'STAY-KF1004-A')
        self.assertEqual(folio['postings'], '99.00')
        self.assertEqual(len(report['reports']['transactions']['rows']), 3)
        prices = [row for row in report['reports']['room_rate_control']['rows']
                  if row['reservation_id'] == 'KF1004']
        self.assertEqual({row['room_stay_id'] for row in prices},
                         {'STAY-KF1004-A', 'STAY-KF1004-B'})

    def test_regenerated_report_changes_binding_after_source_change(self):
        first = self.report()
        room = next(row for row in self.source['rooms'] if row['id'] == '303')
        room['housekeeping'] = 'inspected'
        second = self.report()
        self.assertNotEqual(first['canonical_sha256'], second['canonical_sha256'])
        self.assertNotEqual(first['review_snapshot_sha256'], second['review_snapshot_sha256'])
        self.assertEqual(first['reports']['transactions']['rows'], second['reports']['transactions']['rows'])
        self.assertEqual(first, build_canonical_operations_report(FIXTURE))

    def test_future_synthetic_snapshot_is_deterministic_and_uses_its_own_business_date(self):
        def shifted(value):
            if isinstance(value, dict):
                return {key: shifted(item) for key, item in value.items()}
            if isinstance(value, list):
                return [shifted(item) for item in value]
            if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                return (date.fromisoformat(value) + timedelta(days=30)).isoformat()
            return value
        self.source = shifted(self.source)
        first = self.report()
        self.assertEqual(first, self.report())
        self.assertEqual(first['as_of'], '2026-12-12')
        self.assertEqual(first['reports']['daily_balance']['rows'][0]['date'], first['as_of'])
