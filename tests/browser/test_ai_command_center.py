"""AI command center desktop/mobile regression — synthetic and offline only."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parents[2] / "demo" / "v04-integrated-preview.html"

class AICommandCenterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1366, "height": 768})
        self.errors, self.requests = [], []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("request", lambda req: self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.page.close()

    def test_start_screen_has_command_center_and_source_charts(self):
        self.assertEqual(self.page.evaluate("page"), "dashboard")
        self.assertEqual(self.page.locator("#aiCommandCenter").count(), 1)
        self.assertEqual(self.page.locator(".ai-chart-column").count(), 7)
        self.assertGreaterEqual(self.page.locator(".ai-chart-channel > div").count(), 3)
        self.assertIn("Mateo Costa", self.page.locator("#aiCommandCenter").inner_text())
        self.assertIn("KF1002", self.page.locator("#aiCommandCenter").inner_text())
        self.assertNotIn("KF1001", self.page.locator(".stay-bar strong").first.inner_text())

    def test_play_pause_advance_and_reset_in_dashboard(self):
        self.page.locator("#startShowcase").click()
        self.assertTrue(self.page.evaluate("storyStarted"))
        self.assertEqual(self.page.evaluate("page"), "dashboard")
        self.page.locator("#commandPause").click()
        self.assertFalse(self.page.evaluate("storyPlaying"))
        self.page.locator("#commandNext").click()
        self.assertEqual(self.page.evaluate("storyStep"), 1)
        self.page.locator("#commandReset").click()
        self.assertFalse(self.page.evaluate("storyStarted"))

    def test_locales_and_scrollable_navigation_and_workflow_select(self):
        for width in (390, 1024, 1366, 1440):
            self.page.set_viewport_size({"width": width, "height": 768})
            for lang in ("en", "ar", "de", "tr"):
                self.page.locator("#globalLanguage").select_option(lang)
                self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                self.assertEqual(self.page.locator("#aiCommandCenter").count(), 1)
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        labels = self.page.locator("#wfFlow option").all_inner_texts()
        self.assertEqual(len(labels), 14)
        self.assertTrue(all(x.strip() for x in labels))
        self.page.locator("#wfFlow").select_option("housekeeping")
        self.assertEqual(self.page.locator("#wfFlow").input_value(), "housekeeping")

if __name__ == "__main__":
    unittest.main()
