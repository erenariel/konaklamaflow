"""Build a product-facing, offline scenario viewer from Python solver outputs.

All assignments are computed by the authoritative fictional Python solver at
build time. Browser JavaScript only switches already-rendered scenario panels;
it never recomputes, approves or writes an allocation.
"""
from __future__ import annotations

from base64 import b64encode
from hashlib import sha256
from html import escape

from konaklamaflow.global_room_solver import propose_global_room_plan
from konaklamaflow.room_allocation_solver import SCHEMA


SCENARIOS = (18, 60, 200)
SCRIPT = """(() => {
  const buttons = [...document.querySelectorAll('[data-scenario-button]')];
  const panels = [...document.querySelectorAll('[data-scenario-panel]')];
  function activate(id) {
    for (const button of buttons) {
      button.setAttribute('aria-pressed',
        String(button.getAttribute('data-scenario-button') === id));
    }
    for (const panel of panels) {
      panel.hidden = panel.getAttribute('data-scenario-panel') !== id;
    }
  }
  for (const button of buttons) {
    button.addEventListener('click', () =>
      activate(button.getAttribute('data-scenario-button')));
  }
  document.getElementById('resetScenario').addEventListener('click',
    () => activate('18'));
})();"""


def _room(n: int, bed: str) -> dict:
    return {"id": f"R{n:03d}", "category": "standard", "capacity": 2,
            "bed": bed, "readiness": "inspected",
            "occupancy": "verified_vacant", "maintenance": []}


def _stay(n: int, bed: str) -> dict:
    return {"id": f"S{n:03d}", "arrival": "2026-11-17",
            "departure": "2026-11-20", "category": "standard",
            "persons": 2, "bed_request": bed, "status": "confirmed"}


