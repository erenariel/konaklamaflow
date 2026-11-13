"""v0.5 fictional hotel-operations domain tests: no guest IDs, settlement or writes."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from konaklamaflow.hotel_ops import (
    HotelOpsError, build_operations_report, draft_new_reservation, validate_fictional_hotel,
)

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"examples/hotel-operations-fictional.json"


class HotelOperationsTests(unittest.TestCase):
    def setUp(self):
        self.src=json.loads(FILE.read_text(encoding="utf-8"))

    def test_32_report_registry_items_and_intentional_unavailable_sections(self):
        report=build_operations_report(self.src)
        self.assertEqual(report["report_count"],32)
        self.assertEqual(report["mode"],"READ_ONLY_SYNTHETIC")
        self.assertEqual(report["safety"]["guest_identity_data"],False)
        self.assertFalse(report["safety"]["fiscal_invoices"])
        self.assertTrue(report["safety"]["human_approval_required"])
        self.assertEqual(len(report["reports"]["active_folios"]["rows"]),3)
        self.assertEqual(len(report["reports"]["room_list"]["rows"]),18)
        self.assertEqual(len(report["reports"]["guest_list"]["rows"]),9)
        for key in ("trial_balance","fiscal_list","budget_analysis","invoice_register",
                    "safe_deposit","revenue_management","email_report"):
            self.assertEqual(report["reports"][key]["rows"],[])
            self.assertNotEqual(report["reports"][key]["status"],"implemented")

    def test_folio_math_in_cents_and_city_ledger_excludes_early_payment_double_count(self):
        report=build_operations_report(self.src)
        folios={f["folio_id"]:f for f in report["folios"]}
        self.assertEqual((folios["FOL-001"]["postings"],folios["FOL-001"]["payments"],
                          folios["FOL-001"]["balance"]),("95.00","20.00","75.00"))
        self.assertEqual(folios["FOL-002"]["balance"],"160.00")
        self.assertEqual(folios["FOL-003"]["balance"],"3250.00")
        self.assertEqual({f["folio_id"] for f in report["city_ledger"]},{"FOL-001","FOL-002"})
        self.assertEqual(report["reports"]["daily_balance"]["rows"],[
            {"currency":"EUR","postings":"255.00","payments":"20.00","net":"235.00"},
            {"currency":"TRY","postings":"4250.00","payments":"1000.00","net":"3250.00"},
        ])
        self.assertEqual(len(report["reports"]["posting_invoice"]["rows"]),7)

    def test_no_raw_personal_identity_data_accepted_even_in_fixture(self):
        for key,value in (("identity_number","P1234567"),("turkish_national_id","12345678901"),
                          ("date_of_birth","1990-01-01"),("telephone","+905550000000"),
                          ("email","someone@example.com"),("address","PRIVATE STREET")):
            data=deepcopy(self.src)
            data["guests"][0][key]=value
            with self.subTest(key=key),self.assertRaises(HotelOpsError):
                validate_fictional_hotel(data)
        self.assertEqual(validate_fictional_hotel(self.src),self.src)

    def test_multi_room_new_reservation_draft_is_never_automatic_pms_confirmation(self):
        before=deepcopy(self.src)
        req={"checkin":"2026-11-18","checkout":"2026-11-21","agency_id":"HOTELBEDS",
             "board":"BB","payment_type":"city_ledger","status":"confirmed",
             "rooms":[{"category":"family","adults":2,"children":1},
                      {"category":"standard","adults":2,"children":0}]}
        draft=draft_new_reservation(self.src,req)
        self.assertEqual(draft["room_count"],2)
        self.assertEqual(draft["total_persons"],5)
        self.assertEqual(draft["reservation_draft_id"],"KFD-2026-0007")
        self.assertEqual(draft["status"],"STAFF_REVIEW_REQUIRED_NOT_SAVED")
        self.assertTrue(draft["requires_source_pms_inventory_check"])
        self.assertEqual(draft["selected_room_ids"],[])
        self.assertEqual(draft["folio_ids"],[])
        self.assertFalse(draft["kbs_submitted"])
        self.assertFalse(draft["payment_collected"])
        self.assertEqual(self.src,before)

    def test_capacity_overnight_dates_and_rooms_fail_closed(self):
        request={"checkin":"2026-11-18","checkout":"2026-11-19","agency_id":"DIRECT",
                 "board":"RO","payment_type":"self_payment","status":"option",
                 "rooms":[{"category":"standard","adults":2,"children":0}]}
        for changes in ({"checkout":"2026-11-18"},{"checkin":"2026-11-20"},
                        {"agency_id":"MISSING"},{"board":"ALL_INCLUSIVE"},
                        {"rooms":[{"category":"economy","adults":4,"children":0}]},
                        {"rooms":[{"category":"standard","adults":1,"children":10}]},
                        {"rooms":[{"category":"standard","adults":True,"children":0}]}):
            item={**request,**changes}
            with self.subTest(changes=changes),self.assertRaises(HotelOpsError):
                draft_new_reservation(self.src,item)

    def test_conflicting_allocations_and_stale_rate_schedule_rejected(self):
        data=deepcopy(self.src)
        data["reservations"][1]["rooms"][0]["room_id"]="101"
        with self.assertRaises(HotelOpsError):
            validate_fictional_hotel(data)
        data=deepcopy(self.src)
        data["reservations"][0]["rooms"][0]["nightly_rates"][0]["date"]="2026-11-14"
        with self.assertRaises(HotelOpsError):
            validate_fictional_hotel(data)

    def test_postings_and_payments_are_not_interchangeable_with_city_ledger(self):
        data=deepcopy(self.src)
        data["folios"][0]["payments"][0]["method"]="city_ledger"
        with self.assertRaises(HotelOpsError):
            validate_fictional_hotel(data)
        data=deepcopy(self.src)
        data["folios"][0]["postings"][0]["amount"]="-1.00"
        with self.assertRaises(HotelOpsError):
            validate_fictional_hotel(data)

    def test_fx_rates_are_marked_synthetic_not_issued_invoice_amounts(self):
        report=build_operations_report(self.src)
        self.assertTrue(all(r["source"]=="FICTIONAL_DEMO_RATE"
                            for r in report["reports"]["exchange_rates"]["rows"]))
        self.assertEqual(report["reports"]["invoice_register"]["rows"],[])
        data=deepcopy(self.src)
        data["fx_rates"][0]["source"]="LIVE_TCMB"
        with self.assertRaises(HotelOpsError):
            build_operations_report(data)


if __name__=="__main__":
    unittest.main()
