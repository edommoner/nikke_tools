"""Exact inverse of guarded ADD battle hooks before historical source audits."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);ledger=json.loads((root/'tests/fixtures/portable-add-attack-battle-source-delta.json').read_text());out=dict(sources or {})
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise ValueError('Unreviewed ADD battle dependency: '+name)
    for name,row in ledger['files'].items():
        current=out.get(name,(root/name).read_text());digest=hashlib.sha256(current.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if current!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:raise ValueError('Unreviewed ADD battle shared source: '+name)
        out[name]=row['before']
    return out
