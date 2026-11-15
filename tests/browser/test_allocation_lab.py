"""Functional desktop/mobile keyboard checks of Python-precomputed hotel proposals."""
from pathlib import Path
import tempfile
import unittest

from playwright.sync_api import sync_playwright
from scripts.stage_demo_site import stage_site


class AllocationLabBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name) / "site"
        stage_site(self.site)
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda req: self.requests.append(req.url)
                     if req.url.startswith(("http:", "https:")) else None)
        self.page.goto((self.site / "allocation-lab.html").as_uri())

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.page.close()
        self.tmp.cleanup()

    def test_selection_calculate_explain_and_reset_buttons_work(self):
        p = self.page
        self.assertEqual(p.locator("#scenario option").count(), 6)
        self.assertFalse(p.locator("#outcome").is_visible())
        p.locator("#calculate").click()
        self.assertTrue(p.locator("#outcome").is_visible())
        self.assertIn("Öneri oluşturuldu", p.locator("#status").inner_text())
        self.assertEqual(p.locator("#proposal-list article.proposal").count(), 2)
        body = p.locator("#proposal-list").inner_text()
        self.assertIn("A_FLEX → D102", body)
        self.assertIn("B_TWIN → T101", body)
        p.locator("#explain").click()
        self.assertTrue(p.locator("#explanation").is_visible())
        self.assertEqual(p.locator("#explain").get_attribute("aria-expanded"), "true")
        self.assertIn("ALL_CONSTRAINTS_SATISFIED", p.locator("#reason-codes").inner_text())
        p.locator("#explain").click()
        self.assertFalse(p.locator("#explanation").is_visible())
        p.locator("#scenario").select_option("maintenance")
        self.assertFalse(p.locator("#outcome").is_visible())
        p.locator("#calculate").click()
        self.assertIn("Uygun ortak çözüm", p.locator("#status").inner_text())
        self.assertEqual(p.locator("#proposal-list article.proposal").count(), 0)
        p.locator("#reset").click()
        self.assertEqual(p.locator("#scenario").input_value(), "twin-scarcity")
        self.assertFalse(p.locator("#outcome").is_visible())
        self.assertTrue(p.locator("#scenario").evaluate("(node) => node === document.activeElement"))

    def test_manual_review_and_checkout_nonoverlap_cases(self):
        p = self.page
        for name, reason in (
            ("unknown-occupancy", "ROOM_READINESS_UNVERIFIED"),
            ("cancelled-hold", "HELD_ROOM_RELEASE_NOT_VERIFIED"),
        ):
            with self.subTest(name=name):
                p.locator("#scenario").select_option(name)
                p.locator("#calculate").click()
                self.assertIn("Personel incelemesi", p.locator("#status").inner_text())
                self.assertEqual(p.locator("#proposal-list article.proposal").count(), 0)
                p.locator("#explain").click()
                self.assertIn(reason, p.locator("#reason-codes").inner_text())
        p.locator("#scenario").select_option("checkout")
        p.locator("#calculate").click()
        self.assertEqual(p.locator("#proposal-list article.proposal").count(), 2)
        self.assertEqual(p.locator("#proposal-list").inner_text().count("D102"), 2)

    def test_keyboard_and_mobile_views(self):
        p = self.page
        for width in (320, 375, 390, 768, 1280):
            p.set_viewport_size({"width": width, "height": 900})
            with self.subTest(width=width):
                self.assertTrue(p.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertTrue(p.locator("#calculate").is_visible())
                self.assertTrue(p.locator("h1").is_visible())
        p.locator("#scenario").select_option("overlap")
        p.locator("#calculate").focus()
        p.keyboard.press("Enter")
        self.assertIn("Uygun ortak çözüm", p.locator("#status").inner_text())

    def test_from_main_and_overview_navigation_is_discoverable(self):
        self.page.goto((self.site / "index.html").as_uri())
        link = self.page.locator('a[href="allocation-lab.html"]')
        self.assertEqual(link.count(), 1)
        link.click()
        self.assertTrue(self.page.url.endswith("/allocation-lab.html"))
        self.page.goto((self.site / "project-overview.html").as_uri())
        self.assertEqual(self.page.locator('a[href="allocation-lab.html"]').count(), 1)


if __name__ == "__main__":
    unittest.main()
