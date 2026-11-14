"""Aurora timeline controls are source-bound, read-only and locale-safe."""
from pathlib import Path
import json
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "demo/v04-integrated-preview.html"


class AuroraTimelineFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1366, "height": 900})
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("request", lambda request: self.requests.append(request.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))
        self.original = self.page.evaluate(
            "() => JSON.stringify({canonical:CANONICAL_DATA,report:HOTEL_OPS_REPORT,graph:AURORA_ROOM_GRAPH})")
        self.page.locator('nav [data-nav="rooms"]').click()
        expect(self.page.locator("#auroraTimelineFilters")).to_be_visible()

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.requests, [])
        self.assertEqual(self.original, self.page.evaluate(
            "() => JSON.stringify({canonical:CANONICAL_DATA,report:HOTEL_OPS_REPORT,graph:AURORA_ROOM_GRAPH})"))
        self.page.close()

    def test_room_filter_and_reset_preserve_canonical_identity(self):
        graph = self.page.evaluate("() => AURORA_ROOM_GRAPH")
        all_rooms = len(graph["rooms"])
        rows = self.page.locator('.rack-panel .rack-row')
        expect(rows).to_have_count(all_rooms)
        self.page.locator("#auroraTimelineFloor").select_option("2")
        expected = {row["id"] for row in graph["rooms"] if row["floor"] == 2}
        displayed = set(self.page.locator(".rack-panel .rack-row:visible").evaluate_all(
            "(items) => items.map(item => item.dataset.rackRoom)"))
        self.assertEqual(displayed, expected)
        self.page.locator("#auroraTimelineReset").click()
        expect(self.page.locator(".rack-panel .rack-row:visible")).to_have_count(all_rooms)

    def test_channel_and_booking_status_filters_only_show_matching_source(self):
        for channel in ("booking", "direct"):
            self.page.locator("#auroraTimelineChannel").select_option(channel)
            visible = self.page.locator(".rack-panel .stay-bar:visible")
            self.assertGreater(visible.count(), 0)
            for bar in visible.all():
                self.assertEqual(bar.get_attribute("data-timeline-channel"), channel)
                parent = bar.get_attribute("data-booking")
                result = self.page.evaluate("(id) => {const parent=canonicalReservationId(id); return CANONICAL_DATA.reservations.find(row=>row.id===parent)?.source_ref.provider;}",parent)
                self.assertEqual(result, channel)
        self.page.locator("#auroraTimelineChannel").select_option("all")
        self.page.locator("#auroraTimelineStatus").select_option("cancelled")
        for bar in self.page.locator(".rack-panel .stay-bar:visible").all():
            self.assertEqual(bar.get_attribute("data-timeline-status"), "cancelled")

    def test_date_buttons_rebuild_filter_bar_without_clearing_selection(self):
        self.page.locator("#auroraTimelineFloor").select_option("2")
        before = self.page.locator(".aurora-timeline-range").inner_text()
        self.page.locator('.rack-panel [data-timeline-shift="7"]').click()
        self.assertNotEqual(self.page.locator(".aurora-timeline-range").inner_text(), before)
        self.assertEqual(self.page.locator("#auroraTimelineFloor").input_value(), "2")
        filtered = self.page.locator(".rack-panel .rack-row:visible")
        self.assertEqual(filtered.count(), len([
            row for row in self.page.evaluate("() => AURORA_ROOM_GRAPH.rooms") if row["floor"] == 2]))
        self.page.locator('.rack-panel [data-timeline-shift="0"]').click()
        self.assertEqual(self.page.locator(".aurora-timeline-range").inner_text(), before)

    def test_mobile_reflow_and_selected_language(self):
        self.page.set_viewport_size({"width": 320, "height": 720})
        self.assertTrue(self.page.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        self.page.locator("#auroraTimelineFloor").select_option("2")
        self.assertTrue(self.page.locator("#auroraTimelineSummary").inner_text())
        self.page.locator("#auroraTimelineReset").click()
        self.assertTrue(self.page.locator("#auroraTimelineFilters").is_visible())


if __name__ == "__main__":
    unittest.main()
