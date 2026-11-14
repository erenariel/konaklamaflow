#!/usr/bin/env python3
"""Capture and verify the offline demo's visual preferences in real Chromium.

This bounded audit measures representative text on solid/alpha backgrounds.
It is not a WCAG certification, assistive-technology audit, or pixel-baseline
regression suite. Files are written only to an explicitly chosen new directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
THEMES = ('light', 'dark', 'night')
MODES = ('operator', 'presentation')
WIDTHS = (320, 375, 768, 1440)
TEXT_SELECTORS = (
    '#pagetitle', '#pagesub', '#startShowcase', '#resetButton',
    '.kf-prefs label', '#kfTheme', '#kfMode', '#kfMotion', '#kfModule',
    '.metric strong', '.copilot-heading h2', '.copilot-disclaimer',
    '.story-label', '.story-select', '.story-booking b',
    '.story-evidence h3', '.story-evidence p', '.tour-status',
)

# Browser-computed text and alpha-composited background, rather than a hardcoded
# expectation for theme colors. Gradients/images are explicitly left unmeasured.
CONTRAST_JS = r'''(selectors) => {
 const channels = value => (value.match(/[\d.]+/g) || []).map(Number);
 const blend = (foreground, background) => {
  const alpha = foreground.length < 4 ? 1 : foreground[3];
  return background.map((component, index) =>
   foreground[index] * alpha + component * (1 - alpha));
 };
 const luminance = rgb => rgb.slice(0,3).map(channel => {
  const c = channel / 255;
  return c <= .04045 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4);
 }).reduce((sum, value, index) => sum + value * [.2126,.7152,.0722][index], 0);
 const rows = [];
 for (const selector of selectors) {
  for (const element of document.querySelectorAll(selector)) {
   const style = getComputedStyle(element), rect = element.getBoundingClientRect();
   if (!rect.width || !rect.height || style.visibility !== 'visible' ||
       element.closest('[disabled]')) continue;
   let layers = [], complex = false;
   for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
    const layer = getComputedStyle(ancestor);
    if (layer.backgroundImage !== 'none') complex = true;
    const rgba = channels(layer.backgroundColor);
    layers.push(rgba);
    if (rgba.length === 3 || rgba[3] === 1) break;
   }
   const background = layers.reverse().reduce((color, layer) => blend(layer,color), [255,255,255]);
   const foreground = blend(channels(style.color), background);
   const a=luminance(foreground), b=luminance(background);
   const ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
   const size=Number.parseFloat(style.fontSize), weight=Number.parseInt(style.fontWeight);
   const minimum=(size >= 24 || (size >= 18.6667 && weight >= 700)) ? 3 : 4.5;
   rows.push({selector, ratio, minimum, measured:!complex,
    pass:complex ? null : ratio >= minimum,
    font_size_px:size, foreground, background,
    limitation:complex ? 'Background image/gradient requires separate review' : null});
  }
 }
 return rows;
}'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure_text_contrast(page) -> list[dict]:
    return page.evaluate(CONTRAST_JS, TEXT_SELECTORS)


def audit(output: Path) -> dict:
    from playwright.sync_api import expect, sync_playwright

    # Do not accidentally mix captures from different HTML revisions.
    output.mkdir(parents=True, exist_ok=False)
    html = ROOT / 'demo/hotel-suite.html'
    source = html.read_text(encoding='utf-8')
    report = json.loads((ROOT / 'examples/canonical-review-report.json').read_text())
    result = {
        'schema_version': 'konaklamaflow.visual-experience.v1',
        'html_sha256': digest(html),
        'canonical_file_sha256': digest(ROOT / 'examples/canonical-hotel.json'),
        'snapshot_file_sha256': digest(ROOT / 'examples/canonical-review.json'),
        'report_file_sha256': digest(ROOT / 'examples/canonical-review-report.json'),
        'source_commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_has_uncommitted_changes': bool(subprocess.check_output(
            ['git', 'status', '--porcelain', '--', 'demo/hotel-suite.html'],
            cwd=ROOT, text=True).strip()),
        'data_kind': 'fictional', 'records': [], 'browser_errors': [],
        'network_requests': [], 'checks': {},
        'limitations': [
            'Representative solid-background text contrast; not a full WCAG audit.',
            'Screenshot capture evidence; no approved pixel-baseline comparison.',
            'CSS zoom/reflow exercised; manual screen-reader review remains separate.',
        ],
    }
    with sync_playwright() as driver:
        options = {'headless': True}
        if os.environ.get('KONAKLAMAFLOW_CHROMIUM'):
            options['executable_path'] = os.environ['KONAKLAMAFLOW_CHROMIUM']
        browser = driver.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.on('pageerror', lambda error: result['browser_errors'].append(str(error)))
        page.on('request', lambda request: result['network_requests'].append(request.url))
        page.set_content(source)
        snapshot_before = page.evaluate('() => JSON.stringify(INITIAL_DATA)')
        evaluation_before = page.evaluate('() => INITIAL_EVALUATION')
        assert evaluation_before == report, 'Browser report must match authoritative Python output'
        for theme in THEMES:
            page.locator('#kfTheme').select_option(theme)
            for mode in MODES:
                if page.locator('html').get_attribute('data-kf-mode') != mode:
                    page.locator('#kfMode').click()
                for width in WIDTHS:
                    page.set_viewport_size({'width': width, 'height': 900})
                    expect(page.locator('html')).to_have_attribute('data-kf-theme', theme)
                    expect(page.locator('html')).to_have_attribute('data-kf-mode', mode)
                    filename = f'{theme}-{mode}-{width}.png'
                    page.screenshot(path=str(output / filename), full_page=True, animations='disabled')
                    rows = measure_text_contrast(page)
                    result['records'].append({
                        'theme': theme, 'mode': mode, 'width': width,
                        'body_within_viewport': page.evaluate(
                            '() => document.documentElement.scrollWidth <= innerWidth'),
                        'screenshot': filename, 'screenshot_sha256': digest(output / filename),
                        'text_contrast': rows,
                    })
        page.set_viewport_size({'width': 1440, 'height': 900})
        stage = page.locator('#content').bounding_box()
        result['checks']['presentation_stage_16_by_9'] = (
            abs(stage['width'] / stage['height'] - 16 / 9) < .005)
        result['checks']['presentation_module_navigation_available'] = page.locator('#kfModule').is_visible()
        page.locator('#kfModule').focus()
        page.keyboard.press('Home')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        result['checks']['presentation_navigation_keyboard'] = (
            page.locator('#kfModule').input_value() == 'arrivals')
        page.locator('#kfModule').select_option('dashboard')
        page.evaluate("() => { document.body.style.zoom = '2'; }")
        result['checks']['zoom_200_percent_body_within_viewport'] = page.evaluate(
            '() => document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(output / 'night-presentation-zoom-200.png'), full_page=True,
                        animations='disabled')
        page.evaluate("() => { document.body.style.zoom = ''; }")
        page.locator('#kfMode').click()
        page.locator('nav [data-nav="arrivals"]').press('Enter')
        opener = page.locator('[data-booking="KF1003"]').first
        opener.press('Enter')
        expect(page.locator('#closeDrawer')).to_be_focused()
        page.keyboard.press('Shift+Tab')
        result['checks']['dialog_focus_trap'] = page.locator('#queueReview').evaluate(
            '(element) => element === document.activeElement')
        page.keyboard.press('Escape')
        result['checks']['dialog_returns_focus'] = opener.evaluate(
            '(element) => element === document.activeElement')
        result['checks']['background_unlocked_after_escape'] = page.locator('.app').evaluate(
            '(element) => !element.inert')
        page.locator('nav [data-nav="dashboard"]').click()
        page.emulate_media(reduced_motion='reduce')
        expect(page.locator('html')).to_have_attribute('data-kf-motion', 'off')
        expect(page.locator('#kfMotion')).to_be_disabled()
        page.locator('#startShowcase').click()
        expect(page.locator('#tourPanel')).to_have_attribute('data-playing', 'false')
        before = page.locator('#tourPanel').get_attribute('data-current-step')
        page.wait_for_timeout(2300)
        result['checks']['reduced_motion_manual_step_only'] = (
            page.locator('#tourPanel').get_attribute('data-current-step') == before)
        result['checks']['source_data_unchanged'] = (
            page.evaluate('() => JSON.stringify(INITIAL_DATA)') == snapshot_before)
        result['checks']['authoritative_report_unchanged'] = (
            page.evaluate('() => INITIAL_EVALUATION') == evaluation_before)
        result['checks']['report_fresh'] = not page.evaluate('() => reportStale')
        result['checks']['export_preserved'] = not page.locator('#exportButton').is_disabled()
        result['checks']['live_side_effects_disabled'] = not any(
            report['approval_policy'][name] for name in ('pms_writes', 'payments', 'kbs'))
        browser.close()
    result['checks']['body_bounds_matrix'] = all(r['body_within_viewport'] for r in result['records'])
    result['checks']['representative_text_contrast'] = all(
        row['pass'] for record in result['records']
        for row in record['text_contrast'] if row['measured'])
    result['checks']['zero_network_requests'] = not result['network_requests']
    result['checks']['zero_browser_errors'] = not result['browser_errors']
    result['passed'] = all(result['checks'].values())
    (output / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New destination directory (must not exist).')
    args = parser.parse_args()
    result = audit(args.output)
    print(json.dumps({'passed': result['passed'], 'screenshots': len(result['records']) + 1,
                      'checks': result['checks'], 'manifest': str(args.output / 'manifest.json')},
                     ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
