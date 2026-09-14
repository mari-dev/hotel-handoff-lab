"""Record the intro animation (scripts/video/intro-animation.html) as a video."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE / "out" / "intro"
OUT.mkdir(parents=True, exist_ok=True)
DURATION_MS = 17_600

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(
        viewport={"width": 1440, "height": 1050},
        record_video_dir=str(OUT),
        record_video_size={"width": 1440, "height": 1050},
    )
    page = context.new_page()
    page.goto((HERE / "intro-animation.html").resolve().as_uri())
    page.wait_for_timeout(DURATION_MS)
    context.close()
    browser.close()

produced = list(OUT.glob("*.webm"))
print("recorded:", produced)
