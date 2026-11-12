"""Browser checks for the offline operations cockpit (optional Playwright dependency)."""
import json
import os
from pathlib import Path
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / 'demo' / 'operations.html').read_text(encoding='utf-8')
SAMPLE = json.loads((ROOT / 'examples' / 'operations-report.json').read_text(encoding='utf-8'))


@unittest.skipIf(sync_playwright is None, 'Install the optional browser extra')
class OperationsCockpitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        location = os.environ.get('KONAKLAMAFLOW_CHROMIUM')
        try:
            cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=location or None)
        except Exception:
            cls.playwright.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1366, 'height': 768})
        self.errors = []
        self.requests = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('request', lambda r: self.requests.append(r.url))
        self.page.set_content(HTML, wait_until='load')

    def tearDown(self):
        self.page.close()

    def test_summary_and_visibility(self):
        self.assertEqual(self.page.locator('#metricAll').inner_text(), '4')
        self.assertEqual(self.page.locator('#metricReady').inner_text(), '1')
        self.assertEqual(self.page.locator('#metricBlocked').inner_text(), '3')
        self.assertEqual(self.page.locator('.r').count(), 4)

    def test_filter_and_search(self):
        self.page.locator('[data-filter=ready]').click()
        self.assertEqual(self.page.locator('.r').count(), 1)
        self.page.locator('[data-filter=all]').click()
        self.page.locator('#search').fill('DEMO_A03')
        self.assertEqual(self.page.locator('.r').count(), 1)

    def test_invalid_json_keeps_last_report(self):
        self.page.locator('#file').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'not json'})
        self.assertIn('Dosya yüklenemedi', self.page.locator('#error').inner_text())
        self.assertEqual(self.page.locator('#metricAll').inner_text(), '4')

    def test_valid_json_import_and_reset(self):
        other = dict(SAMPLE)
        other['property_id'] = 'TEST_HOTEL_02'
        other['tasks'] = other['tasks'][:2]
        self.page.locator('#file').set_input_files({'name':'report.json','mimeType':'application/json','buffer':json.dumps(other).encode()})
        self.assertEqual(self.page.locator('#metricProperty').inner_text(), 'TEST_HOTEL_02')
        self.assertEqual(self.page.locator('#metricAll').inner_text(), '2')
        self.page.locator('#reset').click()
        self.assertEqual(self.page.locator('#metricAll').inner_text(), '4')

    def test_untrusted_text_not_interpreted_as_html(self):
        other = json.loads(json.dumps(SAMPLE))
        other['tasks'][0]['reasons']=['<img src=x onerror=alert(1)>']
        self.page.locator('#file').set_input_files({'name':'report.json','mimeType':'application/json','buffer':json.dumps(other).encode()})
        self.assertEqual(self.page.locator('img').count(),0)
        self.assertIn('<img',self.page.locator('#reasons').inner_text())
        self.assertEqual(self.errors,[])

    def test_mobile_view_no_horizontal_overflow(self):
        self.page.set_viewport_size({'width':375,'height':812})
        self.assertFalse(self.page.evaluate('document.documentElement.scrollWidth > window.innerWidth'))

    def test_no_network_requests(self):
        self.assertEqual(self.requests,[])
        self.assertEqual(self.errors,[])


if __name__ == '__main__':unittest.main()
