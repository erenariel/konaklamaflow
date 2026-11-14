"""Capture current offline app screenshots; no decorative mockups or deployment."""
from __future__ import annotations
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/images'

async def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sources = {name: (ROOT / 'demo' / name).read_text(encoding='utf-8')
               for name in ('v04-integrated-preview.html', 'global-presentation-concept.html', 'viewer.html')}
    evidence = {'kind': 'ACTUAL_OFFLINE_BROWSER_SCREENSHOTS',
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_has_uncommitted_changes': bool(subprocess.check_output(
            ['git', 'status', '--porcelain', '--', 'demo/v04-integrated-preview.html',
             'demo/global-presentation-concept.html', 'demo/viewer.html'], cwd=ROOT, text=True).strip()),
        'source_files': {name: sha256(content.encode()).hexdigest() for name, content in sources.items()},
        'requests': [], 'errors': [], 'captures': [], 'fictional': True,
        'live_ai_calls': False, 'pms_writes': False, 'payments': False, 'kbs': False}
    profiles = [
        ('v052-overview-1366.png', 'v04-integrated-preview.html', 1366, 768, 'en', 'light'),
        ('v052-overview-1440.png', 'v04-integrated-preview.html', 1440, 900, 'en', 'light'),
        ('v052-overview-1600.png', 'v04-integrated-preview.html', 1600, 900, 'en', 'light'),
        ('v052-overview-dark.png', 'v04-integrated-preview.html', 1440, 900, 'en', 'dark'),
        ('v052-overview-night.png', 'v04-integrated-preview.html', 1440, 900, 'en', 'night'),
        ('v052-overview-rtl.png', 'v04-integrated-preview.html', 1440, 900, 'ar', 'light'),
        ('v052-mobile.png', 'v04-integrated-preview.html', 390, 844, 'en', 'light'),
        ('v052-global-presentation.png', 'global-presentation-concept.html', 1440, 900, 'en', 'light'),
        ('demo-report.png', 'viewer.html', 1440, 1000, 'tr', 'light'),
        ('social-card.png', 'v04-integrated-preview.html', 1200, 630, 'en', 'light'),
        ('aurora-room-plan-desktop.png', 'v04-integrated-preview.html', 1440, 1000, 'en', 'light'),
        ('aurora-room-plan-mobile.png', 'v04-integrated-preview.html', 390, 1000, 'en', 'light'),
        ('aurora-room-plan-rtl.png', 'v04-integrated-preview.html', 1440, 1000, 'ar', 'dark'),
        ('aurora-room-plan-night.png', 'v04-integrated-preview.html', 1440, 1000, 'en', 'night')]
    async with async_playwright() as driver:
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        browser = await driver.chromium.launch(**options)
        try:
            for filename, source, width, height, locale, theme in profiles:
                page = await browser.new_page(viewport={'width': width, 'height': height}, locale='en', reduced_motion='reduce')
                page.on('request', lambda request: evidence['requests'].append(request.url))
                page.on('pageerror', lambda error: evidence['errors'].append(str(error)))
                await page.set_content(sources[source], wait_until='load')
                if source == 'v04-integrated-preview.html':
                    await page.locator('#globalLanguage').select_option(locale)
                    await page.locator('#kfTheme').select_option(theme)
                    await page.locator('#aiCommandCenter').wait_for(state='visible')
                    if filename.startswith('aurora-room-plan-'):
                        await page.locator('nav [data-nav="rooms"]').click()
                        await page.locator('#auroraRoomPlan').wait_for(state='visible')
                elif source == 'global-presentation-concept.html':
                    await page.locator('#locale').select_option(locale)
                within = await page.evaluate('() => document.documentElement.scrollWidth <= innerWidth')
                if not within:
                    raise RuntimeError('Preview body overflowed its viewport')
                await page.screenshot(path=str(OUTPUT / filename), animations='disabled')
                evidence['captures'].append({'file': filename, 'source': source, 'width': width, 'height': height,
                    'locale': locale, 'theme': theme, 'body_within_viewport': within,
                    'sha256': sha256((OUTPUT / filename).read_bytes()).hexdigest()})
                await page.close()
            if evidence['requests'] or evidence['errors']:
                raise RuntimeError('Preview generation must remain offline and error-free')
            for name, content in sources.items():
                if (ROOT / 'demo' / name).read_text(encoding='utf-8') != content:
                    raise RuntimeError('Preview source changed during capture')
            (OUTPUT / 'v052-previews.json').write_text(json.dumps(evidence, indent=2) + chr(10), encoding='utf-8')
        finally:
            await browser.close()
    print(f'Captured {len(profiles)} actual app screenshots; zero requests and browser errors.')

if __name__ == '__main__':
    asyncio.run(main())
