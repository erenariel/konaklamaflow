"""Schema 1.1 reservation review: stay statuses, capacity, blocks, moves and times.

Every fixture is fictional. These tests pin the behaviour added after the
November 2026 review; legacy (schema 1.0) behaviour is covered in test_core.
"""
import copy
import json
from pathlib import Path
import unittest

from konaklamaflow.core import InputError, review

ROOT = Path(__file__).resolve().parents[1]
DEMO = json.loads((ROOT / "examples" / "demo.json").read_text(encoding="utf-8"))
TODAY = "2026-11-12"


def res(ref, checkin="2026-11-13", checkout="2026-11-15", category="standard", source="OTA", **extra):
    item = {"ref": ref, "source": source, "checkin": checkin, "checkout": checkout, "category": category}
    item.update(extra)
    return item


def snapshot(*reservations, rooms=None, **extra):
    data = {"rooms": rooms if rooms is not None else [
        {"id": "101", "category": "standard", "beds": "double", "max_occupancy": 2},
        {"id": "102", "category": "standard", "beds": "twin", "max_occupancy": 3},
    ], "reservations": list(reservations)}
    data.update(extra)
    return data


def codes(report, ref=None):
    return [i["code"] for i in report["issues"] if ref is None or i["reservation_ref"] == ref]


def proposed(report):
    return {p["reservation_ref"]: p["room_id"] for p in report["room_proposals"]}


class BackwardCompatibilityTests(unittest.TestCase):
    def test_schema_10_input_keeps_every_legacy_field(self):
        report = review(copy.deepcopy(DEMO), TODAY)
        self.assertEqual(report["schema_version"], "1.1")
        self.assertEqual(codes(report), ["CANCELLED_HOLD_REVIEW", "BASE_PRICE_MISMATCH", "NO_SAFE_ROOM_PROPOSAL"])
        self.assertEqual(proposed(report), {"D002": "102"})
        self.assertEqual(report["summary"]["tomorrow_arrivals"], 3)
        for key in ("split_stay_proposals", "today_departures", "room_moves", "blocks"):
            self.assertEqual(report[key], [])
        self.assertEqual([a["category"] for a in report["availability"]], ["standard", "superior"])

    def test_output_is_deterministic(self):
        data = snapshot(res("A"), res("B", status="pending"), res("C", checkin="2026-11-11", status="checked_in"))
        self.assertEqual(review(copy.deepcopy(data), TODAY), review(copy.deepcopy(data), TODAY))


class StayStatusTests(unittest.TestCase):
    def test_confirmed_stay_already_started_without_room_is_critical_and_reserves_a_room(self):
        data = snapshot(
            res("INHOUSE", checkin="2026-11-11", checkout="2026-11-14"),
            res("TAKEN", checkin=TODAY, checkout="2026-11-13", room_id="101"),
            res("ARRIVAL", checkin=TODAY, checkout="2026-11-13"),
        )
        report = review(data, TODAY)
        self.assertIn("IN_HOUSE_WITHOUT_ROOM", codes(report, "INHOUSE"))
        # Room 102 may be where the unrecorded guest sleeps: never offer it.
        self.assertNotIn("ARRIVAL", proposed(report))
        self.assertIn("NO_SAFE_ROOM_PROPOSAL", codes(report, "ARRIVAL"))

    def test_checked_in_without_room_is_flagged_even_on_departure_day(self):
        report = review(snapshot(res("CI", checkin="2026-11-10", checkout=TODAY, status="checked_in")), TODAY)
        self.assertEqual(codes(report, "CI"), ["IN_HOUSE_WITHOUT_ROOM"])

    def test_overdue_checkout_keeps_room_blocked_tonight(self):
        data = snapshot(
            res("LATE", checkin="2026-11-08", checkout="2026-11-11", status="checked_in", room_id="101"),
            res("NEXT", checkin=TODAY, checkout="2026-11-13", room_id="101"),
            res("FREE", checkin=TODAY, checkout="2026-11-13"),
        )
        report = review(data, TODAY)
        self.assertIn("CHECKOUT_OVERDUE", codes(report, "LATE"))
        self.assertIn("ROOM_OVERLAP", codes(report, "NEXT"))
        self.assertEqual(proposed(report), {"FREE": "102"})

    def test_checked_out_stay_releases_room_and_needs_no_room_checks(self):
        data = snapshot(
            res("GONE", checkin="2026-11-10", checkout="2026-11-14", status="checked_out", room_id="999"),
            res("NEW", checkin=TODAY, checkout="2026-11-13"),
        )
        report = review(data, TODAY)
        self.assertEqual(codes(report, "GONE"), [])
        self.assertIn("NEW", proposed(report))

    def test_future_dates_with_started_status_are_inconsistent(self):
        for status in ("checked_in", "checked_out", "no_show"):
            with self.subTest(status=status):
                report = review(snapshot(res("X", status=status, room_id="101")), TODAY)
                self.assertIn("STATUS_DATE_CONFLICT", codes(report, "X"))

    def test_no_show_room_stays_held_until_release(self):
        data = snapshot(
            res("NS", checkin="2026-11-11", checkout="2026-11-14", status="no_show", room_id="101"),
            res("A", checkin=TODAY, checkout="2026-11-13"),
        )
        report = review(data, TODAY)
        self.assertEqual(codes(report, "NS"), ["NO_SHOW_HOLD_REVIEW"])
        self.assertEqual(proposed(report), {"A": "102"})

    def test_unknown_status_still_rejected(self):
        with self.assertRaises(InputError):
            review(snapshot(res("X", status="in_house")), TODAY)


