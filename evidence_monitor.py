"""Read local PDFs and exported Sent EMLs; never send email.
The Sent directory is a trusted input convention, not proof of SMTP delivery.
"""
import hashlib
import io
import json
import re
import threading
import unicodedata
from email import policy
from email.parser import BytesParser
from pathlib import Path
from pypdf import PdfReader
from invoice_store import now

def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())

def pdf_lines(data):
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted or len(reader.pages)>20:
        raise ValueError('Encrypted PDF or more than 20 pages')
    text='\n'.join(page.extract_text() or '' for page in reader.pages)
    if not text.strip():
        raise ValueError('PDF has no readable text: review or OCR required')
    return text.splitlines()

class Monitor:
    def __init__(self,store,folder):
        self.store,self.folder=store,Path(folder)
        self.lock=threading.Lock()
        for name in ('pdfs','sent'):
            (self.folder/name).mkdir(parents=True,exist_ok=True)
        with store.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS evidence (
              digest TEXT PRIMARY KEY, kind TEXT NOT NULL, filename TEXT NOT NULL,
              state TEXT NOT NULL, reason TEXT NOT NULL, payload TEXT NOT NULL,
              request_id TEXT, created TEXT NOT NULL)""")

    def records(self):
        with self.store.connect() as db:
            return [dict(row) for row in db.execute(
                'SELECT digest,kind,filename,state,reason,request_id,created FROM evidence ORDER BY created DESC')]

    def ingest(self,path,kind):
        if path.is_symlink() or not path.is_file(): return
        if path.stat().st_size>10*1024*1024:
            data=None
            digest=hashlib.sha256((str(path)+str(path.stat().st_mtime_ns)).encode()).hexdigest()
        else:
            data=path.read_bytes()
            digest=hashlib.sha256(data).hexdigest()
        with self.store.connect() as db:
            if db.execute('SELECT 1 FROM evidence WHERE digest=?',(digest,)).fetchone(): return
        state,reason,payload='pending','',{}
        try:
            if data is None: raise ValueError('File exceeds 10 MB')
            if kind=='pdf':
                payload={'lines':pdf_lines(data)}
            else:
                message=BytesParser(policy=policy.default).parsebytes(data)
                if message.defects or not message.get('To') or not message.get('Date'):
                    raise ValueError('Malformed email or missing recipient/date')
                attachments=[]
                for part in message.iter_attachments():
                    content=part.get_payload(decode=True)
                    if content and part.get_content_type()=='application/pdf':
                        attachments.append(hashlib.sha256(content).hexdigest())
                if not attachments: raise ValueError('No PDF attachment')
                payload={'attachments':attachments,'to':str(message['To'])}
        except Exception as exc:
            state='review'
            reason=str(exc) if isinstance(exc,ValueError) else 'Unreadable document; review required'
        with self.store.connect() as db:
            db.execute('INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?,?,?)',
                       (digest,kind,path.name,state,reason,json.dumps(payload),None,now()))

    def reconcile(self):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            requests=[dict(row) for row in db.execute('SELECT * FROM requests')]
            docs=db.execute("SELECT * FROM evidence WHERE kind='pdf' AND state='pending'").fetchall()
            for doc in docs:
                lines=json.loads(doc['payload'])['lines']
                values={normalized(re.sub(r'^(Guest|Gast|Ospite|Stay|Aufenthalt|Soggiorno)\s*:\s*','',line,flags=re.I)) for line in lines}
                # Conservative exact identity + stay, never name alone.
                candidates=[row for row in requests if row['stay'].strip()
                            and normalized(row['guest']) in values and normalized(row['stay']) in values]
                if not re.search(r'\b(rechnung|invoice|fattura)\b','\n'.join(lines),re.I): candidates=[]
                if len(candidates)!=1:
                    db.execute('UPDATE evidence SET reason=? WHERE digest=?',
                               ('Guest and stay do not identify a unique request; no automatic change',doc['digest']))
                    continue
                row=candidates[0]
                previous=db.execute("SELECT 1 FROM evidence WHERE kind='pdf' AND state='linked' AND request_id=?",(row['id'],)).fetchone()
                if previous or row['status'] in {'sent','delivered'}:
                    db.execute("UPDATE evidence SET state='review',reason=? WHERE digest=?",
                               ('Possible second invoice or revision: review required',doc['digest']))
                    continue
                db.execute("UPDATE evidence SET state='linked',reason='',request_id=? WHERE digest=?",(row['id'],doc['digest']))
                db.execute("UPDATE requests SET status='prepared',updated=? WHERE id=?",(now(),row['id']))
                db.execute('INSERT INTO events(request_id,at,actor,detail) VALUES (?,?,?,?)',
                           (row['id'],now(),'PDF folder','PDF detected: '+doc['filename']))
            # Revisit pending messages: email-before-PDF arrival is supported.
            emails=db.execute("SELECT * FROM evidence WHERE kind='eml' AND state='pending'").fetchall()
            for email in emails:
                payload=json.loads(email['payload']);matched=[]
                for digest in payload['attachments']:
                    doc=db.execute("SELECT request_id FROM evidence WHERE digest=? AND kind='pdf' AND state='linked'",(digest,)).fetchone()
                    if doc: matched.append(doc['request_id'])
                ids=set(matched)
                if len(ids)!=1 or len(matched)!=len(payload['attachments']):
                    db.execute('UPDATE evidence SET reason=? WHERE digest=?',
                               ('Unmatched attachment or email covering multiple requests',email['digest']))
                    continue
                key=ids.pop()
                row=db.execute('SELECT status FROM requests WHERE id=?',(key,)).fetchone()
                if row['status'] not in {'prepared','sent'}: continue
                db.execute("UPDATE evidence SET state='linked',reason='',request_id=? WHERE digest=?",(key,email['digest']))
                if row['status']!='sent':
                    db.execute("UPDATE requests SET status='sent',updated=? WHERE id=?",(now(),key))
                    db.execute('INSERT INTO events(request_id,at,actor,detail) VALUES (?,?,?,?)',
                               (key,now(),'Sent mail archive','Exported email with identical PDF: '+email['filename']))

    def scan(self):
        with self.lock:
            for dirname,pattern,kind in [('pdfs','*.pdf','pdf'),('sent','*.eml','eml')]:
                for path in sorted((self.folder/dirname).glob(pattern)): self.ingest(path,kind)
            self.reconcile()

    def run(self,stop):
        while not stop.wait(3):
            try: self.scan()
            except OSError: continue
