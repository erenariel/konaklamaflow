"""End-to-end tests for integrated 18-room hotel workbench and 32 reports.

All data synthetic; no user passport, payment gateway or booking API calls.
"""
from pathlib import Path
import json
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
HTML=ROOT/"demo/v04-integrated-preview.html"
SAMPLE=json.loads((ROOT/"examples/hotel-operations-fictional.json").read_text(encoding="utf-8"))
from konaklamaflow.hotel_ops import build_operations_report


class TestIntegratedHotelOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start()
        cls.browser=cls.p.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()

    def setUp(self):
        self.page=self.browser.new_page(viewport={"width":1440,"height":1000})
        self.errors=[];self.requests=[]
        self.page.on("pageerror",lambda error:self.errors.append(str(error)))
        self.page.on("request",lambda req:self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors,[])
        self.assertEqual(self.requests,[])
        self.page.close()

    def nav(self,id):
        self.page.locator('nav [data-nav="'+id+'"]').click()

    def test_room_plan_is_entrypoint_and_new_menus_are_real(self):
        self.assertEqual(self.page.evaluate("() => page"),"rooms")
        self.assertEqual(self.page.locator("nav [data-nav]").count(),18)
        self.assertTrue(self.page.locator('nav [data-nav="ops_folios"]').is_visible())
        self.assertTrue(self.page.locator("#globalLanguage").is_visible())
        self.assertEqual(self.page.locator("#globalLanguage").input_value(),"tr")

    def test_python_generated_report_exactly_matches_browser_data(self):
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_DATA"),SAMPLE)
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_REPORT"),build_operations_report(SAMPLE))
        self.assertEqual(self.page.evaluate("() => Object.keys(HOTEL_OPS_REPORT.reports).length"),32)
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_REPORT.safety.guest_identity_data"),False)

    def test_folios_show_revenue_postings_payments_and_agency_debt(self):
        self.nav("ops_folios")
        self.assertIn("FOL-001",self.page.locator("#content").inner_text())
        self.assertIn("RESTAURANT",self.page.locator("#content").inner_text())
        self.assertIn("75,00",self.page.locator("#content").inner_text())
        self.nav("ops_agencies")
        self.assertIn("Demo Booking Travel",self.page.locator("#content").inner_text())
        self.assertNotIn("FOL-003",self.page.locator("#content").inner_text())

    def test_all_32_reports_can_be_selected_missing_sources_are_visible(self):
        self.nav("ops_reports")
        self.assertEqual(self.page.locator("#opsReportType option").count(),32)
        self.page.locator("#opsReportType").select_option("posting_invoice")
        self.page.locator('[data-op-action="apply-report"]').click()
        self.assertIn("RESTAURANT",self.page.locator("#content").inner_text())
        self.page.locator("#opsReportType").select_option("trial_balance")
        self.page.locator('[data-op-action="apply-report"]').click()
        self.assertIn("yetkili muhasebe altyapısı",self.page.locator("#content").inner_text())

    def test_new_reservation_multiroom_is_not_saved_or_confirmed(self):
        self.nav("ops_reservations")
        self.page.locator('[data-op-action="new-reservation"]').click()
        self.assertTrue(self.page.locator("#opsDraftForm").is_visible())
        self.page.locator('[data-op-action="add-room"]').click()
        self.assertEqual(self.page.locator(".ops-room-field").count(),2)
        self.page.locator("#opsDraftForm button[type=submit]").click()
        self.assertIn("KFD-2026-0007",self.page.locator("#content").inner_text())
        self.assertIn("geçici taslaktır",self.page.locator("#content").inner_text())
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_DATA.reservations.length"),6)
        self.assertFalse(self.page.evaluate("() => HOTEL_OPS_REPORT.safety.pms_writes"))

    def test_guest_fields_restricted_and_tr_country_flag_only(self):
        self.nav("ops_guests")
        self.assertIn("KVKK / GDPR",self.page.locator("#content").inner_text())
        self.assertTrue(self.page.locator("#opsTCKN").is_disabled())
        self.assertEqual(self.page.locator("#opsGuestCountry option").count(),249)
        self.page.locator("#opsGuestCountry").select_option("DE")
        self.assertIn("aktif değildir",self.page.locator("#opsGuestCountryInfo").inner_text())
        self.page.locator("#opsGuestCountry").select_option("TR")
        self.assertIn("TR:",self.page.locator("#opsGuestCountryInfo").inner_text())
        self.assertTrue(self.page.locator("#opsTCKN").is_disabled())

    def test_locale_topbar_changes_explanations_and_operations_without_mutating_report(self):
        before=self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        self.nav("ops_reservations")
        for lang in ("tr","en","fr","el","he","ar","de","ru","es","uk"):
            self.page.locator("#globalLanguage").select_option(lang)
            self.assertEqual(self.page.locator("#v04Global").get_attribute("lang"),lang)
            self.assertEqual(self.page.locator("#opsView").get_attribute("dir"),
                             "rtl" if lang in {"he","ar"} else "ltr")
        self.assertEqual(self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"),before)

    def test_mobile_no_overflow_whole_page(self):
        for width in (320,375,390,768,1440):
            self.page.set_viewport_size({"width":width,"height":1000})
            for section in ("ops_folios","ops_reports","ops_guests"):
                self.page.locator('nav [data-nav="'+section+'"]').click()
                with self.subTest(width=width,section=section):
                    self.assertTrue(self.page.evaluate(
                        "() => document.documentElement.scrollWidth <= window.innerWidth"))


if __name__=="__main__":
    unittest.main()
