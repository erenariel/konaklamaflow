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

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ASSETS = {
    'index.html': 'demo/v04-integrated-preview.html',
    'hotel-operations.html': 'demo/v04-integrated-preview.html',
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
    (output / '.nojekyll').write_text('', encoding='utf-8')


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
