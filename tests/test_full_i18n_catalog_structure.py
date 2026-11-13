"""The offline language dictionary must cover exactly ten locales.

This test protects the browser from loading half-filled catalog rows.
It does not certify human linguistic accuracy.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
CATALOG=(ROOT/'demo/full-ui-i18n-catalog.js').read_text(encoding='utf-8')
ENGINE=(ROOT/'demo/full-ui-i18n.js').read_text(encoding='utf-8')

class FullI18nCatalogStructureTests(unittest.TestCase):
    def test_ten_languages_for_every_authored_localized_term(self):
        blocks=re.findall(r'fullUiRows\((\[\[[\s\S]*?\]\])\);',CATALOG)
        self.assertEqual(len(blocks),2)
        rows=[entry for block in blocks for entry in json.loads(block)]
        self.assertGreaterEqual(len(rows),100)
        seen=set()
        for row in rows:
            self.assertEqual(len(row),10)
            self.assertTrue(all(isinstance(value,str) and value.strip() for value in row))
            self.assertNotIn(row[0],seen)
            seen.add(row[0])

    def test_ten_navigation_categories_each_have_eighteen_labels(self):
        pattern=re.compile(r'^([a-z]{2}):\[(.*?)\],?\s*$',re.MULTILINE)
        head=ENGINE.split('const fullUiMenu={',1)[1].split('};',1)[0]
        labels=pattern.findall(head)
        self.assertEqual(len(labels),10)
        for lang,source in labels:
            # JS arrays are authored with single-quoted strings; we only count
            # delimiters and avoid evaluating JavaScript during Python tests.
            self.assertEqual(source.count("','")+1,18,lang)
        self.assertEqual({k for k,_ in labels},
                         {'tr','en','fr','el','he','ar','de','ru','es','uk'})

    def test_fallbacks_must_be_offline_and_decision_neutral(self):
        self.assertNotIn('fetch(',ENGINE)
        self.assertNotIn('XMLHttpRequest',ENGINE)
        self.assertNotIn('localStorage',ENGINE)
        self.assertNotIn('evaluate(',ENGINE)
        self.assertIn('document.documentElement.dir',ENGINE)
        self.assertIn('window.localizePageMetadata',ENGINE)

if __name__=='__main__':
    unittest.main()
