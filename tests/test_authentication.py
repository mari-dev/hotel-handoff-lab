import tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from authentication import Auth, LoginError, LoginLimited, COOKIE
from invoice_store import Store

class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.auth=Auth(Store(Path(self.temp.name)/'db.sqlite'))
        self.auth.set_password('alice','Synthetic-alice-password-2026','Alice')
    def login(self):
        return self.auth.login('alice','Synthetic-alice-password-2026')[0]
    def test_password_is_hashed_and_session_is_opaque(self):
        token=self.login()
        with self.auth.store.connect() as db:
            self.assertTrue(db.execute('SELECT password_hash FROM auth_users').fetchone()[0].startswith('scrypt:'))
            self.assertNotEqual(db.execute('SELECT digest FROM auth_sessions').fetchone()[0],token)
        self.assertEqual(self.auth.user(f'{COOKIE}={token}')['display_name'],'Alice')
    def test_logout_revokes_session(self):
        cookie=f'{COOKIE}={self.login()}'
        self.auth.logout(cookie);self.assertIsNone(self.auth.user(cookie))
    def test_expired_session_is_rejected(self):
        cookie=f'{COOKIE}={self.login()}'
        with patch('authentication.time.time',return_value=time.time()+9*3600):
            self.assertIsNone(self.auth.user(cookie))
    def test_password_reset_revokes_all_sessions(self):
        cookies=[f'{COOKIE}={self.login()}' for _ in range(2)]
        self.auth.set_password('alice','Synthetic-new-password-2026','Alice')
        self.assertTrue(all(self.auth.user(c) is None for c in cookies))
    def test_repeated_bad_passwords_are_limited(self):
        for _ in range(5):
            with self.assertRaises(LoginError): self.auth.login('alice','incorrect')
        with self.assertRaises(LoginLimited): self.login()
    def test_unknown_and_wrong_password_have_same_error(self):
        messages=[]
        for name in ('unknown','alice'):
            with self.assertRaises(LoginError) as error:self.auth.login(name,'incorrect')
            messages.append(str(error.exception))
        self.assertEqual(messages[0],messages[1])
    def test_secure_cookie_attributes(self):
        cookie=self.auth.cookie('test',secure=True)
        for flag in ('HttpOnly','SameSite=Strict','Secure','Path=/'):
            self.assertIn(flag,cookie)
    def test_forged_cookie_is_rejected(self):
        self.assertIsNone(self.auth.user(f'{COOKIE}=forged'))
