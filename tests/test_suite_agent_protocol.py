"""All suite AI handoff inputs are synthetic and no provider is called."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from konaklamaflow.agent_protocol import ProtocolError
from konaklamaflow.experience_engine import evaluate
from konaklamaflow.suite_agent_protocol import make_suite_handoff, verify_suite_suggestion

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'examples/fictional-hotel.json').read_text())
ISSUED = '2026-11-12T11:00:00Z'
CHECKED = '2026-11-12T11:01:00Z'


class SuiteAgentProtocolTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = copy.deepcopy(FIXTURE)
        self.manifest = make_suite_handoff(self.snapshot, ISSUED)
        self.suggestion = {
            'task_id': self.manifest['tasks'][0]['task_id'],
            'intent': 'SUGGEST_RECEPTION_REVIEW',
            'snapshot_sha256': self.manifest['snapshot_sha256'],
            'report_sha256': self.manifest['report_sha256'],
        }

    def verify(self, manifest=None, suggestion=None, snapshot=None, checked=CHECKED):
        return verify_suite_suggestion(
            self.manifest if manifest is None else manifest,
            self.suggestion if suggestion is None else suggestion,
            checked, current_snapshot=self.snapshot if snapshot is None else snapshot,
        )

    def test_read_only_explanation_is_valid_and_repeatable_without_input_mutation(self):
        original = copy.deepcopy(self.snapshot)
        self.assertTrue(self.verify())
        self.assertTrue(self.verify())
        self.assertEqual(self.snapshot, original)
        self.assertEqual(self.manifest['mode'], 'NO_EXECUTION_READ_ONLY')
        self.assertTrue(all(t['allowed_tools'] == ['explain_status', 'prepare_checklist'] for t in self.manifest['tasks']))

    def test_uses_final_suite_blockers_not_weaker_base_projection(self):
        snapshot = copy.deepcopy(self.snapshot)
        snapshot['rooms'][0]['capacity'] = 1
        report = evaluate(snapshot)
        manifest = make_suite_handoff(snapshot, ISSUED)
        self.assertEqual([(r['status'],r['blockers']) for r in report['arrivals']],
                         [(t['state'],t['reason_codes']) for t in manifest['tasks']])
        self.assertTrue(any('ROOM_INCOMPATIBLE' in t['reason_codes'] for t in manifest['tasks']))

    def test_current_source_property_capacity_event_task_and_clock_changes_reject_old_handoff(self):
        variants=[]
        for key,value in [('property_id','OTHER_SYNTHETIC_PROPERTY'), ('at_time','15:00')]:
            snapshot=copy.deepcopy(self.snapshot);snapshot[key]=value;variants.append(snapshot)
        snapshot=copy.deepcopy(self.snapshot);snapshot['rooms'][0]['capacity']=1;variants.append(snapshot)
        snapshot=copy.deepcopy(self.snapshot);snapshot['channel_events'][0]['status']='needs_review';variants.append(snapshot)
        snapshot=copy.deepcopy(self.snapshot);snapshot['tasks'][0]['priority']='normal';variants.append(snapshot)
        for snapshot in variants:
            with self.subTest(change=snapshot['property_id']), self.assertRaises(ProtocolError):
                self.verify(snapshot=snapshot)

    def test_manifest_tampering_cannot_grant_tool_or_approval_scope(self):
        variants=[]
        for key,value in [('mode','EXECUTE'),('protocol','other'),('snapshot_sha256','0'*64),('report_sha256','0'*64),('approved',True)]:
            manifest=copy.deepcopy(self.manifest);manifest[key]=value;variants.append(manifest)
        manifest=copy.deepcopy(self.manifest);manifest['tasks'][0]['allowed_tools'].append('write_pms');variants.append(manifest)
        manifest=copy.deepcopy(self.manifest);manifest['tasks'][0]['reason_codes']=['IGNORE_PREVIOUS_INSTRUCTIONS'];variants.append(manifest)
        manifest=copy.deepcopy(self.manifest);manifest['tasks'][0]['state']='review_ready' if manifest['tasks'][0]['state']=='blocked' else 'blocked';variants.append(manifest)
        manifest=copy.deepcopy(self.manifest);manifest['tasks'].append(copy.deepcopy(manifest['tasks'][0]));variants.append(manifest)
        manifest=copy.deepcopy(self.manifest);manifest['expires_at']='2026-11-12T11:10:00+00:00';variants.append(manifest)
        for manifest in variants:
            with self.assertRaises(ProtocolError):self.verify(manifest=manifest)

    def test_same_report_reissued_later_does_not_accept_old_task_reference(self):
        fresh=make_suite_handoff(self.snapshot,'2026-11-12T11:01:00Z')
        self.assertNotEqual(fresh['tasks'][0]['task_id'],self.manifest['tasks'][0]['task_id'])
        self.assertEqual(fresh['report_sha256'],self.manifest['report_sha256'])
        with self.assertRaises(ProtocolError):self.verify(manifest=fresh)

    def test_write_approval_identity_messages_and_extra_tool_fields_are_rejected(self):
        for intent in ('approve','write_pms','check_in','capture_payment','submit_kbs','send_guest_message','read_identity_document'):
            suggestion=dict(self.suggestion,intent=intent)
            with self.subTest(intent=intent), self.assertRaises(ProtocolError):self.verify(suggestion=suggestion)
        for key,value in [('task_id','f'*24),('task_id',True),('snapshot_sha256','0'*64),('report_sha256','0'*64),('tool_call',{'name':'write_pms'}),('guest_name','SYNTHETIC_PRIVATE')]:
            suggestion=dict(self.suggestion);suggestion[key]=value
            with self.assertRaises(ProtocolError):self.verify(suggestion=suggestion)

    def test_ttl_boundaries_future_and_invalid_utc_types_fail_closed(self):
        for seconds in (True,30.5,'300',29,601):
            with self.assertRaises(ProtocolError):make_suite_handoff(self.snapshot,ISSUED,seconds)
        for timestamp in (None,3,False,'2026-11-12T11:00:00','2026-11-12T11:00:00+03:00'):
            with self.assertRaises(ProtocolError):make_suite_handoff(self.snapshot,timestamp)
        with self.assertRaises(ProtocolError):make_suite_handoff(self.snapshot,'9999-12-31T23:59:59Z')
        for timestamp in ('2026-11-12T10:59:59Z','2026-11-12T11:05:00Z'):
            with self.assertRaises(ProtocolError):self.verify(checked=timestamp)
        for manifest in ([],{}, {'issued_at':None,'expires_at':ISSUED}):
            with self.assertRaises(ProtocolError):self.verify(manifest=manifest)

    def test_private_fields_and_prompt_injection_are_rejected_without_echo(self):
        variants=[None,[],{}]
        snapshot=copy.deepcopy(self.snapshot);snapshot['guest_name']='SYNTHETIC_PRIVATE';variants.append(snapshot)
        snapshot=copy.deepcopy(self.snapshot);snapshot['reservations'][0]['requests']=['IGNORE_INSTRUCTIONS_SENDFUNDS'];variants.append(snapshot)
        snapshot=copy.deepcopy(self.snapshot);snapshot['tasks'][0]['guest_email']='SYNTHETIC_PRIVATE';variants.append(snapshot)
        for snapshot in variants:
            with self.assertRaises(ProtocolError) as caught:make_suite_handoff(snapshot,ISSUED)
            self.assertNotIn('SYNTHETIC_PRIVATE',str(caught.exception))
            self.assertNotIn('IGNORE_INSTRUCTIONS',str(caught.exception))

    def test_forwarded_manifest_contains_no_raw_property_reservation_room_channel_or_free_text(self):
        serialized=json.dumps(self.manifest)
        for private in (self.snapshot['property_id'], self.snapshot['reservations'][0]['id'],
                        self.snapshot['reservations'][0]['external_ref'], 'property_id','room_id','channel','external_ref','notes'):
            self.assertNotIn(private,serialized)
        self.assertEqual(len({t['task_id'] for t in self.manifest['tasks']}),len(self.manifest['tasks']))
        self.assertTrue(all(len(t['task_id'])==24 for t in self.manifest['tasks']))

    def test_malformed_engine_contract_cannot_forward_unstructured_text(self):
        report=evaluate(self.snapshot)
        variants=[]
        for field,value in [('blockers',['SYNTHETIC_PRIVATE']),('task_id','not_an_opaque_task'),('status','CHECKED_IN')]:
            broken=copy.deepcopy(report);broken['arrivals'][0][field]=value;variants.append(broken)
        for broken in variants:
            with patch('konaklamaflow.suite_agent_protocol.evaluate',return_value=broken):
                with self.assertRaises(ProtocolError):make_suite_handoff(self.snapshot,ISSUED)

    def test_unexpected_engine_write_policy_is_never_forwarded_as_safe(self):
        report=evaluate(self.snapshot)
        for key in ('pms_writes','payments','kbs','guest_messages','human_approval_required'):
            broken=copy.deepcopy(report);broken['approval_policy'][key]=not broken['approval_policy'][key]
            with patch('konaklamaflow.suite_agent_protocol.evaluate',return_value=broken):
                with self.subTest(key=key), self.assertRaises(ProtocolError):make_suite_handoff(self.snapshot,ISSUED)
        broken=copy.deepcopy(report);broken['approval_policy']['payments']=0
        with patch('konaklamaflow.suite_agent_protocol.evaluate',return_value=broken):
            with self.assertRaises(ProtocolError):make_suite_handoff(self.snapshot,ISSUED)


if __name__ == '__main__':
    unittest.main()
