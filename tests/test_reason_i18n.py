"""Presentation translations may not change or authorize operational decisions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from konaklamaflow.experience_engine import BLOCKER_CODES, evaluate
from konaklamaflow.reason_i18n import (
    CODES, SUPPORTED, RTL, LocalizationError, localize_code, localized_pre_review,
    resolve_locale,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"tr", "en", "fr", "el", "he", "ar", "de", "ru", "es", "uk"}


class TenLanguageReviewTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / "examples/fictional-hotel.json").read_text())
        self.report = evaluate(self.source)

    def test_all_26_reason_codes_have_nonempty_translations_for_ten_locales(self):
        self.assertEqual(set(SUPPORTED), EXPECTED)
        self.assertEqual(set(CODES), BLOCKER_CODES)
        self.assertEqual(len(CODES), 26)
        for language in SUPPORTED:
            for code in CODES:
                with self.subTest(locale=language, reason=code):
                    t = localize_code(code, language)
                    self.assertEqual(t["reason_code"], code)
                    self.assertTrue(t["text"].strip())
                    self.assertEqual(t["translation_status"], "CATALOG_DRAFT_UNREVIEWED")
                    self.assertEqual(t["direction"], "rtl" if language in RTL else "ltr")

    def test_bcp_locale_variations_and_explicit_fallback(self):
        for requested, expected in (("tr-TR", "tr"), ("en-US", "en"),
                                    ("fr-CA", "fr"), ("de-DE", "de"),
                                    ("el-GR", "el"), ("he-IL", "he"),
                                    ("ar-SA", "ar"), ("ru-RU", "ru"),
                                    ("es-MX", "es"), ("uk-UA", "uk")):
            with self.subTest(requested=requested):
                self.assertEqual(resolve_locale(requested)["locale"], expected)
        other = resolve_locale("pt-BR")
        self.assertEqual(other["locale"], "en")
        self.assertEqual(other["translation_status"], "FALLBACK_EN_UNSUPPORTED_LOCALE")
        self.assertEqual(resolve_locale("he")["direction"], "rtl")
        self.assertEqual(resolve_locale("ar")["direction"], "rtl")
        for bad in ("", "../../etc", "language=tr", "x" * 100, None, 12, "he<script>"):
            with self.subTest(bad=bad), self.assertRaises(LocalizationError):
                resolve_locale(bad)

    def test_rule_report_is_unmodified_and_human_review_only_for_all_languages(self):
        src, orig = deepcopy(self.source), deepcopy(self.report)
        expected_codes = [(r["task_id"], r["status"], r["blockers"])
                          for r in self.report["arrivals"]]
        for language in SUPPORTED:
            out = localized_pre_review(self.source, self.report, language)
            self.assertEqual(out["mode"], "NO_EXECUTION_READ_ONLY")
            self.assertEqual(out["schema"], "konaklamaflow.localized-pre-review.v1")
            self.assertEqual(out["source_validity"], "UNVERIFIED_MINIMIZED_SNAPSHOT")
            self.assertTrue(out["no_live_write"])
            self.assertEqual(out["translation_status"], "CATALOG_DRAFT_UNREVIEWED")
            actual_codes = [(r["task_id"], r["status_code"], r["reason_codes"])
                            for r in out["results"]]
            self.assertEqual(actual_codes, expected_codes)
            self.assertTrue(all(result["staff_action"] for result in out["results"]))
        self.assertEqual(self.source, src)
        self.assertEqual(self.report, orig)

    def test_invalid_and_stale_data_are_rejected_without_echoing(self):
        tampered = deepcopy(self.report)
        tampered["summary"]["rooms"] = -999
        with self.assertRaises(LocalizationError):
            localized_pre_review(self.source, tampered, "en")
        stale = deepcopy(self.source)
        stale["rooms"][0]["capacity"] += 1
        with self.assertRaises(LocalizationError):
            localized_pre_review(stale, self.report, "tr")
        dirty = deepcopy(self.source)
        dirty["reservations"][0]["email"] = "NEVER_OUTPUT_THIS"
        with self.assertRaises(LocalizationError) as raised:
            localized_pre_review(dirty, self.report, "fr")
        self.assertNotIn("NEVER_OUTPUT_THIS", str(raised.exception))
        for code in ("NOT_A_REAL_REASON", "guest@email.com", "", None):
            with self.subTest(code=code), self.assertRaises(LocalizationError):
                localize_code(code, "tr")

    def test_guest_ids_and_financial_values_are_not_emitted(self):
        for language in SUPPORTED:
            serialized = json.dumps(localized_pre_review(self.source, self.report, language),
                                    ensure_ascii=False)
            for reservation in self.source["reservations"]:
                for field in ("external_ref", "pms_ref", "id", "room_id"):
                    value = reservation.get(field)
                    if value and len(str(value)) >= 6:
                        self.assertNotIn('"' + str(value) + '"', serialized)
            self.assertNotIn("price_total", serialized)
            self.assertNotIn("passport", serialized)
            self.assertNotIn("api_key", serialized)

    def test_localized_status_does_not_falsely_claim_checkin(self):
        for language in SUPPORTED:
            out = localized_pre_review(self.source, self.report, language)
            self.assertTrue(out["source_notice"])
            self.assertTrue(out["no_live_write"])
            self.assertEqual(out["report_snapshot_sha256"], self.report["snapshot_sha256"])


if __name__ == "__main__":
    unittest.main()
