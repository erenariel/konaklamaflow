"""Test CLI locale selection, no PII and safe failure without clobbering output."""
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from konaklamaflow.experience_engine import evaluate
from konaklamaflow.reason_i18n_cli import main

ROOT = Path(__file__).resolve().parents[1]


class LocalizedReviewCliTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.snapshot = json.loads((ROOT / "examples/fictional-hotel.json").read_text(encoding="utf-8"))
        self.report = evaluate(self.snapshot)
        self.source_path = self.root / "snapshot.json"
        self.report_path = self.root / "report.json"
        self.output_path = self.root / "translation.json"
        self.source_path.write_text(json.dumps(self.snapshot))
        self.report_path.write_text(json.dumps(self.report))

    def test_cli_emits_only_translated_pre_review_in_greek(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            result = main([str(self.source_path), str(self.report_path), "el-GR"])
        self.assertEqual(result, 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["locale"], "el")
        self.assertEqual(data["translation_status"], "CATALOG_DRAFT_UNREVIEWED")
        self.assertEqual(data["schema"], "konaklamaflow.localized-pre-review.v1")
        self.assertTrue(data["results"])
        self.assertNotIn("external_ref", out.getvalue())
        self.assertNotIn("pms_ref", out.getvalue())
        self.assertNotIn("price_total", out.getvalue())

    def test_unsupported_language_falls_back_to_english_openly(self):
        self.assertEqual(main([str(self.source_path), str(self.report_path),
                               "pt-BR", str(self.output_path)]), 0)
        data = json.loads(self.output_path.read_text())
        self.assertEqual(data["locale"], "en")
        self.assertEqual(data["translation_status"], "FALLBACK_EN_UNSUPPORTED_LOCALE")

    def test_bad_or_stale_data_does_not_overwrite_existing_output(self):
        self.output_path.write_text("SENTINEL")
        changed = deepcopy(self.report)
        changed["summary"]["rooms"] = -999
        self.report_path.write_text(json.dumps(changed))
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main([str(self.source_path), str(self.report_path),
                         "tr", str(self.output_path)])
        self.assertEqual(code, 2)
        self.assertEqual(self.output_path.read_text(), "SENTINEL")
        self.assertNotIn("SENTINEL", err.getvalue())

    def test_malformed_or_sensitive_json_not_echoed(self):
        self.source_path.write_text('{"private":"DO_NOT_ECHO", "schema_version":"0.3"}')
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = main([str(self.source_path), str(self.report_path), "ar"])
        self.assertEqual(code, 2)
        self.assertNotIn("DO_NOT_ECHO", err.getvalue())


if __name__ == "__main__":
    unittest.main()
