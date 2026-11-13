"""Full-page locale regression: all 18 modules, topbar and evidence share one language.

No external translator or sensitive data flows: catalog and UI are offline.
"""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "demo" / "v04-integrated-preview.html"
LOCALES = ("tr", "en", "fr", "el", "he", "ar", "de", "ru", "es", "uk")


class FullLanguageSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 980})
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda req: self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [], "JavaScript error in locale navigation")
        self.assertEqual(self.requests, [], "No translation or booking network access allowed")
        self.page.close()

    def test_every_locale_changes_all_twenty_nav_items_and_page_direction(self):
        self.assertEqual(self.page.locator('nav [data-nav]').count(), 20)
        self.assertEqual(self.page.locator('#globalLanguage').input_value(), "tr")
        for lang in LOCALES:
            self.page.locator('#globalLanguage').select_option(lang)
            with self.subTest(lang=lang):
                actual = self.page.locator('nav [data-nav]').all_inner_texts()
                expected = self.page.evaluate(
                    """() => fullUiMenu[opsState.lang]""")
                self.assertEqual([x.strip() for x in actual], expected)
                self.assertEqual(self.page.locator('html').get_attribute('lang'), lang)
                self.assertEqual(self.page.locator('html').get_attribute('dir'),
                                 'rtl' if lang in ('ar', 'he') else 'ltr')
                self.assertEqual(self.page.locator('#v04Locale').input_value(), lang)
                self.assertEqual(self.page.locator('#fullUiTranslationMarker').get_attribute('lang'), lang)

    def test_existing_core_modules_relabel_and_restore_turkish(self):
        self.page.locator('nav [data-nav="dashboard"]').click()
        self.page.locator('#globalLanguage').select_option("en")
        self.assertEqual(self.page.locator('#pagetitle').inner_text(), 'Overview')
        self.assertIn('Priority arrivals', self.page.locator('#content').inner_text())
        self.assertNotIn('Öncelikli girişler', self.page.locator('#content').inner_text())
        self.page.locator('nav [data-nav="ota"]').click()
        self.assertIn('Incoming OTA events', self.page.locator('#content').inner_text())
        self.page.locator('nav [data-nav="rooms"]').click()
        self.assertIn('Graphical room plan', self.page.locator('#content').inner_text())
        self.page.locator('#globalLanguage').select_option('de')
        self.assertIn('Grafischer Zimmerplan', self.page.locator('#content').inner_text())
        self.page.locator('#globalLanguage').select_option('tr')
        self.assertIn('Grafik oda planı', self.page.locator('#content').inner_text())
        self.assertEqual(self.page.locator('#pagetitle').inner_text(), 'Oda Planı')

    def test_all_report_options_are_translated_and_values_stay_stable(self):
        self.page.locator('nav [data-nav="ops_reports"]').click()
        before = self.page.evaluate("() => JSON.stringify(HOTEL_OPS_REPORT)")
        original_keys = self.page.locator('#opsReportType option').evaluate_all(
            '(nodes) => nodes.map(node => node.value)')
        self.assertEqual(len(original_keys), 32)
        for lang in LOCALES:
            self.page.locator('#globalLanguage').select_option(lang)
            with self.subTest(lang=lang):
                label = self.page.locator('#opsReportType option[value="monthly_revenue"]').inner_text()
                expected = self.page.evaluate(
                    """() => fullUiPhrases[opsState.lang].get('Aylık Detaylı Gelir')""")
                self.assertIn(expected, label)
                self.assertEqual(original_keys,
                    self.page.locator('#opsReportType option').evaluate_all(
                        '(nodes) => nodes.map(node => node.value)'))
                self.assertEqual(before,
                    self.page.evaluate("() => JSON.stringify(HOTEL_OPS_REPORT)"))

    def test_both_language_selectors_drive_whole_app(self):
        self.page.locator('#v04Locale').select_option('es')
        self.assertEqual(self.page.locator('#globalLanguage').input_value(), 'es')
        self.assertEqual(self.page.locator('html').get_attribute('lang'), 'es')
        self.assertEqual(self.page.locator('nav [data-nav="rooms"]').inner_text(),
                         'Plan de habitaciones')
        self.page.locator('#v04Locale').select_option('ar')
        self.assertEqual(self.page.locator('html').get_attribute('dir'), 'rtl')
        self.assertEqual(self.page.locator('#globalLanguage').input_value(), 'ar')
        self.assertEqual(self.page.locator('#v04Global').get_attribute('lang'), 'ar')

    def test_reservation_folio_and_guest_views_localize_without_mutating_bookings(self):
        old = self.page.evaluate('() => JSON.stringify(HOTEL_OPS_DATA)')
        for page in ('ops_reservations', 'ops_folios', 'ops_guests', 'ops_agencies'):
            self.page.locator('nav [data-nav="' + page + '"]').click()
            self.page.locator('#globalLanguage').select_option('fr')
            self.assertEqual(self.page.locator('#pagetitle').inner_text(),
                             self.page.evaluate('() => fullUiMenu.fr[PAGE_LIST.findIndex(row => row[0] === page)]'))
            self.assertTrue(self.page.locator('#content').inner_text())
        self.assertEqual(self.page.evaluate('() => JSON.stringify(HOTEL_OPS_DATA)'), old)

    def test_unsupported_locale_is_not_an_option_or_clandestine_machine_translation(self):
        self.assertEqual(self.page.locator('#globalLanguage option').count(), 10)
        raw = HTML.read_text(encoding='utf-8')
        self.assertIn("connect-src 'none'", raw)
        self.assertNotIn('translate.googleapis.com', raw)
        self.assertNotIn('fetch(', raw.split("// BEGIN GENERATED_FULL_UI_RUNTIME")[1].split("// END GENERATED_FULL_UI_RUNTIME")[0])

    def test_mobile_ltr_and_rtl_do_not_overflow(self):
        for lang in ('en', 'ar', 'he', 'ru'):
            self.page.locator('#globalLanguage').select_option(lang)
            for width in (320, 375, 390, 768, 1440):
                self.page.set_viewport_size({"width":width, "height":900})
                with self.subTest(lang=lang, width=width):
                    self.assertTrue(self.page.evaluate(
                        '() => document.documentElement.scrollWidth <= window.innerWidth'))


if __name__ == '__main__':
    unittest.main()
