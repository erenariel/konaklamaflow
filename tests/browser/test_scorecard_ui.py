"""Offline scorecard UI: responsive and demonstrably no live data fetching."""
import unittest
from playwright.sync_api import sync_playwright

from scripts.render_scorecard import scorecard_html


class ScorecardBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_scorecard_uses_source_derived_cases_and_no_requests(self):
        page=self.browser.new_page(viewport={"width":1366,"height":900})
        try:
            requests=[]
            errors=[]
            page.on("request",lambda req:requests.append(req.url))
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.set_content(scorecard_html())
            self.assertEqual(page.locator(".cards .card").count(),4)
            self.assertEqual(page.locator("table").count(),2)
            self.assertEqual(page.locator("section.panel:last-of-type tbody tr").count(),10)
            self.assertIn("7 / 10",page.locator(".card").first.inner_text())
            self.assertIn("Gerçek otel doğruluğu değildir",page.locator("main").inner_text())
            for width in (320,390,768,1366):
                page.set_viewport_size({"width":width,"height":900})
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            self.assertEqual(requests,[])
            self.assertEqual(errors,[])
        finally:
            page.close()


if __name__=="__main__":
    unittest.main()
