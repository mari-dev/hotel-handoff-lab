import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from invoice_store import Store
from server import make_server
from playwright.sync_api import sync_playwright,expect

with tempfile.TemporaryDirectory() as temp:
    store=Store(Path(temp)/'db.sqlite');store.seed();server=make_server(0,store)
    server.auth.set_password("language-test","Synthetic-language-password-2026","Test Operator")
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1050});errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://localhost:{server.server_port}')
            page.locator('#username').fill('language-test')
            page.locator('#password').fill('Synthetic-language-password-2026')
            page.locator('#submit').click()
            page.wait_for_url(f'http://localhost:{server.server_port}/')
            expect(page.locator('.card')).to_have_count(3)
            expect(page.locator('html')).to_have_attribute('lang','en')
            page.locator('#language').select_option('de')
            expect(page.locator('#heading')).to_have_text('Wer wartet auf eine Rechnung?')
            page.locator('#new').click()
            page.locator('#guest').fill('Untranslated Guest')
            page.locator('#form details').last.locator('summary').click()
            page.locator('[name=stay]').fill('September 12–15')
            page.locator('[name=note]').fill('Original guest note: fattura richiesta. <script>bad()</script>')
            page.locator('[name=source]').select_option('Phone')
            page.locator('#language-dialog').select_option('it')
            expect(page.locator('#save-request')).to_have_text('Aggiungi richiesta')
            expect(page.locator('#guest')).to_have_value('Untranslated Guest')
            expect(page.locator('[name=source]')).to_have_value('Phone')
            expect(page.locator('[name=note]')).to_have_value('Original guest note: fattura richiesta. <script>bad()</script>')
            page.locator('#save-request').click()
            expect(page.locator('.card')).to_have_count(4)
            row=next(x for x in store.list() if x['guest']=='Untranslated Guest')
            assert row['source']=='Phone' and row['note'].startswith('Original guest note: fattura')
            card=page.locator('.card').filter(has_text='Untranslated Guest')
            expect(card).to_contain_text('Telefono')
            card.locator('summary').click()
            expect(card).to_contain_text('Richiesta registrata')
            page.locator('#language').select_option('de')
            expect(card).to_contain_text('Telefon')
            expect(card).to_contain_text('Anfrage hinzugefügt')
            expect(card).to_contain_text('Original guest note: fattura richiesta.')
            page.reload();expect(page.locator('html')).to_have_attribute('lang','de')
            expect(page.locator('#language')).to_have_value('de')
            expect(page.locator('#actor')).to_have_value('Test Operator')
            expect(page.locator('#actor')).to_have_attribute('readonly','')
            page.locator('#new').click()
            page.locator('#language-dialog').select_option('it')
            page.locator('#close').click()
            for lang in ('de','it','en'):
                page.locator('#language').select_option(lang)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),lang
                assert page.locator('#language').is_visible()
            page.screenshot(path='/tmp/hotel-languages-mobile.png',full_page=True)
            page.set_viewport_size({'width':1440,'height':1050})
            page.locator('#language').select_option('de')
            page.screenshot(path='/tmp/hotel-languages-desktop.png',full_page=True)
            assert not errors,errors
            print('PASS: EN/DE/IT switching, remembered language, unsaved form preservation, stable API source, localized events, untouched guest text, mobile layout, no JS errors')
            browser.close()
    finally:server.shutdown();server.server_close()
