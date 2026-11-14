"""Generate all current demo views from one validated canonical fixture."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from konaklamaflow.canonical_presentation import build_presentation
from scripts.generate_suite_demo import embed as embed_review, safe_json
from scripts.generate_hotel_ops_demo import embed as embed_operations


def replace_block(text, start, end, body):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Missing or ambiguous generated source boundary')
    left = text.index(start)
    right = text.index(end, left) + len(end)
    return text[:left] + start + '\n' + body + '\n' + end + text[right:]


def generate(check=False):
    source = json.loads((ROOT/'examples/canonical-hotel.json').read_text(encoding='utf-8'))
    bundle = build_presentation(source)
    outputs = {}
    for name, key in [('canonical-review.json', 'review_data'),
                      ('canonical-review-report.json', 'review_report'),
                      ('canonical-operations.json', 'operations_data'),
                      ('canonical-operations-report.json', 'operations_report')]:
        outputs[ROOT/'examples'/name] = json.dumps(bundle[key], ensure_ascii=False, indent=2) + '\n'
    for filename in ('hotel-suite.html', 'v04-integrated-preview.html'):
        path = ROOT/'demo'/filename
        text = embed_review(path.read_text(encoding='utf-8'), bundle['review_data'], bundle['review_report'])
        start, end = '// BEGIN GENERATED_CANONICAL_DATA', '// END GENERATED_CANONICAL_DATA'
        if start not in text:
            marker = '// END GENERATED_SUITE_DATA'
            text = text.replace(marker, marker + '\n' + start + '\n' + end, 1)
        text = replace_block(text, start, end,
                'const CANONICAL_DATA=' + safe_json(bundle['canonical']) + ';\n'
                + 'const CANONICAL_LINKS=' + safe_json(bundle['canonical_links']) + ';')
        if filename == 'v04-integrated-preview.html':
            text = embed_operations(text, bundle['operations_data'], bundle['operations_report'])
            workflow_start, workflow_end = '// BEGIN GENERATED_CANONICAL_WORKFLOWS', '// END GENERATED_CANONICAL_WORKFLOWS'
            if workflow_start not in text:
                left = text.index('/* KonaklamaFlow illustrated hotel workflows')
                right = text.index('</script>', left)
                text = text[:left] + workflow_start + '\n' + text[left:right] + workflow_end + '\n' + text[right:]
            text = replace_block(text, workflow_start, workflow_end,
                                 (ROOT/'demo/hotel-workflow-ui.js').read_text(encoding='utf-8'))
            # Presentation translations are not decisions; bind their existing
            # reason/evidence catalog to the same current Python review source.
            match = re.search(r'\bconst V04_CATALOG\s*=\s*', text)
            if match is None:
                raise ValueError('Missing localized review catalog')
            catalog, size = json.JSONDecoder().raw_decode(text[match.end():])
            catalog['sourceSha'] = bundle['review_report']['snapshot_sha256']
            text = text[:match.end()] + safe_json(catalog) + text[match.end()+size:]
            start, end = '// BEGIN GENERATED_CANONICAL_UI', '// END GENERATED_CANONICAL_UI'
            if start not in text:
                text = text.replace('</body>', '<script>\n' + start + '\n' + end + '\n</script>\n</body>', 1)
            text = replace_block(text, start, end, (ROOT/'demo/canonical-navigation.js').read_text(encoding='utf-8'))
            aurora_start, aurora_end = '// BEGIN GENERATED_AURORA_ROOM_UI', '// END GENERATED_AURORA_ROOM_UI'
            if aurora_start not in text:
                text = text.replace(end, end + '\n' + aurora_start + '\n' + aurora_end, 1)
            text = replace_block(text, aurora_start, aurora_end,
                'const AURORA_ROOM_GRAPH=' + safe_json(bundle['room_graph']) + ';\n'
                + (ROOT/'demo/aurora-room-i18n.js').read_text(encoding='utf-8') + '\n'
                + (ROOT/'demo/aurora-room-plan.js').read_text(encoding='utf-8'))
            timeline_start, timeline_end = '// BEGIN GENERATED_AURORA_TIMELINE_UI', '// END GENERATED_AURORA_TIMELINE_UI'
            if timeline_start not in text:
                text = text.replace(aurora_end, aurora_end + '\n' + timeline_start + '\n' + timeline_end, 1)
            text = replace_block(text, timeline_start, timeline_end,
                                 (ROOT/'demo/aurora-timeline.js').read_text(encoding='utf-8'))
            css_start, css_end = '/* BEGIN GENERATED_AURORA_ROOM_STYLES */', '/* END GENERATED_AURORA_ROOM_STYLES */'
            if css_start not in text:
                text = text.replace('</head>', '<style>\n' + css_start + '\n' + css_end + '\n</style>\n</head>', 1)
            text = replace_block(text, css_start, css_end,
                                 (ROOT/'demo/aurora-room-plan.css').read_text(encoding='utf-8'))
            timeline_css_start, timeline_css_end = '/* BEGIN GENERATED_AURORA_TIMELINE_STYLES */', '/* END GENERATED_AURORA_TIMELINE_STYLES */'
            if timeline_css_start not in text:
                text = text.replace(css_end, css_end + '\n' + timeline_css_start + '\n' + timeline_css_end, 1)
            text = replace_block(text, timeline_css_start, timeline_css_end,
                                 (ROOT/'demo/aurora-timeline.css').read_text(encoding='utf-8'))
        outputs[path] = text
    path = ROOT/'demo/global-presentation-concept.html'
    outputs[path] = replace_block(path.read_text(encoding='utf-8'),
        '// BEGIN GENERATED_CANONICAL_CONCEPT', '// END GENERATED_CANONICAL_CONCEPT',
        'const CANONICAL_CONCEPT=' + safe_json(bundle['concept']) + ';')
    changed = [str(path.relative_to(ROOT)) for path, text in outputs.items()
               if not path.exists() or path.read_text(encoding='utf-8') != text]
    if check:
        if changed:
            raise ValueError('Canonical generated views are stale: ' + ', '.join(changed))
    else:
        for path, text in outputs.items():
            path.write_text(text, encoding='utf-8')
    return bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        generate(args.check)
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print('Canonical generation failed: ' + type(error).__name__, file=sys.stderr)
        return 1
    print('All current demo projections match one Python-validated canonical fixture.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
