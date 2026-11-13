"""Regression coverage for offline input bounds and clobber-safe report outputs."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from konaklamaflow.cli import main


def sample():
    return {
        "property_id": "FICTIONAL_PROPERTY",
        "rooms": [{"id": "R101", "category": "standard", "beds": "double"}],
        "reservations": [],
    }


class CliFileSafetyTests(unittest.TestCase):
    def run_cli(self, *args):
        stderr = io.StringIO()
        stdout = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
            status = main(list(args))
        return status, stderr.getvalue(), stdout.getvalue()

    def test_distinct_output_remains_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "synthetic-input.json"
            output = Path(folder) / "synthetic-report.json"
            source.write_text(json.dumps(sample()), encoding="utf-8")
            before = source.read_bytes()
            status, error, printed = self.run_cli(str(source), "--as-of", "2026-11-12", "--output", str(output))
            self.assertEqual((status, error, printed), (0, "", ""))
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["mode"], "DRY_RUN_ONLY")

    def test_input_path_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "private-synthetic-source.json"
            source.write_text(json.dumps(sample()), encoding="utf-8")
            before = source.read_bytes()
            status, error, stdout = self.run_cli(str(source), "--output", str(source), "--as-of", "2026-11-12")
            self.assertEqual(status, 2)
            self.assertIn("must differ", error)
            self.assertNotIn(str(source), error)
            self.assertEqual(stdout, "")
            self.assertEqual(source.read_bytes(), before)

    def test_hard_link_and_symlink_outputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "fixture.json"
            source.write_text(json.dumps(sample()), encoding="utf-8")
            for kind in ("hard", "sym"):
                output = Path(folder) / (kind + ".json")
                try:
                    os.link(source, output) if kind == "hard" else output.symlink_to(source)
                except (OSError, NotImplementedError):
                    continue
                with self.subTest(kind=kind):
                    status, error, _ = self.run_cli(str(source), "--as-of", "2026-11-12", "--output", str(output))
                    self.assertEqual(status, 2)
                    self.assertIn("must differ", error)
                    self.assertEqual(json.loads(source.read_text(encoding="utf-8")), sample())

    def test_oversized_payload_fails_without_echoing_path_or_content(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "private-synthetic-guest-example.json"
            source.write_bytes(b'{}' + b'X' * 100)
            with patch("konaklamaflow.cli.MAX_INPUT_BYTES", 64):
                status, error, stdout = self.run_cli(str(source), "--as-of", "2026-11-12")
            self.assertEqual(status, 2)
            self.assertIn("32 MiB safety limit", error)
            self.assertNotIn(str(source), error)
            self.assertEqual(stdout, "")

    def test_small_invalid_payload_keeps_generic_error(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "private-synthetic-source.json"
            source.write_bytes(b'not json')
            status, error, stdout = self.run_cli(str(source), "--as-of", "2026-11-12")
            self.assertEqual(status, 2)
            self.assertIn("unable to read JSON", error)
            self.assertNotIn(str(source), error)
            self.assertEqual(stdout, "")


if __name__ == "__main__":
    unittest.main()