class PendingCapacityTests(unittest.TestCase):
    def test_pending_arrival_needs_decision_and_capacity_check(self):
        data = snapshot(res("C1"), res("C2"), res("P1", status="pending", checkout="2026-11-14"))
        report = review(data, TODAY)
        self.assertEqual(codes(report, "P1"), ["PENDING_ARRIVAL_DECISION", "PENDING_EXCEEDS_CAPACITY"])
        self.assertEqual(len(report["room_proposals"]), 2)

    def test_pending_that_fits_is_only_reminded(self):
        report = review(snapshot(res("C1"), res("P1", status="pending")), TODAY)
        self.assertEqual(codes(report, "P1"), ["PENDING_ARRIVAL_DECISION"])

    def test_later_pending_bookings_compete_for_the_last_room(self):
        data = snapshot(res("C1", checkin="2026-11-20", checkout="2026-11-21"),
                        res("P1", status="pending", checkin="2026-11-20", checkout="2026-11-21"),
                        res("P2", status="pending", checkin="2026-11-20", checkout="2026-11-21"))
        report = review(data, TODAY)
        self.assertEqual(codes(report, "P1"), [])
        self.assertEqual(codes(report, "P2"), ["PENDING_EXCEEDS_CAPACITY"])

    def test_assigned_pending_still_holds_its_room(self):
        data = snapshot(res("P", status="pending", room_id="101"), res("A"), res("B"))
        report = review(data, TODAY)
        self.assertEqual(proposed(report), {"A": "102"})
        self.assertIn("NO_SAFE_ROOM_PROPOSAL", codes(report, "B"))


class DuplicateTests(unittest.TestCase):
    def test_same_guest_same_dates_through_two_sources_is_flagged(self):
        data = snapshot(res("X1", source="BOOKING", guest_key="G_1"), res("Y9", source="DIRECT", guest_key="G_1"))
        report = review(data, TODAY)
        self.assertEqual(codes(report), ["POSSIBLE_DUPLICATE_BOOKING", "POSSIBLE_DUPLICATE_BOOKING"])

    def test_multi_room_booking_from_one_source_is_not_a_duplicate(self):
        data = snapshot(res("X1", guest_key="G_1"), res("X2", guest_key="G_1"))
        self.assertEqual(codes(review(data, TODAY)), [])

    def test_equal_references_across_channels_are_not_merged(self):
        # Channel numbering is independent; a shared reference is not evidence.
        data = snapshot(res("100", source="BOOKING"), res("100", source="DIRECT"))
        self.assertEqual(codes(review(data, TODAY)), [])

    def test_different_dates_are_not_flagged(self):
        data = snapshot(res("X1", source="BOOKING", guest_key="G_1"),
                        res("Y9", source="DIRECT", guest_key="G_1", checkout="2026-11-16"))
        self.assertEqual(codes(review(data, TODAY)), [])


