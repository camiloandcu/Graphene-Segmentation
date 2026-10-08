import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description='Verify the local readiness UI with Playwright.')
parser.add_argument('--url', default='http://127.0.0.1:8000/')
parser.add_argument('--output', default='/tmp/graphene-wi01-review')
parser.add_argument('--browser-executable')
args=parser.parse_args()
out=Path(args.output)
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=args.browser_executable,headless=True,args=['--no-sandbox'])
    failures=[]
    for name,width,height in [('desktop',1440,1000),('mobile',390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        page.on('pageerror',lambda error: failures.append(str(error)))
        page.goto(args.url)
        page.get_by_role('status').filter(has_text='Workspace connected').wait_for()
        assert page.get_by_role('heading',name='No model available').is_visible()
        assert page.get_by_role('button',name='Check connection').is_enabled()
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(out/f'{name}.png'),full_page=True)
        page.close()
    page=browser.new_page(viewport={'width':1280,'height':900})
    page.route('**/health',lambda route:route.abort())
    page.goto(args.url)
    page.get_by_role('status').filter(has_text='Connection unavailable').wait_for()
    page.screenshot(path=str(out/'connection-error.png'),full_page=True)
    page.unroute('**/health')
    page.get_by_role('button',name='Check connection').click()
    page.get_by_role('status').filter(has_text='Workspace connected').wait_for()
    page.reload()
    page.keyboard.press('Tab')
    assert page.get_by_role('link',name='Skip to workspace').evaluate('(el) => el === document.activeElement')
    page.keyboard.press('Enter')
    assert page.locator('#main').evaluate('(el) => el === document.activeElement')
    # Slow and malformed responses must not claim the workspace is ready.
    page.route('**/health',lambda route:route.fulfill(status=200,body='{"status":"ok","storage_ready":false}',content_type='application/json'))
    page.get_by_role('button',name='Check connection').click()
    page.get_by_role('status').filter(has_text='Connection unavailable').wait_for()
    assert not failures,failures
    print(json.dumps({'desktop_mobile':'passed','overflow':'none','connection_failure_retry':'passed','keyboard_skip_link':'passed','invalid_health':'passed','page_errors':failures,'screenshots':str(out)},indent=2))
    browser.close()
