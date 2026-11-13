"""Tests for vendor-neutral hotel reference flows and demo staff privileges."""
from copy import deepcopy
import json
import unittest

from konaklamaflow.workflow_catalog import (
    BLOCKED_ACTIONS, FLOWS, FLOW_CODES, PRINCIPALS, ROLE_SCOPES, VENDORS,
    WorkflowPermissionError, public_catalog, request_simulation, role_preview,
)


class HotelWorkflowCatalogTests(unittest.TestCase):
    def test_all_reference_flows_are_completely_disconnected(self):
        catalog=public_catalog()
        self.assertEqual(catalog["mode"],"OFFLINE_READ_ONLY_DEMO")
        self.assertEqual(len(catalog["vendors"]),3)
        self.assertTrue(all(v["integration"]=="NOT_CONNECTED" for v in catalog["vendors"]))
        self.assertGreaterEqual(len(FLOWS),12)
        self.assertEqual(len(FLOW_CODES),len(FLOWS))
        self.assertTrue(all(x["human_approval_required"] and
                            x["source_type"]=="SYNTHETIC_NOT_VERIFIED"
                            for x in catalog["flows"]))
        self.assertFalse(catalog["policy"]["real_authentication"])
        self.assertFalse(catalog["policy"]["payment_collection"])
        self.assertFalse(catalog["policy"]["kbs"])

    def test_demo_principals_are_never_real_login_or_credentials(self):
        for principal in PRINCIPALS:
            identity=role_preview(principal["staff_id"])
            self.assertTrue(identity["staff_id"].startswith("DEMO-"))
            self.assertFalse(identity["can_execute_real_operations"])
            self.assertEqual(identity["authentication"],"NOT_AUTHENTICATED_DEMO_IDENTITY")
            self.assertEqual(set(identity["scopes"]),set(ROLE_SCOPES[identity["role"]]))
            self.assertNotIn("password",json.dumps(identity).lower())
        for missing in ("",None,"DEMO-FAKE","admin"):
            with self.subTest(missing=missing),self.assertRaises(WorkflowPermissionError):
                role_preview(missing)

    def test_safe_preview_is_strictly_role_scoped(self):
        good=request_simulation("DEMO-HK-002","housekeeping","preview")
        self.assertTrue(good["requires_human_approval"])
        self.assertFalse(good["real_actions_enabled"])
        self.assertFalse(good["source_verified"])
        self.assertEqual(good["workflow"]["status"],"STAFF_REVIEW")
        with self.assertRaises(WorkflowPermissionError):
            request_simulation("DEMO-HK-002","agency_credit","preview")
        with self.assertRaises(WorkflowPermissionError):
            request_simulation("DEMO-AUD-005","guest_profile","preview")

    def test_execution_verb_is_always_forbidden(self):
        for action in (*BLOCKED_ACTIONS,"write","delete","approve","notify","send"):
            with self.subTest(action=action),self.assertRaises(WorkflowPermissionError):
                request_simulation("DEMO-MGR-004","reservation_intake",action)
        for invalid in ("",None,"__proto__","unlisted",123):
            with self.assertRaises(WorkflowPermissionError):
                request_simulation("DEMO-MGR-004",invalid,"preview")

    def test_catalog_is_deterministic_and_has_no_personal_details(self):
        a=public_catalog()
        b=public_catalog()
        self.assertEqual(a,b)
        self.assertEqual(len(a["integrity_sha256"]),64)
        s=json.dumps(a).lower()
        for text in ("passport_number","guest_email","api_key","authorization_bearer",
                     "session_token","password_hash","credit_card_number"):
            self.assertNotIn(text,s)


if __name__=="__main__":
    unittest.main()
