import copy
import json
from pathlib import Path
import unittest
from konaklamaflow.core import InputError, review

HERE = Path(__file__).resolve().parent.parent
DEMO = json.loads((HERE / "examples" / "demo.json").read_text(encoding="utf-8"))


def reservation(ref="A", status="confirmed", room_id=None, checkin="2026-11-13", checkout="2026-11-15", category="standard", source="SRC", **extra):
    r = dict(ref=ref, source=source, status=status, checkin=checkin, checkout=checkout, category=category)
    if room_id is not None:
        r["room_id"] = room_id
    r.update(extra)
    return r


def base():
    return {"rooms": [{"id":"101", "category":"standard", "beds":"double"}, {"id":"102","category":"standard", "beds":"twin"}], "reservations": []}


class ReviewTests(unittest.TestCase):
    def test_demo_reports_proposal_price_and_cancellation(self):
        report = review(DEMO, "2026-11-12")
        self.assertEqual(report["mode"], "DRY_RUN_ONLY")
        self.assertEqual(report["summary"]["tomorrow_arrivals"], 3)
        self.assertIn("CANCELLED_HOLD_REVIEW", [i["code"] for i in report["issues"]])
        self.assertIn("BASE_PRICE_MISMATCH", [i["code"] for i in report["issues"]])
        self.assertEqual(report["room_proposals"][0]["room_id"], "102")

    def test_adjacent_stays_no_overlap(self):
        x=base(); x["reservations"] = [reservation("A",room_id="101",checkout="2026-11-13",checkin="2026-11-12"),reservation("B",room_id="101")]
        self.assertNotIn("ROOM_OVERLAP", [i["code"] for i in review(x,"2026-11-12")["issues"]])

    def test_overlap_found(self):
        x=base(); x["reservations"]=[reservation("A",room_id="101"),reservation("B",room_id="101",checkin="2026-11-14")]
        self.assertIn("ROOM_OVERLAP",[i["code"] for i in review(x,"2026-11-12")["issues"]])

    def test_greedy_proposals_never_reuse_room(self):
        x=base(); x["reservations"]=[reservation("A"),reservation("B")]
        result=review(x,"2026-11-12")
        self.assertEqual(len(set(p["room_id"] for p in result["room_proposals"])),2)

    def test_cancelled_reservation_does_not_block_room(self):
        x=base(); x["reservations"]=[reservation("A",status="cancelled",room_id="101"),reservation("B")]
        self.assertEqual(review(x,"2026-11-12")["room_proposals"][0]["room_id"],"101")

    def test_twin_never_proposed_double(self):
        x=base(); x["reservations"]=[reservation("A",twin_requested=True)]
        self.assertEqual(review(x,"2026-11-12")["room_proposals"][0]["room_id"],"102")

    def test_no_twin_available_requires_human(self):
        x=base(); x["rooms"]=[x["rooms"][0]]; x["reservations"]=[reservation("A",twin_requested=True)]
        result=review(x,"2026-11-12")
        self.assertFalse(result["room_proposals"])
        self.assertIn("NO_SAFE_ROOM_PROPOSAL", [i["code"] for i in result["issues"]])

    def test_maintenance_prevents_proposal(self):
        x=base(); x["rooms"][0]["maintenance"]=[{"start":"2026-11-12", "end":"2026-11-16"}]; x["reservations"]=[reservation("A")]
        self.assertEqual(review(x,"2026-11-12")["room_proposals"][0]["room_id"],"102")

    def test_unknown_personal_data_field_refused(self):
        x=base(); x["reservations"]=[reservation("A",guest_name="PRIVATE NAME")]
        with self.assertRaisesRegex(InputError,"unsupported field names"):
            review(x,"2026-11-12")

    def test_pii_as_identifier_rejected(self):
        x=base(); x["reservations"]=[reservation("user@example.com")]
        with self.assertRaises(InputError): review(x,"2026-11-12")

    def test_invalid_nights_rejected(self):
        x=base(); x["reservations"]=[reservation("A",checkout="2026-11-13")]
        with self.assertRaises(InputError): review(x,"2026-11-12")

    def test_duplicate_ref_flagged_no_proposal(self):
        x=base(); x["reservations"]=[reservation("A"),reservation("A")]
        result=review(x,"2026-11-12")
        self.assertIn("DUPLICATE_SOURCE_REF",[i["code"] for i in result["issues"]])
        self.assertEqual(result["room_proposals"],[])

    def test_duplicate_ref_different_source_allowed(self):
        x=base(); x["reservations"]=[reservation("A",source="OTA_1"),reservation("A",source="OTA_2")]
        result=review(x,"2026-11-12")
        self.assertNotIn("DUPLICATE_SOURCE_REF",[i["code"] for i in result["issues"]])

    def test_wrong_category(self):
        x=base(); x["reservations"]=[reservation("A",category="superior",room_id="101")]
        self.assertIn("CATEGORY_MISMATCH",[i["code"] for i in review(x,"2026-11-12")["issues"]])

    def test_no_invented_room_for_future_when_fully_occupied(self):
        x=base();x["reservations"]=[reservation("A",room_id="101"),reservation("B",room_id="102"),reservation("C")]
        result=review(x,"2026-11-12")
        self.assertEqual(result["room_proposals"],[])
        self.assertIn("NO_SAFE_ROOM_PROPOSAL",[i["code"] for i in result["issues"]])

    def test_float_money_rejected(self):
        x=base();x["reservations"]=[reservation("A",nightly_base=23.5,total_base="47.00",currency="EUR")]
        with self.assertRaises(InputError): review(x,"2026-11-12")

    def test_price_consistent(self):
        x=base();x["reservations"]=[reservation("A",nightly_base="27.50",total_base="55.00",currency="EUR")]
        self.assertNotIn("BASE_PRICE_MISMATCH",[i["code"] for i in review(x,"2026-11-12")["issues"]])

    def test_inactive_room_no_proposal(self):
        x=base();x["rooms"][0]["active"]=False;x["reservations"]=[reservation("A")]
        self.assertEqual(review(x,"2026-11-12")["room_proposals"][0]["room_id"],"102")

    def test_stable_deterministic_output(self):
        self.assertEqual(review(copy.deepcopy(DEMO),"2026-11-12"),review(copy.deepcopy(DEMO),"2026-11-12"))


