"""Interactive timeline regressions using the real offline HTML and Chromium."""
from pathlib import Path
import re
import unittest
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[2]
HTML=(ROOT/'demo/v04-integrated-preview.html').read_text(encoding='utf-8')

class AuroraTimelineBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=sync_playwright().start()
        cls.browser=cls.p.chromium.launch(headless=True)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()
    def setUp(self):
        self.page=self.browser.new_page(viewport={'width':1366,'height':900})
        self.errors=[]
        self.requests=[]
        self.page.on('pageerror',lambda error:self.errors.append(str(error)))
        self.page.on('request',lambda request:self.requests.append(request.url))
        self.page.set_content(HTML)
        self.page.locator('nav [data-nav="rooms"]').click()
        expect(self.page.locator('.aurora-timeline')).to_be_visible()
    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors,[])
        self.assertEqual(self.requests,[])

    def test_source_and_rows(self):
        timeline=self.page.locator('.aurora-timeline')
        expect(timeline).to_have_attribute('data-source-state','synthetic_snapshot')
        expect(timeline.locator('.rack-row')).to_have_count(18)
        expect(timeline.locator('.rack-day')).to_have_count(7)
        self.assertEqual(timeline.locator('.rack-cells span').count(),18*7)
        self.assertEqual(self.page.locator('.aurora-room-card').count(),18)
        self.assertEqual(self.page.evaluate('() => CANONICAL_DATA.room_stays.length'),12)

    def test_dates_filters_and_checkout_exclusive(self):
        timeline=self.page.locator('.aurora-timeline')
        self.page.locator('#auroraTimelineDays').select_option('14')
        expect(timeline).to_have_attribute('data-days','14')
        expect(timeline.locator('.rack-day')).to_have_count(14)
        # A one-night reservation must occupy a single date cell, never its checkout day.
        facts=self.page.evaluate("""() => {
            const s=CANONICAL_DATA.room_stays.find(x=>x.room_id&&x.departure>x.arrival);
            const first=s.arrival;
            return {arrival:first,departure:s.departure,
                    span:auroraTimelineWindow(first,s.departure,[first,s.departure])};
        }""")
        self.assertEqual(facts['span']['width'],1)
        self.page.locator('#auroraTimelineDays').select_option('21')
        expect(timeline).to_have_attribute('data-days','21')
        self.page.locator('#auroraTimelineStart').fill('2026-11-15')
        expect(timeline.locator('.rack-day').first).to_contain_text('2026-11-15')
        self.page.locator('[data-timeline-shift="0"]').last.click()
        expect(timeline.locator('.rack-day').first).to_contain_text('2026-11-11')
        self.page.locator('#auroraTimelineFloor').select_option('2')
        self.assertGreater(timeline.locator('.rack-row').count(),0)
        self.assertLess(timeline.locator('.rack-row').count(),18)
        self.page.locator('#auroraTimelineStatus').select_option('cancelled')
        self.assertLessEqual(timeline.locator('.rack-row').count(),18)

    def test_reservation_navigation_and_read_only(self):
        link=self.page.locator('.aurora-timeline .aurora-stay').first
        self.assertGreater(self.page.locator('.aurora-timeline .aurora-stay').count(),0)
        booking=link.get_attribute('data-canonical-reservation')
        self.assertTrue(booking.startswith('KF'))
        link.click()
        expect(self.page.locator('#backdrop')).to_have_class(re.compile(r'\\bopen\\b'))
        expect(self.page.locator('#drawer')).to_contain_text(booking)
        self.assertEqual(self.page.evaluate('() => CANONICAL_DATA.folios.length'),3)

    def test_mobile_rtl_and_reduced_motion(self):
        self.page.set_viewport_size({'width':375,'height':812})
        self.page.locator('#auroraTimelineDays').select_option('21')
        self.assertTrue(self.page.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))
        self.assertGreater(self.page.locator('.aurora-timeline .rack-scroll').evaluate('(x)=>x.scrollWidth'),375)
        self.page.evaluate("() => document.documentElement.dataset.kfMotion='off'")
        transition=self.page.locator('.aurora-timeline .aurora-stay').first.evaluate('(x)=>getComputedStyle(x).transitionDuration')
        self.assertEqual(transition,'0s')

if __name__=="__main__":
    unittest.main()
