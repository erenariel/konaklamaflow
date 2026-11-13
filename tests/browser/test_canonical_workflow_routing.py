"""Workflow action cards must retain their intended read-only destination."""
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]


class CanonicalWorkflowRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        cls.browser = cls.driver.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1440, 'height': 1000})
        self.errors, self.requests = [], []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.page.set_content((ROOT / 'demo/v04-integrated-preview.html').read_text())
        self.original = self.snapshot()
        self.page.evaluate("navTo('ops_workflows')")

    def tearDown(self):
        self.assertEqual(self.snapshot(), self.original)
        self.page.close()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])

    def snapshot(self):
        return self.page.evaluate('''() => JSON.stringify({source:CANONICAL_DATA,
            review:INITIAL_EVALUATION,ops:HOTEL_OPS_DATA,finance:HOTEL_OPS_REPORT})''')

    def test_each_workflow_review_action_opens_python_evidence_without_pms_redirect(self):
        scenarios = self.page.locator('#wfScenario option').evaluate_all(
            '(nodes) => nodes.map(node => node.value)')
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                self.page.locator('#wfScenario').select_option(scenario)
                button = self.page.locator('#wfView [data-canonical-action="review"]')
                self.assertEqual(button.count(), 1)
                identifier = button.get_attribute('data-reservation-id')
                self.assertTrue(self.page.evaluate('''id => INITIAL_EVALUATION.arrivals.some(
                    row => row.id === id && row.blockers.length > 0)''', identifier))
                button.click()
                self.assertEqual(self.page.evaluate('page'), 'ops_workflows')
                expect(self.page.locator('#backdrop')).to_have_class('drawer-backdrop open')
                expect(self.page.locator('#drawer')).to_contain_text(identifier)
                self.page.keyboard.press('Escape')

    def test_workflow_pms_action_selects_the_exact_canonical_parent(self):
        button = self.page.locator('#wfView [data-canonical-action="reservation"]')
        identifier = button.get_attribute('data-reservation-id')
        button.click()
        self.assertEqual(self.page.evaluate('page'), 'ops_reservations')
        expect(self.page.locator('#opsView [data-canonical-reservation]')).to_have_attribute(
            'data-canonical-reservation', identifier)
        expect(self.page.locator('#backdrop')).not_to_have_class('drawer-backdrop open')
