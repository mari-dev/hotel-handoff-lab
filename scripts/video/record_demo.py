"""Record the real app walkthrough with a visible, glided mouse cursor and
realistic typing, for the submission video. Uses the live Strands/Bedrock
model exactly like tests/browser_live_demo.py; synthetic data only.
"""
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
sys.path.insert(0, str(Path(__file__).parent))
from narration import DEMO_LINES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scripts/video/out/demo"
OUT.mkdir(parents=True, exist_ok=True)
DURATIONS = json.loads((ROOT / "scripts/video/out/audio/durations.json").read_text())
NARRATION = iter(DEMO_LINES)

CURSOR_JS = """
(() => {
  const dot = document.createElement('div');
  dot.id = '__cursor';
  dot.style.cssText = 'position:fixed;top:50%;left:50%;width:22px;height:22px;border-radius:50%;'
    + 'background:rgba(56,81,73,.88);border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4);'
    + 'pointer-events:none;z-index:2147483647;transform:translate(-50%,-50%);';
  const attach = () => document.body && document.body.appendChild(dot);
  if (document.body) attach(); else document.addEventListener('DOMContentLoaded', attach);
  window.__setCursor = (x, y) => { dot.style.left = x + 'px'; dot.style.top = y + 'px'; };
  window.__cursorClick = () => {
    dot.animate(
      [{ transform: 'translate(-50%,-50%) scale(1)' },
       { transform: 'translate(-50%,-50%) scale(1.9)', opacity: .35 },
       { transform: 'translate(-50%,-50%) scale(1)', opacity: 1 }],
      { duration: 280 }
    );
  };
})();
"""

SERVER = """import sys,threading; from pathlib import Path; from invoice_store import Store; from server import make_server
store=Store(Path(sys.argv[1])/'test.sqlite'); server=make_server(0,store)
server.auth.set_password('browser-test','Synthetic-browser-password-2026','Test Operator')
stop=threading.Event(); threading.Thread(target=server.monitor.run,args=(stop,),daemon=True).start()
print(server.server_port,flush=True); server.serve_forever()
"""

cursor_pos = [720, 525]


def glide(page, x, y, steps=22, step_ms=16):
    x0, y0 = cursor_pos
    for i in range(1, steps + 1):
        t = i / steps
        cx, cy = x0 + (x - x0) * t, y0 + (y - y0) * t
        page.mouse.move(cx, cy)
        page.evaluate("([x,y])=>window.__setCursor(x,y)", [cx, cy])
        page.wait_for_timeout(step_ms)
    cursor_pos[0], cursor_pos[1] = x, y


def click_at(page, locator, pause_before=250):
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    glide(page, x, y)
    page.wait_for_timeout(pause_before)
    page.evaluate("window.__cursorClick()")
    page.mouse.down()
    page.wait_for_timeout(70)
    page.mouse.up()


def type_into(page, locator, text, delay=38):
    click_at(page, locator)
    page.keyboard.type(text, delay=delay)


def caption(page, text):
    page.evaluate(
        """text=>{let e=document.getElementById('demo-caption');
        if(!e){e=document.createElement('div');e.id='demo-caption';e.setAttribute('popover','manual');
        e.style.cssText='position:fixed;inset:auto;bottom:26px;left:6%;width:88%;margin:0;border:0;'
        +'box-sizing:border-box;padding:18px 22px;background:#142831;color:white;font:22px system-ui,sans-serif;'
        +'z-index:2147483000;border-radius:12px;text-align:center;pointer-events:none;line-height:1.4';
        document.body.appendChild(e);} e.textContent=text;e.hidePopover();e.showPopover();}""",
        text,
    )


TIMELINE = []
T0 = [None]


def beat(page, _unused_text=None, _unused_wait_ms=None):
    text = next(NARRATION)
    wait_ms = int(DURATIONS[text]["duration_ms"]) + 600
    caption(page, text)
    offset_ms = int((time.time() - T0[0]) * 1000) if T0[0] else 0
    TIMELINE.append({"text": text, "wait_ms": wait_ms, "offset_ms": offset_ms})
    page.wait_for_timeout(wait_ms)


