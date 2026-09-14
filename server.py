"""Loopback-only invoice lab with file evidence and optional Strands."""
import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from invoice_store import Store,Conflict,now
from evidence_monitor import Monitor
from sample_documents import place_demo_file
from bedrock_config import ai_configured
from authentication import Auth,LoginError,LoginLimited
ROOT=Path(__file__).parent

def make_server(port,store,monitor=None,*,secure_cookies=False):
    auth=Auth(store)
    monitor=monitor or Monitor(store,Path(store.path).parent/'inbox')
    ai_lock=threading.Lock()
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS ai_runs(at TEXT NOT NULL,outcome TEXT NOT NULL,usage TEXT NOT NULL)')
    class Handler(BaseHTTPRequestHandler):
        def send(self,status,data,mime='application/json; charset=utf-8',headers=None):
            body=json.dumps(data,ensure_ascii=False).encode() if isinstance(data,(dict,list)) else data
            self.send_response(status);self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Referrer-Policy','same-origin')
            for key,value in (headers or {}).items(): self.send_header(key,value)
            self.end_headers();self.wfile.write(body)
        def local(self):
            host=self.headers.get('Host','');origin=self.headers.get('Origin')
            return host in {f'localhost:{self.server.server_port}',f'127.0.0.1:{self.server.server_port}'} and (not origin or origin=='http://'+host)
        def do_GET(self):
            if not self.local(): return self.send(403,{'error':'Origin not allowed'})
            path=urlparse(self.path).path
            if path=='/healthz': return self.send(200,{'status':'ok','authentication_required':True})
            if path in {'/login','/login.js','/login.css'}:
                name={'/login':'login.html','/login.js':'login.js','/login.css':'login.css'}[path]
                mime={'/login':'text/html','/login.js':'text/javascript','/login.css':'text/css'}[path]
                return self.send(200,(ROOT/'web'/name).read_bytes(),mime+'; charset=utf-8')
            user=auth.user(self.headers.get('Cookie'))
            if not user:
                if path.startswith('/api/'): return self.send(401,{'error':'Sign in required'})
                return self.send(303,b'',headers={'Location':'/login'})
            if path=='/api/auth/session': return self.send(200,user)
            if path=='/api/requests': self.send(200,store.list())
            elif path=='/api/evidence': self.send(200,monitor.records())
            elif path=='/api/health':
                self.send(200,{'ai_configured':ai_configured(),'watch_folder':str(monitor.folder),'synthetic_only':True})
            elif path in {'/vendor/i18next.min.js','/locales.js','/i18n.js','/followup.js'}:
                self.send(200,(ROOT/'web'/path.lstrip('/')).read_bytes(),'text/javascript; charset=utf-8')
            elif path in {'/','/app.js','/style.css'}:
                name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path]
                mime={'/':'text/html','/app.js':'text/javascript','/style.css':'text/css'}[path]
                self.send(200,(ROOT/'web'/name).read_bytes(),mime+'; charset=utf-8')
            else: self.send(404,{'error':'Not found'})
        def do_POST(self):
            if not self.local(): return self.send(403,{'error':'Origin not allowed'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'JSON required'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=20000: raise ValueError('Invalid request size')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict): raise ValueError('Invalid request')
                if self.path=='/api/auth/login':
                    try: token,user=auth.login(data.get('username'),data.get('password'))
                    except LoginLimited as exc: return self.send(429,{'error':str(exc)})
                    except LoginError as exc: return self.send(401,{'error':str(exc)})
                    auth.logout(self.headers.get('Cookie'))
                    return self.send(200,user,headers={'Set-Cookie':auth.cookie(token,secure_cookies)})
                if self.path=='/api/auth/logout':
                    auth.logout(self.headers.get('Cookie'))
                    return self.send(200,{'ok':True},headers={'Set-Cookie':auth.cookie('',secure_cookies,True)})
                user=auth.user(self.headers.get('Cookie'))
                if not user: return self.send(401,{'error':'Sign in required'})
                data['actor']=user['display_name']
                if self.path=='/api/requests':
                    if not isinstance(data.get('prepare',False),bool): raise ValueError('Invalid prepare value')
                    key=store.create(data.get('guest',''),data.get('stay',''),data.get('source','In person'),data.get('note',''),data.get('actor',''),data.get('prepare',False))
                    self.send(201,{'id':key})
                elif self.path=='/api/action':
                    key,action=data.get('id'),data.get('action')
                    if not isinstance(key,str) or action not in {'claim','release','deliver'}: raise ValueError('Action unavailable')
                    store.act(key,action,data.get('actor',''));self.send(200,{'ok':True})
                elif self.path=='/api/details':
                    store.details(data.get('id'),data.get('stay'),data.get('note'),data.get('actor'))
                    monitor.scan();self.send(200,{'ok':True})
                elif self.path=='/api/followup/confirm':
                    key=store.confirm_followup(data.get('proposal_id'),user['username'],user['display_name'])
                    monitor.scan();self.send(200,{'ok':True,'id':key})
                elif self.path=='/api/sample-file':
                    row=next((row for row in store.list() if row['id']==data.get('id')),None)
                    if not row: raise ValueError('Request not found')
                    name=place_demo_file(monitor.folder,row,data.get('kind'))
                    # This endpoint only writes a file. The monitor updates state.
                    self.send(201,{'filename':name})
                elif self.path in {'/api/intake','/api/followup'}:
                    if not ai_configured():
                        return self.send(503,{'error':'AI is not configured: restart with AWS_PROFILE or AWS_BEARER_TOKEN_BEDROCK.'})
                    if not ai_lock.acquire(blocking=False): return self.send(409,{'error':'Analysis already in progress'})
                    try:
                        with store.connect() as db:
                            count=db.execute('SELECT COUNT(*) FROM ai_runs WHERE substr(at,1,10)=?',(now()[:10],)).fetchone()[0]
                            if count>=20: return self.send(429,{'error':'Local limit: 20 analyses per day'})
                            stamp=now();db.execute('INSERT INTO ai_runs VALUES (?,?,?)',(stamp,'started','{}'))
                        try:
                            if self.path=='/api/followup':
                                from followup import propose_followup
                                result=propose_followup(data.get('message'),store.list(),data.get('selected_id',''))
                                result['proposal_id']=store.save_followup(result['plan'],user['username'])
                            else:
                                from invoice_intake import propose
                                result=propose(data.get('message'),store.list())
                        except Exception as exc:
                            with store.connect() as db: db.execute("UPDATE ai_runs SET outcome='failed' WHERE at=?",(stamp,))
                            message=str(exc) if isinstance(exc,ValueError) else 'Analysis failed. Check model access; no request was created.'
                            return self.send(502,{'error':message})
                        with store.connect() as db:
                            db.execute("UPDATE ai_runs SET outcome='completed',usage=? WHERE at=?",(json.dumps(result['usage']),stamp))
                        self.send(200,result)
                    finally: ai_lock.release()
                else: self.send(404,{'error':'Not found'})
            except Conflict as exc: self.send(409,{'error':str(exc)})
            except (ValueError,TypeError) as exc: self.send(400,{'error':str(exc)})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.monitor=monitor;server.auth=auth
    return server

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args();folder=ROOT/'results';folder.mkdir(exist_ok=True)
    store=Store(folder/'invoices.sqlite3');store.seed();monitor=Monitor(store,folder/'inbox')
    server=make_server(args.port,store,monitor);stop=threading.Event()
    worker=threading.Thread(target=monitor.run,args=(stop,),daemon=True);worker.start()
    print(f'Invoice app: http://localhost:{server.server_port}; synthetic files only',flush=True)
    try: server.serve_forever()
    finally: stop.set();worker.join(timeout=5);server.server_close()
