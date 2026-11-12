"""Record the actual fictional browser tour as a small GIF for the README.

Requires the optional Playwright extra, Chromium and ffmpeg. No AI service,
private source, external page or manually painted fake application frame is used.
The screenshot/video generation is development tooling, not a runtime dependency.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def record(output: Path) -> dict:
    from playwright.sync_api import sync_playwright
    encoder = shutil.which('ffmpeg')
    if encoder is None:
        raise RuntimeError('ffmpeg is required')
    document = (ROOT / 'demo/hotel-suite.html').read_text(encoding='utf-8')
    options = {'headless': True}
    if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
        options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
    with tempfile.TemporaryDirectory() as directory, sync_playwright() as playwright:
        frames = Path(directory)
        browser = playwright.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 920}, device_scale_factor=1,
                                    reduced_motion='no-preference')
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append(request.url))
            page.set_content(document, wait_until='load')
            page.locator('#tourPlay').wait_for(state='visible')
            page.screenshot(path=str(frames/'frame-000.png'), animations='disabled')
            page.locator('#tourPlay').click()
            observed_steps = set()
            for frame in range(1, 49):
                page.wait_for_timeout(450)
                observed_steps.add(page.locator('#tourPanel').get_attribute('data-current-step'))
                page.screenshot(path=str(frames/f'frame-{frame:03d}.png'))
                if errors or requests:
                    raise RuntimeError('The offline tour made a request or raised a browser error')
                if page.locator('#tourPanel').get_attribute('data-playing') == 'false' and page.locator('#tourNext').is_disabled():
                    # A timer may advance during screenshot encoding. Capture
                    # the settled final phase explicitly before stopping.
                    frame += 1
                    observed_steps.add(page.locator('#tourPanel').get_attribute('data-current-step'))
                    page.screenshot(path=str(frames/f'frame-{frame:03d}.png'))
                    break
            expected_steps = page.evaluate("() => DEMO_STORIES.stories.find(s => s.id === document.getElementById('tourPanel').dataset.storyId).steps.length")
            if observed_steps != {str(i) for i in range(expected_steps)}:
                raise RuntimeError(f'Tour recording steps {sorted(observed_steps)} do not cover {expected_steps} phases')
            for _ in range(3):
                frame += 1
                page.wait_for_timeout(450)
                page.screenshot(path=str(frames/f'frame-{frame:03d}.png'))
            if errors or requests:
                raise RuntimeError('The offline preview failed')
            report_hash = page.evaluate('() => DEMO_STORIES.report_sha256')
            snapshot_hash = page.evaluate('() => DEMO_STORIES.snapshot_sha256')
            story_id = page.locator('#tourPanel').get_attribute('data-story-id')
            count = len(list(frames.glob('frame-*.png')))
            output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([
                encoder, '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '20/9',
                '-i', str(frames/'frame-%03d.png'), '-filter_complex',
                '[0:v]scale=1120:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
                '-loop', '0', str(output),
            ], check=True, capture_output=True)
            if output.stat().st_size > 5_000_000:
                raise RuntimeError('Recorded preview exceeded the 5 MB budget')
            return {'kind': 'ACTUAL_FICTIONAL_BROWSER_TOUR', 'story_id': story_id,
                    'html_sha256': sha256(document.encode()).hexdigest(),
                    'snapshot_sha256': snapshot_hash, 'report_sha256': report_hash,
                    'gif_sha256': sha256(output.read_bytes()).hexdigest(),
                    'frames': count, 'observed_steps': sorted(observed_steps),
                    'external_requests': len(requests), 'browser_errors': len(errors),
                    'live_ai_calls': False, 'pms_writes': False, 'payments': False, 'kbs': False}
        finally:
            browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'docs/images/operations-tour.gif')
    args = parser.parse_args(argv)
    try:
        metadata = record(args.output)
        args.output.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, ImportError):
        print('Could not record the offline fictional browser tour.', file=sys.stderr)
        return 2
    print('Recorded actual fictional tour; no external requests or live operations.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
