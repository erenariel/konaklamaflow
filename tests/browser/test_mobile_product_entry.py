"""Product-first mobile demo, offline translated entry, and manual scenario boundaries.

Checks the actual integrated page rather than a static marketing mockup.
"""
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "demo" / "v04-integrated-preview.html"
LOCALES = ("tr", "en", "fr", "el", "he", "ar", "de", "ru", "es", "uk")


class MobileProductEntryTests(unittest.TestCase):
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
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda err: self.errors.append(str(err)))
        self.page.on("request", lambda req: self.requests.append(req.url))
        self.page.set_content(PAGE.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.page.close()

    def test_first_screen_is_product_not_four_promotion_links(self):
        details = self.page.locator("#aboutProject")
        self.assertEqual(details.count(), 1)
        self.assertFalse(details.evaluate("(node) => node.open"))
        self.assertTrue(self.page.locator("#aiCommandCenter").is_visible())
        self.assertLess(self.page.locator("#aiCommandCenter").bounding_box()["y"],
                        details.bounding_box()["y"])
        self.assertEqual(details.locator("a").count(), 4)
        self.assertFalse(details.locator("a").first.is_visible())
        for width in (320, 375, 390, 430, 768):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 844})
                self.assertTrue(self.page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertLess(self.page.locator("#content").bounding_box()["y"],
                                details.bounding_box()["y"])
                self.assertTrue(self.page.locator("#startShowcase").is_visible())
        self.page.locator("#aboutProject summary").click()
        self.assertTrue(details.evaluate("(node) => node.open"))
        self.assertTrue(details.locator("a").first.is_visible())
        self.assertEqual(details.locator('a[href$=".pdf"]').count(), 0)
        self.assertEqual(details.locator('a[href*="privacy-vault"]').count(), 0)
        self.assertEqual(details.locator('a[href*="privacy-campaign"]').count(), 0)

    def test_all_ten_languages_translate_project_links_and_rtl(self):
        self.page.locator("#aboutProject summary").click()
        for locale in LOCALES:
            with self.subTest(locale=locale):
                self.page.locator("#globalLanguage").select_option(locale)
                expected = self.page.evaluate(
                    """(lang) => fullUiPhrases[lang].get('Proje hakkında ve indirmeler')""",
                    locale,
                )
                self.assertEqual(self.page.locator("#aboutProject summary").inner_text(),
                                 expected)
                for source in (
                    "Program modüllerini keşfet",
                    "Örnek rezervasyon senaryolarını gör",
                    "Oda tahsisini dene (18/60/200)",
                    "Çevrimdışı demoyu indir (ZIP)",
                ):
                    translated = self.page.evaluate(
                        "(args) => fullUiPhrases[args.lang].get(args.source)",
                        {"lang": locale, "source": source},
                    )
                    self.assertIn(translated, self.page.locator("#aboutProject").inner_text())
                self.assertEqual(self.page.locator("html").get_attribute("lang"), locale)
                self.assertEqual(self.page.locator("html").get_attribute("dir"),
                                 "rtl" if locale in ("ar", "he") else "ltr")
                self.assertTrue(self.page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                if locale in ("ar", "he"):
                    self.assertEqual(self.page.locator("#aboutProject summary").evaluate(
                        "(el) => getComputedStyle(el).direction"), "rtl")

    def test_workflow_ends_without_changing_selected_scenario(self):
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        self.page.locator("#wfScenario").select_option("room_block")
        first = self.page.locator("#wfScenario").input_value()
        self.page.locator("#wfPlay").click()
        self.assertTrue(self.page.evaluate("() => wfState.playing"))
        self.page.evaluate("() => { wfState.stage = wfScenarios[0].steps.length - 1; }")
        self.page.wait_for_function("() => !wfState.playing", timeout=6000)
        self.assertEqual(self.page.evaluate("() => wfState.scenario"), first)
        self.assertEqual(self.page.evaluate("() => wfState.stage"),
                         self.page.evaluate("() => wfScenarios[0].steps.length-1"))
        self.assertIn("SCENARIO COMPLETE", self.page.evaluate(
            "() => wfState.log.join(' ')"))
        self.page.locator("#wfNext").click()
        self.assertEqual(self.page.evaluate("() => wfState.scenario"), first)
        self.assertEqual(self.page.evaluate("() => wfState.stage"),
                         self.page.evaluate("() => wfScenarios[0].steps.length-1"))
        self.page.locator("#wfScenario").select_option("payment")
        self.assertEqual(self.page.evaluate("() => wfState.stage"), 0)
        self.assertFalse(self.page.evaluate("() => wfState.playing"))


if __name__ == "__main__":
    unittest.main()