class PriceTests(unittest.TestCase):
    def test_variable_nightly_rates_and_discount_reconcile(self):
        data = snapshot(res("E", nightly_rates=["100", "120.50"], discount_base="20.50",
                            total_base="200.00", currency="RUB"))
        self.assertEqual(codes(review(data, TODAY)), [])

    def test_variable_rates_mismatch_reports_expected_total(self):
        data = snapshot(res("E", nightly_rates=["100", "120"], total_base="250", currency="EUR"))
        issue = review(data, TODAY)["issues"][0]
        self.assertEqual(issue["code"], "BASE_PRICE_MISMATCH")
        self.assertTrue(issue["detail"].startswith("Expected base-only total 220.00 EUR;"))

    def test_invalid_price_shapes_fail_closed(self):
        bad = [
            dict(nightly_rates=["100"], total_base="100", currency="EUR"),                      # 1 rate, 2 nights
            dict(nightly_rates=["100", "100"], nightly_base="100", total_base="200", currency="EUR"),
            dict(nightly_base="100", total_base="200", currency="EUR", discount_base="300"),
            dict(discount_base="10"),
            dict(nightly_rates=[100, 100], total_base="200", currency="EUR"),
            dict(nightly_base="100", total_base="200", currency="XXX"),
        ]
        for fields in bad:
            with self.subTest(fields=fields):
                with self.assertRaises(InputError):
                    review(snapshot(res("E", **fields)), TODAY)


class OccupancyAndBoardTests(unittest.TestCase):
    def test_assigned_room_too_small_is_critical(self):
        report = review(snapshot(res("BIG", adults=2, children=1, room_id="101")), TODAY)
        self.assertEqual(codes(report, "BIG"), ["OCCUPANCY_EXCEEDS_ROOM"])

    def test_proposal_skips_rooms_that_are_too_small(self):
        report = review(snapshot(res("FAM", adults=3)), TODAY)
        self.assertEqual(proposed(report), {"FAM": "102"})

    def test_max_adults_is_respected(self):
        rooms = [{"id": "301", "category": "family", "beds": "flex", "max_occupancy": 4, "max_adults": 2}]
        report = review(snapshot(res("F", category="family", adults=3), rooms=rooms), TODAY)
        self.assertIn("NO_SAFE_ROOM_PROPOSAL", codes(report, "F"))

    def test_unknown_counts_are_never_rejected(self):
        report = review(snapshot(res("A"), res("B")), TODAY)
        self.assertEqual(len(report["room_proposals"]), 2)

    def test_invalid_guest_counts_and_board_fail_closed(self):
        for fields in (dict(adults=0), dict(adults=-1), dict(adults=True), dict(adults=15, children=6),
                       dict(board="ALL"), dict(board="ai")):
            with self.subTest(fields=fields):
                with self.assertRaises(InputError):
                    review(snapshot(res("X", **fields)), TODAY)
        with self.assertRaises(InputError):
            review(snapshot(rooms=[{"id": "1", "category": "s", "beds": "double",
                                    "max_occupancy": 2, "max_adults": 3}]), TODAY)

    def test_meal_forecast_counts_breakfast_lunch_and_dinner(self):
        data = snapshot(
            res("DEP", checkin="2026-11-10", checkout=TODAY, status="checked_in", room_id="101",
                board="AI", adults=2, children=1),
            res("ARR", checkin=TODAY, checkout="2026-11-15", room_id="101", board="HB", adults=2),
            res("STAY", checkin="2026-11-11", checkout="2026-11-14", room_id="102", board="FB", adults=1),
            res("NOBOARD", checkin="2026-11-11", checkout="2026-11-14", category="standard"),
            res("PEND", checkin=TODAY, checkout="2026-11-13", status="pending", board="AI", adults=4),
        )
        today, tomorrow = review(data, TODAY)["meal_forecast"]
        self.assertEqual(today["date"], TODAY)
        self.assertEqual(today["breakfast"], {"adults": 3, "children": 1})
        self.assertEqual(today["lunch"], {"adults": 1, "children": 0})
        self.assertEqual(today["dinner"], {"adults": 3, "children": 0})
        self.assertEqual(today["reservations_without_board"], 1)
        self.assertEqual(tomorrow["breakfast"], {"adults": 3, "children": 0})


