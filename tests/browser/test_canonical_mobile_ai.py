"""One fictional source across the interactive review and hotel operations.

These exercise the generated offline document, including PR #34's real mobile
click target and motion labels. They do not certify translations or live PMS use.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

from konaklamaflow.canonical import (
    canonical_fingerprint, project_operations, project_review, validate_canonical,
)
from konaklamaflow.experience_engine import evaluate

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / 'demo/v04-integrated-preview.html'
SOURCE = ROOT / 'examples/canonical-hotel.json'
LOCALES = ('tr', 'en', 'fr', 'el', 'he', 'ar', 'de', 'ru', 'es', 'uk')


class CanonicalMobileAndAITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        cls.browser = cls.driver.chromium.launch(**options)
        cls.canonical = validate_canonical(json.loads(SOURCE.read_text(encoding='utf-8')))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1000},
                                          locale='tr-TR')
        self.errors, self.requests, self.console_errors = [], [], []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.on('console', lambda message: self.console_errors.append(message.text)
                     if message.type == 'error' else None)
        self.page.set_content(HTML.read_text(encoding='utf-8'))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.console_errors, [])
        self.assertEqual(self.requests, [], 'The public demo must remain fully offline')

    def frozen_documents(self):
        return self.page.evaluate("""() => JSON.stringify({
            canonical:CANONICAL_DATA, review:INITIAL_EVALUATION,
            operations:HOTEL_OPS_DATA, reports:HOTEL_OPS_REPORT
        })""")

    def test_both_projections_and_all_report_references_resolve_to_one_source(self):
        review = project_review(self.canonical)
        operations = project_operations(self.canonical)
        self.assertEqual(self.page.evaluate('() => CANONICAL_DATA'), self.canonical)
        self.assertEqual(self.page.evaluate('() => INITIAL_DATA'), review)
        self.assertEqual(self.page.evaluate('() => INITIAL_EVALUATION'), evaluate(review))
        self.assertEqual(self.page.evaluate('() => HOTEL_OPS_DATA'), operations)

        links = self.page.evaluate('() => CANONICAL_LINKS')
        reports = self.page.evaluate('() => HOTEL_OPS_REPORT')
        checksum = canonical_fingerprint(self.canonical)
        self.assertEqual(links['canonical_sha256'], checksum)
        self.assertEqual(reports['canonical_sha256'], checksum)
        self.assertEqual(links['as_of'], self.canonical['as_of'])
        self.assertEqual(reports['as_of'], self.canonical['as_of'])
        self.assertEqual(operations['as_of'], review['as_of'])
        parent_ids = {row['id'] for row in self.canonical['reservations']}
        self.assertEqual(set(links['reservations']), parent_ids)
        self.assertEqual({row['id'] for row in operations['reservations']}, parent_ids)
        self.assertEqual(set(links['review_links']), {row['id'] for row in review['reservations']})
        self.assertEqual({row['reservation_id'] for row in links['review_links'].values()}, parent_ids)
        self.assertEqual(len(reports['reports']), 32)
        self.assertEqual(set(reports['reports']), {row['id'] for row in self.canonical['report_catalog']})

        stays = {row['id']: row for row in self.canonical['room_stays']}
        canonical_bookings = {row['id']: row for row in self.canonical['reservations']}
        operation_bookings = {row['id']: row for row in operations['reservations']}
        guests = {row['id'] for row in self.canonical['guests']}
        folios = {row['id']: row for row in self.canonical['folios']}
        rooms = {row['id'] for row in self.canonical['rooms']}
        for reservation_id, row in links['reservations'].items():
            with self.subTest(reservation=reservation_id):
                self.assertEqual(row['reservation_id'], reservation_id)
                source_booking = canonical_bookings[reservation_id]
                shown_booking = operation_bookings[reservation_id]
                portions = [stays[stay_id] for stay_id in source_booking['room_stay_ids']]
                self.assertEqual(shown_booking['status'], source_booking['status'])
                self.assertEqual(shown_booking['arrival_state'], source_booking['arrival_state'])
                self.assertEqual(shown_booking['source_ref'], source_booking['source_ref'])
                self.assertEqual(shown_booking['pms_ref'], source_booking['pms_ref'])
                self.assertEqual(shown_booking['checkin'], min(part['arrival'] for part in portions))
                self.assertEqual(shown_booking['checkout'], max(part['departure'] for part in portions))
                self.assertEqual({part['room_stay_id'] for part in shown_booking['rooms']},
                                 set(source_booking['room_stay_ids']))
                self.assertTrue(set(row['guest_ids']) <= guests)
                self.assertTrue(set(row['room_ids']) <= rooms)
                for stay_id in row['room_stay_ids']:
                    self.assertEqual(stays[stay_id]['reservation_id'], reservation_id)
                for folio_id in row['folio_ids']:
                    self.assertEqual(folios[folio_id]['reservation_id'], reservation_id)
                self.assertEqual(row['finance_status'],
                                 'available' if row['folio_ids'] else 'not_applicable')
        self.assertEqual({row['id'] for row in operations['folios']}, set(folios))
        self.assertEqual({row['folio_id'] for row in reports['folios']}, set(folios))

        def assert_references(value):
            if isinstance(value, list):
                for child in value:
                    assert_references(child)
            elif isinstance(value, dict):
                for field, child in value.items():
                    if field == 'reservation_id' and child is not None:
                        self.assertIn(child, parent_ids)
                    elif field == 'folio_id' and child is not None:
                        self.assertIn(child, folios)
                    assert_references(child)

        for report in reports['reports'].values():
            self.assertEqual(report['canonical_sha256'], checksum)
            if report['status'] != 'implemented':
                self.assertEqual(report['rows'], [])
            assert_references(report['rows'])
        self.assertTrue(all(state == 'source_not_connected'
                            for state in reports['integrations'].values()))

    def test_all_ai_scenarios_use_the_same_reservations_rooms_and_read_only_reports(self):
        before = self.frozen_documents()
        source_before = self.page.evaluate('() => JSON.stringify(state)')
        canonical_ids = {row['id'] for row in self.canonical['reservations']}
        room_ids = {row['id'] for row in self.canonical['rooms']}
        stories = self.page.evaluate('() => DEMO_STORIES.stories')
        self.assertEqual({story['id'] for story in stories}, {
            'twin-review', 'housekeeping-review', 'channel-review', 'arrival-review'})
        links = self.page.evaluate('() => CANONICAL_LINKS.review_links')
        for story in stories:
            with self.subTest(story=story['id']):
                self.assertIn(links[story['booking_id']]['reservation_id'], canonical_ids)
                self.assertTrue(set(story['room_ids']) <= room_ids)
                self.page.locator('#tourScenario').select_option(story['id'])
                for index, step in enumerate(story['steps']):
                    self.page.locator('#commandNext').click()
                    expect(self.page.locator('#aiCommandCenter')).to_have_attribute(
                        'data-scene-step', str(index))
                    self.assertTrue(set(step['room_ids']) <= room_ids)
                    highlighted = self.page.locator('.rack-row.evidence-highlight').evaluate_all(
                        '(elements) => elements.map(element => element.dataset.rackRoom)')
                    self.assertEqual(set(highlighted), set(step['room_ids']))
                    self.assertEqual(self.frozen_documents(), before)
                self.assertEqual(self.page.evaluate('() => JSON.stringify(state)'), source_before)
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertFalse(self.page.locator('#exportButton').is_disabled())

    def test_mobile_language_hit_target_rtl_and_motion_labels_survive_all_ten_locales(self):
        before = self.frozen_documents()
        for width in (320, 375, 390):
            self.page.set_viewport_size({'width': width, 'height': 844})
            for locale in LOCALES:
                with self.subTest(width=width, locale=locale):
                    selector = self.page.locator('#globalLanguage')
                    selector.scroll_into_view_if_needed()
                    selector.select_option(locale)
                    selector.scroll_into_view_if_needed()
                    target = selector.evaluate("""element => {
                        const bounds=element.getBoundingClientRect();
                        const hit=document.elementFromPoint(
                            bounds.x+bounds.width/2,bounds.y+bounds.height/2);
                        return {hit:hit?.id, width:bounds.width, height:bounds.height};
                    }""")
                    self.assertEqual(target['hit'], 'globalLanguage')
                    self.assertGreater(target['width'], 0)
                    self.assertGreater(target['height'], 0)
                    expect(self.page.locator('html')).to_have_attribute('lang', locale)
                    expect(self.page.locator('html')).to_have_attribute(
                        'dir', 'rtl' if locale in ('ar', 'he') else 'ltr')
                    self.assertTrue(self.page.evaluate(
                        '() => document.documentElement.scrollWidth <= innerWidth'))
                    label = self.page.locator('#kfMotion').inner_text()
                    if locale != 'tr':
                        self.assertNotIn('Hareket:', label)
                    self.page.locator('#kfMotion').click()
                    self.assertNotEqual(self.page.locator('#kfMotion').inner_text(), label)
                    self.page.locator('#kfMotion').click()
                    self.assertEqual(self.page.locator('#kfMotion').inner_text(), label)
                    expect(self.page.locator('#commandProgressCount bdi')).to_have_attribute('dir', 'ltr')
                    self.assertEqual(self.frozen_documents(), before)

    def test_absent_finance_is_not_an_unrelated_first_folio_or_zero_balance(self):
        before = self.frozen_documents()
        self.assertTrue(self.page.evaluate(
            "() => window.opsFocusReservation('KF1002', {tab:'folio'})"))
        self.assertEqual(self.page.evaluate('() => opsState.selectedReservation'), 'KF1002')
        marker = self.page.locator('[data-financial-state="not_applicable"]')
        expect(marker.first).to_be_visible()
        self.assertIn('KF1002', self.page.locator('#content').inner_text())
        self.assertEqual(self.page.evaluate('() => CANONICAL_LINKS.reservations.KF1002.folio_ids'), [])
        self.assertNotIn('FOL-CAN-KF1001', self.page.locator('#content').inner_text())
        selected = self.page.evaluate('() => JSON.stringify(opsState)')
        self.assertFalse(self.page.evaluate(
            "() => window.opsFocusReservation('UNKNOWN_RESERVATION', {tab:'folio'})"))
        self.assertEqual(self.page.evaluate('() => JSON.stringify(opsState)'), selected)
        self.assertEqual(self.frozen_documents(), before)

    def test_housekeeping_simulation_marks_frozen_financial_source_stale(self):
        before = self.frozen_documents()
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.assertTrue(self.page.evaluate('() => reportStale'))
        self.assertTrue(self.page.locator('#exportButton').is_disabled())
        self.page.locator('nav [data-nav="ops_reports"]').click()
        expect(self.page.locator('[data-canonical-source-state="stale"]').first).to_be_visible()
        self.assertEqual(self.frozen_documents(), before)
        self.assertFalse(self.page.evaluate('() => HOTEL_OPS_REPORT.safety.pms_writes'))
        self.assertFalse(self.page.evaluate('() => HOTEL_OPS_REPORT.safety.payments'))
        self.page.locator('#resetButton').click()
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertEqual(self.page.locator('[data-canonical-source-state="stale"]').count(), 0)
        self.assertEqual(self.frozen_documents(), before)


if __name__ == '__main__':
    unittest.main()
