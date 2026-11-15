"""Functional control audit — phase one: all 20 demo modules.

A button is not certified functional by having an event target alone.  These
tests establish a repeatable control inventory, exercise meaningful actions,
and keep disabled/safety-sensitive behavior explicit. Follow-up #68 covers
each remaining per-control effect, not just the sample paths below.
"""
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "demo" / "v04-integrated-preview.html"
EXPECTED_MODULES = (
    "dashboard", "arrivals", "ota", "rooms", "housekeeping",
    "guest", "tasks", "revenue", "ai", "integrations",
    "ops_reservations", "ops_guests", "ops_folios", "ops_agencies",
    "ops_reports", "ops_rates", "ops_blocks", "ops_inventory",
    "ops_workflows", "ops_staff",
)


class FunctionalControlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        self.errors = []
        self.network = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.on("request", lambda req: self.network.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))

    def tearDown(self):
        self.assertEqual(self.errors, [], "Interactive demo emitted JavaScript errors")
        self.assertEqual(self.network, [], "Demo made an unexpected network call")
        self.page.close()

    def nav(self, name):
        self.page.locator(f'nav [data-nav="{name}"]').click()
        self.assertEqual(self.page.evaluate("() => page"), name)

    def test_all_20_modules_navigation_is_real_and_has_content(self):
        self.assertEqual(self.page.locator("nav [data-nav]").count(), 20)
        for name in EXPECTED_MODULES:
            with self.subTest(module=name):
                self.nav(name)
                self.assertEqual(
                    self.page.locator('nav [aria-current="page"]').get_attribute("data-nav"),
                    name,
                )
                content = self.page.locator("#content")
                self.assertTrue(content.is_visible())
                self.assertGreater(len(content.inner_text().strip()), 45)

    def test_every_enabled_visible_button_has_a_semantic_target(self):
        total = 0
        for name in EXPECTED_MODULES:
            self.nav(name)
            controls = self.page.locator("#content button").evaluate_all("""buttons =>
                buttons.filter(button => !button.disabled &&
                                      button.getClientRects().length > 0)
                    .map(button => ({
                        name: (button.textContent || '').trim().slice(0, 70),
                        id: button.id || '',
                        type: button.getAttribute('type') || '',
                        dataset: Object.keys(button.dataset),
                        aria: button.getAttribute('aria-label') || '',
                    }))""")
            total += len(controls)
            for control in controls:
                with self.subTest(module=name, button=control["name"]):
                    self.assertTrue(
                        control["id"] or control["dataset"] or
                        control["type"] == "submit",
                        "Visible active control has no defined action target",
                    )
        self.assertGreater(total, 35)

    def test_technical_block_is_clickable_explanation_not_a_fake_release(self):
        self.nav("housekeeping")
        blocked = self.page.locator(
            '#content button[data-room][aria-label^="Teknik blokaj ayrıntılarını görüntüle"]'
        )
        self.assertGreater(blocked.count(), 0)
        source_before = self.page.evaluate("() => JSON.stringify(state)")
        report_before = self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)")
        blocked.first.click()
        self.assertTrue(
            self.page.locator("#backdrop").evaluate(
                "(node) => node.classList.contains('open')"
            )
        )
        self.assertIn("Teknik kapalı", self.page.locator("#drawer").inner_text())
        self.page.locator("#closeDrawer").click()
        self.assertEqual(self.page.evaluate("() => JSON.stringify(state)"), source_before)
        self.assertEqual(
            self.page.evaluate("() => JSON.stringify(INITIAL_EVALUATION)"),
            report_before,
        )

    def test_core_booking_filter_and_workflow_controls_have_real_effects(self):
        self.nav("arrivals")
        filters = self.page.locator('#content [data-filter="blocked"]')
        self.assertGreater(filters.count(), 0)
        filters.first.click()
        self.assertEqual(
            self.page.locator('#content [data-filter="blocked"]').get_attribute("aria-pressed"),
            "true",
        )
        self.nav("ops_reservations")
        self.page.locator('[data-op-action="new-reservation"]').click()
        self.assertTrue(self.page.locator("#opsDraftForm").is_visible())
        before = self.page.evaluate("() => opsState.roomCount")
        self.page.locator('[data-op-action="add-room"]').click()
        self.assertEqual(self.page.evaluate("() => opsState.roomCount"), before + 1)
        self.page.locator('[data-op-action="close-form"]').click()
        self.assertEqual(self.page.locator("#opsDraftForm").count(), 0)
        self.nav("ops_workflows")
        self.assertTrue(self.page.locator("#wfNext").is_visible())
        before = self.page.evaluate("() => wfState.stage")
        self.page.locator("#wfNext").click()
        self.assertNotEqual(self.page.evaluate("() => wfState.stage"), before)

    def test_new_booking_draft_remains_visible_and_can_be_removed(self):
        self.nav("ops_reservations")
        original = self.page.evaluate("() => JSON.stringify(HOTEL_OPS_DATA)")
        self.page.locator('[data-op-action="new-reservation"]').click()
        self.page.locator("#opsDraftForm button[type=submit]").click()
        code = self.page.evaluate("() => opsState.drafts[0]?.id")
        self.assertTrue(code.startswith("DRAFT-"))
        self.page.locator('[data-op-action="close-form"]').click()
        tray = self.page.locator("#content")
        self.assertIn("Kurgusal rezervasyon taslakları", tray.inner_text())
        self.assertIn(code, tray.inner_text())
        self.assertEqual(self.page.evaluate("() => HOTEL_OPS_DATA.reservations.length"), 12)
        self.page.locator('[data-op-action="delete-draft"][data-draft-id="'+code+'"]').click()
        self.assertEqual(self.page.evaluate("() => opsState.drafts.length"), 0)
        self.assertNotIn(code, self.page.locator("#content").inner_text())
        self.assertEqual(self.page.evaluate("() => JSON.stringify(HOTEL_OPS_DATA)"), original)

    def test_adding_room_does_not_erase_edited_form_fields(self):
        self.nav("ops_reservations")
        self.page.locator('[data-op-action="new-reservation"]').click()
        form = self.page.locator("#opsDraftForm")
        form.locator('[name="draftLabel"]').fill("EXAMPLE GROUP")
        form.locator('[name="checkin"]').fill("2026-11-20")
        form.locator('[name="checkout"]').fill("2026-11-24")
        self.page.locator('[data-op-action="add-room"]').click()
        self.assertEqual(self.page.locator(".ops-room-field").count(), 2)
        self.assertEqual(form.locator('[name="draftLabel"]').input_value(), "EXAMPLE GROUP")
        self.assertEqual(form.locator('[name="checkin"]').input_value(), "2026-11-20")
        self.assertEqual(form.locator('[name="checkout"]').input_value(), "2026-11-24")
        self.assertEqual(self.page.evaluate("() => opsState.roomCount"), 2)
        self.assertEqual(form.locator('[name="adults1"]').input_value(), "2")
        self.assertEqual(form.locator('[name="children1"]').input_value(), "0")
        # Opening the already-open form must not erase edits.
        self.page.locator('[data-op-action="new-reservation"]').click()
        self.assertEqual(form.locator('[name="draftLabel"]').input_value(), "EXAMPLE GROUP")

    def test_invalid_draft_dates_show_reason_without_erasing_inputs(self):
        self.nav("ops_reservations")
        self.page.locator('[data-op-action="new-reservation"]').click()
        form = self.page.locator("#opsDraftForm")
        form.locator('[name="checkin"]').fill("2026-11-24")
        form.locator('[name="checkout"]').fill("2026-11-20")
        form.locator('button[type="submit"]').click()
        self.assertIn("Tarihler geçerli olmalı", form.inner_text())
        self.assertEqual(form.locator('[name="checkin"]').input_value(), "2026-11-24")
        self.assertEqual(form.locator('[name="checkout"]').input_value(), "2026-11-20")
        self.assertEqual(self.page.evaluate("() => opsState.drafts.length"), 0)

    def test_navigation_and_source_are_immutable_under_demo_ui_changes(self):
        source_before = self.page.evaluate("""() => JSON.stringify([
            INITIAL_EVALUATION, CANONICAL_DATA, HOTEL_OPS_REPORT
        ])""")
        self.nav("ops_reports")
        self.page.locator('[data-op-action="apply-report"]').click()
        self.nav("rooms")
        self.nav("ops_staff")
        self.nav("dashboard")
        self.assertEqual(
            self.page.evaluate("""() => JSON.stringify([
                INITIAL_EVALUATION, CANONICAL_DATA, HOTEL_OPS_REPORT
            ])"""),
            source_before,
        )


if __name__ == "__main__":
    unittest.main()
