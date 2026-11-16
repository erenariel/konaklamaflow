"""Chromium checks for Python-precomputed fictional room allocation lab."""
from pathlib import Path
import tempfile
import unittest

from playwright.sync_api import sync_playwright

from scripts.stage_demo_site import stage_site


class GlobalAllocationLabBrowserTests(unittest.TestCase):
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
        self.root = Path(self.temp.name) / "site"
        stage_site(self.root)
        self.page = self.browser.new_page(viewport={"width": 1200, "height": 850})
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("request", lambda req: self.requests.append(req.url)
                     if req.url.startswith(("http:", "https:")) else None)
        self.page.goto((self.root / "global-allocation-lab.html").as_uri())

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.page.close()
        self.temp.cleanup()

    def test_authentic_full_synthetic_results_and_controls(self):
        page = self.page
        self.assertEqual(page.locator("h1").count(), 1)
        panels = page.locator("[data-scenario-panel]")
        self.assertEqual(panels.count(), 4)
        for size in (18, 60, 200):
            with self.subTest(rooms=size):
                selector = page.locator(f'[data-scenario-button="{size}"]')
                selector.click()
                self.assertEqual(selector.get_attribute("aria-pressed"), "true")
                panel = page.locator(f'[data-scenario-panel="{size}"]')
                self.assertTrue(panel.is_visible())
                self.assertEqual(panel.locator("tbody tr:visible").count(), 0)  # collapsed details
                self.assertIn(f"{size} odalı kurgusal otel", panel.inner_text())
                self.assertIn("Tam öneri üretildi", panel.inner_text())
                self.assertIn(f"Tüm {size} oda önerisini göster",
                              panel.locator("summary").inner_text())
                panel.locator("summary").click()
                self.assertEqual(panel.locator("tbody tr").count(), size)
                self.assertEqual(page.locator(
                    '[data-scenario-panel]:visible').count(), 1)

        page.locator('[data-scenario-button="review"]').click()
        review = page.locator('[data-scenario-panel="review"]')
        self.assertTrue(review.is_visible())
        self.assertIn("Personel incelemesi gerekiyor", review.inner_text())
        self.assertIn("Öneri yok.", review.inner_text())
        self.assertEqual(review.locator("tbody tr").count(), 0)
        page.get_by_role("button", name="Sıfırla").click()
        self.assertTrue(page.locator('[data-scenario-panel="18"]').is_visible())
        self.assertEqual(page.locator('[data-scenario-button="18"]')
                         .get_attribute("aria-pressed"), "true")

    def test_mobile_keyboard_navigation_and_no_network(self):
        page = self.page
        for width in (320, 375, 390, 768, 1366):
            page.set_viewport_size({"width": width, "height": 850})
            with self.subTest(width=width):
                self.assertTrue(page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertTrue(page.locator("h1").is_visible())
                self.assertTrue(page.locator('[data-scenario-button="200"]').is_visible())
        page.set_viewport_size({"width": 390, "height": 850})
        button = page.locator('[data-scenario-button="60"]')
        button.focus()
        page.keyboard.press("Enter")
        self.assertEqual(button.get_attribute("aria-pressed"), "true")
        self.assertTrue(page.locator('[data-scenario-panel="60"]').is_visible())
        self.assertEqual(page.locator('input,textarea').count(), 0)
        self.assertEqual(page.locator('a[href^="https:"]').count(), 0)

    def test_workbench_overview_and_offline_zip_include_lab(self):
        page = self.page
        page.goto((self.root / "index.html").as_uri())
        self.assertEqual(page.locator(
            'a[href="global-allocation-lab.html"]').count(), 1)
        page.goto((self.root / "project-overview.html").as_uri())
        self.assertEqual(page.locator(
            'a[href="global-allocation-lab.html"]').count(), 1)
        self.assertTrue((self.root / "konaklamaflow-offline-demo.zip").exists())


if __name__ == "__main__":
    unittest.main()
