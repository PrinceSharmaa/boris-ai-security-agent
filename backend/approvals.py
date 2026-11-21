"""Persistent advisory approval requests. No operational actions are performed."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from backend.config import settings

def _connect():
    path=settings.boris_data_dir/'telemetry'/'approvals.sqlite3'
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=10)
    con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, event_id TEXT NOT NULL, status TEXT NOT NULL, requested_at TEXT NOT NULL, decided_at TEXT, reviewer TEXT, reason TEXT, payload TEXT NOT NULL)')
    return con

def request_approval(event_id:str, payload:dict)->dict:
    """Idempotent pending request per event, so repeated chats do not spam reviewers."""
    with _connect() as db:
        existing=db.execute("SELECT * FROM approvals WHERE event_id=? AND status='pending'",(event_id,)).fetchone()
        if existing:return _format(existing)
        aid=str(uuid.uuid4());now=datetime.now(timezone.utc).isoformat()
        db.execute('INSERT INTO approvals(id,event_id,status,requested_at,payload) VALUES (?,?,?,?,?)',(aid,event_id,'pending',now,json.dumps(payload)))
        return {'id':aid,'event_id':event_id,'status':'pending','requested_at':now,'payload':payload}

def _format(row):
    d=dict(row);d['payload']=json.loads(d['payload']);return d

def list_approvals(status:str|None=None)->list[dict]:
    if status not in (None,'pending','approved','rejected'):raise ValueError('Invalid approval status')
    with _connect() as db:
        rows=db.execute('SELECT * FROM approvals WHERE status=? ORDER BY requested_at DESC',(status,)).fetchall() if status else db.execute('SELECT * FROM approvals ORDER BY requested_at DESC').fetchall()
        return [_format(r) for r in rows]

def decide(approval_id:str, decision:str, reviewer:str, reason:str='')->dict|None:
    if decision not in ('approved','rejected'):raise ValueError('Decision must be approved or rejected')
    if not reviewer.strip():raise ValueError('Reviewer is required')
    with _connect() as db:
        updated=db.execute("UPDATE approvals SET status=?,reviewer=?,reason=?,decided_at=? WHERE id=? AND status='pending'",(decision,reviewer.strip(),reason,datetime.now(timezone.utc).isoformat(),approval_id)).rowcount
        row=db.execute('SELECT * FROM approvals WHERE id=?',(approval_id,)).fetchone()
        if not row:return None
        result=_format(row);result['updated']=bool(updated);return result
