"""Generate a local handoff report. Fixture replay is explicitly not AI."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from workflow import build_handoff

def render(report):
    esc = html.escape
    cards = []
    for task in report["tasks"]:
        observations = []
        for obs in task["observations"]:
            quotes = "".join("<blockquote>" + esc(c["quote"]) + "<br><small>" +
                             esc(c["source_id"]) + "</small></blockquote>" for c in obs["evidence"])
            observations.append("<li>" + esc(obs["text"]) + quotes + "</li>")
        cards.append("<article><p class='tag'>" + esc(task["attention"].replace("_", " ")) +
                     "</p><h2>" + esc(task["task_key"]) + "</h2><ul>" +
                     "".join(observations) + "</ul><p>Needs human review</p></article>")
    return """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hotel handoff</title><style>
body{font:17px system-ui;background:#f3f5f4;color:#172d2a;margin:0 auto;max-width:960px;padding:32px}
h1{font-size:40px}article{background:white;border:1px solid #d4dfda;border-radius:14px;padding:24px;margin:18px 0}
blockquote{border-left:3px solid #568879;padding-left:16px;color:#385149}
.tag{color:#805614;text-transform:uppercase;font-size:13px;letter-spacing:1px}
small{color:#53645e}li{margin-bottom:16px}.notice{background:#fff0ca;padding:16px;border-radius:8px}
</style><main><p>RECEPTION / NEXT SHIFT</p><h1>What still needs attention</h1>
<p class="notice">""" + esc(report["mode"]) + """ · Synthetic data only.
Quotes are checked for exact occurrence, not semantic truth. Review before acting.</p>
""" + "".join(cards) + "</main></html>"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Call configured Strands/Bedrock model")
    parser.add_argument("--output", type=Path, default=Path("results/demo"))
    args = parser.parse_args()
    fixture = json.loads((Path(__file__).parent / "fixtures/shift.json").read_text())
    if args.live:
        from agent_adapter import extract
        observations = extract(fixture["sources"])
        mode = "Live Strands extraction"
    else:
        observations = fixture["observations"]
        mode = "Fixture replay — no AI model used"
    tasks = build_handoff(observations, fixture["sources"])
    report = {"mode": mode, "source_sha256": hashlib.sha256(json.dumps(fixture["sources"],
              sort_keys=True).encode()).hexdigest(), "sources": fixture["sources"], "tasks": tasks}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "handoff.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (args.output / "index.html").write_text(render(report))
    print(f"{mode}: {len(tasks)} tasks; report: {args.output / 'index.html'}")

if __name__ == "__main__":
    main()
