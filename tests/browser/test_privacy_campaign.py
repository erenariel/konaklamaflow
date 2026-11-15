"""Privacy campaign must explain an unimplemented vision without leaking guest data."""
from pathlib import Path
import tempfile
import unittest

from playwright.sync_api import sync_playwright
from scripts.stage_demo_site import stage_site


class PrivacyCampaignBrowserTests(unittest.TestCase):
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
        self.page = self.browser.new_page(viewport={"width": 1366, "height": 850})
        self.page_errors = []
        self.remote_requests = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.on("request", lambda req: self.remote_requests.append(req.url)
                     if req.url.startswith(("http:", "https:")) else None)
        self.page.goto((self.site / "privacy-campaign.html").as_uri())

    def tearDown(self):
        self.assertEqual(self.page_errors, [])
        self.assertEqual(self.remote_requests, [],
                         "A static fictional campaign should never request remote assets")
        self.page.close()
        self.temp.cleanup()

    def test_concept_labels_and_policy_boundaries(self):
        page = self.page
        self.assertEqual(page.locator("h1").count(), 1)
        body = page.locator("main").inner_text()
        for phrase in (
            "Gizliliğinizi", "Verilerinizi görmemeyi hedefliyoruz",
            "CONCEPT VISION / GELİŞTİRME HEDEFİ",
            "Şu anda canlı şifreli otel sistemi değil",
            "KBS", "kurgusal", "denetim",
            "Bugün herhangi bir otele KonaklamaFlow güvenlik sertifikası verilmedi",
            "not yet a production guarantee",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)
        self.assertEqual(page.locator("#akış .flow li").count(), 5)
        self.assertEqual(page.locator("script").count(), 0)
        self.assertEqual(page.locator('a[href="privacy-vault-lab.html"]').count(), 3)
        self.assertEqual(page.locator('a[href="project-overview.html#otel-degerlendirmesi"]').count(), 2)

    def test_real_concept_gifs_are_local_and_loaded(self):
        for image in self.page.locator(".card img").all():
            image.scroll_into_view_if_needed()
            self.page.wait_for_function(
                "(img) => img.complete && img.naturalWidth > 0",
                arg=image.element_handle(),
            )
            self.assertTrue(image.evaluate("(img) => img.currentSrc.startsWith('file:')"))
        self.assertEqual(self.page.locator(".card img").count(), 3)
        self.assertEqual(self.page.locator(".hero-art img").get_attribute("src"), "privacy-promise.gif")
        for filename in ("privacy-promise.gif", "authorized-device.gif", "zero-access-flow.gif", "future-certification.gif"):
            self.assertIn(filename, self.page.content())

    def test_accessibility_and_mobile_no_overflow(self):
        page = self.page
        for width in (320, 375, 390, 768, 1024, 1366):
            with self.subTest(width=width):
                page.set_viewport_size({"width": width, "height": 900})
                self.assertTrue(page.locator("h1").is_visible())
                self.assertFalse(page.evaluate(
                    "() => document.documentElement.scrollWidth > window.innerWidth"
                ))
        page.locator('a[href="#akış"]').click()
        self.assertEqual(page.evaluate("decodeURIComponent(location.hash)"), "#akış")

    def test_five_step_flow_labels_and_all_four_media_pairs_are_public(self):
        page = self.page
        expected_labels = [
            "Kimlik verisi",
            "Cihazda şifrele",
            "Sunucuda şifreli kayıt",
            "Yetkili cihazda aç",
            "İnsan onayı",
        ]
        actual_labels = page.locator("#akış .flow li strong").all_inner_texts()
        self.assertEqual(actual_labels, expected_labels)
        visual_assets = (
            ("privacy-promise.gif", "privacy-promise-poster.jpg"),
            ("authorized-device.gif", "authorized-device-poster.jpg"),
            ("zero-access-flow.gif", "zero-access-flow-poster.jpg"),
            ("future-certification.gif", "future-certification-poster.jpg"),
        )
        images = page.locator("picture img")
        sources = page.locator("picture source")
        self.assertEqual(images.count(), 4)
        self.assertEqual(sources.count(), 4)
        for gif, poster in visual_assets:
            with self.subTest(gif=gif):
                img = page.locator(f'picture img[src="{gif}"]')
                self.assertEqual(img.count(), 1)
                self.assertEqual(
                    img.locator("xpath=..").locator("source").get_attribute("srcset"),
                    poster)
                img.scroll_into_view_if_needed()
                page.wait_for_function("(img) => img.complete && img.naturalWidth > 0",
                                       arg=img.element_handle())
                self.assertTrue(img.get_attribute("alt"))

        page.emulate_media(reduced_motion="reduce")
        for gif, poster in visual_assets:
            with self.subTest(poster=poster):
                image = page.locator(f'picture img[src="{gif}"]')
                image.scroll_into_view_if_needed()
                page.wait_for_function("(img) => img.complete && img.naturalWidth > 0",
                                       arg=image.element_handle())
                self.assertTrue(image.evaluate(
                    "(img) => img.currentSrc.endsWith(" + repr(poster) + ")"))

    def test_reduced_motion_uses_still_images(self):
        page = self.page
        page.emulate_media(reduced_motion="reduce")
        image = page.locator(".card picture img").first
        image.scroll_into_view_if_needed()
        page.wait_for_function(
            "(img) => img.complete && img.naturalWidth > 0",
            arg=image.element_handle(),
        )
        self.assertTrue(image.evaluate(
            "(img) => img.currentSrc.endsWith('authorized-device-poster.jpg')"
        ))


if __name__ == "__main__":
    unittest.main()