class BlockTests(unittest.TestCase):
    BLOCK = {"id": "ALT1", "kind": "allotment", "source": "TUI", "category": "standard",
             "start": "2026-11-15", "end": "2026-11-30", "rooms": 1, "release_days": 7}

    def test_unsold_allotment_room_is_not_offered_to_free_sale_before_release(self):
        data = snapshot(res("F1", checkin="2026-11-20", checkout="2026-11-21", source="DIRECT"),
                        res("F2", checkin="2026-11-20", checkout="2026-11-21", source="DIRECT"),
                        blocks=[self.BLOCK])
        report = review(data, TODAY)
        self.assertEqual(len(report["room_proposals"]), 1)
        self.assertIn("NO_SAFE_ROOM_PROPOSAL", codes(report, "F2"))
        night = next(n for n in report["availability"][0]["nights"] if n["date"] == "2026-11-20")
        # Two sold stays plus one held allotment room exceed the two rooms.
        self.assertEqual((night["committed"], night["block_reserve"], night["free"]), (2, 1, -1))

    def test_released_allotment_rooms_return_to_free_sale(self):
        data = snapshot(res("F1", checkin="2026-11-16", checkout="2026-11-17", source="DIRECT"),
                        res("F2", checkin="2026-11-16", checkout="2026-11-17", source="DIRECT"),
                        blocks=[self.BLOCK])
        self.assertEqual(len(review(data, TODAY)["room_proposals"]), 2)

    def test_block_member_uses_its_own_held_room(self):
        data = snapshot(res("T1", checkin="2026-11-20", checkout="2026-11-21", source="TUI", block_id="ALT1"),
                        res("F1", checkin="2026-11-20", checkout="2026-11-21", source="DIRECT"),
                        blocks=[self.BLOCK])
        report = review(data, TODAY)
        self.assertEqual(set(proposed(report)), {"T1", "F1"})
        summary = report["blocks"][0]
        self.assertEqual(summary["picked_up_peak"], 1)
        self.assertEqual(summary["next_release_date"], "2026-11-14")

    def test_block_summary_counts_held_and_released_room_nights(self):
        report = review(snapshot(blocks=[dict(self.BLOCK, rooms=2)]), TODAY)
        summary = report["blocks"][0]
        # Nights 15-19 are already released (release date <= today); 20-29 still held.
        self.assertEqual(summary["released_unsold_room_nights"], 10)
        self.assertEqual(summary["held_unsold_room_nights"], 20)
        self.assertEqual((summary["next_release_date"], summary["unsold_at_next_release"]), ("2026-11-13", 2))

    def test_group_cutoff_releases_every_night_at_once(self):
        group = dict(self.BLOCK, kind="group", cutoff="2026-11-18")
        del group["release_days"]
        report = review(snapshot(blocks=[group]), TODAY)
        self.assertEqual(report["blocks"][0]["next_release_date"], "2026-11-18")
        self.assertEqual(report["blocks"][0]["release_days"], None)

    def test_block_link_problems_are_reviewed(self):
        data = snapshot(res("A", source="TUI", block_id="NOPE", checkin="2026-11-20", checkout="2026-11-21"),
                        res("B", source="OTHER", block_id="ALT1", checkin="2026-11-20", checkout="2026-11-21"),
                        res("C", source="TUI", block_id="ALT1", checkin="2026-11-20", checkout="2026-11-21", room_id="101"),
                        res("D", source="TUI", block_id="ALT1", checkin="2026-11-20", checkout="2026-11-21", room_id="102"),
                        blocks=[self.BLOCK])
        report = review(data, TODAY)
        self.assertIn("BLOCK_NOT_FOUND", codes(report, "A"))
        self.assertIn("BLOCK_MISMATCH", codes(report, "B"))
        # B claims the block (with a mismatch) first in deterministic order, so
        # the single contracted room is exceeded by C and D.
        overbooked = [i["reservation_ref"] for i in report["issues"] if i["code"] == "BLOCK_OVERBOOKED"]
        self.assertEqual(overbooked, ["C", "D"])

    def test_invalid_blocks_fail_closed(self):
        for change in (dict(category="suite"), dict(cutoff="2026-11-18"), dict(rooms=0),
                       dict(kind="contract"), dict(end="2026-11-15")):
            with self.subTest(change=change):
                with self.assertRaises(InputError):
                    review(snapshot(blocks=[dict(self.BLOCK, **change)]), TODAY)
        with self.assertRaises(InputError):
            review(snapshot(blocks=[self.BLOCK, self.BLOCK]), TODAY)


