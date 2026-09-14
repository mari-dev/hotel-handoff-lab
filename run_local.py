"""Restart the local demo, inheriting credentials without printing them."""
import argparse, os, signal, subprocess, time, urllib.request, json
from pathlib import Path
from bedrock_config import ai_configured
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--require-ai',action='store_true');args=p.parse_args()
if args.require_ai and not ai_configured():
    raise SystemExit('Set AWS_PROFILE or AWS_BEARER_TOKEN_BEDROCK in this terminal first.')
folder=ROOT/'results';folder.mkdir(exist_ok=True);pidfile=folder/'server.pid'
if pidfile.exists():
    pid=int(pidfile.read_text().strip());proc=Path('/proc')/str(pid)
    try:
        if proc.joinpath('cwd').resolve()==ROOT and b'server.py' in proc.joinpath('cmdline').read_bytes().split(b'\0'):
            os.kill(pid,signal.SIGTERM)
            for _ in range(30):
                try:
                    if proc.joinpath('stat').read_text().split(') ',1)[1].startswith('Z'): break
                except FileNotFoundError: break
                time.sleep(.1)
    except FileNotFoundError: pass
with (folder/'server.log').open('ab') as log:
    process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'server.py'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
pidfile.write_text(str(process.pid))
for _ in range(40):
    time.sleep(.15)
    if process.poll() is not None: raise SystemExit('Server failed: inspect results/server.log')
    try:
        with urllib.request.urlopen('http://localhost:8765/healthz',timeout=1) as response: health=json.load(response)
        print('http://localhost:8765/login — sign-in required');break
    except OSError: pass
else: raise SystemExit('Server did not become ready; inspect results/server.log')
