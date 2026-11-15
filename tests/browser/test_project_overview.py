"""Showcase must distinguish the published demo from unmerged PR candidates.

All visual assets are local and explicitly staged; there is no fetch or JS.
"""
from pathlib import Path
import tempfile
import unittest

from playwright.sync_api import sync_playwright

from scripts.stage_demo_site import stage_site


class ProjectOverviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.site = Path(self.temp.name) / "site"
        stage_site(self.site)
        self.page = self.browser.new_page(viewport={"width": 1366, "height": 900})
        self.errors = []
        self.external_requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.external_requests.append(request.url)
                     if request.url.startswith(("http:", "https:")) else None)
        self.page.goto((self.site / "project-overview.html").as_uri())

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.external_requests, [])
        self.page.close()
        self.temp.cleanup()

    def test_visual_and_copy_are_grounded_in_shipped_and_candidate_status(self):
        page = self.page
        self.assertEqual(page.locator("h1").count(), 1)
        self.assertEqual(page.locator(".flow-step").count(), 4)
        self.assertEqual(page.locator(".metric").count(), 4)
        self.assertEqual(page.locator(".feature").count(), 5)
        self.assertTrue(page.locator(".hero-visual img").evaluate(
            "(img) => img.complete && img.naturalWidth > 0"))
        body = page.locator("main").inner_text()
        self.assertIn("Yayımlanmış v0.5.2 demoyu keşfet", body)
        self.assertIn("henüz ana sürüme birleştirilmediler", body)
        self.assertIn("Gerçek otel", body)
        self.assertIn("7 / 10", body)
        self.assertIn("English summary", body)
        hrefs = page.locator(".feature a").evaluate_all(
            "(elements) => elements.map(element => element.href)")
        for pr in (51, 53, 55, 58, 59):
            self.assertTrue(any(url.endswith("/pull/" + str(pr)) for url in hrefs))

    def test_responsive_and_navigation_are_accessible(self):
        page = self.page
        self.assertEqual(page.locator('nav.links a').count(), 4)
        for width in (320, 375, 390, 768, 1366):
            page.set_viewport_size({"width": width, "height": 900})
            with self.subTest(width=width):
                self.assertTrue(page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertTrue(page.locator("h1").is_visible())
                self.assertTrue(page.locator(".feature").first.is_visible())
        page.locator('a[href="#nasil"]').click()
        self.assertEqual(page.evaluate("location.hash"), "#nasil")

    def test_existing_demo_has_discoverable_overview_entry(self):
        page = self.page
        page.goto((self.site / "index.html").as_uri())
        link = page.locator(".kf-promo-entry a")
        self.assertEqual(link.count(), 1)
        self.assertEqual(link.get_attribute("href"), "project-overview.html")
        self.assertTrue(link.is_visible())


if __name__ == "__main__":
    unittest.main()
