"""Chromium tests for the standalone offline fictional PMS suite."""
from pathlib import Path
import re
import os
import json
import tempfile
import importlib.util
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
SNAPSHOT=json.loads((ROOT/'examples/fictional-hotel.json').read_text())
REPORT=json.loads((ROOT/'examples/operations-evaluation.json').read_text())
HTML=ROOT/'demo/hotel-suite.html'
class TestBrowserSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        options={'headless':True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):options['executable_path']=os.environ['KONAKLAMAFLOW_CHROMIUM']
        cls.browser=cls.playwright.chromium.launch(**options)
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.playwright.stop()
    def setUp(self):
        self.page=self.browser.new_page(viewport={'width':1440,'height':900})
        self.errors=[];self.requests=[]
        self.page.on('pageerror',lambda err:self.errors.append(str(err)))
        self.page.on('request',lambda req:self.requests.append(req.url))
        self.page.set_content(HTML.read_text(encoding="utf-8"))
    def tearDown(self):
        self.assertEqual(self.errors,[])
        # file:// initial document request is expected; all network requests rejected.
        self.assertEqual([url for url in self.requests if not url.startswith('file://')],[])
        self.page.close()
    def test_visual_theme_and_presentation_do_not_change_rule_report(self):
        original=self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)')
        self.assertEqual(self.page.locator('#kfTheme').input_value(),'light')
        self.page.locator('#kfTheme').select_option('dark')
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfTheme'),'dark')
        self.page.locator('#kfTheme').select_option('night')
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfTheme'),'night')
        self.page.locator('#kfMode').click()
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfMode'),'presentation')
        self.assertEqual(self.page.locator('#kfMode').get_attribute('aria-pressed'),'true')
        self.assertEqual(self.page.locator('nav button').count(),10)
        self.assertEqual(self.page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)'),original)
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertFalse(self.page.locator('#exportButton').is_disabled())
        self.page.locator('#kfMode').click()
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfMode'),'operator')

    def test_visual_motion_toggle_and_reduced_motion(self):
        toggle=self.page.locator('#kfMotion')
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfMotion'),'on')
        toggle.click()
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfMotion'),'off')
        toggle.click()
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfMotion'),'on')
        self.page.emulate_media(reduced_motion='reduce')
        self.page.wait_for_function("document.documentElement.dataset.kfMotion === 'off'")
        self.assertEqual(self.page.evaluate('() => document.documentElement.dataset.kfMotion'),'off')
        self.assertTrue(toggle.is_disabled())

    def test_visual_modes_keep_mobile_body_in_bounds(self):
        for width in (320,375,768):
            self.page.set_viewport_size({'width':width,'height':800})
            for mode in ('presentation','operator'):
                if (self.page.evaluate('() => document.documentElement.dataset.kfMode')!=mode):
                    self.page.locator('#kfMode').click()
                self.assertTrue(self.page.evaluate('() => document.documentElement.scrollWidth <= window.innerWidth'),(width,mode))

    def test_dashboard_metrics(self):
        self.assertIn('Resepsiyon kontrol merkezi',self.page.locator('h1').inner_text())
        self.assertIn('18',self.page.locator('.metrics').inner_text())
        self.assertGreater(self.page.locator('[data-booking]').count(),1)
    def test_navigation_all_modules(self):
        self.assertEqual(self.page.locator('nav button').count(),10)
        for section in ('arrivals','ota','rooms','housekeeping','guest','tasks','revenue','ai','integrations'):
            self.page.locator(f'nav [data-nav="{section}"]').click()
            self.assertTrue(self.page.locator('#content').inner_text().strip(),section)
    def test_search_and_filter(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('#search').fill('KF1003')
        self.assertEqual(self.page.locator('.table tbody tr').count(),1)
        self.page.locator('[data-filter="review_ready"]').click()
        self.assertIn('Kayıt bulunamadı',self.page.locator('#content').inner_text())
    def test_details_and_approval(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('[data-booking="KF1003"]').first.click()
        self.assertTrue(self.page.locator('#backdrop').evaluate('el=>el.classList.contains("open")'))
        self.assertIn('Kat hizmetleri',self.page.locator('#drawer').inner_text())
        self.page.locator('#queueReview').click()
        self.assertIn('kuyruğuna eklendi',self.page.locator('#toast').inner_text())
    def test_housekeeping_demo_state_and_reset(self):
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        row=self.page.locator('.table tbody tr').filter(has=self.page.locator('td.tdstrong',has_text='303'))
        self.assertIn('Kontrol edildi',row.inner_text())
        self.page.locator('#resetButton').click()
        self.assertIn('Kirli',self.page.locator('.table tbody tr').filter(has=self.page.locator('td.tdstrong',has_text='303')).inner_text())
    def test_ota_review(self):
        self.page.locator('nav [data-nav="ota"]').click()
        self.page.locator('[data-event="E1005"]').click()
        self.assertIn('Eşleşmedi',self.page.locator('#drawer').inner_text())
        self.page.locator('#queueEvent').click()
        self.assertIn('inceleme kuyruğuna alındı',self.page.locator('#toast').inner_text())
    def test_guest_draft_not_sent(self):
        self.page.locator('nav [data-nav="guest"]').click()
        self.page.locator('[data-draft="KF1002"]').click()
        self.assertIn('kesin olarak garanti edemiyoruz',self.page.locator('#drawer').inner_text())
        self.assertEqual(self.page.locator('#drawer button').count(),2)
    def test_mobile_no_horizontal_overflow(self):
        for width in (320,375,390,768,1440):
            self.page.set_viewport_size({'width':width,'height':820})
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),width)
    def test_no_external_exfiltration(self):
        self.page.locator('nav [data-nav="ai"]').click()
        self.page.locator('nav [data-nav="integrations"]').click()
        self.assertFalse(self.page.evaluate('typeof window.fetch === "undefined"')) # fetch exists but is never called
        self.assertEqual(len([v for v in self.requests if v.startswith('https://')]),0)


    def test_python_report_parity_and_no_second_browser_rule_engine(self):
        from konaklamaflow.experience_engine import evaluate
        self.assertEqual(evaluate(SNAPSHOT),REPORT)
        self.assertEqual(self.page.evaluate('() => INITIAL_EVALUATION'),REPORT)
        visible=self.page.evaluate('() => state.reservations.map(b => ({id:b.id,status:reviewOf(b).status,suggested:reviewOf(b).suggested}))')
        expected=[dict(id=x['id'],status=x['status'],suggested=x['suggested_room']) for x in REPORT['arrivals']]
        self.assertEqual(visible,expected)
        self.assertIsNone(re.search(r'function\s+(?:evaluate|eligible|proposal|overlaps)\s*\(',HTML.read_text()))

    def test_dialog_focus_trap_escape_and_background_inert(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        opener=self.page.locator('[data-booking="KF1003"]').first
        opener.press('Enter')
        self.assertTrue(self.page.locator('#closeDrawer').evaluate('el=>el===document.activeElement'))
        self.assertTrue(self.page.locator('.app').evaluate('el=>el.inert'))
        self.assertEqual(self.page.locator('#drawer').get_attribute('aria-labelledby'),'drawerTitle')
        self.page.keyboard.press('Shift+Tab')
        self.assertEqual(self.page.evaluate('() => document.activeElement.id'),'queueReview')
        self.page.keyboard.press('Tab')
        self.assertEqual(self.page.evaluate('() => document.activeElement.id'),'closeDrawer')
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('.app').evaluate('el=>el.inert'))
        self.assertTrue(opener.evaluate('el=>el===document.activeElement'))

    def test_housekeeping_visual_change_invalidates_every_readiness_and_export(self):
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.assertTrue(self.page.evaluate('() => reportStale'))
        self.assertEqual(self.page.evaluate("() => state.reservations.filter(b=>reviewOf(b).status==='review_ready').length"),0)
        self.assertTrue(self.page.locator('#exportButton').is_disabled())
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('[data-filter="review_ready"]').click()
        self.assertIn('Kayıt bulunamadı',self.page.locator('#content').inner_text())
        self.assertIn('Rapor güncel değil',self.page.locator('#content').inner_text())
        self.page.locator('#resetButton').click()
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertFalse(self.page.locator('#exportButton').is_disabled())
        self.assertEqual(self.page.evaluate("() => state.reservations.filter(b=>reviewOf(b).status==='review_ready').length"),REPORT['summary']['review_ready'])

    def test_export_is_exact_authoritative_fictional_report(self):
        with self.page.expect_download() as download:
            self.page.locator('#exportButton').click()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json';download.value.save_as(path)
            self.assertEqual(json.loads(path.read_text()),REPORT)
        self.assertFalse(REPORT['approval_policy']['pms_writes'])
        self.assertFalse(REPORT['approval_policy']['payments'])
        self.assertFalse(REPORT['approval_policy']['kbs'])

    def test_review_queue_is_idempotent_for_open_and_in_progress_tasks(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('[data-booking="KF1003"]').first.click()
        self.page.locator('#queueReview').click()
        self.page.evaluate("() => {state.tasks.find(t=>t.kind==='frontdesk'&&t.reservation_id==='KF1003').status='in_progress';}")
        before=self.page.evaluate('() => state.tasks.length')
        log_before=self.page.evaluate('() => log.length')
        self.page.locator('[data-booking="KF1003"]').first.click()
        self.page.locator('#queueReview').click()
        self.assertEqual(self.page.evaluate('() => state.tasks.length'),before)
        self.assertEqual(self.page.evaluate('() => log.length'),log_before)
        self.assertIn('zaten açık',self.page.locator('#toast').inner_text())

    def test_new_task_identifier_cannot_collide(self):
        self.page.evaluate("() => state.tasks.push({id:'TDEMO1',kind:'frontdesk',room_id:null,reservation_id:'KF1001',status:'done',priority:'low'})")
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('[data-booking="KF1003"]').first.click()
        self.page.locator('#queueReview').click()
        ids=self.page.evaluate('() => state.tasks.map(t=>t.id)')
        self.assertEqual(len(ids),len(set(ids)))
        self.assertIn('TDEMO2',ids)

    def test_repeated_event_review_is_idempotent(self):
        self.page.locator('nav [data-nav="ota"]').click()
        self.page.locator('[data-event="E1005"]').click();self.page.locator('#queueEvent').click()
        before=self.page.evaluate('() => log.length')
        self.page.locator('[data-event="E1005"]').click();self.page.locator('#queueEvent').click()
        self.assertEqual(self.page.evaluate('() => log.length'),before)
        self.assertIn('zaten inceleme',self.page.locator('#toast').inner_text())

    def test_task_completion_invalidates_report_without_touching_original_fixture(self):
        self.page.locator('nav [data-nav="tasks"]').click()
        self.page.locator('[data-task="T1001"]').click()
        self.assertTrue(self.page.evaluate('() => reportStale'))
        self.assertTrue(self.page.locator('[data-task="T1001"]').is_disabled())
        self.assertEqual(self.page.evaluate('() => INITIAL_DATA.tasks.find(t=>t.id==="T1001").status'),'open')

    def test_untrusted_snapshot_and_reason_text_never_becomes_markup(self):
        self.page.evaluate("""() => {
            state.reservations[0].external_ref='<img src="https://example.invalid/" onerror="window.syntheticInjected=true">';
            INITIAL_EVALUATION.arrivals[0].blockers=['<script>window.syntheticInjected=true</script>'];
            showBooking(state.reservations[0].id);
        }""")
        self.assertEqual(self.page.locator('#drawer img,#drawer script').count(),0)
        self.assertIn('<img',self.page.locator('#drawer').inner_text())
        self.assertIn('<script>',self.page.locator('#drawer').inner_text())
        self.assertIsNone(self.page.evaluate('() => window.syntheticInjected'))

    def test_generated_json_cannot_end_its_script_element(self):
        spec=importlib.util.spec_from_file_location('suite_generator',ROOT/'scripts/generate_suite_demo.py')
        generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
        payload={'note':'</script><script>unsafe()</script>\u2028&'}
        safe=generator.safe_json(payload)
        self.assertNotIn('</script>',safe)
        self.assertNotIn('<',safe)
        self.assertEqual(json.loads(safe),payload)

    def test_financial_view_displays_separate_python_currency_totals(self):
        self.page.locator('nav [data-nav="revenue"]').click()
        for currency,amount in REPORT['financial_review']['reservation_totals_by_currency'].items():
            self.assertIn(currency,self.page.locator('#content').inner_text())
            self.assertIn(amount,self.page.locator('#content').inner_text())
        self.assertIn('günlük gelir',self.page.locator('#content').inner_text())
        self.assertIn('ADR',self.page.locator('#content').inner_text())

    def test_filters_and_search_have_keyboard_accessible_names(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('[data-filter="blocked"]').press('Enter')
        self.assertEqual(self.page.locator('[data-filter="blocked"]').get_attribute('aria-pressed'),'true')
        self.assertTrue(self.page.locator('[data-filter="blocked"]').evaluate('el=>el===document.activeElement'))
        self.page.locator('nav [data-nav="ota"]').click()
        self.assertEqual(self.page.locator('#search').get_attribute('aria-label'),'OTA olaylarında ara')
        self.assertEqual(self.page.locator('button').evaluate_all("els=>els.filter(el=>!el.textContent.trim()&&!el.getAttribute('aria-label')).length"),0)

    def test_nested_room_dialog_keeps_original_focus_return(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        opener=self.page.locator('[data-booking="KF1003"]').first
        opener.click()
        self.page.evaluate("() => showRoom('303')")
        self.assertEqual(self.page.locator('#drawerTitle').inner_text(),'Oda 303')
        self.page.keyboard.press('Escape')
        self.assertTrue(opener.evaluate('el=>el===document.activeElement'))

    def test_queue_action_restores_focus_after_render(self):
        self.page.locator('nav [data-nav="arrivals"]').click()
        self.page.locator('[data-booking="KF1003"]').first.click()
        self.page.locator('#queueReview').click()
        self.assertFalse(self.page.locator('.app').evaluate('el=>el.inert'))
        self.assertTrue(self.page.locator('[data-booking="KF1003"]').first.evaluate('el=>el===document.activeElement'))

    def load_generated_snapshot(self,snapshot):
        from konaklamaflow.experience_engine import evaluate
        spec=importlib.util.spec_from_file_location('suite_generator_scenario',ROOT/'scripts/generate_suite_demo.py')
        generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
        report=evaluate(snapshot)
        self.page.close()
        self.page=self.browser.new_page(viewport={'width':1440,'height':900})
        self.page.on('pageerror',lambda err:self.errors.append(str(err)))
        self.page.on('request',lambda req:self.requests.append(req.url))
        self.page.set_content(generator.embed(HTML.read_text(encoding='utf-8'),snapshot,report))
        return report

    def test_ota_labels_and_counts_use_authoritative_event_review(self):
        snapshot=json.loads(json.dumps(SNAPSHOT))
        snapshot['channel_events'][0]['channel']='expedia'
        report=self.load_generated_snapshot(snapshot)
        event=next(item for item in report['event_reviews'] if item['id']=='E1001')
        self.assertEqual(event['status'],'needs_review')
        self.assertIn('CHANNEL_REFERENCE_MISMATCH',event['reason_codes'])
        self.page.locator('nav [data-nav="ota"]').click()
        row=self.page.locator('.table tbody tr').filter(has=self.page.locator('[data-event="E1001"]'))
        self.assertIn('İnceleme',row.inner_text())
        self.assertIn('Eşleşmedi',row.inner_text())
        self.assertEqual(self.page.evaluate("() => pendingChannel().length"),sum(item['status']!='matched' for item in report['event_reviews']))
        self.page.locator('[data-event="E1001"]').click()
        self.assertIn('Kanal ve dış referans eşleşmiyor',self.page.locator('#drawer').inner_text())
        self.assertIn('Eşleşmedi',self.page.locator('#drawer').inner_text())

    def test_graphic_rooms_preserve_pending_and_cancelled_physical_holds(self):
        snapshot=json.loads(json.dumps(SNAPSHOT))
        cancelled=next(b for b in snapshot['reservations'] if b['id']=='KF1006')
        cancelled['arrival_state']='checked_in'
        pending=dict(snapshot['reservations'][0],id='SYNTHETIC_PENDING',external_ref='PENDING_REF',pms_ref='PENDING_PMS',room_id='103',status='pending',arrival_state='expected')
        snapshot['reservations'].append(pending)
        overdue=next(b for b in snapshot['reservations'] if b['id']=='KF1012')
        overdue.update(status='no_show',arrival_state='checked_in',arrival='2026-11-10',departure='2026-11-11')
        report=self.load_generated_snapshot(snapshot)
        expected={room['id'] for room in report['room_plan'] if room['held_reservation_ids']}
        self.assertTrue({'102','103','403'} <= expected)
        self.assertEqual(set(self.page.evaluate('() => [...occupiedIds()]')),expected)
        self.page.locator('nav [data-nav="rooms"]').click()
        for room in ('102','103','403'):
            self.assertIn('occupied',self.page.locator('.room[data-room="'+room+'"]').get_attribute('class'))
        self.page.locator('.room[data-room="102"]').click()
        self.assertIn('KF1006',self.page.locator('#drawer').inner_text())
        self.assertNotIn('aktif tahsis yok',self.page.locator('#drawer').inner_text())


    def test_guided_stories_are_bound_to_the_authoritative_report_and_idle_initially(self):
        data=self.page.evaluate('() => DEMO_STORIES')
        self.assertEqual(data['snapshot_sha256'],REPORT['snapshot_sha256'])
        self.assertEqual(data['mode'],'SCRIPTED_FICTIONAL_REVIEW')
        self.assertEqual({s['id'] for s in data['stories']},{'twin-review','housekeeping-review','channel-review','arrival-review'})
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),'-1')
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'false')
        self.assertIn('gerçek AI/API çağrısı yok',self.page.locator('#tourPanel').inner_text())

    def test_manual_tour_reveals_engine_evidence_without_mutating_source_or_authorizing(self):
        before=self.page.evaluate('() => JSON.stringify(state)')
        story=self.page.evaluate('() => currentStory()')
        for index,step in enumerate(story['steps']):
            self.page.locator('#tourNext').click()
            self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),str(index))
            self.assertIn(step['title'],self.page.locator('.story-evidence').inner_text())
            for evidence in step['evidence']:
                self.assertIn(evidence['value'],self.page.locator('.story-evidence').inner_text())
        self.assertTrue(self.page.locator('#tourNext').is_disabled())
        self.assertEqual(self.page.evaluate('() => JSON.stringify(state)'),before)
        self.assertFalse(self.page.evaluate('() => reportStale'))
        self.assertFalse(self.page.locator('#exportButton').is_disabled())
        self.assertIn('Gerçek check-in veya mesaj gönderimi yapılmadı',self.page.locator('.tour-status').inner_text())

    def test_autoplay_pause_and_reset_cancel_pending_timers(self):
        self.page.clock.install()
        self.page.locator('#tourPlay').click()
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'true')
        self.page.clock.fast_forward(2101)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),'1')
        self.page.locator('#tourPause').click()
        self.page.clock.fast_forward(10000)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),'1')
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'false')
        self.page.locator('#tourReset').click()
        self.page.clock.fast_forward(10000)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),'-1')

    def test_navigation_and_dialog_stop_story_without_losing_modal_focus(self):
        self.page.clock.install()
        self.page.locator('#tourPlay').click()
        opener=self.page.locator('.rack-row [data-room="303"]')
        opener.click()
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'false')
        self.page.clock.fast_forward(10000)
        self.assertEqual(self.page.evaluate('() => storyStep'),0)
        self.page.keyboard.press('Escape')
        self.assertTrue(opener.evaluate('el=>el===document.activeElement'))
        self.page.locator('#tourPlay').click()
        self.page.locator('nav [data-nav="ota"]').click()
        self.page.clock.fast_forward(10000)
        self.assertFalse(self.page.evaluate('() => storyPlaying'))
        self.page.locator('nav [data-nav="dashboard"]').click()
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'false')

    def test_scenario_change_cancels_playback_and_positive_case_is_only_human_review(self):
        self.page.clock.install()
        self.page.locator('#tourPlay').click()
        self.page.locator('#tourScenario').select_option('arrival-review')
        self.page.clock.fast_forward(10000)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),'-1')
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-story-id'),'arrival-review')
        for _ in range(5):self.page.locator('#tourNext').click()
        self.assertIn('yetkili personel ön incelemesi',self.page.locator('.story-evidence').inner_text())
        self.assertFalse(REPORT['approval_policy']['pms_writes'])
        self.assertFalse(REPORT['approval_policy']['payments'])
        self.assertFalse(REPORT['approval_policy']['kbs'])

    def test_reduced_motion_requires_explicit_step_and_stale_report_disables_tour(self):
        self.page.clock.install()
        self.page.emulate_media(reduced_motion='reduce')
        self.page.locator('#tourPlay').click()
        self.page.clock.fast_forward(10000)
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-current-step'),'0')
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'false')
        self.page.locator('nav [data-nav="housekeeping"]').click()
        self.page.locator('[data-hk="303"]').click()
        self.page.locator('nav [data-nav="dashboard"]').click()
        self.assertTrue(self.page.locator('#tourPlay').is_disabled())
        self.assertTrue(self.page.locator('#tourNext').is_disabled())
        self.assertTrue(self.page.locator('#tourScenario').is_disabled())
        self.assertEqual(self.page.locator('#tourPanel').get_attribute('data-playing'),'false')

    def test_room_timeline_renders_literal_dates_and_report_holds_without_new_decisions(self):
        self.assertEqual(self.page.locator('.rack-header .rack-day').count(),7)
        self.assertEqual(self.page.locator('.rack-header .rack-day.today').count(),1)
        self.assertIn('KF1003',self.page.locator('[data-rack-room="303"]').inner_text())
        self.assertIn('TEKNİK BLOKAJ',self.page.locator('[data-rack-room="401"]').inner_text())
        before=self.page.evaluate('() => JSON.stringify(state)')
        self.page.locator('[data-timeline-shift="7"]').click()
        self.assertEqual(self.page.evaluate('() => timelineOffset'),7)
        self.assertEqual(self.page.evaluate('() => JSON.stringify(state)'),before)
        self.page.locator('[data-timeline-shift="0"]').click()
        self.assertEqual(self.page.evaluate('() => timelineOffset'),0)

    def test_scheduled_maintenance_is_visible_and_uses_engine_current_day_warning(self):
        snapshot=json.loads(json.dumps(SNAPSHOT))
        snapshot['rooms'][0]['maintenance']=[{'start':'2026-11-12','end':'2026-11-14'}]
        report=self.load_generated_snapshot(snapshot)
        self.page.locator('nav [data-nav="rooms"]').click()
        self.assertIn('PLANLI BAKIM',self.page.locator('[data-rack-room="B01"]').inner_text())
        self.assertIn('ooo',self.page.locator('.room[data-room="B01"]').get_attribute('class'))
        self.page.locator('.room[data-room="B01"]').click()
        self.assertIn('2026-11-12',self.page.locator('#drawer').inner_text())
        self.assertIn('personel incelemesi gerekli',self.page.locator('#drawer').inner_text())

    def test_tour_keyboard_focus_and_mobile_priority(self):
        self.page.locator('#tourNext').press('Enter')
        self.assertTrue(self.page.locator('#tourNext').evaluate('el=>el===document.activeElement'))
        self.page.set_viewport_size({'width':390,'height':844})
        self.assertLess(self.page.locator('#tourPanel').bounding_box()['y'],self.page.locator('.rack-panel').first.bounding_box()['y'])
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))


if __name__=='__main__':
    unittest.main()
