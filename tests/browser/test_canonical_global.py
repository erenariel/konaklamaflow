"""The guided page must explain the same canonical booking facts as the workbench."""
from copy import deepcopy
from datetime import date, timedelta
import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / 'demo/global-presentation-concept.html'
STORY_IDS = {'twin': 'twin-review', 'hk': 'housekeeping-review',
             'ota': 'channel-review', 'ready': 'arrival-review'}
LOCALES = ('tr', 'en', 'fr', 'el', 'he', 'ar', 'de', 'ru', 'es', 'uk')


class CanonicalGlobalPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        cls.browser = cls.driver.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 920})
        self.errors, self.requests = [], []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.set_content(HTML.read_text(encoding='utf-8'))
        self.source = json.loads((ROOT / 'examples/canonical-hotel.json').read_text())

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])

    def test_source_hash_date_and_metrics_match_the_python_canonical_projection(self):
        from konaklamaflow.canonical import canonical_fingerprint, project_review
        from konaklamaflow.experience_engine import evaluate

        source = deepcopy(self.source)
        review = project_review(source)
        report = evaluate(review)
        shown = self.page.evaluate('() => CANONICAL_CONCEPT')
        self.assertEqual(shown['canonical_sha256'], canonical_fingerprint(source))
        self.assertEqual(shown['as_of'], review['as_of'])
        self.assertEqual(shown['arrivals'], report['arrivals'])
        self.assertEqual(shown['room_plan'], report['room_plan'])
        self.assertEqual(shown['metrics']['rooms'], len(source['rooms']))
        today = [r for r in review['reservations'] if r['arrival'] == review['as_of']
                 and r['status'] != 'checked_out']
        self.assertEqual(shown['metrics']['arrivals_today'], len(today))
        expected_blocked = sum(r['status'] == 'blocked' for r in report['arrivals']
                               if r['id'] in {b['id'] for b in today})
        self.assertEqual(shown['metrics']['blocked_today'], expected_blocked)
        self.assertEqual(self.page.locator('.app').get_attribute('data-canonical-source-state'),
                         'synthetic_snapshot')
        self.assertEqual(self.page.locator('#metricRooms').inner_text(), str(len(source['rooms'])))

    def test_each_story_uses_its_explicit_reservation_and_authoritative_result(self):
        data = self.page.evaluate('() => CANONICAL_CONCEPT')
        bookings = {row['id']: row for row in data['reservations']}
        for selection, story_id in STORY_IDS.items():
            self.page.locator('#scenario').select_option(selection)
            story = next(s for s in data['stories'] if s['id'] == story_id)
            with self.subTest(story=story_id):
                self.assertEqual(self.page.locator('#factBooking').inner_text(), story['booking_id'])
                self.assertEqual(self.page.locator('.hero').get_attribute('data-reservation-id'),
                                 story['booking_id'])
                self.assertEqual(self.page.locator('.hero').get_attribute('data-engine-status'),
                                 story['final_status'])
                self.assertEqual(self.page.locator('#factRoom').inner_text(),
                                 bookings[story['booking_id']]['room_id'] or '—')
                for code in story['reason_codes']:
                    self.assertIn(code, self.page.locator('#factRule').inner_text())
                self.assertNotIn('KF-2048', ' '.join(self.page.locator('.fact').all_inner_texts()))

    def test_room_timeline_has_no_invented_ids_or_unrelated_dates(self):
        data = self.page.evaluate('() => CANONICAL_CONCEPT')
        self.page.locator('#locale').select_option('en')
        self.assertEqual(self.page.locator('#rackCaption').inner_text(),
                         'Source assignments · not availability')
        self.assertEqual(self.page.locator('#legendHeld').inner_text(), 'Source assignment')
        room_ids = {row['id'] for row in self.source['rooms']}
        booking_ids = {row['id'] for row in self.source['reservations']}
        self.assertEqual(set(self.page.locator('.roomname').evaluate_all(
            '(nodes) => nodes.map(node => node.dataset.roomId)')), room_ids)
        expected_dates = [(date.fromisoformat(data['as_of']) + timedelta(days=i)).isoformat()
                          for i in range(-1, 6)]
        self.assertEqual(self.page.locator('#rack .day').evaluate_all(
            '(nodes) => nodes.map(node => node.dataset.date)'), expected_dates)
        cells = self.page.locator('#rack .cell').evaluate_all('''(nodes) => nodes.map(node => ({
            room:node.dataset.roomId,date:node.dataset.date,
            reservations:JSON.parse(node.dataset.reservationIds),technical:node.dataset.technical
        }))''')
        self.assertEqual(len(cells), len(room_ids) * 7)
        for cell in cells:
            self.assertIn(cell['room'], room_ids)
            self.assertIn(cell['date'], expected_dates)
            self.assertTrue(set(cell['reservations']) <= booking_ids)
        for row in data['timeline']['rows']:
            for cell in row['cells']:
                node = self.page.locator(f'.cell[data-room-id="{row["room_id"]}"][data-date="{cell["date"]}"]')
                self.assertEqual(node.get_attribute('data-current-day-hold'), str(cell['current_day_hold']).lower())
                self.assertEqual(node.get_attribute('data-technical'), str(cell['technical']).lower())

    def test_language_and_manual_playback_do_not_change_source_or_booking_facts(self):
        before = self.page.evaluate('() => JSON.stringify(CANONICAL_CONCEPT)')
        booking = self.page.locator('#factBooking').inner_text()
        self.page.emulate_media(reduced_motion='reduce')
        for locale in LOCALES:
            self.page.locator('#locale').select_option(locale)
            with self.subTest(locale=locale):
                expect(self.page.locator('html')).to_have_attribute('dir', 'rtl' if locale in ('ar', 'he') else 'ltr')
                self.assertEqual(self.page.locator('#factBooking').inner_text(), booking)
                self.page.locator('#play').click()
                self.assertFalse(self.page.evaluate('() => state.playing'))
                self.page.set_viewport_size({'width': 375, 'height': 844})
                self.assertTrue(self.page.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))
                self.assertEqual(self.page.evaluate('() => JSON.stringify(CANONICAL_CONCEPT)'), before)

    def test_missing_source_disables_playback_and_does_not_show_old_fabricated_facts(self):
        source = HTML.read_text(encoding='utf-8')
        left = source.index('// BEGIN GENERATED_CANONICAL_CONCEPT')
        right = source.index('// END GENERATED_CANONICAL_CONCEPT', left)
        source = source[:left] + '// BEGIN GENERATED_CANONICAL_CONCEPT\nconst CANONICAL_CONCEPT=null;\n' + source[right:]
        # A new document resets the original script's lexical const bindings.
        self.page.goto('about:blank')
        self.page.set_content(source)
        expect(self.page.locator('#play')).to_be_disabled()
        expect(self.page.locator('#guidedStart')).to_be_disabled()
        expect(self.page.locator('#heroTour')).to_be_disabled()
        self.assertEqual(self.page.locator('#factBooking').inner_text(), '—')
        self.assertEqual(self.page.locator('#metricRooms').inner_text(), '—')
        self.assertEqual(self.page.locator('#rack .cell').count(), 0)
        self.assertEqual(self.page.locator('.app').get_attribute('data-canonical-source-state'), 'missing_source')
