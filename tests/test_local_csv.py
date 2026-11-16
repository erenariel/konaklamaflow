"""Local fictional CSV import contracts and privacy regressions."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.cli import main
from konaklamaflow.core import InputError, review
from konaklamaflow.local_csv import import_csv_snapshot

ROOT = Path(__file__).resolve().parents[1]


def sample_inputs(directory):
    rooms = directory / "rooms.csv"
    reservations = directory / "reservations.csv"
    rooms.write_text(
        "room_id,category,beds,active,guest_name\n"
        "A101,standard,double,true,FICTIONAL_PRIVATE_NAME\n"
        "A102,standard,twin,true,FICTIONAL_PRIVATE_PERSON\n",
        encoding="utf-8",
    )
    reservations.write_text(
        "reservation_ref,checkin,checkout,category,status,room_id,"
        "twin_requested,guest_name,guest_email,phone,passport_number,notes\n"
        "FICT1,2026-11-12,2026-11-14,standard,confirmed,A101,false,"
        "FICTIONAL_PRIVATE_NAME,private@example.invalid,PRIVATE_PHONE,"
        "PRIVATE_PASSPORT,SECRET_NOTE\n"
        "FICT2,2026-11-13,2026-11-15,standard,confirmed,,true,"
        "FICTIONAL_PRIVATE_PERSON,private@example.invalid,PRIVATE_PHONE,"
        "PRIVATE_PASSPORT,SECRET_NOTE\n",
        encoding="utf-8",
    )
    return rooms, reservations


class LocalCsvTests(unittest.TestCase):
    def test_private_columns_never_survive_and_references_are_one_run_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            rooms, reservations = sample_inputs(Path(tmp))
            first = import_csv_snapshot(str(rooms), str(reservations))
            second = import_csv_snapshot(str(rooms), str(reservations))
            text = json.dumps(first, ensure_ascii=False)
            for secret in ("FICTIONAL_PRIVATE_NAME", "FICTIONAL_PRIVATE_PERSON",
                           "private@example.invalid", "PRIVATE_PHONE",
                           "PRIVATE_PASSPORT", "SECRET_NOTE", "A101", "FICT1"):
                self.assertNotIn(secret, text)
            self.assertEqual(first["property_id"], "LOCAL_CSV_PROPERTY")
            self.assertEqual(first["reservations"][0]["source"], "LOCAL_CSV")
            self.assertEqual(first["reservations"][0]["room_id"],
                             first["rooms"][0]["id"])
            self.assertNotEqual(first["rooms"][0]["id"], second["rooms"][0]["id"])
            self.assertNotEqual(first["reservations"][0]["ref"],
                                second["reservations"][0]["ref"])
            self.assertTrue(first["rooms"][0]["id"].startswith("R_"))
            self.assertTrue(first["reservations"][0]["ref"].startswith("B_"))
            self.assertEqual(len(first["rooms"][0]["id"]), 26)
            original = deepcopy(first)
            report = review(first, "2026-11-12")
            self.assertEqual(first, original)
            self.assertEqual(report["mode"], "DRY_RUN_ONLY")
            self.assertFalse(any("PRIVATE_" in json.dumps(item)
                                 for item in report["issues"]))

    def test_cli_uses_local_only_and_can_write_private_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            rooms, reservations = sample_inputs(Path(tmp))
            output = Path(tmp) / "review.json"
            capture = StringIO()
            with redirect_stdout(capture):
                result = main([
                    "review-csv", "--rooms", str(rooms),
                    "--reservations", str(reservations),
                    "--as-of", "2026-11-12", "--output", str(output),
                ])
            self.assertEqual(result, 0)
            self.assertEqual(capture.getvalue(), "")
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["reservations"], 2)
            self.assertEqual(report["summary"]["rooms"], 2)
            self.assertNotIn("PRIVATE_PASSPORT", output.read_text())
            self.assertNotIn("private@example.invalid", output.read_text())
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            before = rooms.read_bytes()
            error = StringIO()
            with redirect_stderr(error):
                rejected = main([
                    "review-csv", "--rooms", str(rooms),
                    "--reservations", str(reservations),
                    "--output", str(rooms),
                ])
            self.assertEqual(rejected, 2)
            self.assertEqual(rooms.read_bytes(), before)
            self.assertNotIn(str(rooms), error.getvalue())

    def test_existing_json_cli_and_packaged_demo_command(self):
        capture = StringIO()
        with redirect_stdout(capture):
            self.assertEqual(main(["demo"]), 0)
        sample = json.loads(capture.getvalue())
        self.assertEqual(sample["property_id"], "DEMO_INN_01")
        self.assertEqual(sample["as_of"], "2026-11-12")
        self.assertEqual(sample["summary"]["rooms"], 5)
        with redirect_stdout(StringIO()):
            self.assertEqual(main([
                str(ROOT / "examples" / "demo.json"),
                "--as-of", "2026-11-12",
            ]), 0)

    def test_rejects_unknown_or_duplicate_headers_and_malformed_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            rooms, reservations = sample_inputs(Path(tmp))
            for contents in (
                "room_id,category,beds,private_surprise\nA101,standard,double,SECRET\n",
                "room_id,category,beds,beds\nA101,standard,double,twin\n",
                "room_id,category\nA101,standard\n",
                "room_id,category,beds\nA101,standard,double,EXTRA\n",
                "room_id,category,beds\nA101,standard,\"unterminated\n",
            ):
                with self.subTest(header=contents[:35]):
                    rooms.write_text(contents, encoding="utf-8")
                    with self.assertRaises(InputError):
                        import_csv_snapshot(str(rooms), str(reservations))
            self.assertFalse((Path(tmp) / "review.json").exists())

    def test_unapproved_labels_and_invalid_dates_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            rooms, bookings = sample_inputs(Path(tmp))
            original = rooms.read_text(encoding="utf-8")
            for value in ("FICTIONAL_PERSON_NAME", "unknown-room", "=1+2"):
                with self.subTest(value=value):
                    rooms.write_text(original.replace("standard", value),
                                     encoding="utf-8")
                    with self.assertRaises(InputError):
                        import_csv_snapshot(str(rooms), str(bookings))
            rooms.write_text(original, encoding="utf-8")
            original_bookings = bookings.read_text(encoding="utf-8")
            bookings.write_text(original_bookings.replace(
                "2026-11-15", "2026-11-12"), encoding="utf-8")
            with self.assertRaises(InputError):
                import_csv_snapshot(str(rooms), str(bookings))

    def test_duplicate_ref_preserves_duplicate_detection_without_raw_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            rooms, bookings = sample_inputs(Path(tmp))
            original = bookings.read_text(encoding="utf-8")
            bookings.write_text(original.replace("FICT2", "FICT1"),
                                encoding="utf-8")
            snapshot = import_csv_snapshot(str(rooms), str(bookings))
            report = review(snapshot, "2026-11-12")
            self.assertTrue(any(issue["code"] == "DUPLICATE_SOURCE_REF"
                                for issue in report["issues"]))
            self.assertNotIn("FICT1", json.dumps(report))

    def test_size_and_symlink_or_same_input_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            rooms, bookings = sample_inputs(Path(tmp))
            rooms.write_bytes(b"room_id,category,beds\n" +
                              b"x" * (2_000_000 + 1))
            with self.assertRaises(InputError):
                import_csv_snapshot(str(rooms), str(bookings))
            rooms, bookings = sample_inputs(Path(tmp))
            with self.assertRaises(InputError):
                import_csv_snapshot(str(rooms), str(rooms))
            if os.name == "posix":
                alias = Path(tmp) / "alias.csv"
                alias.symlink_to(rooms)
                with self.assertRaises(InputError):
                    import_csv_snapshot(str(rooms), str(alias))

    def test_realistic_fictional_csv_examples(self):
        source = import_csv_snapshot(
            str(ROOT / "examples/csv/rooms.csv"),
            str(ROOT / "examples/csv/reservations.csv"),
        )
        self.assertEqual(len(source["rooms"]), 3)
        self.assertEqual(len(source["reservations"]), 3)
        self.assertEqual(review(source, "2026-11-12")["summary"]["rooms"], 3)


if __name__ == "__main__":
    unittest.main()
