"""Exercise WI-04 in an isolated workspace with synthetic model packages.

Requires Playwright and a built frontend. Fixtures must be v1 compatible ZIPs;
these checks establish model management, never lab prediction quality.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixtures', required=True, type=Path)
parser.add_argument('--output', default='/tmp/graphene-wi04-review', type=Path)
parser.add_argument('--port', default=8014, type=int)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
args.output.mkdir(parents=True, exist_ok=True)
url = f'http://127.0.0.1:{args.port}'
failures = []
results = {}

with tempfile.TemporaryDirectory(prefix='graphene-wi04-browser-') as directory:
    workspace = Path(directory)
    logfile = (args.output / 'server.log').open('w')
    def start():
        environment = {**os.environ, 'GRAPHENE_WORKSPACE_DIR': str(workspace)}
        process = subprocess.Popen([str(root/'backend/.venv/bin/python'), '-m', 'uvicorn',
                                   'app.main:create_app', '--factory', '--host', '127.0.0.1',
                                   '--port', str(args.port)], cwd=root/'backend', env=environment,
                                   stdout=logfile, stderr=logfile)
        for _ in range(100):
            try:
                with urlopen(url+'/health', timeout=1) as response:
                    if response.status == 200:
                        return process
            except OSError:
                time.sleep(.1)
            if process.poll() is not None:
                raise AssertionError('Local server failed; inspect server.log')
        process.terminate()
        raise AssertionError('Local server startup timeout')

    def stop(process):
        process.terminate()
        process.wait(timeout=10)

    def state():
        with urlopen(url+'/api/models') as response:
            return json.load(response)

    server = start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            page.on('pageerror', lambda error: failures.append(str(error)))
            page.on('dialog', lambda dialog: (failures.append('Unexpected dialog'), dialog.dismiss()))
            page.goto(url+'/#models')
            expect(page.get_by_text('No models imported yet.', exact=False)).to_be_visible()
            page.screenshot(path=str(args.output/'desktop-empty.png'), full_page=True)
            picker = page.get_by_label('Model package ZIP', exact=True)
            picker.set_input_files(str(args.fixtures/'unmeasured.zip'))
            picker.focus()
            page.keyboard.press('Tab')
            assert page.get_by_role('button', name='Import model', exact=True).evaluate('(el)=>el===document.activeElement')
            page.keyboard.press('Enter')
            expect(page.get_by_role('heading', name='Synthetic identity fixture', exact=True)).to_be_visible()
            assert state()['selected_model_id'] is None
            expect(page.locator('.model-feedback')).to_contain_text('Selection unchanged')
            assert page.locator('.model-feedback').evaluate('(el)=>el===document.activeElement')
            button = page.get_by_role('button', name='Select model Synthetic identity fixture', exact=True)
            button.focus()
            page.keyboard.press('Enter')
            expect(page.locator('.model-feedback')).to_contain_text('selected and saved locally')
            selected = state()['selected_model_id']
            picker.set_input_files(str(args.fixtures/'reported.zip'))
            page.get_by_role('button', name='Import model', exact=True).click()
            expect(page.get_by_role('heading', name='Imported models (2)', exact=True)).to_be_visible()
            assert state()['selected_model_id'] == selected
            entries = page.locator('.model-list > li')
            entries.nth(1).locator('summary').first.click()
            expect(entries.nth(1).get_by_text('few-layer pixel recall', exact=True)).to_be_visible()
            expect(entries.nth(1).get_by_text('These results have not been independently verified', exact=False)).to_be_visible()
            assert page.locator('img').count() == 0
            entries.nth(0).locator('summary').first.click()
            expect(entries.nth(0).get_by_text('Unmeasured:', exact=False)).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(args.output/'desktop-models.png'), full_page=True)
            results['keyboard_import_select_focus'] = 'passed'
            results['explicit_import_selection_and_safe_reported_details'] = 'passed'

            # A failed package does not lose the selected model.
            picker.set_input_files(str(args.fixtures/'invalid.zip'))
            page.get_by_role('button', name='Import model', exact=True).click()
            expect(page.get_by_role('alert')).to_contain_text('corrected ZIP')
            assert state()['selected_model_id'] == selected
            page.screenshot(path=str(args.output/'invalid-package.png'), full_page=True)
            results['invalid_package_preserves_selection'] = 'passed'

            stop(server)
            server = start()
            page.reload()
            expect(page.locator('.selection-summary')).to_contain_text('Synthetic identity fixture')
            assert state()['selected_model_id'] == selected
            results['backend_browser_restart'] = 'passed'

            # Other-tab updates reconcile when this tab receives focus.
            other = browser.new_page()
            other.goto(url+'/#models')
            expect(other.get_by_role('heading', name='Imported models (2)', exact=True)).to_be_visible()
            alternative = next(model for model in state()['models'] if model['model_id'] != selected)
            other.get_by_role('button', name='Select model '+alternative['name'], exact=True).click()
            expect(other.locator('.model-feedback')).to_contain_text('selected and saved locally')
            page.evaluate('window.dispatchEvent(new Event("focus"))')
            expect(page.locator('.selection-summary')).to_contain_text(alternative['name'])
            selected = alternative['model_id']
            other.close()
            results['other_tab_selection_reconciliation'] = 'passed'

            page.route('**/api/models', lambda route: route.abort())
            page.get_by_role('button', name='Refresh Models', exact=True).click()
            expect(page.get_by_text('Showing last confirmed model data.', exact=False)).to_be_visible()
            page.screenshot(path=str(args.output/'connection-stale.png'), full_page=True)
            page.unroute('**/api/models')
            page.get_by_role('button', name='Refresh Models', exact=True).click()
            expect(page.get_by_text('Showing last confirmed model data.', exact=False)).not_to_be_visible()
            results['connection_failure_retry_stale_state'] = 'passed'

            # Missing extras keep the registry inspectable and disable mutations.
            snapshot = state()
            snapshot['validation_available'] = False
            page.route('**/api/models', lambda route: route.fulfill(json=snapshot))
            page.get_by_role('button', name='Refresh Models', exact=True).click()
            expect(page.get_by_role('heading', name='Model support needs installation')).to_be_visible()
            expect(page.get_by_role('button', name='Import model', exact=True)).to_be_disabled()
            page.screenshot(path=str(args.output/'missing-runtime.png'), full_page=True)
            page.unroute('**/api/models')
            results['missing_runtime_guidance'] = 'passed'

            # Corrupt the selected file between actual backend restarts.
            stop(server)
            with sqlite3.connect(workspace/'workspace.sqlite3') as connection:
                relative = connection.execute('SELECT relative_path FROM artifacts JOIN models ON artifact_id=id WHERE model_id=?',(selected,)).fetchone()[0]
            (workspace/relative).write_bytes(b'corrupt fixture')
            server = start()
            page.reload()
            expect(page.get_by_text('Selected file is missing or damaged.', exact=False)).to_be_visible()
            assert state()['selected_model_id'] == selected
            page.screenshot(path=str(args.output/'unavailable-selection.png'), full_page=True)
            page.get_by_role('button', name='Select model Synthetic identity fixture', exact=True).click()
            expect(page.locator('.model-feedback')).to_contain_text('selected and saved locally')
            results['unavailable_selection_explicit_recovery'] = 'passed'

            mobile = browser.new_page(viewport={'width':390,'height':844})
            mobile.on('pageerror', lambda error: failures.append(str(error)))
            mobile.goto(url+'/#models')
            expect(mobile.get_by_role('heading', name='Imported models (2)', exact=True)).to_be_visible()
            mobile.locator('.model-list > li').nth(1).locator('summary').first.click()
            expect(mobile.get_by_text('few-layer pixel recall', exact=True)).to_be_visible()
            assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
            mobile.screenshot(path=str(args.output/'mobile-models.png'), full_page=True)
            mobile.reload()
            mobile.keyboard.press('Tab')
            expect(mobile.get_by_role('link', name='Skip to workspace')).to_be_focused()
            mobile.keyboard.press('Enter')
            expect(mobile.locator('#main')).to_be_focused()
            expect(mobile.get_by_role('heading', name='Models', exact=True)).to_be_visible()
            results['narrow_layout_and_skip_link'] = 'passed'
            assert not failures, failures
            results['page_errors'] = failures
            (args.output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
            print(json.dumps(results, indent=2))
            browser.close()
    finally:
        stop(server)
        logfile.close()
