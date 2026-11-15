"""Fail-closed checks for the staged fictional Pages release candidate.

This is a *preflight check*, not a deployer. It never accesses GitHub, a
hotel system, guest records or any third-party website.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import urlsplit

from scripts.stage_demo_site import ROOT, PUBLIC_ASSETS, GENERATED_ASSETS

EXPECTED_INTERNAL_PAGES = frozenset({
    "index.html", "project-overview.html", "synthetic-scorecard.html",
    "fictional-trace.html",
    "privacy-vault-lab.html",
})
_REQUIRED_OVERVIEW_COPY = (
    "Geliştirme durumunu açıkça ayırıyoruz:",
    "birleşik sürüm adayında",
    "7 / 10",
    "PR #65",
    "PR #67",
    "Gerçek otel",
    "English summary",
    "Future Intelligence Vision",
    "Zero-Access Hotel Vault",
    "Concept art only",
    "gerçek tarayıcı ekran kayıtlarıdır",
)
_STALE_COPY = (
    "henüz ana sürüme birleştirilmediler",
    "14 Kasım 2026 durum özeti",
    "unmerged review candidates",
    "PR #51 · İnceleme adayı",
)


class ReleaseReadinessError(ValueError):
    """Do not publish on a failed release-readiness check."""


def _require(condition: bool, reason: str):
    if not condition:
        raise ReleaseReadinessError(reason)


class _OverviewLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.internal = set()
        self.local_images = set()
        self.external = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag not in ("a", "img", "source"):
            return
        value = attributes.get(
            "href" if tag == "a" else "src" if tag == "img" else "srcset", "")
        _require(type(value) is str and value != "", "Overview link/image missing URL")
        url = urlsplit(value)
        if url.scheme or url.netloc:
            _require(
                tag == "a" and url.scheme == "https"
                and url.hostname == "github.com" and url.port in (None, 443)
                and url.path.startswith("/erenariel/konaklamaflow"),
                "Unexpected remote asset or link",
            )
            self.external.add(value)
            return
        if url.path == "" and url.fragment:
            return  # accessible in-page jump
        path = PurePosixPath(url.path)
        _require(
            url.path != "" and not url.path.startswith("/")
            and all(piece not in (".", "..") for piece in url.path.split("/"))
            and len(path.parts) == 1,
            "Unexpected local path in overview",
        )
        if tag == "img":
            _require(
                bool(attributes.get("alt")) and not url.fragment,
                "Overview image missing alt text",
            )
            self.local_images.add(url.path)
        elif tag == "source":
            # Accept only a single local still poster for reduced-motion mode.
            _require(attributes.get("media") == "(prefers-reduced-motion: reduce)",
                     "Unexpected picture source media")
            _require(url.path.endswith((".png", ".jpg")),
                     "Reduced-motion source must be a local still image")
            self.local_images.add(url.path)
        else:
            self.internal.add(url.path)


def verify_overview_content(html: str, staged_files):
    """Validate public copy and navigation before any Pages release."""
    _require(type(html) is str and bool(html), "Missing overview HTML")
    for phrase in _REQUIRED_OVERVIEW_COPY:
        _require(phrase in html, "Overview release description incomplete")
    for phrase in _STALE_COPY:
        _require(phrase not in html, "Outdated PR/deployment claim")
    _require("<script" not in html.lower(), "Active script in overview")
    _require("connect-src 'none'" in html, "Network-restricted CSP missing")
    parser = _OverviewLinks()
    parser.feed(html)
    _require({"index.html"} <= parser.internal,
             "Published demo not linked from overview")
    _require("ai-command-tour-poster.png" in parser.local_images,
             "Historical demo screenshot missing")
    for name in ("vision-ai-command-core.gif", "vision-smart-room-grid.gif",
                 "vision-executive-intelligence.gif"):
        _require(name in parser.local_images, "Vision concept GIF missing")
    for name in ("vision-ai-command-core-poster.jpg", "vision-smart-room-grid-poster.jpg",
                 "vision-executive-intelligence-poster.jpg"):
        _require(name in parser.local_images, "Reduced-motion vision poster missing")
    for name in ("ai-command-tour.gif", "roomplan-story.gif", "overview-pulse.gif"):
        _require(name in parser.local_images, "Real-demo GIF missing")
    _require((parser.internal | parser.local_images) <= set(staged_files),
             "Broken local overview reference")
    _require(EXPECTED_INTERNAL_PAGES <= set(staged_files),
             "Missing required release pages")
    return {
        "internal_links": len(parser.internal),
        "local_images": len(parser.local_images),
    }


def verify_staged_site(site: Path, root: Path = ROOT):
    site = Path(site)
    root = Path(root)
    _require(site.is_dir() and not site.is_symlink(), "Staging directory absent or unsafe")
    expected = set(PUBLIC_ASSETS) | set(GENERATED_ASSETS) | {".nojekyll"}
    present = {path.name for path in site.iterdir()}
    _require(present == expected, "Unexpected, private or missing staged assets")
    for name in expected:
        target = site / name
        _require(target.is_file() and not target.is_symlink(),
                 "Unsafe directory or symlink in public output")
    for destination, source in PUBLIC_ASSETS.items():
        # Byte-compare HTML; media are already restricted to the stage allowlist.
        if destination.endswith(".html"):
            _require(
                (site / destination).read_bytes() == (root / source).read_bytes(),
                "Staged static page differs from reviewed source",
            )
    for destination, builder in GENERATED_ASSETS.items():
        _require(
            (site / destination).read_text(encoding="utf-8") == builder(root),
            "Source-derived report mismatch",
        )
    _require((site / ".nojekyll").read_bytes() == b"",
             "Unexpected Pages metadata")
    overview = (site / "project-overview.html").read_text(encoding="utf-8")
    link_info = verify_overview_content(overview, present)
    home = (site / "index.html").read_text(encoding="utf-8")
    for name in EXPECTED_INTERNAL_PAGES - {"index.html"}:
        _require(f'href="{name}"' in home, "Integrated demo missing navigation link")
    _require("BEGIN GENERATED_DECISION_EVIDENCE_UI" in home,
             "Source-bound evidence panel missing")
    return {"staged_files": len(expected), **link_info}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path,
                        help="Previously staged offline site to inspect; does not deploy")
    args = parser.parse_args(argv)
    try:
        result = verify_staged_site(args.site)
    except (ReleaseReadinessError, OSError, UnicodeError, ValueError):
        print("Offline release candidate preflight failed", file=sys.stderr)
        return 2
    print(f"Offline fictional release preflight passed: {result['staged_files']} staged files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
