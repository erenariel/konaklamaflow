"""Offline explanation CLI never echoes bad source data or clobbers prior report."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.explain_cli import main
from konaklamaflow.experience_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]


class ExplanationCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = json.loads((ROOT / "examples/fictional-hotel.json").read_text())
        self.report = evaluate(self.source)
        self.src_path = self.root / "source.json"
        self.rpt_path = self.root / "report.json"
        self.dest = self.root / "explanations.json"
        self.src_path.write_text(json.dumps(self.source), encoding="utf-8")
        self.rpt_path.write_text(json.dumps(self.report), encoding="utf-8")

    def test_output_has_only_safe_reason_keys(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = main([str(self.src_path), str(self.rpt_path)])
        self.assertEqual(result, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["schema"], "konaklamaflow.explanations.v1")
        self.assertTrue(data["arrivals"])
        self.assertEqual(data["mode"], "NO_EXECUTION_READ_ONLY")

    def test_output_file_is_generated_without_source_values(self):
        self.assertEqual(main([str(self.src_path), str(self.rpt_path),
                               str(self.dest)]), 0)
        data = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertEqual(data["source_validity"], "UNVERIFIED_MINIMIZED_SNAPSHOT")
        self.assertNotIn("guest_name", self.dest.read_text())
        self.assertNotIn("passport", self.dest.read_text())

    def test_stale_or_bad_report_does_not_overwrite_existing_output(self):
        self.dest.write_text("SENTINEL", encoding="utf-8")
        self.report["summary"]["rooms"] = -1
        self.rpt_path.write_text(json.dumps(self.report))
        with contextlib.redirect_stderr(io.StringIO()) as err:
            result = main([str(self.src_path), str(self.rpt_path),
                           str(self.dest)])
        self.assertEqual(result, 2)
        self.assertEqual(self.dest.read_text(), "SENTINEL")
        self.assertIn("Invalid or stale", err.getvalue())

    def test_invalid_source_content_never_echoes(self):
        self.src_path.write_text('{"guest_name":"PRIVATE_TEST","schema_version":"0.3"}')
        with contextlib.redirect_stderr(io.StringIO()) as err:
            result = main([str(self.src_path), str(self.rpt_path)])
        self.assertEqual(result, 2)
        self.assertNotIn("PRIVATE_TEST", err.getvalue())


if __name__ == "__main__":
    unittest.main()
