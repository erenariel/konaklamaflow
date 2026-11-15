"""Interactive-looking but strictly Python-precomputed fictional allocation lab.

The browser only chooses from audited, deterministic example outcomes. It
does not run Python, compute room assignments or touch any live hotel data.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import sys

from konaklamaflow.room_allocation_solver import SCHEMA, propose_group

ROOT = Path(__file__).resolve().parents[1]

DATES = ("2026-11-16", "2026-11-18")


def room(ident, bed="double", *, occupancy="verified_vacant",
         readiness="inspected", maintenance=None):
    return {"id": ident, "category": "standard", "capacity": 2, "bed": bed,
            "readiness": readiness, "occupancy": occupancy,
            "maintenance": [] if maintenance is None else maintenance}


def stay(ident, bed="none", *, arrival=DATES[0], departure=DATES[1]):
    return {"id": ident, "arrival": arrival, "departure": departure,
            "category": "standard", "persons": 2,
            "bed_request": bed, "status": "confirmed"}


def source(rooms, stays, holds=None):
    return {"schema_version": SCHEMA, "source_kind": "fictional",
            "rooms": rooms, "stays": stays, "holds": [] if holds is None else holds}


SCENARIOS = (
    {
        "id": "twin-scarcity", "title": "Twin yatağı koru",
        "description": "A rezervasyonu yatak konusunda esnek, B için twin zorunlu. İki uygun odadan yalnız biri twin.",
        "source": source([room("T101", "twin"), room("D102")],
                         [stay("A_FLEX"), stay("B_TWIN", "twin")]),
        "expected": "proposed",
    },
    {
        "id": "maintenance", "title": "Bakım çakışması",
        "description": "Twin oda rezervasyon sırasında bakımda. Diğer odanın yatak türü isteği karşılamıyor.",
        "source": source(
            [room("T101", "twin", maintenance=[{"start": "2026-11-17", "end": "2026-11-20"}]),
             room("D102")],
            [stay("B_TWIN", "twin")]),
        "expected": "no_solution",
    },
    {
        "id": "unknown-occupancy", "title": "Doluluk doğrulanmadı",
        "description": "Twin odanın fiziksel doluluk sinyali bilinmiyor. Atanmamış oda otomatik olarak boş sayılmaz.",
        "source": source([room("T101", "twin", occupancy="unknown"), room("D102")],
                         [stay("B_TWIN", "twin")]),
        "expected": "manual_review_required",
    },
    {
        "id": "cancelled-hold", "title": "İptal edilen blokaj",
        "description": "İptal edilmiş tutmanın odayı serbest bıraktığı ayrıca doğrulanmamış; personel incelemesi gerekiyor.",
        "source": source(
            [room("T101", "twin"), room("D102")],
            [stay("B_TWIN", "twin")],
            [{"id": "HOLD1", "room_id": "T101", "arrival": DATES[0],
              "departure": "2026-11-19", "status": "cancelled",
              "release_confirmed": False}]),
        "expected": "manual_review_required",
    },
    {
        "id": "overlap", "title": "Aynı oda, çakışan tarihler",
        "description": "İki onaylı rezervasyon aynı günlerde tek double odayı istiyor; kısmi atama önerilmez.",
        "source": source([room("D102")], [stay("A_DOUBLE", "double"), stay("B_DOUBLE", "double")]),
        "expected": "no_solution",
    },
    {
        "id": "checkout", "title": "Çıkış gününde yeni giriş",
        "description": "İki konaklama çakışmıyor: İlk rezervasyonun çıkış günü ikinci rezervasyonun giriş günü.",
        "source": source([room("D102")],
                         [stay("A_DOUBLE", "double"),
                          stay("B_DOUBLE", "double", arrival=DATES[1], departure="2026-11-20")]),
        "expected": "proposed",
    },
)


def authoritative_scenarios(root=ROOT):
    """Recompute proposals; do not import staff or room data from the real hotel."""
    result = []
    for item in SCENARIOS:
        sample = deepcopy(item["source"])
        outcome = propose_group(sample)
        if outcome["status"] != item["expected"]:
            raise ValueError("Unexpected deterministic allocation result")
        if outcome["mode"] != "DRY_RUN_ONLY" or not outcome["human_approval_required"]:
            raise ValueError("Authorization boundary changed")
        if any(outcome["side_effects"].values()):
            raise ValueError("Operational side effect indicated")
        result.append({"id": item["id"], "title": item["title"],
                       "description": item["description"],
                       "source": sample, "report": outcome})
    return result


def _json_for_inline_script(data):
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    # The payload is inserted into a script block; keep it non-terminating
    # even if future safe fixtures contain odd markup-like characters.
    return (encoded.replace("&", "\\u0026").replace("<", "\\u003c")
                   .replace(">", "\\u003e").replace("\u2028", "\\u2028")
                   .replace("\u2029", "\\u2029"))


def allocation_lab_html(root=ROOT):
    root = Path(root)
    scripts = root / "demo" / "allocation-lab.js"
    script = scripts.read_text(encoding="utf-8")
    if "</script" in script.lower() or "fetch(" in script or "XMLHttpRequest" in script:
        raise ValueError("Unsafe inline allocation viewer")
    choices = authoritative_scenarios(root)
    options = "".join(
        f'<option value="{escape(item["id"], quote=True)}">{escape(item["title"])}</option>'
        for item in choices
    )
    return (
        '<!doctype html>\n<html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="referrer" content="no-referrer">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'style-src &#39;unsafe-inline&#39;; script-src &#39;unsafe-inline&#39;; '
        'img-src &#39;none&#39;; connect-src &#39;none&#39;; form-action &#39;none&#39;; '
        'base-uri &#39;none&#39;; object-src &#39;none&#39;; font-src &#39;none&#39;">'
        '<title>KonaklamaFlow | Akıllı Oda Tahsis Merkezi (Kurgusal)</title>'
        '<style>' + STYLE + '</style></head><body>'
        '<main class="layout"><header class="header">'
        '<div class="brand"><span class="mark">K</span><div><strong>KonaklamaFlow</strong>'
        '<span class="sub">Fictional allocation lab · Offline</span></div></div>'
        '<nav aria-label="Geri dönüş bağlantıları"><a href="index.html">← Ana demo</a>'
        '<a href="project-overview.html">Proje tanıtımı</a></nav>'
        '</header>'
        '<section class="hero"><span class="eyebrow">KURGUSAL DEMO • PYTHON HESAPLAMIŞTIR</span>'
        '<h1>Akıllı <em>Oda Tahsis Merkezi</em></h1>'
        '<p>Rezervasyonların yatak talebi, bakım ve çakışma kurallarının oda önerisini '
        'nasıl etkilediğini incele. <strong>Bu ekran gerçek oda atamaz.</strong> '
        'Python sonucu önceden hesaplandı; tarayıcı yalnızca senaryo seçer.</p>'
        '<div class="notice" role="note"><strong>Önemli:</strong> '
        'Bu örneklerdeki oda adları ve “doğrulanmış boş” bilgisi yalnızca '
        'kurgusal veri setine aittir; gerçek otel doluluğu veya müsaitlik göstermez. '
        'Personel onayı hiçbir zaman otomatik verilmez.</div></section>'
        '<section class="work" aria-label="İnteraktif oda tahsis örneği">'
        '<div class="controls">'
        '<label for="scenario">Bir senaryo seç</label>'
        '<select id="scenario" name="scenario">' + options + '</select>'
        '<p id="scenario-description" class="desc"></p>'
        '<div class="buttons">'
        '<button type="button" id="calculate">Önerileri göster</button>'
        '<button type="button" id="explain" class="secondary" hidden '
        'aria-expanded="false" aria-controls="explanation">Kararın nedenlerini göster</button>'
        '<button type="button" id="reset" class="quiet">Sıfırla</button>'
        '</div><p class="hint" id="prompt" aria-live="polite"></p>'
        '</div><div class="inventory"><div class="sectiontitle">'
        '<h2>Kurgusal kaynak veriler</h2><span id="case-count"></span></div>'
        '<h3>Rezervasyonlar</h3><div id="stays" class="tiles"></div>'
        '<h3>Oda adayları</h3><div id="rooms" class="tiles"></div>'
        '<h3>Aktif ya da serbestliği teyit edilmemiş blokaj</h3><div id="holds" class="tiles"></div>'
        '</div></section>'
        '<section id="outcome" class="outcome" aria-labelledby="resulttitle" aria-live="polite" hidden>'
        '<div class="sectiontitle"><h2 id="resulttitle">Python kararının sonucu</h2>'
        '<span id="status" class="status"></span></div>'
        '<p id="status-message"></p><div id="proposal-list" class="tiles"></div>'
        '<p class="hint" id="searched"></p></section>'
        '<section id="explanation" class="explanation" hidden aria-labelledby="explanation-title">'
        '<h2 id="explanation-title">Kararın nedenleri ve kanıt sınırları</h2>'
        '<ol id="reason-codes"></ol><p>Oda kategorisi ve yatak talebi zorunlu '
        'kısıtlardır; hazır/boş bilgisi yalnızca bu kurgusal örnekte belirtilen sinyaldir. '
        'Çıkış günü önceki konaklama aralığına dahil değildir. '
        'Eksik kanıtta veya çakışmada kısmi tahsis yapılmaz.</p></section>'
        '<footer><strong>DRY_RUN_ONLY • HUMAN_APPROVAL_REQUIRED</strong> · '
        'Canlı AI, PMS, OTA, KBS, ödeme, veri aktarımı veya gerçek personel onayı yoktur.'
        ' Bu ekranda hesaplama yapılmaz; Python tarafından doğrulanan önceden oluşturulmuş '
        'sonuçlar gösterilir.</footer></main>'
        '<script>window.ALLOCATION_SCENARIOS=' + _json_for_inline_script(choices) + ';</script>'
        '<script>' + script + '</script></body></html>\n'
    )


STYLE = r"""
:root{color-scheme:dark;font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:#edf6ff;background:#080f21;--ink:#edf6ff;--muted:#b9cbdf;--teal:#9cebd7;--line:#38506e}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(circle at 85% 0%,#234b5b 0%,transparent 38%),#080f21}
.layout{max-width:1160px;margin:auto;padding:0 24px 55px}
.header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;border-bottom:1px solid var(--line);padding:20px 0}
.brand{display:flex;align-items:center;gap:10px}.brand strong{display:block;font-size:18px}.sub{display:block;color:var(--muted);font-size:11px;letter-spacing:.05em}.mark{width:36px;height:36px;border-radius:10px;background:linear-gradient(145deg,#8be7cc,#779de5);display:grid;place-items:center;font-weight:900;color:#11213a}
.header nav{display:flex;gap:18px;flex-wrap:wrap}a{color:#acefe0;text-underline-offset:3px}
.hero{padding:38px 0 27px}.eyebrow{font-size:11px;font-weight:800;letter-spacing:.12em;color:#8fe6c6}.hero h1{font-size:clamp(31px,5vw,56px);margin:10px 0;letter-spacing:-.04em;line-height:1.1}.hero h1 em{font-style:normal;color:var(--teal)}
.hero>p{max-width:780px;color:#d4e3f5;font-size:17px}.notice{border:1px solid #a79264;border-left:4px solid #f0d08b;background:#342d39;color:#f7e6c2;border-radius:12px;max-width:920px;padding:14px 17px;margin-top:21px}
.work{display:grid;grid-template-columns:minmax(280px,.9fr) minmax(0,1.1fr);gap:20px;align-items:start}
.controls,.inventory,.outcome,.explanation{background:#152540;border:1px solid #455f79;border-radius:18px;padding:23px;min-width:0}
.controls{position:sticky;top:16px}.controls label{display:block;font-weight:750;margin-bottom:9px}select{width:100%;min-height:48px;padding:10px 12px;color:#f3ffff;background:#243952;border:1px solid #95aec4;border-radius:10px;font:inherit}
.desc{color:#d1dfee;min-height:3.4em}.buttons{display:flex;gap:9px;flex-wrap:wrap;margin-top:15px}
button{background:#a3f0d9;color:#102640;font:inherit;font-weight:760;border:1px solid #a3f0d9;padding:10px 13px;border-radius:10px;min-height:44px;cursor:pointer}
button.secondary{background:#28486b;color:#f4f9ff;border-color:#a9bdd5}button.quiet{background:transparent;color:#ecf7ff;border-color:#768ca8}
button:hover{filter:brightness(1.12)}button:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #f7ce76;outline-offset:3px}
.sectiontitle{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
h2{font-size:22px;margin:0 0 12px}h3{font-size:14px;color:#f2fbff;margin:16px 0 9px}.sectiontitle span{font-size:12px;color:#a9dcd1}
.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}.tile{background:#1d3453;border:1px solid #4b6484;border-radius:12px;padding:14px;min-width:0}.tile h3{font-size:17px;margin:0 0 3px}.sub{color:#bfd0e5;font-size:12px}
.fields{display:grid;gap:6px;margin:14px 0 0}.field{display:flex;justify-content:space-between;gap:10px;align-items:baseline;font-size:12px}.field dt{color:#bdcee4}.field dd{text-align:right;overflow-wrap:anywhere;margin:0;color:#e5f9ff;font-weight:680}.hold{border-color:#bd996e}.proposal{border-color:#74d5b5}
.outcome,.explanation{margin-top:21px}.status{border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;background:#2a3a5d;color:#f1f7ff}
.status.proposed{background:#1b594a;color:#c7ffea}.status.no_solution{background:#64414a;color:#fff0e8}.status.manual_review_required{background:#625235;color:#fff2c8}
.hint{color:#bfcee2;font-size:12px}.empty{color:#c8d8ed;margin:8px 0}.warning{color:#f2dfb1}
.explanation ol{padding-left:20px}.explanation li{margin:11px 0}.explanation code{color:#b8dbff;overflow-wrap:anywhere}.explanation li p{margin:5px 0;color:#c8dff2}
[hidden]{display:none!important}footer{border-top:1px solid #34506e;margin-top:27px;padding:22px 0;color:#bdcfe4;font-size:12px;line-height:1.8}
@media(max-width:850px){.work{grid-template-columns:1fr}.controls{position:static}.layout{padding:0 16px 36px}}
@media(max-width:520px){.tiles{grid-template-columns:1fr}.controls,.inventory,.outcome,.explanation{padding:16px}.header{align-items:flex-start}.buttons button{flex-grow:1}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the fictional offline allocation lab")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    try:
        html = allocation_lab_html()
        target = args.output or args.check
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != html:
                raise ValueError("Stale allocation lab")
        else:
            if target.exists() or target.is_symlink():
                raise ValueError("Refuse to overwrite allocation lab")
            target.write_text(html, encoding="utf-8")
        return 0
    except (OSError, ValueError, TypeError):
        print("Invalid fictional allocation lab source or output", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
