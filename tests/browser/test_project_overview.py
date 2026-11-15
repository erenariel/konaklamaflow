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
        self.assertEqual(page.locator('nav.links a').count(), 5)
        for width in (320, 375, 390, 768, 1366):
            page.set_viewport_size({"width": width, "height": 900})
            with self.subTest(width=width):
                self.assertTrue(page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"))
                self.assertTrue(page.locator("h1").is_visible())
                self.assertTrue(page.locator(".feature").first.is_visible())
        page.locator('a[href="#nasil"]').click()
        self.assertEqual(page.evaluate("location.hash"), "#nasil")

    def test_first_party_hotel_evaluation_is_visible_and_properly_scoped(self):
        page = self.page
        page.locator('a[href="#otel-degerlendirmesi"]').click()
        self.assertEqual(page.evaluate("location.hash"), "#otel-degerlendirmesi")
        review = page.locator("#otel-degerlendirmesi")
        self.assertTrue(review.is_visible())
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

    def test_animated_recordings_and_vision_concepts_are_distinct_and_accessible(self):
        page = self.page
        recorded = page.locator('#real-gifs .showcase-card')
        visions = page.locator('#vision .showcase-card.concept')
        self.assertEqual(recorded.count(), 3)
        self.assertEqual(visions.count(), 3)
        self.assertIn('gerçek tarayıcı kayıtlarıdır', page.locator('#real-gifs').inner_text())
        self.assertIn('konsept sanattır', page.locator('#vision').inner_text())
        for segment, expected in (
            ('#real-gifs', ('ai-command-tour.gif', 'roomplan-story.gif', 'overview-pulse.gif')),
            ('#vision', ('vision-ai-command-core.gif', 'vision-smart-room-grid.gif',
                        'vision-executive-intelligence.gif')),
        ):
            links = page.locator(segment + ' .showcase-card a')
            self.assertEqual([links.nth(i).get_attribute('href') for i in range(3)],
                             list(expected))
            for i in range(3):
                card = page.locator(segment + ' .showcase-card').nth(i)
                self.assertTrue(card.locator('img').get_attribute('alt'))
                self.assertEqual(card.locator('picture source').get_attribute('media'),
                                 '(prefers-reduced-motion: reduce)')
                self.assertTrue((self.site / expected[i]).is_file())
        page.emulate_media(reduced_motion='reduce')
        for image in page.locator('#vision img').all():
            self.assertTrue(image.evaluate('(img) => img.currentSrc.endsWith("-poster.jpg")'))

    def test_existing_demo_has_discoverable_overview_entry(self):
        page = self.page
        page.goto((self.site / "index.html").as_uri())
        link = page.locator(".kf-promo-entry a")
        self.assertEqual(link.count(), 1)
        self.assertEqual(link.get_attribute("href"), "project-overview.html")
        self.assertTrue(link.is_visible())


if __name__ == "__main__":
    unittest.main()
