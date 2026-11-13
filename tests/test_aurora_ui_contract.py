"""Aurora styling remains source-bound, offline and motion-safe.

This does not imply live AI execution, PMS writes or new canonical data.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AuroraStyleContractTests(unittest.TestCase):
    def test_both_themes_are_embedded_exactly_once(self):
        html = (ROOT / "demo/v04-integrated-preview.html").read_text(encoding="utf-8")
        for file, begin, end in (
            ("ai-command-center.css", "/* BEGIN AI_COMMAND_CSS */", "/* END AI_COMMAND_CSS */"),
            ("hotel-ops-styles.css", "/* BEGIN GENERATED_HOTEL_OPS_STYLES */", "/* END GENERATED_HOTEL_OPS_STYLES */"),
        ):
            content = (ROOT / "demo" / file).read_text(encoding="utf-8")
            self.assertIn("AURORA 01", content)
            self.assertEqual(html.count(begin), 1)
            self.assertEqual(html.count(end), 1)
            self.assertIn(begin + "\n" + content + "\n" + end, html)

    def test_motion_opt_out_and_keyboard_focus_are_present(self):
        css = "\n".join((ROOT / "demo" / x).read_text(encoding="utf-8")
                        for x in ("ai-command-center.css", "hotel-ops-styles.css"))
        self.assertIn('data-kf-motion="off"', css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("focus-visible", css)
        self.assertIn("data-kf-theme", css)
        self.assertIn(".rack-row", css)
        self.assertIn(".ops-table", css)

if __name__ == "__main__":
    unittest.main()
