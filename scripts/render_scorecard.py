"""Offline HTML scorecard from the deterministic, project-labeled synthetic benchmark.

Do not interpret this as independent expert validation or hotel performance.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import sys

from konaklamaflow.evaluation import (
    DEFAULT_MANIFEST, SOURCE_FIXTURE, SCHEMA, run_evaluation,
)
from konaklamaflow.io_safety import read_limited_json

ROOT = Path(__file__).resolve().parents[1]
METRIC_LABELS = (
    ("precision", "Precision", "TP / (TP + FP)"),
    ("recall", "Recall", "TP / (TP + FN)"),
    ("false_positive_rate", "False positive rate", "FP / (FP + TN)"),
    ("false_negative_rate", "False negative rate", "FN / (FN + TP)"),
)


def authoritative_report(root=ROOT):
    base = Path(root)
    return run_evaluation(
        read_limited_json(str(base / "evaluation" / "benchmark.json")),
        read_limited_json(str(base / "examples" / "fictional-hotel.json")),
    )


def fmt_ratio(value):
    if value is None:
        return "Undefined — zero denominator"
    if type(value) not in (float, int) or not 0 <= value <= 1:
        raise ValueError("Invalid synthetic ratio")
    return f"{value:.1%}"


def render_scorecard(report, root=ROOT):
    """Fail closed: never publish a caller-invented score as authoritative."""
    if report != authoritative_report(root) or report.get("schema_version") != SCHEMA:
        raise ValueError("Unverified synthetic benchmark report")
    esc = lambda value: escape(str(value), quote=True)
    summary, metrics = report["summary"], report["metrics"]
    if (report["mode"] != "DRY_RUN_ONLY"
            or report["human_override_rate"] != "not_measured"
            or report["independent_expert_review"] != "not_performed"):
        raise ValueError("Synthetic safety boundary missing")
    labels = {
        "pass": "Matched project label",
        "fail": "MISMATCH — expected vs observed",
        "unsupported": "Excluded — unsupported",
        "unlabelled": "Excluded — not independently labeled",
    }
    cards = [
        ("Scored cases", f"{summary['evaluated']} / {summary['total_cases']}",
         "Not all scenario categories are supported"),
        ("Coverage", fmt_ratio(summary["coverage"]),
         "Scored case count / total cases"),
        ("TP / TN", f"{metrics['tp']} / {metrics['tn']}",
         "Project-authored synthetic labels"),
        ("FP / FN", f"{metrics['fp']} / {metrics['fn']}",
         "On the scored labels only"),
    ]
    card_html = "".join(
        '<div class="card"><span>'+esc(name)+'</span><strong>'+
        esc(value)+'</strong><small>'+esc(note)+'</small></div>'
        for name, value, note in cards
    )
    metric_html = "".join(
        '<tr><th scope="row">'+esc(name)+'</th><td>'+esc(fmt_ratio(metrics[key]))+
        '</td><td><code>'+esc(formula)+'</code></td></tr>'
        for key, name, formula in METRIC_LABELS
    )
    rows = []
    for case in report["cases"]:
        if case["status"] not in labels:
            raise ValueError("Unknown benchmark status")
        code = case.get("reason_code", "not evaluated")
        expected = ("yes" if case["expected"] else "no") if "expected" in case else "n/a"
        predicted = ("yes" if case["predicted"] else "no") if "predicted" in case else "n/a"
        rows.append(
            '<tr><th scope="row"><code>'+esc(case["id"])+
            '</code></th><td>'+esc(case["category"])+
            '</td><td><code>'+esc(code)+
            '</code></td><td>'+esc(expected)+'</td><td>'+esc(predicted)+
            '</td><td>'+esc(labels[case["status"]])+'</td></tr>'
        )
    css = """
    :root{color-scheme:dark;font:15px system-ui,-apple-system,sans-serif;background:#0e1427;color:#f2f5ff}
    *{box-sizing:border-box}body{margin:0}main{max-width:1180px;padding:26px 20px 56px;margin:auto}
    a{color:#9fe7db}h1{font-size:clamp(24px,4vw,39px);margin:10px 0}h2{font-size:20px;margin-top:32px}
    p{line-height:1.65;color:#c9d5e9}.eyebrow{color:#86e4c4;font-size:12px;letter-spacing:.08em;text-transform:uppercase}
    .panel{border:1px solid #35456b;background:#18233c;border-radius:17px;padding:22px;margin-top:20px}
    .cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
    .card{display:flex;flex-direction:column;gap:9px;border:1px solid #45537b;border-radius:12px;padding:16px;background:#202b49;min-width:0}
    .card strong{font-size:clamp(22px,3vw,30px);color:#a3f5d9;font-variant-numeric:tabular-nums}
    .card span{font-weight:700}.card small{color:#c6d1e9;line-height:1.5}
    .table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:660px}
    th,td{text-align:start;padding:12px 10px;border-bottom:1px solid #3b4a68;vertical-align:top}
    th{font-weight:650}code{overflow-wrap:anywhere;word-break:break-word;font-size:12px;color:#b2e4ff}
    .caution{border-inline-start:3px solid #e8c480;padding:10px 15px;background:#302c36}
    :focus-visible{outline:3px solid #f5d886;outline-offset:3px}
    @media(max-width:760px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}main{padding:15px}}
    @media(max-width:390px){.cards{grid-template-columns:1fr}.panel{padding:13px}}
    """
    return (
        '<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'style-src &#39;unsafe-inline&#39;; img-src &#39;none&#39;; '
        'connect-src &#39;none&#39;; script-src &#39;none&#39;; form-action &#39;none&#39;">'
        '<title>KonaklamaFlow | Synthetic scorecard</title>'
        '<style>'+css+'</style></head><body><main>'
        '<a href="index.html">← Kurgusal otel demosuna dön</a>'
        '<p class="eyebrow">DRY_RUN_ONLY · Project-authored synthetic benchmark</p>'
        '<h1>Karar doğruluğu — sentetik ölçüm paneli</h1>'
        '<p class="caution"><strong>Gerçek otel doğruluğu değildir.</strong> '
        'Etiketler proje içinde oluşturulmuştur; bağımsız uzman kontrolü veya '
        'gerçek operasyon pilotu yapılmamıştır. Sıfır hata, üretim güvenilirliği kanıtı değildir.</p>'
        '<div class="cards">'+card_html+'</div>'
        '<section class="panel"><h2>Ölçüm oranları ve paydaları</h2>'
        '<div class="table-wrap"><table><thead><tr><th>Gösterge</th><th>Sonuç</th>'
        '<th>Tanım</th></tr></thead><tbody>'+metric_html+'</tbody></table></div>'
        '<p><strong>Ölçüm birimi:</strong> Bir vakada tek rezervasyon için tek gerekçe kodunun '
        'beklenen/gözlenen ikili durumu. Desteklenmeyen ve etiketlenmeyen '
        'vakalar accuracy metriklerinin dışında; kapsamın içindedir.</p>'
        '<p>Excluded: unsupported='+esc(summary["unsupported"])+
        '; unlabelled='+esc(summary["unlabelled"])+'.'
        ' Human override: not_measured · processing time: not_measured.</p></section>'
        '<section class="panel"><h2>Sentetik vakalar</h2>'
        '<div class="table-wrap"><table><thead><tr><th>Vaka</th><th>Tür</th><th>Gerekçe</th>'
        '<th>Beklenen</th><th>Gözlenen</th><th>Durum</th></tr></thead><tbody>'+
        "".join(rows)+'</tbody></table></div></section>'
        '<p>Çevrimdışı, salt okunur. Canlı AI/PMS/OTA/KBS/ödeme bağlantısı yok.</p>'
        '</main></body></html>\n'
    )


def scorecard_html(root=ROOT):
    return render_scorecard(authoritative_report(root), root)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render fictional benchmark scorecard")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output")
    group.add_argument("--check")
    args = parser.parse_args(argv)
    try:
        content = scorecard_html()
        target = Path(args.output or args.check)
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                raise ValueError("Synthetic scorecard not current")
        else:
            if target.exists() or target.is_symlink():
                raise ValueError("Refuse to overwrite scorecard")
            target.write_text(content, encoding="utf-8")
        return 0
    except (OSError, ValueError, TypeError, RecursionError):
        print("Invalid synthetic scorecard source or output", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
