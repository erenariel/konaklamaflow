"""Browser checks for the offline operations cockpit (optional Playwright dependency)."""
import copy
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
class OperationsBrowserCase(unittest.TestCase):
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
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [], 'The operations viewer must stay offline')



class OperationsCockpitTests(OperationsBrowserCase):
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
        other['summary'] = dict(arrivals_total=2, ready_for_review=1, blocked=1, already_checked_in_requires_review=0)
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
        self.assertIn('Dosya yüklenemedi',self.page.locator('#error').inner_text())
        self.assertNotIn('<img',self.page.locator('body').inner_text())
        self.assertEqual(self.errors,[])

    def test_mobile_view_no_horizontal_overflow(self):
        self.page.set_viewport_size({'width':375,'height':812})
        for width in (320,375,768,1366):
            self.page.set_viewport_size({'width':width,'height':812})
            self.assertFalse(self.page.evaluate('document.documentElement.scrollWidth > window.innerWidth'))

    def test_no_network_requests(self):
        self.assertEqual(self.requests,[])
        self.assertEqual(self.errors,[])


class OperationsImportAuditTests(OperationsBrowserCase):
    """Adversarial report imports and concurrent file reads found during audit."""
    def upload(self, value, name='report.json'):
        raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.page.locator('#file').set_input_files({'name':name,'mimeType':'application/json','buffer':raw})
        self.page.wait_for_function("() => document.getElementById('error').textContent !== 'Rapor okunuyor…'")

    def test_bad_schema_private_fields_and_inconsistent_counts_preserve_panels(self):
        before = self.page.locator('.grid').inner_html()
        variants = [None, [], b'SYNTHETIC_PRIVATE_INVALID_JSON', b' '*2_000_001]
        for field,value in [('schema_version','1.0'),('mode','LIVE'),('as_of','2026-02-30'),('guest_name','SYNTHETIC_PRIVATE')]:
            r=copy.deepcopy(SAMPLE);r[field]=value;variants.append(r)
        r=copy.deepcopy(SAMPLE);r['summary']['ready_for_review']=99;variants.append(r)
        r=copy.deepcopy(SAMPLE);r['tasks'][0]['task_id']=r['tasks'][1]['task_id'];variants.append(r)
        for field,value in [('state','CHECKED_IN'),('checklist',{'guest_name':'SYNTHETIC_PRIVATE'}),('required_action','AUTO_APPROVE'),('reasons',['SYNTHETIC_PRIVATE']),('task_id',None),('stay',{'checkin':'2026-11-12','checkout':'2026-11-11'})]:
            r=copy.deepcopy(SAMPLE);r['tasks'][0][field]=value;variants.append(r)
        r=copy.deepcopy(SAMPLE);r['tasks'][0]['checklist']['room_clean_and_inspected']='true';variants.append(r)
        for r in variants:
            self.upload(r)
            self.assertIn('Dosya yüklenemedi',self.page.locator('#error').inner_text())
            self.assertNotIn('SYNTHETIC_PRIVATE',self.page.locator('body').inner_text())
            self.assertEqual(self.page.locator('.grid').inner_html(),before)

    def test_slow_read_cannot_overwrite_newer_selection_or_reset(self):
        self.page.evaluate("""() => {
            const original = File.prototype.text;
            File.prototype.text = function() {
                if (this.name === 'slow.json') return new Promise(resolve => {
                    window.finishSlowRead = async () => resolve(await original.call(this));
                });
                return original.call(this);
            };
        }""")
        self.page.locator('#file').set_input_files({'name':'slow.json','mimeType':'application/json','buffer':json.dumps(SAMPLE).encode()})
        newer=copy.deepcopy(SAMPLE);newer['property_id']='NEWER_REPORT'
        self.upload(newer)
        self.page.evaluate('window.finishSlowRead()')
        self.assertEqual(self.page.locator('#metricProperty').inner_text(),'NEWER_REPORT')
        self.page.locator('#file').set_input_files({'name':'slow.json','mimeType':'application/json','buffer':json.dumps(newer).encode()})
        self.page.locator('#reset').click();self.page.evaluate('window.finishSlowRead()')
        self.assertEqual(self.page.locator('#metricProperty').inner_text(),SAMPLE['property_id'])
        self.assertIn('Kurgusal örnek',self.page.locator('#stamp').inner_text())

    def test_filters_search_details_and_reset_remain_consistent(self):
        self.page.locator('[data-filter=blocked]').click()
        self.assertNotEqual(self.page.locator('#selectedRef').inner_text(),'DEMO_A01')
        self.page.locator('#search').fill('MISSING')
        self.assertEqual(self.page.locator('#selectedRef').inner_text(),'—')
        self.assertEqual(self.page.locator('#checks').inner_text(),'')
        self.page.locator('#reset').click()
        self.assertEqual(self.page.locator('.r').count(),4)
        self.assertEqual(self.page.locator('#search').input_value(),'')
        self.assertEqual(self.page.locator('[data-filter=all]').get_attribute('aria-pressed'),'true')

    def test_existing_checkin_has_distinct_filter(self):
        r=copy.deepcopy(SAMPLE);r['tasks'][0]['state']='REVIEW_EXISTING_CHECKIN';r['tasks'][0]['reasons']=['already_marked_checked_in']
        r['summary'].update(ready_for_review=0,already_checked_in_requires_review=1)
        self.upload(r)
        self.page.locator('[data-filter=existing]').click()
        self.assertEqual(self.page.locator('.r').count(),1)
        self.assertEqual(self.page.locator('#selectedRef').inner_text(),'DEMO_A01')
        self.page.locator('[data-filter=blocked]').click()
        self.assertEqual(self.page.locator('.r').count(),3)

    def test_keyboard_picker_and_repeated_imports(self):
        with self.page.expect_file_chooser() as chooser:
            self.page.locator('#importButton').press('Enter')
        chooser.value.set_files(ROOT/'examples/operations-report.json')
        self.page.wait_for_function("() => document.getElementById('stamp').textContent.includes('Yerel rapor')")
        self.upload(SAMPLE);self.upload(SAMPLE)
        self.assertEqual(self.page.locator('#error').inner_text(),'')
        self.assertNotIn('Kurgusal örnek',self.page.locator('#stamp').inner_text())


if __name__ == '__main__':
    unittest.main()
