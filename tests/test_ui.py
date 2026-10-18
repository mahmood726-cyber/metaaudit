"""Browser contract for the builder, using the already-shipped data snapshot.

Run explicitly with RUN_BROWSER_TESTS=1 and Playwright Chromium installed.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.environ.get('RUN_BROWSER_TESTS') != '1',
                    reason='opt-in browser contract: RUN_BROWSER_TESTS=1')
def test_generated_dashboard_loads_and_filters(tmp_path):
    from playwright.sync_api import sync_playwright

    # Reuse the committed snapshot, with its identifiers and numeric values
    # unchanged. This verifies rendering, not the research claims themselves.
    shipped = (ROOT / 'dashboard' / 'index.html').read_text(encoding='utf-8')
    payload, _ = json.JSONDecoder().raw_decode(shipped.split('const DATA = ', 1)[1])
    source = tmp_path / 'dashboard_data.json'
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'index.html'
    subprocess.run([sys.executable, str(ROOT / 'build_dashboard.py'),
                    '--data', str(source), '--template',
                    str(ROOT / 'dashboard' / 'index.template.html'),
                    '--output', str(output)], cwd=tmp_path, check=True, timeout=30)
    handler = partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(('127.0.0.1', 8000), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto('http://127.0.0.1:8000/index.html', wait_until='load')
                page.locator('#hero-grid .hero-card').first.wait_for(timeout=10000)
                assert page.title().startswith('MetaAudit')
                page.get_by_role('button', name='Review Explorer', exact=True).click()
                page.locator('#tbl-body tr').first.wait_for(timeout=10000)
                assert page.locator('#tbl-body tr').count() > 0
                page.locator('#tbl-search').fill('__no_review_matches_this_fixture__')
                page.wait_for_function("document.getElementById('tbl-info').textContent.includes('0')")
                assert page.locator('#tbl-body tr').count() <= 1
                page.get_by_role('button', name='About', exact=True).click()
                assert page.locator('#view-3').is_visible()
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
