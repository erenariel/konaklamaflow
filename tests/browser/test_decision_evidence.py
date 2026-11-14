"""Source-bound fictional decision evidence UI: no approvals, network or fresh rules."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML=Path(__file__).resolve().parents[2]/"demo"/"v04-integrated-preview.html"
LANGS=("tr","en","fr","de","el","he","ar","es","ru","uk")


class DecisionEvidenceBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start()
        cls.browser=cls.p.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()

    def setUp(self):
        self.page=self.browser.new_page(viewport={"width":1366,"height":900})
        self.errors=[]
        self.requests=[]
        self.page.on("pageerror",lambda error:self.errors.append(str(error)))
        self.page.on("request",lambda req:self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors,[])
        self.assertEqual(self.requests,[])
        self.page.close()

    def test_initial_trail_uses_exact_authoritative_rule_reasons(self):
        self.assertEqual(self.page.locator("#kfDecisionEvidence").count(),1)
        self.assertEqual(self.page.locator("#kfDecisionEvidence").get_attribute("data-source-state"),"source_bound")
        self.assertEqual(self.page.locator(".kf-decision-evidence-step").count(),4)
        row=self.page.evaluate("""() => INITIAL_EVALUATION.arrivals.find(
          row=>row.task_id===document.getElementById('v04Booking').value)""")
        self.assertEqual(self.page.locator('[data-trace-step="rules"] .kf-decision-code').all_inner_texts()[1:],row["blockers"])
        self.assertIn("SHA-256:",self.page.locator('[data-trace-step="source"]').inner_text())
        self.assertIn("DRY_RUN_ONLY",self.page.locator("#v04Global").inner_text())
        self.assertIn("Gerçek audit kaydı değildir",self.page.locator("#kfDecisionEvidenceNote").inner_text())

    def test_every_selected_booking_rebinds_without_changing_report(self):
        before=self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        tasks=self.page.evaluate("() => INITIAL_EVALUATION.arrivals.map(row=>row.task_id)")
        for task in tasks:
            self.page.locator("#v04Booking").select_option(task)
            expected=self.page.evaluate("""() => {
              const row=INITIAL_EVALUATION.arrivals.find(x=>x.task_id===document.getElementById('v04Booking').value);
              return {
                codes:row.blockers,
                fields:[...new Set(row.blockers.flatMap(code=>V04_CATALOG.evidence[code]||[]))]
              };
            }""")
            self.assertEqual(self.page.locator('[data-trace-step="rules"] .kf-decision-code').all_inner_texts()[1:],expected["codes"])
            self.assertEqual(self.page.locator('[data-trace-step="evidence"] .kf-decision-code').all_inner_texts(),expected["fields"])
        self.assertEqual(self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"),before)

    def test_stale_report_hides_all_details_until_reset(self):
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.assertTrue(self.page.evaluate("() => reportStale"))
        self.assertEqual(self.page.locator("#kfDecisionEvidence").get_attribute("data-source-state"),"unverified")
        self.assertEqual(self.page.locator(".kf-decision-evidence-step").count(),0)
        self.page.locator("#resetButton").click()
        self.assertEqual(self.page.locator("#kfDecisionEvidence").get_attribute("data-source-state"),"source_bound")
        self.assertEqual(self.page.locator(".kf-decision-evidence-step").count(),4)

    def test_catalog_mismatch_fails_closed(self):
        self.page.evaluate("""() => {
          V04_CATALOG.sourceSha='f'.repeat(64);
          window.v04Render();
        }""")
        self.assertEqual(self.page.locator("#kfDecisionEvidence").get_attribute("data-source-state"),"unverified")
        self.assertEqual(self.page.locator(".kf-decision-evidence-code").count(),0)
        self.assertEqual(self.page.locator(".kf-decision-evidence-step").count(),0)

    def test_ten_draft_locales_keyboard_and_responsive(self):
        before=self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        for lang in LANGS:
            self.page.locator("#v04Locale").select_option(lang)
            for width in (320,390,768,1366):
                self.page.set_viewport_size({"width":width,"height":900})
                with self.subTest(lang=lang,width=width):
                    self.assertEqual(self.page.locator("#kfDecisionEvidence").get_attribute("data-source-state"),"source_bound")
                    self.assertTrue(self.page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth"))
                    self.assertEqual(self.page.locator(".kf-decision-evidence-step").count(),4)
        self.assertEqual(self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"),before)


if __name__=="__main__":
    unittest.main()