with tempfile.TemporaryDirectory() as temp:
    env = {**os.environ, "AWS_PROFILE": "hotel-handoff-lab", "AWS_REGION": "eu-north-1",
           "HANDOFF_MODEL_ID": "amazon.nova-lite-v1:0"}
    proc = subprocess.Popen([str(ROOT / ".venv/bin/python"), "-c", SERVER, temp], cwd=ROOT, env=env,
                             stdout=subprocess.PIPE, stderr=(OUT / "server.log").open("w"), text=True)
    try:
        port = int(proc.stdout.readline().strip())
        url = f"http://127.0.0.1:{port}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(viewport={"width": 1440, "height": 1050},
                                           record_video_dir=str(OUT),
                                           record_video_size={"width": 1440, "height": 1050})
            context.add_init_script(CURSOR_JS)
            context.route("https://app.lexware.de/**",
                           lambda route: route.fulfill(status=200, body="Lexware navigation verified."))
            page = context.new_page()
            T0[0] = time.time()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url)
            page.wait_for_timeout(1500)

            type_into(page, page.locator("#username"), "browser-test")
            type_into(page, page.locator("#password"), "Synthetic-browser-password-2026")
            click_at(page, page.locator("#submit"))
            expect(page.locator("#new")).to_be_visible()
            beat(page, "Hotel Handoff Lab — invoice requests arrive across messages and staff shifts.", 3200)

            click_at(page, page.locator("#new"))
            click_at(page, page.locator("#intake-box summary"))
            message = "Anna Keller requests an invoice for 12-14 September. Company: Example GmbH. Address will follow."
            type_into(page, page.locator("#intake-message"), message, delay=18)
            beat(page, "Synthetic guest message. Strands extracts literal details; staff review before saving.", 3200)

            with page.expect_response(lambda r: r.url.endswith("/api/intake"), timeout=180000) as response:
                click_at(page, page.locator("#analyze"))
            result = response.value.json()
            (OUT / "browser-live-proposal.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
            assert response.value.status == 200, result
            expect(page.locator("#guest")).to_have_value("Anna Keller")
            assert result["proposal"]["address"] is None, result
            expect(page.locator("#intake-status")).to_contain_text("Proposal ready")
            beat(page, "Every field is shown with its source text. Missing details stay empty, not guessed.", 3600)

            click_at(page, page.locator("#save-request"))
            expect(page.locator(".card")).to_have_count(1)
            beat(page, "Only explicit confirmation creates the request. Preparing it assigns one operator atomically.", 3600)

            card = page.locator(".card").first
            box = card.locator("[data-action=claim]").bounding_box()
            with context.expect_page() as popup:
                click_at(page, card.locator("[data-action=claim]"))
            popup.value.wait_for_url("https://app.lexware.de/")
            popup.value.close()
            expect(card.locator(".status")).to_have_text("In progress")
            click_at(page, card.locator("summary"))
            beat(page, "Lexware opens as a browser link. This prototype does not create accounting invoices.", 3600)

            click_at(page, card.locator("[data-action=sample_pdf]"))
            expect(card.locator(".status")).to_have_text("PDF prepared", timeout=20000)
            beat(page, "A real synthetic PDF is matched by an independent guest-and-stay monitor.", 4000)

            click_at(page, card.locator("[data-action=sample_eml]"))
            expect(page.locator(".card")).to_have_count(0, timeout=20000)
            click_at(page, page.locator("#nav-history"))
            expect(page.locator(".card")).to_have_count(1)
            expect(page.locator(".status")).to_have_text("Sent")
            click_at(page, page.locator(".card summary"))
            beat(page, "The exported Sent email contains the identical PDF attachment. No email is sent by this app.", 4600)

            beat(page, "A local synthetic prototype. Human review stays required at every step.", 3600)
            assert not errors, errors

            video = page.video
            context.close()
            video.save_as(str(OUT / "hotel-handoff-demo.webm"))
            browser.close()
            (OUT / "timeline.json").write_text(json.dumps(TIMELINE, indent=2))
            print("DONE:", OUT / "hotel-handoff-demo.webm")
    finally:
        proc.terminate()
        proc.wait(timeout=15)
