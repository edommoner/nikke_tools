"""Exact CPU extension inverse; never a generated-code normalization rule."""
import hashlib,json
from pathlib import Path


def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {})
    ledger=json.loads((root/'tests/fixtures/portable-enemy-ammo-self-destruct-source-delta.json').read_text(encoding='utf-8'))
    for name,digest in ledger['added_sources'].items():
        value=out[name] if name in out else (root/name).read_text(encoding='utf-8')
        if hashlib.sha256(value.encode()).hexdigest()!=digest:raise ValueError('Unreviewed final-queue dependency: '+name)
    for name,row in ledger['files'].items():
        value=out[name] if name in out else (root/name).read_text(encoding='utf-8')
        digest=hashlib.sha256(value.encode()).hexdigest()
        if name in out and digest==row['before_sha256']:continue
        if value!=row['after'] or digest!=row['after_sha256'] or hashlib.sha256(row['before'].encode()).hexdigest()!=row['before_sha256']:
            raise ValueError('Unreviewed final-queue shared source: '+name)
        out[name]=row['before']
    return out
