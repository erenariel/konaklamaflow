"""Integration tests: real offline hotel workbench with ten-language read-only explanation panel."""
from pathlib import Path
import json
import re
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "demo" / "v04-integrated-preview.html"
REPORT = json.loads((ROOT / "examples" / "operations-evaluation.json").read_text())
LANGS = ("tr", "en", "fr", "el", "he", "ar", "de", "ru", "es", "uk")


class V04WorkbenchPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.on("request", lambda req: self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.page.close()

    def test_actual_ten_module_workbench_remains_accessible(self):
        self.assertEqual(self.page.locator("nav [data-nav]").count(), 10)
        self.assertEqual(self.page.evaluate("() => INITIAL_EVALUATION"), REPORT)
        self.assertEqual(self.page.locator("#v04Booking option").count(),
                         len(REPORT["arrivals"]))
        self.assertEqual(self.page.evaluate("() => V04_CATALOG.sourceSha"),
                         REPORT["snapshot_sha256"])
        self.assertEqual(self.page.evaluate("() => V04_CATALOG.codes.length"), 26)
        self.assertEqual(self.page.evaluate("() => Object.keys(V04_CATALOG.evidence).length"), 26)
        self.assertFalse(self.page.evaluate("() => reportStale"))

    def test_ten_language_live_panel_relabels_without_altering_decisions(self):
        initial = self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        original_row = REPORT["arrivals"][0]
        self.assertEqual(self.page.locator("#v04Booking").input_value(), original_row["task_id"])
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.page.locator("#v04Locale").select_option(lang)
                self.assertEqual(self.page.locator("#v04Global").get_attribute("lang"), lang)
                self.assertEqual(self.page.locator("#v04Global").get_attribute("dir"),
                                 "rtl" if lang in ("ar", "he") else "ltr")
                expected = self.page.evaluate("""() => {
                    const r=INITIAL_EVALUATION.arrivals[0],i=V04_CATALOG.codes.indexOf(r.blockers[0]);
                    return V04_CATALOG.reasons[document.getElementById('v04Locale').value][i];
                }""")
                self.assertIn(expected, self.page.locator("#v04Reasons").inner_text())
                self.assertEqual(self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"),
                                 initial)
                self.assertTrue(self.page.locator("#v04TranslationStatus").inner_text())
                self.assertIn("DRY_RUN_ONLY", self.page.locator("#v04Global").inner_text())

    def test_evidence_fields_come_from_allowlisted_reason_codes(self):
        for row in REPORT["arrivals"]:
            self.page.locator("#v04Booking").select_option(row["task_id"])
            codes = self.page.locator("#v04Reasons code").all_inner_texts()
            self.assertEqual(codes, row["blockers"])
            expected_fields = self.page.evaluate("""taskId => {
                const row=INITIAL_EVALUATION.arrivals.find(r=>r.task_id===taskId);
                return [...new Set(row.blockers.flatMap(code=>V04_CATALOG.evidence[code]||[]))];
            }""", row["task_id"])
            self.assertEqual(self.page.locator("#v04Evidence code").all_inner_texts(),
                             expected_fields)
            self.assertEqual(self.page.evaluate("() => V04_CATALOG.sourceSha"),
                             REPORT["snapshot_sha256"])

    def test_ai_provider_badges_honestly_indicate_disconnected(self):
        self.assertEqual(self.page.locator("#v04Providers span").count(), 5)
        self.assertEqual(self.page.locator("#v04Providers span").all_inner_texts(),
                         [f"{name} · Bağlı değil" for name in (
                             "OpenAI API", "Anthropic API", "Google Gemini API",
                             "Azure OpenAI", "Self-hosted model")])
        self.assertNotIn("CONNECTED", self.page.locator("#v04Providers").inner_text())

    def test_visual_state_change_invalidates_read_only_explanations(self):
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.assertTrue(self.page.evaluate("() => reportStale"))
        self.assertTrue(self.page.locator("#v04Booking").is_disabled())
        self.assertEqual(self.page.locator("#v04Reasons code").count(), 0)
        self.assertIn("Veri değişti", self.page.locator("#v04State").inner_text())
        self.assertTrue(self.page.locator("#exportButton").is_disabled())
        self.page.locator("#resetButton").click()
        self.assertFalse(self.page.evaluate("() => reportStale"))
        self.assertFalse(self.page.locator("#v04Booking").is_disabled())

    def test_themes_presentation_mode_and_mobile_widths(self):
        self.page.locator("#kfTheme").select_option("night")
        self.page.locator("#kfMode").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-kf-mode"), "presentation")
        for lang in ("tr", "ar", "he", "de"):
            self.page.locator("#v04Locale").select_option(lang)
            for width in (320, 375, 768, 1440):
                self.page.set_viewport_size({"width": width, "height": 900})
                with self.subTest(lang=lang, width=width):
                    self.assertTrue(self.page.evaluate(
                        "() => document.documentElement.scrollWidth <= window.innerWidth"))

    def test_no_external_calls_no_second_python_engine_in_browser(self):
        text = HTML.read_text(encoding="utf-8")
        self.assertIn("connect-src 'none'", text)
        self.assertNotIn("api.openai.com", text)
        self.assertIsNone(re.search(
            r'function\s+(?:evaluate|eligible|proposal|overlaps)\s*\(', text))
        self.assertEqual(self.page.evaluate("() => INITIAL_EVALUATION.mode"), "DRY_RUN_ONLY")


if __name__ == "__main__":
    unittest.main()
