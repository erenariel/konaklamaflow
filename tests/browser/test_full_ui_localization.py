"""v0.5.1 regression: real whole-page language changes, scrollable nav and staff/scenario UI.

The preview is a fictional offline app: tests NEVER assert live supplier connectivity,
identity verification, invoice issuance, financial posting or authority.
"""
import json
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/"demo/v04-integrated-preview.html"
LANGS=("tr","en","fr","el","he","ar","de","ru","es","uk")


class FullApplicationLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page=self.browser.new_page(viewport={"width":1380,"height":760})
        self.errors=[]
        self.requests=[]
        self.page.on("pageerror",lambda e:self.errors.append(str(e)))
        self.page.on("request",lambda r:self.requests.append(r.url))
        self.page.set_content(PAGE.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors,[])
        self.assertEqual(self.requests,[])
        self.page.close()

    def test_all_twenty_modules_and_left_sidebar_scrollable(self):
        self.assertEqual(self.page.locator("nav [data-nav]").count(),20)
        self.assertEqual(self.page.evaluate("() => page"),"dashboard")
        state=self.page.evaluate("""() => {
            const m=document.getElementById('nav');
            return {scroll:m.scrollHeight,client:m.clientHeight,
                    overflow:getComputedStyle(m).overflowY};
        }""")
        self.assertGreater(state["scroll"],state["client"])
        self.assertEqual(state["overflow"],"auto")
        self.page.evaluate("""() => {const n=document.getElementById('nav');n.scrollTop=n.scrollHeight;}""")
        self.assertTrue(self.page.locator('nav [data-nav="ops_staff"]').is_visible())
        self.page.locator('nav [data-nav="ops_staff"]').click()
        self.assertEqual(self.page.evaluate("() => page"),"ops_staff")
        self.assertTrue(self.page.locator("#wfView").is_visible())

    def test_locale_switch_translates_entire_nav_title_controls_and_rtl(self):
        self.page.locator('nav [data-nav="rooms"]').click()
        original=self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        for locale in LANGS:
            self.page.locator("#globalLanguage").select_option(locale)
            self.assertEqual(self.page.locator("html").get_attribute("lang"),locale)
            self.assertEqual(self.page.locator("html").get_attribute("dir"),
                             "rtl" if locale in ("he","ar") else "ltr")
            text=self.page.locator("#pagetitle").inner_text()
            expected=self.page.evaluate("""() => fullUiMenu[opsState.lang][3]""")
            with self.subTest(locale=locale):
                self.assertEqual(text,expected)
                self.assertEqual(self.page.locator("nav [data-nav]").count(),20)
                self.assertEqual(self.page.locator("#v04Global").get_attribute("lang"),locale)
                self.assertEqual(self.page.locator("#globalLanguage").input_value(),locale)
                self.assertTrue(self.page.locator("#fullUiTranslationMarker").inner_text())
                self.assertEqual(self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"),original)
        self.page.locator("#globalLanguage").select_option("en")
        self.assertEqual(self.page.locator("#startShowcase").inner_text(),"Explore AI scenarios")
        self.assertEqual(self.page.locator('nav [data-nav="ops_staff"]').inner_text().strip(),
                         "Staff & Session")

    def test_language_does_not_reset_while_navigating_every_module(self):
        self.page.locator("#globalLanguage").select_option("de")
        for module in ["dashboard","arrivals","rooms","ops_reservations","ops_folios",
                       "ops_reports","ops_workflows","ops_staff"]:
            self.page.locator(f'nav [data-nav="{module}"]').click()
            with self.subTest(module=module):
                self.assertEqual(self.page.locator("html").get_attribute("lang"),"de")
                self.assertEqual(self.page.locator("#globalLanguage").input_value(),"de")
                self.assertTrue(self.page.locator("#pagetitle").inner_text())
                self.assertTrue(self.page.locator("#content").inner_text())

    def test_secondary_locale_selector_follows_topbar_without_loop(self):
        self.page.locator("#v04Locale").select_option("ar")
        self.assertEqual(self.page.locator("#globalLanguage").input_value(),"ar")
        self.assertEqual(self.page.locator("html").get_attribute("dir"),"rtl")
        self.page.locator("#globalLanguage").select_option("fr")
        self.assertEqual(self.page.locator("#v04Locale").input_value(),"fr")

    def test_demo_staff_profile_role_switch_and_audit_are_non_authorizing(self):
        self.page.locator("#wfStaffButton").click()
        self.assertEqual(self.page.evaluate("() => page"),"ops_staff")
        self.assertIn("DEMO-REC-001",self.page.locator("#content").inner_text())
        self.page.locator("#wfOperator").select_option("DEMO-FIN-003")
        self.assertEqual(self.page.evaluate("() => wfState.operator"),"DEMO-FIN-003")
        self.assertIn("DEMO ROLE SWITCH",self.page.locator("#wfAuditLog").inner_text())
        self.assertIn("NOT CONNECTED",self.page.locator("#content").inner_text().upper())
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_REPORT.safety.pms_writes"),False)

    def test_workflow_role_scopes_and_vendor_disconnection(self):
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        self.assertEqual(self.page.locator("#wfFlow option").count(),14)
        self.assertEqual(self.page.locator(".wf-vendor").count(),3)
        self.page.locator("#wfFlow").select_option("agency_credit")
        self.assertTrue(self.page.locator("#wfPreview").is_disabled())
        self.page.locator('nav [data-nav="ops_staff"]').click()
        self.page.locator("#wfOperator").select_option("DEMO-FIN-003")
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        self.assertFalse(self.page.locator("#wfPreview").is_disabled())
        self.page.locator("#wfPreview").click()
        self.assertIn("HUMAN_APPROVAL_REQUIRED",self.page.locator("#wfPreviewResult").inner_text())
        self.assertIn("NO_LIVE_EXECUTION",self.page.locator("#wfPreviewResult").inner_text())

    def test_demo_launch_runs_multiple_stories_on_ai_dashboard(self):
        self.page.locator("#startShowcase").click()
        self.assertEqual(self.page.evaluate("() => page"),"dashboard")
        self.assertTrue(self.page.evaluate("() => commandTourAll && storyPlaying"))
        self.assertGreaterEqual(self.page.evaluate("() => stories().length"),4)
        self.assertEqual(self.page.locator("#aiCommandCenter").count(),1)
        first=self.page.evaluate("() => selectedStoryId")
        self.page.evaluate("() => {storyStep=currentStory().steps.length-1;}")
        self.page.wait_for_timeout(2400)\n        self.assertNotEqual(self.page.evaluate("() => selectedStoryId"),first)
        self.assertEqual(self.page.evaluate("() => storyStep"),0)
        self.page.locator("#commandPause").click()
        self.assertFalse(self.page.evaluate("() => commandTourAll || storyPlaying"))
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        self.assertEqual(self.page.locator("#wfScenario option").count(),5)
        self.page.locator("#wfScenario").select_option("payment")
        self.assertIn("PAYMENT_REVIEW",self.page.locator("#wfView").inner_text())
        self.page.locator("#wfNext").click()
        self.assertEqual(self.page.evaluate("() => wfState.stage"),1)

    def test_small_mobile_horizontal_navigation_reachable(self):
        self.page.set_viewport_size({"width":390,"height":844})
        self.assertEqual(self.page.evaluate("() => getComputedStyle(document.querySelector('.sidebar .menu')).overflowX"),"auto")
        self.page.locator("#globalLanguage").select_option("ar")
        self.page.locator('nav [data-nav="ops_workflows"]').click()
        self.assertTrue(self.page.locator("#wfView").is_visible())


if __name__=="__main__":
    unittest.main()
