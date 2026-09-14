"""Local invoice request coordination with transactional ownership changes."""
import sqlite3
import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

class Conflict(ValueError):
    pass

def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS requests (
              id TEXT PRIMARY KEY, guest TEXT NOT NULL, stay TEXT NOT NULL,
              source TEXT NOT NULL, note TEXT NOT NULL, status TEXT NOT NULL,
              owner TEXT, created TEXT NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY, request_id TEXT NOT NULL,
              at TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS billing_details (
              request_id TEXT PRIMARY KEY, company TEXT NOT NULL DEFAULT '',
              address TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS followup_proposals (
              id TEXT PRIMARY KEY, username TEXT NOT NULL, expires REAL NOT NULL,
              payload TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def list(self):
        with self.connect() as db:
            rows = [dict(row) for row in db.execute('SELECT * FROM requests ORDER BY created DESC')]
            for row in rows:
                billing = db.execute('SELECT company,address FROM billing_details WHERE request_id=?', (row['id'],)).fetchone()
                row.update(dict(billing) if billing else {'company': '', 'address': ''})
                row['events'] = [dict(e) for e in db.execute(
                    'SELECT at, actor, detail FROM events WHERE request_id=? ORDER BY id', (row['id'],))]
            return rows

    def create(self, guest, stay, source, note, actor, prepare=False):
        values = [guest, stay, source, note, actor]
        if not all(isinstance(v, str) for v in values):
            raise ValueError('Invalid fields')
        if not guest.strip() or not actor.strip():
            raise ValueError('Enter the guest and operator names')
        if any(len(v) > 4000 for v in values):
            raise ValueError('Text is too long')
        if source not in {'In person', 'Phone', 'Booking', 'Paper note', 'Email', 'Other'}:
            raise ValueError('Invalid source')
        key, stamp = uuid4().hex, now()
        with self.connect() as db:
            db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?)',
                       (key, guest.strip(), stay.strip(), source, note.strip(),
                        'working' if prepare else 'requested', actor.strip() if prepare else None, stamp, stamp))
            db.execute('INSERT INTO events(request_id,at,actor,detail) VALUES (?,?,?,?)',
                       (key, stamp, actor, 'Request added' + (' and claimed' if prepare else '')))
        return key

    def act(self, key, action, actor):
        if not isinstance(actor, str) or not actor.strip() or len(actor) > 100:
            raise ValueError('Invalid operator')
        with self.connect() as db:
            # Serialize check-and-update across tabs/operators: no double claim.
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM requests WHERE id=?', (key,)).fetchone()
            if row is None:
                raise ValueError('Request not found')
            state, owner = row['status'], row['owner']
            if action == 'claim':
                if state == 'working' and owner == actor:
                    return
                if state != 'requested':
                    raise Conflict('Request already claimed or completed. Refresh the list.')
                state, owner, detail = 'working', actor, 'Preparation started; Lexware opening requested'
            elif action == 'release':
                if state != 'working' or owner != actor:
                    raise Conflict('Only the assigned operator can release this request')
                state, owner, detail = 'requested', None, 'Request released'
            elif action == 'deliver':
                if state != 'prepared' or owner != actor:
                    raise Conflict('Hand delivery requires a prepared invoice and its assigned operator')
                state, detail = 'delivered', 'Hand delivery confirmed by the operator'
            else:
                raise ValueError('Invalid action')
            stamp = now()
            db.execute('UPDATE requests SET status=?,owner=?,updated=? WHERE id=?', (state, owner, stamp, key))
            db.execute('INSERT INTO events(request_id,at,actor,detail) VALUES (?,?,?,?)', (key, stamp, actor, detail))

    def details(self,key,stay,note,actor):
        if not all(isinstance(v,str) for v in (key,stay,note,actor)): raise ValueError('Invalid fields')
        if not actor.strip() or len(stay)>300 or len(note)>4000: raise ValueError('Invalid fields')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM requests WHERE id=?',(key,)).fetchone()
            if row is None: raise ValueError('Request not found')
            if row['status'] not in {'requested','working'}: raise Conflict('Invoice already prepared: details retained in history')
            db.execute('UPDATE requests SET stay=?,note=?,updated=? WHERE id=?',(stay.strip(),note.strip(),now(),key))
            db.execute('INSERT INTO events(request_id,at,actor,detail) VALUES (?,?,?,?)',(key,now(),actor,'Details updated'))

    def seed(self):
        if self.list():
            return
        self.create('Anna Keller', 'September 12–15 · Room 12', 'Booking',
                    'Company invoice requested. Billing address missing.', 'Reception')
        self.create('Marco Rossi', 'September 10–13 · Private room', 'Phone',
                    'Called again about the invoice. Check dates and amount in the paper ledger.', 'Reception')
        self.create('Peter Wagner', 'September 14–18 · Contractor', 'Paper note',
                    'Company details on the paper note. Email address still needed.', 'Reception')

    def save_followup(self, plan, username):
        if plan['status'] != 'ready':
            return None
        key = uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO followup_proposals(id,username,expires,payload) VALUES (?,?,?,?)',
                       (key, username, time.time() + 900, json.dumps(plan)))
        return key

    def confirm_followup(self, proposal_id, username, actor):
        if not isinstance(proposal_id, str):
            raise ValueError('Invalid proposal')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            saved = db.execute('SELECT * FROM followup_proposals WHERE id=? AND username=?', (proposal_id, username)).fetchone()
            if not saved or saved['consumed'] or saved['expires'] < time.time():
                raise Conflict('Proposal expired or already used. Analyze the message again.')
            plan = json.loads(saved['payload']); target = plan['target']
            row = db.execute('SELECT * FROM requests WHERE id=?', (target['id'],)).fetchone()
            if not row or row['updated'] != target['updated'] or row['status'] not in {'requested', 'working'}:
                raise Conflict('Request changed. Analyze the message again before confirming.')
            billing = db.execute('SELECT company,address FROM billing_details WHERE request_id=?', (row['id'],)).fetchone()
            values = {'stay': row['stay'], **(dict(billing) if billing else {'company': '', 'address': ''})}
            for change in plan['changes']:
                field = change['field']
                if field not in values or values[field] or change['before'] or not change['after'] or change['after'] not in plan['source']:
                    raise Conflict('Proposed change is no longer valid. Analyze again.')
                values[field] = change['after']
            note = row['note'] + '\n\nFollow-up message:\n' + plan['source']
            if len(note) > 12000:
                raise Conflict('Request notes are full. Review the request manually.')
            stamp = now()
            db.execute('UPDATE requests SET stay=?,note=?,updated=? WHERE id=?', (values['stay'], note, stamp, row['id']))
            db.execute('INSERT INTO billing_details(request_id,company,address) VALUES (?,?,?) ON CONFLICT(request_id) DO UPDATE SET company=excluded.company,address=excluded.address',
                       (row['id'], values['company'], values['address']))
            db.execute('INSERT INTO events(request_id,at,actor,detail) VALUES (?,?,?,?)',
                       (row['id'], stamp, actor, 'Follow-up confirmed: ' + ', '.join(c['field'] for c in plan['changes'])))
            db.execute('UPDATE followup_proposals SET consumed=1 WHERE id=?', (proposal_id,))
            return row['id']
