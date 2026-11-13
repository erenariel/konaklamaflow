"""End-to-end tests for integrated 18-room hotel workbench and 32 reports.

All data synthetic; no user passport, payment gateway or booking API calls.
"""
from pathlib import Path
import json
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
HTML=ROOT/"demo/v04-integrated-preview.html"
CANONICAL=json.loads((ROOT/"examples/canonical-hotel.json").read_text(encoding="utf-8"))
from konaklamaflow.canonical import project_operations
from konaklamaflow.canonical_reporting import build_canonical_operations_report

SAMPLE=project_operations(CANONICAL)


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

    def test_dashboard_is_entrypoint_and_room_plan_is_accessible(self):
        self.assertEqual(self.page.evaluate("() => page"),"dashboard")
        self.page.locator('nav [data-nav="rooms"]').click()
        self.assertEqual(self.page.evaluate("() => page"),"rooms")
        self.assertEqual(self.page.locator("nav [data-nav]").count(),20)
        self.assertTrue(self.page.locator('nav [data-nav="ops_folios"]').is_visible())
        self.assertTrue(self.page.locator("#globalLanguage").is_visible())
        self.assertEqual(self.page.locator("#globalLanguage").input_value(),"tr")

    def test_python_generated_report_exactly_matches_browser_data(self):
        self.assertEqual(self.page.evaluate("() => CANONICAL_DATA"),CANONICAL)
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_DATA"),SAMPLE)
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_REPORT"),build_canonical_operations_report(CANONICAL))
        self.assertEqual(self.page.evaluate("() => Object.keys(HOTEL_OPS_REPORT.reports).length"),32)
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_REPORT.safety.guest_identity_data"),False)

    def test_folios_show_only_explicit_source_postings_and_agency_debt(self):
        self.nav("ops_folios")
        for folio in SAMPLE["folios"]:
            clear_scope=self.page.locator('[data-op-action="clear-folio-scope"]')
            if clear_scope.count():
                clear_scope.first.click()
            self.page.locator('[data-op-open="folio:'+folio['id']+'"]').click()
            detail=self.page.locator('[data-canonical-folio="'+folio['id']+'"]')
            self.assertEqual(detail.get_attribute("data-reservation-id"),folio["reservation_id"])
            self.assertIn(folio["reservation_id"],detail.inner_text())
            for posting in folio["postings"]:
                self.assertIn(posting["kind"],detail.inner_text())
                self.assertIn(posting["amount"].replace(".",","),detail.inner_text())
            # This scenario has no payment records; the UI must not borrow
            # transactions from the unrelated historical six-booking fixture.
            self.assertEqual(folio["payments"],[])
            self.assertNotIn("RESTAURANT",detail.inner_text())
            self.assertNotIn("MINIBAR",detail.inner_text())
        self.nav("ops_agencies")
        ledger=self.page.locator("#content").inner_text()
        self.assertIn("Hotelbeds (DEMO)",ledger)
        self.assertIn("KF1007",ledger)
        self.assertIn("FOL-CAN-KF1007",ledger)
        self.assertIn("127,50",ledger)
        self.assertNotIn("FOL-CAN-KF1001",ledger)
        self.assertNotIn("FOL-CAN-KF1004",ledger)

    def test_all_32_reports_can_be_selected_missing_sources_are_visible(self):
        self.nav("ops_reports")
        self.assertEqual(self.page.locator("#opsReportType option").count(),32)
        self.page.locator("#opsReportType").select_option("posting_invoice")
        self.page.locator('[data-op-action="apply-report"]').click()
        result=self.page.locator('.ops-report-result')
        self.assertEqual(result.get_attribute('data-report-source-state'),'synthetic_snapshot')
        self.assertIn("ROOM",result.inner_text())
        self.assertIn("POST-CAN-KF1001",result.inner_text())
        self.assertNotIn("RESTAURANT",result.inner_text())
        self.page.locator("#opsReportType").select_option("trial_balance")
        self.page.locator('[data-op-action="apply-report"]').click()
        self.assertIn("yetkili muhasebe altyapısı",self.page.locator("#content").inner_text())
        self.assertEqual(self.page.locator('.ops-report-result').get_attribute('data-report-source-state'),'missing_source')

    def test_new_reservation_multiroom_is_not_saved_or_confirmed(self):
        original=self.page.evaluate("() => JSON.stringify([CANONICAL_DATA,HOTEL_OPS_DATA,HOTEL_OPS_REPORT])")
        self.nav("ops_reservations")
        self.page.locator('[data-op-action="new-reservation"]').click()
        self.assertTrue(self.page.locator("#opsDraftForm").is_visible())
        self.page.locator('[data-op-action="add-room"]').click()
        self.assertEqual(self.page.locator(".ops-room-field").count(),2)
        self.page.locator("#opsDraftForm button[type=submit]").click()
        self.assertIn("DRAFT-2026-0001",self.page.locator("#content").inner_text())
        self.assertIn("geçici taslaktır",self.page.locator("#content").inner_text())
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_DATA.reservations.length"),12)
        self.assertEqual(self.page.evaluate("() => opsState.drafts[0]"),{"id":"DRAFT-2026-0001","rooms":2,"persons":4})
        self.assertEqual(self.page.evaluate("() => JSON.stringify([CANONICAL_DATA,HOTEL_OPS_DATA,HOTEL_OPS_REPORT])"),original)
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
