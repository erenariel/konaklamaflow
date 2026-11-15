"""The v0.5.2 review panel uses a precomputed fictional Python report, not Pyodide."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parents[2] / "demo" / "v04-integrated-preview.html"
LANGUAGES = ("tr", "en", "fr", "el", "he", "ar", "de", "ru", "es", "uk")


class ReviewProvenanceBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1366, "height": 900})
        self.errors, self.requests = [], []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.requests.append(request.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.page.close()

    def test_first_render_explains_three_real_precomputed_reasons(self):
        selected = self.page.evaluate("""() => INITIAL_EVALUATION.arrivals.find(
            r=>r.task_id===document.getElementById('v04Booking').value)""")
        self.assertEqual(selected["id"], "KF1002")
        self.assertEqual(self.page.locator("#v04Reasons code").all_inner_texts(), selected["blockers"])
        self.assertGreaterEqual(self.page.locator("#v04Evidence code").count(), 2)
        self.assertTrue(self.page.locator("#v04AIText").inner_text())
        self.assertIn("KF1002", self.page.locator("#v04SampleStatus").inner_text())
        self.assertIn("v0.5.2", self.page.locator("#v04Kicker").inner_text())
        self.assertIn("v0.5.2", self.page.locator("footer.footer").inner_text())

    def test_browser_accurately_identifies_precomputed_python_not_live_model(self):
        text = self.page.locator("#v04RuntimeNote").inner_text()
        self.assertIn("JavaScript", text)
        self.assertIn("Pyodide", text)
        self.assertIn("Python", self.page.locator("#v04Footer").inner_text())
        self.assertNotIn("v0.3 konsept", self.page.locator("footer.footer").inner_text())
        self.assertNotIn("gerçek kural raporunu incele", self.page.locator("#v04Sub").inner_text())
        self.assertEqual(self.page.evaluate("() => INITIAL_EVALUATION.mode"), "DRY_RUN_ONLY")
        self.assertEqual(self.page.evaluate("() => V04_CATALOG.sourceSha"),
                         self.page.evaluate("() => INITIAL_EVALUATION.snapshot_sha256"))

    def test_ten_locales_rtl_geometry_and_responsive_no_overflow(self):
        original = self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        for width in (320, 390, 768, 1366):
            self.page.set_viewport_size({"width": width, "height": 900})
            for lang in LANGUAGES:
                with self.subTest(lang=lang, width=width):
                    self.page.locator("#v04Locale").select_option(lang)
                    self.assertEqual(self.page.locator("#v04Global").get_attribute("dir"),
                                     "rtl" if lang in ("ar", "he") else "ltr")
                    self.assertEqual(self.page.locator("#v04Reasons code").count(),
                                     self.page.evaluate("""() => INITIAL_EVALUATION.arrivals.find(
                                         r=>r.task_id===document.getElementById('v04Booking').value).blockers.length"""))
                    self.assertGreaterEqual(self.page.locator("#v04Evidence code").count(), 2)
                    self.assertIn("v0.5.2", self.page.locator("#v04Kicker").inner_text())
                    self.assertIn("Pyodide", self.page.locator("#v04RuntimeNote").inner_text())
                    self.assertTrue(self.page.evaluate(
                        "() => document.documentElement.scrollWidth <= window.innerWidth"))
                    if lang in ("ar", "he"):
                        bounds = self.page.evaluate("""() => {
                            const a=document.querySelector('.v04-left').getBoundingClientRect();
                            const b=document.querySelector('.v04-right').getBoundingClientRect();
                            const horizontal=Math.min(a.right,b.right)-Math.max(a.left,b.left);
                            const vertical=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
                            return {
                                direction:getComputedStyle(document.querySelector('#v04Global')).direction,
                                overlapping:horizontal>2 && vertical>2
                            };
                        }""")
                        self.assertEqual(bounds["direction"], "rtl")
                        self.assertFalse(bounds["overlapping"], bounds)
        self.assertEqual(self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"), original)

    def test_static_fallback_is_not_blank_without_javascript(self):
        context = self.browser.new_context(java_script_enabled=False)
        try:
            page = context.new_page()
            page.set_content(HTML.read_text(encoding="utf-8"))
            self.assertTrue(page.locator("#v04Reasons").inner_text().strip())
            self.assertTrue(page.locator("#v04Evidence").inner_text().strip())
            self.assertIn("Kurgusal veri", page.locator(".topbar .date").inner_text())
            self.assertTrue(page.locator("#v04State").inner_text().strip())
            self.assertTrue(page.locator("#v04StaffText").inner_text().strip())
            self.assertTrue(page.locator("#v04Providers").inner_text().strip())
            self.assertIn("JavaScript", page.locator("#v04AIText").inner_text())
            self.assertIn("v0.5.2", page.locator("footer.footer").inner_text())
            page.close()
        finally:
            context.close()


if __name__ == "__main__":
    unittest.main()
