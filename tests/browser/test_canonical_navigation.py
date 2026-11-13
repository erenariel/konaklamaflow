"""Read-only identity journeys across canonical operations, folios and reports."""
from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / 'demo/v04-integrated-preview.html'


class CanonicalNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        cls.browser = cls.driver.chromium.launch(**options)
        cls.source = json.loads((ROOT / 'examples/canonical-hotel.json').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1000})
        self.errors, self.requests, self.console_errors = [], [], []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.on('console', lambda message: self.console_errors.append(message.text)
                     if message.type == 'error' else None)
        self.page.set_content(HTML.read_text(encoding='utf-8'))
        self.original = self.snapshot()

    def tearDown(self):
        self.assertEqual(self.snapshot(), self.original, 'Display navigation must not change source facts')
        self.page.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.console_errors, [])
        self.assertEqual(self.requests, [], 'No public-demo network traffic is permitted')

    def snapshot(self):
        return self.page.evaluate('''() => JSON.stringify({canonical:CANONICAL_DATA,
            data:INITIAL_DATA, review:INITIAL_EVALUATION,
            operations:HOTEL_OPS_DATA, reports:HOTEL_OPS_REPORT})''')

    def focus(self, identifier, **options):
        self.assertTrue(self.page.evaluate('''([id,options]) =>
            window.opsFocusReservation(id,options)''', [identifier, options]))

    def action(self, name):
        return self.page.locator('[data-canonical-action="' + name + '"]')

    def report(self, identifier, report_id):
        self.focus(identifier, tab='reports', reportId=report_id)
        return self.page.locator('.ops-report-result')

    def test_reservation_folio_report_and_room_plan_journey_preserves_identity(self):
        self.focus('KF1004')
        expect(self.page.locator('[data-canonical-reservation="KF1004"]')).to_be_visible()
        self.assertIn('STAY-KF1004-A', self.page.locator('#opsView').inner_text())
        self.action('folio').click()
        folio = self.page.locator('[data-canonical-folio="FOL-CAN-KF1004"]')
        expect(folio).to_be_visible()
        self.assertEqual(folio.get_attribute('data-reservation-id'), 'KF1004')
        self.action('reservation').click()
        self.action('reports').click()
        result = self.page.locator('.ops-report-result')
        self.assertEqual(result.get_attribute('data-reservation-scope'), 'KF1004')
        self.assertEqual(result.get_attribute('data-report-id'), 'reservation_list')
        row = result.locator('[data-op-open="res:KF1004"]')
        expect(row).to_have_count(1)
        row.focus()
        row.press('Enter')
        expect(self.page.locator('[data-canonical-reservation="KF1004"]')).to_be_visible()
        self.action('room-plan').click()
        self.assertEqual(self.page.evaluate('() => page'), 'rooms')
        expect(self.page.locator('[data-booking="KF1004"]').first).to_be_visible()

    def test_missing_folio_and_invalid_identifiers_never_select_unrelated_finance(self):
        self.focus('KF1002', tab='folio')
        expect(self.page.locator('[data-financial-state="not_applicable"]')).to_be_visible()
        self.assertIn('KF1002', self.page.locator('#opsView').inner_text())
        expect(self.page.locator('[data-canonical-folio]')).to_have_count(0)
        self.assertNotIn('FOL-CAN-KF1001', self.page.locator('#opsView').inner_text())
        self.focus('KF1004', tab='folio')
        before = self.page.locator('#opsView').inner_html()
        for identifier, options in [('KFD-2026-0004', {}), ('KF1004x', {}),
                                    ('KF1004', {'tab': 'folio', 'folioId': 'FOL-CAN-KF1001'})]:
            with self.subTest(identifier=identifier, options=options):
                self.assertFalse(self.page.evaluate('''([id,options]) =>
                    window.opsFocusReservation(id,options)''', [identifier, options]))
                self.assertEqual(self.page.locator('#opsView').inner_html(), before)
        self.assertFalse(self.page.evaluate("() => window.opsFocusFolio('FOL-NOT-A-SOURCE')"))
        self.assertTrue(self.page.evaluate("() => window.opsFocusFolio('FOL-CAN-KF1007')"))
        expect(self.page.locator('[data-canonical-folio="FOL-CAN-KF1007"]')).to_be_visible()

    def test_report_filter_uses_foreign_keys_and_does_not_apportion_aggregates(self):
        result = self.report('KF1004', 'folio_analysis')
        expect(result.locator('tbody tr')).to_have_count(1)
        self.assertIn('FOL-CAN-KF1004', result.inner_text())
        self.assertNotIn('FOL-CAN-KF1001', result.inner_text())
        self.page.locator('#opsReportType').select_option('transactions')
        self.page.locator('#opsReportReservation').select_option('KF1007')
        self.page.locator('[data-op-action="apply-report"]').click()
        result = self.page.locator('.ops-report-result')
        expect(result.locator('tbody tr')).to_have_count(1)
        self.assertIn('POST-CAN-KF1007', result.inner_text())
        self.assertNotIn('POST-CAN-KF1004', result.inner_text())
        result = self.report('KF1002', 'folio_analysis')
        expect(result.locator('[data-report-scope-state="not_applicable"]')).to_be_visible()
        expect(result.locator('tbody tr')).to_have_count(0)
        result = self.report('KF1004', 'daily_balance')
        expect(result.locator('[data-report-scope-state="not_applicable"]')).to_be_visible()
        expect(result.locator('tbody tr')).to_have_count(0)
        self.page.locator('[data-op-action="clear-report"]').click()
        result = self.page.locator('.ops-report-result')
        expect(result.locator('tbody tr')).to_have_count(1)
        self.assertEqual(result.get_attribute('data-reservation-scope'), '')

    def test_shared_room_report_retains_source_membership_without_aliasing_bookings(self):
        result = self.report('KF1002', 'occupancy')
        expect(result.locator('tbody tr')).to_have_count(1)
        text = result.inner_text()
        self.assertIn('201', text)
        self.assertIn('KF1002', text)
        self.assertIn('KF1003', text)
        row = result.locator('[data-op-open="res:KF1002"]')
        expect(row).to_have_count(1)
        row.click()
        expect(self.page.locator('[data-canonical-reservation="KF1002"]')).to_be_visible()

    def test_guest_links_resolve_actual_membership_and_all_bookings_keep_their_own_stays(self):
        for reservation in self.source['reservations']:
            with self.subTest(reservation=reservation['id']):
                self.focus(reservation['id'])
                detail = self.page.locator('[data-canonical-reservation="' + reservation['id'] + '"]')
                expect(detail).to_be_visible()
                for stay_id in reservation['room_stay_ids']:
                    self.assertIn(stay_id, detail.inner_text())
        self.focus('KF1004')
        guest_button = self.action('guest').first
        guest_id = guest_button.get_attribute('data-guest-id')
        guest_button.click()
        self.assertEqual(self.page.evaluate('() => page'), 'ops_guests')
        self.assertIn(guest_id, self.page.locator('#opsView').inner_text())
        expect(self.action('reservation')).to_have_count(1)
        self.assertEqual(self.action('reservation').get_attribute('data-reservation-id'), 'KF1004')
        self.action('reservation').click()
        expect(self.page.locator('[data-canonical-reservation="KF1004"]')).to_be_visible()

    def test_workflow_story_links_only_precomputed_rule_findings(self):
        self.page.evaluate("() => navTo('ops_workflows')")
        for scenario in ('room_block', 'payment', 'identity', 'channel', 'maintenance'):
            with self.subTest(scenario=scenario):
                self.page.locator('#wfScenario').select_option(scenario)
                source = self.page.evaluate('scenario => wfSourceCase(scenario)', scenario)
                self.assertIsNotNone(source)
                linked = self.page.locator('[data-workflow-reservation]')
                self.assertEqual(linked.get_attribute('data-workflow-reservation'), source['reservationId'])
                self.assertTrue(source['row']['blockers'])
                for code in source['row']['blockers']:
                    self.assertIn(code, self.page.locator('.wf-story').inner_text())
                self.assertIn(source['reservationId'], {r['id'] for r in self.source['reservations']})


if __name__ == '__main__':
    unittest.main()
