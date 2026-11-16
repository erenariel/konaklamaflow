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
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.render_scorecard import scorecard_html
from scripts.render_trace_view import trace_view_html
PUBLIC_ASSETS = {
    'index.html': 'demo/v04-integrated-preview.html',
    'hotel-operations.html': 'demo/v04-integrated-preview.html',
    'project-overview.html': 'demo/project-overview.html',
    'privacy-vault-lab.html': 'demo/privacy-vault-lab.html',
    'privacy-campaign.html': 'demo/privacy-campaign.html',
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
    'vision-ai-command-core.gif': 'docs/images/vision-ai-command-core.gif',
    'vision-ai-command-core-poster.jpg': 'docs/images/vision-ai-command-core-poster.jpg',
    'vision-smart-room-grid.gif': 'docs/images/vision-smart-room-grid.gif',
    'vision-smart-room-grid-poster.jpg': 'docs/images/vision-smart-room-grid-poster.jpg',
    'vision-executive-intelligence.gif': 'docs/images/vision-executive-intelligence.gif',
    'vision-executive-intelligence-poster.jpg': 'docs/images/vision-executive-intelligence-poster.jpg',
    'privacy-promise.gif': 'docs/images/privacy-promise.gif',
    'privacy-promise-poster.jpg': 'docs/images/privacy-promise-poster.jpg',
    'authorized-device.gif': 'docs/images/authorized-device.gif',
    'authorized-device-poster.jpg': 'docs/images/authorized-device-poster.jpg',
    'zero-access-flow.gif': 'docs/images/zero-access-flow.gif',
    'zero-access-flow-poster.jpg': 'docs/images/zero-access-flow-poster.jpg',
    'future-certification.gif': 'docs/images/future-certification.gif',
    'future-certification-poster.jpg': 'docs/images/future-certification-poster.jpg',
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


# Download only actual fictional program screens and their local media.
# Future-vault research, concept galleries, certification artwork and operator
# assessment PDFs are deliberately excluded from this end-user bundle.
DOWNLOAD_BUNDLE = "konaklamaflow-offline-demo.zip"
PRODUCT_BUNDLE_ASSETS = frozenset({
    "index.html", "hotel-operations.html", "project-overview.html",
    "v04-integrated-preview.html", "global-presentation.html",
    "hotel-suite.html", "reviewer.html", "viewer.html", "operations.html",
    "demo-report.png", "social-card.png", "operations-tour.gif",
    "ai-command-tour.gif", "roomplan-story.gif", "overview-pulse.gif",
    "ai-command-tour-poster.png", "roomplan-story-poster.png",
    "overview-pulse-poster.png", "desktop-preview.png", "mobile-preview.png",
})
OFFLINE_GUIDE = """# KonaklamaFlow — offline fictional software demo

1. Extract this ZIP to an empty directory.
2. Open index.html in a current desktop or mobile browser.
3. Explore reservations, room plans, channel mismatch reviews and
   staff approval boundaries using the included fictional records.

This is an offline product demonstration, not a deployed hotel PMS.
No live OTA, PMS, KBS, payment or AI-provider integration is included.
No guest check-in or room assignment is performed.
Do not enter genuine guest information or operational credentials.
Links to GitHub may need an internet connection, but the included demo
screens and synthetic reports are local.

Bu paket yalnızca kurgusal otel verileriyle çalışan yazılım demosudur.
Gerçek misafir kimliği, ödeme veya otel şifresi girme. Değerlendirme,
sertifikasyon ya da gerçek otel kurulumunun kanıtı değildir.
"""


# A downloaded ZIP cannot link to itself. Remove the online-only download
# control from the four HTML pages inside the archive (not from the site).
OFFLINE_DOWNLOAD_ANCHOR = {
    "project-overview.html":
        '<a class="cta ghost" href="konaklamaflow-offline-demo.zip" download>Çevrimdışı demoyu indir (ZIP)</a>',
    "index.html":
        '<a href="konaklamaflow-offline-demo.zip" download aria-label="Kurgusal otel programını çevrimdışı indir">Çevrimdışı demoyu indir (ZIP)</a>',
    "hotel-operations.html":
        '<a href="konaklamaflow-offline-demo.zip" download aria-label="Kurgusal otel programını çevrimdışı indir">Çevrimdışı demoyu indir (ZIP)</a>',
    "v04-integrated-preview.html":
        '<a href="konaklamaflow-offline-demo.zip" download aria-label="Kurgusal otel programını çevrimdışı indir">Çevrimdışı demoyu indir (ZIP)</a>',
}


def offline_bundle_asset(name: str, source: bytes) -> bytes:
    """Remove dead self-download actions in extracted product pages."""
    link = OFFLINE_DOWNLOAD_ANCHOR.get(name)
    if link is None:
        return source
    needle = link.encode("utf-8")
    if source.count(needle) != 1:
        raise ValueError("Offline product page download CTA changed")
    return source.replace(needle, b"")



def write_offline_demo_bundle(output: Path) -> None:
    """Deterministic allowlisted product-only ZIP; no repository traversal."""
    if not PRODUCT_BUNDLE_ASSETS <= set(PUBLIC_ASSETS):
        raise ValueError("Unreviewed offline demo asset")
    filenames = sorted(PRODUCT_BUNDLE_ASSETS | set(GENERATED_ASSETS))
    with ZipFile(output / DOWNLOAD_BUNDLE, "w", compression=ZIP_DEFLATED) as archive:
        for name in filenames:
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_STORED if name.endswith((".png", ".jpg", ".gif")) else ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, offline_bundle_asset(name, (output / name).read_bytes()))
        info = ZipInfo("README_OFFLINE.md", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, OFFLINE_GUIDE.encode("utf-8"))


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
    write_offline_demo_bundle(output)


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
