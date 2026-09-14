import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/demo'; OUT.mkdir(parents=True,exist_ok=True)
SERVER="""import sys,threading; from pathlib import Path; from invoice_store import Store; from server import make_server
store=Store(Path(sys.argv[1])/'test.sqlite'); server=make_server(0,store)
server.auth.set_password('browser-test','Synthetic-browser-password-2026','Test Operator')
stop=threading.Event(); threading.Thread(target=server.monitor.run,args=(stop,),daemon=True).start()
print(server.server_port,flush=True); server.serve_forever()
"""
with tempfile.TemporaryDirectory() as temp:
    env={**os.environ,'AWS_PROFILE':'hotel-handoff-lab','AWS_REGION':'eu-north-1','HANDOFF_MODEL_ID':'amazon.nova-lite-v1:0'}
    proc=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-c',SERVER,temp],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=(OUT/'server.log').open('w'),text=True)
    try:
        port=int(proc.stdout.readline().strip()); url=f'http://127.0.0.1:{port}'
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chromium',headless=True,args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':1440,'height':1050},record_video_dir=str(OUT),record_video_size={'width':1440,'height':1050})
            context.route('https://app.lexware.de/**',lambda route:route.fulfill(status=200,body='Lexware navigation verified. External page intercepted in this test.'))
            page=context.new_page(); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url)
            page.wait_for_timeout(3500)
            page.locator('#username').fill('browser-test');page.locator('#password').fill('Synthetic-browser-password-2026');page.locator('#submit').click()
            expect(page.locator('#new')).to_be_visible()
            def caption(text):
                page.evaluate('''text=>{let e=document.getElementById('demo-caption');if(!e){e=document.createElement('div');e.id='demo-caption';e.setAttribute('popover','manual');e.style.cssText='position:fixed;inset:auto;bottom:12px;left:5%;width:90%;margin:0;border:0;box-sizing:border-box;padding:18px;background:#142831;color:white;font:20px sans-serif;z-index:99999;border-radius:12px;text-align:center;pointer-events:none';document.body.appendChild(e);} e.textContent=text;e.hidePopover();e.showPopover();}''',text)
            caption('Hotel Handoff Lab — invoice requests arrive across messages and staff shifts.');page.wait_for_timeout(4000)
            page.locator('#new').click();page.locator('#intake-box summary').click()
            message='Anna Keller requests an invoice for 12–14 September. Company: Example GmbH. Address will follow.'
            page.locator('#intake-message').fill(message)
            caption('Synthetic guest message. Strands extracts literal details; staff review before saving.');page.wait_for_timeout(4000)
            with page.expect_response(lambda r:r.url.endswith('/api/intake'),timeout=180000) as response:
                page.locator('#analyze').click()
            result=response.value.json(); (OUT/'browser-live-proposal.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
            assert response.value.status==200,result
            expect(page.locator('#guest')).to_have_value('Anna Keller')
            assert result['proposal']['address'] is None,result
            with urllib.request.urlopen(urllib.request.Request(url+'/api/requests',headers={'Cookie': '; '.join(c['name']+'='+c['value'] for c in context.cookies())})) as r: assert json.load(r)==[]
            expect(page.locator('#intake-status')).to_contain_text('Proposal ready')
            page.screenshot(path=str(OUT/'01-live-proposal.png'),full_page=True)
            page.wait_for_timeout(5000)
            page.locator('#save-request').click();expect(page.locator('.card')).to_have_count(1)
            caption('Only confirmation creates the request. Preparing it assigns one operator atomically.');page.wait_for_timeout(4000)
            card=page.locator('.card').first
            with context.expect_page() as popup:card.locator('[data-action=claim]').click()
            popup.value.wait_for_url('https://app.lexware.de/');popup.value.close()
            expect(card.locator('.status')).to_have_text('In progress')
            card.locator('summary').click()
            page.screenshot(path=str(OUT/'02-claimed.png'),full_page=True)
            caption('Lexware opens as a browser link. This demo does not create accounting invoices.');page.wait_for_timeout(4000)
            card.locator('[data-action=sample_pdf]').click()
            expect(card.locator('.status')).to_have_text('PDF prepared',timeout=20000)
            caption('A real synthetic PDF file is matched by the independent guest-and-stay monitor.');page.wait_for_timeout(5000)
            page.screenshot(path=str(OUT/'03-pdf-prepared.png'),full_page=True)
            card.locator('[data-action=sample_eml]').click();expect(page.locator('.card')).to_have_count(0,timeout=20000)
            page.locator('#nav-history').click();expect(page.locator('.card')).to_have_count(1)
            expect(page.locator('.status')).to_have_text('Sent')
            page.locator('.card summary').click()
            caption('The exported Sent EML contains the identical PDF attachment. No email is sent by this app.');page.wait_for_timeout(6000)
            page.screenshot(path=str(OUT/'04-completed.png'),full_page=True)
            with urllib.request.urlopen(urllib.request.Request(url+'/api/requests',headers={'Cookie': '; '.join(c['name']+'='+c['value'] for c in context.cookies())})) as r: rows=json.load(r)
            assert rows[0]['status']=='sent'
            with urllib.request.urlopen(urllib.request.Request(url+'/api/evidence',headers={'Cookie': '; '.join(c['name']+'='+c['value'] for c in context.cookies())})) as r: evidence=json.load(r)
            assert len(evidence)==2 and all(x['state']=='linked' for x in evidence)
            caption('Local synthetic prototype. Human review remains required. No direct accounting or mail API integration.');page.wait_for_timeout(6000)
            assert not errors,errors
            video=page.video;context.close();video.save_as(str(OUT/'hotel-handoff-live-demo.webm'));browser.close()
            (OUT/'browser-check.json').write_text(json.dumps({'passed':True,'synthetic_only':True,'live_model':True,'lexware_intercepted':True,'requests':rows,'evidence':evidence,'javascript_errors':errors},indent=2))
            print('PASS: actual browser live intake, human confirmation, claim, PDF monitor, exact EML attachment, archive. Video: results/demo/hotel-handoff-live-demo.webm')
    finally:
        proc.terminate();proc.wait(timeout=15)
