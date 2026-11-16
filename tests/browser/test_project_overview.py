"""Browser checks for a product-first fictional hotel demo overview.

The public demo demonstrates software workflows, not stamped operator reviews,
public certifications or decorative unreleased features.
"""
from pathlib import Path
import tempfile
import unittest

from playwright.sync_api import sync_playwright

from scripts.stage_demo_site import stage_site


class ProjectOverviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.site = Path(self.temp.name) / "site"
        stage_site(self.site)
        self.page = self.browser.new_page(viewport={"width": 1366, "height": 900})
        self.errors = []
        self.external_requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.external_requests.append(request.url)
                     if request.url.startswith(("http:", "https:")) else None)
        self.page.goto((self.site / "project-overview.html").as_uri())

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.external_requests, [])
        self.page.close()
        self.temp.cleanup()

    def test_overview_leads_with_product_scenarios_and_modules(self):
        page = self.page
        self.assertEqual(page.locator("h1").count(), 1)
        self.assertEqual(page.locator(".flow-step").count(), 4)
        self.assertEqual(page.locator("#senaryolar .feature").count(), 3)
        self.assertEqual(page.locator("#moduller .feature").count(), 6)
        self.assertEqual(page.locator(".metric").count(), 0)
        self.assertEqual(page.locator('nav.links a').count(), 5)
        self.assertTrue(page.locator(".hero-visual img").evaluate(
            "(img) => img.complete && img.naturalWidth > 0"))
        body = page.locator("main").inner_text()
        for phrase in ("Çalışan demoyu aç", "İki ayrı yatak talebi",
                       "Çakışma ve kanal uyuşmazlığı", "Bakım ve temizlik blokajı",
                       "Rezervasyon incelemesi", "Oda planı", "English summary"):
            self.assertIn(phrase, body)
        self.assertIn("Kurgusal", body)

    def test_no_signed_operator_pdf_proof_or_future_concept_promotion(self):
        page = self.page
        html = page.content()
        for forbidden in ("otel-degerlendirmesi", "KonaklamaFlow_Operator_Review",
                          "OPERATOR_FIRST_PARTY_REVIEW", "PUBLIC_EVIDENCE_DISCLOSURE",
                          "kaşeli otel", "company-stamped", "Asmalı Hotel",
                          'id="vizyon"', 'id="sifreli-kasa"',
                          'href="privacy-campaign.html"',
                          'href="privacy-vault-lab.html"', "PR #"):
            self.assertNotIn(forbidden, html)
        self.assertEqual(page.locator('a[href$=".pdf"]').count(), 0)
        self.assertGreaterEqual(page.locator('a[href="index.html"]').count(), 4)

    def test_responsive_navigation_and_accessible_product_links(self):
        page = self.page
        for width in (320, 375, 390, 768, 1366):
            page.set_viewport_size({"width": width, "height": 900})
            with self.subTest(width=width):
                self.assertTrue(page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertTrue(page.locator("h1").is_visible())
                self.assertTrue(page.locator("#moduller .feature").first.is_visible())
        for anchor in ("#senaryolar", "#nasil", "#moduller"):
            page.locator('nav.links a[href="' + anchor + '"]').click()
            self.assertEqual(page.evaluate("location.hash"), anchor)

    def test_actual_browser_recordings_are_kept_as_product_demonstrations(self):
        page = self.page
        recordings = page.locator("#gercek-gif")
        self.assertEqual(recordings.locator(".showcase-card").count(), 3)
        self.assertIn("gerçek tarayıcı ekran kayıtlarıdır", recordings.inner_text())
        for img in recordings.locator(".showcase-media img").all():
            self.assertTrue(img.get_attribute("alt"))
            img.scroll_into_view_if_needed()
            page.wait_for_function(
                "(image) => image.complete && image.naturalWidth > 0",
                arg=img.element_handle())
            self.assertTrue(img.evaluate("(image) => image.currentSrc.startsWith('file:')"))

    def test_product_zip_is_discoverable_without_operator_proof(self):
        page = self.page
        download = page.locator('a[href="konaklamaflow-offline-demo.zip"]')
        self.assertEqual(download.count(), 1)
        self.assertEqual(download.get_attribute("download"), "")
        self.assertTrue((self.site / "konaklamaflow-offline-demo.zip").is_file())
        self.assertNotIn("değerlendirme formu", page.locator("main").inner_text().lower())
        self.assertEqual(page.locator('a[href$=".pdf"]').count(), 0)

    def test_reduced_motion_uses_real_demo_still_poster(self):
        page = self.page
        page.emulate_media(reduced_motion="reduce")
        img = page.locator("#gercek-gif picture img").first
        img.scroll_into_view_if_needed()
        page.wait_for_function(
            "(image) => image.complete && image.naturalWidth > 0",
            arg=img.element_handle())
        self.assertTrue(img.evaluate(
            "(image) => image.currentSrc.endsWith('ai-command-tour-poster.png')"))

    def test_integrated_demo_links_only_to_workflow_overview(self):
        page = self.page
        page.goto((self.site / "index.html").as_uri())
        info = page.locator("#aboutProject")
        self.assertEqual(info.count(), 1)
        self.assertFalse(info.evaluate("(node) => node.open"))
        self.assertLess(page.locator("#content").bounding_box()["y"],
                        info.bounding_box()["y"])
        self.assertLess(page.locator("#aiCommandCenter").bounding_box()["y"],
                        info.bounding_box()["y"])
        page.locator("#aboutProject summary").click()
        self.assertTrue(info.evaluate("(node) => node.open"))
        links = info.locator("a")
        self.assertEqual(links.count(), 4)
        self.assertEqual(links.first.get_attribute("href"), "project-overview.html")
        self.assertEqual(links.nth(1).get_attribute("href"), "project-overview.html#senaryolar")
        self.assertEqual(links.nth(2).get_attribute("href"), "global-allocation-lab.html")
        self.assertTrue(links.nth(2).is_visible())
        self.assertEqual(links.nth(3).get_attribute("href"), "konaklamaflow-offline-demo.zip")
        self.assertTrue(links.nth(3).is_visible())
        self.assertNotIn("imzalı ve kaşeli", page.locator(".kf-promo-entry").inner_text().lower())
        self.assertNotIn("privacy-campaign.html", page.locator(".kf-promo-entry").inner_html())
        for width in (320, 375, 390):
            page.set_viewport_size({"width": width, "height": 844})
            with self.subTest(width=width):
                self.assertTrue(page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertLess(page.locator("#content").bounding_box()["y"],
                                page.locator("#aboutProject").bounding_box()["y"])
                self.assertTrue(page.locator("#aiCommandCenter").is_visible())
                self.assertTrue(page.locator("#aboutProject summary").is_visible())


if __name__ == "__main__":
    unittest.main()