class SecurityRegressionTests(unittest.TestCase):
    def test_unknown_field_name_is_not_echoed(self):
        x = base()
        x["SYNTHETIC_PRIVATE_FIELD"] = "synthetic"
        with self.assertRaises(InputError) as caught:
            review(x, "2026-11-12")
        self.assertNotIn("SYNTHETIC_PRIVATE_FIELD", str(caught.exception))

    def test_extreme_money_rejected(self):
        for amount in ("1e999999999", "9" * 1000, "NaN", "Infinity", "0.001"):
            with self.subTest(amount=amount[:20]):
                x = base()
                x["reservations"] = [reservation(nightly_base=amount, total_base="1", currency="EUR")]
                with self.assertRaises(InputError):
                    review(x, "2026-11-12")

    def test_max_date_rejected_without_overflow(self):
        with self.assertRaises(InputError):
            review(base(), "9999-12-31")

    def test_cli_invalid_encoding_and_private_path_not_echoed(self):
        import contextlib
        import io
        import tempfile
        from konaklamaflow.cli import main
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SYNTHETIC_PRIVATE_PATH.json"
            for payload in (b"\xff", b"invalid json"):
                path.write_bytes(payload)
                error = io.StringIO()
                with contextlib.redirect_stderr(error):
                    self.assertEqual(main([str(path)]), 2)
                self.assertNotIn(str(path), error.getvalue())


if __name__ == "__main__": unittest.main()
