import http.client,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from invoice_store import Store
from server import make_server

class AuthHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'db.sqlite')
        self.server=make_server(0,self.store)
        self.server.auth.set_password('alice','Synthetic-alice-password-2026','Alice')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
    def close(self):
        self.server.shutdown();self.thread.join();self.server.server_close()
    def request(self,path,body=None,cookie='',origin=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        headers={'Content-Type':'application/json','Cookie':cookie}
        if origin:headers['Origin']=origin
        connection.request('POST' if body is not None else 'GET',path,
                           json.dumps(body) if body is not None else None,headers)
        response=connection.getresponse();result=(response.status,dict(response.headers),response.read())
        connection.close();return result
    def login(self):
        status,headers,_=self.request('/api/auth/login',dict(username='alice',password='Synthetic-alice-password-2026'))
        self.assertEqual(status,200)
        return headers['Set-Cookie'].split(';')[0]
    def test_ui_redirects_and_every_data_api_rejects_anonymous_access(self):
        status,headers,_=self.request('/')
        self.assertEqual(status,303);self.assertEqual(headers['Location'],'/login')
        for path in ('/api/requests','/api/evidence','/api/health','/api/auth/session'):
            self.assertEqual(self.request(path)[0],401,path)
        for path in ('/api/requests','/api/action','/api/details','/api/sample-file','/api/intake'):
            self.assertEqual(self.request(path,{})[0],401,path)
        self.assertEqual(self.store.list(),[])
    def test_actor_comes_from_session_not_request(self):
        cookie=self.login()
        body=dict(guest='Synthetic Guest',stay='September 12',source='Email',note='',actor='Forged',prepare=True)
        self.assertEqual(self.request('/api/requests',body,cookie)[0],201)
        row=self.store.list()[0]
        self.assertEqual(row['owner'],'Alice');self.assertEqual(row['events'][0]['actor'],'Alice')
    def test_logout_revokes_old_cookie_and_clears_browser_cookie(self):
        cookie=self.login()
        status,headers,_=self.request('/api/auth/logout',{},cookie)
        self.assertEqual(status,200);self.assertIn('Max-Age=0',headers['Set-Cookie'])
        self.assertEqual(self.request('/api/requests',cookie=cookie)[0],401)
    def test_cross_origin_login_and_authenticated_writes_rejected(self):
        cookie=self.login()
        self.assertEqual(self.request('/api/auth/login',{},origin='https://evil.invalid')[0],403)
        self.assertEqual(self.request('/api/requests',{},cookie,origin='https://evil.invalid')[0],403)
    def test_new_login_invalidates_preexisting_session_cookie(self):
        old=self.login()
        status,headers,_=self.request('/api/auth/login',dict(username='alice',password='Synthetic-alice-password-2026'),old)
        self.assertEqual(status,200);self.assertNotEqual(old,headers['Set-Cookie'].split(';')[0])
        self.assertEqual(self.request('/api/requests',cookie=old)[0],401)

    def test_authenticated_intake_route_preserves_confirmation_boundary(self):
        cookie=self.login()
        fake={'proposal':{'invoice_requested':False},'usage':{},'mode':'offline-test'}
        with patch.dict('os.environ',{'AWS_PROFILE':'synthetic-test'}),patch('invoice_intake.propose',return_value=fake) as propose:
            status,_,body=self.request('/api/intake',{'message':'Synthetic source'},cookie)
        self.assertEqual(status,200);self.assertEqual(json.loads(body),fake)
        propose.assert_called_once_with('Synthetic source',[])
        self.assertEqual(self.store.list(),[])
