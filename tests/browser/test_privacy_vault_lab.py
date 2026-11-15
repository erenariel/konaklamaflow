"""Browser proof-of-concept tests: fictional-only local Web Crypto, not a security audit."""
from __future__ import annotations

import json
import threading
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright
from scripts.stage_demo_site import stage_site


class ZeroAccessVaultLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.site = Path(cls.temp.name) / "site"
        stage_site(cls.site)

        class StaticHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(cls.site), **kwargs)

            def log_message(self, *args):
                return  # Offline synthetic test server; no guest data logged.

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), StaticHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:" + str(cls.server.server_port)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)
        cls.temp.cleanup()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 780})
        self.errors = []
        self.remote_requests = []
        self.page.on("pageerror", lambda err: self.errors.append(str(err)))
        self.page.on("request", lambda r: self.remote_requests.append(r.url)
                     if r.url.startswith(("https:", "http:")) and
                     not r.url.startswith(self.base_url + "/") else None)
        self.page.goto(self.base_url + "/privacy-vault-lab.html")
        self.assertTrue(self.page.evaluate("() => window.isSecureContext && !!window.crypto.subtle"))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.remote_requests, [],
                         "The lab must not request any external resources")
        self.page.close()

    def _encrypt(self):
        self.page.locator("#passphrase").fill("UniqueFictionalLabPhrase-2026-Only")
        self.page.locator("#encrypt").click()
        self.page.wait_for_function(
            "() => document.getElementById('status').textContent.startsWith('Encrypted locally.')")
        self.assertEqual(self.page.locator("#passphrase").input_value(), "")
        envelope = json.loads(self.page.locator("#envelope").input_value())
        self.assertEqual(envelope["schema"], "kf-vault-lab-v1")
        self.assertEqual(envelope["hotel_id"], "FICTIONAL_HOTEL_ONLY")
        self.assertEqual(envelope["kdf_iterations"], 600000)
        self.assertNotIn("SYNTHETIC_GUEST_001", json.dumps(envelope))
        self.assertNotIn("NOT_A_REAL_DOCUMENT", json.dumps(envelope))
        self.assertIn("LOCKED", self.page.locator("#revealed").inner_text())
        return envelope

    def test_encrypt_and_decrypt_only_fixed_fictional_record(self):
        self._encrypt()
        self.page.locator("#passphrase").fill("UniqueFictionalLabPhrase-2026-Only")
        self.page.locator("#decrypt").click()
        self.page.wait_for_function(
            "() => document.getElementById('status').textContent.startsWith('Local decryption succeeded.')")
        self.assertIn("SYNTHETIC_GUEST_001", self.page.locator("#revealed").inner_text())
        self.page.locator("#lock").click()
        self.assertIn("LOCKED", self.page.locator("#revealed").inner_text())
        self.assertEqual(self.page.locator("#passphrase").input_value(), "")

    def test_wrong_passphrase_or_tamper_fails_closed(self):
        envelope = self._encrypt()
        self.page.locator("#passphrase").fill("WrongPassphraseThatIsLongEnough")
        self.page.locator("#decrypt").click()
        self.page.wait_for_function(
            "() => document.getElementById('status').textContent.startsWith('Unlock rejected:')")
        self.assertIn("LOCKED", self.page.locator("#revealed").inner_text())

        envelope["ciphertext"] = ("A" if envelope["ciphertext"][0] != "A" else "B") + envelope["ciphertext"][1:]
        self.page.locator("#envelope").fill(json.dumps(envelope))
        self.page.locator("#passphrase").fill("UniqueFictionalLabPhrase-2026-Only")
        self.page.locator("#decrypt").click()
        self.page.wait_for_function(
            "() => document.getElementById('status').textContent.startsWith('Unlock rejected:')")
        self.assertIn("LOCKED", self.page.locator("#revealed").inner_text())

    def test_metadata_binding_and_clear(self):
        envelope = self._encrypt()
        envelope["vault_id"] = "0" * 32 if envelope["vault_id"] != "0" * 32 else "1" * 32
        self.page.locator("#envelope").fill(json.dumps(envelope))
        self.page.locator("#passphrase").fill("UniqueFictionalLabPhrase-2026-Only")
        self.page.locator("#decrypt").click()
        self.page.wait_for_function(
            "() => document.getElementById('status').textContent.startsWith('Unlock rejected:')")
        self.assertIn("LOCKED", self.page.locator("#revealed").inner_text())
        self.page.locator("#clear").click()
        self.assertEqual(self.page.locator("#envelope").input_value(), "")
        self.assertEqual(self.page.locator("#passphrase").input_value(), "")

    def test_readability_and_no_private_record_entry(self):
        self.assertEqual(self.page.locator("textarea").count(), 1)
        self.assertEqual(self.page.locator('input[type="password"]').count(), 1)
        self.assertIn("NOT A PRODUCTION SECURITY FEATURE", self.page.locator("body").inner_text())
        self.assertIn("FICTIONAL_HOTEL_ONLY", self.page.locator("#sample").inner_text())
        for width in (320, 375, 768, 1280):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 780})
                self.assertFalse(self.page.evaluate(
                    "() => document.documentElement.scrollWidth > innerWidth"))


if __name__ == "__main__":
    unittest.main()
