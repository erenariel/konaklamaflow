"""Stage only the reviewed fictional demo assets; never an entire checkout.

The integrated multilingual hotel workbench is the entry page. Earlier viewers keep dedicated
URLs. A nonempty/preexisting output is refused to prevent accidental publication
of leftover files, private reports or Git metadata. This does not deploy a site.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.render_scorecard import scorecard_html
from scripts.render_trace_view import trace_view_html
PUBLIC_ASSETS = {
    'index.html': 'demo/v04-integrated-preview.html',
    'hotel-operations.html': 'demo/v04-integrated-preview.html',
    'project-overview.html': 'demo/project-overview.html',
    'v04-integrated-preview.html': 'demo/v04-integrated-preview.html',
    'global-presentation.html': 'demo/global-presentation-concept.html',
    'hotel-suite.html': 'demo/hotel-suite.html',
    'reviewer.html': 'demo/viewer.html',
    'viewer.html': 'demo/viewer.html',
    'operations.html': 'demo/operations.html',
    'demo-report.png': 'docs/images/demo-report.png',
    'social-card.png': 'docs/images/social-card.png',
    'operations-tour.gif': 'docs/images/operations-tour.gif',
    'ai-command-tour.gif': 'docs/images/ai-command-tour.gif',
    'roomplan-story.gif': 'docs/images/roomplan-story.gif',
    'overview-pulse.gif': 'docs/images/overview-pulse.gif',
    'ai-command-tour-poster.png': 'docs/images/ai-command-tour-poster.png',
    'roomplan-story-poster.png': 'docs/images/roomplan-story-poster.png',
    'overview-pulse-poster.png': 'docs/images/overview-pulse-poster.png',
    'desktop-preview.png': 'demo/desktop-preview.png',
    'mobile-preview.png': 'demo/mobile-preview.png',
}

# Build only offline, source-verified fictional pages. No private output is copied.
GENERATED_ASSETS = {
    'synthetic-scorecard.html': scorecard_html,
    'fictional-trace.html': trace_view_html,
}



DOWNLOAD_BUNDLE = 'konaklamaflow-offline-evaluation.zip'
OPERATOR_FEEDBACK_TEMPLATE = """# KonaklamaFlow — çevrimdışı operatör değerlendirmesi / offline operator test

Bu paket yalnızca kurgusal otel verileri içerir. Gerçek PMS, OTA, KBS, ödeme
sistemleri veya canlı bir yapay zekâ modeline bağlanmaz. index.html dosyasını
bir tarayıcıda aç; internet bağlantısı gerekli değildir.

Dikkat: Bu formu doldurmak gerçek bir denetimin yerini tutmaz. Gözlem
yapılmadan 'denetlendi', 'bağımsız test edildi' veya 'otelde kullanıldı' yazma.

Değerlendiren: [gerçek ad veya onaylı anonim rol]
İlişki: [proje sahibi / projeye katılmamış otel çalışanı / diğer]
Test tarihi ve saati: [gerçek tarih]
Ortam ve tarayıcı: [gerçek cihaz/tarayıcı]
İncelenen sürüm: [GitHub commit veya paket sürümü]
Test durumu: YAPILMADI (gözlem tamamlanınca değiştir)

Senaryo 1 — Rezervasyon çakışması:
Beklenen: kurgusal rezervasyon ve dayanağı gösterilsin.
Gözlenen: [yalnızca gerçekten görülen]
Sonuç: [geçti / geçmedi / denenmedi]

Senaryo 2 — Oda planı ve oda blokajları:
Beklenen: teklif edilen oda ile fiilen doğrulanmış doluluk ayrışsın.
Gözlenen: [yalnızca gerçekten görülen]
Sonuç: [geçti / geçmedi / denenmedi]

Senaryo 3 — Vardiya devri ve personel onayı:
Beklenen: otomatik karar yerine doğrulama ihtiyacı görülsün.
Gözlenen: [yalnızca gerçekten görülen]
Sonuç: [geçti / geçmedi / denenmedi]

Senaryo 4 — Dil ve erişilebilirlik:
Beklenen: dil geçişi çalışsın; eksik çeviriler not edilsin.
Gözlenen: [yalnızca gerçekten görülen]
Sonuç: [geçti / geçmedi / denenmedi]

En önemli gerçek bulgu / gelişim önerisi: [doldur]
Kanıt: [kişisel bilgi içermeyen isteğe bağlı ekran görüntüsü veya issue]
Yayın izni: [verildi / verilmedi / sorulmadı]

Bağımsız değerlendirme yalnızca projeyi geliştirmemiş bir katılımcının
gerçekten yaptığı test için kullanılabilir. Proje sahibinin testi,
birinci taraf / maintainer self-assessment olarak kaydedilmelidir.

Never upload real guest/employee identifiers, PMS exports, credentials,
private rates, passport details, hotel logs or payment records.
"""


def write_offline_evaluation_bundle(output: Path) -> None:
    """Build a deterministic, allowlisted ZIP from staged fictional public assets."""
    members = sorted(set(PUBLIC_ASSETS) | set(GENERATED_ASSETS))
    with ZipFile(output / DOWNLOAD_BUNDLE, 'w', compression=ZIP_DEFLATED) as archive:
        for filename in members:
            info = ZipInfo(filename, date_time=(2026, 11, 15, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (output / filename).read_bytes())
        info = ZipInfo('OPERATOR_FEEDBACK_TEMPLATE.md', date_time=(2026, 11, 15, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, OPERATOR_FEEDBACK_TEMPLATE.encode('utf-8'))


def stage_site(output: Path, root: Path = ROOT) -> None:
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists')
    for relative in PUBLIC_ASSETS.values():
        source = root / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError('Missing reviewed public asset')
    output.mkdir(parents=True)
    for destination, relative in PUBLIC_ASSETS.items():
        shutil.copyfile(root / relative, output / destination)
    for destination, render in GENERATED_ASSETS.items():
        (output / destination).write_text(render(root), encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    write_offline_evaluation_bundle(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        stage_site(args.output)
    except (OSError, ValueError):
        print('Demo staging rejected: reviewed assets and a new output directory are required.', file=sys.stderr)
        return 2
    print('Fictional integrated hotel workbench staged with global presentation and legacy viewers.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
