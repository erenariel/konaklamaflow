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

SHOWCASES = ('ai-command-tour', 'roomplan-story', 'overview-pulse')


def record_showcase(name: str, output: Path) -> dict:
    """Record user-visible interactions in the actual integrated offline app."""
    from playwright.sync_api import sync_playwright
    if name not in SHOWCASES:
        raise ValueError('Unknown showcase')
    encoder = shutil.which('ffmpeg')
    if encoder is None:
        raise RuntimeError('ffmpeg is required')
    source = ROOT / 'demo/v04-integrated-preview.html'
    document = source.read_text(encoding='utf-8')
    options = {'headless': True}
    if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
        options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
    with tempfile.TemporaryDirectory() as directory, sync_playwright() as driver:
        frames = Path(directory)
        browser = driver.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 900},
                                    locale='en', reduced_motion='no-preference')
            errors, requests, observed, events = [], [], set(), []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append(request.url))
            page.set_content(document, wait_until='load')
            page.locator('#globalLanguage').select_option('en')
            canonical = page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)')
            initial_state = page.evaluate('() => JSON.stringify(state)')
            operations = page.evaluate('() => JSON.stringify(HOTEL_OPS_REPORT)')
            output.parent.mkdir(parents=True, exist_ok=True)
            frame = 0

            def capture(delay=350):
                nonlocal frame
                page.wait_for_timeout(delay)
                panel = page.locator('#aiCommandCenter')
                if panel.count():
                    value = page.evaluate('() => storyStarted ? String(storyStep) : "idle"')
                    observed.add(value)
                page.screenshot(path=str(frames / f'frame-{frame:03d}.png'))
                frame += 1
                if errors or requests:
                    raise RuntimeError('Showcase must remain offline and error-free')

            def act(selector, event):
                page.locator(selector).first.click()
                events.append(event)
                for _ in range(3):
                    capture()

            capture(750)
            shutil.copyfile(frames / 'frame-000.png', output.with_name(name + '-poster.png'))
            if name == 'ai-command-tour':
                page.locator('#commandPlay').click()
                events.append('play_actual_scripted_tour')
                # Capture the first complete source→rules→insight→staff story.
                for _ in range(44):
                    capture()
                    if page.evaluate('() => storyStarted && storyStep === 2'):
                        shutil.copyfile(frames / f'frame-{frame-1:03d}.png',
                                        output.with_name(name + '-poster.png'))
                    if page.evaluate('() => storyStarted && storyStep === 4'):
                        page.locator('#commandPause').click()
                        capture()
                        break
                if not {'0', '1', '2', '3', '4'} <= observed:
                    raise RuntimeError('Recording missed a real story phase')
            elif name == 'roomplan-story':
                act('#commandNext', 'reveal_source')
                act('#commandNext', 'reveal_room_evidence')
                act('nav [data-nav="rooms"]', 'open_room_plan')
                capture()
                shutil.copyfile(frames / f'frame-{frame-1:03d}.png',
                                output.with_name(name + '-poster.png'))
                act('.aurora-room-card[data-room="101"]', 'inspect_canonical_room_101')
                page.keyboard.press('Escape')
                capture()
                page.locator('.rack-panel').first.scroll_into_view_if_needed()
                capture()
                act('.rack-row [data-room="303"]', 'inspect_fictional_room_303')
                page.keyboard.press('Escape')
                capture()
                act('[data-timeline-shift="7"]', 'next_week')
                act('[data-timeline-shift="0"]', 'return_to_snapshot_week')
                act('.rack-row [data-room="401"]', 'inspect_technical_hold')
                page.keyboard.press('Escape')
                capture()
            else:
                act('#commandNext', 'show_source_stage')
                act('#commandNext', 'show_constraints_stage')
                act('#commandNext', 'show_engine_stage')
                act('#commandNext', 'show_insight_stage')
                act('#commandNext', 'show_staff_boundary')
                page.locator('#opsSnapshotCharts').scroll_into_view_if_needed()
                for _ in range(4):
                    capture()
                page.locator('#aiCommandCenter').scroll_into_view_if_needed()
                capture()
            while frame < 26:
                capture()
            if (page.evaluate('() => JSON.stringify(INITIAL_EVALUATION)') != canonical
                    or page.evaluate('() => JSON.stringify(state)') != initial_state
                    or page.evaluate('() => JSON.stringify(HOTEL_OPS_REPORT)') != operations):
                raise RuntimeError('A presentation changed canonical source/report data')
            if source.read_text(encoding='utf-8') != document:
                raise RuntimeError('Source changed during the recording')
            subprocess.run([
                encoder, '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '2',
                '-i', str(frames / 'frame-%03d.png'), '-filter_complex',
                '[0:v]scale=1120:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
                '-loop', '0', str(output),
            ], check=True, capture_output=True)
            if output.stat().st_size > 5_000_000:
                raise RuntimeError('Showcase exceeded its 5 MB budget')
            return {
                'kind': 'ACTUAL_INTEGRATED_FICTIONAL_BROWSER_SHOWCASE',
                'profile': name, 'source': 'demo/v04-integrated-preview.html',
                'source_commit': subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'source_has_uncommitted_changes': bool(subprocess.check_output(
                    ['git', 'status', '--porcelain', '--', 'demo/v04-integrated-preview.html'],
                    cwd=ROOT, text=True).strip()),
                'browser_version': browser.version,
                'viewport': {'width': 1440, 'height': 900},
                'html_sha256': sha256(document.encode()).hexdigest(),
                'snapshot_sha256': page.evaluate('() => DEMO_STORIES.snapshot_sha256'),
                'report_sha256': page.evaluate('() => DEMO_STORIES.report_sha256'),
                'gif_sha256': sha256(output.read_bytes()).hexdigest(),
                'poster_sha256': sha256(output.with_name(name + '-poster.png').read_bytes()).hexdigest(),
                'frames': frame, 'fps': 2, 'observed_story_steps': sorted(observed),
                'interactions': events, 'external_requests': len(requests),
                'browser_errors': len(errors), 'canonical_source_unchanged': True,
                'canonical_report_unchanged': True, 'live_ai_calls': False,
                'pms_writes': False, 'payments': False, 'kbs': False,
            }
        finally:
            browser.close()


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
    parser.add_argument('--showcase', choices=(*SHOWCASES, 'all'),
                        help='Record the current integrated app; legacy recording remains available.')
    args = parser.parse_args(argv)
    try:
        names = SHOWCASES if args.showcase == 'all' else (args.showcase,) if args.showcase else ()
        if names:
            for name in names:
                output = args.output.parent / (name + '.gif')
                metadata = record_showcase(name, output)
                output.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
        else:
            metadata = record(args.output)
            args.output.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, ImportError):
        print('Could not record the offline fictional browser tour.', file=sys.stderr)
        return 2
    print('Recorded actual fictional tour; no external requests or live operations.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
