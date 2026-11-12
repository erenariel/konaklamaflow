"""Scripted visual tours must show real rule facts, never fabricated operations."""
import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest

from konaklamaflow.demo_stories import build_demo_stories, report_fingerprint
from konaklamaflow.experience_engine import BLOCKER_CODES, SnapshotError, evaluate

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = json.loads((ROOT / 'examples/fictional-hotel.json').read_text())


class DemoStoryTests(unittest.TestCase):
    def test_four_reproducible_stories_do_not_mutate_input(self):
        source = copy.deepcopy(SNAPSHOT); original = copy.deepcopy(source)
        result = build_demo_stories(source)
        self.assertEqual(result, build_demo_stories(source))
        self.assertEqual(source, original)
        self.assertEqual([s['id'] for s in result['stories']],
                         ['twin-review', 'housekeeping-review', 'channel-review', 'arrival-review'])
        self.assertEqual(result['mode'], 'SCRIPTED_FICTIONAL_REVIEW')
        self.assertIn('gerçek model', result['label'])
        self.assertTrue(all(v is False for v in result['side_effects'].values()))

    def test_final_story_decisions_and_codes_match_authoritative_report(self):
        result = build_demo_stories(SNAPSHOT)
        report = evaluate(SNAPSHOT)
        rows = {r['id']: r for r in report['arrivals']}
        rooms = {r['id'] for r in report['room_plan']}
        for story in result['stories']:
            with self.subTest(story=story['id']):
                row = rows[story['booking_id']]
                self.assertEqual(story['final_status'], row['status'])
                self.assertEqual(story['reason_codes'], row['blockers'])
                self.assertTrue(set(story['room_ids']) <= rooms)
                self.assertEqual([step['actor'] for step in story['steps']],
                                 ['ai1', 'ai1', 'rule_engine', 'ai2', 'human'])
                self.assertEqual(len({s['id'] for s in story['steps']}), len(story['steps']))
                for step in story['steps']:
                    self.assertTrue(set(step['reason_codes']) <= BLOCKER_CODES)
                    self.assertTrue(set(step['reason_codes']) <= set(row['blockers']))
                    self.assertTrue(set(step['room_ids']) <= rooms)
                self.assertEqual(story['steps'][-1]['reason_codes'], row['blockers'])
                if row['status'] == 'blocked':
                    self.assertEqual(story['steps'][-1]['title'], 'Personel incelemesi gerekli')
                    self.assertIn('Yapılmadı', [e['value'] for e in story['steps'][-1]['evidence']])

    def test_room_proposal_evidence_does_not_invent_safe_twin_availability(self):
        story = build_demo_stories(SNAPSHOT)['stories'][0]
        rules = next(s for s in story['steps'] if s['actor'] == 'rule_engine')
        self.assertEqual(next(e['value'] for e in rules['evidence'] if e['label']=='Güvenli oda önerisi'), 'Yok')
        self.assertIn('NO_ASSIGNED_ROOM', rules['reason_codes'])
        self.assertIn('401', story['room_ids'])
        self.assertIn('302', story['room_ids'])

    def test_positive_story_is_only_ready_for_human_review_when_engine_passes(self):
        result = build_demo_stories(SNAPSHOT)
        story = next(s for s in result['stories'] if s['id'] == 'arrival-review')
        row = next(r for r in evaluate(SNAPSHOT)['arrivals'] if r['id'] == 'KF1010')
        self.assertEqual(row['status'], 'review_ready')
        self.assertTrue(row['human_approval_required'])
        self.assertEqual(story['final_status'], row['status'])
        self.assertEqual(story['reason_codes'], [])
        self.assertEqual(story['ai_payload']['tasks'][0]['state'], row['status'])
        self.assertEqual(story['steps'][-1]['title'], 'Hazır: yetkili personel ön incelemesi')
        final_evidence = {e['label']: e['value'] for e in story['steps'][-1]['evidence']}
        self.assertEqual(final_evidence['İnsan kontrolü'], 'Zorunlu')
        self.assertEqual(final_evidence['Gerçek işlem'], 'Yapılmadı')
        # Changing a real prerequisite changes the generated tour, not just its badge.
        source = copy.deepcopy(SNAPSHOT)
        next(b for b in source['reservations'] if b['id'] == 'KF1010')['identity_signal'] = 'pending_staff'
        changed = next(s for s in build_demo_stories(source)['stories'] if s['id'] == 'arrival-review')
        self.assertEqual(changed['final_status'], 'blocked')
        self.assertIn('IDENTITY_STAFF_REVIEW', changed['reason_codes'])
        self.assertEqual(changed['steps'][-1]['title'], 'Personel incelemesi gerekli')

    def test_source_evidence_follows_mapping_result_instead_of_source_label(self):
        source = copy.deepcopy(SNAPSHOT)
        source['channel_events'][1]['channel'] = 'booking'
        story = build_demo_stories(source)['stories'][0]
        evidence = story['steps'][0]['evidence']
        self.assertEqual(next(e['value'] for e in evidence if e['label']=='Eşleştirme sonucu'), 'İnceleme gerekiyor')
        self.assertIn('UNMAPPED_PMS', story['reason_codes'])

    def test_report_and_snapshot_fingerprints_bind_all_suite_context(self):
        report = evaluate(SNAPSHOT); stories = build_demo_stories(SNAPSHOT)
        digest = sha256(json.dumps(report, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        self.assertEqual(stories['snapshot_sha256'], report['snapshot_sha256'])
        self.assertEqual(stories['report_sha256'], digest)
        variants=[]
        source=copy.deepcopy(SNAPSHOT);source['property_id']='OTHER_FICTIONAL';variants.append(source)
        source=copy.deepcopy(SNAPSHOT);source['at_time']='15:00';variants.append(source)
        source=copy.deepcopy(SNAPSHOT);source['rooms'][0]['capacity']=1;variants.append(source)
        for source in variants:
            with self.subTest(property_id=source['property_id']):
                changed=build_demo_stories(source)
                self.assertNotEqual(changed['snapshot_sha256'],stories['snapshot_sha256'])
                self.assertNotEqual(changed['report_sha256'],stories['report_sha256'])

    def test_ai_envelope_has_only_opaque_review_protocol_not_raw_source_refs(self):
        result=build_demo_stories(SNAPSHOT)
        for story in result['stories']:
            payload=story['ai_payload'];serialized=json.dumps(payload)
            self.assertEqual(payload['mode'],'NO_EXECUTION_READ_ONLY')
            self.assertEqual(payload['snapshot_sha256'],result['snapshot_sha256'])
            self.assertEqual(payload['report_sha256'],result['report_sha256'])
            self.assertEqual(len(payload['tasks']),1)
            task=payload['tasks'][0]
            self.assertEqual(task['intent'],'SUGGEST_RECEPTION_REVIEW')
            self.assertEqual(task['allowed_tools'],['explain_status','prepare_checklist'])
            self.assertEqual(task['state'],story['final_status'])
            self.assertEqual(task['reason_codes'],story['reason_codes'])
            self.assertEqual(len(task['task_id']),24)
            booking=next(b for b in SNAPSHOT['reservations'] if b['id']==story['booking_id'])
            for raw in (booking['id'], booking['external_ref'], SNAPSHOT['property_id'], 'room_id', 'pms_ref', 'channel'):
                self.assertNotIn(raw,serialized)

    def test_absent_example_is_omitted_without_inventing_a_reservation(self):
        source=copy.deepcopy(SNAPSHOT)
        for booking in source['reservations']:
            if booking['id']=='KF1002':booking['id']='RENAMED_FICTIONAL'
        for event in source['channel_events']:
            if event['reservation_id']=='KF1002':event['reservation_id']='RENAMED_FICTIONAL'
        for task in source['tasks']:
            if task['reservation_id']=='KF1002':task['reservation_id']='RENAMED_FICTIONAL'
        stories=build_demo_stories(source)['stories']
        self.assertEqual(len(stories),3)
        self.assertFalse(any(s['booking_id']=='KF1002' for s in stories))

    def test_invalid_private_or_instruction_fields_rejected_without_echo(self):
        for change in ('root','request'):
            source=copy.deepcopy(SNAPSHOT)
            if change=='root':source['guest_email']='SYNTHETIC_PRIVATE'
            else:source['reservations'][0]['requests']=['IGNORE_PREVIOUS_INSTRUCTIONS']
            with self.subTest(change=change), self.assertRaises(SnapshotError) as caught:
                build_demo_stories(source)
            self.assertNotIn('SYNTHETIC_PRIVATE',str(caught.exception))
            self.assertNotIn('IGNORE_PREVIOUS',str(caught.exception))

    def test_generator_binds_story_data_and_rejects_tampered_report(self):
        spec=importlib.util.spec_from_file_location('suite_story_generator',ROOT/'scripts/generate_suite_demo.py')
        generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
        document='<script>\n'+generator.START+'\n'+generator.END+'\n</script>'
        report=evaluate(SNAPSHOT)
        embedded=generator.embed(document,SNAPSHOT,report)
        self.assertIn('const DEMO_STORIES=',embedded)
        story_json=embedded.split('const DEMO_STORIES=',1)[1].split(';\n',1)[0]
        self.assertEqual(json.loads(story_json),build_demo_stories(SNAPSHOT))
        self.assertEqual(generator.embed(embedded,SNAPSHOT,report),embedded)
        report['summary']['review_ready']=999
        with self.assertRaises(ValueError):generator.embed(document,SNAPSHOT,report)


if __name__=='__main__':
    unittest.main()