class RoomMoveTests(unittest.TestCase):
    def test_recorded_room_move_is_checked_per_segment(self):
        moving = res("MOVE", checkin=TODAY, checkout="2026-11-15", segments=[
            {"room_id": "101", "start": TODAY, "end": "2026-11-13"},
            {"room_id": "102", "start": "2026-11-13", "end": "2026-11-15"}])
        other = res("OTHER", checkin="2026-11-13", checkout="2026-11-14", room_id="101")
        clash = res("CLASH", checkin="2026-11-14", checkout="2026-11-16", room_id="102")
        report = review(snapshot(moving, other, clash), TODAY)
        self.assertEqual(codes(report, "OTHER"), [])
        self.assertEqual(codes(report, "MOVE"), ["ROOM_OVERLAP"])
        self.assertEqual(report["room_moves"], [{"reservation_ref": "MOVE", "source": "OTA", "date": "2026-11-13",
                                                 "from_room": "101", "to_room": "102"}])

    def test_invalid_segments_fail_closed(self):
        bad = [
            [{"room_id": "101", "start": "2026-11-13", "end": "2026-11-14"}],
            [{"room_id": "101", "start": "2026-11-13", "end": "2026-11-14"},
             {"room_id": "101", "start": "2026-11-14", "end": "2026-11-15"}],
            [{"room_id": "101", "start": "2026-11-13", "end": "2026-11-14"},
             {"room_id": "102", "start": "2026-11-14", "end": "2026-11-16"}],
            [{"room_id": "101", "start": "2026-11-13", "end": "2026-11-14"},
             {"room_id": "102", "start": "2026-11-13", "end": "2026-11-15"}],
        ]
        for segments in bad:
            with self.subTest(segments=segments):
                with self.assertRaises(InputError):
                    review(snapshot(res("M", segments=segments)), TODAY)
        with self.assertRaises(InputError):
            review(snapshot(res("M", room_id="101", segments=bad[1])), TODAY)

    def test_split_stay_option_when_no_single_room_is_free(self):
        data = snapshot(
            res("H1", checkin="2026-11-13", checkout="2026-11-14", room_id="102"),
            res("H2", checkin="2026-11-14", checkout="2026-11-16", room_id="101"),
            res("S", checkin="2026-11-13", checkout="2026-11-15"),
        )
        report = review(data, TODAY)
        self.assertEqual(report["room_proposals"], [])
        self.assertEqual(codes(report, "S"), ["NO_SAFE_ROOM_PROPOSAL", "ROOM_MOVE_OPTION"])
        self.assertEqual(report["split_stay_proposals"], [{
            "reservation_ref": "S", "source": "OTA", "kind": "MANUAL_APPROVAL_REQUIRED",
            "segments": [{"room_id": "101", "start": "2026-11-13", "end": "2026-11-14"},
                         {"room_id": "102", "start": "2026-11-14", "end": "2026-11-15"}]}])
        self.assertEqual(report["summary"]["split_stay_proposals"], 1)

    def test_one_night_stay_is_never_split(self):
        data = snapshot(res("H1", checkin="2026-11-13", checkout="2026-11-14", room_id="101"),
                        res("H2", checkin="2026-11-13", checkout="2026-11-14", room_id="102"),
                        res("S", checkin="2026-11-13", checkout="2026-11-14"))
        self.assertEqual(review(data, TODAY)["split_stay_proposals"], [])


