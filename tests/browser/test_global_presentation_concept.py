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

    def test_themes_and_presentation_mode(self):
        for theme in ("light", "dark", "night"):
            self.page.locator("#theme").select_option(theme)
            self.assertEqual(self.page.locator("html").get_attribute("data-theme"), theme)
        self.page.locator("#mode").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-mode"), "presentation")
        self.page.locator("#mode").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-mode"), "operator")

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
