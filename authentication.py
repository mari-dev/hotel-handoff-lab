"""Local accounts, revocable opaque sessions, and bounded sign-in attempts."""
import hashlib
import re
import secrets
import time
from http.cookies import SimpleCookie, CookieError
from werkzeug.security import generate_password_hash, check_password_hash

COOKIE = 'handoff_session'
LIFETIME = 8 * 60 * 60


class LoginError(ValueError):
    pass


class LoginLimited(LoginError):
    pass


class Auth:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS auth_users (
                    username TEXT PRIMARY KEY, display_name TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    digest TEXT PRIMARY KEY, username TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS auth_attempts (username TEXT NOT NULL, at REAL NOT NULL);
            ''')
        self._dummy = generate_password_hash(secrets.token_urlsafe(24))

    def has_users(self):
        with self.store.connect() as db:
            return bool(db.execute('SELECT 1 FROM auth_users LIMIT 1').fetchone())

    def set_password(self, username, password, display_name):
        username = username.strip().casefold()
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,63}', username):
            raise ValueError('Username must contain 3–64 letters, numbers, dots, hyphens or underscores')
        if not 12 <= len(password) <= 256:
            raise ValueError('Use a password of 12–256 characters')
        display_name = display_name.strip()
        if not display_name or len(display_name) > 100:
            raise ValueError('A display name of up to 100 characters is required')
        hashed = generate_password_hash(password)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT display_name FROM auth_users WHERE username=?',(username,)).fetchone()
            if existing and existing[0]!=display_name:
                raise ValueError('Keep the existing display name when resetting a password; invoice ownership uses that name')
            db.execute('INSERT INTO auth_users VALUES (?,?,?) ON CONFLICT(username) DO UPDATE SET display_name=excluded.display_name,password_hash=excluded.password_hash',
                       (username, display_name, hashed))
            db.execute('DELETE FROM auth_sessions WHERE username=?', (username,))

    def login(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str) or len(username)>64 or len(password)>256:
            raise LoginError('Invalid username or password')
        username = username.strip().casefold()
        stamp = time.time()
        # Reserve the attempt before hashing, including concurrent requests.
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM auth_attempts WHERE at<?', (stamp-600,))
            db.execute('DELETE FROM auth_sessions WHERE expires<=?', (stamp,))
            count = db.execute('SELECT COUNT(*) FROM auth_attempts WHERE username=?', (username,)).fetchone()[0]
            total = db.execute('SELECT COUNT(*) FROM auth_attempts').fetchone()[0]
            if count >= 5 or total >= 50:
                raise LoginLimited('Too many sign-in attempts. Try again in 10 minutes.')
            db.execute('INSERT INTO auth_attempts VALUES (?,?)', (username,stamp))
            row = db.execute('SELECT * FROM auth_users WHERE username=?', (username,)).fetchone()
        valid = check_password_hash(row['password_hash'] if row else self._dummy, password)
        if not valid or not row:
            raise LoginError('Invalid username or password')
        token = secrets.token_urlsafe(32)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # A concurrent password reset must not issue a session for the old password.
            current = db.execute('SELECT password_hash FROM auth_users WHERE username=?', (username,)).fetchone()
            if not current or current[0] != row['password_hash']:
                raise LoginError('Invalid username or password')
            db.execute('INSERT INTO auth_sessions VALUES (?,?,?)',
                       (self.digest(token),username,stamp+LIFETIME))
            db.execute('DELETE FROM auth_attempts WHERE username=?', (username,))
        return token, {'username':username, 'display_name':row['display_name']}

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def token(cookie):
        try:
            parsed = SimpleCookie(cookie or '')
            return parsed[COOKIE].value if COOKIE in parsed else ''
        except CookieError:
            return ''

    def user(self, cookie):
        token = self.token(cookie)
        if not token or len(token)>128:
            return None
        with self.store.connect() as db:
            row = db.execute('SELECT u.username,u.display_name FROM auth_sessions s JOIN auth_users u ON u.username=s.username WHERE s.digest=? AND s.expires>?',
                             (self.digest(token),time.time())).fetchone()
        return dict(row) if row else None

    def logout(self, cookie):
        with self.store.connect() as db:
            db.execute('DELETE FROM auth_sessions WHERE digest=?', (self.digest(self.token(cookie)),))

    @staticmethod
    def cookie(token, secure=False, clear=False):
        return f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={0 if clear else LIFETIME}' + ('; Secure' if secure else '')