def example_source(size: int) -> dict:
    """Synthetic-only input, deliberately independent of actual hotel records."""
    if size not in SCENARIOS:
        raise ValueError("Unsupported fictional scenario")
    twins = max(1, size // 5)
    return {
        "schema_version": SCHEMA, "source_kind": "fictional",
        "rooms": [_room(i, "twin" if i < twins else "double")
                  for i in range(size)],
        "stays": [_stay(i, "twin" if i < twins else "none")
                  for i in range(size)],
        "holds": [],
    }


def scenario_reports():
    """Compute authentic, all-or-nothing results once at build time."""
    reports = {}
    for size in SCENARIOS:
        report = propose_global_room_plan(example_source(size), max_seconds=30)
        if report["status"] != "proposed" or len(report["proposals"]) != size:
            # Fail closed: never publish a fake successful scenario.
            raise ValueError("Fictional allocation scenario is not fully solved")
        reports[size] = report

    unknown = {
        "schema_version": SCHEMA, "source_kind": "fictional",
        "rooms": [{**_room(0, "twin"), "occupancy": "unknown"}],
        "stays": [_stay(0, "twin")],
        "holds": [],
    }
    failure = propose_global_room_plan(unknown, max_seconds=30)
    if failure["status"] != "manual_review_required" or failure["proposals"]:
        raise ValueError("Uncertain occupancy was incorrectly proposed")
    reports["review"] = failure
    return reports


STYLE = """*{box-sizing:border-box}html{color-scheme:dark;scroll-behavior:smooth}
body{margin:0;background:#0b1220;color:#e8edf7;font-family:system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.55}
main,header,footer{max-width:1100px;margin:auto;padding:25px 20px}
a{color:#a6d9ff}nav{display:flex;flex-wrap:wrap;gap:15px}
header{border-bottom:1px solid #26344c}h1{font-size:clamp(26px,4vw,43px);line-height:1.17;letter-spacing:-.03em;margin:14px 0}
h2{font-size:clamp(21px,3vw,29px);margin:0 0 8px}
.kicker{color:#9ae7cc;font-size:12px;text-transform:uppercase;letter-spacing:.12em;font-weight:750}
.muted{color:#b4c2d7}.lead{font-size:17px;max-width:760px}.notice{background:#14243a;border:1px solid #32516d;padding:15px 18px;border-radius:12px}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin:25px 0 18px}
button{font:inherit;cursor:pointer;padding:11px 16px;background:#1b304e;color:#f3f7ff;border:1px solid #486384;border-radius:10px;min-height:44px}
button[aria-pressed="true"]{background:#b2e8dc;color:#0d2536;border-color:#b2e8dc;font-weight:750}
button:hover{border-color:#b2e8dc}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #efdc94;outline-offset:3px}
.panels{min-height:380px}.panel{border:1px solid #344766;background:#101c30;border-radius:16px;padding:24px}
.panel[hidden]{display:none}.panel,.notice,.stat,button{min-width:0;overflow-wrap:anywhere}code{white-space:normal;word-break:break-word;overflow-wrap:anywhere}.stat-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:22px 0}
.stat{background:#1b2a42;border:1px solid #334867;border-radius:12px;padding:15px}
.stat strong{font-size:clamp(22px,4vw,34px);display:block}.stat span{color:#b4c2d7;font-size:13px}
.status{display:inline-block;color:#a6f4d9;background:#1c403c;padding:5px 10px;border-radius:30px;font-size:13px;font-weight:700}
.status.review{background:#53391f;color:#ffe0ab}.explain{padding-left:20px;color:#c3d1e5}
details{border:1px solid #344766;border-radius:12px;margin-top:20px;padding:12px 16px;background:#16253b}
summary{cursor:pointer;font-weight:700}table{border-collapse:collapse;width:100%;margin-top:10px;font-size:14px}
th,td{text-align:left;border-bottom:1px solid #334867;padding:10px}th{color:#bbd1e8}
.scroll{overflow-x:auto}footer{border-top:1px solid #26344c;margin-top:30px;color:#b4c2d7;font-size:13px}
@media(max-width:620px){.stat-grid{grid-template-columns:1fr}.panel{padding:16px}main,header,footer{padding-left:15px;padding-right:15px}.controls button{flex:1}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def _panel(size, report):
    approved = report["status"] == "proposed"
    proposals = report["proposals"]
    heading = (f"{size} odalı kurgusal otel" if isinstance(size, int)
               else "Bilinmeyen doluluk — insan incelemesi")
    status = ("Tam öneri üretildi" if approved else "Personel incelemesi gerekiyor")
    cls = "status" if approved else "status review"
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>Personel onayı gerekli</td></tr>".format(
            escape(p["stay_id"]), escape(p["room_id"]))
        for p in proposals
    )
    explanation = (
        "Sistem, oda kategorisi, kapasite, yatak tipi, bakım ve tarih "
        "çakışması kurallarını kullanarak tüm gruba eksiksiz bir öneri buldu."
        if approved else
        "Odanın fiziksel boşluğu doğrulanmadığı için tahsis önerisi yapılmadı."
    )
    sample = (
        "<details><summary>Tüm {} oda önerisini göster</summary>"
        "<div class='scroll'><table><thead><tr><th>Konaklama</th>"
        "<th>Önerilen oda</th><th>Yetki sınırı</th></tr></thead>"
        "<tbody>{}</tbody></table></div></details>".format(len(proposals), rows)
        if approved else "<p><strong>Öneri yok.</strong> Gerçek durum ayrıca doğrulanmalı.</p>"
    )
    return (
        f'<section class="panel" data-scenario-panel="{size}"'
        + ("" if size == 18 else " hidden")
        + f' aria-label="{escape(heading)}">'
        + f'<span class="{cls}">{status}</span>'
        + f'<h2>{escape(heading)}</h2>'
        + f'<p class="muted">{explanation}</p>'
        + '<div class="stat-grid">'
        + f'<div class="stat"><strong>{report["search"]["candidate_rooms"]}</strong><span>Kurgusal oda</span></div>'
        + f'<div class="stat"><strong>{report["search"]["requested_stays"]}</strong><span>Konaklama isteği</span></div>'
        + f'<div class="stat"><strong>{len(proposals)}</strong><span>Eksiksiz öneri</span></div>'
        + '</div><p class="muted">Durum: <code>{}</code> · Gerekçe: <code>{}</code>'
        .format(escape(report["status"]), escape(", ".join(report["reason_codes"])))
        + f' · Aranan aday sayısı: {report["search"]["states_explored"]}</p>'
        + "<p>Öneriler yalnızca kurgusal veriden, Python çözücüsüyle "
        "sayfa oluşturulurken hesaplandı. Bu ekran veri girişi veya "
        "gerçek rezervasyon onayı yapmaz.</p>"
        + sample
        + '</section>'
    )


def global_allocation_lab_html(root=None):
    """Generate a complete offline browser page with no live integration."""
    reports = scenario_reports()
    panels = "".join(_panel(key, reports[key]) for key in (*SCENARIOS, "review"))
    buttons = "".join(
        f'<button type="button" data-scenario-button="{size}"'
        + (' aria-pressed="true"' if size == 18 else ' aria-pressed="false"')
        + f'>{size} oda</button>'
        for size in SCENARIOS
    )
    buttons += ('<button type="button" aria-pressed="false" '
                'data-scenario-button="review">Bilinmeyen doluluk</button>')
    script_hash = b64encode(sha256(SCRIPT.encode("utf-8")).digest()).decode("ascii")
    csp = ("default-src 'none'; connect-src 'none'; "
           "style-src 'unsafe-inline'; script-src 'sha256-" + script_hash +
           "'; base-uri 'none'; form-action 'none'; img-src 'self' data:")
    return (
        '<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="' + escape(csp, quote=False) + '">'
        '<meta name="description" content="Kurgusal, çevrimdışı 18, 60 ve 200 odalı '
        'KonaklamaFlow oda tahsis önerisi laboratuvarı">'
        '<title>KonaklamaFlow | Oda Tahsis Laboratuvarı</title>'
        '<style>' + STYLE + '</style></head><body>'
        '<header><nav><a href="index.html">← Ana otel demosu</a>'
        '<a href="project-overview.html">Program modülleri</a></nav></header>'
        '<main><span class="kicker">Gerçek Python çıktısı · Kurgusal otel · Çevrimdışı</span>'
        '<h1>Oda tahsis önerilerini keşfet</h1>'
        '<p class="lead">18, 60 ve 200 odalı sentetik örneklerde Python çözücüsünün '
        'ürettiği tam önerileri ve hiçbir öneri vermemesi gereken durumları incele.</p>'
        '<div class="notice"><strong>Gerçek tahsis değildir.</strong> Oda önerileri '
        'otomatik check-in, PMS/OTA/KBS kaydı, ödeme veya personel onayı oluşturmaz. '
        'Büyük otellerde her zaman çözüm garantisi yoktur; arama sınırları '
        'aşıldığında sistem öneri üretmez.</div>'
        '<div class="controls" role="group" aria-label="Kurgusal senaryo seç">'
        + buttons
        + '<button type="button" id="resetScenario">Sıfırla</button></div>'
        '<div class="panels" aria-live="polite">'
        + panels + '</div>'
        '</main><footer>KonaklamaFlow · Yalnızca kurgusal veriler ve kaynak-kodlu '
        'Python hesapları · İnsan kontrolü zorunludur · Canlı sistem bağlı değildir.'
        '</footer><script>' + SCRIPT + '</script></body></html>'
    )
