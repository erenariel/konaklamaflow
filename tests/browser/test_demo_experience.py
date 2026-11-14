"""Measured regression gates for the v0.4 visual-preference starter.

These tests deliberately do not claim full WCAG2.2 conformance or complete
presentation-story implementation. They exercise the real offline HTML.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location('verify_demo_experience', ROOT / 'scripts/verify_demo_experience.py')
_VERIFIER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_VERIFIER)


class TestDemoExperience(unittest.TestCase):
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
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 900})
        self.errors = []
        self.requests = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.set_content((ROOT / 'demo/hotel-suite.html').read_text())

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])

    def test_visual_matrix_has_measured_readable_text_and_preserves_report(self):
        original = self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)')
        for theme in _VERIFIER.THEMES:
            self.page.locator('#kfTheme').select_option(theme)
            for mode in _VERIFIER.MODES:
                if self.page.locator('html').get_attribute('data-kf-mode') != mode:
                    self.page.locator('#kfMode').click()
                for width in _VERIFIER.WIDTHS:
                    with self.subTest(theme=theme, mode=mode, width=width):
                        self.page.set_viewport_size({'width': width, 'height': 900})
                        self.assertTrue(self.page.evaluate(
                            '() => document.documentElement.scrollWidth <= innerWidth'))
                        measured = [row for row in _VERIFIER.measure_text_contrast(self.page)
                                    if row['measured']]
                        self.assertGreaterEqual(len(measured), 12)
                        failures = [{key: row[key] for key in ('selector', 'ratio', 'minimum')}
                                    for row in measured if not row['pass']]
                        self.assertEqual(failures, [])
        self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)'), original)
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertFalse(self.page.locator('#exportButton').is_disabled())

    def test_visual_preferences_are_keyboard_operable_with_focus_indicator(self):
        theme = self.page.locator('#kfTheme')
        theme.focus()
        self.page.keyboard.press('ArrowUp')
        self.page.keyboard.press('Enter')
        self.assertEqual(theme.input_value(), 'dark')
        self.page.locator('#kfMode').press('Enter')
        expect(self.page.locator('html')).to_have_attribute('data-kf-mode', 'presentation')
        self.page.locator('#kfMotion').press('Enter')
        expect(self.page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        focused = self.page.locator('#kfMotion')
        self.assertTrue(focused.evaluate('(element) => element.matches(":focus-visible")'))
        self.assertGreaterEqual(focused.evaluate(
            '(element) => parseFloat(getComputedStyle(element).outlineWidth)'), 2)

    def test_presentation_navigation_reaches_all_modules_without_hidden_controls(self):
        original = self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)')
        self.page.locator('#kfMode').click()
        choice = self.page.locator('#kfModule')
        self.assertTrue(choice.is_visible())
        self.assertFalse(self.page.locator('.sidebar').is_visible())
        choice.focus()
        self.page.keyboard.press('Home')
        self.page.keyboard.press('ArrowDown')
        self.page.keyboard.press('Enter')
        self.assertEqual(choice.input_value(), 'arrivals')
        for module in ('dashboard', 'arrivals', 'ota', 'rooms', 'housekeeping',
                       'guest', 'tasks', 'revenue', 'ai', 'integrations'):
            choice.select_option(module)
            self.assertEqual(choice.input_value(), module)
            self.assertTrue(self.page.locator('#content').inner_text().strip(), module)
        self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)'), original)
        self.assertFalse(self.page.evaluate('() => reportStale'))

    def test_reduced_motion_is_manual_and_preserves_source_data(self):
        original = self.page.evaluate('() => JSON.stringify(INITIAL_DATA)')
        self.page.emulate_media(reduced_motion='reduce')
        expect(self.page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        expect(self.page.locator('#kfMotion')).to_be_disabled()
        self.page.locator('#startShowcase').click()
        expect(self.page.locator('#tourPanel')).to_have_attribute('data-playing', 'false')
        before = self.page.locator('#tourPanel').get_attribute('data-current-step')
        self.page.wait_for_timeout(2300)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'), before)
        self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_DATA)'), original)

    def test_manual_motion_off_stops_story_timer_and_survives_render_reset(self):
        self.page.locator('#startShowcase').click()
        expect(self.page.locator('#tourPanel')).to_have_attribute('data-playing', 'true')
        self.page.locator('#kfMotion').click()
        expect(self.page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        expect(self.page.locator('#tourPanel')).to_have_attribute('data-playing', 'false')
        before = self.page.locator('#tourPanel').get_attribute('data-current-step')
        self.page.wait_for_timeout(2300)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'), before)
        self.page.locator('#startShowcase').click()
        expect(self.page.locator('#tourPanel')).to_have_attribute('data-playing', 'false')
        self.page.locator('#resetButton').click()
        expect(self.page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        self.assertFalse(self.page.locator('#exportButton').is_disabled())

    def test_desktop_presentation_stage_is_16_by_9_and_keyboard_scrollable(self):
        self.page.locator('#kfMode').click()
        for width in (1100, 1280, 1440):
            self.page.set_viewport_size({'width': width, 'height': 900})
            stage = self.page.locator('#content')
            rect = stage.bounding_box()
            self.assertAlmostEqual(rect['width'] / rect['height'], 16 / 9, delta=.005)
            self.assertEqual(stage.get_attribute('role'), 'region')
            self.assertTrue(stage.get_attribute('aria-label'))
        stage.focus()
        stage.press('PageDown')
        self.page.wait_for_timeout(350)
        self.assertGreater(stage.evaluate('(element) => element.scrollTop'), 0)

    def test_200_percent_zoom_reflows_both_modes(self):
        self.page.evaluate("() => { document.body.style.zoom = '2'; }")
        for mode in _VERIFIER.MODES:
            if self.page.locator('html').get_attribute('data-kf-mode') != mode:
                self.page.locator('#kfMode').click()
            self.assertTrue(self.page.evaluate(
                '() => document.documentElement.scrollWidth <= innerWidth'), mode)
            self.assertTrue(self.page.locator('#kfMode').is_visible())
            self.assertTrue(self.page.locator('#kfTheme').is_visible())
