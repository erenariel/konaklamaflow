"""Capture fictional report and share previews with the optional browser extra.

Run from any directory: python scripts/capture_previews.py
Set KONAKLAMAFLOW_CHROMIUM to use a locally installed Chromium executable.
"""
import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/images'


async def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        browser = await playwright.chromium.launch(**options)
        page = await browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        requests, errors = [], []
        page.on('request', lambda request: requests.append(request.url))
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.set_content((ROOT / 'demo/viewer.html').read_text(encoding='utf-8'))
        await page.locator('.report-shell').screenshot(path=str(OUTPUT / 'demo-report.png'))
        brand = await page.locator('.brand-mark').evaluate('node => node.outerHTML')
        art = await page.locator('.hotel-art').evaluate('node => node.outerHTML')
        # These are static, repository-owned SVGs, never selected report content.
        card = '''<!doctype html><html lang="en"><meta charset="utf-8"><style>
        *{box-sizing:border-box}body{margin:0;width:1200px;height:630px;background:#f5f2eb;color:#203d35;font-family:Arial,sans-serif;padding:49px 58px}
        header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #d8ddd0;padding-bottom:25px}.brand{display:flex;gap:12px;align-items:center;font-size:27px;letter-spacing:-1px;font-weight:700}.brand span{font-weight:400}.brand svg{width:37px;height:43px}.tag{font-size:11px;letter-spacing:1.8px;color:#5e7058}
        main{display:grid;grid-template-columns:1.6fr 1fr;gap:32px;align-items:center;padding:32px 0 29px}.eyebrow{font-size:11px;letter-spacing:1.7px;color:#637457;margin-bottom:18px}h1{font-family:Georgia,serif;font-size:61px;line-height:1.08;font-weight:400;letter-spacing:-2px;margin:0 0 20px}h1 em{color:#728369;font-weight:400}p{font-size:18px;line-height:1.55;color:#63715f;margin:0}.art{height:329px;border-radius:180px 180px 10px 10px;overflow:hidden;background:#e8e9df}.art svg{width:100%;height:100%}
        footer{border-top:1px solid #d8ddd0;padding-top:22px;display:flex;align-items:center;justify-content:space-between}.url{font-size:14px;color:#50664a}.labels{display:flex;gap:9px}.labels span{border:1px solid #d2dcc9;border-radius:4px;padding:7px 10px;font-size:10px;color:#50664a}.labels .demo{background:#163e37;color:#fffdf4;border-color:#163e37}
        </style><header><div class="brand">BRAND<div>Konaklama<span>Flow</span></div></div><div class="tag">THOUGHTFUL TOOLS FOR INDEPENDENT HOTELS</div></header>
        <main><div><div class="eyebrow">OPEN SOURCE. PRIVACY FIRST.</div><h1>A calmer front desk.<br><em>Clearer decisions.</em></h1><p>Offline reservation review.<br>Built for small &amp; boutique hotels.</p></div><div class="art">ART</div></main>
        <footer><div class="url">erenariel.github.io/konaklamaflow</div><div class="labels"><span>MIT LICENSE</span><span class="demo">EXPLORE THE FICTIONAL DEMO</span></div></footer></html>'''
        await page.set_viewport_size({'width': 1200, 'height': 630})
        await page.set_content(card.replace('BRAND', brand).replace('ART', art))
        await page.screenshot(path=str(OUTPUT / 'social-card.png'))
        assert not requests, 'Preview generation must not access the network'
        assert not errors, errors
        await browser.close()
        print('Captured fictional report and 1200x630 share card; no network requests.')


if __name__ == '__main__':
    asyncio.run(main())
