"""Actual-browser checks for the v0.5.2 fictional AI operations showcase.

Visual phases may change focus, captions and the displayed evidence count. They
must never manufacture new occupancy, approval or revenue decisions. Translation
smoke checks do not certify the semantic accuracy of draft catalogs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
INTEGRATED = ROOT / 'demo/v04-integrated-preview.html'
CONCEPT = ROOT / 'demo/global-presentation-concept.html'
REPORT = json.loads((ROOT / 'examples/operations-evaluation.json').read_text())
SNAPSHOT = json.loads((ROOT / 'examples/fictional-hotel.json').read_text())
LOCALES = ('tr', 'en', 'fr', 'el', 'he', 'ar', 'de', 'ru', 'es', 'uk')
DESKTOPS = ((1366, 768), (1440, 900), (1600, 900))
ACTOR_STAGES = {'ai1': 'source', 'rule_engine': 'rule_engine',
                'ai2': 'ai_insight', 'human': 'staff_approval'}


class MotionShowcaseTests(unittest.TestCase):
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
        self.errors, self.console_errors, self.requests = [], [], []
        self.load_document(INTEGRATED)

    def load_document(self, path):
        # set_content replaces the DOM but keeps global lexical bindings. A new
        # offline document needs a fresh page, like a real navigation.
        if hasattr(self, 'page'):
            self.page.close()
        self.page = self.browser.new_page(viewport={'width': 1366, 'height': 768})
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda message: self.console_errors.append(message.text)
                     if message.type == 'error' else None)
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.set_content(path.read_text(encoding='utf-8'))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [], 'No browser errors permitted')
        self.assertEqual(self.console_errors, [], 'No console/CSP errors permitted')
        self.assertEqual(self.requests, [], 'Both showcases must remain fully offline')

    def assert_report_unchanged(self, source=None):
        self.assertEqual(self.page.evaluate('() => INITIAL_EVALUATION'), REPORT)
        if source is not None:
            self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_DATA)'), source)
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertFalse(self.page.locator('#exportButton').is_disabled())
        self.assertEqual(self.page.evaluate('() => INITIAL_EVALUATION.mode'), 'DRY_RUN_ONLY')
        self.assertFalse(any(REPORT['approval_policy'][key]
                             for key in ('pms_writes', 'payments', 'kbs', 'guest_messages')))

    def test_desktop_overview_hero_and_source_metrics_remain_visible(self):
        ids = {booking['id'] for booking in SNAPSHOT['reservations']
               if booking['arrival'] == SNAPSHOT['as_of'] and booking['status'] != 'checked_out'}
        rows = [row for row in REPORT['arrivals'] if row['id'] in ids]
        expected_metrics = [str(len(ids)),
                            str(sum(booking['departure'] == SNAPSHOT['as_of']
                                    for booking in SNAPSHOT['reservations'])),
                            str(sum(room['housekeeping'] in ('dirty', 'in_progress')
                                    for room in SNAPSHOT['rooms'])),
                            str(sum(room['housekeeping'] in ('out_of_order', 'out_of_service')
                                    for room in SNAPSHOT['rooms'])),
                            str(sum(row['status'] == 'blocked' for row in rows))]
        for width, height in DESKTOPS:
            with self.subTest(width=width, height=height):
                self.page.set_viewport_size({'width': width, 'height': height})
                self.assertEqual(self.page.evaluate('() => page'), 'dashboard')
                expect(self.page.locator('#aiCommandCenter')).to_be_visible()
                self.assertEqual(self.page.locator('nav [data-nav]').count(), 20)
                self.assertEqual(self.page.locator('nav [data-nav="dashboard"]').get_attribute(
                    'aria-current'), 'page')
                self.assertTrue(self.page.evaluate(
                    '() => document.documentElement.scrollWidth <= innerWidth'))
                self.assertEqual(self.page.locator('.overview-metrics .metric strong').all_inner_texts(),
                                 expected_metrics)
                hero = self.page.locator('#aiCommandCenter').bounding_box()
                self.assertLess(hero['y'], height)
                self.assertGreater(hero['width'], 600)
                self.assert_report_unchanged()

    def test_flow_updates_real_evidence_and_room_focus_without_new_decisions(self):
        source = self.page.evaluate('() => JSON.stringify(INITIAL_DATA)')
        initial_metrics = self.page.locator('.overview-metrics .metric strong').all_inner_texts()
        chart_source = self.page.locator('.ai-chart-column').evaluate_all(
            '(nodes) => nodes.map(node => [node.dataset.date, node.dataset.sourceCount])')
        self.assertEqual(len(chart_source), 7)
        for _, count in chart_source:
            self.assertTrue(count.isdecimal())
        story = self.page.evaluate('() => currentStory()')
        seen_stages = set()
        for index, step in enumerate(story['steps']):
            self.page.locator('#commandNext').click()
            expected_stage = ACTOR_STAGES[step['actor']]
            with self.subTest(step=index, stage=expected_stage):
                expect(self.page.locator('#aiCommandCenter')).to_have_attribute(
                    'data-scene-step', str(index))
                expect(self.page.locator('#aiCommandCenter')).to_have_attribute(
                    'data-active-stage', expected_stage)
                active = self.page.locator('.ai-flow-node.is-active')
                self.assertEqual(active.count(), 1)
                self.assertEqual(active.get_attribute('data-flow-stage'), expected_stage)
                self.assertEqual(active.get_attribute('aria-current'), 'step')
                self.assertEqual(self.page.locator('#commandEvidenceCount').inner_text().strip(),
                                 str(len(step['evidence'])))
                details = self.page.locator('#aiCommandCenter details')
                if details.count():
                    details.locator('summary').press('Enter')
                evidence_values = self.page.locator(
                    '#aiCommandCenter [data-source-value]').evaluate_all(
                    '(nodes) => nodes.map(node => node.dataset.sourceValue)')
                self.assertEqual(evidence_values, [str(item['value']) for item in step['evidence']])
                self.assertEqual(self.page.locator('.ai-evidence-card').count(),
                                 min(3, len(step['evidence'])))
                highlighted = self.page.locator('.rack-row.evidence-highlight').evaluate_all(
                    '(nodes) => nodes.map(node => node.dataset.rackRoom)')
                self.assertEqual(set(highlighted), set(step['room_ids']))
                self.assertEqual(self.page.locator('.overview-metrics .metric strong').all_inner_texts(),
                                 initial_metrics)
                self.assertEqual(self.page.locator('.ai-chart-column').evaluate_all(
                    '(nodes) => nodes.map(node => [node.dataset.date, node.dataset.sourceCount])'),
                    chart_source)
                self.assert_report_unchanged(source)
                seen_stages.add(expected_stage)
        self.assertEqual(seen_stages, set(ACTOR_STAGES.values()))
        prior_rooms = set(highlighted)
        self.page.locator('#tourScenario').select_option('housekeeping-review')
        self.page.locator('#commandNext').click()
        new_rooms = set(self.page.locator('.rack-row.evidence-highlight').evaluate_all(
            '(nodes) => nodes.map(node => node.dataset.rackRoom)'))
        self.assertEqual(new_rooms, {'303'})
        self.assertNotEqual(new_rooms, prior_rooms)
        self.assert_report_unchanged(source)

    def test_ten_locales_relabel_new_hero_without_claiming_live_connectivity(self):
        original = self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)')
        titles = {}
        turkish_narrative = []
        for locale in LOCALES:
            self.page.locator('#globalLanguage').select_option(locale)
            self.page.locator('#commandReset').click()
            with self.subTest(locale=locale):
                self.assertEqual(self.page.locator('html').get_attribute('lang'), locale)
                self.assertEqual(self.page.locator('html').get_attribute('dir'),
                                 'rtl' if locale in ('ar', 'he') else 'ltr')
                self.assertEqual(self.page.locator('#v04Locale').input_value(), locale)
                title = self.page.locator('#aiCommandCenter h2').inner_text().strip()
                self.assertTrue(title)
                titles[locale] = title
                self.assertTrue(self.page.locator('#commandRooms').inner_text().strip())
                self.assertTrue(self.page.locator('#commandReports').inner_text().strip())
                self.assertEqual(self.page.locator('.ai-flow-node').count(), 4)
                self.assertTrue(all(text.strip() for text in
                                    self.page.locator('.ai-flow-node').all_inner_texts()))
                self.assertTrue(self.page.locator('.ai-status-ticker').inner_text().strip())
                self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)'),
                                 original)
                self.assertIn(self.page.evaluate('() => commandText(15)'),
                              self.page.locator('#aiCommandCenter').inner_text())
                self.assertEqual(self.page.locator('.ai-status-ticker').get_attribute(
                    'data-simulated'), 'true')
                self.assertEqual(self.page.locator(
                    '#aiCommandCenter [data-ai-mode="mock_demo"]').count(), 1)
                # Isolate the whole ratio, not its separate numerals: RTL can
                # otherwise paint 0/5 as 5/0 while DOM text remains unchanged.
                ratio = self.page.locator('#commandProgressCount bdi')
                expect(ratio).to_have_attribute('dir', 'ltr')
                self.assertEqual(ratio.evaluate(
                    '(element) => getComputedStyle(element).direction'), 'ltr')
                self.assertEqual(ratio.evaluate(
                    '(element) => getComputedStyle(element).unicodeBidi'), 'isolate')
                caption_ratios = self.page.locator(
                    '#aiCommandCenter .ai-command-main > .ai-command-caption bdi')
                self.assertEqual(caption_ratios.count(), 2)
                self.assertTrue(all(value == 'ltr' for value in caption_ratios.evaluate_all(
                    '(nodes) => nodes.map(node => getComputedStyle(node).direction)')))
                narrative = [(self.page.locator('#aiCommandCenter h3[aria-live]').inner_text(),
                              self.page.locator('.ai-command-description').inner_text())]
                for _ in range(5):
                    self.page.locator('#commandNext').click()
                    narrative.append((
                        self.page.locator('#aiCommandCenter h3[aria-live]').inner_text(),
                        self.page.locator('.ai-command-description').inner_text()))
                if locale == 'tr':
                    turkish_narrative = narrative
                else:
                    for index, (heading, body) in enumerate(narrative):
                        self.assertTrue(heading.strip())
                        self.assertTrue(body.strip())
                        self.assertNotEqual((heading, body), turkish_narrative[index],
                                            (locale, index, 'New hero text must relabel'))
                self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)'),
                                 original)
        self.assertEqual(len(set(titles.values())), len(LOCALES))

    def test_mobile_ltr_rtl_new_hero_controls_do_not_overflow(self):
        for locale in ('en', 'ar', 'he', 'de'):
            self.page.locator('#globalLanguage').select_option(locale)
            for width in (375, 390):
                with self.subTest(locale=locale, width=width):
                    self.page.set_viewport_size({'width': width, 'height': 844})
                    self.assertTrue(self.page.evaluate(
                        '() => document.documentElement.scrollWidth <= innerWidth'))
                    expect(self.page.locator('#commandPlay')).to_be_visible()
                    expect(self.page.locator('#commandRooms')).to_be_visible()
                    expect(self.page.locator('#commandReports')).to_be_visible()
                    self.assert_report_unchanged()

    def test_manual_motion_off_stops_tour_and_ticker_without_changing_source(self):
        self.page.clock.install()
        source = self.page.evaluate('() => JSON.stringify(INITIAL_DATA)')
        self.page.locator('#commandPlay').click()
        self.assertTrue(self.page.evaluate('() => storyPlaying'))
        self.page.clock.fast_forward(1801)
        self.assertEqual(self.page.evaluate('() => storyStep'), 1)
        self.page.locator('#kfMotion').click()
        expect(self.page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        self.assertFalse(self.page.evaluate('() => storyPlaying'))
        before = self.page.evaluate('() => [selectedStoryId, storyStep]')
        self.page.clock.fast_forward(20000)
        self.assertEqual(self.page.evaluate('() => [selectedStoryId, storyStep]'), before)
        self.assertFalse(self.page.locator('#aiCommandCenter').evaluate(
            '(element) => element.getAnimations({subtree:true}).some(a => a.playState === "running")'))
        self.page.locator('#commandNext').click()
        self.assertEqual(self.page.evaluate('() => storyStep'), before[1] + 1)
        self.assert_report_unchanged(source)

    def test_os_reduced_motion_takes_priority_and_never_autoplays(self):
        self.page.clock.install()
        self.page.emulate_media(reduced_motion='reduce')
        expect(self.page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        expect(self.page.locator('#kfMotion')).to_be_disabled()
        self.page.locator('#commandPlay').click()
        self.assertFalse(self.page.evaluate('() => storyPlaying'))
        step = self.page.evaluate('() => storyStep')
        self.page.clock.fast_forward(20000)
        self.assertEqual(self.page.evaluate('() => storyStep'), step)
        self.assertFalse(self.page.locator('#aiCommandCenter').evaluate(
            '(element) => element.getAnimations({subtree:true}).some(a => a.playState === "running")'))
        self.assert_report_unchanged()

    def test_new_ctas_use_existing_read_only_navigation_and_stale_gate(self):
        self.page.locator('#commandRooms').press('Enter')
        self.assertEqual(self.page.evaluate('() => page'), 'rooms')
        self.page.locator('nav [data-nav="dashboard"]').click()
        self.page.locator('#commandReports').press('Enter')
        self.assertEqual(self.page.evaluate('() => page'), 'ops_reports')
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.page.locator('nav [data-nav="dashboard"]').click()
        self.assertTrue(self.page.evaluate('() => reportStale'))
        expect(self.page.locator('#commandPlay')).to_be_disabled()
        expect(self.page.locator('#commandNext')).to_be_disabled()
        expect(self.page.locator('#exportButton')).to_be_disabled()
        expect(self.page.locator('#aiCommandCenter')).to_have_attribute(
            'data-source-stale', 'true')
        self.assertEqual(self.page.locator('#commandEvidenceCount').get_attribute('data-value'), '0')
        self.assertEqual(self.page.locator('#commandEvidenceDetails').count(), 0)
        self.assertEqual(self.page.locator('.ai-flow-node.is-active').count(), 0)
        before = self.page.evaluate('() => storyStep')
        self.page.clock.install()
        self.page.clock.fast_forward(20000)
        self.assertEqual(self.page.evaluate('() => storyStep'), before)

    def test_presentation_concept_new_hero_ctas_and_localization(self):
        self.load_document(CONCEPT)
        for locale in LOCALES:
            self.page.locator('#locale').select_option(locale)
            with self.subTest(locale=locale):
                self.assertEqual(self.page.locator('html').get_attribute('dir'),
                                 'rtl' if locale in ('ar', 'he') else 'ltr')
                labels = self.page.evaluate('() => heroLabels[state.lang]')
                self.assertEqual(self.page.locator('#heroTourText').inner_text(), labels['play'])
                self.assertEqual(self.page.locator('#heroRooms').inner_text(), labels['rooms'])
                self.assertEqual(self.page.locator('#heroReports').inner_text(), labels['reports'])
                self.assertIn('MOCK_DEMO', self.page.locator('#heroMockBadge').inner_text())
        self.page.locator('#heroTour').click()
        self.assertTrue(self.page.evaluate('() => state.playing && state.guided'))
        self.page.locator('#play').click()
        self.assertFalse(self.page.evaluate('() => state.playing'))
        self.page.locator('#heroRooms').click()
        expect(self.page.locator('#rackPanel')).to_be_focused()
        for width, height in (*DESKTOPS, (375, 844), (390, 844)):
            self.page.set_viewport_size({'width': width, 'height': height})
            with self.subTest(width=width, height=height):
                self.assertTrue(self.page.evaluate(
                    '() => document.documentElement.scrollWidth <= innerWidth'))

    def test_presentation_concept_motion_preferences_disable_decorative_activity(self):
        self.load_document(CONCEPT)
        self.page.clock.install()
        self.page.locator('#heroTour').click()
        self.page.locator('#motion').click()
        expect(self.page.locator('html')).to_have_attribute('data-motion', 'off')
        self.assertFalse(self.page.evaluate('() => state.playing || state.guided'))
        before = self.page.evaluate('() => [state.story, state.step]')
        self.page.clock.fast_forward(30000)
        self.assertEqual(self.page.evaluate('() => [state.story, state.step]'), before)
        self.assertFalse(self.page.locator('.hero').evaluate(
            '(element) => element.getAnimations({subtree:true}).some(a => a.playState === "running")'))
        self.page.emulate_media(reduced_motion='reduce')
        expect(self.page.locator('#motion')).to_be_disabled()
        self.page.locator('#heroTour').click()
        self.assertFalse(self.page.evaluate('() => state.playing || state.guided'))
        self.assertEqual(self.page.locator('html').get_attribute('data-motion'), 'off')
