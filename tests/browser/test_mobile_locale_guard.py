"""Offline browser regressions for mobile locale reachability and live controls."""
from pathlib import Path
import os
import unittest
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[2]/"demo"/"v04-integrated-preview.html").read_text(encoding="utf-8")


class MobileLocaleGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=sync_playwright().start()
        options={"headless":True,"args":["--no-sandbox"]}
        if os.environ.get("KONAKLAMAFLOW_CHROMIUM"):
            options["executable_path"]=os.environ["KONAKLAMAFLOW_CHROMIUM"]
        cls.browser=cls.engine.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.engine.stop()

    def test_mobile_language_select_not_covered_by_sidebar(self):
        for width in (320, 375, 390, 760):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":812})
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.set_content(HTML)
                info=page.evaluate("""() => {
                    const sel=document.querySelector('#globalLanguage').getBoundingClientRect();
                    const nav=document.querySelector('.sidebar').getBoundingClientRect();
                    return {
                      belowSidebar:sel.top>=nav.bottom,
                      hit:document.elementFromPoint(sel.x+sel.width/2,sel.y+sel.height/2)?.id,
                      noOverflow:document.documentElement.scrollWidth<=window.innerWidth
                    };
                }""")
                self.assertTrue(info["belowSidebar"],info)
                self.assertEqual(info["hit"],"globalLanguage")
                self.assertTrue(info["noOverflow"],info)
                page.locator("#globalLanguage").select_option("en")
                self.assertEqual(page.locator("html").get_attribute("lang"),"en")
                self.assertEqual(errors,[])
                page.close()

    def test_ten_locale_motion_and_shift_labels(self):
        page=self.browser.new_page(viewport={"width":1366,"height":768})
        errors=[]
        outbound=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("request",lambda request:outbound.append(request.url))
        page.set_content(HTML)
        for locale in ("tr","en","fr","el","he","ar","de","ru","es","uk"):
            with self.subTest(locale=locale):
                page.locator("#globalLanguage").select_option(locale)
                motion=page.locator("#kfMotion").inner_text()
                shift=page.locator(".shift-banner").inner_text()
                if locale!="tr":
                    self.assertNotIn("Hareket:",motion)
                    self.assertNotIn("12 Kasım",shift)
                if locale=="ar":
                    self.assertIn("وردية",shift)
                    self.assertNotIn("FRONT DESK SHIFT",shift)
                self.assertEqual(page.locator("html").get_attribute("dir"),
                                 "rtl" if locale in ("ar","he") else "ltr")
                page.locator("#kfMotion").click()
                self.assertNotEqual(page.locator("#kfMotion").inner_text(),motion)
                page.locator("#kfMotion").click()
        self.assertEqual(errors,[])
        self.assertEqual(outbound,[])
        page.close()


if __name__=="__main__":
    unittest.main()
