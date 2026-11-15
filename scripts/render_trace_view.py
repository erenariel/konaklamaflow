"""Public, fictional, source-verified trace viewer. No staff authorization implied.

A rendered chain cannot prove immutability without an independently trusted anchor.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import sys

from konaklamaflow.decision_trace import fictional_walkthrough, verify_trace
from konaklamaflow.experience_engine import evaluate
from konaklamaflow.io_safety import read_limited_json

ROOT = Path(__file__).resolve().parents[1]


def trusted_trace(root=ROOT):
    source = read_limited_json(str(Path(root) / "examples" / "fictional-hotel.json"))
    report = evaluate(source)
    trace = fictional_walkthrough(source, report)
    verify_trace(source, report, trace)
    return source, report, trace


def render_trace_view(trace, root=ROOT):
    """Accept only the complete, independently regenerated synthetic walkthrough."""
    source, report, reference = trusted_trace(root)
    verify_trace(source, report, trace)
    if trace != reference:
        raise ValueError("Synthetic trace was replaced, stale or not the example sequence")
    if trace["mode"] != "DRY_RUN_ONLY":
        raise ValueError("No authorization boundary")
    esc = lambda value: escape(str(value), quote=True)
    css = """
    :root{color-scheme:dark;background:#10182c;color:#ecf5ff;font:15px system-ui,-apple-system,sans-serif}
    *{box-sizing:border-box}body{margin:0}main{margin:auto;max-width:1100px;padding:28px 22px 60px}
    a{color:#92ecd6}h1{font-size:clamp(26px,4vw,40px);margin:10px 0}h2{font-size:21px}
    p{line-height:1.65;color:#d1d9ed}.eyebrow{letter-spacing:.08em;text-transform:uppercase;font-size:12px;color:#a7eee0}
    .warning{padding:15px 19px;border-radius:10px;background:#352f3e;border-inline-start:4px solid #eac48c}
    .hash{border:1px solid #53617e;padding:12px;border-radius:12px;background:#1a2942;margin-top:14px}
    .hash dt{font-weight:750;margin-bottom:5px}.hash dd{margin:0 0 12px;color:#e0effb}
    .cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;list-style:none;padding:0}
    .event{border:1px solid #566787;border-radius:15px;background:#1b2842;padding:18px;min-width:0}
    .event-head{color:#9cebcf;font-weight:800;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
    .event h3{font-size:18px;margin:10px 0}.event p{font-size:13px;margin:7px 0}
    .event dl{display:grid;grid-template-columns:1fr;gap:7px}.event dt{font-size:12px;color:#c2cae2}.event dd{margin:0}
    .pill{display:inline-block;background:#303e5d;border-radius:7px;padding:3px 7px;margin:3px 4px 2px 0}
    code{font-size:11px;overflow-wrap:anywhere;word-break:break-word;color:#b9e6ff}
    :focus-visible{outline:3px solid #ffe0a4;outline-offset:3px}
    @media(max-width:900px){.cards{grid-template-columns:1fr}}
    @media(max-width:390px){main{padding:14px}.event{padding:12px}}
    """
    timeline = []
    for event in trace["events"]:
        reasons = "".join('<code class="pill">'+esc(code)+'</code>'
                          for code in event["reason_codes"]) or '<em>None</em>'
        fields = "".join('<code class="pill">'+esc(code)+'</code>'
                         for code in event["evidence_field_paths"]) or '<em>None</em>'
        timeline.append(
            '<li class="event" data-sequence="'+esc(event["sequence"])+'" data-event="'+
            esc(event["kind"])+'">'
            '<span class="event-head">Simulation step '+esc(event["sequence"])+'</span>'
            '<h3>'+esc(event["kind"].replace("_", " ").title())+'</h3>'
            '<p><strong>Simulated role:</strong> '+esc(event["simulated_role"])+
            ' · <strong>Fictional time:</strong> <time datetime="'+esc(event["simulated_at"])+
            '">'+esc(event["simulated_at"])+'</time></p>'
            '<dl><dt>Opaque task ID</dt><dd><code>'+esc(event["task_id"])+
            '</code></dd><dt>Python reason codes</dt><dd>'+reasons+
            '</dd><dt>Evidence field names (not values)</dt><dd>'+fields+
            '</dd><dt>Previous link hash</dt><dd><code>'+esc(event["previous_hash"])+
            '</code></dd><dt>Event digest</dt><dd><code>'+esc(event["event_hash"])+
            '</code></dd></dl></li>'
        )
    return (
        '<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'script-src &#39;none&#39;; connect-src &#39;none&#39;; '
        'style-src &#39;unsafe-inline&#39;; img-src &#39;none&#39;; form-action &#39;none&#39;">'
        '<title>KonaklamaFlow | Fictional decision trace</title><style>'+css+
        '</style></head><body><main><a href="index.html">← Kurgusal otel demosuna dön</a>'
        '<p class="eyebrow">DRY_RUN_ONLY · simulated events, not production audit</p>'
        '<h1>Kurgusal karar geçmişi</h1>'
        '<p class="warning"><strong>Gerçek personel eylemi, check-in onayı veya değiştirilemez '
        'denetim kaydı değildir.</strong> Olaylar senaryo için üretilmiştir. '
        'Haricî güvenilir hash dayanağı olmadan tüm zincir yeniden hesaplanabilir.</p>'
        '<section class="hash"><h2>Kaynak ve doğrulama bağı</h2><dl>'
        '<dt>Source SHA-256 (fictional snapshot)</dt><dd><code>'+
        esc(trace["snapshot_sha256"])+
        '</code></dd><dt>Report SHA-256 (recomputed Python rules)</dt><dd><code>'+
        esc(trace["report_sha256"])+
        '</code></dd><dt>Final chain hash — not independently anchored</dt><dd><code>'+
        esc(trace["head_hash"])+
        '</code></dd></dl></section>'
        '<section><h2>Üç kurgusal inceleme adımı</h2><ol class="cards">'+
        "".join(timeline)+'</ol></section>'
        '<p>Olaylar doğrulanmış Python karar izinden türetilir. Hash dizisi yalnız '
        'gösterilen kurgusal dosyada değişikliklerin tespitini destekler; kişi/kurum '
        'yetkisi, gerçek zaman damgası, canlı AI, PMS, OTA, KBS veya ödeme kanıtı değildir.</p>'
        '</main></body></html>\n'
    )


def trace_view_html(root=ROOT):
    return render_trace_view(trusted_trace(root)[2], root)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render fictional read-only trace")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output")
    mode.add_argument("--check")
    args = parser.parse_args(argv)
    try:
        html = trace_view_html()
        path = Path(args.output or args.check)
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != html:
                raise ValueError("Stale trace viewer")
        else:
            if path.exists() or path.is_symlink():
                raise ValueError("Existing path may not be overwritten")
            path.write_text(html, encoding="utf-8")
        return 0
    except (ValueError, TypeError, OSError, RecursionError, OverflowError):
        print("Invalid fictional trace or output path", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
