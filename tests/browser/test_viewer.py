"""Real Chromium checks for local reports. Install the optional browser extra first."""
import copy
import json
import os
from pathlib import Path
import unittest

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
DEMO = json.loads((ROOT / 'examples/demo-report.json').read_text())


class ViewerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.playwright = await async_playwright().start()
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        self.browser = await self.playwright.chromium.launch(**options)
        self.page = await self.browser.new_page()
        self.errors, self.requests = [], []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        await self.page.set_content((ROOT / 'demo/viewer.html').read_text())

    async def asyncTearDown(self):
        await self.browser.close()
        await self.playwright.stop()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [], 'The inline offline viewer must not make network requests')

    async def upload(self, value, name='synthetic-report.json'):
        raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        await self.page.set_input_files('#reportFile', {'name': name, 'mimeType': 'application/json', 'buffer': raw})
        await expect(self.page.locator('#importStatus')).not_to_have_text('Rapor okunuyor…')

    async def test_valid_report_and_keyboard_file_picker(self):
        self.assertEqual(await self.page.locator('#issues .item').count(), 3)
        await self.page.locator('#chooseReport').focus()
        async with self.page.expect_file_chooser() as chooser:
            await self.page.keyboard.press('Enter')
        await (await chooser.value).set_files(ROOT / 'examples/demo-report.json')
        await expect(self.page.locator('#importStatus')).to_have_text('Rapor yüklendi. Öneriler insan onayı gerektirir.')
        self.assertEqual(await self.page.locator('#proposals .item').count(), 1)

    async def test_rejected_reports_preserve_every_panel(self):
        before = await self.page.locator('.cols').inner_html()
        samples = [None, [], {'summary': {}}, b'PRIVATE_SYNTHETIC_INVALID_JSON']
        bad_item = copy.deepcopy(DEMO)
        bad_item['issues'].append(None)
        samples.append(bad_item)
        unknown = copy.deepcopy(DEMO)
        unknown['guest_name'] = 'SYNTHETIC_DO_NOT_ECHO'
        samples.append(unknown)
        for value in samples:
            await self.upload(value)
            self.assertTrue(await self.page.locator('#importStatus').evaluate("e => e.classList.contains('error')"))
            self.assertEqual(await self.page.locator('.cols').inner_html(), before)
        self.assertNotIn('PRIVATE_SYNTHETIC', await self.page.locator('#importStatus').inner_text())
        self.assertNotIn('SYNTHETIC_DO_NOT_ECHO', await self.page.locator('#importStatus').inner_text())

    async def test_wrong_mode_date_counts_and_unapproved_proposals_rejected(self):
        variants = []
        for field, value in [('schema_version', '2.0'), ('mode', 'LIVE'), ('as_of', '2026-02-30')]:
            report = copy.deepcopy(DEMO)
            report[field] = value
            variants.append(report)
        report = copy.deepcopy(DEMO)
        report['summary']['critical_alerts'] = -1
        variants.append(report)
        report = copy.deepcopy(DEMO)
        report['summary']['room_proposals'] = 99
        variants.append(report)
        report = copy.deepcopy(DEMO)
        report['room_proposals'][0]['kind'] = 'AUTO_APPROVED'
        variants.append(report)
        for value in variants:
            await self.upload(value)
            self.assertTrue(await self.page.locator('#importStatus').evaluate("e => e.classList.contains('error')"))
            self.assertIn('Kurgusal örnek rapor', await self.page.locator('#fileInfo').inner_text())

    async def test_large_file_rejected_then_same_file_can_be_retried(self):
        await self.upload(b' ' * 3_000_001)
        self.assertIn('3 MB', await self.page.locator('#importStatus').inner_text())
        await self.upload(DEMO)
        await self.upload(DEMO)
        self.assertIn('Rapor yüklendi', await self.page.locator('#importStatus').inner_text())

    async def test_html_is_text_and_reset_restores_sample(self):
        report = copy.deepcopy(DEMO)
        report['issues'][0]['detail'] = '<img src="https://example.invalid/" onerror="window.injected=true">'
        await self.upload(report)
        self.assertEqual(await self.page.locator('#issues img').count(), 0)
        self.assertIsNone(await self.page.evaluate('window.injected'))
        self.assertIn('<img', await self.page.locator('#issues').inner_text())
        await self.page.locator('#resetReport').click()
        self.assertNotIn('<img', await self.page.locator('#issues').inner_text())
        self.assertIn('Kurgusal örnek rapor', await self.page.locator('#fileInfo').inner_text())

    async def test_old_file_read_cannot_replace_new_selection_or_reset(self):
        await self.page.evaluate("""() => {
            const original = File.prototype.text;
            File.prototype.text = function() {
                if (this.name === 'slow.json') return new Promise(resolve => {
                    window.finishSlowRead = async () => resolve(await original.call(this));
                });
                return original.call(this);
            };
        }""")
        await self.page.set_input_files('#reportFile', {'name': 'slow.json', 'mimeType': 'application/json', 'buffer': json.dumps(DEMO).encode()})
        await self.upload(DEMO, 'newer.json')
        await self.page.evaluate('window.finishSlowRead()')
        self.assertIn('newer.json', await self.page.locator('#fileInfo').inner_text())
        await self.page.set_input_files('#reportFile', {'name': 'slow.json', 'mimeType': 'application/json', 'buffer': json.dumps(DEMO).encode()})
        await self.page.locator('#resetReport').click()
        await self.page.evaluate('window.finishSlowRead()')
        self.assertIn('Kurgusal örnek rapor', await self.page.locator('#fileInfo').inner_text())

    async def test_mobile_has_no_horizontal_overflow(self):
        await self.page.set_viewport_size({'width': 390, 'height': 844})
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))


if __name__ == '__main__':
    unittest.main()
