"""Offline browser check of login, language, identity and logout."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from invoice_store import Store
from server import make_server
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    store=Store(Path(folder)/'db.sqlite');store.seed();server=make_server(0,store)
    server.auth.set_password('reception','Synthetic-browser-password-2026','Reception Test')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chromium',headless=True,args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':1440,'height':1000})
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            base=f'http://127.0.0.1:{server.server_port}'
            page.goto(base);expect(page).to_have_url(base+'/login')
            assert page.request.get(base+'/api/requests').status==401
            page.screenshot(path=str(ROOT/'results/auth-login-desktop.png'),full_page=True)
            page.locator('#username').fill('reception');page.locator('#password').fill('incorrect')
            page.locator('#language').select_option('it')
            expect(page.locator('#username')).to_have_value('reception')
            page.locator('#submit').click();expect(page.locator('#login-error')).to_have_text('Nome utente o password non validi.')
            page.locator('#password').fill('Synthetic-browser-password-2026')
            page.locator('#show-password').click();expect(page.locator('#password')).to_have_attribute('type','text')
            page.locator('#show-password').click();expect(page.locator('#password')).to_have_attribute('type','password')
            page.locator('#language').select_option('de');expect(page.locator('#submit')).to_have_text('Anmelden')
            page.locator('#submit').click();expect(page).to_have_url(base+'/')
            expect(page.locator('.card')).to_have_count(3)
            expect(page.locator('#actor')).to_have_value('Reception Test')
            expect(page.locator('#actor')).to_have_attribute('readonly','')
            cookies=context.cookies();session=next(c for c in cookies if c['name']=='handoff_session')
            assert session['httpOnly'] and session['sameSite']=='Strict'
            page.reload();expect(page.locator('#actor')).to_have_value('Reception Test')
            page.locator('#logout').click();expect(page).to_have_url(base+'/login')
            assert page.request.get(base+'/api/requests').status==401
            assert not any(c['name']=='handoff_session' for c in context.cookies())
            page.goto(base);expect(page).to_have_url(base+'/login')
            page.set_viewport_size({'width':390,'height':844})
            for lang in ('en','de','it'):
                page.locator('#language').select_option(lang)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                expect(page.locator('#submit')).to_be_visible()
            page.screenshot(path=str(ROOT/'results/auth-login-mobile.png'),full_page=True)
            assert not errors,errors
            browser.close();print('PASS: protected APIs, EN/DE/IT login, invalid password, visibility toggle, remembered session, verified actor, logout revocation, mobile layout; no JS errors. No model calls.')
    finally:server.shutdown();thread.join();server.server_close()
