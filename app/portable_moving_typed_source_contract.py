"""Exact opt-in inverse, retaining approved downstream movement preimages."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});ledger=json.loads((root/'tests/fixtures/portable-moving-typed-source-delta.json').read_text())
    downstream=json.loads((root/'tests/fixtures/portable-enemy-movement-source-delta.json').read_text())['files']
    for name,digest in ledger['added_sources'].items():
        if hashlib.sha256(out.get(name,(root/name).read_text()).encode()).hexdigest()!=digest:raise ValueError('Unreviewed moving typed dependency: '+name)
    for name,row in ledger['files'].items():
        value=out.get(name,(root/name).read_text());digest=hashlib.sha256(value.encode()).hexdigest()
        if name in out and digest in {row['before_sha256'],downstream.get(name,{}).get('before_sha256')}:continue
        if digest!=row['after_sha256']:raise ValueError('Unreviewed moving typed shared source: '+name)
        for h in reversed(row['hunks']):
            if value.count(h['after'])!=1:raise ValueError('Ambiguous moving typed inverse')
            value=value.replace(h['after'],h['before'],1)
        if hashlib.sha256(value.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Moving typed inverse differs')
        out[name]=value
    return out
