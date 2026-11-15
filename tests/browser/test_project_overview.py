"""Showcase must distinguish the published demo from unmerged PR candidates.

All visual assets are local and explicitly staged; there is no fetch or JS.
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

    def test_visual_and_copy_are_grounded_in_shipped_and_candidate_status(self):
        page = self.page
        self.assertEqual(page.locator("h1").count(), 1)
        self.assertEqual(page.locator(".flow-step").count(), 4)
        self.assertEqual(page.locator(".metric").count(), 4)
        self.assertEqual(page.locator(".feature").count(), 6)
        self.assertTrue(page.locator(".hero-visual img").evaluate(
            "(img) => img.complete && img.naturalWidth > 0"))
        body = page.locator("main").inner_text()
        self.assertIn("Kurgusal otel demosunu keşfet", body)
        self.assertIn("birleşik sürüm adayında", body)
        self.assertIn("Gerçek otel", body)
        self.assertIn("7 / 10", body)
        self.assertIn("English summary", body)
        hrefs = page.locator(".feature a").evaluate_all(
            "(elements) => elements.map(element => element.href)")
        for pr in (51, 53, 55, 58, 59, 65):
            self.assertTrue(any(url.endswith("/pull/" + str(pr)) for url in hrefs))

    def test_responsive_and_navigation_are_accessible(self):
        page = self.page
        self.assertEqual(page.locator('nav.links a').count(), 8)
        for width in (320, 375, 390, 768, 1366):
            page.set_viewport_size({"width": width, "height": 900})
            with self.subTest(width=width):
                self.assertTrue(page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertTrue(page.locator("h1").is_visible())
                self.assertTrue(page.locator(".feature").first.is_visible())
        page.locator('a[href="#nasil"]').click()
        self.assertEqual(page.evaluate("location.hash"), "#nasil")

    def test_product_recordings_and_future_vision_remain_distinct(self):
        page = self.page
        recordings = page.locator("#gercek-gif")
        vision = page.locator("#vizyon")
        self.assertEqual(recordings.locator(".showcase-card").count(), 3)
        self.assertEqual(vision.locator(".showcase-card.vision").count(), 3)
        self.assertIn("gerçek tarayıcı ekran kayıtlarıdır", recordings.inner_text())
        self.assertIn("Concept art only", vision.inner_text())
        self.assertIn("not implemented product features", vision.inner_text())
        self.assertIn("bilinci kanıtı değildir", vision.inner_text())
        for section in (recordings, vision):
            for img in section.locator(".showcase-media img").all():
                self.assertTrue(img.get_attribute("alt"))
                img.scroll_into_view_if_needed()
                page.wait_for_function(
                    "(image) => image.complete && image.naturalWidth > 0",
                    arg=img.element_handle())
                self.assertTrue(img.evaluate("(image) => image.currentSrc.startsWith('file:')"))

    def test_reduced_motion_uses_still_posters(self):
        page = self.page
        page.emulate_media(reduced_motion="reduce")
        vision = page.locator("#vizyon")
        img = vision.locator("picture img").first
        img.scroll_into_view_if_needed()
        page.wait_for_function(
            "(image) => image.complete && image.naturalWidth > 0",
            arg=img.element_handle())
        self.assertTrue(img.evaluate(
            "(image) => image.currentSrc.endsWith('vision-ai-command-core-poster.jpg')"))
        self.assertEqual(page.locator("picture source").count(), 6)

    def test_synthetic_encryption_research_is_clearly_not_a_live_vault(self):
        page = self.page
        section = page.locator('#sifreli-kasa')
        self.assertEqual(section.count(), 1)
        self.assertIn('kurgusal kayıt', section.inner_text())
        self.assertIn('Future design, not deployed end-to-end encryption', section.inner_text())
        self.assertEqual(section.locator('a[href="privacy-vault-lab.html"]').count(), 1)
        self.assertIn('ZERO_ACCESS_HOTEL_VAULT_TR_EN.md', section.inner_html())

    def test_first_party_hotel_evaluation_is_visible_and_properly_scoped(self):
        page = self.page
        page.locator('nav.links a[href="#otel-degerlendirmesi"]').click()
        self.assertEqual(page.evaluate("location.hash"), "#otel-degerlendirmesi")
        review = page.locator("#otel-degerlendirmesi")
        self.assertTrue(review.is_visible())
        # The signed evaluation is surfaced before the decorative GIF galleries.
        self.assertTrue(page.evaluate("() => document.querySelector('#otel-degerlendirmesi').compareDocumentPosition(document.querySelector('#gercek-gif')) & Node.DOCUMENT_POSITION_FOLLOWING"))
        body = review.inner_text()
        self.assertIn("imzalı ve kaşeli", body)
        self.assertIn("birinci taraf", body)
        self.assertIn("Pass", body)
        self.assertIn("işaretlenmemiş", body)
        self.assertIn("bağımsız denetim", body)
        self.assertIn("maintainer-affiliated", body)
        self.assertGreaterEqual(review.locator(
            'a[href*="OPERATOR_FIRST_PARTY_REVIEW_2026-11-15.md"]').count(), 1)
        self.assertGreaterEqual(review.locator(
            'a[href*="Operator_Review_PUBLIC_REDACTED_TR_EN_2026-11-15.pdf"]').count(), 1)
        self.assertGreaterEqual(review.locator(
            'a[href*="PUBLIC_EVIDENCE_DISCLOSURE_TR_EN.md"]').count(), 1)
        self.assertIn("otel ortamında değerlendirdiğini beyan", body)

    def test_existing_demo_has_discoverable_overview_entry(self):
        page = self.page
        page.goto((self.site / "index.html").as_uri())
        link = page.locator(".kf-promo-entry a")
        self.assertEqual(link.count(), 2)
        self.assertEqual(link.first.get_attribute("href"), "project-overview.html")
        self.assertEqual(link.nth(1).get_attribute("href"), "project-overview.html#otel-degerlendirmesi")
        self.assertTrue(link.nth(1).is_visible())


if __name__ == "__main__":
    unittest.main()
