"""Smoke tests for the stand-alone international presentation concept.

This file does not assert translation accuracy or production integration.
It verifies only synthetic, offline interactive behaviour of the concept.
"""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "demo" / "global-presentation-concept.html"
LANGUAGES = ("tr", "en", "fr", "el", "he", "ar", "de", "ru", "es", "uk")
RTL = {"ar", "he"}


class GlobalPresentationConceptBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 920})
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda err: self.errors.append(str(err)))
        self.page.on("request", lambda request: self.requests.append(request.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"), wait_until="load")

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])  # no external calls or internal fetches
        self.page.close()

    def test_ten_languages_and_right_to_left(self):
        for code in LANGUAGES:
            with self.subTest(locale=code):
                self.page.locator("#locale").select_option(code)
                self.assertEqual(self.page.locator("html").get_attribute("lang"), code)
                self.assertEqual(self.page.locator("html").get_attribute("dir"), "rtl" if code in RTL else "ltr")
                self.assertTrue(self.page.locator("#heading").inner_text().strip())
                self.assertTrue(self.page.locator("#heroTitle").inner_text().strip())

    def test_all_ten_locales_have_complete_scripted_story_contract(self):
        catalog = self.page.evaluate("""() => Object.fromEntries(Object.entries(locales).map(
            ([id, value]) => [id, {
                keys: Object.keys(value).sort(),
                stories: Object.keys(value.stories).sort(),
                steps: value.steps.length,
                message_steps: value.stepMessages.length,
                complete: Object.values(value).every(v => v !== null && v !== '')
            }]
        ))""")
        self.assertEqual(set(catalog), set(LANGUAGES))
        reference = catalog["en"]["keys"]
        for language, data in catalog.items():
            with self.subTest(language=language):
                self.assertEqual(data["keys"], reference)
                self.assertEqual(data["stories"], ["hk", "ota", "ready", "twin"])
                self.assertEqual(data["steps"], 5)
                self.assertEqual(data["message_steps"], 5)
                self.assertTrue(data["complete"])

    def test_accessible_controls_and_room_dates_localize(self):
        for language in LANGUAGES:
            self.page.locator("#locale").select_option(language)
            labels = self.page.evaluate("""() => ({
                scenario: document.querySelector('#scenario').getAttribute('aria-label'),
                next: document.querySelector('#next').getAttribute('aria-label'),
                actual: accessibleLabels[state.lang].next,
                room: document.querySelector('#rack .cell').getAttribute('aria-label')
            })""")
            with self.subTest(language=language):
                self.assertEqual(labels["next"], labels["actual"])
                self.assertTrue(labels["scenario"])
                self.assertTrue(labels["room"])
                self.assertNotIn("Room 101, 13 November", labels["room"])
        self.page.locator("#next").click()
        self.assertEqual(self.page.locator("#progress").get_attribute("aria-valuenow"), "2")

    def test_themes_and_presentation_mode(self):
        for theme in ("light", "dark", "night"):
            self.page.locator("#theme").select_option(theme)
            self.assertEqual(self.page.locator("html").get_attribute("data-theme"), theme)
        self.page.locator("#mode").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-mode"), "presentation")
        self.page.locator("#mode").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-mode"), "operator")

    def test_speed_and_manual_motion_are_decision_neutral(self):
        before = self.page.locator("#factRule").inner_text()
        self.page.locator("#speed").select_option("2")
        self.assertEqual(self.page.evaluate("() => state.speed"), 2)
        self.page.locator("#play").click()
        self.assertTrue(self.page.evaluate("() => state.playing"))
        self.page.locator("#speed").select_option("1.5")
        self.assertEqual(self.page.evaluate("() => state.speed"), 1.5)
        self.assertTrue(self.page.evaluate("() => state.playing"))
        self.page.locator("#motion").click()
        self.assertFalse(self.page.evaluate("() => state.playing"))
        self.assertEqual(self.page.locator("html").get_attribute("data-motion"), "off")
        self.assertEqual(self.page.locator("#motion").get_attribute("aria-pressed"), "true")
        old_step = self.page.evaluate("() => state.step")
        self.page.locator("#play").click()
        self.assertEqual(self.page.evaluate("() => state.step"), old_step + 1)
        self.assertFalse(self.page.evaluate("() => state.playing"))
        self.assertEqual(self.page.locator("#factRule").inner_text(), before)
        self.page.locator("#motion").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-motion"), "on")

    def test_playback_accessibility_labels_for_all_ten_languages(self):
        for language in LANGUAGES:
            self.page.locator("#locale").select_option(language)
            with self.subTest(language=language):
                actual = self.page.locator("#speed").get_attribute("aria-label")
                self.assertEqual(actual, self.page.evaluate(
                    "() => playbackLabels[state.lang].speed"))
                self.assertEqual(self.page.locator("#motion").get_attribute("aria-label"),
                                 self.page.evaluate("() => playbackLabels[state.lang].on"))
        self.page.emulate_media(reduced_motion="reduce")
        # Wait for the media-query change listener without CSP-unsafe string eval.
        self.page.locator('html[data-motion="off"]').wait_for(state="attached", timeout=5000)
        self.assertTrue(self.page.locator("#motion").is_disabled())
        self.page.locator("#play").click()
        self.assertFalse(self.page.evaluate("() => state.playing"))

    def test_four_scripted_stories(self):
        for story in ("twin", "hk", "ota", "ready"):
            with self.subTest(story=story):
                self.page.locator("#scenario").select_option(story)
                self.assertTrue(self.page.locator("#heroTitle").inner_text())
                for _ in range(4):
                    self.page.locator("#next").click()
                self.assertTrue(self.page.locator("#next").is_disabled())

    def test_responsive_no_body_overflow(self):
        for width in (320, 375, 390, 768, 1440):
            self.page.set_viewport_size({"width": width, "height": 900})
            with self.subTest(width=width):
                self.assertTrue(self.page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"
                ))

    def test_document_explicitly_avoids_live_operations(self):
        raw = HTML.read_text(encoding="utf-8")
        self.assertIn("connect-src 'none'", raw)
        self.assertIn("default-src 'none'", raw)
        self.assertNotIn("fetch(", raw)
        self.assertNotIn("localStorage.setItem", raw)


if __name__ == "__main__":
    unittest.main()
