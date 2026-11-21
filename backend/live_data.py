"""Synthetic, persistent, local-only security event feed. No vendor connection."""
import json
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4
from backend.config import settings

_LOCK = Lock()
TYPES = [
    ('MDE','Suspicious PowerShell execution','execution','high'),
    ('SentinelOne','Malware quarantined on workstation','malware','medium'),
    ('SIEM','Repeated failed sign-ins','identity','medium'),
    ('MDE','Potential credential dumping','credential_access','critical'),
    ('SIEM','Unusual outbound data transfer','exfiltration','high'),
    ('SentinelOne','Unrecognized scheduled task','persistence','low'),
]
HOSTS=['LAPTOP-FIN-042','SRV-IDENTITY-01','WS-HR-019','SRV-ERP-03','LAPTOP-SALES-114']

def _db():
    path = Path(settings.boris_data_dir)/'telemetry'/'boris_events.sqlite3'
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=20)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('''CREATE TABLE IF NOT EXISTS events (
      id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, source TEXT NOT NULL,
      title TEXT NOT NULL, category TEXT NOT NULL, severity TEXT NOT NULL,
      hostname TEXT NOT NULL, username TEXT NOT NULL, status TEXT NOT NULL,
      description TEXT NOT NULL, simulated INTEGER NOT NULL DEFAULT 1)''')
    con.execute('CREATE INDEX IF NOT EXISTS idx_events_observed ON events(observed_at DESC)')
    con.commit()
    return con

def generate(count=20, seed=None, base_time=None):
    if not 1 <= count <= 250:raise ValueError('count must be 1–250')
    rng=random.Random(seed)
    now=base_time or datetime.now(timezone.utc)
    rows=[]
    for i in range(count):
        source,title,category,severity=rng.choice(TYPES)
        host=rng.choice(HOSTS)
        observed=(now-timedelta(minutes=rng.randint(0,1440))).isoformat()
        rows.append((str(uuid4()),observed,source,title,category,severity,host,
            f'user{rng.randint(1,30):02d}@example.invalid',rng.choice(['new','investigating','resolved']),
            f'SYNTHETIC DEMO EVENT: {title} on {host}. No real security telemetry or confirmed compromise.',1))
    with _LOCK:
        with _db() as con:
            con.executemany('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)',rows)
    return {'inserted':len(rows),'simulated':True}

def list_events(limit=50, severity=None, source=None, status=None, hours=None):
    limit=max(1,min(int(limit),500))
    clauses=[];args=[]
    for key,value in [('severity',severity),('source',source),('status',status)]:
        if value:
            clauses.append(f'{key}=?');args.append(value)
    if hours is not None:
        if not 1 <= int(hours) <= 24*30:raise ValueError('hours must be between 1 and 720')
        cutoff=(datetime.now(timezone.utc)-timedelta(hours=int(hours))).isoformat()
        clauses.append('observed_at>=?');args.append(cutoff)
    where=(' WHERE '+' AND '.join(clauses)) if clauses else ''
    with _db() as con:
        records=con.execute('SELECT * FROM events'+where+' ORDER BY observed_at DESC LIMIT ?',(*args,limit)).fetchall()
    return [dict(r) for r in records]

def get_event(event_id):
    with _db() as con:
        row=con.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
    return dict(row) if row else None

def summary():
    with _db() as con:
        total=con.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        by_severity={r['severity']:r['n'] for r in con.execute('SELECT severity,COUNT(*) n FROM events GROUP BY severity')}
        by_source={r['source']:r['n'] for r in con.execute('SELECT source,COUNT(*) n FROM events GROUP BY source')}
    return {'total':total,'by_severity':by_severity,'by_source':by_source,'simulated':True}

def seed_if_empty(count=30):
    with _db() as con:
        existing=con.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    return {'inserted':0,'simulated':True} if existing else generate(count,seed=42)
