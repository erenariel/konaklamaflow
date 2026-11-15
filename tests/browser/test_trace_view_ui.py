"""Static, offline fictional trace proof viewer in Chromium."""
import unittest
from playwright.sync_api import sync_playwright

from scripts.render_trace_view import trace_view_html, trusted_trace


class TraceViewerBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_trace_view_has_three_real_simulated_events_and_no_network(self):
        page=self.browser.new_page(viewport={"width":1366,"height":900})
        try:
            errors=[]
            requests=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.on("request",lambda req:requests.append(req.url))
            page.set_content(trace_view_html())
            _,_,trace=trusted_trace()
            self.assertEqual(page.locator("li.event").count(),len(trace["events"]))
            self.assertEqual(page.locator("li.event").evaluate_all(
                "(els)=>els.map(el=>el.dataset.event)"),[e["kind"] for e in trace["events"]])
            self.assertIn("Gerçek personel eylemi",page.locator("h1 + p").inner_text())
            self.assertIn(trace["head_hash"],page.locator(".hash").inner_text())
            for width in (320,390,768,1366):
                page.set_viewport_size({"width":width,"height":900})
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            self.assertEqual(errors,[])
            self.assertEqual(requests,[])
        finally:
            page.close()


if __name__=="__main__":
    unittest.main()
