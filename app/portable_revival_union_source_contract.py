"""Exact historical union source inverse; no current GPU parity claim."""
import hashlib,json
from pathlib import Path
LEDGER_SHA256='b61f14c0ec03d6c1221bdd800f0f9ae0f33233ded998e16547c9c26a2a217c98'

def preimages(root):
    root=Path(root);path=root/'tests/fixtures/portable-revival-stack-union-source-delta.json'
    if not path.exists():return {}
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Revival union history ledger changed')
    rows=json.loads(raw)['files'];out={}
    for name,row in rows.items():
        path=root/name
        if not path.is_file():continue
        text=path.read_text();digest=hashlib.sha256(text.encode()).hexdigest()
        if digest==row['before_sha256']:out[name]=text;continue
        if digest!=row['after_sha256']:raise ValueError('Unreviewed revival union source: '+name)
        boundary=len(text)
        for hunk in reversed(row['hunks']):
            start,end=hunk['start'],hunk['end']
            if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Revival union inverse span differs')
            text=text[:start]+hunk['before']+text[end:];boundary=start
        if hashlib.sha256(text.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Revival union historical preimage differs')
        out[name]=text
    return out
