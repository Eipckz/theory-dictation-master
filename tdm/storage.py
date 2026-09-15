"""Local, transactional evidence store with separate app identity."""
import json
import os
from pathlib import Path
import sqlite3
import time

def default_dir():
    return Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local'/'share'))/'TheoryDictationMaster'

class Store:
    def __init__(self,directory=None):
        self.directory=Path(directory) if directory else default_dir()
        self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/'progress.sqlite3'
        self.db=sqlite3.connect(self.path)
        if self.db.execute('PRAGMA quick_check').fetchone()[0]!='ok': raise ValueError('Progress database needs recovery from a backup.')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, created REAL NOT NULL, data TEXT NOT NULL);''')
        self.db.commit()
    def get(self,key,default=None):
        r=self.db.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
        return json.loads(r[0]) if r else default
    def put(self,key,value):
        with self.db:self.db.execute('INSERT OR REPLACE INTO kv VALUES(?,?)',(key,json.dumps(value)))
    def submit(self,attempt):
        with self.db:
            cur=self.db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?)',(attempt['id'],attempt.get('created',time.time()),json.dumps(attempt)))
        return cur.rowcount==1
    def attempts(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT data FROM attempts ORDER BY created,id')]
    def backup(self,path):
        path=Path(path)
        if path.resolve()==self.path.resolve(): raise ValueError('Choose a different backup path.')
        dest=sqlite3.connect(path)
        try:self.db.backup(dest)
        finally:dest.close()
    def restore(self,path):
        path=Path(path)
        if path.stat().st_size>50_000_000:raise ValueError('Backup exceeds 50 MB.')
        source=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
        try:
            if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup is corrupt.')
            tables={r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'kv','attempts'}<=tables:raise ValueError('This is not a Theory Dictation Master backup.')
            for r in source.execute('SELECT value FROM kv'):json.loads(r[0])
            for r in source.execute('SELECT data FROM attempts'):
                a=json.loads(r[0])
                if not isinstance(a,dict) or 'id' not in a:raise ValueError('Invalid attempt record.')
            self.backup(self.directory/f'before-restore-{time.time_ns()}.sqlite3')
            source.backup(self.db)
        finally:source.close()
    def close(self):self.db.close()

def independent(a):
    return a.get('kind')=='independent' and not a.get('assistance') and a.get('audio_ok') and a.get('result',{}).get('complete')

def comparable(a):
    s=a['target'];p=a['policy']
    return (s['level'],s['bars'],s['bpm'],s['numerator'],s['denominator'],p['support'],p['mode'],p['hearings'],p['rhythm_only'])

def progression(attempts,current,threshold=.9,block_size=8):
    candidates=[a for a in attempts if independent(a) and comparable(a)==comparable(current)]
    seen=set();rows=[]
    for a in candidates:
        fp=a['fingerprint']
        if fp not in seen:seen.add(fp);rows.append(a)
    def passed(a):
        r=a['result'];return r['attacks']>=threshold and r['durations']>=threshold and (r['pitch'] is None or r['pitch']>=threshold)
    last=rows[-2*block_size:]
    advance=len(last)==2*block_size and all(sum(passed(a) for a in last[i:i+block_size])>=block_size-1 for i in (0,block_size))
    support=len(rows)>=5 and sum(a['result']['integrated'] for a in rows[-5:])/5<.7
    return dict(count=len(rows),passed=sum(map(passed,rows)),action='advance' if advance else 'support' if support else 'consolidate',
                rule=f'Two blocks of {block_size}; at least {block_size-1} passes per block; each assessed component at least {threshold:.0%}.')
