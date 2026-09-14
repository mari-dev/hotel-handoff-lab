"""Offline HTTP adapter integration; synthetic auth and data, no cloud calls."""
import json,os,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import judge_lambda as app
from invoice_store import Store
from server import make_server

def main():
    with tempfile.TemporaryDirectory() as folder:
        os.environ['JUDGE_PASSWORD']='synthetic-adapter-check'
        server=make_server(0,Store(Path(folder)/'db.sqlite'),secure_cookies=True)
        server.auth.set_password('judge','synthetic-adapter-check','Judge')
        cookies=[]
        app._server=server
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def call(path,body=None):
            event={'headers':{'content-type':'application/json'},'cookies':cookies,'rawPath':path,'requestContext':{'domainName':'example.lambda-url.eu-north-1.on.aws','http':{'method':'POST' if body is not None else 'GET'}}}
            if body is not None:event['body']=json.dumps(body)
            result=app.handler(event,None)
            if result.get('cookies'):cookies[:]=[c.split(';')[0] for c in result['cookies']]
            assert result['statusCode']<300,result
            return json.loads(result['body']) if path.startswith('/api/') else result['body']
        try:
            call('/api/auth/login',dict(username='judge',password='synthetic-adapter-check'))
            assert 'Judge sandbox' in call('/')
            key=call('/api/requests',dict(guest='Synthetic Guest',stay='12–14 September',source='Email',note='',actor='Judge'))['id']
            call('/api/action',dict(id=key,action='claim',actor='Judge'))
            call('/api/sample-file',dict(id=key,kind='pdf'))
            assert call('/api/requests')[0]['status']=='prepared'
            call('/api/sample-file',dict(id=key,kind='eml'))
            assert call('/api/requests')[0]['status']=='sent'
            print('PASS: judge adapter auth, HTML, request, claim, PDF and EML reconciliation through HTTP. No model calls.')
        finally:
            server.shutdown();thread.join();server.server_close();app._server=None

if __name__=='__main__': main()