class TimeAndPolicyTests(unittest.TestCase):
    def test_late_checkout_and_early_arrival_need_turnover_time(self):
        data = snapshot(
            res("OUT", checkin="2026-11-10", checkout=TODAY, status="checked_in", room_id="101", departure_time="13:30"),
            res("IN", checkin=TODAY, checkout="2026-11-14", room_id="101", arrival_time="14:00"),
            policy={"turnover_minutes": 90},
        )
        report = review(data, TODAY)
        self.assertEqual(codes(report, "IN"), ["SAME_DAY_TURNOVER_RISK"])
        self.assertEqual(report["today_departures"][0]["departure_time"], "13:30")

    def test_policy_defaults_alone_never_raise_turnover_alerts(self):
        data = snapshot(res("OUT", checkin="2026-11-10", checkout=TODAY, room_id="101"),
                        res("IN", checkin=TODAY, checkout="2026-11-14", room_id="101"),
                        policy={"checkin_time": "12:00", "checkout_time": "12:00"})
        self.assertEqual(codes(review(data, TODAY)), [])

    def test_proposal_prefers_room_without_same_day_squeeze(self):
        data = snapshot(
            res("OUT", checkin="2026-11-10", checkout=TODAY, status="checked_in", room_id="101", departure_time="16:00"),
            res("IN", checkin=TODAY, checkout="2026-11-14", arrival_time="10:00"),
        )
        report = review(data, TODAY)
        self.assertEqual(proposed(report), {"IN": "102"})
        self.assertNotIn("SAME_DAY_TURNOVER_RISK", codes(report))

    def test_invalid_times_and_policy_fail_closed(self):
        for fields in (dict(arrival_time="25:00"), dict(departure_time="9:00"), dict(arrival_time=900)):
            with self.subTest(fields=fields):
                with self.assertRaises(InputError):
                    review(snapshot(res("X", **fields)), TODAY)
        for policy in ({"turnover_minutes": -1}, {"horizon_nights": 0}, {"checkin_time": "2pm"}, {"timezone": "UTC"}):
            with self.subTest(policy=policy):
                with self.assertRaises(InputError):
                    review(snapshot(policy=policy), TODAY)


class AvailabilityTests(unittest.TestCase):
    def test_grid_counts_sold_pending_and_free_rooms_per_night(self):
        data = snapshot(res("A", checkin=TODAY, checkout="2026-11-14"),
                        res("P", checkin="2026-11-13", checkout="2026-11-14", status="pending"),
                        policy={"horizon_nights": 3})
        nights = review(data, TODAY)["availability"][0]["nights"]
        self.assertEqual([n["date"] for n in nights], [TODAY, "2026-11-13", "2026-11-14"])
        self.assertEqual([(n["sellable"], n["committed"], n["pending"], n["free"]) for n in nights],
                         [(2, 1, 0, 1), (2, 1, 1, 1), (2, 0, 0, 2)])

    def test_overbooking_shows_negative_free_rooms(self):
        data = snapshot(res("A", room_id="101"), res("B", room_id="101"), res("C", room_id="102"))
        night = review(data, TODAY)["availability"][0]["nights"][1]
        self.assertEqual(night["free"], -1)

    def test_maintenance_reduces_sellable_rooms(self):
        rooms = [{"id": "101", "category": "standard", "beds": "double",
                  "maintenance": [{"start": TODAY, "end": "2026-11-13"}]},
                 {"id": "102", "category": "standard", "beds": "double", "active": False}]
        nights = review(snapshot(rooms=rooms), TODAY)["availability"][0]["nights"]
        self.assertEqual([n["sellable"] for n in nights[:2]], [0, 1])


if __name__ == "__main__":
    unittest.main()
