"""Source-bound, offline graphical room control; no live availability claims."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import unittest
from copy import deepcopy

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / 'demo/v04-integrated-preview.html'
LOCALES = ('tr', 'en', 'fr', 'el', 'he', 'ar', 'de', 'ru', 'es', 'uk')


def replace_constant(document, name, value):
    match = re.search(r'\bconst\s+' + re.escape(name) + r'\s*=\s*', document)
    if match is None:
        raise AssertionError('Missing generated room-graph source')
    _, length = json.JSONDecoder().raw_decode(document[match.end():])
    return (document[:match.end()] + json.dumps(value, ensure_ascii=False)
            + document[match.end() + length:])


class AuroraRoomPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        cls.browser = cls.driver.chromium.launch(**options)
        cls.source = json.loads((ROOT / 'examples/canonical-hotel.json').read_text())

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
        self.open_rooms()

    def tearDown(self):
        self.assertEqual(self.snapshot(), self.original,
                         'Filters/navigation must preserve the source and Python reports')
        self.page.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.console_errors, [])
        self.assertEqual(self.requests, [], 'The room plan must remain entirely offline')

    def snapshot(self):
        return self.page.evaluate('''() => JSON.stringify({canonical:CANONICAL_DATA,
            review:INITIAL_EVALUATION,operations:HOTEL_OPS_DATA,
            reports:HOTEL_OPS_REPORT,graph:AURORA_ROOM_GRAPH})''')

    def open_rooms(self):
        self.page.locator('nav [data-nav="rooms"]').click()
        expect(self.page.locator('#auroraRoomPlan')).to_be_visible()

    def cards(self):
        return self.page.locator('#auroraRoomPlan .aurora-room-card')

    def use_source(self, source):
        """Render a Python-validated variant, without browser-side decisions."""
        from konaklamaflow.canonical_presentation import build_presentation
        from konaklamaflow.room_graph import build_room_graph
        from scripts.generate_hotel_ops_demo import embed as embed_operations
        from scripts.generate_suite_demo import embed as embed_review

        bundle = build_presentation(source)
        document = embed_review(HTML.read_text(encoding='utf-8'),
                                bundle['review_data'], bundle['review_report'])
        document = embed_operations(document, bundle['operations_data'], bundle['operations_report'])
        for name, value in (('CANONICAL_DATA', bundle['canonical']),
                            ('CANONICAL_LINKS', bundle['canonical_links']),
                            ('AURORA_ROOM_GRAPH', build_room_graph(source))):
            document = replace_constant(document, name, value)
        match = re.search(r'\bconst V04_CATALOG\s*=\s*', document)
        catalog, _ = json.JSONDecoder().raw_decode(document[match.end():])
        catalog['sourceSha'] = bundle['review_report']['snapshot_sha256']
        document = replace_constant(document, 'V04_CATALOG', catalog)
        self.page.goto('about:blank')
        self.page.set_content(document)
        self.original = self.snapshot()
        self.open_rooms()

    def test_all_cards_and_floors_match_python_canonical_projection(self):
        from konaklamaflow.room_graph import build_room_graph

        graph = build_room_graph(self.source)
        self.assertEqual(self.page.evaluate('() => AURORA_ROOM_GRAPH'), graph)
        expect(self.page.locator('#auroraRoomPlan')).to_have_attribute(
            'data-source-state', 'synthetic_snapshot')
        expected_floors = {str(room['floor']) for room in self.source['rooms']}
        self.assertEqual(set(self.page.locator('.aurora-floor').evaluate_all(
            '(nodes) => nodes.map(node => node.dataset.floor)')), expected_floors)
        self.assertEqual(self.cards().count(), len(self.source['rooms']))
        self.assertEqual(len(self.source['rooms']), 18)
        for room in graph['rooms']:
            card = self.page.locator(f'.aurora-room-card[data-room="{room["id"]}"]')
            with self.subTest(room=room['id']):
                self.assertEqual(card.get_attribute('data-occupancy'), room['occupancy_state'])
                self.assertEqual(card.get_attribute('data-housekeeping'), room['housekeeping'])
                self.assertEqual(card.get_attribute('data-assignment'), room['assignment_state'])
                self.assertEqual(json.loads(card.get_attribute('data-state-codes')), room['state_codes'])
                self.assertEqual(card.get_attribute('type'), 'button')
                self.assertNotEqual(card.get_attribute('draggable'), 'true')
                for axis in ('occupancy', 'housekeeping', 'allocation'):
                    self.assertTrue(card.locator(f'[data-axis="{axis}"]').inner_text().strip())
        # Graphical control is primary; the existing timeline remains available.
        self.assertTrue(self.page.evaluate('''() => Boolean(
            document.querySelector('#auroraRoomPlan').compareDocumentPosition(
                document.querySelector('.rack-panel')) & Node.DOCUMENT_POSITION_FOLLOWING)'''))

    def test_physical_occupancy_is_independent_of_housekeeping_and_holds(self):
        graph = self.page.evaluate('() => AURORA_ROOM_GRAPH')
        self.assertEqual(graph['physical_occupancy_source'], 'source_not_connected')
        # The supplied canonical scenario has arrivals but no checked-in evidence.
        self.assertTrue(all(room['occupancy_state'] == 'unknown' for room in graph['rooms']))
        self.assertTrue(any(room['assignment_state'] == 'assigned' for room in graph['rooms']))
        self.assertTrue(any(room['housekeeping'] == 'dirty' for room in graph['rooms']))
        for room in graph['rooms']:
            card = self.page.locator(f'.aurora-room-card[data-room="{room["id"]}"]')
            self.assertEqual(card.get_attribute('data-occupancy'), 'unknown')
            self.assertNotIn('occupied', json.loads(card.get_attribute('data-state-codes')))
        technical = self.page.locator('.aurora-room-card[data-room="401"]')
        self.assertIn('out_of_order', json.loads(technical.get_attribute('data-state-codes')))
        self.assertTrue(technical.locator('[data-axis="housekeeping"]').inner_text().strip())

    def test_filters_are_display_only_and_reset_restores_the_exact_room_set(self):
        rooms = self.page.evaluate('() => AURORA_ROOM_GRAPH.rooms')
        sample = next(room for room in rooms if room['floor'] == 2)
        self.page.locator('#auroraFloorFilter').select_option(str(sample['floor']))
        expected = {room['id'] for room in rooms if room['floor'] == sample['floor']}
        self.assertEqual(set(self.cards().evaluate_all('(nodes) => nodes.map(n => n.dataset.room)')), expected)
        self.page.locator('#auroraCategoryFilter').select_option(sample['category'])
        expected = {room['id'] for room in rooms
                    if room['floor'] == sample['floor'] and room['category'] == sample['category']}
        self.assertEqual(set(self.cards().evaluate_all('(nodes) => nodes.map(n => n.dataset.room)')), expected)
        self.page.locator('#auroraRoomSearch').fill('NO_SUCH_SYNTHETIC_ROOM')
        expect(self.cards()).to_have_count(0)
        self.page.locator('#auroraResetFilters').click()
        expect(self.cards()).to_have_count(18)
        self.assertEqual(self.page.locator('#auroraFloorFilter').input_value(), 'all')
        self.assertEqual(self.page.locator('#auroraCategoryFilter').input_value(), 'all')
        self.assertEqual(self.page.locator('#auroraRoomSearch').input_value(), '')

    def test_explicit_occupied_signal_stays_occupied_when_housekeeping_is_dirty(self):
        source = deepcopy(self.source)
        booking = next(row for row in source['reservations'] if row['id'] == 'KF1010')
        booking['arrival_state'] = 'checked_in'
        next(row for row in source['rooms'] if row['id'] == '201')['housekeeping'] = 'dirty'
        self.use_source(source)
        card = self.page.locator('.aurora-room-card[data-room="201"]')
        self.assertEqual(card.get_attribute('data-occupancy'), 'occupied')
        self.assertEqual(card.get_attribute('data-housekeeping'), 'dirty')
        states = json.loads(card.get_attribute('data-state-codes'))
        self.assertIn('occupied', states)
        self.assertNotIn('vacant_unverified', states)
        self.assertTrue(card.locator('[data-axis="occupancy"]').inner_text().strip())
        self.assertTrue(card.locator('[data-axis="housekeeping"]').inner_text().strip())

    def test_representative_solid_background_text_contrast_in_three_themes(self):
        from scripts.verify_demo_experience import CONTRAST_JS

        # Hero gradients remain a separate visual-review limitation. These
        # selectors measure the operating card/filter text on solid surfaces.
        selectors = ('.aurora-card-top strong', '.aurora-card-top small',
                     '.aurora-axis > span', '.aurora-axis b', '.aurora-room-capacity',
                     '.aurora-room-status', '.aurora-room-guest', '.aurora-room-foot',
                     '.aurora-filter', '.aurora-filter select', '.aurora-filter input',
                     '#auroraResetFilters')
        for theme in ('light', 'dark', 'night'):
            with self.subTest(theme=theme):
                self.page.locator('#kfTheme').select_option(theme)
                rows = self.page.evaluate(CONTRAST_JS, selectors)
                measured = [row for row in rows if row['measured']]
                self.assertGreaterEqual(len(measured), 20)
                failures = [{'selector': row['selector'], 'ratio': round(row['ratio'], 3),
                             'minimum': row['minimum']} for row in measured if not row['pass']]
                self.assertEqual(failures, [])

    def test_keyboard_room_selection_preserves_reservation_to_folio_identity(self):
        card = self.page.locator('.aurora-room-card[data-room="101"]')
        # Use genuine keyboard navigation: a preceding mouse click must not
        # accidentally make a programmatic-focus check test pointer modality.
        self.page.locator('#auroraResetFilters').focus()
        for _ in range(20):
            self.page.keyboard.press('Tab')
            if card.evaluate('(node) => node === document.activeElement'):
                break
        self.assertTrue(card.evaluate('(node) => node === document.activeElement'))
        self.assertTrue(card.evaluate('(node) => node.matches(":focus-visible")'))
        self.assertGreaterEqual(card.evaluate(
            '(node) => parseFloat(getComputedStyle(node).outlineWidth)'), 2)
        card.press('Enter')
        expect(self.page.locator('[data-aurora-room-detail="101"]')).to_be_visible()
        link = self.page.locator('#drawer .canonical-links[data-canonical-reservation-id="KF1001"]')
        expect(link).to_be_visible()
        link.locator('[data-canonical-action="folio"][data-folio-id="FOL-CAN-KF1001"]').click()
        folio = self.page.locator('[data-canonical-folio="FOL-CAN-KF1001"]')
        expect(folio).to_be_visible()
        self.assertEqual(folio.get_attribute('data-reservation-id'), 'KF1001')

    def test_missing_graph_fails_closed_without_inventing_rooms_or_claiming_connectivity(self):
        document = replace_constant(HTML.read_text(encoding='utf-8'), 'AURORA_ROOM_GRAPH', None)
        self.page.goto('about:blank')
        self.page.set_content(document)
        self.original = self.snapshot()
        self.open_rooms()
        expect(self.page.locator('#auroraRoomPlan')).to_have_attribute(
            'data-source-state', 'source_not_connected')
        expect(self.cards()).to_have_count(0)
        self.assertTrue(self.page.locator('#auroraRoomPlan').inner_text().strip())
        # A missing new projection must not delete historical/current routes.
        expect(self.page.locator('.rack-panel')).to_be_visible()

    def test_mismatched_source_hash_or_business_date_cannot_render_room_facts(self):
        graph = self.page.evaluate('() => AURORA_ROOM_GRAPH')
        for field, value in (('canonical_sha256', '0' * 64), ('as_of', '2026-11-13')):
            with self.subTest(field=field):
                mismatched = deepcopy(graph)
                mismatched[field] = value
                document = replace_constant(HTML.read_text(encoding='utf-8'),
                                            'AURORA_ROOM_GRAPH', mismatched)
                self.page.goto('about:blank')
                self.page.set_content(document)
                self.original = self.snapshot()
                self.open_rooms()
                expect(self.page.locator('#auroraRoomPlan')).to_have_attribute(
                    'data-source-state', 'source_not_connected')
                expect(self.cards()).to_have_count(0)
                expect(self.page.locator('.rack-panel')).to_be_visible()

    def test_housekeeping_simulation_marks_graph_stale_until_source_reset(self):
        before = self.snapshot()
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.open_rooms()
        expect(self.page.locator('#auroraRoomPlan')).to_have_attribute('data-source-state', 'stale')
        self.assertTrue(self.page.locator('#exportButton').is_disabled())
        self.assertEqual(self.snapshot(), before)
        self.page.locator('#resetButton').click()
        expect(self.page.locator('#auroraRoomPlan')).to_have_attribute(
            'data-source-state', 'synthetic_snapshot')

    def test_mobile_ten_language_rtl_themes_and_reduced_motion_preserve_source(self):
        self.page.emulate_media(reduced_motion='reduce')
        for width in (320, 375, 390):
            self.page.set_viewport_size({'width': width, 'height': 900})
            for locale in LOCALES:
                with self.subTest(width=width, locale=locale):
                    self.page.locator('#globalLanguage').select_option(locale)
                    expect(self.page.locator('html')).to_have_attribute(
                        'dir', 'rtl' if locale in ('ar', 'he') else 'ltr')
                    self.assertEqual(self.page.locator('#auroraRoomPlan h2').first.inner_text(),
                                     self.page.evaluate('(locale) => AURORA_ROOM_TEXT[locale].title', locale))
                    self.assertTrue(self.page.evaluate(
                        '() => document.documentElement.scrollWidth <= innerWidth'))
                    expect(self.cards()).to_have_count(18)
                    self.assertEqual(self.cards().first.evaluate(
                        '(node) => getComputedStyle(node).animationName'), 'none')
                    self.assertEqual(self.cards().first.evaluate(
                        '(node) => getComputedStyle(node).transitionDuration'), '0s')
        for theme in ('light', 'dark', 'night'):
            self.page.locator('#kfTheme').select_option(theme)
            expect(self.page.locator('html')).to_have_attribute('data-kf-theme', theme)
            self.assertTrue(self.page.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))

    def test_zoom_200_percent_preserves_room_filters_and_reflow_in_three_themes(self):
        # CSS zoom matches the existing visual audit; this is not an OS-level
        # magnifier or a claim of complete screen-reader/WCAG certification.
        self.page.set_viewport_size({'width': 1440, 'height': 1000})
        self.page.evaluate("() => { document.body.style.zoom = '200%'; }")
        sample = next(room for room in self.source['rooms'] if room['floor'] == 2)
        for theme in ('light', 'dark', 'night'):
            with self.subTest(theme=theme):
                self.page.locator('#kfTheme').select_option(theme)
                self.assertTrue(self.page.evaluate(
                    '() => document.documentElement.scrollWidth <= innerWidth'))
                expect(self.cards()).to_have_count(18)
                self.page.locator('#auroraFloorFilter').select_option('2')
                self.page.locator('#auroraRoomSearch').fill(sample['id'])
                expect(self.cards()).to_have_count(1)
                card = self.cards().first
                self.assertEqual(card.get_attribute('data-room'), sample['id'])
                card.click()
                expect(self.page.locator(
                    f'[data-aurora-room-detail="{sample["id"]}"]')).to_be_visible()
                self.page.keyboard.press('Escape')
                self.page.locator('#auroraResetFilters').click()
                expect(self.cards()).to_have_count(18)
                self.assertTrue(self.page.evaluate(
                    '() => document.documentElement.scrollWidth <= innerWidth'))


if __name__ == '__main__':
    unittest.main()
