"""Mobile-first demo and 10-locale product-link/browser playback regressions."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML = Path(__file__).resolve().parents[2] / "demo" / "v04-integrated-preview.html"


class MobileProductFirstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 390, "height": 844})
        self.errors, self.requests = [], []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda req: self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [], "The demo must make zero network requests")
        self.page.close()

    def test_product_precedes_collapsed_project_links_on_small_phones(self):
        for width in (320, 375, 390, 430, 768):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 844})
                self.assertTrue(self.page.evaluate(
                    "() => document.documentElement.scrollWidth <= innerWidth"
                ))
                self.assertTrue(self.page.locator("#aiCommandCenter").is_visible())
                self.assertTrue(self.page.locator("#startShowcase").is_visible())
                self.assertLess(
                    self.page.locator("#startShowcase").bounding_box()["y"],
                    self.page.locator("#projectInfo").bounding_box()["y"],
                )
                self.assertLess(
                    self.page.locator("#aiCommandCenter").bounding_box()["y"],
                    self.page.locator("#projectInfo").bounding_box()["y"],
                )
                self.assertFalse(self.page.locator("#projectInfo").evaluate(
                    "(node) => node.open"
                ))
                self.assertFalse(self.page.locator(
                    '#projectInfo a[href="konaklamaflow-offline-demo.zip"]'
                ).is_visible())
        self.page.locator("#projectInfo summary").click()
        self.assertTrue(self.page.locator("#projectInfo").evaluate(
            "(node) => node.open"
        ))
        self.assertEqual(self.page.locator("#projectInfo a").count(), 4)
        self.assertTrue(self.page.locator(
            '#projectInfo a[href="global-allocation-lab.html"]'
        ).is_visible())
        about = self.page.locator("#projectInfo").inner_html().lower()
        self.assertNotIn("privacy-vault-lab.html", about)
        self.assertNotIn("otel-degerlendirmesi", about)
        self.assertNotIn("imzalı ve kaşeli", about)

    def test_optional_project_section_localizes_in_all_ten_languages(self):
        terms = {
            "tr": "Proje hakkında ve indirmeler",
            "en": "About the project and downloads",
            "fr": "À propos du projet et téléchargements",
            "el": "Σχετικά με το έργο και λήψεις",
            "he": "על הפרויקט והורדות",
            "ar": "حول المشروع والتنزيلات",
            "de": "Über das Projekt und Downloads",
            "ru": "О проекте и загрузки",
            "es": "Acerca del proyecto y descargas",
            "uk": "Про проєкт і завантаження",
        }
        self.page.locator("#projectInfo summary").click()
        for locale, expected in terms.items():
            with self.subTest(locale=locale):
                self.page.locator("#globalLanguage").select_option(locale)
                self.assertIn(expected, self.page.locator("#projectInfo summary").inner_text())
                self.assertEqual(
                    self.page.evaluate("document.documentElement.dir"),
                    "rtl" if locale in ("ar", "he") else "ltr",
                )
                self.assertEqual(
                    self.page.locator("#projectInfo summary").evaluate(
                        "(node) => getComputedStyle(node).direction"),
                    "rtl" if locale in ("ar", "he") else "ltr",
                )
                self.assertTrue(self.page.locator(
                    '#projectInfo a[href="konaklamaflow-offline-demo.zip"]'
                ).is_visible())
                self.assertTrue(self.page.evaluate(
                    "() => document.documentElement.scrollWidth <= innerWidth"
                ))
                self.assertNotIn(
                    "Program modüllerini keşfet",
                    self.page.locator("#projectInfo").inner_text()
                ) if locale != "tr" else None

    def test_play_controls_disclose_distinct_scopes(self):
        self.assertIn("4 senaryonun tamamını", self.page.locator("#commandPlay").inner_text())
        self.assertIn("Seçili senaryoyu oynat", self.page.locator("#tourPlay").inner_text())
        self.assertIn("sonraki senaryoya geçer",
                      self.page.locator(".ai-command-help").inner_text())
        self.page.locator("#globalLanguage").select_option("en")
        self.assertIn("all 4 scenarios", self.page.locator("#commandPlay").inner_text())
        self.assertIn("Play selected scenario", self.page.locator("#tourPlay").inner_text())
        self.assertIn("five steps", self.page.locator(".ai-command-help").inner_text())
        self.page.locator("#globalLanguage").select_option("ar")
        self.assertIn("السيناريوهات الأربعة", self.page.locator("#commandPlay").inner_text())

    def test_workflow_playback_stops_without_switching_scenario(self):
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        self.assertTrue(self.page.locator("#wfPlay").is_visible())
        original = self.page.locator("#wfScenario").input_value()
        self.page.locator("#wfPlay").click()
        self.assertTrue(self.page.evaluate("wfState.playing"))
        self.page.wait_for_function(
            "() => !wfState.playing && wfState.stage === wfScenarios[0].steps.length - 1",
            timeout=16000,
        )
        self.assertEqual(self.page.locator("#wfScenario").input_value(), original)
        self.assertIn("SCENARIO COMPLETE", self.page.evaluate("wfState.log.at(-1)"))
        self.assertEqual(self.page.evaluate("wfState.stage"), 4)


if __name__ == "__main__":
    unittest.main()
