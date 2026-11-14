"""The offline trace page is derived from the actual verified Python chain."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.render_trace_view import trusted_trace, render_trace_view, trace_view_html, main
from scripts.stage_demo_site import GENERATED_ASSETS, PUBLIC_ASSETS, stage_site


class TraceViewUiTests(unittest.TestCase):
    def test_real_hash_bound_fictional_trace_is_the_only_published_source(self):
        _,_,trace=trusted_trace()
        html=render_trace_view(trace)
        self.assertEqual(html.count('class="event"'),3)
        self.assertIn("Gerçek personel eylemi",html)
        self.assertIn("not independently anchored",html)
        for event in trace["events"]:
            self.assertIn(event["event_hash"],html)
            self.assertIn(event["task_id"],html)
            for code in event["reason_codes"]:
                self.assertIn(code,html)
        self.assertEqual(trace_view_html(),html)
        self.assertNotIn("<script",html.lower())
        self.assertNotIn("guest_email",html)

    def test_source_tamper_role_and_chain_changes_fail_closed(self):
        _,_,trace=trusted_trace()
        variants=[]
        for key,val in (("simulated_role","administrator"),
                        ("event_hash","f"*64),("sequence",10),
                        ("reason_codes",["FAKE_APPROVAL"])):
            candidate=deepcopy(trace)
            candidate["events"][0][key]=val
            variants.append(candidate)
        removed=deepcopy(trace)
        removed["events"].pop()
        variants.append(removed)
        for candidate in variants:
            with self.subTest(payload=candidate["events"]),self.assertRaises(ValueError):
                render_trace_view(candidate)

    def test_cli_and_staged_site_are_offline_and_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"fictional-trace.html"
            self.assertEqual(main(["--output",str(path)]),0)
            self.assertEqual(main(["--check",str(path)]),0)
            path.write_text("forged",encoding="utf-8")
            self.assertEqual(main(["--check",str(path)]),2)
            self.assertEqual(main(["--output",str(path)]),2)
            stage=Path(d)/"stage"
            stage_site(stage)
            self.assertEqual((stage/"fictional-trace.html").read_text(),trace_view_html())
            self.assertEqual({p.name for p in stage.iterdir()},
                             set(PUBLIC_ASSETS)|set(GENERATED_ASSETS)|{".nojekyll"})


if __name__=="__main__":
    unittest.main()
